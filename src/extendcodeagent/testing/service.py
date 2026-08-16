"""Deterministic test selection and test-obsolescence classification."""

from __future__ import annotations

from extendcodeagent.analysis import ImpactReport
from extendcodeagent.core.config.schema import CapabilityName
from extendcodeagent.core.contracts import CanonicalRef, SourceRevision
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.runtime import ObservationStatus

from .contracts import (
    TestCandidate,
    TestHealthResult,
    TestHealthSignals,
    TestHealthState,
    TestSelectionResult,
)


def select_tests(report: ImpactReport, *, minimum_confidence: float = 0.7) -> TestSelectionResult:
    if not 0.0 <= minimum_confidence <= 1.0:
        raise ValueError("minimum_confidence must be between zero and one")
    candidates = tuple(
        TestCandidate(
            CanonicalRef(item.canonical_ref),
            item.source_ref,
            min(item.confidence, item.path_confidence),
            item.reason,
        )
        for item in report.recommended_tests
    )
    low = tuple(item for item in candidates if item.confidence < minimum_confidence)
    fallback = "full_suite" if not candidates or low else None
    diagnostics = (
        ("no graph-linked test candidate",)
        if not candidates
        else (("candidate confidence below safe threshold",) if low else ())
    )
    return TestSelectionResult(candidates, fallback, minimum_confidence, diagnostics)


def evaluate_test_health(
    signals: TestHealthSignals,
    *,
    current_revision: SourceRevision,
    policy: CapabilityPolicy,
) -> TestHealthResult:
    policy.require_explicit_use(CapabilityName.TEST_OBSOLESCENCE)
    if not signals.exists:
        return _health(signals, TestHealthState.MISSING, "test target does not exist")
    if signals.redundant_with is not None:
        return _health(
            signals,
            TestHealthState.REDUNDANT,
            f"duplicates evidence from {signals.redundant_with.value}",
        )
    if signals.target_refs and set(signals.target_refs) <= set(signals.removed_refs):
        return _health(signals, TestHealthState.OBSOLETE, "all observed target refs were removed")
    if signals.disabled:
        return _health(signals, TestHealthState.SUSPECT, "test is disabled or skipped")
    if signals.coverage_dropped:
        return _health(signals, TestHealthState.SUSPECT, "runtime coverage dropped")
    if signals.assertion_relevant is False:
        return _health(signals, TestHealthState.SUSPECT, "assertion relevance is no longer proven")

    relevant = tuple(
        item
        for item in signals.observations
        if signals.test_ref in item.observed_refs
        or any(target in item.observed_refs for target in signals.target_refs)
    )
    fresh = tuple(item for item in relevant if item.source_revision == current_revision)
    fresh_passed = tuple(item for item in fresh if item.status is ObservationStatus.PASSED)
    impacted = bool(set(signals.target_refs) & set(signals.changed_refs))
    if fresh_passed and not signals.behavior_path_changed:
        return _health(
            signals,
            TestHealthState.HEALTHY,
            "matching-revision passing evidence covers the target",
            fresh_passed,
        )
    stale_passed = tuple(
        item
        for item in relevant
        if item.source_revision != current_revision and item.status is ObservationStatus.PASSED
    )
    if stale_passed and (impacted or signals.behavior_path_changed):
        return _health(
            signals,
            TestHealthState.STALE,
            "implementation changed after the last passing evidence",
            stale_passed,
        )
    if any(item.status is ObservationStatus.FAILED for item in fresh):
        return _health(
            signals,
            TestHealthState.SUSPECT,
            "matching-revision test evidence failed",
            fresh,
        )
    if any(item.status is ObservationStatus.UNAVAILABLE for item in fresh):
        return _health(
            signals,
            TestHealthState.SUSPECT,
            "matching-revision evidence is unavailable",
            fresh,
        )
    return _health(signals, TestHealthState.SUSPECT, "no matching-revision passing evidence")


def _health(
    signals: TestHealthSignals,
    state: TestHealthState,
    reason: str,
    observations: tuple[object, ...] = (),
) -> TestHealthResult:
    evidence_ids = tuple(
        item.observation_id for item in observations if hasattr(item, "observation_id")
    )
    return TestHealthResult(signals.test_ref, state, (reason,), evidence_ids, False)
