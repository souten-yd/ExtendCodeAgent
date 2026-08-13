from __future__ import annotations

from pathlib import Path

import pytest

from extendcodeagent.core.contracts import (
    CanonicalRef,
    Confidence,
    ProjectRef,
    Provenance,
    SourceRevision,
)
from extendcodeagent.graph import FactStatus, GraphDelta, GraphEdge, GraphNode
from extendcodeagent.storage import RevisionConflict, SqliteGraphStore, StoreError


def _project(workspace: str = "w1") -> ProjectRef:
    return ProjectRef("p1", workspace, "file:///repo")


def _node(source: SourceRevision, *, label: str = "app.py") -> GraphNode:
    return GraphNode(
        "n1",
        CanonicalRef("file://app.py"),
        "file",
        "app.py",
        Provenance("static", "snapshot", "v1", source),
        Confidence(1),
        FactStatus.DECLARED,
        source,
        {"label": label},
    )


def _edge(source: SourceRevision) -> GraphEdge:
    return GraphEdge(
        "e1",
        CanonicalRef("file://app.py"),
        CanonicalRef("file://test.py"),
        "depends_on",
        "app.py",
        Provenance("static", "snapshot", "v1", source),
        Confidence(1),
        FactStatus.DECLARED,
        source,
    )


def _delta(
    key: str,
    *,
    project: ProjectRef | None = None,
    source: str = "s1",
    expected: str | None = None,
    label: str = "app.py",
) -> GraphDelta:
    revision = SourceRevision(source)
    return GraphDelta(
        project or _project(),
        revision,
        f"work-{source}",
        key,
        {"snapshot": "v1"},
        (_node(revision, label=label),),
        (_edge(revision),),
        expected_revision_id=expected,
    )


def test_apply_is_idempotent_and_historical_revisions_are_immutable() -> None:
    with SqliteGraphStore(":memory:") as store:
        first = store.apply(_delta("one", label="v1"))
        assert store.apply(_delta("one", label="ignored")) == first
        second = store.apply(_delta("two", source="s2", expected=first.revision_id, label="v2"))
        assert second.parent_revision_id == first.revision_id
        assert store.snapshot(_project(), first.revision_id).nodes[0].properties["label"] == "v1"
        assert store.snapshot(_project()).nodes[0].properties["label"] == "v2"


def test_expected_revision_conflict_keeps_current_head() -> None:
    with SqliteGraphStore(":memory:") as store:
        first = store.apply(_delta("one"))
        with pytest.raises(RevisionConflict):
            store.apply(_delta("two", source="s2", expected="stale"))
        assert store.current_revision(_project()) == first


def test_workspace_isolation_and_reverse_index() -> None:
    with SqliteGraphStore(":memory:") as store:
        store.apply(_delta("w1"))
        store.apply(_delta("w2", project=_project("w2")))
        assert len(store.snapshot(_project()).nodes) == 1
        assert len(store.snapshot(_project("w2")).nodes) == 1
        assert [
            edge.edge_id for edge in store.reverse_edges(_project(), CanonicalRef("file://test.py"))
        ] == ["e1"]


def test_restart_persistence_and_export(tmp_path: Path) -> None:
    database = tmp_path / "graph.db"
    store = SqliteGraphStore(database)
    revision = store.apply(_delta("one"))
    store.close()
    reopened = SqliteGraphStore(database)
    assert reopened.current_revision(_project()) == revision
    output = tmp_path / "snapshot.json"
    reopened.export_snapshot(_project(), output)
    assert "extendcodeagent.graph-snapshot.v1" in output.read_text(encoding="utf-8")
    reopened.close()

    imported = SqliteGraphStore(tmp_path / "imported.db")
    imported.import_snapshot(_project(), output)
    assert imported.snapshot(_project()).nodes[0].canonical_ref == CanonicalRef("file://app.py")
    imported.close()


def test_import_rejects_corrupt_snapshot(tmp_path: Path) -> None:
    output = tmp_path / "snapshot.json"
    with SqliteGraphStore(":memory:") as store:
        store.apply(_delta("one"))
        store.export_snapshot(_project(), output)
        output.write_text(
            output.read_text(encoding="utf-8").replace("app.py", "bad.py"), encoding="utf-8"
        )
        with pytest.raises(StoreError, match="integrity"):
            SqliteGraphStore(":memory:").import_snapshot(_project(), output)


def test_retention_prunes_closed_history_but_keeps_recent_revisions() -> None:
    with SqliteGraphStore(":memory:") as store:
        first = store.apply(_delta("one", label="v1"))
        second = store.apply(_delta("two", source="s2", expected=first.revision_id, label="v2"))
        store.apply(_delta("three", source="s3", expected=second.revision_id, label="v3"))
        assert store.prune(_project(), keep=2) == 1
        with pytest.raises(StoreError, match="revision not found"):
            store.get_revision(_project(), first.revision_id)
        assert store.snapshot(_project()).nodes[0].properties["label"] == "v3"


def test_fact_revision_mismatch_rolls_back_atomically() -> None:
    delta = _delta("bad")
    bad = GraphDelta(
        delta.project,
        SourceRevision("other"),
        delta.worktree_fingerprint,
        delta.idempotency_key,
        delta.analyzer_versions,
        delta.nodes,
    )
    with SqliteGraphStore(":memory:") as store:
        with pytest.raises(StoreError):
            store.apply(bad)
        assert store.current_revision(_project()) is None
