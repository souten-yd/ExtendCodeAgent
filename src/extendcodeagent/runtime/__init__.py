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
from .receipt import EditReceipt, completed_paths, receipt_json
from .service import (
    TaskSignalCollector,
    covering_tests,
    reconcile_observations,
    summarize_observations,
    unavailable_observation,
)
from .task_state import (
    Attempt,
    AttemptOutcome,
    TaskExecutionState,
    advance,
    remaining_after,
    task_state_json,
)
from .triggers import ImprovementTrigger, TriggerKind, detect_triggers

__all__ = [
    "Attempt",
    "AttemptOutcome",
    "EditReceipt",
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
    "TaskExecutionState",
    "TriggerKind",
    "advance",
    "completed_paths",
    "covering_tests",
    "established_absences",
    "receipt_json",
    "remaining_after",
    "task_state_json",
    "detect_triggers",
    "observation_from_coverage",
    "symbols_touched",
    "reconcile_observations",
    "summarize_observations",
    "unavailable_observation",
]
