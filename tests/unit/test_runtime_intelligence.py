from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from extendcodeagent.core.contracts import (
    CanonicalRef,
    EvidenceRef,
    EvidenceStatus,
    ProjectRef,
    Provenance,
    SourceRevision,
)
from extendcodeagent.runtime import (
    ObservationKind,
    ObservationStatus,
    ReconciliationDecision,
    RuntimeObservation,
    reconcile_observations,
    summarize_observations,
    unavailable_observation,
)

NOW = datetime(2026, 8, 13, tzinfo=UTC)
PROJECT = ProjectRef("project", "workspace", "file:///repo")
PROVENANCE = Provenance("tool", "pytest", "1")


def _observation(
    status: ObservationStatus,
    revision: str = "rev-1",
    *,
    observation_id: str = "obs-1",
) -> RuntimeObservation:
    return RuntimeObservation(
        observation_id=observation_id,
        kind=ObservationKind.TEST,
        project=PROJECT,
        source_revision=SourceRevision(revision),
        status=status,
        observed_refs=(CanonicalRef("py://service#handler"),),
        started_at=NOW,
        finished_at=NOW + timedelta(seconds=1),
        command="pytest tests/test_service.py",
        provenance=PROVENANCE,
        artifacts=(EvidenceRef("artifact-1", EvidenceStatus.OBSERVED),),
    )


def test_runtime_observation_is_immutable_and_time_ordered() -> None:
    observation = _observation(ObservationStatus.PASSED)
    with pytest.raises((AttributeError, TypeError)):
        observation.status = ObservationStatus.FAILED  # type: ignore[misc]
    with pytest.raises(ValueError, match="finished_at"):
        RuntimeObservation(
            observation_id="bad",
            kind=ObservationKind.BUILD,
            project=PROJECT,
            source_revision=SourceRevision("rev-1"),
            status=ObservationStatus.FAILED,
            started_at=NOW,
            finished_at=NOW - timedelta(seconds=1),
            provenance=PROVENANCE,
        )


def test_only_matching_revision_pass_verifies_a_ref() -> None:
    fresh = reconcile_observations(
        CanonicalRef("py://service#handler"),
        SourceRevision("rev-1"),
        (_observation(ObservationStatus.PASSED),),
    )
    stale = reconcile_observations(
        CanonicalRef("py://service#handler"),
        SourceRevision("rev-2"),
        (_observation(ObservationStatus.PASSED),),
    )
    assert fresh.decision is ReconciliationDecision.VERIFIED
    assert stale.decision is ReconciliationDecision.STALE
    assert stale.verified is False


def test_unavailable_and_collector_failure_never_roll_up_to_success() -> None:
    passed = _observation(ObservationStatus.PASSED)
    unavailable = unavailable_observation(
        observation_id="collector-failed",
        kind=ObservationKind.RUNTIME,
        project=PROJECT,
        source_revision=SourceRevision("rev-1"),
        provenance=PROVENANCE,
        summary="collector crashed",
        observed_refs=(CanonicalRef("py://service#handler"),),
    )
    reconciliation = reconcile_observations(
        CanonicalRef("py://service#handler"),
        SourceRevision("rev-1"),
        (unavailable,),
    )
    rollup = summarize_observations((passed, unavailable))
    assert reconciliation.decision is ReconciliationDecision.UNAVAILABLE
    assert reconciliation.verified is False
    assert rollup.success is False
    assert rollup.unavailable == 1
