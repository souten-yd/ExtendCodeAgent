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
from .execution_discovery import declared_profile, discover_from_root
from .execution_profile import (
    ExecutionCommand,
    ExecutionProfile,
    KnowledgeSource,
    profile_json,
)
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
    "ExecutionCommand",
    "ExecutionProfile",
    "ImprovementTrigger",
    "KnowledgeSource",
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
    "declared_profile",
    "discover_from_root",
    "established_absences",
    "receipt_json",
    "remaining_after",
    "task_state_json",
    "detect_triggers",
    "observation_from_coverage",
    "profile_json",
    "symbols_touched",
    "reconcile_observations",
    "summarize_observations",
    "unavailable_observation",
]
