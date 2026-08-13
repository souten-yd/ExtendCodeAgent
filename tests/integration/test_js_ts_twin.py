from __future__ import annotations

from pathlib import Path

from extendcodeagent.analysis import (
    GraphAnalysisService,
    ImpactQuery,
    JavaScriptTypeScriptCanonicalReferenceResolver,
)
from extendcodeagent.core.contracts import ProjectRef
from extendcodeagent.graph.analyzers import JavaScriptTypeScriptGraphAnalyzer
from extendcodeagent.storage import SqliteGraphStore
from extendcodeagent.twin import TwinService


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _project(root: Path) -> ProjectRef:
    return ProjectRef("p", "w", root.resolve().as_uri())


def test_js_ts_twin_incremental_refresh_and_test_impact(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "src/service.ts", "export function handler() { return true }\n")
    _write(
        root,
        "tests/service.test.ts",
        """import { handler } from '../src/service';
export function testHandler() { return handler() }
""",
    )
    project = _project(root)
    with SqliteGraphStore(tmp_path / "graph.db") as store:
        twin = TwinService(store, analyzer=JavaScriptTypeScriptGraphAnalyzer())
        opened = twin.open(project)
        report = GraphAnalysisService(
            twin.snapshot(project), JavaScriptTypeScriptCanonicalReferenceResolver()
        ).assess_impact(ImpactQuery(("js://src/service.ts#handler",), max_depth=4))
        assert {item.canonical_ref for item in report.recommended_tests} == {
            "js://tests/service.test.ts#testHandler"
        }

        _write(root, "src/service.ts", "export function replacement() { return true }\n")
        refreshed = twin.refresh(project, changed_paths=("src/service.ts",))
        snapshot = twin.snapshot(project)

    assert opened.revision is not None
    assert refreshed.revision is not None
    assert refreshed.revision.parent_revision_id == opened.revision.revision_id
    assert refreshed.affected_paths == ("src/service.ts", "tests/service.test.ts")
    assert not any(
        item.canonical_ref.value == "js://src/service.ts#handler" for item in snapshot.nodes
    )
    assert any(
        item.edge_type == "may_call"
        and item.source.value == "js://tests/service.test.ts#testHandler"
        and item.target.value == "jsname://handler"
        for item in snapshot.edges
    )


def test_js_ts_twin_selects_full_refresh_for_broad_dependency_closure(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "src/core.ts", "export function core() { return true }\n")
    _write(
        root,
        "src/caller.ts",
        "import { core } from './core'; export function caller() { return core() }\n",
    )
    for name in ("one", "two", "three"):
        _write(root, f"src/{name}.ts", f"export function {name}() {{ return true }}\n")

    project = _project(root)
    with SqliteGraphStore(tmp_path / "graph.db") as store:
        twin = TwinService(store, analyzer=JavaScriptTypeScriptGraphAnalyzer())
        twin.open(project)
        refreshed = twin.refresh(project, changed_paths=("src/core.ts",))

    assert refreshed.affected_paths == (
        "src/caller.ts",
        "src/core.ts",
        "src/one.ts",
        "src/three.ts",
        "src/two.ts",
    )
    assert "auto_full_refresh_selected" in {item.code for item in refreshed.diagnostics}
