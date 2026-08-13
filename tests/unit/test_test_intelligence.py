from __future__ import annotations

from datetime import UTC, datetime

import pytest

from extendcodeagent.analysis import ImpactItem, ImpactReport
from extendcodeagent.core.contracts import CanonicalRef, ProjectRef, Provenance, SourceRevision
from extendcodeagent.graph import FactStatus
from extendcodeagent.runtime import ObservationKind, ObservationStatus, RuntimeObservation
from extendcodeagent.testing import (
    TestHealthSignals as HealthSignals,
)
from extendcodeagent.testing import (
    TestHealthState as HealthState,
)
from extendcodeagent.testing import (
    evaluate_test_health,
    select_tests,
)

NOW = datetime(2026, 8, 13, tzinfo=UTC)
PROJECT = ProjectRef("project", "workspace", "file:///repo")
PROVENANCE = Provenance("tool", "pytest", "1")
TEST_REF = CanonicalRef("py://test_service#test_handler")
TARGET_REF = CanonicalRef("py://service#handler")


def _item(confidence: float) -> ImpactItem:
    return ImpactItem(
        TEST_REF.value,
        "test",
        FactStatus.DECLARED,
        confidence,
        confidence,
        "test_service.py",
        "reverse_dependency_depth_1",
    )


def _observation(status: ObservationStatus, revision: str) -> RuntimeObservation:
    return RuntimeObservation(
        observation_id=f"obs-{status.value}-{revision}",
        kind=ObservationKind.TEST,
        project=PROJECT,
        source_revision=SourceRevision(revision),
        status=status,
        observed_refs=(TEST_REF, TARGET_REF),
        started_at=NOW,
        finished_at=NOW,
        provenance=PROVENANCE,
        tool="pytest",
    )


def test_test_selection_falls_back_for_missing_or_low_confidence_candidates() -> None:
    missing = select_tests(ImpactReport(None), minimum_confidence=0.7)
    low = select_tests(ImpactReport(None, recommended_tests=(_item(0.35),)), minimum_confidence=0.7)
    high = select_tests(ImpactReport(None, recommended_tests=(_item(0.9),)), minimum_confidence=0.7)
    assert missing.fallback == "full_suite" and not missing.candidates
    assert low.fallback == "full_suite" and low.candidates[0].confidence == 0.35
    assert high.fallback is None and high.candidates[0].canonical_ref == TEST_REF


@pytest.mark.parametrize(
    ("signals", "expected"),
    [
        (HealthSignals(TEST_REF, exists=False), HealthState.MISSING),
        (
            HealthSignals(TEST_REF, redundant_with=CanonicalRef("test://duplicate")),
            HealthState.REDUNDANT,
        ),
        (
            HealthSignals(TEST_REF, target_refs=(TARGET_REF,), removed_refs=(TARGET_REF,)),
            HealthState.OBSOLETE,
        ),
        (
            HealthSignals(
                TEST_REF,
                target_refs=(TARGET_REF,),
                changed_refs=(TARGET_REF,),
                observations=(_observation(ObservationStatus.PASSED, "rev-1"),),
            ),
            HealthState.STALE,
        ),
        (HealthSignals(TEST_REF, disabled=True), HealthState.SUSPECT),
        (
            HealthSignals(
                TEST_REF,
                target_refs=(TARGET_REF,),
                observations=(_observation(ObservationStatus.PASSED, "rev-2"),),
            ),
            HealthState.HEALTHY,
        ),
    ],
)
def test_test_health_states_are_evidence_based(
    signals: HealthSignals, expected: HealthState
) -> None:
    result = evaluate_test_health(signals, current_revision=SourceRevision("rev-2"))
    assert result.state is expected
    assert result.reasons
    assert result.delete_recommended is False
