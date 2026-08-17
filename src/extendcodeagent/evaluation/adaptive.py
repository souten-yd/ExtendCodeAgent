"""Deterministic policy for evidence-directed B0a adaptive screening.

The module deliberately contains no model or OpenCode calls.  It turns observed
active tool traces and deterministic PI outputs into a bounded set of candidate
cells while preserving the sealed task/oracle effect threshold.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

DEPTH_ORDER = ("D0", "D1", "D2", "D3", "D4")

# pi_status reports configured state; it does not exercise a capability and is
# intentionally absent.  These routes are the versioned activation-plan routes,
# with references/path assigned to the same governing query capabilities.
TOOL_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "pi_symbol": ("graph", "twin", "semantic"),
    "pi_references": ("graph", "twin", "semantic"),
    "pi_path": ("impact",),
    "pi_impact": ("impact",),
    "pi_tests": ("test_selection", "test_obsolescence"),
    "pi_context": ("context",),
    "pi_runtime_evidence": ("runtime",),
    "pi_research_plan": ("research",),
    "pi_plan": ("blueprint", "strategy"),
    "pi_verify": ("convergence", "traceability"),
}

VOLATILE_PI_FIELDS = frozenset(
    {
        "depth",
        "interface",
        "revision_id",
        "timing",
        "view",
    }
)


def capability_task_relevance(
    active_results: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, tuple[str, ...]]]:
    """Derive relevance only from non-status PI tools actually observed in active cells."""

    tools_by_task: defaultdict[str, set[str]] = defaultdict(set)
    capabilities_by_task: defaultdict[str, set[str]] = defaultdict(set)
    known_capabilities = {item for values in TOOL_CAPABILITIES.values() for item in values}
    for result in active_results:
        if result.get("arm") != "active":
            continue
        task_id = result.get("task_id")
        if not isinstance(task_id, str):
            continue
        for tool in result.get("pi_tools", ()):
            if isinstance(tool, str) and tool in TOOL_CAPABILITIES:
                tools_by_task[task_id].add(tool)
        for capability in result.get("pi_capabilities_used", ()):
            if isinstance(capability, str) and capability in known_capabilities:
                capabilities_by_task[task_id].add(capability)

    relevance: dict[str, dict[str, tuple[str, ...]]] = {}
    for task_id in sorted(set(tools_by_task) | set(capabilities_by_task)):
        tools = tools_by_task[task_id]
        capabilities = {
            capability for tool in tools for capability in TOOL_CAPABILITIES[tool]
        } | capabilities_by_task[task_id]
        relevance[task_id] = {
            "tools": tuple(sorted(tools)),
            "capabilities": tuple(sorted(capabilities)),
        }
    return relevance


def canonical_pi_output(value: Any) -> Any:
    """Remove only transport/revision/depth metadata before task-output comparison."""

    if isinstance(value, dict):
        return {
            key: canonical_pi_output(item)
            for key, item in sorted(value.items())
            if key not in VOLATILE_PI_FIELDS
        }
    if isinstance(value, list):
        return [canonical_pi_output(item) for item in value]
    return value


def pi_output_digest(value: Any) -> str:
    payload = json.dumps(
        canonical_pi_output(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def depth_equivalence_classes(outputs: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Group depths with identical task-relevant PI output, preserving depth order."""

    unknown = set(outputs) - set(DEPTH_ORDER)
    if unknown:
        raise ValueError(f"unknown depths: {sorted(unknown)}")
    groups: list[dict[str, Any]] = []
    by_digest: dict[str, dict[str, Any]] = {}
    for depth in DEPTH_ORDER:
        if depth not in outputs:
            continue
        digest = pi_output_digest(outputs[depth])
        group = by_digest.get(digest)
        if group is None:
            group = {"representative": depth, "depths": [], "output_digest": digest}
            by_digest[digest] = group
            groups.append(group)
        group["depths"].append(depth)
    return groups


def representative_depths(classes: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    """Return the minimum depth from each distinct output class in depth order."""

    representatives = {
        str(item["representative"]) for item in classes if item.get("representative") in DEPTH_ORDER
    }
    return tuple(depth for depth in DEPTH_ORDER if depth in representatives)


def sequential_ablation_decision(
    pairs: Sequence[Mapping[str, Any]],
    *,
    threshold: int,
    current_repetition: int,
    max_repetitions: int = 3,
) -> dict[str, Any]:
    """Decide whether an ablation needs another repetition.

    `pairs` contains only exercised capability/task pairs.  Missing or unexercised
    pairs are never converted into no-effect evidence.  Future potential is
    bounded by known active PASS cells, so stopping cannot manufacture a positive
    signal.
    """

    if not 1 <= current_repetition <= max_repetitions:
        raise ValueError("current_repetition must be within the sequential range")
    if not pairs:
        return {
            "decision": "NOT_TESTED_NO_ACTIVE_USE",
            "needs_next_repetition": False,
            "completed_pairs": 0,
            "active_pass": 0,
            "ablation_pass": 0,
            "pass_delta": 0,
            "critical_override": False,
            "future_active_pass_upper_bound": 0,
        }
    completed = [
        item
        for item in pairs
        if int(item.get("repetition", 0)) <= current_repetition
        and item.get("ablation_outcome") is not None
    ]
    active_pass = sum(item.get("active_outcome") == "PASS" for item in completed)
    ablation_pass = sum(item.get("ablation_outcome") == "PASS" for item in completed)
    delta = active_pass - ablation_pass
    critical = any(
        item.get("active_outcome") == "PASS"
        and item.get("ablation_outcome") != "PASS"
        and item.get("task_class") in {"negative-control", "unsafe-or-insufficient-evidence"}
        for item in completed
    )
    future_active_pass = sum(
        item.get("active_outcome") == "PASS" and int(item.get("repetition", 0)) > current_repetition
        for item in pairs
    )
    if delta >= threshold or critical:
        decision = "PROCEED_TO_B0B_EARLY"
        needs_next = False
    elif current_repetition == max_repetitions or delta + future_active_pass < threshold:
        decision = "NO_SCREENED_EFFECT"
        needs_next = False
    else:
        decision = "CONTINUE_TO_REPETITION"
        needs_next = True
    return {
        "decision": decision,
        "needs_next_repetition": needs_next,
        "completed_pairs": len(completed),
        "active_pass": active_pass,
        "ablation_pass": ablation_pass,
        "pass_delta": delta,
        "critical_override": critical,
        "future_active_pass_upper_bound": future_active_pass,
    }


def next_depth(representatives: Sequence[str], outcomes: Mapping[str, str]) -> dict[str, Any]:
    """Select the minimum untested distinct depth, stopping at the first PASS."""

    ordered = [depth for depth in DEPTH_ORDER if depth in representatives]
    passed = next((depth for depth in ordered if outcomes.get(depth) == "PASS"), None)
    if passed is not None:
        return {"decision": "MINIMUM_SUFFICIENT", "depth": passed, "next": None}
    pending = next((depth for depth in ordered if depth not in outcomes), None)
    if pending is not None:
        return {"decision": "CONTINUE", "depth": None, "next": pending}
    return {"decision": "NO_SUFFICIENT_DEPTH", "depth": None, "next": None}


def reasoning_input_fingerprint(values: Mapping[str, Any]) -> str:
    """Fingerprint advisory reasoning inputs without treating the output as Project Truth."""

    required = (
        "project_workspace",
        "revision",
        "task_intent",
        "capability_depth",
        "selected_evidence_ids",
        "relevant_environment",
    )
    missing = [key for key in required if key not in values]
    if missing:
        raise ValueError(f"reasoning fingerprint fields missing: {missing}")
    payload = json.dumps(
        {key: values[key] for key in required},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def efficiency_summary(
    *,
    requested_calls: int,
    results: Sequence[Mapping[str, Any]],
    skips: Sequence[Mapping[str, Any]],
    deterministic_pi_wall_ms: float,
    total_wall_ms: float,
    reused_evidence_count: int,
    invalidated_evidence_count: int,
    minimum_sufficient_depths: Mapping[str, str],
) -> dict[str, Any]:
    """Project the cross-stage efficiency metrics from one evaluation truth set."""

    executed = sum(item.get("llm_call_execution", "executed") == "executed" for item in results)
    avoided = sum(bool(item.get("avoids_llm_call")) for item in skips)
    if executed + avoided > requested_calls:
        raise ValueError("executed and avoided calls exceed the requested hard maximum")
    input_tokens = sum(int(item.get("input_tokens") or 0) for item in results)
    output_tokens = sum(int(item.get("output_tokens") or 0) for item in results)
    reasoning_tokens = sum(int(item.get("reasoning_tokens") or 0) for item in results)
    current_results = [
        item for item in results if item.get("llm_call_execution", "executed") == "executed"
    ]
    model_wall_ms = sum(
        float(item.get("model_wall_ms", item.get("wall_ms", 0.0))) for item in current_results
    )
    contexts = [int(item.get("input_tokens") or 0) for item in current_results]
    deterministic_resolutions = sum(
        item.get("reason")
        in {
            "NOT_TESTED_NO_ACTIVE_USE",
            "SKIPPED_DEPTH_OUTPUT_EQUIVALENT",
            "SKIPPED_MINIMUM_SUFFICIENT_DEPTH",
            "SKIPPED_EARLY_POSITIVE",
            "REUSED_COMPATIBLE_EVIDENCE",
        }
        for item in skips
    )
    return {
        "llm_calls_requested": requested_calls,
        "llm_calls_executed": executed,
        "llm_calls_avoided": avoided,
        "avoided_call_ratio": round(avoided / requested_calls, 6) if requested_calls else 0.0,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "deterministic_resolution_ratio": (
            round(deterministic_resolutions / requested_calls, 6) if requested_calls else 0.0
        ),
        "escalation_rate": round(executed / requested_calls, 6) if requested_calls else 0.0,
        "average_context_tokens": round(sum(contexts) / len(contexts), 3) if contexts else 0.0,
        "max_context_tokens": max(contexts, default=0),
        "minimum_sufficient_depth": dict(sorted(minimum_sufficient_depths.items())),
        "model_wall_time_ms": round(model_wall_ms, 3),
        "deterministic_pi_wall_time_ms": round(deterministic_pi_wall_ms, 3),
        "total_wall_time_ms": round(total_wall_ms, 3),
        "reused_evidence_count": reused_evidence_count,
        "invalidated_evidence_count": invalidated_evidence_count,
    }
