"""Deterministic revision freshness and truthful runtime rollups."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from extendcodeagent.core.contracts import CanonicalRef, ProjectRef, Provenance, SourceRevision

from .contracts import (
    ObservationKind,
    ObservationRollup,
    ObservationStatus,
    ReconciliationDecision,
    ReconciliationOutcome,
    RuntimeObservation,
)


def reconcile_observations(
    canonical_ref: CanonicalRef,
    current_revision: SourceRevision,
    observations: Iterable[RuntimeObservation],
) -> ReconciliationOutcome:
    relevant = tuple(item for item in observations if canonical_ref in item.observed_refs)
    if not relevant:
        return ReconciliationOutcome(
            canonical_ref,
            current_revision,
            ReconciliationDecision.NOT_OBSERVED,
            False,
            diagnostics=("no runtime observation for ref",),
        )
    fresh = tuple(item for item in relevant if item.source_revision == current_revision)
    stale = tuple(item for item in relevant if item.source_revision != current_revision)
    failed = tuple(item for item in fresh if item.status is ObservationStatus.FAILED)
    if failed:
        return _outcome(
            canonical_ref,
            current_revision,
            ReconciliationDecision.CONTRADICTED,
            failed,
            "fresh runtime evidence failed",
        )
    passed = tuple(item for item in fresh if item.status is ObservationStatus.PASSED)
    if passed:
        return ReconciliationOutcome(
            canonical_ref,
            current_revision,
            ReconciliationDecision.VERIFIED,
            True,
            tuple(item.observation_id for item in passed),
        )
    unavailable = tuple(item for item in fresh if item.status is ObservationStatus.UNAVAILABLE)
    if unavailable:
        return _outcome(
            canonical_ref,
            current_revision,
            ReconciliationDecision.UNAVAILABLE,
            unavailable,
            "fresh instrumentation was unavailable",
        )
    observed = tuple(item for item in fresh if item.status is ObservationStatus.OBSERVED)
    if observed:
        return _outcome(
            canonical_ref,
            current_revision,
            ReconciliationDecision.OBSERVED,
            observed,
            "runtime evidence observed the ref without verification",
        )
    return _outcome(
        canonical_ref,
        current_revision,
        ReconciliationDecision.STALE,
        stale,
        "only older-revision runtime evidence exists",
    )


def summarize_observations(
    observations: Iterable[RuntimeObservation],
) -> ObservationRollup:
    values = tuple(observations)
    passed = sum(item.status is ObservationStatus.PASSED for item in values)
    failed = sum(item.status is ObservationStatus.FAILED for item in values)
    observed = sum(item.status is ObservationStatus.OBSERVED for item in values)
    unavailable = sum(item.status is ObservationStatus.UNAVAILABLE for item in values)
    diagnostics = tuple(
        message
        for count, message in (
            (failed, f"{failed} failed observation(s)"),
            (unavailable, f"{unavailable} unavailable observation(s)"),
        )
        if count
    )
    return ObservationRollup(
        passed > 0 and failed == 0 and unavailable == 0,
        passed,
        failed,
        observed,
        unavailable,
        diagnostics,
    )


def unavailable_observation(
    *,
    observation_id: str,
    kind: ObservationKind,
    project: ProjectRef,
    source_revision: SourceRevision,
    provenance: Provenance,
    summary: str,
    observed_refs: tuple[CanonicalRef, ...] = (),
    observed_at: datetime | None = None,
) -> RuntimeObservation:
    timestamp = observed_at or datetime.now(UTC)
    return RuntimeObservation(
        observation_id,
        kind,
        project,
        source_revision,
        ObservationStatus.UNAVAILABLE,
        timestamp,
        timestamp,
        provenance,
        observed_refs=observed_refs,
        summary=summary,
    )


def _outcome(
    canonical_ref: CanonicalRef,
    source_revision: SourceRevision,
    decision: ReconciliationDecision,
    observations: tuple[RuntimeObservation, ...],
    diagnostic: str,
) -> ReconciliationOutcome:
    return ReconciliationOutcome(
        canonical_ref,
        source_revision,
        decision,
        False,
        tuple(item.observation_id for item in observations),
        (diagnostic,),
    )
