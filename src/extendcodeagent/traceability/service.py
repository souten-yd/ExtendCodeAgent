"""Project-level requirement convergence through the existing convergence engine."""

from __future__ import annotations

from extendcodeagent.convergence import (
    ActualElement,
    ActualSnapshot,
    TargetElement,
    TargetSnapshot,
    VerificationEvidence,
    decide_convergence,
    evaluate_convergence,
)
from extendcodeagent.core.contracts import (
    CanonicalRef,
    EvidenceStatus,
    ProjectRef,
    TwinRevisionRef,
)

from .contracts import ProjectRequirementReport, Requirement, RequirementEvidence


def evaluate_project_requirements(
    project: ProjectRef,
    requirement_revision_id: str,
    requirements: tuple[Requirement, ...],
    actual_refs: tuple[CanonicalRef, ...],
    twin_revision: TwinRevisionRef,
    evidence: tuple[RequirementEvidence, ...],
) -> ProjectRequirementReport:
    target = TargetSnapshot(
        project,
        requirement_revision_id,
        tuple(
            TargetElement(
                item.requirement_id,
                CanonicalRef(f"planned://requirement/{item.requirement_id}"),
                item.expected_actual_refs,
                item.mandatory,
                item.requires_verification,
            )
            for item in requirements
        ),
    )
    actual = ActualSnapshot(
        project,
        twin_revision,
        tuple(ActualElement(item, "project_fact") for item in actual_refs),
    )
    by_requirement = {item.requirement_id: item for item in evidence}
    verification: list[VerificationEvidence] = []
    for requirement in requirements:
        item = by_requirement.get(requirement.requirement_id)
        if item is None:
            continue
        status = _evidence_status(item, twin_revision)
        for ref in item.actual_refs:
            verification.append(
                VerificationEvidence(ref, status, item.source_revision, item.evidence)
            )
    convergence = evaluate_convergence(target, actual, tuple(verification))
    return ProjectRequirementReport(convergence, decide_convergence(convergence))


def _evidence_status(item: RequirementEvidence, twin_revision: TwinRevisionRef) -> EvidenceStatus:
    if item.external:
        return EvidenceStatus.OBSERVED
    statuses = {evidence.status for evidence in item.evidence}
    if EvidenceStatus.FAILED in statuses:
        return EvidenceStatus.FAILED
    if item.source_revision != twin_revision.source_revision:
        return EvidenceStatus.STALE
    if EvidenceStatus.VERIFIED in statuses:
        return EvidenceStatus.VERIFIED
    if EvidenceStatus.OBSERVED in statuses:
        return EvidenceStatus.OBSERVED
    return EvidenceStatus.UNAVAILABLE
