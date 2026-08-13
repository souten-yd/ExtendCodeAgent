from __future__ import annotations

from pathlib import Path

from extendcodeagent.core.contracts import ProjectRef
from extendcodeagent.graph.analyzers import (
    CompositeGraphAnalyzer,
    JavaScriptTypeScriptGraphAnalyzer,
    PythonGraphAnalyzer,
)
from extendcodeagent.twin.source_snapshot import SourceSnapshotter


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _project(root: Path) -> ProjectRef:
    return ProjectRef("p", "w", root.resolve().as_uri())


def test_js_ts_semantic_facts_resolve_imports_calls_inheritance_and_uncertainty(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "src/helper.ts", "export function helper(value: number) { return value }\n")
    _write(
        root,
        "src/service.ts",
        """import { helper as runHelper } from './helper';
class Base { save() { return true } }
@sealed
export class Service extends Base {
  @route('/items')
  handler(value: number) {
    runHelper(value)
    this.save()
    client.unknown(value)
  }
}
""",
    )
    source = SourceSnapshotter().snapshot(_project(root))

    first = JavaScriptTypeScriptGraphAnalyzer().analyze(_project(root), source)
    second = JavaScriptTypeScriptGraphAnalyzer().analyze(_project(root), source)
    nodes = {(item.node_type, item.canonical_ref.value) for item in first.nodes}
    edges = {
        (item.edge_type, item.source.value, item.target.value, item.confidence.value)
        for item in first.edges
    }

    assert first == second
    assert ("module", "module://src/service.ts") in nodes
    assert ("function", "js://src/helper.ts#helper") in nodes
    assert ("class", "js://src/service.ts#Service") in nodes
    assert ("method", "js://src/service.ts#Service.handler") in nodes
    assert ("imports", "module://src/service.ts", "module://src/helper.ts", 1.0) in edges
    assert (
        "calls",
        "js://src/service.ts#Service.handler",
        "js://src/helper.ts#helper",
        1.0,
    ) in edges
    assert (
        "calls",
        "js://src/service.ts#Service.handler",
        "js://src/service.ts#Base.save",
        0.9,
    ) in edges
    assert (
        "may_call",
        "js://src/service.ts#Service.handler",
        "jsname://unknown",
        0.35,
    ) in edges
    assert (
        "inherits",
        "js://src/service.ts#Service",
        "js://src/service.ts#Base",
        1.0,
    ) in edges
    assert any(item[0] == "decorated_by" for item in edges)


def test_ts_test_definition_and_call_are_impact_reachable(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(
        root,
        "src/service.ts",
        "export class Service { handler() { return true } }\n",
    )
    _write(
        root,
        "tests/service.test.ts",
        """import { Service } from '../src/service';
export function testService() {
  const service = new Service()
  return service.handler()
}
""",
    )
    result = JavaScriptTypeScriptGraphAnalyzer().analyze(
        _project(root), SourceSnapshotter().snapshot(_project(root))
    )

    assert any(
        item.node_type == "test" and item.canonical_ref.value.endswith("#testService")
        for item in result.nodes
    )
    assert any(
        item.edge_type == "calls"
        and item.source.value.endswith("#testService")
        and item.target.value == "js://src/service.ts#Service.handler"
        for item in result.edges
    )


def test_js_ts_parse_failure_is_truthful_and_composite_keeps_python(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "broken.ts", "export function broken( {\n")
    _write(root, "ok.py", "def usable():\n    return 1\n")
    source = SourceSnapshotter().snapshot(_project(root))
    analyzer = CompositeGraphAnalyzer((PythonGraphAnalyzer(), JavaScriptTypeScriptGraphAnalyzer()))
    result = analyzer.analyze(_project(root), source)

    assert any(item.canonical_ref.value == "file://broken.ts" for item in result.nodes)
    assert any(item.canonical_ref.value == "py://ok#usable" for item in result.nodes)
    assert any(item.code == "javascript_typescript_parse_error" for item in result.diagnostics)
    assert dict(result.analyzer_versions).keys() >= {"python_ast", "javascript_typescript"}


def test_same_name_js_functions_are_not_collapsed(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "a.js", "export function handler() { return 1 }\n")
    _write(root, "b.ts", "export function handler(): number { return 2 }\n")
    result = JavaScriptTypeScriptGraphAnalyzer().analyze(
        _project(root), SourceSnapshotter().snapshot(_project(root))
    )
    refs = {item.canonical_ref.value for item in result.nodes if item.node_type == "function"}
    assert {"js://a.js#handler", "js://b.ts#handler"} <= refs


def test_playwright_inline_test_callback_is_a_test_definition(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "src/service.ts", "export function save() { return true }\n")
    _write(
        root,
        "tests/service.spec.ts",
        """import { save } from '../src/service';
test('saves the record', async () => { save() });
""",
    )
    result = JavaScriptTypeScriptGraphAnalyzer().analyze(
        _project(root), SourceSnapshotter().snapshot(_project(root))
    )

    test_ref = "js://tests/service.spec.ts#test@2"
    assert any(
        node.canonical_ref.value == test_ref and node.node_type == "test" for node in result.nodes
    )
    assert any(
        edge.source.value == test_ref
        and edge.target.value == "js://src/service.ts#save"
        and edge.edge_type == "calls"
        for edge in result.edges
    )
