"""Atomic SQLite persistence for immutable graph revisions."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import fields, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import cast

from extendcodeagent.blueprint.contracts import (
    BlueprintElement,
    BlueprintRevision,
    BlueprintScope,
    BlueprintStatus,
)
from extendcodeagent.convergence.contracts import (
    ConvergenceDecision,
    ConvergenceRecommendation,
    ConvergenceReport,
    ElementConvergence,
    ElementState,
)
from extendcodeagent.core.contracts import (
    CanonicalRef,
    Confidence,
    EvidenceRef,
    EvidenceStatus,
    ProjectRef,
    Provenance,
    SourceRevision,
    TwinRevisionRef,
)
from extendcodeagent.graph import (
    FactStatus,
    GraphDelta,
    GraphEdge,
    GraphEvidence,
    GraphNode,
    GraphRevision,
    GraphSnapshot,
)
from extendcodeagent.research.contracts import Evidence
from extendcodeagent.runtime import (
    ObservationKind,
    ObservationStatus,
    RuntimeObservation,
)

SCHEMA_VERSION = 5


class StoreError(RuntimeError):
    pass


class RevisionConflict(StoreError):
    pass


class SqliteGraphStore:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._connection = sqlite3.connect(self.path, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        if self.path != ":memory:":
            self._connection.execute("PRAGMA journal_mode = WAL")
        self._migrate()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> SqliteGraphStore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def apply(self, delta: GraphDelta) -> GraphRevision:
        scope = _scope(delta.project)
        self._validate_scope(delta)
        with self._transaction():
            existing = self._connection.execute(
                "SELECT revision_id FROM delta_log WHERE scope=? AND idempotency_key=?",
                (scope, delta.idempotency_key),
            ).fetchone()
            if existing:
                return self.get_revision(delta.project, existing["revision_id"])
            head = self.current_revision(delta.project)
            head_id = head.revision_id if head else None
            if delta.expected_revision_id is not None and delta.expected_revision_id != head_id:
                raise RevisionConflict(
                    f"expected revision {delta.expected_revision_id!r}, current is {head_id!r}"
                )
            revision_id = uuid.uuid4().hex
            sequence = self._next_sequence(scope)
            revision = GraphRevision(
                revision_id,
                delta.project,
                delta.source_revision,
                delta.worktree_fingerprint,
                delta.analyzer_versions,
                parent_revision_id=head_id,
            )
            for node in delta.nodes:
                self._close_current(
                    "nodes", scope, "canonical_ref", node.canonical_ref.value, sequence
                )
                self._connection.execute(
                    "INSERT INTO nodes(scope,node_id,canonical_ref,source_ref,status,payload,valid_from,valid_to) VALUES(?,?,?,?,?,?,?,NULL)",
                    (
                        scope,
                        node.node_id,
                        node.canonical_ref.value,
                        node.source_ref,
                        node.status.value,
                        _dump(node),
                        sequence,
                    ),
                )
            for edge in delta.edges:
                self._close_current("edges", scope, "edge_id", edge.edge_id, sequence)
                self._connection.execute(
                    "INSERT INTO edges(scope,edge_id,source_ref,target_ref,fact_source_ref,status,payload,valid_from,valid_to) VALUES(?,?,?,?,?,?,?,?,NULL)",
                    (
                        scope,
                        edge.edge_id,
                        edge.source.value,
                        edge.target.value,
                        edge.source_ref,
                        edge.status.value,
                        _dump(edge),
                        sequence,
                    ),
                )
            for item in delta.evidence:
                self._connection.execute(
                    "INSERT INTO evidence(scope,evidence_id,payload,revision_sequence) VALUES(?,?,?,?)",
                    (scope, item.evidence_id, _dump(item), sequence),
                )
            for node_id in delta.invalidate_node_ids:
                self._invalidate("nodes", scope, "node_id", node_id, sequence)
            for edge_id in delta.invalidate_edge_ids:
                self._invalidate("edges", scope, "edge_id", edge_id, sequence)
            self._connection.execute(
                "INSERT INTO revisions(scope,revision_id,sequence,parent_revision_id,payload) VALUES(?,?,?,?,?)",
                (scope, revision_id, sequence, head_id, _dump_revision(revision)),
            )
            self._connection.execute(
                "INSERT INTO projects(scope,project_id,workspace_id,head_revision_id) VALUES(?,?,?,?) "
                "ON CONFLICT(scope) DO UPDATE SET head_revision_id=excluded.head_revision_id",
                (scope, delta.project.project_id, delta.project.workspace_id, revision_id),
            )
            self._connection.execute(
                "INSERT INTO delta_log(scope,idempotency_key,revision_id) VALUES(?,?,?)",
                (scope, delta.idempotency_key, revision_id),
            )
        return revision

    def current_revision(self, project: ProjectRef) -> GraphRevision | None:
        row = self._connection.execute(
            "SELECT r.payload FROM projects p JOIN revisions r ON r.scope=p.scope AND r.revision_id=p.head_revision_id WHERE p.scope=?",
            (_scope(project),),
        ).fetchone()
        return _load_revision(row["payload"]) if row else None

    def get_revision(self, project: ProjectRef, revision_id: str) -> GraphRevision:
        row = self._connection.execute(
            "SELECT payload FROM revisions WHERE scope=? AND revision_id=?",
            (_scope(project), revision_id),
        ).fetchone()
        if not row:
            raise StoreError(f"revision not found: {revision_id}")
        return _load_revision(row["payload"])

    def snapshot(self, project: ProjectRef, revision_id: str | None = None) -> GraphSnapshot:
        revision = (
            self.get_revision(project, revision_id)
            if revision_id
            else self.current_revision(project)
        )
        if revision is None:
            return GraphSnapshot(project, None)
        sequence = self._sequence(project, revision.revision_id)
        scope = _scope(project)
        valid = "valid_from<=? AND (valid_to IS NULL OR valid_to>?)"
        nodes = self._connection.execute(
            f"SELECT payload FROM nodes WHERE scope=? AND {valid} ORDER BY row_id",
            (scope, sequence, sequence),
        ).fetchall()
        edges = self._connection.execute(
            f"SELECT payload FROM edges WHERE scope=? AND {valid} ORDER BY row_id",
            (scope, sequence, sequence),
        ).fetchall()
        evidence = self._connection.execute(
            "SELECT payload FROM evidence WHERE scope=? AND revision_sequence<=? ORDER BY row_id",
            (scope, sequence),
        ).fetchall()
        return GraphSnapshot(
            project,
            revision,
            tuple(_load_node(row["payload"]) for row in nodes),
            tuple(_load_edge(row["payload"]) for row in edges),
            tuple(_load_evidence(row["payload"]) for row in evidence),
        )

    def reverse_edges(self, project: ProjectRef, target: CanonicalRef) -> tuple[GraphEdge, ...]:
        rows = self._connection.execute(
            "SELECT payload FROM edges WHERE scope=? AND target_ref=? AND valid_to IS NULL ORDER BY row_id",
            (_scope(project), target.value),
        ).fetchall()
        return tuple(_load_edge(row["payload"]) for row in rows)

    def put_observation(self, observation: RuntimeObservation) -> bool:
        scope = _scope(observation.project)
        payload = _dump(observation)
        existing = self._connection.execute(
            "SELECT payload FROM runtime_observations WHERE scope=? AND observation_id=?",
            (scope, observation.observation_id),
        ).fetchone()
        if existing:
            if existing["payload"] != payload:
                raise StoreError(
                    f"observation_id collision with different payload: {observation.observation_id}"
                )
            return False
        with self._transaction():
            self._connection.execute(
                "INSERT INTO runtime_observations(scope,observation_id,source_revision,kind,status,finished_at,payload) VALUES(?,?,?,?,?,?,?)",
                (
                    scope,
                    observation.observation_id,
                    observation.source_revision.value,
                    observation.kind.value,
                    observation.status.value,
                    observation.finished_at.isoformat(),
                    payload,
                ),
            )
            self._connection.executemany(
                "INSERT INTO runtime_observation_refs(scope,observation_id,canonical_ref) VALUES(?,?,?)",
                [
                    (scope, observation.observation_id, item.value)
                    for item in observation.observed_refs
                ],
            )
        return True

    def observations(
        self,
        project: ProjectRef,
        *,
        refs: tuple[CanonicalRef, ...] = (),
        limit: int = 1_000,
    ) -> tuple[RuntimeObservation, ...]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        scope = _scope(project)
        if refs:
            placeholders = ",".join("?" for _ in refs)
            rows = self._connection.execute(
                f"SELECT DISTINCT o.payload,o.finished_at,o.observation_id FROM runtime_observations o JOIN runtime_observation_refs r ON r.scope=o.scope AND r.observation_id=o.observation_id WHERE o.scope=? AND r.canonical_ref IN ({placeholders}) ORDER BY o.finished_at DESC,o.observation_id LIMIT ?",
                (scope, *(item.value for item in refs), limit),
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT payload,finished_at,observation_id FROM runtime_observations WHERE scope=? ORDER BY finished_at DESC,observation_id LIMIT ?",
                (scope, limit),
            ).fetchall()
        return tuple(_load_observation(row["payload"]) for row in rows)

    def put_blueprint_revision(self, revision: BlueprintRevision) -> bool:
        scope = _scope(revision.project)
        payload = _dump(revision)
        existing = self._connection.execute(
            "SELECT payload FROM blueprint_revisions WHERE scope=? AND revision_id=?",
            (scope, revision.revision_id),
        ).fetchone()
        if existing:
            if existing["payload"] != payload:
                raise StoreError(f"immutable blueprint revision collision: {revision.revision_id}")
            return False
        with self._transaction():
            self._connection.execute(
                "INSERT INTO blueprint_revisions(scope,revision_id,blueprint_id,status,created_at,payload) VALUES(?,?,?,?,?,?)",
                (
                    scope,
                    revision.revision_id,
                    revision.blueprint_id,
                    revision.status.value,
                    revision.created_at.isoformat(),
                    payload,
                ),
            )
        return True

    def blueprint_revision(self, project: ProjectRef, revision_id: str) -> BlueprintRevision | None:
        row = self._connection.execute(
            "SELECT payload FROM blueprint_revisions WHERE scope=? AND revision_id=?",
            (_scope(project), revision_id),
        ).fetchone()
        return _load_blueprint_revision(row["payload"]) if row else None

    def blueprint_revisions(self, project: ProjectRef) -> tuple[BlueprintRevision, ...]:
        rows = self._connection.execute(
            "SELECT payload FROM blueprint_revisions WHERE scope=? ORDER BY created_at,revision_id",
            (_scope(project),),
        ).fetchall()
        return tuple(_load_blueprint_revision(row["payload"]) for row in rows)

    def blueprint_status(self, project: ProjectRef, revision_id: str) -> BlueprintStatus | None:
        row = self._connection.execute(
            "SELECT status FROM blueprint_revisions WHERE scope=? AND revision_id=?",
            (_scope(project), revision_id),
        ).fetchone()
        return BlueprintStatus(row["status"]) if row else None

    def set_blueprint_status(
        self, project: ProjectRef, revision_id: str, status: BlueprintStatus
    ) -> None:
        with self._transaction():
            cursor = self._connection.execute(
                "UPDATE blueprint_revisions SET status=? WHERE scope=? AND revision_id=?",
                (status.value, _scope(project), revision_id),
            )
            if cursor.rowcount != 1:
                raise StoreError(f"blueprint revision not found: {revision_id}")

    def set_active_blueprint(self, project: ProjectRef, revision_id: str) -> None:
        if self.blueprint_revision(project, revision_id) is None:
            raise StoreError(f"blueprint revision not found: {revision_id}")
        with self._transaction():
            self._connection.execute(
                "INSERT INTO active_blueprints(scope,revision_id) VALUES(?,?) ON CONFLICT(scope) DO UPDATE SET revision_id=excluded.revision_id",
                (_scope(project), revision_id),
            )

    def active_blueprint_revision_id(self, project: ProjectRef) -> str | None:
        row = self._connection.execute(
            "SELECT revision_id FROM active_blueprints WHERE scope=?", (_scope(project),)
        ).fetchone()
        return str(row["revision_id"]) if row else None

    def put_convergence(
        self,
        report: ConvergenceReport,
        recommendation: ConvergenceRecommendation,
    ) -> None:
        if report.project is None:
            raise StoreError("cannot persist an unscoped convergence report")
        with self._transaction():
            self._connection.execute(
                "INSERT INTO convergence_reports(scope,report_id,generated_at,report_payload,recommendation_payload) VALUES(?,?,?,?,?)",
                (
                    _scope(report.project),
                    report.report_id,
                    report.generated_at.isoformat(),
                    _dump(report),
                    _dump(recommendation),
                ),
            )

    def latest_convergence(
        self, project: ProjectRef
    ) -> tuple[ConvergenceReport, ConvergenceRecommendation] | None:
        row = self._connection.execute(
            "SELECT report_payload,recommendation_payload FROM convergence_reports WHERE scope=? ORDER BY generated_at DESC,row_id DESC LIMIT 1",
            (_scope(project),),
        ).fetchone()
        if not row:
            return None
        return (
            _load_convergence_report(row["report_payload"]),
            _load_convergence_recommendation(row["recommendation_payload"]),
        )

    def put_research_evidence(self, project: ProjectRef, evidence: Evidence) -> None:
        payload = _dump(evidence)
        existing = self._connection.execute(
            "SELECT payload FROM research_evidence WHERE scope=? AND evidence_id=?",
            (_scope(project), evidence.evidence_id),
        ).fetchone()
        if existing:
            if existing["payload"] != payload:
                raise StoreError(f"immutable research evidence collision: {evidence.evidence_id}")
            return
        with self._transaction():
            self._connection.execute(
                "INSERT INTO research_evidence(scope,evidence_id,retrieved_at,payload) VALUES(?,?,?,?)",
                (_scope(project), evidence.evidence_id, evidence.retrieved_at.isoformat(), payload),
            )

    def research_evidence(self, project: ProjectRef, evidence_id: str) -> Evidence | None:
        row = self._connection.execute(
            "SELECT payload FROM research_evidence WHERE scope=? AND evidence_id=?",
            (_scope(project), evidence_id),
        ).fetchone()
        return _load_research_evidence(row["payload"]) if row else None

    def prune(self, project: ProjectRef, *, keep: int) -> int:
        if keep <= 0:
            raise ValueError("keep must be positive")
        scope = _scope(project)
        rows = self._connection.execute(
            "SELECT revision_id,sequence FROM revisions WHERE scope=? ORDER BY sequence DESC",
            (scope,),
        ).fetchall()
        removable = rows[keep:]
        if not removable:
            return 0
        cutoff = removable[0]["sequence"]
        with self._transaction():
            self._connection.execute(
                "DELETE FROM evidence WHERE scope=? AND revision_sequence<=?", (scope, cutoff)
            )
            self._connection.execute(
                "DELETE FROM nodes WHERE scope=? AND valid_to IS NOT NULL AND valid_to<=?",
                (scope, cutoff),
            )
            self._connection.execute(
                "DELETE FROM edges WHERE scope=? AND valid_to IS NOT NULL AND valid_to<=?",
                (scope, cutoff),
            )
            self._connection.executemany(
                "DELETE FROM delta_log WHERE scope=? AND revision_id=?",
                [(scope, row["revision_id"]) for row in removable],
            )
            self._connection.executemany(
                "DELETE FROM revisions WHERE scope=? AND revision_id=?",
                [(scope, row["revision_id"]) for row in removable],
            )
        return len(removable)

    def export_snapshot(self, project: ProjectRef, path: str | Path) -> None:
        snapshot = self.snapshot(project)
        payload = {
            "format": "extendcodeagent.graph-snapshot.v1",
            "revision": _dump_revision(snapshot.revision) if snapshot.revision else None,
            "nodes": [_dump(item) for item in snapshot.nodes],
            "edges": [_dump(item) for item in snapshot.edges],
            "evidence": [_dump(item) for item in snapshot.evidence],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        envelope = {"content": payload, "sha256": hashlib.sha256(canonical.encode()).hexdigest()}
        Path(path).write_text(
            json.dumps(envelope, sort_keys=True, separators=(",", ":")), encoding="utf-8"
        )

    def import_snapshot(self, project: ProjectRef, path: str | Path) -> GraphRevision:
        envelope = json.loads(Path(path).read_text(encoding="utf-8"))
        content = envelope.get("content")
        if not isinstance(content, dict):
            raise StoreError("invalid snapshot envelope")
        canonical = json.dumps(content, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode()).hexdigest()
        if envelope.get("sha256") != digest:
            raise StoreError("snapshot integrity check failed")
        if content.get("format") != "extendcodeagent.graph-snapshot.v1":
            raise StoreError("unsupported snapshot format")
        revision_payload = content.get("revision")
        if not isinstance(revision_payload, str):
            raise StoreError("snapshot has no revision")
        exported_revision = _load_revision(revision_payload)
        current = self.current_revision(project)
        delta = GraphDelta(
            project,
            exported_revision.source_revision,
            exported_revision.worktree_fingerprint,
            f"import:{digest}",
            exported_revision.analyzer_versions,
            tuple(_load_node(item) for item in content.get("nodes", [])),
            tuple(_load_edge(item) for item in content.get("edges", [])),
            tuple(_load_evidence(item) for item in content.get("evidence", [])),
            expected_revision_id=current.revision_id if current else None,
        )
        return self.apply(delta)

    def _validate_scope(self, delta: GraphDelta) -> None:
        revisions = [item.revision for item in delta.nodes]
        revisions.extend(item.revision for item in delta.edges)
        revisions.extend(item.revision for item in delta.evidence)
        if any(item != delta.source_revision for item in revisions):
            raise StoreError("fact revision does not match delta source revision")

    def _next_sequence(self, scope: str) -> int:
        row = self._connection.execute(
            "SELECT COALESCE(MAX(sequence),0)+1 AS value FROM revisions WHERE scope=?", (scope,)
        ).fetchone()
        return int(row["value"])

    def _sequence(self, project: ProjectRef, revision_id: str) -> int:
        row = self._connection.execute(
            "SELECT sequence FROM revisions WHERE scope=? AND revision_id=?",
            (_scope(project), revision_id),
        ).fetchone()
        if not row:
            raise StoreError(f"revision not found: {revision_id}")
        return int(row["sequence"])

    def _close_current(self, table: str, scope: str, key: str, value: str, sequence: int) -> None:
        self._connection.execute(
            f"UPDATE {table} SET valid_to=?,status='superseded' WHERE scope=? AND {key}=? AND valid_to IS NULL",
            (sequence, scope, value),
        )

    def _invalidate(self, table: str, scope: str, key: str, value: str, sequence: int) -> None:
        self._connection.execute(
            f"UPDATE {table} SET valid_to=?,status='invalidated' WHERE scope=? AND {key}=? AND valid_to IS NULL",
            (sequence, scope, value),
        )

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            yield
        except Exception:
            self._connection.execute("ROLLBACK")
            raise
        self._connection.execute("COMMIT")

    def _migrate(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_meta(version INTEGER NOT NULL);
            INSERT INTO schema_meta(version) SELECT 1 WHERE NOT EXISTS(SELECT 1 FROM schema_meta);
            CREATE TABLE IF NOT EXISTS projects(scope TEXT PRIMARY KEY,project_id TEXT NOT NULL,workspace_id TEXT NOT NULL,head_revision_id TEXT);
            CREATE TABLE IF NOT EXISTS revisions(scope TEXT NOT NULL,revision_id TEXT NOT NULL,sequence INTEGER NOT NULL,parent_revision_id TEXT,payload TEXT NOT NULL,PRIMARY KEY(scope,revision_id),UNIQUE(scope,sequence));
            CREATE TABLE IF NOT EXISTS delta_log(scope TEXT NOT NULL,idempotency_key TEXT NOT NULL,revision_id TEXT NOT NULL,PRIMARY KEY(scope,idempotency_key));
            CREATE TABLE IF NOT EXISTS nodes(row_id INTEGER PRIMARY KEY,scope TEXT NOT NULL,node_id TEXT NOT NULL,canonical_ref TEXT NOT NULL,source_ref TEXT NOT NULL,status TEXT NOT NULL,payload TEXT NOT NULL,valid_from INTEGER NOT NULL,valid_to INTEGER);
            CREATE INDEX IF NOT EXISTS nodes_current_ref ON nodes(scope,canonical_ref,valid_to);
            CREATE INDEX IF NOT EXISTS nodes_source ON nodes(scope,source_ref,valid_to);
            CREATE TABLE IF NOT EXISTS edges(row_id INTEGER PRIMARY KEY,scope TEXT NOT NULL,edge_id TEXT NOT NULL,source_ref TEXT NOT NULL,target_ref TEXT NOT NULL,fact_source_ref TEXT NOT NULL,status TEXT NOT NULL,payload TEXT NOT NULL,valid_from INTEGER NOT NULL,valid_to INTEGER);
            CREATE INDEX IF NOT EXISTS edges_current_id ON edges(scope,edge_id,valid_to);
            CREATE INDEX IF NOT EXISTS edges_reverse ON edges(scope,target_ref,valid_to);
            CREATE INDEX IF NOT EXISTS edges_source ON edges(scope,fact_source_ref,valid_to);
            CREATE TABLE IF NOT EXISTS evidence(row_id INTEGER PRIMARY KEY,scope TEXT NOT NULL,evidence_id TEXT NOT NULL,payload TEXT NOT NULL,revision_sequence INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS runtime_observations(scope TEXT NOT NULL,observation_id TEXT NOT NULL,source_revision TEXT NOT NULL,kind TEXT NOT NULL,status TEXT NOT NULL,finished_at TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(scope,observation_id));
            CREATE INDEX IF NOT EXISTS runtime_observations_revision ON runtime_observations(scope,source_revision,status);
            CREATE TABLE IF NOT EXISTS runtime_observation_refs(scope TEXT NOT NULL,observation_id TEXT NOT NULL,canonical_ref TEXT NOT NULL,PRIMARY KEY(scope,observation_id,canonical_ref),FOREIGN KEY(scope,observation_id) REFERENCES runtime_observations(scope,observation_id) ON DELETE CASCADE);
            CREATE INDEX IF NOT EXISTS runtime_observation_refs_reverse ON runtime_observation_refs(scope,canonical_ref,observation_id);
            CREATE TABLE IF NOT EXISTS blueprint_revisions(scope TEXT NOT NULL,revision_id TEXT NOT NULL,blueprint_id TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(scope,revision_id));
            CREATE INDEX IF NOT EXISTS blueprint_revisions_blueprint ON blueprint_revisions(scope,blueprint_id,created_at);
            CREATE TABLE IF NOT EXISTS active_blueprints(scope TEXT PRIMARY KEY,revision_id TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS convergence_reports(row_id INTEGER PRIMARY KEY,scope TEXT NOT NULL,report_id TEXT NOT NULL,generated_at TEXT NOT NULL,report_payload TEXT NOT NULL,recommendation_payload TEXT NOT NULL,UNIQUE(scope,report_id));
            CREATE INDEX IF NOT EXISTS convergence_reports_latest ON convergence_reports(scope,generated_at,row_id);
            CREATE TABLE IF NOT EXISTS research_evidence(scope TEXT NOT NULL,evidence_id TEXT NOT NULL,retrieved_at TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(scope,evidence_id));
            CREATE INDEX IF NOT EXISTS research_evidence_time ON research_evidence(scope,retrieved_at,evidence_id);
            UPDATE schema_meta SET version=2 WHERE version<2;
            UPDATE schema_meta SET version=3 WHERE version<3;
            UPDATE schema_meta SET version=4 WHERE version<4;
            UPDATE schema_meta SET version=5 WHERE version<5;
            """
        )


def _scope(project: ProjectRef) -> str:
    return f"{project.project_id}\0{project.workspace_id}"


def _dump(value: object) -> str:
    return json.dumps(_json_value(value), sort_keys=True, separators=(",", ":"))


def _json_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _json_value(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_value(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value"):
        return str(value.value)
    return value


def _dump_revision(value: GraphRevision) -> str:
    return _dump(value)


def _source(raw: dict[str, object]) -> SourceRevision:
    return SourceRevision(str(raw["value"]), str(raw["kind"]))


def _project(raw: dict[str, object]) -> ProjectRef:
    return ProjectRef(**raw)  # type: ignore[arg-type]


def _provenance(raw: dict[str, object]) -> Provenance:
    revision = raw.get("source_revision")
    attributes = cast("dict[str, str]", raw.get("attributes", {}))
    return Provenance(
        str(raw["source"]),
        str(raw["producer"]),
        str(raw["producer_version"]),
        _source(revision) if isinstance(revision, dict) else None,
        attributes,
    )


def _confidence(raw: dict[str, object]) -> Confidence:
    return Confidence(float(cast("int | float | str", raw["value"])), str(raw.get("rationale", "")))


def _evidence_ref(raw: dict[str, object]) -> EvidenceRef:
    revision = raw.get("revision")
    return EvidenceRef(
        str(raw["evidence_id"]),
        EvidenceStatus(str(raw["status"])),
        _source(revision) if isinstance(revision, dict) else None,
    )


def _load_research_evidence(payload: str) -> Evidence:
    raw = json.loads(payload)
    return Evidence(
        str(raw["evidence_id"]),
        str(raw["candidate_id"]),
        str(raw["content_hash"]),
        str(raw["summary"]),
        _provenance(raw["provenance"]),
        _confidence(raw["confidence"]),
        datetime.fromisoformat(str(raw["retrieved_at"])),
        EvidenceStatus(str(raw["status"])),
        bool(raw["external"]),
    )


def _load_node(payload: str) -> GraphNode:
    raw = json.loads(payload)
    return GraphNode(
        str(raw["node_id"]),
        CanonicalRef(raw["canonical_ref"]["value"]),
        str(raw["node_type"]),
        str(raw["source_ref"]),
        _provenance(raw["provenance"]),
        _confidence(raw["confidence"]),
        FactStatus(raw["status"]),
        _source(raw["revision"]),
        raw["properties"],
        tuple(_evidence_ref(item) for item in raw["evidence"]),
    )


def _load_edge(payload: str) -> GraphEdge:
    raw = json.loads(payload)
    return GraphEdge(
        str(raw["edge_id"]),
        CanonicalRef(raw["source"]["value"]),
        CanonicalRef(raw["target"]["value"]),
        str(raw["edge_type"]),
        str(raw["source_ref"]),
        _provenance(raw["provenance"]),
        _confidence(raw["confidence"]),
        FactStatus(raw["status"]),
        _source(raw["revision"]),
        raw["properties"],
        tuple(_evidence_ref(item) for item in raw["evidence"]),
    )


def _load_evidence(payload: str) -> GraphEvidence:
    raw = json.loads(payload)
    return GraphEvidence(
        str(raw["evidence_id"]),
        str(raw["evidence_type"]),
        str(raw["source_ref"]),
        _provenance(raw["provenance"]),
        _confidence(raw["confidence"]),
        FactStatus(raw["status"]),
        _source(raw["revision"]),
        str(raw["summary"]),
    )


def _load_revision(payload: str) -> GraphRevision:
    raw = json.loads(payload)
    return GraphRevision(
        str(raw["revision_id"]),
        _project(raw["project"]),
        _source(raw["source_revision"]),
        str(raw["worktree_fingerprint"]),
        raw["analyzer_versions"],
        datetime.fromisoformat(raw["created_at"]),
        raw["parent_revision_id"],
    )


def _load_observation(payload: str) -> RuntimeObservation:
    raw = json.loads(payload)
    return RuntimeObservation(
        str(raw["observation_id"]),
        ObservationKind(raw["kind"]),
        _project(raw["project"]),
        _source(raw["source_revision"]),
        ObservationStatus(raw["status"]),
        datetime.fromisoformat(raw["started_at"]),
        datetime.fromisoformat(raw["finished_at"]),
        _provenance(raw["provenance"]),
        tuple(CanonicalRef(item["value"]) for item in raw["observed_refs"]),
        raw["command"],
        raw["tool"],
        tuple(_evidence_ref(item) for item in raw["artifacts"]),
        str(raw["summary"]),
        raw.get("runtime_session_id"),
        raw.get("runtime_call_id"),
    )


def _load_blueprint_revision(payload: str) -> BlueprintRevision:
    raw = json.loads(payload)
    twin = raw.get("source_twin_revision")
    return BlueprintRevision(
        str(raw["blueprint_id"]),
        str(raw["revision_id"]),
        _project(raw["project"]),
        BlueprintScope(raw["scope"]),
        tuple(
            BlueprintElement(
                str(item["element_id"]),
                CanonicalRef(item["planned_ref"]["value"]),
                str(item["element_type"]),
                bool(item["mandatory"]),
                tuple(CanonicalRef(value["value"]) for value in item["expected_actual_refs"]),
                tuple(str(value) for value in item["acceptance_criteria"]),
                tuple(str(value) for value in item["depends_on_element_ids"]),
                bool(item["requires_verification"]),
            )
            for item in raw["elements"]
        ),
        datetime.fromisoformat(raw["created_at"]),
        BlueprintStatus(raw["status"]),
        raw["parent_revision_id"],
        TwinRevisionRef(str(twin["revision_id"]), _source(twin["source_revision"]))
        if isinstance(twin, dict)
        else None,
    )


def _load_convergence_report(payload: str) -> ConvergenceReport:
    raw = json.loads(payload)
    twin = raw.get("actual_twin_revision")
    project = raw.get("project")
    return ConvergenceReport(
        str(raw["report_id"]),
        _project(project) if isinstance(project, dict) else None,
        raw["target_revision_id"],
        TwinRevisionRef(str(twin["revision_id"]), _source(twin["source_revision"]))
        if isinstance(twin, dict)
        else None,
        tuple(
            ElementConvergence(
                str(item["element_id"]),
                ElementState(item["state"]),
                tuple(CanonicalRef(value["value"]) for value in item["matched_actual_refs"]),
                tuple(CanonicalRef(value["value"]) for value in item["missing_actual_refs"]),
                tuple(_evidence_ref(value) for value in item["evidence"]),
                tuple(str(value) for value in item["diagnostics"]),
            )
            for item in raw["elements"]
        ),
        bool(raw["available"]),
        datetime.fromisoformat(raw["generated_at"]),
        tuple(str(value) for value in raw["diagnostics"]),
        tuple(
            (str(item[0]), tuple(str(value) for value in item[1]))
            for item in raw.get("dependencies", [])
        ),
        bool(raw.get("target_valid", True)),
        bool(raw.get("decision_required", False)),
    )


def _load_convergence_recommendation(payload: str) -> ConvergenceRecommendation:
    raw = json.loads(payload)
    return ConvergenceRecommendation(
        ConvergenceDecision(raw["decision"]),
        tuple(str(value) for value in raw["reason_codes"]),
        tuple(str(value) for value in raw["affected_element_ids"]),
    )
