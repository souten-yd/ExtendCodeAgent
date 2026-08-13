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
from extendcodeagent.graph import FactStatus, GraphDelta, GraphNode, GraphRevision, GraphSnapshot
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
    """Coordinates source snapshots and durable graph revisions without semantic analysis."""

    def __init__(
        self, store: SqliteGraphStore, snapshotter: SourceSnapshotter | None = None
    ) -> None:
        self.store = store
        self.snapshotter = snapshotter or SourceSnapshotter()

    def open(self, project: ProjectRef) -> TwinRefreshResult:
        source = self.snapshotter.snapshot(project)
        current = self.store.current_revision(project)
        if current and _matches(current, source):
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
        selected = {item.path: item for item in source.files if item.path in set(paths)}
        nodes = tuple(_file_node(project, source, item) for item in selected.values())
        existing = self.store.snapshot(project).nodes if current else ()
        active_in_scope = {
            node.source_ref: node for node in existing if full or node.source_ref in paths
        }
        invalidations = tuple(
            node.node_id for path, node in active_in_scope.items() if path not in selected
        )
        key_payload = "\n".join(
            [source.worktree_fingerprint, "full" if full else "incremental", *sorted(paths)]
        )
        delta = GraphDelta(
            project,
            source.source_revision,
            source.worktree_fingerprint,
            hashlib.sha256(key_payload.encode()).hexdigest(),
            dict(source.analyzer_versions),
            nodes,
            invalidate_node_ids=invalidations,
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
            len(invalidations),
            paths,
            source.diagnostics,
        )


def _matches(revision: GraphRevision, source: SourceSnapshot) -> bool:
    return (
        revision.source_revision == source.source_revision
        and revision.worktree_fingerprint == source.worktree_fingerprint
        and dict(revision.analyzer_versions) == dict(source.analyzer_versions)
    )


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
