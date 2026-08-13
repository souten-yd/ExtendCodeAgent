"""Schema-independent task convergence contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from extendcodeagent.core.contracts import (
    CanonicalRef,
    EvidenceRef,
    EvidenceStatus,
    ProjectRef,
    SourceRevision,
    TwinRevisionRef,
)


class ElementState(StrEnum):
    ABSENT = "absent"
    PARTIAL = "partial"
    MATERIALIZED = "materialized"
    OBSERVED = "observed"
    VERIFIED = "verified"
    DIVERGENT = "divergent"
    BLOCKED = "blocked"
    STALE = "stale"


class ConvergenceDecision(StrEnum):
    CONTINUE = "continue"
    COMPLETE = "complete"
    REPAIR_CURRENT = "repair_current"
    REPLAN_DOWNSTREAM = "replan_downstream"
    REVISE_TARGET = "revise_target"
    REQUEST_DECISION = "request_decision"
    HALT = "halt"


@dataclass(frozen=True, slots=True)
class TargetElement:
    element_id: str
    planned_ref: CanonicalRef
    expected_actual_refs: tuple[CanonicalRef, ...]
    mandatory: bool = True
    requires_verification: bool = True
    depends_on_element_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.planned_ref.value.startswith(("bp://", "planned://")):
            raise ValueError("target planned_ref must use a planned namespace")


@dataclass(frozen=True, slots=True)
class TargetSnapshot:
    project: ProjectRef
    target_revision_id: str
    elements: tuple[TargetElement, ...]
    valid: bool = True
    decision_required: bool = False


@dataclass(frozen=True, slots=True)
class ActualElement:
    canonical_ref: CanonicalRef
    kind: str

    def __post_init__(self) -> None:
        if self.canonical_ref.value.startswith(("bp://", "planned://")):
            raise ValueError("actual elements cannot use a planned namespace")


@dataclass(frozen=True, slots=True)
class ActualSnapshot:
    project: ProjectRef
    twin_revision: TwinRevisionRef
    elements: tuple[ActualElement, ...]


@dataclass(frozen=True, slots=True)
class VerificationEvidence:
    canonical_ref: CanonicalRef
    status: EvidenceStatus
    source_revision: SourceRevision | None
    evidence: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True, slots=True)
class ElementConvergence:
    element_id: str
    state: ElementState
    matched_actual_refs: tuple[CanonicalRef, ...] = ()
    missing_actual_refs: tuple[CanonicalRef, ...] = ()
    evidence: tuple[EvidenceRef, ...] = ()
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ConvergenceReport:
    report_id: str
    project: ProjectRef | None
    target_revision_id: str | None
    actual_twin_revision: TwinRevisionRef | None
    elements: tuple[ElementConvergence, ...]
    available: bool
    generated_at: datetime
    diagnostics: tuple[str, ...] = ()
    dependencies: tuple[tuple[str, tuple[str, ...]], ...] = ()
    target_valid: bool = True
    decision_required: bool = False


@dataclass(frozen=True, slots=True)
class ConvergenceRecommendation:
    decision: ConvergenceDecision
    reason_codes: tuple[str, ...]
    affected_element_ids: tuple[str, ...] = ()


def unavailable_report(*diagnostics: str) -> ConvergenceReport:
    return ConvergenceReport(
        "unavailable",
        None,
        None,
        None,
        (),
        False,
        datetime.now(UTC),
        diagnostics or ("target_or_actual_unavailable",),
    )
