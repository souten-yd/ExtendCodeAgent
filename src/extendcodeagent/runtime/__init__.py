"""Revision-aware runtime and verification intelligence."""

from .absence import ObservedAbsence, established_absences
from .contracts import (
    ObservationKind,
    ObservationRollup,
    ObservationStatus,
    ReconciliationDecision,
    ReconciliationOutcome,
    RuntimeAdapterCapability,
    RuntimeCapabilities,
    RuntimeCapabilityDeclaration,
    RuntimeCapabilityStatus,
    RuntimeObservation,
    RuntimeSignal,
    RuntimeSignalKind,
    RuntimeSignalSnapshot,
)
from .coverage import observation_from_coverage, symbols_touched
from .service import (
    TaskSignalCollector,
    covering_tests,
    reconcile_observations,
    summarize_observations,
    unavailable_observation,
)
from .triggers import ImprovementTrigger, TriggerKind, detect_triggers

__all__ = [
    "ImprovementTrigger",
    "ObservedAbsence",
    "ObservationKind",
    "ObservationRollup",
    "ObservationStatus",
    "ReconciliationDecision",
    "ReconciliationOutcome",
    "RuntimeObservation",
    "RuntimeAdapterCapability",
    "RuntimeCapabilities",
    "RuntimeCapabilityDeclaration",
    "RuntimeCapabilityStatus",
    "RuntimeSignal",
    "RuntimeSignalKind",
    "RuntimeSignalSnapshot",
    "TaskSignalCollector",
    "TriggerKind",
    "covering_tests",
    "established_absences",
    "detect_triggers",
    "observation_from_coverage",
    "symbols_touched",
    "reconcile_observations",
    "summarize_observations",
    "unavailable_observation",
]
