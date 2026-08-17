"""Revision-aware runtime and verification intelligence."""

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
from .service import (
    TaskSignalCollector,
    reconcile_observations,
    summarize_observations,
    unavailable_observation,
)

__all__ = [
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
    "reconcile_observations",
    "summarize_observations",
    "unavailable_observation",
]
