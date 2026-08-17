from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from extendcodeagent.evaluation.causal import (  # noqa: E402
    EvaluationPIPlanError,
    forced_use_compliance,
    intrinsic_pi_assessment,
    paired_causal_assessment,
    selection_assessment,
    validate_evaluation_pi_plan,
)
from tools.local import evaluation_runner as legacy  # noqa: E402


def _plans() -> tuple[dict[str, Any], dict[str, Any]]:
    evaluation_plan = json.loads(legacy.EVALUATION_PI_PLAN.read_text())
    task_suite = json.loads(legacy.TASK_SUITE.read_text())
    return evaluation_plan, task_suite


def _entry(task_id: str = "eca-impact-001") -> dict[str, Any]:
    plan, _ = _plans()
    return next(item for item in plan["tasks"] if item["task_id"] == task_id)


def _compliant_result(entry: dict[str, Any], outcome: str) -> dict[str, Any]:
    result = {
        "outcome": outcome,
        "pi_tools": list(entry["required_pi_tools"]),
        "pi_tool_requests": copy.deepcopy(entry["tool_requests"]),
        "pi_tool_failures": [],
        "errors": [],
    }
    result["forced_use_compliance"] = forced_use_compliance(entry, result)
    return result


def test_evaluation_pi_plan_covers_sealed_suite_without_observed_use_input() -> None:
    plan, task_suite = _plans()

    validate_evaluation_pi_plan(plan, task_suite, legacy.CONFIGURABLE_CAPABILITIES)

    assert set(plan["construction"]["excluded_inputs"]) == {
        "Qwen tool choice",
        "observed active pi_* trace",
        "screening outcome",
    }
    assert plan["causal_correction"]["maximum_forced_calls"] == 57


def test_evaluation_pi_plan_fails_closed_on_task_drift() -> None:
    plan, task_suite = _plans()
    plan["tasks"] = plan["tasks"][:-1]

    with pytest.raises(EvaluationPIPlanError, match="cover every sealed task"):
        validate_evaluation_pi_plan(plan, task_suite, legacy.CONFIGURABLE_CAPABILITIES)


def test_selection_reports_expected_but_not_used_as_selection_gap() -> None:
    result = selection_assessment(_entry(), ["pi_status", "pi_symbol"])

    assert result["states"]["impact"] == "EXPECTED_BUT_NOT_USED"
    assert result["classification"] == "PI_SELECTION_GAP"
    assert result["capability_selection_recall"] < 1.0


def test_forced_use_requires_exact_order_and_inputs() -> None:
    entry = _entry()
    result = _compliant_result(entry, "PASS")

    assert result["forced_use_compliance"]["classification"] == "FORCED_USE_COMPLIANT"

    changed = copy.deepcopy(result)
    changed["pi_tool_requests"][1]["input"] = {"query": "different"}
    compliance = forced_use_compliance(entry, changed)
    assert compliance["classification"] == "FORCED_USE_COMPLIANCE_FAILURE"
    assert compliance["compliant"] is False

    extra = copy.deepcopy(result)
    extra["pi_tool_requests"].append({"tool": "pi_tests", "input": {"objective": "extra"}})
    assert forced_use_compliance(entry, extra)["compliant"] is False


def test_forced_tool_error_is_api_gap_and_cannot_score_causally() -> None:
    entry = _entry()
    on = _compliant_result(entry, "PASS")
    off = _compliant_result(entry, "FAIL")
    off["pi_tool_failures"] = [{"tool": "pi_impact", "reason": "tool_state_error"}]
    off["forced_use_compliance"] = forced_use_compliance(entry, off)

    causal = paired_causal_assessment(on, off)

    assert causal["classification"] == "PI_TOOL_API_GAP"
    assert causal["causal_score_permitted"] is False


def test_on_off_and_ablation_pairs_use_the_same_request_fingerprint() -> None:
    entry = _entry()
    on = _compliant_result(entry, "PASS")
    off = _compliant_result(entry, "FAIL")
    ablated = _compliant_result(entry, "FAIL")

    assert intrinsic_pi_assessment(on, off)["classification"] == "POSITIVE_CAUSAL_SIGNAL"
    assert paired_causal_assessment(on, ablated)["classification"] == ("POSITIVE_CAUSAL_SIGNAL")
    assert {
        item["forced_use_compliance"]["observed_request_fingerprint"] for item in (on, off, ablated)
    } == {on["forced_use_compliance"]["planned_request_fingerprint"]}


def test_eval_only_use_policy_does_not_change_core_active_semantics() -> None:
    assert legacy._arm_mode("active") == ("active", None)
    assert legacy._arm_mode("auto_pi") == ("active", None)
    assert legacy._arm_mode("forced_pi") == ("active", None)
    assert legacy._arm_mode("forced_ablation:impact") == ("active", "impact")


def test_forced_on_off_and_ablation_have_identical_task_prompt() -> None:
    task = next(item for item in _plans()[1]["tasks"] if item["id"] == "eca-impact-001")
    prompts = {
        legacy._task_instruction({"pi_use_policy": policy}, task, mode)
        for policy, mode in (
            ("forced_pi", "active"),
            ("forced_off", "off"),
            ("forced_ablation", "active"),
        )
    }

    assert len(prompts) == 1
