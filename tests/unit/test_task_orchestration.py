from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from extendcodeagent.core.config.schema import CapabilityName, Depth, RolloutMode
from extendcodeagent.core.contracts import ProjectRef, Provenance
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.orchestration import (
    MAX_OBJECTIVE_CHARS,
    IntelligenceLevel,
    TaskIntentName,
    TaskSignals,
    build_intelligence_plan,
    classify_task,
    create_shadow_plan,
    project_task_signals,
)
from extendcodeagent.runtime import (
    RuntimeAdapterCapability,
    RuntimeCapabilities,
    RuntimeCapabilityDeclaration,
    RuntimeCapabilityStatus,
    RuntimeSignal,
    RuntimeSignalKind,
    TaskSignalCollector,
)

PROJECT = ProjectRef("project", "workspace", "file:///repo")
NOW = datetime(2026, 8, 17, tzinfo=UTC)


def _policy(mode: RolloutMode = RolloutMode.SHADOW, depth: Depth = Depth.D2) -> CapabilityPolicy:
    return CapabilityPolicy(
        {name: mode for name in CapabilityName},
        {name: depth for name in CapabilityName},
    )


def _signals(objective: str) -> TaskSignals:
    return TaskSignals(PROJECT, objective)


def test_classifier_uses_general_task_language_not_evaluation_identity() -> None:
    cases = (
        ("Find the definition and explain the symbol callers.", TaskIntentName.LOCATE_EXPLAIN),
        (
            "Assess the change impact before touching this threshold.",
            TaskIntentName.IMPACT_ASSESSMENT,
        ),
        ("Select the minimum existing tests for this obligation.", TaskIntentName.TEST_SELECTION),
        ("Refactor this helper across several modules.", TaskIntentName.REFACTOR),
        (
            "The failing test exposes a production defect; reproduce, localize, and fix it.",
            TaskIntentName.BUG_FIX,
        ),
        (
            "Trace the requirement to its implementation and verifier.",
            TaskIntentName.REQUIREMENT_TRACE,
        ),
        (
            "Trace the user-visible causal flow through the HTTP runtime.",
            TaskIntentName.RUNTIME_BOUNDARY,
        ),
        (
            "Decide whether evidence is sufficient to claim completion.",
            TaskIntentName.INSUFFICIENT_EVIDENCE,
        ),
        (
            "Create note.txt containing exactly hello; no code analysis is needed.",
            TaskIntentName.MECHANICAL,
        ),
        ("Produce a migration plan for the architecture.", TaskIntentName.ARCHITECTURE),
        ("Research the current external protocol sources.", TaskIntentName.RESEARCH),
    )
    for objective, expected in cases:
        assert classify_task(_signals(objective)).primary is expected


def test_minimum_plan_is_policy_bounded_and_shadow_only() -> None:
    intent = classify_task(_signals("Trace the user-visible causal flow through the HTTP runtime."))
    policy = _policy()
    plan = build_intelligence_plan(
        _signals("Trace the user-visible causal flow through the HTTP runtime."), intent, policy
    )
    assert plan.level is IntelligenceLevel.L3_RUNTIME_AWARE
    assert plan.minimum_depth is Depth.D1
    assert plan.context_budget_tokens == 8_192
    assert plan.capabilities == (
        CapabilityName.GRAPH,
        CapabilityName.TWIN,
        CapabilityName.SEMANTIC,
        CapabilityName.CONTEXT,
        CapabilityName.RUNTIME,
        CapabilityName.TRACEABILITY,
        CapabilityName.CONVERGENCE,
    )
    assert plan.shadow_only is True

    modes = {name: RolloutMode.SHADOW for name in CapabilityName}
    modes[CapabilityName.RUNTIME] = RolloutMode.OFF
    bounded = CapabilityPolicy(modes, {name: Depth.D0 for name in CapabilityName})
    bounded_plan = build_intelligence_plan(
        _signals("Trace the user-visible causal flow through the HTTP runtime."), intent, bounded
    )
    assert CapabilityName.RUNTIME not in bounded_plan.capabilities
    assert bounded_plan.unavailable_capabilities == (CapabilityName.RUNTIME,)
    assert bounded_plan.minimum_depth is Depth.D0


def test_shadow_outcome_is_deterministic_and_never_applies_work() -> None:
    signals = _signals("Locate the definition and direct callers.")
    first = create_shadow_plan(signals, _policy())
    second = create_shadow_plan(signals, _policy())
    assert first.plan.plan_id == second.plan.plan_id
    assert first.actual_capabilities == ()
    assert first.actual_evidence_ids == ()
    assert first.behavior_changed is False
    assert first.llm_calls == 0


def test_plan_identity_changes_when_bounded_plan_semantics_change() -> None:
    signals = _signals("Locate the definition and direct callers.")
    base = create_shadow_plan(signals, _policy()).plan
    narrower = create_shadow_plan(replace(signals, max_items=10), _policy()).plan
    truncated = create_shadow_plan(replace(signals, objective_truncated=True), _policy()).plan

    assert base.query_bounds != narrower.query_bounds
    assert base.plan_id != narrower.plan_id
    assert base.intent.uncertainty != truncated.intent.uncertainty
    assert base.plan_id != truncated.plan_id


def test_runtime_projection_is_bounded_and_uses_latest_collector_values() -> None:
    collector = TaskSignalCollector(PROJECT)
    collector.connect(
        RuntimeCapabilities(
            "runtime",
            "1",
            tuple(
                RuntimeCapabilityDeclaration(
                    capability,
                    RuntimeCapabilityStatus.SUPPORTED,
                )
                for capability in RuntimeAdapterCapability
            ),
        )
    )
    producer = Provenance("runtime", "adapter", "1")
    collector.collect(
        RuntimeSignal(
            "mutation",
            RuntimeSignalKind.MUTATION,
            PROJECT,
            NOW,
            producer,
            paths=tuple(f"src/{index}.py" for index in range(80)),
            source_category="file.edited",
        )
    )
    collector.collect(
        RuntimeSignal(
            "task",
            RuntimeSignalKind.TASK,
            PROJECT,
            NOW,
            producer,
            runtime_session_id="session",
            task_text=(
                "Inspect src/service.py and helper_symbol before proceeding. "
                + "x" * (MAX_OBJECTIVE_CHARS + 100)
            ),
        )
    )
    signals = project_task_signals(collector.snapshot())
    assert signals is not None
    assert len(signals.objective) == MAX_OBJECTIVE_CHARS
    assert signals.objective_truncated is True
    assert signals.referenced_paths == ("src/service.py",)
    assert signals.referenced_symbols == ("helper_symbol",)
    assert signals.language_signals == ("python",)
    assert signals.framework_signals == ()
    assert signals.pi_freshness == "unknown"
    assert len(signals.changed_paths) == 64


def test_unknown_task_falls_back_to_native_without_guessing() -> None:
    outcome = create_shadow_plan(_signals("Hello there."), _policy())
    assert outcome.plan.intent.primary is TaskIntentName.UNKNOWN
    assert outcome.plan.level is IntelligenceLevel.L0_NATIVE
    assert outcome.plan.capabilities == ()
    assert outcome.plan.context_budget_tokens == 0
