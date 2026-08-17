from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from pytest import MonkeyPatch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from extendcodeagent.evaluation import EvaluationTraceLog  # noqa: E402
from extendcodeagent.evaluation.causal import forced_use_compliance  # noqa: E402
from tools.local import adaptive_screening_runner as adaptive  # noqa: E402
from tools.local import b0b_confirmation_runner as runner  # noqa: E402
from tools.local import evaluation_runner as legacy  # noqa: E402

CAUSAL_EVIDENCE = ROOT / "docs/evidence/final/b0a-causal-correction-result-v1.json"


def test_b0b_plan_is_exact_local_only_held_out_contract(tmp_path: Path) -> None:
    output = tmp_path / "plan.json"

    runner.create_plan(CAUSAL_EVIDENCE, output)

    plan = json.loads(output.read_text())
    legacy._verify_seal(plan, "test B0b plan")
    assert plan["execution_scope"] == "local-only"
    assert plan["model"] == "Qwen3.6 27B"
    assert plan["endpoint"] == "127.0.0.1:8090"
    assert plan["context"] == 262144
    assert plan["output_limit"] == 8192
    assert plan["cell_count"] == len(plan["cells"]) == 57
    assert plan["model_parallelism"] == 1
    assert plan["cpu_pipeline_batch_size"] == 4
    assert plan["repetitions"] == 3
    assert plan["effect_threshold_pass_delta"] == 2
    assert plan["eligible_tasks"] == [
        "kasane-cross-boundary-001",
        "kasane-requirement-001",
        "kasane-tests-001",
    ]
    assert plan["excluded_held_out_tasks"] == ["kasane-unsafe-001"]
    assert set(plan["no_held_out_task_coverage"]) == {
        "blueprint",
        "impact",
        "strategy",
        "test_obsolescence",
    }
    assert all(item["model_tier"] == "local-practical" for item in plan["cells"])
    assert all(item["split"] == "held-out" for item in plan["cells"])


def test_b0b_plan_keeps_auto_selection_separate_and_pairs_exactly(tmp_path: Path) -> None:
    output = tmp_path / "plan.json"
    runner.create_plan(CAUSAL_EVIDENCE, output)
    cells = json.loads(output.read_text())["cells"]

    assert sum(item["pi_use_policy"] == "auto_pi" for item in cells) == 9
    assert sum(item["pi_use_policy"] == "forced_pi" for item in cells) == 9
    assert sum(item["pi_use_policy"] == "forced_off" for item in cells) == 9
    ablations = [item for item in cells if item["pi_use_policy"] == "forced_ablation"]
    assert len(ablations) == 30
    assert {
        capability: sum(item["ablation_capability"] == capability for item in ablations)
        for capability in {item["ablation_capability"] for item in ablations}
    } == {"graph": 9, "semantic": 9, "test_selection": 3, "twin": 9}


def _pair(
    on: str, off: str, classification: str = "NO_OBSERVED_CAUSAL_EFFECT_BOUNDARY"
) -> dict[str, Any]:
    return {
        "task_id": "task",
        "task_class": "symbol-lookup",
        "repetition": 1,
        "capability": "graph",
        "on_cell_id": "on",
        "off_cell_id": "off",
        "on_outcome": on,
        "off_outcome": off,
        "assessment": {"classification": classification},
    }


def test_b0b_effect_requires_unchanged_absolute_pass_delta() -> None:
    confirmed = runner._aggregate_pairs(
        [_pair("PASS", "FAIL"), _pair("PASS", "FAIL"), _pair("FAIL", "FAIL")]
    )
    boundary = runner._aggregate_pairs(
        [_pair("PASS", "FAIL"), _pair("PASS", "PASS"), _pair("FAIL", "FAIL")]
    )

    assert confirmed["decision"] == "CONFIRMED_CAUSAL_EFFECT_PENDING_LAYER_C_BUDGET"
    assert confirmed["pass_delta"] == 2
    assert boundary["decision"] == "NO_CONFIRMED_CAUSAL_EFFECT"
    assert boundary["pass_delta"] == 1


def test_b0b_noncompliance_is_excluded_fail_closed() -> None:
    result = runner._aggregate_pairs([_pair("PASS", "FAIL", "FORCED_USE_COMPLIANCE_FAILURE")])

    assert result["decision"] == "NOT_TESTED_FORCED_USE_COMPLIANCE_FAILURE"
    assert result["invalid_pairs"] == 1


def test_b0b_complete_report_keeps_selection_and_efficacy_separate(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    runner.create_plan(CAUSAL_EVIDENCE, plan_path)
    plan = json.loads(plan_path.read_text())
    expected = json.loads(legacy.EVALUATION_PI_PLAN.read_text())
    entries = {item["task_id"]: item for item in expected["tasks"]}
    results: dict[str, dict[str, Any]] = {}
    log_root = tmp_path / "logs"
    log_root.mkdir()
    for cell in plan["cells"]:
        entry = entries[cell["task_id"]]
        result = {
            **cell,
            "outcome": "PASS",
            "provider_failure": None,
            "input_tokens": 10,
            "output_tokens": 2,
            "reasoning_tokens": 0,
            "model_wall_ms": 5,
            "pi_analysis_ms": 3,
            "pi_timing_ms": {},
            "pi_capabilities_used": [],
            "errors": [],
            "pi_tool_failures": [],
            "outcome_attribution": {
                "required_verification_set_quality": (
                    {
                        "status": "MEASURED_BY_SEALED_TASK_ORACLE",
                        "true_positive": 4,
                        "false_positive": 0,
                        "false_negative": 0,
                        "precision": 1.0,
                        "recall": 1.0,
                    }
                    if cell["task_id"] == "kasane-tests-001"
                    else None
                )
            },
        }
        if cell["pi_use_policy"] == "auto_pi":
            result["pi_tools"] = []
            result["pi_tool_requests"] = []
        else:
            result["pi_tools"] = list(entry["required_pi_tools"])
            result["pi_tool_requests"] = list(entry["tool_requests"])
            result["forced_use_compliance"] = forced_use_compliance(entry, result)
        results[cell["cell_id"]] = result
        log_root.joinpath(f"{cell['cell_id']}.jsonl").write_text(
            json.dumps(
                {
                    "type": "step_finish",
                    "part": {
                        "type": "step-finish",
                        "tokens": {
                            "input": 7,
                            "output": 2,
                            "cache": {"read": 11, "write": 0},
                        },
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )

    report = runner._report(
        plan,
        results,
        [],
        EvaluationTraceLog(tmp_path / "traces.jsonl"),
        time.monotonic(),
    )

    assert report["classification"] == "B0B_HELD_OUT_CONFIRMATION_COMPLETE"
    assert report["cells_accounted"] == 57
    assert report["forced_cells"] == report["forced_use_compliant"] == 48
    assert report["selection_metrics"]["measured_cells"] == 9
    assert report["promotion_or_demotion_decision"] is False
    assert report["promotion_gate"] == "PENDING_LAYER_C_BUDGET"
    assert set(report["no_held_out_task_coverage"]) == {
        "blueprint",
        "impact",
        "strategy",
        "test_obsolescence",
    }
    assert report["efficiency"]["context_request_count"] == 57
    assert report["efficiency"]["average_context_tokens"] == 18
    assert report["efficiency"]["max_context_tokens"] == 18
    assert report["efficiency"]["context_metric_basis"] == (
        "per-model-request input + cache-read + cache-write prompt tokens from step-finish events"
    )
    assert report["efficiency"]["deterministic_pi_wall_time_ms"] == 171
    assert report["efficiency"]["deterministic_pi_wall_time_basis"] == (
        "sum of observed pi_* tool intervals"
    )
    assert report["required_verification_set_quality"] == {
        "overall": {
            "status": "MEASURED_BY_SEALED_TASK_ORACLE",
            "measured_cells": 21,
            "true_positive": 84,
            "false_positive": 0,
            "false_negative": 0,
            "micro_precision": 1.0,
            "micro_recall": 1.0,
        },
        "auto_pi": {
            "status": "MEASURED_BY_SEALED_TASK_ORACLE",
            "measured_cells": 3,
            "true_positive": 12,
            "false_positive": 0,
            "false_negative": 0,
            "micro_precision": 1.0,
            "micro_recall": 1.0,
        },
        "forced_pi": {
            "status": "MEASURED_BY_SEALED_TASK_ORACLE",
            "measured_cells": 3,
            "true_positive": 12,
            "false_positive": 0,
            "false_negative": 0,
            "micro_precision": 1.0,
            "micro_recall": 1.0,
        },
        "forced_off": {
            "status": "MEASURED_BY_SEALED_TASK_ORACLE",
            "measured_cells": 3,
            "true_positive": 12,
            "false_positive": 0,
            "false_negative": 0,
            "micro_precision": 1.0,
            "micro_recall": 1.0,
        },
        "forced_ablation": {
            "status": "MEASURED_BY_SEALED_TASK_ORACLE",
            "measured_cells": 12,
            "true_positive": 48,
            "false_positive": 0,
            "false_negative": 0,
            "micro_precision": 1.0,
            "micro_recall": 1.0,
        },
    }


def test_b0b_run_pipelines_cpu_work_in_bounded_batches(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    plan_path = tmp_path / "plan.json"
    output = tmp_path / "result.json"
    runner.create_plan(CAUSAL_EVIDENCE, plan_path)
    expected = json.loads(legacy.EVALUATION_PI_PLAN.read_text())
    entries = {item["task_id"]: item for item in expected["tasks"]}
    batch_sizes: list[int] = []
    monkeypatch.setattr(legacy, "_require_clean_worktree", lambda: None)
    monkeypatch.setattr(legacy, "_append_trace", lambda *args: None)

    def execute(cells: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
        batch_sizes.append(len(cells))
        results: list[dict[str, Any]] = []
        for cell in cells:
            entry = entries[cell["task_id"]]
            result = {
                **cell,
                "outcome": "PASS",
                "provider_failure": None,
                "input_tokens": 10,
                "output_tokens": 2,
                "reasoning_tokens": 0,
                "model_wall_ms": 5,
                "pi_timing_ms": {},
                "pi_capabilities_used": [],
                "errors": [],
                "pi_tool_failures": [],
                "pi_tools": [],
                "pi_tool_requests": [],
            }
            if cell["pi_use_policy"] != "auto_pi":
                result["pi_tools"] = list(entry["required_pi_tools"])
                result["pi_tool_requests"] = list(entry["tool_requests"])
                result["forced_use_compliance"] = forced_use_compliance(entry, result)
            results.append(result)
        return results

    monkeypatch.setattr(adaptive, "_execute_batch", execute)

    runner.run(plan_path, tmp_path / "raw", output, resume=False)

    report = json.loads(output.read_text())
    assert report["classification"] == "B0B_HELD_OUT_CONFIRMATION_COMPLETE"
    assert batch_sizes == [4] * 14 + [1]


def test_evaluation_sidecar_match_is_exact_to_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "cell-one"
    other = tmp_path / "cell-two"
    command = [
        "python3",
        "-m",
        "extendcodeagent.adapters.local_sidecar",
        "--root",
        str(workspace),
        "--database",
        str(workspace / ".eca.sqlite3"),
    ]

    assert adaptive._sidecar_matches_workspace(command, workspace)
    assert not adaptive._sidecar_matches_workspace(command, other)
    assert not adaptive._sidecar_matches_workspace(
        ["python3", "extendcodeagent.adapters.local_sidecar", "--root", str(workspace)],
        workspace,
    )


def test_evaluation_sidecar_pid_scan_ignores_other_workspaces(tmp_path: Path) -> None:
    proc = tmp_path / "proc"
    workspace = tmp_path / "cell-one"
    other = tmp_path / "cell-two"
    for pid, root in (("101", workspace), ("202", other)):
        process = proc / pid
        process.mkdir(parents=True)
        process.joinpath("cmdline").write_bytes(
            b"python3\0-m\0extendcodeagent.adapters.local_sidecar\0--root\0"
            + str(root).encode()
            + b"\0"
        )

    assert adaptive._evaluation_sidecar_pids(workspace, proc) == [101]
