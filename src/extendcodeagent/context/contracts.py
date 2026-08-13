"""Bounded revision-aware context contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from extendcodeagent.core.contracts import CanonicalRef, Provenance, SourceRevision


class ContextProfile(StrEnum):
    STANDARD = "standard"
    WEAK = "weak"


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
