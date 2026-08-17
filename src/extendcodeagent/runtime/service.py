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
    RuntimeAdapterCapability,
    RuntimeCapabilities,
    RuntimeCapabilityStatus,
    RuntimeObservation,
    RuntimeSignal,
    RuntimeSignalKind,
    RuntimeSignalSnapshot,
)

_SIGNAL_CAPABILITY = {
    RuntimeSignalKind.TASK: (RuntimeAdapterCapability.OBSERVE_TASK,),
    RuntimeSignalKind.SESSION: (
        RuntimeAdapterCapability.OBSERVE_SESSION,
        RuntimeAdapterCapability.SESSION_LIFECYCLE,
    ),
    RuntimeSignalKind.MUTATION: (RuntimeAdapterCapability.OBSERVE_FILE_MUTATION,),
    RuntimeSignalKind.MODEL: (RuntimeAdapterCapability.OBSERVE_MODEL_ROUTE,),
    RuntimeSignalKind.ADVISORY_DELIVERY: (RuntimeAdapterCapability.EXPOSE_TOOLS,),
}


class TaskSignalCollector:
    """Consume normalized runtime inputs without retaining a competing truth store."""

    def __init__(self, project: ProjectRef) -> None:
        self._project = project
        self._capabilities: RuntimeCapabilities | None = None
        self._signals: dict[RuntimeSignalKind, RuntimeSignal] = {}
        self._tool_execution_count = 0
        self._verification_count = 0
        self._latest_tool_observation_id: str | None = None
        self._latest_verification_observation_id: str | None = None
        self._diagnostics: dict[str, None] = {}

    def connect(self, capabilities: RuntimeCapabilities) -> None:
        self._capabilities = capabilities
        self._diagnostics.clear()

    def collect(self, signal: RuntimeSignal) -> bool:
        self._validate_project(signal.project)
        if not all(self._accepts(capability) for capability in _SIGNAL_CAPABILITY[signal.kind]):
            return False
        self._signals[signal.kind] = signal
        return True

    def collect_observation(self, observation: RuntimeObservation) -> bool:
        self._validate_project(observation.project)
        tool_accepted = self._accepts(RuntimeAdapterCapability.OBSERVE_TOOL_EXECUTION)
        verification_accepted = observation.kind is not ObservationKind.RUNTIME and self._accepts(
            RuntimeAdapterCapability.OBSERVE_VERIFICATION
        )
        if tool_accepted:
            self._tool_execution_count += 1
            self._latest_tool_observation_id = observation.observation_id
        if verification_accepted:
            self._verification_count += 1
            self._latest_verification_observation_id = observation.observation_id
        return tool_accepted or verification_accepted

    def snapshot(self) -> RuntimeSignalSnapshot:
        return RuntimeSignalSnapshot(
            self._project,
            self._capabilities,
            self._signals.get(RuntimeSignalKind.TASK),
            self._signals.get(RuntimeSignalKind.SESSION),
            self._signals.get(RuntimeSignalKind.MUTATION),
            self._signals.get(RuntimeSignalKind.MODEL),
            self._signals.get(RuntimeSignalKind.ADVISORY_DELIVERY),
            self._tool_execution_count,
            self._verification_count,
            self._latest_tool_observation_id,
            self._latest_verification_observation_id,
            tuple(self._diagnostics),
        )

    def _accepts(self, capability: RuntimeAdapterCapability) -> bool:
        if self._capabilities is None:
            self._diagnostics["runtime_capabilities_not_negotiated"] = None
            return False
        declaration = self._capabilities.declaration(capability)
        if declaration.status is RuntimeCapabilityStatus.UNAVAILABLE:
            self._diagnostics[f"{capability.value}:unavailable:{declaration.reason}"] = None
            return False
        if declaration.status is RuntimeCapabilityStatus.DEGRADED:
            self._diagnostics[f"{capability.value}:degraded:{declaration.reason}"] = None
        return True

    def _validate_project(self, project: ProjectRef) -> None:
        if (
            project.project_id,
            project.workspace_id,
            project.root_uri,
        ) != (
            self._project.project_id,
            self._project.workspace_id,
            self._project.root_uri,
        ):
            raise ValueError("runtime signal project does not match collector project")


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
