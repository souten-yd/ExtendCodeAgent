from __future__ import annotations

from pathlib import Path

from extendcodeagent.analysis import (
    GraphAnalysisService,
    ImpactQuery,
    PythonCanonicalReferenceResolver,
)
from extendcodeagent.core.contracts import ProjectRef
from extendcodeagent.graph.analyzers import PythonGraphAnalyzer
from extendcodeagent.storage import SqliteGraphStore
from extendcodeagent.twin import TwinReadiness, TwinService


def _project(root: Path, workspace: str = "w1") -> ProjectRef:
    return ProjectRef("p1", workspace, root.resolve().as_uri())


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_full_build_and_unchanged_reopen_reuse_revision(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "a.py", "a = 1\n")
    _write(root, "b.py", "b = 2\n")
    with SqliteGraphStore(tmp_path / "graph.db") as store:
        twin = TwinService(store)
        first = twin.open(_project(root))
        reopened = twin.open(_project(root))
        assert first.readiness is TwinReadiness.READY
        assert first.revision == reopened.revision
        assert {node.source_ref for node in twin.snapshot(_project(root)).nodes} == {"a.py", "b.py"}


def test_incremental_refresh_preserves_unaffected_file_and_history(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "a.py", "a = 1\n")
    _write(root, "b.py", "b = 2\n")
    with SqliteGraphStore(tmp_path / "graph.db") as store:
        twin = TwinService(store)
        first = twin.open(_project(root))
        _write(root, "a.py", "a = 99\n")
        refreshed = twin.refresh(_project(root), changed_paths=("a.py",))
        current = twin.snapshot(_project(root))
        historical = twin.snapshot(_project(root), first.revision.revision_id)  # type: ignore[union-attr]
        assert refreshed.revision != first.revision
        assert {node.source_ref for node in current.nodes} == {"a.py", "b.py"}
        assert (
            next(node for node in historical.nodes if node.source_ref == "a.py").properties
            != next(node for node in current.nodes if node.source_ref == "a.py").properties
        )


def test_deleted_file_is_invalidated(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "a.py", "a = 1\n")
    with SqliteGraphStore(tmp_path / "graph.db") as store:
        twin = TwinService(store)
        twin.open(_project(root))
        (root / "a.py").unlink()
        result = twin.refresh(_project(root), changed_paths=("a.py",))
        assert result.invalidation_count == 1
        assert twin.snapshot(_project(root)).nodes == ()


def test_conflict_is_degraded_and_prior_head_survives(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "a.py", "a = 1\n")
    with SqliteGraphStore(tmp_path / "graph.db") as store:
        twin = TwinService(store)
        first = twin.open(_project(root))
        _write(root, "a.py", "a = 2\n")
        failed = twin.refresh(_project(root), changed_paths=("a.py",), expected_revision_id="stale")
        assert failed.readiness is TwinReadiness.DEGRADED
        assert failed.revision == first.revision
        assert store.current_revision(_project(root)) == first.revision


def test_restart_and_workspace_isolation(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "a.py", "a = 1\n")
    database = tmp_path / "graph.db"
    first_store = SqliteGraphStore(database)
    first = TwinService(first_store).open(_project(root))
    TwinService(first_store).open(_project(root, "w2"))
    first_store.close()
    with SqliteGraphStore(database) as reopened:
        assert reopened.current_revision(_project(root)) == first.revision
        assert reopened.current_revision(_project(root, "w2")) != first.revision


def test_python_facts_persist_and_changed_file_symbols_are_invalidated(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "service.py", "def old_name():\n    return 1\n")
    database = tmp_path / "graph.db"
    with SqliteGraphStore(database) as store:
        twin = TwinService(store, analyzer=PythonGraphAnalyzer())
        opened = twin.open(_project(root))
        assert opened.readiness is TwinReadiness.READY
        assert any(
            node.canonical_ref.value == "py://service#old_name"
            for node in twin.snapshot(_project(root)).nodes
        )
    with SqliteGraphStore(database) as store:
        twin = TwinService(store, analyzer=PythonGraphAnalyzer())
        reopened = twin.open(_project(root))
        assert reopened.revision == opened.revision
        _write(root, "service.py", "def new_name():\n    return 2\n")
        refreshed = twin.refresh(_project(root), changed_paths=("service.py",))
        refs = {node.canonical_ref.value for node in twin.snapshot(_project(root)).nodes}
        assert refreshed.readiness is TwinReadiness.READY
        assert "py://service#old_name" not in refs
        assert "py://service#new_name" in refs


def test_semantic_refresh_reanalyzes_dependent_importers(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "util.py", "def helper():\n    return 1\n")
    _write(root, "service.py", "from util import helper\n\ndef caller():\n    return helper()\n")
    with SqliteGraphStore(tmp_path / "graph.db") as store:
        twin = TwinService(store, analyzer=PythonGraphAnalyzer())
        twin.open(_project(root))
        _write(root, "util.py", "def replacement():\n    return 2\n")
        result = twin.refresh(_project(root), changed_paths=("util.py",))
        snapshot = twin.snapshot(_project(root))
        assert result.affected_paths == ("service.py", "util.py")
        assert not any(
            edge.edge_type == "calls" and edge.target.value == "py://util#helper"
            for edge in snapshot.edges
        )
        assert any(
            edge.edge_type == "may_call"
            and edge.source.value == "py://service#caller"
            and edge.target.value == "pyname://helper"
            for edge in snapshot.edges
        )


def test_persisted_semantic_graph_drives_impact_and_test_candidates(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "service.py", "def leaf():\n    return 1\n\ndef caller():\n    return leaf()\n")
    _write(
        root,
        "test_service.py",
        "from service import caller\n\ndef test_caller():\n    assert caller() == 1\n",
    )
    _write(
        root,
        "plugin.py",
        "def dynamic(client):\n    return client.leaf()\n",
    )
    with SqliteGraphStore(tmp_path / "graph.db") as store:
        twin = TwinService(store, analyzer=PythonGraphAnalyzer())
        twin.open(_project(root))
        report = GraphAnalysisService(
            twin.snapshot(_project(root)), PythonCanonicalReferenceResolver()
        ).assess_impact(ImpactQuery(("py://service#leaf",), max_depth=4))

    impacted = report.direct_impacts + report.transitive_impacts
    assert any(item.canonical_ref == "py://service#caller" for item in impacted)
    assert {item.canonical_ref for item in report.recommended_tests} == {
        "py://test_service#test_caller"
    }
    dynamic = next(item for item in impacted if item.canonical_ref == "py://plugin#dynamic")
    assert dynamic.status.value == "inferred"
    assert dynamic.path_confidence == 0.35
