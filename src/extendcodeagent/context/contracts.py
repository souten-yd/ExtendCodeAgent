"""Bounded revision-aware context contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from extendcodeagent.core.contracts import CanonicalRef, Provenance, SourceRevision


class ContextProfile(StrEnum):
    STANDARD = "standard"
    WEAK = "weak"


class EvidenceScope(StrEnum):
    """Progressive weak-local evidence scopes, from cheapest to broadest."""

    SYMBOL = "symbol"
    NEIGHBORHOOD = "neighborhood"
    IMPACT = "impact"
    VERIFICATION = "verification"
    SUBSYSTEM = "subsystem"


@dataclass(frozen=True, slots=True)
class ContextRequest:
    objective: str
    target_refs: tuple[CanonicalRef, ...] = ()
    token_budget: int = 2_000
    max_items: int = 30
    min_confidence: float = 0.0
    profile: ContextProfile = ContextProfile.STANDARD

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise ValueError("objective must not be empty")
        if self.token_budget <= 0 or self.max_items <= 0:
            raise ValueError("context bounds must be positive")
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be between zero and one")


@dataclass(frozen=True, slots=True)
class ContextItem:
    canonical_ref: CanonicalRef
    kind: str
    summary: str
    why_included: str
    confidence: float
    revision: SourceRevision
    provenance: Provenance
    token_estimate: int
    status: str


@dataclass(frozen=True, slots=True)
class ContextPackage:
    objective: str
    items: tuple[ContextItem, ...]
    used_tokens: int
    token_budget: int
    truncated: bool
    excluded_count: int


@dataclass(frozen=True, slots=True)
class WeakLocalEvidenceRequest:
    """A bounded request for task-relevant evidence, never repository-wide by default."""

    objective: str
    target_refs: tuple[CanonicalRef, ...] = ()
    token_budget: int = 2_000
    max_items: int = 12
    min_confidence: float = 0.0
    scope: EvidenceScope | None = None
    prior_evidence_ids: tuple[str, ...] = ()
    unresolved_gaps: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise ValueError("objective must not be empty")
        if self.token_budget <= 0 or self.max_items <= 0:
            raise ValueError("weak-local evidence bounds must be positive")
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be between zero and one")
        for values, name in (
            (self.prior_evidence_ids, "prior_evidence_ids"),
            (self.unresolved_gaps, "unresolved_gaps"),
        ):
            if any(not value.strip() for value in values):
                raise ValueError(f"{name} must not contain empty values")


@dataclass(frozen=True, slots=True)
class WeakLocalEvidenceItem:
    evidence_id: str
    canonical_ref: CanonicalRef
    kind: str
    summary: str
    reason: str
    confidence: float
    provenance_id: str
    status: str
    token_estimate: int


@dataclass(frozen=True, slots=True)
class WeakLocalEvidencePackage:
    """Task/revision evidence kept separate from the stable protocol prefix."""

    scope: EvidenceScope
    revision_id: str | None
    source_revision: SourceRevision | None
    objective_fingerprint: str
    items: tuple[WeakLocalEvidenceItem, ...]
    provenance: tuple[tuple[str, Provenance], ...]
    selected_evidence_ids: tuple[str, ...]
    prior_evidence_ids: tuple[str, ...]
    unresolved_gaps: tuple[str, ...]
    next_scope: EvidenceScope | None
    used_tokens: int
    token_budget: int
    candidate_count: int
    excluded_count: int
    truncated: bool
    candidate_search_truncated: bool
    deterministic_resolution: bool
