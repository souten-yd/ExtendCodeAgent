from __future__ import annotations

from extendcodeagent.convergence import ConvergenceDecision, ElementState
from extendcodeagent.core.contracts import (
    CanonicalRef,
    EvidenceRef,
    EvidenceStatus,
    ProjectRef,
    SourceRevision,
    TwinRevisionRef,
)
from extendcodeagent.traceability import (
    Requirement,
    RequirementEvidence,
    evaluate_project_requirements,
)


def _project() -> ProjectRef:
    return ProjectRef("p", "w", "file:///repo")


def test_external_evidence_cannot_complete_requirement() -> None:
    revision = SourceRevision("source-1")
    report = evaluate_project_requirements(
        _project(),
        "requirements-1",
        (Requirement("r1", "durable store", (CanonicalRef("file://store.py"),)),),
        (CanonicalRef("file://store.py"),),
        TwinRevisionRef("twin-1", revision),
        (
            RequirementEvidence(
                "r1",
                (CanonicalRef("file://store.py"),),
                (EvidenceRef("external:e1", EvidenceStatus.OBSERVED),),
                revision,
                external=True,
            ),
        ),
    )

    assert report.convergence.elements[0].state is ElementState.OBSERVED
    assert report.recommendation.decision is ConvergenceDecision.CONTINUE


def test_explicit_current_project_evidence_can_complete_requirement() -> None:
    revision = SourceRevision("source-1")
    report = evaluate_project_requirements(
        _project(),
        "requirements-1",
        (Requirement("r1", "durable store", (CanonicalRef("file://store.py"),)),),
        (CanonicalRef("file://store.py"),),
        TwinRevisionRef("twin-1", revision),
        (
            RequirementEvidence(
                "r1",
                (CanonicalRef("file://store.py"),),
                (EvidenceRef("test:e1", EvidenceStatus.VERIFIED, revision),),
                revision,
            ),
        ),
    )

    assert report.convergence.elements[0].state is ElementState.VERIFIED
    assert report.recommendation.decision is ConvergenceDecision.COMPLETE


def test_stale_or_unmapped_evidence_never_completes() -> None:
    current = SourceRevision("source-2")
    report = evaluate_project_requirements(
        _project(),
        "requirements-1",
        (Requirement("r1", "durable store", (CanonicalRef("file://store.py"),)),),
        (CanonicalRef("file://store.py"),),
        TwinRevisionRef("twin-2", current),
        (
            RequirementEvidence(
                "other",
                (CanonicalRef("file://store.py"),),
                (EvidenceRef("test:old", EvidenceStatus.VERIFIED, SourceRevision("source-1")),),
                SourceRevision("source-1"),
            ),
        ),
    )

    assert report.convergence.elements[0].state is ElementState.MATERIALIZED
    assert report.recommendation.decision is ConvergenceDecision.CONTINUE
