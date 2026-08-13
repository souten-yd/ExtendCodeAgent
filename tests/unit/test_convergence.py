from __future__ import annotations

from extendcodeagent.convergence import (
    ActualElement,
    ActualSnapshot,
    ConvergenceDecision,
    ElementState,
    TargetElement,
    TargetSnapshot,
    VerificationEvidence,
    decide_convergence,
    evaluate_convergence,
)
from extendcodeagent.core.contracts import (
    CanonicalRef,
    EvidenceRef,
    EvidenceStatus,
    ProjectRef,
    SourceRevision,
    TwinRevisionRef,
)

PROJECT = ProjectRef("project", "workspace", "file:///repo")
SOURCE = SourceRevision("source-1")
TWIN = TwinRevisionRef("twin-1", SOURCE)


def _target(
    element_id: str,
    *,
    mandatory: bool = True,
    refs: tuple[str, ...] | None = None,
    verify: bool = True,
    depends: tuple[str, ...] = (),
) -> TargetElement:
    return TargetElement(
        element_id,
        CanonicalRef(f"bp://{element_id}"),
        tuple(CanonicalRef(item) for item in (refs or (f"file://{element_id}.py",))),
        mandatory=mandatory,
        requires_verification=verify,
        depends_on_element_ids=depends,
    )


def _actual(*refs: str) -> ActualSnapshot:
    return ActualSnapshot(
        PROJECT,
        TWIN,
        tuple(ActualElement(CanonicalRef(item), "file") for item in refs),
    )


def _evidence(ref: str, status: EvidenceStatus, revision: SourceRevision = SOURCE) -> VerificationEvidence:
    return VerificationEvidence(
        CanonicalRef(ref),
        status,
        revision,
        (EvidenceRef(f"evidence:{ref}", status, revision),),
    )


def test_all_task_states_are_distinct_and_planned_refs_are_not_actual_facts() -> None:
    target = TargetSnapshot(
        PROJECT,
        "blueprint-1",
        (
            _target("blocked"),
            _target("absent", mandatory=False),
            _target("partial", refs=("file://partial.py", "file://helper.py")),
            _target("materialized", verify=False),
            _target("observed"),
            _target("verified"),
            _target("divergent"),
            _target("stale"),
        ),
    )
    actual = _actual(
        "file://partial.py",
        "file://materialized.py",
        "file://observed.py",
        "file://verified.py",
        "file://divergent.py",
        "file://stale.py",
    )
    evidence = (
        _evidence("file://observed.py", EvidenceStatus.OBSERVED),
        _evidence("file://verified.py", EvidenceStatus.VERIFIED),
        _evidence("file://divergent.py", EvidenceStatus.FAILED),
        _evidence("file://stale.py", EvidenceStatus.VERIFIED, SourceRevision("old")),
    )
    report = evaluate_convergence(target, actual, evidence)
    states = {item.element_id: item.state for item in report.elements}

    assert states == {
        "absent": ElementState.ABSENT,
        "blocked": ElementState.BLOCKED,
        "divergent": ElementState.DIVERGENT,
        "materialized": ElementState.MATERIALIZED,
        "observed": ElementState.OBSERVED,
        "partial": ElementState.PARTIAL,
        "stale": ElementState.STALE,
        "verified": ElementState.VERIFIED,
    }
    assert all(item.canonical_ref.value.startswith("file://") for item in actual.elements)
    assert all(item.planned_ref.value.startswith("bp://") for item in target.elements)


def test_unavailable_or_stale_evidence_never_completes() -> None:
    target = TargetSnapshot(PROJECT, "blueprint-1", (_target("service"),))
    actual = _actual("file://service.py")
    unavailable = evaluate_convergence(
        target,
        actual,
        (_evidence("file://service.py", EvidenceStatus.UNAVAILABLE),),
    )
    stale = evaluate_convergence(
        target,
        actual,
        (_evidence("file://service.py", EvidenceStatus.VERIFIED, SourceRevision("old")),),
    )

    assert unavailable.elements[0].state is ElementState.MATERIALIZED
    assert stale.elements[0].state is ElementState.STALE
    assert decide_convergence(unavailable).decision is ConvergenceDecision.CONTINUE
    assert decide_convergence(stale).decision is ConvergenceDecision.CONTINUE


def test_missing_snapshot_is_unavailable_and_cannot_complete() -> None:
    report = evaluate_convergence(None, None, ())
    assert report.available is False
    assert decide_convergence(report).decision is ConvergenceDecision.HALT


def test_decision_policy_is_deterministic_and_scoped() -> None:
    complete_target = TargetSnapshot(
        PROJECT,
        "blueprint-1",
        (_target("service", verify=False),),
    )
    complete = evaluate_convergence(complete_target, _actual("file://service.py"), ())
    assert decide_convergence(complete).decision is ConvergenceDecision.COMPLETE

    dependency_target = TargetSnapshot(
        PROJECT,
        "blueprint-2",
        (
            _target("base"),
            _target("dependent", depends=("base",)),
            _target("other"),
        ),
    )
    divergent = evaluate_convergence(
        dependency_target,
        _actual("file://base.py", "file://dependent.py", "file://other.py"),
        (_evidence("file://base.py", EvidenceStatus.FAILED),),
    )
    decision = decide_convergence(divergent, interface_changed=("base",))
    assert decision.decision is ConvergenceDecision.REPLAN_DOWNSTREAM
    assert decision.affected_element_ids == ("base", "dependent")
    assert decide_convergence(divergent).decision is ConvergenceDecision.REPAIR_CURRENT
    assert decide_convergence(divergent, target_invalid=True).decision is ConvergenceDecision.REVISE_TARGET
    assert decide_convergence(divergent, decision_required=True).decision is ConvergenceDecision.REQUEST_DECISION
    assert decide_convergence(divergent, unsafe=True).decision is ConvergenceDecision.HALT
