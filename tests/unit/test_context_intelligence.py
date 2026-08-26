from __future__ import annotations

from datetime import UTC, datetime

from extendcodeagent.context import (
    ContextProfile,
    ContextRequest,
    EvidenceRole,
    RequiredRef,
    WeakLocalEvidenceRequest,
    attach_excerpts,
    build_context,
    build_weak_local_evidence,
    context_item_json,
    estimate_payload_tokens,
    stable_evidence_envelope,
)
from extendcodeagent.context.obligations import obligation_refs
from extendcodeagent.context.serialization import weak_local_evidence_item_json
from extendcodeagent.core.contracts import (
    CanonicalRef,
    Confidence,
    ProjectRef,
    Provenance,
    SourceRevision,
)
from extendcodeagent.graph import FactStatus, GraphNode, GraphSnapshot
from extendcodeagent.runtime import (
    ObservationKind,
    ObservationStatus,
    RuntimeObservation,
    covering_tests,
)

PROJECT = ProjectRef("project", "workspace", "file:///repo")
REVISION = SourceRevision("rev-1")
PROVENANCE = Provenance("source", "python-ast", "1", REVISION)
_AT = datetime(2026, 8, 26, tzinfo=UTC)


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


def test_the_envelope_carries_what_was_asked_for_and_nothing_else() -> None:
    """PI answers about refs; finding the ref is what search is for.

    The envelope used to run its own term match and graph walk. Measured on Django that
    walk saw 256 of 49,775 nodes and its additions were the dilution, so it was removed.
    """

    package = build_weak_local_evidence(
        _snapshot(),
        WeakLocalEvidenceRequest(
            "Locate function_0",
            target_refs=(CanonicalRef("py://module#function_0"),),
            token_budget=2_000,
            max_items=12,
        ),
    )

    assert [item.canonical_ref.value for item in package.items] == ["py://module#function_0"]
    assert package.items[0].role is EvidenceRole.TARGET
    assert package.used_tokens <= package.token_budget
    assert package.selected_evidence_ids == tuple(item.evidence_id for item in package.items)


def test_an_objective_without_a_ref_returns_nothing_rather_than_guessing() -> None:
    """Guessing a location from prose is what search already does better."""

    package = build_weak_local_evidence(
        _snapshot(), WeakLocalEvidenceRequest("Locate function_0", token_budget=2_000)
    )

    assert package.items == ()
    assert package.candidate_count == 0


def test_widening_is_the_caller_naming_more_obligations() -> None:
    """The ladder widens because a narrow answer did not hold, not by walking outward."""

    nodes = _snapshot(2).nodes
    snapshot = GraphSnapshot(PROJECT, None, nodes)
    narrow = build_weak_local_evidence(
        snapshot,
        WeakLocalEvidenceRequest("Locate function_0", target_refs=(nodes[0].canonical_ref,)),
    )
    widened = build_weak_local_evidence(
        snapshot,
        WeakLocalEvidenceRequest(
            "Locate function_0",
            target_refs=(nodes[0].canonical_ref,),
            required_refs=(RequiredRef(nodes[1].canonical_ref, EvidenceRole.CONSUMER),),
            prior_evidence_ids=narrow.selected_evidence_ids,
        ),
    )

    assert {item.canonical_ref.value for item in narrow.items} == {"py://module#function_0"}
    assert {item.canonical_ref.value for item in widened.items} == {
        "py://module#function_0",
        "py://module#function_1",
    }
    assert widened.prior_evidence_ids == narrow.selected_evidence_ids


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


def test_required_evidence_survives_the_item_cap_and_reports_the_overflow() -> None:
    """An obligation's evidence is never ranked away, but exceeding the bound is visible."""

    snapshot = _snapshot(size=60)
    required = tuple(
        RequiredRef(CanonicalRef(f"py://module#function_{index}"), EvidenceRole.TEST)
        for index in range(40)
    )

    package = build_weak_local_evidence(
        snapshot,
        WeakLocalEvidenceRequest(
            "carry every obligation",
            token_budget=8_192,
            max_items=8,
            required_refs=required,
        ),
    )

    delivered = {item.canonical_ref.value for item in package.items}
    assert {ref.canonical_ref.value for ref in required} <= delivered
    assert len(package.items) > 8
    assert "protected_evidence_exceeds_budget" in package.unresolved_gaps


def test_evidence_items_carry_the_source_path_an_answer_has_to_name() -> None:
    """Emitting only `py://a.b.c#d` made the model derive `a/b/c.py` itself."""

    package = build_weak_local_evidence(
        _snapshot(),
        WeakLocalEvidenceRequest(
            "locate function_1",
            target_refs=(CanonicalRef("py://module#function_1"),),
            token_budget=4_096,
        ),
    )

    assert package.items
    assert all(item.source_ref == "module.py" for item in package.items)
    assert "path" in stable_evidence_envelope()["evidence_item_fields"]


def test_a_seed_bound_never_evicts_required_evidence() -> None:
    """Capping seeds must bite the inferred ones; required truth is not rankable."""

    snapshot = _snapshot(size=200)
    required = tuple(
        RequiredRef(CanonicalRef(f"py://module#function_{index}"), EvidenceRole.TEST)
        for index in range(80)
    )

    package = build_weak_local_evidence(
        snapshot,
        WeakLocalEvidenceRequest(
            "carry every obligation past the seed bound",
            token_budget=8_192,
            max_items=8,
            required_refs=required,
        ),
    )

    delivered = {item.canonical_ref.value for item in package.items}
    assert {ref.canonical_ref.value for ref in required} <= delivered


def test_targeted_evidence_carries_the_symbol_body_not_just_its_name() -> None:
    """Naming a symbol makes a consumer open the file, and a file is not the symbol."""

    node = GraphNode(
        "node-x",
        CanonicalRef("py://module#target"),
        "function",
        "module.py",
        PROVENANCE,
        Confidence(1.0),
        FactStatus.DECLARED,
        REVISION,
        {"name": "target", "start_line": 2, "end_line": 3},
    )
    snapshot = GraphSnapshot(PROJECT, None, (node,))
    package = build_weak_local_evidence(
        snapshot,
        WeakLocalEvidenceRequest(
            "edit target", (CanonicalRef("py://module#target"),), token_budget=4_096
        ),
    )

    def read(source_ref: str, start: int, end: int) -> str | None:
        assert (source_ref, start, end) == ("module.py", 2, 3)
        return "def target():\n    return 1"

    with_source = attach_excerpts(package, read)
    item = with_source.items[0]

    assert (item.start_line, item.end_line) == (2, 3)
    assert item.excerpt == "def target():\n    return 1"
    assert "source" in weak_local_evidence_item_json(item)


def test_a_symbol_too_large_to_be_an_excerpt_is_refused() -> None:
    """A body is delivered because it is smaller than the file, not regardless of size."""

    node = GraphNode(
        "node-a",
        CanonicalRef("py://module#target"),
        "function",
        "module.py",
        PROVENANCE,
        Confidence(1.0),
        FactStatus.DECLARED,
        REVISION,
        {"name": "target", "start_line": 1, "end_line": 500},
    )
    package = build_weak_local_evidence(
        GraphSnapshot(PROJECT, None, (node,)),
        WeakLocalEvidenceRequest(
            "edit target", (CanonicalRef("py://module#target"),), token_budget=4_096
        ),
    )

    with_source = attach_excerpts(package, lambda *_: "body", max_lines=120)

    assert with_source.items[0].excerpt is None


def test_an_excerpt_budget_stops_bodies_from_crowding_the_envelope() -> None:
    package = build_weak_local_evidence(
        _snapshot(),
        WeakLocalEvidenceRequest("locate function_1", token_budget=4_096),
    )

    with_source = attach_excerpts(package, lambda *_: "x" * 4_000, token_budget=1)

    assert all(item.excerpt is None for item in with_source.items)


def test_an_observed_test_becomes_an_obligation_the_graph_cannot_supply() -> None:
    """Coverage reaches a test that never names its subject.

    Django's tests reach theirs through the runner and the app registry, so no call or
    import edge joins them and no amount of traversal recovers the pair. An observation
    naming both is the only evidence there is.
    """

    target = CanonicalRef("py://module#target")
    hidden = CanonicalRef("py://tests.test_via_runner#test_target")
    snapshot = GraphSnapshot(PROJECT, None, _snapshot(1).nodes)

    without = obligation_refs(
        snapshot,
        (target.value,),
        "verify target",
        equivalents=lambda _: (),
        recommended_tests=lambda _: (),
    )
    with_coverage = obligation_refs(
        snapshot,
        (target.value,),
        "verify target",
        equivalents=lambda _: (),
        recommended_tests=lambda _: (),
        observed_tests=lambda refs: (hidden.value,) if target.value in set(refs) else (),
    )

    assert hidden.value not in {item.canonical_ref.value for item in without}
    observed = next(item for item in with_coverage if item.canonical_ref.value == hidden.value)
    assert observed.role is EvidenceRole.TEST


def test_only_a_test_observation_that_ran_counts_as_coverage() -> None:
    """An unavailable observation names nothing that executed."""

    ran = RuntimeObservation(
        "obs-1",
        ObservationKind.TEST,
        PROJECT,
        REVISION,
        ObservationStatus.PASSED,
        _AT,
        _AT,
        PROVENANCE,
        observed_refs=(CanonicalRef("py://module#target"), CanonicalRef("py://tests#covers")),
        command="pytest",
    )
    skipped = RuntimeObservation(
        "obs-2",
        ObservationKind.TEST,
        PROJECT,
        REVISION,
        ObservationStatus.UNAVAILABLE,
        _AT,
        _AT,
        PROVENANCE,
        observed_refs=(CanonicalRef("py://module#target"), CanonicalRef("py://tests#never_ran")),
    )
    lint = RuntimeObservation(
        "obs-3",
        ObservationKind.LINT,
        PROJECT,
        REVISION,
        ObservationStatus.PASSED,
        _AT,
        _AT,
        PROVENANCE,
        observed_refs=(CanonicalRef("py://module#target"), CanonicalRef("py://tools#ruff")),
        command="ruff",
    )

    found = covering_tests(
        (ran, skipped, lint),
        (CanonicalRef("py://module#target"),),
        lambda ref: ref.value.startswith("py://tests"),
    )

    assert [ref.value for ref in found] == ["py://tests#covers"]
