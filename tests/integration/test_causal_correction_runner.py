from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import pytest
from pytest import MonkeyPatch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from extendcodeagent.evaluation import EvaluationTraceLog  # noqa: E402
from extendcodeagent.evaluation.causal import forced_use_compliance  # noqa: E402
from tools.local import adaptive_screening_runner as adaptive  # noqa: E402
from tools.local import causal_correction_runner as runner  # noqa: E402
from tools.local import evaluation_runner as legacy  # noqa: E402

OBSERVATIONAL = Path(".evaluation/unified-v1/b0a-adaptive-screening-e793103.json")
PILOT = Path(".evaluation/unified-v1/b0a-pilot-7e58751.json")


def _entry(task_id: str) -> dict[str, Any]:
    plan = json.loads(legacy.EVALUATION_PI_PLAN.read_text())
    return next(item for item in plan["tasks"] if item["task_id"] == task_id)


def test_correction_plan_is_bounded_and_reclassifies_pilot_reuse(tmp_path: Path) -> None:
    output = tmp_path / "plan.json"

    runner.create_plan(OBSERVATIONAL, PILOT, output)

    plan = json.loads(output.read_text())
    legacy._verify_seal(plan, "test corrective plan")
    assert plan["initial_new_calls"] == 24
    assert plan["maximum_new_calls"] == 58
    assert len(plan["auto_cells"]) == 1
    assert len(plan["forced_cells"]) == 57
    assert plan["new_auto_tasks"] == ["cd-requirement-001"]
    assert plan["pilot_forced_audit"]["classification"] == (
        "REPLAY_REQUIRED_INPUT_PROVENANCE_MISSING"
    )
    assert set(plan["no_task_coverage"]) == {"research", "test_obsolescence"}


def test_workspace_templates_resolve_relative_root_before_git_worktree_creation(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    templates = adaptive.WorkspaceTemplates(Path("relative/workspace-state"), {})

    assert templates.root.is_absolute()
    assert templates.workspace_root == (tmp_path / "relative/workspace-state/workspaces")


def test_workspace_templates_make_treatment_ids_path_safe(tmp_path: Path) -> None:
    templates = adaptive.WorkspaceTemplates(tmp_path, {})
    templates.strategy = "git_worktree"
    captured: list[Path] = []
    templates.ensure_template = lambda task_id: tmp_path / task_id  # type: ignore[method-assign]
    templates._create = lambda template, target, strategy: captured.append(target)  # type: ignore[method-assign]

    workspace = templates.prepare_retry_safe("task", "causal--forced_ablation:graph--r1")

    assert workspace == captured[0]
    assert ":" not in workspace.name
    assert workspace.name.endswith("--363e2c68")


def test_corrective_run_stops_positive_capabilities_after_one_pair(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    plan_path = tmp_path / "plan.json"
    output = tmp_path / "result.json"
    runner.create_plan(OBSERVATIONAL, PILOT, plan_path)
    executed: list[str] = []

    monkeypatch.setattr(legacy, "_require_clean_worktree", lambda: None)
    monkeypatch.setattr(legacy, "_append_trace", lambda *args: None)

    def execute(cells: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
        results = []
        for cell in cells:
            executed.append(cell["cell_id"])
            result = {
                **cell,
                "outcome": "PASS" if cell["pi_use_policy"] in {"forced_pi", "auto_pi"} else "FAIL",
                "provider_failure": None,
                "input_tokens": 10,
                "output_tokens": 5,
                "reasoning_tokens": 0,
                "model_wall_ms": 1,
                "wall_ms": 1,
                "pi_capabilities_used": [],
                "pi_tool_failures": [],
                "errors": [],
            }
            if cell["pi_use_policy"] == "auto_pi":
                result["pi_tools"] = []
                result["pi_tool_requests"] = []
            else:
                entry = _entry(cell["task_id"])
                result["pi_tools"] = list(entry["required_pi_tools"])
                result["pi_tool_requests"] = copy.deepcopy(entry["tool_requests"])
                result["forced_use_compliance"] = forced_use_compliance(entry, result)
            results.append(result)
        return results

    monkeypatch.setattr(adaptive, "_execute_batch", execute)

    runner.run(plan_path, tmp_path / "raw", output, resume=False)

    result = json.loads(output.read_text())
    assert result["classification"] == "CAUSAL_CAPABILITY_CORRECTION_COMPLETE"
    assert result["unique_new_cells_accounted"] == 58
    assert result["efficiency"]["llm_calls_executed"] == 24
    assert result["efficiency"]["llm_calls_avoided"] == 34
    assert len(executed) == 24
    assert set(result["new_causal_candidates"]) == set(result["capability_causal_results"])
    assert set(result["existing_observational_candidates_preserved"]) <= set(
        result["b0b_candidate_union"]
    )
    assert all(
        item["classification"] == "POSITIVE_CAUSAL_SIGNAL"
        for item in result["intrinsic_pi_results"].values()
    )


def test_report_separates_compatible_reuse_from_new_model_calls(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    runner.create_plan(OBSERVATIONAL, PILOT, plan_path)
    plan = json.loads(plan_path.read_text())
    cell = plan["forced_cells"][0]
    migrated = {
        **cell,
        "outcome": "PASS",
        "input_tokens": 10,
        "output_tokens": 5,
        "reasoning_tokens": 0,
        "model_wall_ms": 12,
        "result_origin": "COMPATIBILITY_MIGRATION",
    }
    trace = EvaluationTraceLog(tmp_path / "traces.jsonl")

    report = runner._report(plan, {cell["cell_id"]: migrated}, {}, [], trace, 0)

    assert report["efficiency"]["llm_calls_executed"] == 0
    assert report["efficiency"]["llm_calls_reused"] == 1
    assert report["efficiency"]["reused_model_wall_time_ms"] == 12


def test_compatible_reclassification_keeps_existing_immutable_trace(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    runner.create_plan(OBSERVATIONAL, PILOT, plan_path)
    plan = json.loads(plan_path.read_text())
    cell = plan["forced_cells"][0]
    tasks = {item["id"]: item for item in json.loads(legacy.TASK_SUITE.read_text())["tasks"]}
    result = {
        **cell,
        "outcome": "FAIL",
        "model_id": "eca-local-practical/llama",
        "wall_ms": 100,
        "pi_capabilities_used": [],
    }
    trace = EvaluationTraceLog(tmp_path / "traces.jsonl")
    legacy._append_trace(trace, result, tasks[cell["task_id"]])
    migrated = {**result, "wall_ms": 200, "result_origin": "COMPATIBILITY_MIGRATION"}

    runner._append_missing_traces(trace, {cell["cell_id"]: migrated}, tasks)

    replayed = trace.replay()
    assert len(replayed) == 1
    assert replayed[0].timings_ms["agent_wall"] == 100

    migrated["outcome"] = "PASS"
    with pytest.raises(runner.CausalCorrectionError, match="conflicts with source trace"):
        runner._append_missing_traces(trace, {cell["cell_id"]: migrated}, tasks)
