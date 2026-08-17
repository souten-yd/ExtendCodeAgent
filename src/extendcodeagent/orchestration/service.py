"""Cheap deterministic classification and minimum-sufficient shadow planning."""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from extendcodeagent.core.config.schema import CapabilityName, Depth, RemoteCodePolicy, depth_rank
from extendcodeagent.core.contracts import QueryBounds
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.runtime import RuntimeSignalKind, RuntimeSignalSnapshot

from .contracts import (
    ContextScope,
    IntelligenceLevel,
    IntelligencePlan,
    IntentUncertainty,
    PlanOutcome,
    TaskIntent,
    TaskIntentName,
    TaskSignals,
)

MAX_OBJECTIVE_CHARS = 16_384
MAX_SIGNAL_PATHS = 64
_PATH_PATTERN = re.compile(r"(?<![\w.-])(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+(?:\.[A-Za-z0-9]+)?")
_SYMBOL_PATTERN = re.compile(
    r"(?<![\w])(?:_?[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+|"
    r"[A-Za-z][A-Za-z0-9]*\.[A-Za-z_][A-Za-z0-9_]*)"
)
_LANGUAGE_BY_SUFFIX = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
}
_FRAMEWORK_TOKENS = ("fastapi", "playwright", "pytest", "react", "unittest", "xterm")

_PROJECT_TRUTH = (
    CapabilityName.GRAPH,
    CapabilityName.TWIN,
    CapabilityName.SEMANTIC,
)


def project_task_signals(
    snapshot: RuntimeSignalSnapshot,
    *,
    context_token_limit: int = 8_192,
    max_items: int = 100,
    max_depth: int = 6,
    privacy_policy: RemoteCodePolicy = RemoteCodePolicy.DENY,
) -> TaskSignals | None:
    """Project the C0 collector without repository I/O or retaining another truth store."""

    task = snapshot.latest_task
    if task is None or task.kind is not RuntimeSignalKind.TASK or task.task_text is None:
        return None
    objective = task.task_text.strip()
    truncated = len(objective) > MAX_OBJECTIVE_CHARS
    objective = objective[:MAX_OBJECTIVE_CHARS]
    mutation = snapshot.latest_mutation
    model = snapshot.latest_model
    referenced_paths = tuple(_PATH_PATTERN.findall(objective))
    symbol_source = _PATH_PATTERN.sub(" ", objective)
    all_paths = (*referenced_paths, *(mutation.paths if mutation else ()))
    language_signals = tuple(
        sorted(
            {
                language
                for path in all_paths
                for suffix, language in _LANGUAGE_BY_SUFFIX.items()
                if path.casefold().endswith(suffix)
            }
        )
    )
    normalized_objective = _normalized(objective)
    return TaskSignals(
        project=snapshot.project,
        objective=objective,
        referenced_paths=_bounded_values(referenced_paths),
        referenced_symbols=_bounded_values(tuple(_SYMBOL_PATTERN.findall(symbol_source))),
        changed_paths=_bounded_values(mutation.paths if mutation else ()),
        language_signals=language_signals,
        framework_signals=tuple(
            token for token in _FRAMEWORK_TOKENS if token in normalized_objective
        ),
        pi_freshness="unknown",
        privacy_policy=privacy_policy,
        model_provider=model.model_provider if model else None,
        model_id=model.model_id if model else None,
        runtime_evidence_available=snapshot.tool_execution_count > 0,
        verification_evidence_available=snapshot.verification_count > 0,
        context_token_limit=context_token_limit,
        max_items=max_items,
        max_depth=max_depth,
        objective_truncated=truncated,
    )


def classify_task(signals: TaskSignals) -> TaskIntent:
    """Classify general task language; evaluation IDs/classes are never inputs."""

    text = _normalized(signals.objective)
    reasons: tuple[str, ...]
    primary: TaskIntentName
    if "mechanical file-write" in text or (
        "containing exactly" in text
        and "no code analysis is needed" in text
        and _contains(text, "create ", "write ")
    ):
        primary, reasons = TaskIntentName.MECHANICAL, ("explicit mechanical operation",)
    elif _contains(
        text,
        "insufficient_evidence",
        "sufficient to claim",
        "unavailable live evidence",
        "evidence is sufficient",
    ):
        primary, reasons = (
            TaskIntentName.INSUFFICIENT_EVIDENCE,
            ("completion depends on explicitly missing or unsafe evidence",),
        )
    elif _contains(text, "causal flow", "isolation flow") or (
        "user-visible" in text and _contains(text, "through the", "runtime", "http")
    ):
        primary, reasons = (
            TaskIntentName.RUNTIME_BOUNDARY,
            ("task crosses a user-visible or runtime boundary",),
        )
    elif _contains(text, "trace the requirement", "requirement-to-code"):
        primary, reasons = (
            TaskIntentName.REQUIREMENT_TRACE,
            ("task asks for requirement-to-implementation traceability",),
        )
    elif _contains(
        text, "select the smallest existing test", "select the minimum existing test"
    ) or ("selected_tests" in text and "do not edit" in text):
        primary, reasons = (
            TaskIntentName.TEST_SELECTION,
            ("task asks for a minimum verification provider set",),
        )
    elif _contains(text, "reproduce, localize", "production defect", "failing test", "bug fix"):
        primary, reasons = TaskIntentName.BUG_FIX, ("task asks to localize and repair a failure",)
    elif "refactor" in text:
        primary, reasons = (
            TaskIntentName.REFACTOR,
            ("task requests a behavior-preserving structural change",),
        )
    elif _contains(text, "assess the change impact", "impact assessment", "change impact"):
        primary, reasons = (
            TaskIntentName.IMPACT_ASSESSMENT,
            ("task directly asks for change-impact closure",),
        )
    elif _contains(text, "locate the definition", "find the definition", "explain the symbol"):
        primary, reasons = (
            TaskIntentName.LOCATE_EXPLAIN,
            ("task asks for symbol definition and reference lookup",),
        )
    elif _contains(text, "external research", "research the", "compare current sources"):
        primary, reasons = TaskIntentName.RESEARCH, ("task requires external research",)
    elif _contains(text, "architecture", "migration plan", "system redesign"):
        primary, reasons = (
            TaskIntentName.ARCHITECTURE,
            ("task requests broad architecture or migration reasoning",),
        )
    elif _contains(text, "implement", "update", "modify", "change", "fix"):
        primary, reasons = TaskIntentName.CHANGE, ("task requests a code or configuration change",)
    else:
        primary, reasons = TaskIntentName.UNKNOWN, ("no bounded deterministic intent rule matched",)

    secondary: list[TaskIntentName] = []
    if primary not in {TaskIntentName.TEST_SELECTION, TaskIntentName.MECHANICAL} and _contains(
        text, "focused test", "verification", "tests"
    ):
        secondary.append(TaskIntentName.TEST_SELECTION)
    if primary is not TaskIntentName.RUNTIME_BOUNDARY and _contains(
        text, "runtime", "live service", "browser"
    ):
        secondary.append(TaskIntentName.RUNTIME_BOUNDARY)
    uncertainty = (
        IntentUncertainty.HIGH
        if primary is TaskIntentName.UNKNOWN or signals.objective_truncated
        else IntentUncertainty.MEDIUM
        if primary is TaskIntentName.CHANGE
        else IntentUncertainty.LOW
    )
    if signals.objective_truncated:
        reasons = (*reasons, "objective was truncated at the deterministic signal bound")
    return TaskIntent(primary, tuple(secondary), uncertainty, reasons)


def build_intelligence_plan(
    signals: TaskSignals,
    intent: TaskIntent,
    policy: CapabilityPolicy,
) -> IntelligencePlan:
    """Return the minimum initial plan inside configured capability/depth bounds."""

    specification = _PLAN_BY_INTENT[intent.primary]
    desired = specification.capabilities
    selected = tuple(capability for capability in desired if policy.is_enabled(capability))
    unavailable = tuple(capability for capability in desired if not policy.is_enabled(capability))
    minimum_depth = _bounded_minimum_depth(specification.minimum_depth, selected, policy)
    context_budget = (
        0
        if specification.context_scope is ContextScope.NONE
        else min(specification.context_budget_tokens, signals.context_token_limit)
    )
    query_bounds = QueryBounds(
        max_items=min(specification.max_items, signals.max_items),
        max_depth=min(specification.max_depth, signals.max_depth),
    )
    evidence_needs = list(specification.evidence_needs)
    if CapabilityName.RUNTIME in desired and not signals.runtime_evidence_available:
        evidence_needs.append("fresh_runtime_evidence")
    if CapabilityName.TEST_SELECTION in desired and not signals.verification_evidence_available:
        evidence_needs.append("verification_coverage")
    escalation = list(specification.escalation_conditions)
    if unavailable:
        escalation.append("configured capability bound excludes required intelligence")
    if intent.uncertainty is not IntentUncertainty.LOW:
        escalation.append("task intent remains uncertain")
    reasons = (
        *intent.reasons,
        f"minimum initial intelligence level {specification.level.value}",
        "capability and context selection is shadow-only in C1",
    )
    plan_id = _plan_id(
        signals,
        intent,
        selected,
        unavailable,
        minimum_depth,
        specification.level,
        specification.context_scope,
        context_budget,
        query_bounds,
        tuple(dict.fromkeys(evidence_needs)),
        tuple(dict.fromkeys(escalation)),
    )
    return IntelligencePlan(
        plan_id=plan_id,
        project=signals.project,
        intent=intent,
        level=specification.level,
        capabilities=selected,
        minimum_depth=minimum_depth,
        context_scope=specification.context_scope,
        context_budget_tokens=context_budget,
        query_bounds=query_bounds,
        evidence_needs=tuple(dict.fromkeys(evidence_needs)),
        escalation_conditions=tuple(dict.fromkeys(escalation)),
        unavailable_capabilities=unavailable,
        fallback_rule="preserve native runtime behavior and expose unresolved evidence gaps",
        reasons=reasons,
    )


def create_shadow_plan(signals: TaskSignals, policy: CapabilityPolicy) -> PlanOutcome:
    started = time.perf_counter_ns()
    intent = classify_task(signals)
    plan = build_intelligence_plan(signals, intent, policy)
    elapsed_us = max(0, (time.perf_counter_ns() - started) // 1_000)
    return PlanOutcome(plan, datetime.now(UTC), elapsed_us)


@dataclass(frozen=True, slots=True)
class _PlanSpecification:
    level: IntelligenceLevel
    capabilities: tuple[CapabilityName, ...]
    minimum_depth: Depth
    context_scope: ContextScope
    context_budget_tokens: int
    max_items: int
    max_depth: int
    evidence_needs: tuple[str, ...]
    escalation_conditions: tuple[str, ...]


_PLAN_BY_INTENT = {
    TaskIntentName.MECHANICAL: _PlanSpecification(
        IntelligenceLevel.L0_NATIVE, (), Depth.D0, ContextScope.NONE, 0, 1, 0, (), ()
    ),
    TaskIntentName.LOCATE_EXPLAIN: _PlanSpecification(
        IntelligenceLevel.L1_UNDERSTAND,
        _PROJECT_TRUTH,
        Depth.D0,
        ContextScope.SYMBOL,
        2_000,
        30,
        1,
        ("definition_and_reference_set",),
        ("canonical reference unresolved", "reference set incomplete"),
    ),
    TaskIntentName.IMPACT_ASSESSMENT: _PlanSpecification(
        IntelligenceLevel.L2_CHANGE,
        (*_PROJECT_TRUTH, CapabilityName.IMPACT),
        Depth.D0,
        ContextScope.IMPACT,
        2_000,
        30,
        2,
        ("impact_closure",),
        ("impact closure incomplete", "uncertainty remains"),
    ),
    TaskIntentName.TEST_SELECTION: _PlanSpecification(
        IntelligenceLevel.L2_CHANGE,
        (*_PROJECT_TRUTH, CapabilityName.TEST_SELECTION),
        Depth.D0,
        ContextScope.NEIGHBORHOOD,
        2_000,
        30,
        2,
        ("verification_obligations", "test_coverage"),
        ("verification obligation uncovered", "test evidence conflicted"),
    ),
    TaskIntentName.REFACTOR: _PlanSpecification(
        IntelligenceLevel.L4_STRATEGIC,
        (
            *_PROJECT_TRUTH,
            CapabilityName.IMPACT,
            CapabilityName.BLUEPRINT,
            CapabilityName.STRATEGY,
        ),
        Depth.D1,
        ContextScope.STRATEGIC,
        8_192,
        60,
        3,
        ("change_sites", "impact_closure", "bounded_alternatives"),
        ("call site unresolved", "alternative scores tied", "verification gap remains"),
    ),
    TaskIntentName.BUG_FIX: _PlanSpecification(
        IntelligenceLevel.L2_CHANGE,
        (*_PROJECT_TRUTH, CapabilityName.IMPACT, CapabilityName.TEST_SELECTION),
        Depth.D1,
        ContextScope.IMPACT,
        4_000,
        40,
        3,
        ("failure_localization", "impact_closure", "verification_coverage"),
        ("failure not localized", "production path unresolved", "verification gap remains"),
    ),
    TaskIntentName.REQUIREMENT_TRACE: _PlanSpecification(
        IntelligenceLevel.L2_CHANGE,
        (*_PROJECT_TRUTH, CapabilityName.TRACEABILITY, CapabilityName.CONVERGENCE),
        Depth.D1,
        ContextScope.NEIGHBORHOOD,
        4_000,
        40,
        3,
        ("requirement_mapping", "actual_reference_set", "verification_coverage"),
        ("requirement mapping missing", "actual reference stale", "verification gap remains"),
    ),
    TaskIntentName.RUNTIME_BOUNDARY: _PlanSpecification(
        IntelligenceLevel.L3_RUNTIME_AWARE,
        (
            *_PROJECT_TRUTH,
            CapabilityName.CONTEXT,
            CapabilityName.RUNTIME,
            CapabilityName.TRACEABILITY,
            CapabilityName.CONVERGENCE,
        ),
        Depth.D1,
        ContextScope.RUNTIME_BOUNDARY,
        8_192,
        60,
        4,
        ("cross_boundary_path", "runtime_evidence", "visible_outcome_obligation"),
        ("boundary edge unresolved", "runtime evidence absent", "visible outcome uncovered"),
    ),
    TaskIntentName.INSUFFICIENT_EVIDENCE: _PlanSpecification(
        IntelligenceLevel.L3_RUNTIME_AWARE,
        (CapabilityName.RUNTIME, CapabilityName.TRACEABILITY, CapabilityName.CONVERGENCE),
        Depth.D1,
        ContextScope.NONE,
        0,
        20,
        2,
        ("fresh_runtime_evidence", "completion_obligation"),
        ("live evidence missing", "evidence contradiction", "obligation unresolved"),
    ),
    TaskIntentName.ARCHITECTURE: _PlanSpecification(
        IntelligenceLevel.L4_STRATEGIC,
        (
            *_PROJECT_TRUTH,
            CapabilityName.IMPACT,
            CapabilityName.BLUEPRINT,
            CapabilityName.STRATEGY,
            CapabilityName.CONVERGENCE,
        ),
        Depth.D1,
        ContextScope.STRATEGIC,
        8_192,
        60,
        4,
        ("architecture_boundaries", "impact_closure", "alternatives"),
        ("boundary unresolved", "alternative evidence tied", "scope expands"),
    ),
    TaskIntentName.RESEARCH: _PlanSpecification(
        IntelligenceLevel.L5_DEEP_ON_DEMAND,
        (*_PROJECT_TRUTH, CapabilityName.CONTEXT, CapabilityName.RESEARCH),
        Depth.D1,
        ContextScope.RESEARCH,
        8_192,
        40,
        2,
        ("bounded_research_question", "source_provenance"),
        ("external fact unresolved", "source contradiction"),
    ),
    TaskIntentName.CHANGE: _PlanSpecification(
        IntelligenceLevel.L2_CHANGE,
        (*_PROJECT_TRUTH, CapabilityName.IMPACT, CapabilityName.TEST_SELECTION),
        Depth.D1,
        ContextScope.IMPACT,
        4_000,
        40,
        3,
        ("change_scope", "impact_closure", "verification_coverage"),
        ("change scope unresolved", "impact gap remains", "verification gap remains"),
    ),
    TaskIntentName.UNKNOWN: _PlanSpecification(
        IntelligenceLevel.L0_NATIVE,
        (),
        Depth.D0,
        ContextScope.NONE,
        0,
        1,
        0,
        ("task_intent",),
        ("task intent remains uncertain",),
    ),
}


def _contains(text: str, *needles: str) -> bool:
    return any(needle in text for needle in needles)


def _normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def _bounded_values(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(sorted(values)))[:MAX_SIGNAL_PATHS]


def _bounded_minimum_depth(
    desired: Depth,
    capabilities: tuple[CapabilityName, ...],
    policy: CapabilityPolicy,
) -> Depth:
    if not capabilities:
        return Depth.D0
    shallowest_bound = min((policy.depth(item) for item in capabilities), key=depth_rank)
    return desired if depth_rank(desired) <= depth_rank(shallowest_bound) else shallowest_bound


def _plan_id(
    signals: TaskSignals,
    intent: TaskIntent,
    selected: tuple[CapabilityName, ...],
    unavailable: tuple[CapabilityName, ...],
    depth: Depth,
    level: IntelligenceLevel,
    context_scope: ContextScope,
    context_budget: int,
    query_bounds: QueryBounds,
    evidence_needs: tuple[str, ...],
    escalation_conditions: tuple[str, ...],
) -> str:
    payload = {
        "project": {
            "project_id": signals.project.project_id,
            "workspace_id": signals.project.workspace_id,
            "root_uri": signals.project.root_uri,
            "source_revision": signals.project.source_revision,
            "worktree_fingerprint": signals.project.worktree_fingerprint,
        },
        "objective": signals.objective,
        "objective_truncated": signals.objective_truncated,
        "referenced_paths": signals.referenced_paths,
        "referenced_symbols": signals.referenced_symbols,
        "changed_paths": signals.changed_paths,
        "language_signals": signals.language_signals,
        "framework_signals": signals.framework_signals,
        "prior_task_stage": signals.prior_task_stage,
        "pi_freshness": signals.pi_freshness,
        "privacy_policy": signals.privacy_policy.value,
        "model": (signals.model_provider, signals.model_id),
        "evidence": (
            signals.runtime_evidence_available,
            signals.verification_evidence_available,
            signals.previous_failure_classes,
        ),
        "intent": {
            "primary": intent.primary.value,
            "secondary": tuple(item.value for item in intent.secondary),
            "uncertainty": intent.uncertainty.value,
            "reasons": intent.reasons,
        },
        "selected": tuple(item.value for item in selected),
        "unavailable": tuple(item.value for item in unavailable),
        "depth": depth.value,
        "level": level.value,
        "context_scope": context_scope.value,
        "context_budget": context_budget,
        "query_bounds": {
            "max_items": query_bounds.max_items,
            "max_depth": query_bounds.max_depth,
        },
        "evidence_needs": evidence_needs,
        "escalation_conditions": escalation_conditions,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:24]
    return f"shadow-{digest}"
