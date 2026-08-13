"""Pure task-level convergence evaluator and deterministic decision policy."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from extendcodeagent.core.contracts import CanonicalRef, EvidenceStatus

from .contracts import (
    ActualSnapshot,
    ConvergenceDecision,
    ConvergenceRecommendation,
    ConvergenceReport,
    ElementConvergence,
    ElementState,
    TargetSnapshot,
    VerificationEvidence,
    unavailable_report,
)


def evaluate_convergence(
    target: TargetSnapshot | None,
    actual: ActualSnapshot | None,
    verification: tuple[VerificationEvidence, ...],
) -> ConvergenceReport:
    if target is None or actual is None:
        return unavailable_report()
    if (
        target.project.project_id != actual.project.project_id
        or target.project.workspace_id != actual.project.workspace_id
    ):
        return unavailable_report("target_actual_workspace_mismatch")
    actual_refs = {item.canonical_ref.value: item for item in actual.elements}
    evidence_by_ref = {item.canonical_ref.value: item for item in verification}
    results: list[ElementConvergence] = []
    for element in sorted(target.elements, key=lambda item: item.element_id):
        matched = tuple(item for item in element.expected_actual_refs if item.value in actual_refs)
        missing = tuple(
            item for item in element.expected_actual_refs if item.value not in actual_refs
        )
        if not matched:
            state = ElementState.BLOCKED if element.mandatory else ElementState.ABSENT
            results.append(ElementConvergence(element.element_id, state, (), missing))
            continue
        if missing:
            results.append(
                ElementConvergence(element.element_id, ElementState.PARTIAL, matched, missing)
            )
            continue
        if not element.requires_verification:
            results.append(
                ElementConvergence(element.element_id, ElementState.MATERIALIZED, matched)
            )
            continue
        evidence = _best_evidence(matched, evidence_by_ref)
        if evidence is None or evidence.status is EvidenceStatus.UNAVAILABLE:
            results.append(
                ElementConvergence(
                    element.element_id,
                    ElementState.MATERIALIZED,
                    matched,
                    evidence=evidence.evidence if evidence else (),
                    diagnostics=("verification_unavailable",),
                )
            )
            continue
        if evidence.status is EvidenceStatus.FAILED:
            state = ElementState.DIVERGENT
            diagnostic = "verification_failed"
        elif evidence.status is EvidenceStatus.OBSERVED:
            state = ElementState.OBSERVED
            diagnostic = "observed_not_verified"
        elif evidence.status is EvidenceStatus.VERIFIED:
            if evidence.source_revision == actual.twin_revision.source_revision:
                state = ElementState.VERIFIED
                diagnostic = "verified_at_current_revision"
            else:
                state = ElementState.STALE
                diagnostic = "verification_revision_stale"
        else:
            state = ElementState.STALE
            diagnostic = "evidence_stale"
        results.append(
            ElementConvergence(
                element.element_id,
                state,
                matched,
                evidence=evidence.evidence,
                diagnostics=(diagnostic,),
            )
        )
    return ConvergenceReport(
        f"conv:{uuid.uuid4().hex}",
        target.project,
        target.target_revision_id,
        actual.twin_revision,
        tuple(results),
        True,
        datetime.now(UTC),
        dependencies=tuple(
            (item.element_id, item.depends_on_element_ids)
            for item in sorted(target.elements, key=lambda value: value.element_id)
        ),
        target_valid=target.valid,
        decision_required=target.decision_required,
    )


def decide_convergence(
    report: ConvergenceReport,
    *,
    unsafe: bool = False,
    decision_required: bool = False,
    target_invalid: bool = False,
    interface_changed: tuple[str, ...] = (),
) -> ConvergenceRecommendation:
    if unsafe:
        return ConvergenceRecommendation(ConvergenceDecision.HALT, ("unsafe",))
    if not report.available:
        return ConvergenceRecommendation(ConvergenceDecision.HALT, ("convergence_unavailable",))
    if decision_required or report.decision_required:
        return ConvergenceRecommendation(
            ConvergenceDecision.REQUEST_DECISION, ("critical_decision_required",)
        )
    if target_invalid or not report.target_valid:
        return ConvergenceRecommendation(ConvergenceDecision.REVISE_TARGET, ("target_invalid",))
    changed = set(interface_changed)
    if changed:
        affected = _downstream(report, changed)
        return ConvergenceRecommendation(
            ConvergenceDecision.REPLAN_DOWNSTREAM,
            ("interface_changed",),
            tuple(sorted(changed | affected)),
        )
    divergent = tuple(
        item.element_id for item in report.elements if item.state is ElementState.DIVERGENT
    )
    if divergent:
        return ConvergenceRecommendation(
            ConvergenceDecision.REPAIR_CURRENT,
            ("verification_divergent",),
            divergent,
        )
    incomplete = tuple(
        item.element_id
        for item in report.elements
        if item.state
        in {
            ElementState.ABSENT,
            ElementState.BLOCKED,
            ElementState.PARTIAL,
            ElementState.OBSERVED,
            ElementState.STALE,
        }
        or (
            item.state is ElementState.MATERIALIZED
            and "verification_unavailable" in item.diagnostics
        )
    )
    if incomplete:
        return ConvergenceRecommendation(
            ConvergenceDecision.CONTINUE, ("work_or_evidence_remaining",), incomplete
        )
    return ConvergenceRecommendation(ConvergenceDecision.COMPLETE, ("target_satisfied",))


def _best_evidence(
    refs: tuple[CanonicalRef, ...], evidence_by_ref: dict[str, VerificationEvidence]
) -> VerificationEvidence | None:
    for ref in refs:
        if ref.value in evidence_by_ref:
            return evidence_by_ref[ref.value]
    return None


def _downstream(report: ConvergenceReport, changed: set[str]) -> set[str]:
    dependents: dict[str, set[str]] = {}
    for element_id, dependencies in report.dependencies:
        for dependency in dependencies:
            dependents.setdefault(dependency, set()).add(element_id)
    affected: set[str] = set()
    pending = list(changed)
    while pending:
        dependency = pending.pop()
        for element_id in dependents.get(dependency, ()):
            if element_id not in affected:
                affected.add(element_id)
                pending.append(element_id)
    return affected
