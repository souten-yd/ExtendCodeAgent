from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

from pytest import MonkeyPatch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

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
