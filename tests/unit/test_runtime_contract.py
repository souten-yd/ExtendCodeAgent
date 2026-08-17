from __future__ import annotations

from datetime import UTC, datetime

import pytest

from extendcodeagent.core.contracts import ProjectRef, Provenance, SourceRevision
from extendcodeagent.runtime import (
    ObservationKind,
    ObservationStatus,
    RuntimeAdapterCapability,
    RuntimeCapabilities,
    RuntimeCapabilityDeclaration,
    RuntimeCapabilityStatus,
    RuntimeObservation,
    RuntimeSignal,
    RuntimeSignalKind,
    TaskSignalCollector,
)

NOW = datetime(2026, 8, 17, tzinfo=UTC)
PROJECT = ProjectRef("project", "workspace", "file:///repo")
PROVENANCE = Provenance("runtime", "test_adapter", "1")


def _capabilities(
    overrides: dict[RuntimeAdapterCapability, RuntimeCapabilityStatus] | None = None,
) -> RuntimeCapabilities:
    values = overrides or {}
    return RuntimeCapabilities(
        "test-runtime",
        "1",
        tuple(
            RuntimeCapabilityDeclaration(
                capability,
                values.get(capability, RuntimeCapabilityStatus.SUPPORTED),
                "test limitation" if capability in values else "",
            )
            for capability in RuntimeAdapterCapability
        ),
    )


def _signal(
    kind: RuntimeSignalKind,
    *,
    runtime_session_id: str | None = None,
    task_text: str | None = None,
    paths: tuple[str, ...] = (),
    source_category: str | None = None,
    lifecycle_state: str | None = None,
    model_provider: str | None = None,
    model_id: str | None = None,
    delivery_channel: str | None = None,
    tool: str | None = None,
) -> RuntimeSignal:
    return RuntimeSignal(
        f"signal:{kind.value}",
        kind,
        PROJECT,
        NOW,
        PROVENANCE,
        runtime_session_id,
        task_text,
        paths,
        source_category,
        lifecycle_state,
        model_provider,
        model_id,
        delivery_channel,
        tool,
    )


def test_collector_consumes_each_retained_runtime_field() -> None:
    collector = TaskSignalCollector(PROJECT)
    collector.connect(_capabilities())
    task = _signal(RuntimeSignalKind.TASK, runtime_session_id="session", task_text="fix leaf")
    session = _signal(
        RuntimeSignalKind.SESSION,
        runtime_session_id="session",
        lifecycle_state="created",
    )
    mutation = _signal(
        RuntimeSignalKind.MUTATION,
        paths=("service.py",),
        source_category="file.edited",
    )
    model = _signal(
        RuntimeSignalKind.MODEL,
        runtime_session_id="session",
        model_provider="local",
        model_id="qwen",
    )
    advisory = _signal(
        RuntimeSignalKind.ADVISORY_DELIVERY,
        runtime_session_id="session",
        delivery_channel="tool",
        tool="pi_symbol",
    )
    for signal in (task, session, mutation, model, advisory):
        assert collector.collect(signal) is True

    revision = SourceRevision("revision")
    verification = RuntimeObservation(
        "observation",
        ObservationKind.TEST,
        PROJECT,
        revision,
        ObservationStatus.PASSED,
        NOW,
        NOW,
        Provenance("runtime", "pytest", "1", revision),
        command="pytest",
        runtime_session_id="session",
        runtime_call_id="call",
    )
    assert collector.collect_observation(verification) is True

    snapshot = collector.snapshot()
    assert snapshot.latest_task == task
    assert snapshot.latest_session == session
    assert snapshot.latest_mutation == mutation
    assert snapshot.latest_model == model
    assert snapshot.latest_advisory_delivery == advisory
    assert snapshot.tool_execution_count == 1
    assert snapshot.verification_count == 1
    assert snapshot.latest_tool_observation_id == "observation"
    assert snapshot.latest_verification_observation_id == "observation"
    assert snapshot.diagnostics == ()


def test_missing_and_degraded_capabilities_fail_or_degrade_explicitly() -> None:
    collector = TaskSignalCollector(PROJECT)
    collector.connect(
        _capabilities(
            {
                RuntimeAdapterCapability.OBSERVE_TASK: RuntimeCapabilityStatus.UNAVAILABLE,
                RuntimeAdapterCapability.OBSERVE_FILE_MUTATION: RuntimeCapabilityStatus.DEGRADED,
            }
        )
    )
    assert (
        collector.collect(
            _signal(RuntimeSignalKind.TASK, runtime_session_id="session", task_text="task")
        )
        is False
    )
    assert (
        collector.collect(
            _signal(
                RuntimeSignalKind.MUTATION,
                paths=(),
                source_category="filesystem-fallback",
            )
        )
        is True
    )
    assert collector.snapshot().latest_task is None
    assert collector.snapshot().latest_mutation is not None
    assert collector.snapshot().diagnostics == (
        "observe_task:unavailable:test limitation",
        "observe_file_mutation:degraded:test limitation",
    )


def test_verification_observation_does_not_depend_on_general_tool_observation() -> None:
    collector = TaskSignalCollector(PROJECT)
    capability = RuntimeAdapterCapability.OBSERVE_TOOL_EXECUTION
    collector.connect(_capabilities({capability: RuntimeCapabilityStatus.UNAVAILABLE}))
    revision = SourceRevision("revision")
    observation = RuntimeObservation(
        "verification",
        ObservationKind.TEST,
        PROJECT,
        revision,
        ObservationStatus.PASSED,
        NOW,
        NOW,
        Provenance("runtime", "pytest", "1", revision),
        command="pytest",
    )
    assert collector.collect_observation(observation) is True
    snapshot = collector.snapshot()
    assert snapshot.tool_execution_count == 0
    assert snapshot.verification_count == 1
    assert snapshot.diagnostics == ("observe_tool_execution:unavailable:test limitation",)


def test_capability_descriptor_is_exhaustive_and_non_success_requires_reason() -> None:
    with pytest.raises(ValueError, match="must be exhaustive"):
        RuntimeCapabilities("runtime", "1", ())
    with pytest.raises(ValueError, match="requires a reason"):
        RuntimeCapabilityDeclaration(
            RuntimeAdapterCapability.DELIVER_CONTEXT,
            RuntimeCapabilityStatus.UNAVAILABLE,
        )
