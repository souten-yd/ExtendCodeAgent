from __future__ import annotations

from extendcodeagent.analysis import GraphAnalysisService, ImpactQuery
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
from extendcodeagent.verification import (
    ChangeOperation,
    ObligationStatus,
    ObligationType,
    derive_required_verification_set,
    derive_semantic_change_set,
    evaluate_required_set_quality,
)


def _node(
    ref: str,
    kind: str,
    revision: SourceRevision,
    *,
    version: int = 1,
) -> GraphNode:
    return GraphNode(
        ref,
        CanonicalRef(ref),
        kind,
        "service.py" if kind != "test" else "test_service.py",
        Provenance("fixture", "deterministic", "v1", revision),
        Confidence(1.0),
        FactStatus.DECLARED,
        revision,
        {"version": version},
    )


def _edge(
    source: str,
    target: str,
    kind: str,
    revision: SourceRevision,
    *,
    confidence: float = 1.0,
    status: FactStatus = FactStatus.DECLARED,
) -> GraphEdge:
    return GraphEdge(
        f"{source}|{kind}|{target}",
        CanonicalRef(source),
        CanonicalRef(target),
        kind,
        "service.py",
        Provenance("fixture", "deterministic", "v1", revision),
        Confidence(confidence),
        status,
        revision,
    )


def _snapshots() -> tuple[GraphSnapshot, GraphSnapshot]:
    project = ProjectRef("project", "workspace", "file:///repo")
    source_1 = SourceRevision("source-1")
    source_2 = SourceRevision("source-2")
    leaf = "py://service#leaf"
    caller = "py://service#caller"
    test = "py://test_service#test_caller"
    effect = "effect://cache/write"
    dynamic = "pyname://dynamic"
    base = GraphSnapshot(
        project,
        GraphRevision("twin-1", project, source_1, "tree-1", {"fixture": "v1"}),
        (
            _node(leaf, "function", source_1),
            _node(caller, "function", source_1),
            _node(test, "test", source_1),
            _node(effect, "side_effect", source_1),
        ),
        (
            _edge(caller, leaf, "calls", source_1),
            _edge(test, caller, "tests", source_1),
            _edge(caller, effect, "performs_side_effect", source_1),
        ),
    )
    candidate = GraphSnapshot(
        project,
        GraphRevision(
            "twin-2", project, source_2, "tree-2", {"fixture": "v1"}, parent_revision_id="twin-1"
        ),
        (
            _node(leaf, "function", source_2, version=2),
            _node(caller, "function", source_2),
            _node(test, "test", source_2),
            _node(effect, "side_effect", source_2),
        ),
        (
            _edge(caller, leaf, "calls", source_2),
            _edge(test, caller, "tests", source_2),
            _edge(caller, effect, "performs_side_effect", source_2),
            _edge(
                caller,
                dynamic,
                "may_call",
                source_2,
                confidence=0.35,
                status=FactStatus.INFERRED,
            ),
        ),
    )
    return base, candidate


def test_semantic_change_set_is_a_deterministic_revision_scoped_projection() -> None:
    base, candidate = _snapshots()

    first = derive_semantic_change_set(base, candidate)
    second = derive_semantic_change_set(base, candidate)

    assert first == second
    assert first.base_revision is not None
    assert first.base_revision.revision_id == "twin-1"
    assert first.candidate_revision.revision_id == "twin-2"
    assert [(item.canonical_ref.value, item.operation) for item in first.entities] == [
        ("py://service#leaf", ChangeOperation.CHANGED)
    ]
    assert [(item.relation_type, item.operation) for item in first.relations] == [
        ("may_call", ChangeOperation.ADDED)
    ]
    assert {item.value for item in first.unresolved_refs} == {
        "py://service#caller",
        "pyname://dynamic",
    }
    assert first.changed_files == ("service.py",)


def test_required_set_keeps_uncovered_runtime_obligations_explicit() -> None:
    base, candidate = _snapshots()
    change_set = derive_semantic_change_set(base, candidate)
    impact = GraphAnalysisService(candidate).assess_impact(
        ImpactQuery(tuple(item.value for item in change_set.changed_refs), max_depth=4)
    )

    required = derive_required_verification_set(change_set, impact)

    assert [item.provider_id for item in required.providers] == [
        "test:py://test_service#test_caller"
    ]
    types = {item.obligation_type for item in required.obligations}
    assert ObligationType.LOCAL_BEHAVIOR in types
    assert ObligationType.CONSUMER_BEHAVIOR in types
    assert ObligationType.SIDE_EFFECT in types
    assert ObligationType.UNCERTAINTY_BOUNDARY in types
    assert all(item.status is ObligationStatus.UNCOVERED for item in required.obligations)
    assert required.uncovered_obligation_ids
    assert "required obligations remain uncovered" in required.diagnostics
    test_provider = required.providers[0]
    assert test_provider.obligation_ids
    assert all(
        test_provider.provider_id in item.accepted_provider_ids
        for item in required.obligations
        if item.obligation_id in test_provider.obligation_ids
    )


def test_required_set_quality_exposes_exact_counts_precision_and_recall() -> None:
    base, candidate = _snapshots()
    change_set = derive_semantic_change_set(base, candidate)
    impact = GraphAnalysisService(candidate).assess_impact(
        ImpactQuery(tuple(item.value for item in change_set.changed_refs), max_depth=4)
    )
    required = derive_required_verification_set(change_set, impact)

    quality = evaluate_required_set_quality(
        required,
        ("test:py://test_service#test_caller", "test:py://tests#missing"),
    )

    assert quality.true_positive_count == 1
    assert quality.false_positive_count == 0
    assert quality.false_negative_count == 1
    assert quality.precision == 1.0
    assert quality.recall == 0.5


def test_required_set_rejects_an_impact_report_from_another_revision() -> None:
    base, candidate = _snapshots()
    change_set = derive_semantic_change_set(base, candidate)
    stale_impact = GraphAnalysisService(base).assess_impact(
        ImpactQuery(("py://service#leaf",), max_depth=4)
    )

    try:
        derive_required_verification_set(change_set, stale_impact)
    except ValueError as exc:
        assert "candidate Twin revision" in str(exc)
    else:
        raise AssertionError("stale impact report was accepted")
