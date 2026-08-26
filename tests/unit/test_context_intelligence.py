from __future__ import annotations

from extendcodeagent.context import (
    ContextProfile,
    ContextRequest,
    EvidenceScope,
    WeakLocalEvidenceRequest,
    build_context,
    build_weak_local_evidence,
    context_item_json,
    estimate_payload_tokens,
    stable_evidence_envelope,
)
from extendcodeagent.core.contracts import (
    CanonicalRef,
    Confidence,
    ProjectRef,
    Provenance,
    SourceRevision,
)
from extendcodeagent.graph import FactStatus, GraphEdge, GraphNode, GraphSnapshot

PROJECT = ProjectRef("project", "workspace", "file:///repo")
REVISION = SourceRevision("rev-1")
PROVENANCE = Provenance("source", "python-ast", "1", REVISION)


def _snapshot(size: int = 30) -> GraphSnapshot:
    nodes = tuple(
        GraphNode(
            f"node-{index}",
            CanonicalRef(f"py://module#function_{index}"),
            "function",
            "module.py",
            PROVENANCE,
            Confidence(1.0),
            FactStatus.DECLARED,
            REVISION,
            {"name": f"function_{index}"},
        )
        for index in range(size)
    )
    return GraphSnapshot(PROJECT, None, nodes)


def test_context_is_bounded_and_every_item_is_explainable_and_revisioned() -> None:
    package = build_context(
        _snapshot(),
        ContextRequest(
            objective="change function zero",
            target_refs=(CanonicalRef("py://module#function_0"),),
            token_budget=80,
            max_items=5,
        ),
    )
    assert package.used_tokens <= package.token_budget == 80
    assert len(package.items) <= 5
    assert package.truncated is True
    assert package.items[0].canonical_ref.value == "py://module#function_0"
    assert all(item.why_included and item.revision == REVISION for item in package.items)
    assert all(item.provenance == PROVENANCE and item.token_estimate > 0 for item in package.items)


def test_weak_profile_is_materially_smaller_than_standard() -> None:
    snapshot = _snapshot()
    standard = build_context(
        snapshot,
        ContextRequest("inspect", token_budget=2_000, max_items=30),
    )
    weak = build_context(
        snapshot,
        ContextRequest("inspect", token_budget=2_000, max_items=30, profile=ContextProfile.WEAK),
    )
    assert weak.used_tokens < standard.used_tokens
    assert len(weak.items) <= 8 < len(standard.items)


def test_weak_local_protocol_reduces_candidates_before_projection() -> None:
    snapshot = _snapshot()
    package = build_weak_local_evidence(
        snapshot,
        WeakLocalEvidenceRequest("Locate function_0", token_budget=2_000, max_items=12),
    )

    assert package.scope is EvidenceScope.SYMBOL
    assert package.candidate_count == 1
    assert [item.canonical_ref.value for item in package.items] == ["py://module#function_0"]
    assert package.deterministic_resolution is True
    assert package.next_scope is None
    assert package.used_tokens <= package.token_budget
    assert package.selected_evidence_ids == tuple(item.evidence_id for item in package.items)


def test_weak_local_protocol_expands_only_for_an_explicit_gap() -> None:
    nodes = _snapshot(2).nodes
    snapshot = GraphSnapshot(
        PROJECT,
        None,
        nodes,
        (
            GraphEdge(
                "edge-1",
                nodes[1].canonical_ref,
                nodes[0].canonical_ref,
                "calls",
                "module.py",
                PROVENANCE,
                Confidence(1.0),
                FactStatus.DECLARED,
                REVISION,
            ),
        ),
    )
    resolved = build_weak_local_evidence(
        snapshot,
        WeakLocalEvidenceRequest(
            "Locate function_0",
            target_refs=(nodes[0].canonical_ref,),
            scope=EvidenceScope.SYMBOL,
        ),
    )
    expanded = build_weak_local_evidence(
        snapshot,
        WeakLocalEvidenceRequest(
            "Locate function_0",
            target_refs=(nodes[0].canonical_ref,),
            scope=EvidenceScope.NEIGHBORHOOD,
            prior_evidence_ids=resolved.selected_evidence_ids,
            unresolved_gaps=("direct caller missing",),
        ),
    )

    assert len(resolved.items) == 1
    assert resolved.next_scope is None
    assert {item.canonical_ref.value for item in expanded.items} == {
        "py://module#function_0",
        "py://module#function_1",
    }
    assert expanded.deterministic_resolution is False
    assert expanded.next_scope is EvidenceScope.IMPACT


def test_stable_evidence_envelope_contains_no_task_or_revision_data() -> None:
    first = stable_evidence_envelope()
    second = stable_evidence_envelope()

    assert first == second
    rendered = repr(first)
    assert "objective" not in rendered
    assert "revision" not in rendered
    assert first["protocol"] == "extendcodeagent.weak-local-evidence.v1"


def test_context_item_cost_matches_the_delivered_payload() -> None:
    """The legacy estimator counted three short strings and under-reported roughly fivefold."""

    snapshot = _snapshot()
    package = build_context(snapshot, ContextRequest("bound the delivered payload", ()))

    for item in package.items:
        assert item.token_estimate == estimate_payload_tokens(context_item_json(item))

    delivered = estimate_payload_tokens([context_item_json(item) for item in package.items])
    assert package.used_tokens >= delivered * 0.9
