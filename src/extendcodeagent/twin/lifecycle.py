"""Digital Twin full and file-level refresh lifecycle."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum

from extendcodeagent.core.contracts import (
    CanonicalRef,
    Confidence,
    Diagnostic,
    ProjectRef,
    Provenance,
)
from extendcodeagent.graph import (
    FactStatus,
    GraphDelta,
    GraphEdge,
    GraphNode,
    GraphRevision,
    GraphSnapshot,
)
from extendcodeagent.graph.analyzers import GraphAnalyzer
from extendcodeagent.storage import RevisionConflict, SqliteGraphStore

from .source_snapshot import SourceFileSnapshot, SourceSnapshot, SourceSnapshotter


class TwinReadiness(StrEnum):
    ABSENT = "absent"
    READY = "ready"
    DEGRADED = "degraded"


@dataclass(frozen=True, slots=True)
class TwinRefreshResult:
    readiness: TwinReadiness
    revision: GraphRevision | None
    previous_revision_id: str | None
    changed_node_count: int = 0
    invalidation_count: int = 0
    affected_paths: tuple[str, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()


class TwinService:
    """Coordinates source snapshots, optional analysis, and durable graph revisions."""

    def __init__(
        self,
        store: SqliteGraphStore,
        snapshotter: SourceSnapshotter | None = None,
        analyzer: GraphAnalyzer | None = None,
    ) -> None:
        self.store = store
        self.snapshotter = snapshotter or SourceSnapshotter()
        self.analyzer = analyzer

    def open(self, project: ProjectRef) -> TwinRefreshResult:
        source = self.snapshotter.snapshot(project)
        current = self.store.current_revision(project)
        expected_versions = dict(source.analyzer_versions)
        if self.analyzer is not None:
            expected_versions.update(self.analyzer.analyzer_versions)
        if current and _matches(current, source, expected_versions):
            return TwinRefreshResult(TwinReadiness.READY, current, current.revision_id)
        return self._apply(
            project,
            source,
            full=True,
            expected_revision_id=current.revision_id if current else None,
        )

    def refresh(
        self,
        project: ProjectRef,
        *,
        changed_paths: tuple[str, ...] = (),
        expected_revision_id: str | None = None,
        full: bool = False,
    ) -> TwinRefreshResult:
        current = self.store.current_revision(project)
        source = self.snapshotter.snapshot(project, changed_paths=None if full else changed_paths)
        return self._apply(
            project,
            source,
            full=full or current is None,
            expected_revision_id=expected_revision_id
            if expected_revision_id is not None
            else (current.revision_id if current else None),
        )

    def snapshot(self, project: ProjectRef, revision_id: str | None = None) -> GraphSnapshot:
        return self.store.snapshot(project, revision_id)

    def _apply(
        self,
        project: ProjectRef,
        source: SourceSnapshot,
        *,
        full: bool,
        expected_revision_id: str | None,
    ) -> TwinRefreshResult:
        current = self.store.current_revision(project)
        previous_id = current.revision_id if current else None
        paths = tuple(item.path for item in source.files) if full else source.changed_paths
        previous_snapshot = (
            self.store.snapshot(project) if current else GraphSnapshot(project, None)
        )
        if self.analyzer is not None and not full:
            paths = _dependent_paths(previous_snapshot, paths, source)
        selected = {item.path: item for item in source.files if item.path in set(paths)}
        node_by_ref = {
            f"file://{item.path}": _file_node(project, source, item) for item in selected.values()
        }
        edges: tuple[GraphEdge, ...] = ()
        analyzer_versions = dict(source.analyzer_versions)
        diagnostics = list(source.diagnostics)
        if self.analyzer is not None:
            analysis = self.analyzer.analyze(project, source, paths=None if full else paths)
            node_by_ref.update({item.canonical_ref.value: item for item in analysis.nodes})
            edges = analysis.edges
            analyzer_versions.update(analysis.analyzer_versions)
            diagnostics.extend(analysis.diagnostics)
        nodes = tuple(node_by_ref[key] for key in sorted(node_by_ref))
        generated_node_ids = {node.node_id for node in nodes}
        invalidations = tuple(
            node.node_id
            for node in previous_snapshot.nodes
            if (full or node.source_ref in paths) and node.node_id not in generated_node_ids
        )
        generated_edge_ids = {edge.edge_id for edge in edges}
        edge_invalidations = tuple(
            edge.edge_id
            for edge in previous_snapshot.edges
            if (full or edge.source_ref in paths) and edge.edge_id not in generated_edge_ids
        )
        key_payload = "\n".join(
            [
                source.worktree_fingerprint,
                "full" if full else "incremental",
                *(f"{key}:{value}" for key, value in sorted(analyzer_versions.items())),
                *sorted(paths),
            ]
        )
        delta = GraphDelta(
            project,
            source.source_revision,
            source.worktree_fingerprint,
            hashlib.sha256(key_payload.encode()).hexdigest(),
            analyzer_versions,
            nodes,
            edges,
            invalidate_node_ids=invalidations,
            invalidate_edge_ids=edge_invalidations,
            expected_revision_id=expected_revision_id,
        )
        try:
            revision = self.store.apply(delta)
        except RevisionConflict as exc:
            return TwinRefreshResult(
                TwinReadiness.DEGRADED,
                current,
                previous_id,
                affected_paths=paths,
                diagnostics=(Diagnostic("stale_twin_revision", str(exc)),),
            )
        return TwinRefreshResult(
            TwinReadiness.READY,
            revision,
            previous_id,
            len(nodes),
            len(invalidations) + len(edge_invalidations),
            paths,
            tuple(diagnostics),
        )


def _matches(
    revision: GraphRevision, source: SourceSnapshot, analyzer_versions: dict[str, str]
) -> bool:
    return (
        revision.source_revision == source.source_revision
        and revision.worktree_fingerprint == source.worktree_fingerprint
        and dict(revision.analyzer_versions) == analyzer_versions
    )


def _dependent_paths(
    snapshot: GraphSnapshot, changed_paths: tuple[str, ...], source: SourceSnapshot
) -> tuple[str, ...]:
    affected = set(changed_paths)
    available = {item.path for item in source.files}
    nodes_by_ref = {node.canonical_ref.value: node for node in snapshot.nodes}
    while True:
        affected_refs = {
            node.canonical_ref.value for node in snapshot.nodes if node.source_ref in affected
        }
        dependents = {
            nodes_by_ref[edge.source.value].source_ref
            for edge in snapshot.edges
            if edge.target.value in affected_refs
            and edge.source.value in nodes_by_ref
            and nodes_by_ref[edge.source.value].source_ref in available
        }
        additions = dependents - affected
        if not additions:
            return tuple(sorted(affected))
        affected.update(additions)


def _file_node(
    project: ProjectRef, snapshot: SourceSnapshot, item: SourceFileSnapshot
) -> GraphNode:
    node_id = hashlib.sha256(
        f"{project.project_id}\0{project.workspace_id}\0{item.path}".encode()
    ).hexdigest()
    return GraphNode(
        node_id,
        CanonicalRef(f"file://{item.path}"),
        "file",
        item.path,
        Provenance("source_snapshot", "source_snapshot", "v1", snapshot.source_revision),
        Confidence(1.0, "content hash observed"),
        FactStatus.DECLARED,
        snapshot.source_revision,
        {"size": item.size, "content_hash": item.content_hash},
    )
