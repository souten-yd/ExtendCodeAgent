"""Atomic SQLite persistence for immutable graph revisions."""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import fields, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import cast

from extendcodeagent.core.contracts import (
    CanonicalRef,
    Confidence,
    EvidenceRef,
    EvidenceStatus,
    ProjectRef,
    Provenance,
    SourceRevision,
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

SCHEMA_VERSION = 1


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
        Path(path).write_text(
            json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8"
        )

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
            CREATE INDEX IF NOT EXISTS edges_reverse ON edges(scope,target_ref,valid_to);
            CREATE INDEX IF NOT EXISTS edges_source ON edges(scope,fact_source_ref,valid_to);
            CREATE TABLE IF NOT EXISTS evidence(row_id INTEGER PRIMARY KEY,scope TEXT NOT NULL,evidence_id TEXT NOT NULL,payload TEXT NOT NULL,revision_sequence INTEGER NOT NULL);
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
