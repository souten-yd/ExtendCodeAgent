"""Contracts for deterministic test selection and evidence-based test health."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from extendcodeagent.core.contracts import CanonicalRef
from extendcodeagent.runtime import RuntimeObservation


@dataclass(frozen=True, slots=True)
class TestCandidate:
    canonical_ref: CanonicalRef
    source_ref: str
    confidence: float
    reason: str


@dataclass(frozen=True, slots=True)
class TestSelectionResult:
    candidates: tuple[TestCandidate, ...]
    fallback: str | None
    minimum_confidence: float
    diagnostics: tuple[str, ...] = ()


class TestHealthState(StrEnum):
    HEALTHY = "healthy"
    SUSPECT = "suspect"
    STALE = "stale"
    OBSOLETE = "obsolete"
    MISSING = "missing"
    REDUNDANT = "redundant"


@dataclass(frozen=True, slots=True)
class TestHealthSignals:
    test_ref: CanonicalRef
    target_refs: tuple[CanonicalRef, ...] = ()
    changed_refs: tuple[CanonicalRef, ...] = ()
    removed_refs: tuple[CanonicalRef, ...] = ()
    observations: tuple[RuntimeObservation, ...] = ()
    exists: bool = True
    disabled: bool = False
    redundant_with: CanonicalRef | None = None
    behavior_path_changed: bool = False
    coverage_dropped: bool = False
    assertion_relevant: bool | None = None


@dataclass(frozen=True, slots=True)
class TestHealthResult:
    test_ref: CanonicalRef
    state: TestHealthState
    reasons: tuple[str, ...]
    evidence_ids: tuple[str, ...] = ()
    delete_recommended: bool = False
