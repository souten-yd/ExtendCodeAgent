"""Host-neutral, revision-scoped verification projections.

These objects do not own truth or persistence. They are deterministic views over the
existing Twin, Graph, Impact, Test, and Runtime domains.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from extendcodeagent.core.contracts import (
    CanonicalRef,
    FreshnessPolicy,
    ProjectRef,
    Provenance,
    TwinRevisionRef,
)
from extendcodeagent.graph import FactStatus


def _required(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _confidence(value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError("confidence must be between zero and one")


class ChangeOperation(StrEnum):
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"


@dataclass(frozen=True, slots=True)
class SemanticEntityChange:
    canonical_ref: CanonicalRef
    entity_type: str
    source_ref: str
    operation: ChangeOperation
    confidence: float
    status: FactStatus
    provenance: Provenance

    def __post_init__(self) -> None:
        _required(self.entity_type, "entity_type")
        _required(self.source_ref, "source_ref")
        _confidence(self.confidence)


@dataclass(frozen=True, slots=True)
class SemanticRelationChange:
    source: CanonicalRef
    target: CanonicalRef
    relation_type: str
    source_ref: str
    operation: ChangeOperation
    confidence: float
    status: FactStatus
    provenance: Provenance

    def __post_init__(self) -> None:
        _required(self.relation_type, "relation_type")
        _required(self.source_ref, "source_ref")
        _confidence(self.confidence)


@dataclass(frozen=True, slots=True)
class SemanticChangeSet:
    change_set_id: str
    project: ProjectRef
    base_revision: TwinRevisionRef | None
    candidate_revision: TwinRevisionRef
    entities: tuple[SemanticEntityChange, ...]
    relations: tuple[SemanticRelationChange, ...]
    changed_files: tuple[str, ...]
    unresolved_refs: tuple[CanonicalRef, ...] = ()

    def __post_init__(self) -> None:
        _required(self.change_set_id, "change_set_id")

    @property
    def changed_refs(self) -> tuple[CanonicalRef, ...]:
        return tuple(
            sorted({item.canonical_ref for item in self.entities}, key=lambda ref: ref.value)
        )


class ObligationType(StrEnum):
    LOCAL_BEHAVIOR = "local_behavior"
    CONSUMER_BEHAVIOR = "consumer_behavior"
    PUBLIC_CONTRACT = "public_contract"
    REQUIREMENT = "requirement"
    SIDE_EFFECT = "side_effect"
    TEST_INTENT = "test_intent"
    UNCERTAINTY_BOUNDARY = "uncertainty_boundary"


class ObligationStatus(StrEnum):
    UNCOVERED = "uncovered"
    PARTIALLY_COVERED = "partially_covered"
    COVERED = "covered"
    CONFLICTED = "conflicted"
    UNAVAILABLE = "unavailable"


class Criticality(StrEnum):
    NORMAL = "normal"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class VerificationObligation:
    obligation_id: str
    obligation_type: ObligationType
    originating_refs: tuple[CanonicalRef, ...]
    required_evidence_kinds: tuple[str, ...]
    freshness: FreshnessPolicy
    minimum_confidence: float
    uncertain: bool
    criticality: Criticality
    accepted_provider_ids: tuple[str, ...]
    status: ObligationStatus = ObligationStatus.UNCOVERED

    def __post_init__(self) -> None:
        _required(self.obligation_id, "obligation_id")
        if not self.originating_refs or not self.required_evidence_kinds:
            raise ValueError("an obligation requires originating refs and evidence kinds")
        _confidence(self.minimum_confidence)


@dataclass(frozen=True, slots=True)
class RequiredVerificationProvider:
    provider_id: str
    provider_kind: str
    canonical_ref: CanonicalRef | None
    obligation_ids: tuple[str, ...]
    confidence: float
    reason: str

    def __post_init__(self) -> None:
        _required(self.provider_id, "provider_id")
        _required(self.provider_kind, "provider_kind")
        _required(self.reason, "reason")
        _confidence(self.confidence)


@dataclass(frozen=True, slots=True)
class RequiredVerificationSet:
    change_set_id: str
    candidate_revision: TwinRevisionRef
    obligations: tuple[VerificationObligation, ...]
    providers: tuple[RequiredVerificationProvider, ...]
    uncovered_obligation_ids: tuple[str, ...]
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _required(self.change_set_id, "change_set_id")


@dataclass(frozen=True, slots=True)
class RequiredSetQuality:
    predicted_provider_ids: tuple[str, ...]
    expected_provider_ids: tuple[str, ...]
    true_positive_count: int
    false_positive_count: int
    false_negative_count: int
    precision: float
    recall: float

    def __post_init__(self) -> None:
        if (
            min(
                self.true_positive_count,
                self.false_positive_count,
                self.false_negative_count,
            )
            < 0
        ):
            raise ValueError("quality counts must not be negative")
        _confidence(self.precision)
        _confidence(self.recall)
