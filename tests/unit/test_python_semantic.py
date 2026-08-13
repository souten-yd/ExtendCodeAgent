from __future__ import annotations

from pathlib import Path

from extendcodeagent.core.contracts import ProjectRef
from extendcodeagent.graph.analyzers.python import PythonGraphAnalyzer
from extendcodeagent.twin.source_snapshot import SourceSnapshotter


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_structural_and_python_semantic_facts_are_deterministic(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "pkg/__init__.py", "from .service import handler\n")
    _write(
        root,
        "pkg/service.py",
        """from framework import route
from pkg.util import helper as run_helper

class Base:
    def save(self):
        return None

class Service(Base):
    @route('/items')
    def handler(self, value):
        selected = run_helper
        run_helper(value)
        self.save()
        client.unknown(value)
        return value
""",
    )
    _write(root, "pkg/util.py", "def helper(value):\n    return value\n")
    _write(root, "tests/test_service.py", "def test_handler():\n    assert True\n")
    project = ProjectRef("p", "w", root.resolve().as_uri())
    source = SourceSnapshotter().snapshot(project)

    first = PythonGraphAnalyzer().analyze(project, source)
    second = PythonGraphAnalyzer().analyze(project, source)
    nodes = {(node.node_type, node.canonical_ref.value) for node in first.nodes}
    edges = {
        (edge.edge_type, edge.source.value, edge.target.value, edge.confidence.value)
        for edge in first.edges
    }

    assert first.nodes == second.nodes
    assert first.edges == second.edges
    assert ("repository", "repo://p/w") in nodes
    assert ("directory", "dir://pkg") in nodes
    assert ("module", "module://pkg.service") in nodes
    assert ("class", "py://pkg.service#Service") in nodes
    assert ("method", "py://pkg.service#Service.handler") in nodes
    assert ("test", "py://tests.test_service#test_handler") in nodes
    assert ("dependency", "dependency://framework") in nodes
    assert ("imports", "module://pkg.service", "dependency://framework", 1.0) in edges
    assert ("depends_on", "module://pkg.service", "dependency://framework", 1.0) in edges
    assert ("inherits", "py://pkg.service#Service", "py://pkg.service#Base", 1.0) in edges
    assert (
        "calls",
        "py://pkg.service#Service.handler",
        "py://pkg.util#helper",
        1.0,
    ) in edges
    assert (
        "calls",
        "py://pkg.service#Service.handler",
        "py://pkg.service#Base.save",
        0.9,
    ) in edges
    assert (
        "may_call",
        "py://pkg.service#Service.handler",
        "pyname://unknown",
        0.35,
    ) in edges
    assert (
        "references",
        "py://pkg.service#Service.handler",
        "py://pkg.util#helper",
        0.9,
    ) in edges
    assert (
        "decorated_by",
        "py://pkg.service#Service.handler",
        "py://framework#route",
        1.0,
    ) in edges


def test_parse_failure_is_truthful_and_preserves_structural_file(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "broken.py", "def broken(:\n")
    project = ProjectRef("p", "w", root.resolve().as_uri())
    result = PythonGraphAnalyzer().analyze(project, SourceSnapshotter().snapshot(project))

    assert any(node.canonical_ref.value == "file://broken.py" for node in result.nodes)
    assert any(diagnostic.code == "python_parse_error" for diagnostic in result.diagnostics)
