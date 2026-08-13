from __future__ import annotations

from extendcodeagent.analysis import (
    GraphAnalysisService,
    ImpactQuery,
    PathQuery,
    PythonCanonicalReferenceResolver,
)
from extendcodeagent.core.contracts import (
    CanonicalRef,
    Confidence,
    ProjectRef,
    Provenance,
    SourceRevision,
)
from extendcodeagent.graph import (
    FactStatus,
    GraphEdge,
    GraphNode,
    GraphRevision,
    GraphSnapshot,
)


def _node(ref: str, kind: str, *, confidence: float = 1.0) -> GraphNode:
    revision = SourceRevision("source")
    return GraphNode(
        ref,
        CanonicalRef(ref),
        kind,
        "fixture.py",
        Provenance("fixture", "ground_truth", "v1", revision),
        Confidence(confidence),
        FactStatus.DECLARED,
        revision,
    )


def _edge(
    source: str,
    target: str,
    kind: str,
    *,
    confidence: float = 1.0,
    status: FactStatus = FactStatus.DECLARED,
) -> GraphEdge:
    revision = SourceRevision("source")
    return GraphEdge(
        f"{source}|{kind}|{target}",
        CanonicalRef(source),
        CanonicalRef(target),
        kind,
        "fixture.py",
        Provenance("fixture", "ground_truth", "v1", revision),
        Confidence(confidence),
        status,
        revision,
    )


def _snapshot() -> GraphSnapshot:
    project = ProjectRef("p", "w", "file:///fixture")
    source = SourceRevision("source")
    refs = (
        ("py://app.service#leaf", "function", 1.0),
        ("py://app.service#caller", "function", 1.0),
        ("py://app.api#handler", "function", 1.0),
        ("route://GET/items", "api_route", 1.0),
        ("effect://db/items/write", "side_effect", 1.0),
        ("test://tests/test_service.py::test_caller", "test", 1.0),
        ("requirement://items-persist", "requirement", 1.0),
        ("risk://items-regression", "risk", 0.8),
        ("pyname://leaf", "symbol_alias", 0.35),
        ("py://plugin#dynamic_caller", "function", 0.8),
    )
    edges = (
        _edge("py://app.service#caller", "py://app.service#leaf", "calls"),
        _edge("py://app.api#handler", "py://app.service#caller", "calls", confidence=0.8),
        _edge("route://GET/items", "py://app.api#handler", "handled_by"),
        _edge("py://app.api#handler", "effect://db/items/write", "performs_side_effect"),
        _edge("test://tests/test_service.py::test_caller", "py://app.service#caller", "tests"),
        _edge("requirement://items-persist", "py://app.api#handler", "requires"),
        _edge("risk://items-regression", "py://app.service#leaf", "associated_with"),
        _edge(
            "py://plugin#dynamic_caller",
            "pyname://leaf",
            "may_call",
            confidence=0.35,
            status=FactStatus.INFERRED,
        ),
    )
    return GraphSnapshot(
        project,
        GraphRevision("r1", project, source, "tree", {"fixture": "v1"}),
        tuple(_node(ref, kind, confidence=confidence) for ref, kind, confidence in refs),
        edges,
    )


def test_path_is_bounded_filtered_and_uses_weakest_link_confidence() -> None:
    service = GraphAnalysisService(_snapshot(), PythonCanonicalReferenceResolver())
    result = service.trace_path(
        PathQuery(
            "route://GET/items",
            "effect://db/items/write",
            allowed_edge_types=("handled_by", "performs_side_effect"),
            max_depth=2,
            max_paths=2,
        )
    )

    assert len(result.paths) == 1
    assert result.paths[0].node_refs == (
        "route://GET/items",
        "py://app.api#handler",
        "effect://db/items/write",
    )
    assert result.paths[0].min_confidence == 1.0
    assert not result.truncated


def test_impact_reports_direct_transitive_tests_effects_and_history() -> None:
    service = GraphAnalysisService(_snapshot(), PythonCanonicalReferenceResolver())
    report = service.assess_impact(
        ImpactQuery(("py://app.service#leaf",), max_depth=4, include_historical=True)
    )
    direct = {item.canonical_ref for item in report.direct_impacts}
    transitive = {item.canonical_ref for item in report.transitive_impacts}

    assert "py://app.service#caller" in direct
    assert "py://app.api#handler" in transitive
    assert {item.canonical_ref for item in report.recommended_tests} == {
        "test://tests/test_service.py::test_caller"
    }
    assert {item.canonical_ref for item in report.side_effects} == {"effect://db/items/write"}
    assert {item.canonical_ref for item in report.affected_requirements} == {
        "requirement://items-persist"
    }
    assert {item.canonical_ref for item in report.historical_risks} == {"risk://items-regression"}
    caller = next(
        item for item in report.transitive_impacts if item.canonical_ref == "py://app.api#handler"
    )
    assert caller.path_confidence == 0.8


def test_ambiguous_alias_is_inferred_and_exposed_as_uncertainty() -> None:
    service = GraphAnalysisService(_snapshot(), PythonCanonicalReferenceResolver())
    report = service.assess_impact(ImpactQuery(("py://app.service#leaf",), max_depth=2))

    impacted = report.direct_impacts + report.transitive_impacts
    assert any(item.canonical_ref == "py://plugin#dynamic_caller" for item in impacted)
    uncertain = {item.canonical_ref: item for item in report.uncertainty}
    assert uncertain["py://plugin#dynamic_caller"].path_confidence == 0.35
    assert uncertain["py://plugin#dynamic_caller"].status is FactStatus.INFERRED


def test_route_change_forward_expands_to_handler_and_db_effect() -> None:
    service = GraphAnalysisService(_snapshot(), PythonCanonicalReferenceResolver())
    report = service.assess_impact(ImpactQuery(("route://GET/items",), max_depth=3))

    assert any(
        item.canonical_ref == "py://app.api#handler" and item.reason == "implements_changed_entity"
        for item in report.direct_impacts
    )
    assert {item.canonical_ref for item in report.side_effects} == {"effect://db/items/write"}


def test_missing_path_and_strict_confidence_are_truthful() -> None:
    service = GraphAnalysisService(_snapshot(), PythonCanonicalReferenceResolver())
    path = service.trace_path(PathQuery("py://app.service#leaf", "missing://target"))
    impact = service.assess_impact(
        ImpactQuery(("py://app.service#leaf",), max_depth=2, min_confidence=0.7)
    )

    assert path.paths == ()
    assert path.diagnostics[0].code == "no_path_found"
    assert all(
        item.canonical_ref != "py://plugin#dynamic_caller" for item in impact.transitive_impacts
    )
