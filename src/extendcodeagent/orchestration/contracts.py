"""Compact host-neutral contracts for deterministic task-aware planning."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from extendcodeagent.core.config.schema import CapabilityName, Depth, RemoteCodePolicy
from extendcodeagent.core.contracts import ProjectRef, QueryBounds


class TaskIntentName(StrEnum):
    MECHANICAL = "mechanical"
    LOCATE_EXPLAIN = "locate_explain"
    IMPACT_ASSESSMENT = "impact_assessment"
    TEST_SELECTION = "test_selection"
    REFACTOR = "refactor"
    BUG_FIX = "bug_fix"
    REQUIREMENT_TRACE = "requirement_trace"
    RUNTIME_BOUNDARY = "runtime_boundary"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    ARCHITECTURE = "architecture"
    RESEARCH = "research"
    CHANGE = "change"
    UNKNOWN = "unknown"


class IntentUncertainty(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IntelligenceLevel(StrEnum):
    L0_NATIVE = "L0"
    L1_UNDERSTAND = "L1"
    L2_CHANGE = "L2"
    L3_RUNTIME_AWARE = "L3"
    L4_STRATEGIC = "L4"
    L5_DEEP_ON_DEMAND = "L5"


class ContextScope(StrEnum):
    NONE = "none"
    SYMBOL = "symbol"
    NEIGHBORHOOD = "neighborhood"
    IMPACT = "impact"
    RUNTIME_BOUNDARY = "runtime_boundary"
    STRATEGIC = "strategic"
    RESEARCH = "research"


@dataclass(frozen=True, slots=True)
class TaskSignals:
    """Bounded deterministic projection of runtime and project inputs."""

    project: ProjectRef
    objective: str
    referenced_paths: tuple[str, ...] = ()
    referenced_symbols: tuple[str, ...] = ()
    changed_paths: tuple[str, ...] = ()
    language_signals: tuple[str, ...] = ()
    framework_signals: tuple[str, ...] = ()
    prior_task_stage: str | None = None
    pi_freshness: str = "unknown"
    privacy_policy: RemoteCodePolicy = RemoteCodePolicy.DENY
    model_provider: str | None = None
    model_id: str | None = None
    runtime_evidence_available: bool = False
    verification_evidence_available: bool = False
    previous_failure_classes: tuple[str, ...] = ()
    context_token_limit: int = 8_192
    max_items: int = 100
    max_depth: int = 6
    objective_truncated: bool = False

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise ValueError("task objective must not be empty")
        if self.context_token_limit <= 0 or self.max_items <= 0 or self.max_depth < 0:
            raise ValueError("task signal bounds are invalid")
        for values, name in (
            (self.referenced_paths, "referenced_paths"),
            (self.referenced_symbols, "referenced_symbols"),
            (self.changed_paths, "changed_paths"),
            (self.language_signals, "language_signals"),
            (self.framework_signals, "framework_signals"),
            (self.previous_failure_classes, "previous_failure_classes"),
        ):
            if any(not value.strip() for value in values):
                raise ValueError(f"{name} must not contain empty values")
        if not self.pi_freshness.strip():
            raise ValueError("pi_freshness must not be empty")


@dataclass(frozen=True, slots=True)
class TaskIntent:
    primary: TaskIntentName
    secondary: tuple[TaskIntentName, ...]
    uncertainty: IntentUncertainty
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.primary in self.secondary or len(set(self.secondary)) != len(self.secondary):
            raise ValueError("task intent secondary values must be unique and exclude primary")
        if not self.reasons:
            raise ValueError("task intent requires at least one deterministic reason")


@dataclass(frozen=True, slots=True)
class IntelligencePlan:
    plan_id: str
    project: ProjectRef
    intent: TaskIntent
    level: IntelligenceLevel
    capabilities: tuple[CapabilityName, ...]
    minimum_depth: Depth
    context_scope: ContextScope
    context_budget_tokens: int
    query_bounds: QueryBounds
    evidence_needs: tuple[str, ...]
    escalation_conditions: tuple[str, ...]
    unavailable_capabilities: tuple[CapabilityName, ...]
    fallback_rule: str
    reasons: tuple[str, ...]
    shadow_only: bool = True

    def __post_init__(self) -> None:
        if not self.plan_id.strip():
            raise ValueError("plan_id must not be empty")
        if len(set(self.capabilities)) != len(self.capabilities):
            raise ValueError("planned capabilities must be unique")
        if set(self.capabilities) & set(self.unavailable_capabilities):
            raise ValueError("available and unavailable planned capabilities overlap")
        if self.context_budget_tokens < 0:
            raise ValueError("context budget must not be negative")
        if self.context_scope is ContextScope.NONE and self.context_budget_tokens != 0:
            raise ValueError("no-context plans must use a zero context budget")
        if not self.fallback_rule.strip() or not self.reasons:
            raise ValueError("plan requires a fallback rule and deterministic reasons")


@dataclass(frozen=True, slots=True)
class PlanOutcome:
    """C1 telemetry; it records a plan while proving no behavior was applied."""

    plan: IntelligencePlan
    recorded_at: datetime
    decision_latency_us: int
    status: str = "shadow_recorded"
    actual_capabilities: tuple[CapabilityName, ...] = ()
    actual_evidence_ids: tuple[str, ...] = ()
    expansion_count: int = 0
    fallback_reason: str | None = None
    behavior_changed: bool = False
    llm_calls: int = 0

    def __post_init__(self) -> None:
        if self.decision_latency_us < 0 or self.expansion_count < 0 or self.llm_calls < 0:
            raise ValueError("plan outcome counts must not be negative")
        if self.plan.shadow_only and (
            self.actual_capabilities
            or self.actual_evidence_ids
            or self.expansion_count
            or self.fallback_reason is not None
            or self.behavior_changed
            or self.llm_calls
        ):
            raise ValueError("a shadow plan outcome cannot apply intelligence or model work")
