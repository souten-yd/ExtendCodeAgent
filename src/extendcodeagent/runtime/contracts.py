"""Host-neutral runtime observations and truthful reconciliation results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from extendcodeagent.core.contracts import (
    CanonicalRef,
    EvidenceRef,
    ProjectRef,
    Provenance,
    SourceRevision,
)


class ObservationKind(StrEnum):
    TEST = "test"
    LINT = "lint"
    BUILD = "build"
    TYPECHECK = "typecheck"
    SMOKE = "smoke"
    BENCHMARK = "benchmark"
    RUNTIME = "runtime"


class ObservationStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    OBSERVED = "observed"
    UNAVAILABLE = "unavailable"


class ReconciliationDecision(StrEnum):
    VERIFIED = "verified"
    CONTRADICTED = "contradicted"
    OBSERVED = "observed"
    STALE = "stale"
    UNAVAILABLE = "unavailable"
    NOT_OBSERVED = "not_observed"


class RuntimeAdapterCapability(StrEnum):
    """Host features that bound which runtime observations PI may trust."""

    OBSERVE_TASK = "observe_task"
    OBSERVE_SESSION = "observe_session"
    OBSERVE_FILE_MUTATION = "observe_file_mutation"
    OBSERVE_TOOL_EXECUTION = "observe_tool_execution"
    OBSERVE_MODEL_ROUTE = "observe_model_route"
    OBSERVE_VERIFICATION = "observe_verification"
    DELIVER_CONTEXT = "deliver_context"
    EXPOSE_TOOLS = "expose_tools"
    REQUEST_MODEL = "request_model"
    SESSION_LIFECYCLE = "session_lifecycle"
    RECONNECT = "reconnect"
    MCP = "mcp"


class RuntimeCapabilityStatus(StrEnum):
    SUPPORTED = "supported"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class RuntimeCapabilityDeclaration:
    capability: RuntimeAdapterCapability
    status: RuntimeCapabilityStatus
    reason: str = ""

    def __post_init__(self) -> None:
        if self.status is not RuntimeCapabilityStatus.SUPPORTED and not self.reason.strip():
            raise ValueError("degraded or unavailable runtime capability requires a reason")


@dataclass(frozen=True, slots=True)
class RuntimeCapabilities:
    runtime_name: str
    runtime_version: str
    declarations: tuple[RuntimeCapabilityDeclaration, ...]

    def __post_init__(self) -> None:
        if not self.runtime_name.strip():
            raise ValueError("runtime_name must not be empty")
        if not self.runtime_version.strip():
            raise ValueError("runtime_version must not be empty")
        names = tuple(item.capability for item in self.declarations)
        if len(set(names)) != len(names):
            raise ValueError("runtime capability declarations must be unique")
        missing = set(RuntimeAdapterCapability) - set(names)
        extra = set(names) - set(RuntimeAdapterCapability)
        if missing or extra:
            raise ValueError(
                "runtime capability declarations must be exhaustive: "
                f"missing={sorted(item.value for item in missing)}, "
                f"extra={sorted(str(item) for item in extra)}"
            )

    def declaration(self, capability: RuntimeAdapterCapability) -> RuntimeCapabilityDeclaration:
        return next(item for item in self.declarations if item.capability is capability)


class RuntimeSignalKind(StrEnum):
    TASK = "task"
    SESSION = "session"
    MUTATION = "mutation"
    MODEL = "model"
    ADVISORY_DELIVERY = "advisory_delivery"


@dataclass(frozen=True, slots=True)
class RuntimeSignal:
    """Small host-neutral signal; raw host event objects never enter Core."""

    signal_id: str
    kind: RuntimeSignalKind
    project: ProjectRef
    observed_at: datetime
    provenance: Provenance
    runtime_session_id: str | None = None
    task_text: str | None = None
    paths: tuple[str, ...] = ()
    source_category: str | None = None
    lifecycle_state: str | None = None
    model_provider: str | None = None
    model_id: str | None = None
    delivery_channel: str | None = None
    tool: str | None = None

    def __post_init__(self) -> None:
        if not self.signal_id.strip():
            raise ValueError("signal_id must not be empty")
        required: tuple[tuple[object, str], ...]
        if self.kind is RuntimeSignalKind.TASK:
            required = (
                (self.runtime_session_id, "runtime_session_id"),
                (self.task_text, "task_text"),
            )
        elif self.kind is RuntimeSignalKind.SESSION:
            required = (
                (self.runtime_session_id, "runtime_session_id"),
                (self.lifecycle_state, "lifecycle_state"),
            )
        elif self.kind is RuntimeSignalKind.MUTATION:
            required = ((self.source_category, "source_category"),)
        elif self.kind is RuntimeSignalKind.MODEL:
            required = (
                (self.runtime_session_id, "runtime_session_id"),
                (self.model_provider, "model_provider"),
                (self.model_id, "model_id"),
            )
        else:
            required = (
                (self.runtime_session_id, "runtime_session_id"),
                (self.delivery_channel, "delivery_channel"),
                (self.tool, "tool"),
            )
        for value, field_name in required:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required for {self.kind.value} signals")


@dataclass(frozen=True, slots=True)
class RuntimeSignalSnapshot:
    """The exact runtime inputs available to the future task-aware planner."""

    project: ProjectRef
    capabilities: RuntimeCapabilities | None
    latest_task: RuntimeSignal | None = None
    latest_session: RuntimeSignal | None = None
    latest_mutation: RuntimeSignal | None = None
    latest_model: RuntimeSignal | None = None
    latest_advisory_delivery: RuntimeSignal | None = None
    tool_execution_count: int = 0
    verification_count: int = 0
    latest_tool_observation_id: str | None = None
    latest_verification_observation_id: str | None = None
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RuntimeObservation:
    observation_id: str
    kind: ObservationKind
    project: ProjectRef
    source_revision: SourceRevision
    status: ObservationStatus
    started_at: datetime
    finished_at: datetime
    provenance: Provenance
    observed_refs: tuple[CanonicalRef, ...] = ()
    command: str | None = None
    tool: str | None = None
    artifacts: tuple[EvidenceRef, ...] = ()
    summary: str = ""
    runtime_session_id: str | None = None
    runtime_call_id: str | None = None

    def __post_init__(self) -> None:
        if not self.observation_id.strip():
            raise ValueError("observation_id must not be empty")
        if self.finished_at < self.started_at:
            raise ValueError("finished_at must not precede started_at")
        if not self.command and not self.tool and self.status is not ObservationStatus.UNAVAILABLE:
            raise ValueError("command or tool is required for an available observation")
        for value, field_name in (
            (self.runtime_session_id, "runtime_session_id"),
            (self.runtime_call_id, "runtime_call_id"),
        ):
            if value is not None and not value.strip():
                raise ValueError(f"{field_name} must not be empty when provided")


@dataclass(frozen=True, slots=True)
class ReconciliationOutcome:
    canonical_ref: CanonicalRef
    source_revision: SourceRevision
    decision: ReconciliationDecision
    verified: bool
    observation_ids: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ObservationRollup:
    success: bool
    passed: int
    failed: int
    observed: int
    unavailable: int
    diagnostics: tuple[str, ...] = ()
