"""Deterministic contracts separating PI efficacy from automatic PI selection."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from extendcodeagent.evaluation.adaptive import TOOL_CAPABILITIES

SELECTION_STATES = {
    "EXPECTED_AND_USED",
    "EXPECTED_BUT_NOT_USED",
    "OPTIONAL_USED",
    "IRRELEVANT_NOT_USED",
    "UNRESOLVED",
}


class EvaluationPIPlanError(ValueError):
    """The expected PI ground-truth plan is incomplete or inconsistent."""


def validate_evaluation_pi_plan(
    plan: Mapping[str, Any],
    task_suite: Mapping[str, Any],
    configurable_capabilities: Iterable[str],
) -> None:
    """Fail closed if the manual-reviewed plan drifts from sealed evaluation truth."""

    tasks = {str(item["id"]): item for item in task_suite["tasks"]}
    entries = {str(item["task_id"]): item for item in plan.get("tasks", ())}
    if set(entries) != set(tasks):
        raise EvaluationPIPlanError("EvaluationPIPlan must cover every sealed task exactly once")
    capabilities = set(configurable_capabilities)
    known_tools = {"pi_status", *TOOL_CAPABILITIES}
    for task_id, entry in entries.items():
        if entry.get("task_class") != tasks[task_id].get("task_class"):
            raise EvaluationPIPlanError(f"task class drift: {task_id}")
        expected = list(entry.get("expected_capabilities", ()))
        if len(expected) != len(set(expected)) or set(expected) - capabilities:
            raise EvaluationPIPlanError(f"invalid expected capabilities: {task_id}")
        required = list(entry.get("required_pi_tools", ()))
        optional = list(entry.get("optional_pi_tools", ()))
        if set(required) & set(optional) or set(required + optional) - known_tools:
            raise EvaluationPIPlanError(f"invalid PI tool assignment: {task_id}")
        requests = list(entry.get("tool_requests", ()))
        if [item.get("tool") for item in requests] != required:
            raise EvaluationPIPlanError(
                f"tool requests must exactly follow required tools: {task_id}"
            )
        if any(not isinstance(item.get("input"), dict) for item in requests):
            raise EvaluationPIPlanError(f"tool request input must be an object: {task_id}")
        for field in ("rationale", "minimum_depth", "escalation_conditions"):
            if field not in entry:
                raise EvaluationPIPlanError(f"missing {field}: {task_id}")

    correction = plan["causal_correction"]
    representatives = correction["representative_tasks"]
    no_coverage = correction["no_task_coverage"]
    if set(representatives) & set(no_coverage):
        raise EvaluationPIPlanError("corrective and NO_TASK_COVERAGE capabilities overlap")
    if set(representatives) | set(no_coverage) != capabilities:
        raise EvaluationPIPlanError("corrective coverage must classify every capability")
    for capability, task_id in representatives.items():
        if capability not in entries[task_id]["expected_capabilities"]:
            raise EvaluationPIPlanError(
                f"representative task does not expect {capability}: {task_id}"
            )


def observed_capabilities(
    observed_tools: Iterable[str], observed_capability_values: Iterable[str] = ()
) -> set[str]:
    capabilities = set(observed_capability_values)
    for tool in observed_tools:
        capabilities.update(TOOL_CAPABILITIES.get(tool, ()))
    return capabilities


def selection_assessment(
    entry: Mapping[str, Any],
    observed_tools: Iterable[str],
    observed_capability_values: Iterable[str] = (),
) -> dict[str, Any]:
    """Score auto-use independently from task outcome or capability efficacy."""

    expected = set(entry["expected_capabilities"])
    optional = {
        capability
        for tool in entry["optional_pi_tools"]
        for capability in TOOL_CAPABILITIES.get(tool, ())
    } - expected
    observed = observed_capabilities(observed_tools, observed_capability_values)
    universe = {item for values in TOOL_CAPABILITIES.values() for item in values}
    states: dict[str, str] = {}
    for capability in sorted(universe):
        if capability in expected:
            states[capability] = (
                "EXPECTED_AND_USED" if capability in observed else "EXPECTED_BUT_NOT_USED"
            )
        elif capability in optional and capability in observed:
            states[capability] = "OPTIONAL_USED"
        elif capability in observed:
            states[capability] = "UNRESOLVED"
        else:
            states[capability] = "IRRELEVANT_NOT_USED"
    selected_expected = expected & observed
    unexpected = observed - expected - optional
    precision = (
        len(selected_expected) / len(observed) if observed else (1.0 if not expected else 0.0)
    )
    recall = len(selected_expected) / len(expected) if expected else 1.0
    return {
        "expected_capabilities": sorted(expected),
        "observed_capabilities": sorted(observed),
        "capability_selection_precision": round(precision, 6),
        "capability_selection_recall": round(recall, 6),
        "under_selection_rate": round((len(expected - observed) / len(expected)), 6)
        if expected
        else 0.0,
        "over_selection_rate": round((len(unexpected) / len(observed)), 6) if observed else 0.0,
        "states": states,
        "classification": "PI_SELECTION_GAP" if expected - observed else "SELECTION_COMPLETE",
    }


def tool_request_fingerprint(requests: Sequence[Mapping[str, Any]]) -> str:
    payload = json.dumps(
        list(requests), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def forced_use_compliance(entry: Mapping[str, Any], result: Mapping[str, Any]) -> dict[str, Any]:
    """Require the exact planned tool order and inputs before causal scoring."""

    expected = list(entry["tool_requests"])
    observed = [
        {"tool": item.get("tool"), "input": item.get("input", {})}
        for item in result.get("pi_tool_requests", ())
    ]
    reasons: list[str] = []
    if observed != expected:
        reasons.append("required_tool_order_or_input_mismatch")
    missing = sorted(set(entry["required_pi_tools"]) - set(result.get("pi_tools", ())))
    if missing:
        reasons.append("required_pi_tools_not_observed")
    errors = {str(item) for item in result.get("errors", ())}
    tool_api_gap = bool(
        errors & {"ConfigError", "ApplicationError", "ToolError", "APIError"}
        or result.get("pi_tool_failures")
    )
    if tool_api_gap:
        reasons.append("forced_route_or_tool_input_failure")
    return {
        "classification": (
            "PI_TOOL_API_GAP"
            if tool_api_gap
            else "FORCED_USE_COMPLIANCE_FAILURE"
            if reasons
            else "FORCED_USE_COMPLIANT"
        ),
        "compliant": not reasons,
        "reasons": reasons,
        "missing_required_tools": missing,
        "planned_request_fingerprint": tool_request_fingerprint(expected),
        "observed_request_fingerprint": tool_request_fingerprint(observed),
    }


def paired_causal_assessment(
    forced_result: Mapping[str, Any], ablated_result: Mapping[str, Any]
) -> dict[str, Any]:
    """Classify one forced ON/OFF pair only after both routes meet the same plan."""

    on = forced_result["forced_use_compliance"]
    off = ablated_result["forced_use_compliance"]
    if not on["compliant"] or not off["compliant"]:
        classification = (
            "PI_TOOL_API_GAP"
            if "PI_TOOL_API_GAP" in {on["classification"], off["classification"]}
            else "FORCED_USE_COMPLIANCE_FAILURE"
        )
    elif on["observed_request_fingerprint"] != off["observed_request_fingerprint"]:
        classification = "FORCED_PLAN_INPUT_MISMATCH"
    elif forced_result.get("outcome") == "PASS" and ablated_result.get("outcome") != "PASS":
        classification = "POSITIVE_CAUSAL_SIGNAL"
    elif forced_result.get("outcome") == "FAIL" and ablated_result.get("outcome") == "FAIL":
        classification = "PI_CAPABILITY_GAP"
    else:
        classification = "NO_OBSERVED_CAUSAL_EFFECT_BOUNDARY"
    return {
        "classification": classification,
        "causal_score_permitted": classification
        not in {
            "FORCED_USE_COMPLIANCE_FAILURE",
            "FORCED_PLAN_INPUT_MISMATCH",
            "PI_TOOL_API_GAP",
        },
        "forced_outcome": forced_result.get("outcome"),
        "ablated_outcome": ablated_result.get("outcome"),
    }


def intrinsic_pi_assessment(
    forced_result: Mapping[str, Any], off_result: Mapping[str, Any]
) -> dict[str, Any]:
    """Compare forced PI with a disabled route under the identical request plan."""

    return paired_causal_assessment(forced_result, off_result)


def auto_forced_diagnosis(
    auto_result: Mapping[str, Any] | None, forced_result: Mapping[str, Any]
) -> str:
    if auto_result is None:
        return "UNRESOLVED"
    auto_pass = auto_result.get("outcome") == "PASS"
    forced_pass = forced_result.get("outcome") == "PASS"
    if not auto_pass and forced_pass:
        return "PI_SELECTION_GAP"
    if auto_pass and forced_pass:
        auto_cost = int(auto_result.get("input_tokens") or 0) + int(
            auto_result.get("output_tokens") or 0
        )
        forced_cost = int(forced_result.get("input_tokens") or 0) + int(
            forced_result.get("output_tokens") or 0
        )
        return "AUTO_SKIP_WAS_CORRECT" if forced_cost > auto_cost else "BOTH_PASS"
    if not forced_pass and forced_result.get("forced_use_compliance", {}).get("classification") == (
        "PI_TOOL_API_GAP"
    ):
        return "PI_TOOL_API_GAP"
    if not auto_pass and not forced_pass:
        return "PI_CAPABILITY_GAP"
    return "UNRESOLVED"
