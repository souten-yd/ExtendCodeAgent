from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from pytest import MonkeyPatch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.local import adaptive_screening_runner as adaptive  # noqa: E402
from tools.local import b0b_confirmation_runner as runner  # noqa: E402
from tools.local import evaluation_runner as legacy  # noqa: E402


def _result(cell: dict[str, Any], outcome: str) -> dict[str, Any]:
    return {**cell, "outcome": outcome, "pi_capabilities_used": ["graph"]}


def test_b0b_plan_keeps_held_out_full_repetition_contract(tmp_path: Path) -> None:
    output = tmp_path / "plan.json"

    runner.create_plan(output)

    plan = json.loads(output.read_text())
    legacy._verify_seal(plan, "test B0b plan")
    assert plan["hard_maximum_calls"] == 108
    assert plan["expected_calls_before_active_trace"] == 108
    assert plan["mandatory_base_calls"] == 36
    assert plan["conditional_ablation_maximum_calls"] == 72
    assert plan["repetitions"] == 3
    assert plan["step_limit"] is None
    assert plan["workspace_strategy"] == "git_worktree"
    assert {item["task_id"] for item in plan["cells"]} == {
        "kasane-unsafe-001",
        "kasane-cross-boundary-001",
        "kasane-tests-001",
        "kasane-requirement-001",
    }
    assert {item["model_tier"] for item in plan["cells"]} == {"local-practical"}
    assert len([item for item in plan["cells"] if item["arm"] in runner.BASE_ARMS]) == 36


def test_b0b_decision_uses_all_three_repetitions_and_inherited_threshold() -> None:
    active = [
        {
            "cell_id": f"active--local-practical--task--r{repetition}",
            "arm": "active",
            "task_id": "task",
            "task_class": "test-selection",
            "repetition": repetition,
        }
        for repetition in range(1, 4)
    ]
    ablated = [
        {
            "cell_id": f"ablation:graph--local-practical--task--r{repetition}",
            "arm": "ablation:graph",
            "task_id": "task",
            "task_class": "test-selection",
            "repetition": repetition,
        }
        for repetition in range(1, 4)
    ]
    plan = {"candidates": ["graph"], "cells": [*active, *ablated]}
    results: dict[str, dict[str, Any]] = {
        **{str(item["cell_id"]): _result(item, "PASS") for item in active},
        **{
            str(item["cell_id"]): _result(item, "FAIL" if index == 0 else "PASS")
            for index, item in enumerate(ablated)
        },
    }

    decision = runner._decisions(plan, results, {})["graph"]

    assert decision["paired_cells"] == 3
    assert decision["effect_threshold_pass_delta"] == 1
    assert decision["pass_delta"] == 1
    assert decision["decision"] == "CONFIRMED_POSITIVE_LOCAL_PRACTICAL"


def test_b0b_plan_excludes_non_candidates_and_non_local_models() -> None:
    schedule = legacy.plan("b0b-confirmation")

    assert schedule["counts"] == {"cells": 108, "available": 108, "unavailable": 0}
    assert {item["model_tier"] for item in schedule["cells"]} == {"local-practical"}
    assert not any(item["arm"] == "ablation:blueprint" for item in schedule["cells"])
    assert all(item["split"] == "held-out" for item in schedule["cells"])


def test_held_out_test_oracle_records_required_set_precision_and_recall(
    tmp_path: Path,
) -> None:
    answer = tmp_path / ".eca-eval/answer.json"
    answer.parent.mkdir()
    answer.write_text(
        json.dumps({"status": "completed", "selected_tests": ["tests/a.py", "tests/extra.py"]})
    )
    task = {
        "oracle": {
            "checks": [
                {
                    "kind": "answer",
                    "path": ".eca-eval/answer.json",
                    "equals": {
                        "status": "completed",
                        "selected_tests": ["tests/a.py", "tests/b.py"],
                    },
                }
            ]
        }
    }

    attribution = legacy._outcome_attribution(
        task, tmp_path, arm="active", oracle_exit=1, observed_pi_facts=[]
    )

    assert attribution["required_verification_set_quality"] == {
        "status": "MEASURED_BY_SEALED_TASK_ORACLE",
        "true_positive": 1,
        "false_positive": 1,
        "false_negative": 1,
        "precision": 0.5,
        "recall": 0.5,
    }


def test_b0b_run_executes_only_full_repetition_active_use_pairs(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    plan_path = tmp_path / "plan.json"
    output = tmp_path / "result.json"
    runner.create_plan(plan_path)
    executed: list[str] = []

    monkeypatch.setattr(legacy, "_require_clean_worktree", lambda: None)
    monkeypatch.setattr(legacy, "_append_trace", lambda *args: None)

    def execute(cells: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
        executed.extend(item["cell_id"] for item in cells)
        return [
            {
                **item,
                "outcome": "PASS",
                "provider_failure": None,
                "pi_capabilities_used": ["graph"] if item["arm"] == "active" else [],
                "input_tokens": 1,
                "output_tokens": 1,
                "reasoning_tokens": 0,
                "model_wall_ms": 1,
            }
            for item in cells
        ]

    monkeypatch.setattr(adaptive, "_execute_batch", execute)

    runner.run(plan_path, tmp_path / "raw", output, resume=False)

    result = json.loads(output.read_text())
    assert result["classification"] == "B0B_LOCAL_CONFIRMATION_COMPLETE"
    assert result["unique_cells_accounted"] == 108
    assert result["llm_calls_executed"] == 48
    assert result["llm_calls_avoided"] == 60
    assert len([item for item in executed if item.startswith("ablation:graph--")]) == 12
    assert not any(item.startswith("ablation:twin--") for item in executed)
    assert result["skip_counts"] == {"NOT_TESTED_NO_ACTIVE_USE": 60}
