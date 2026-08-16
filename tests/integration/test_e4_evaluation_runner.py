from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from pytest import MonkeyPatch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.local.evaluation_runner import (  # noqa: E402
    CONFIGURABLE_CAPABILITIES,
    _activation_assessment,
    _activation_gate,
    _environment,
    _isolated_agent_environment,
    _pilot_active_assessment,
    _pilot_gate,
    _pilot_off_assessment,
)

RUNNER = ROOT / "tools/local/evaluation-runner"
MATRIX = ROOT / "docs/evaluation/evaluation-matrix-v1.json"
LABELS = ROOT / "docs/evaluation/labels-v1/graph-quality-labels.json"
METRICS = ROOT / "docs/evaluation/pi-verification-integrated-metrics-v1.json"
ACTIVATION_PLAN = ROOT / "docs/evaluation/b0a-activation-plan-v1.json"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(RUNNER), *args], cwd=ROOT, text=True, capture_output=True, check=False
    )


def _digest(value: dict[str, object]) -> str:
    payload = {key: item for key, item in value.items() if key != "seal"}
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(canonical).hexdigest()


def test_matrix_and_promoted_layer_a_labels_are_sealed() -> None:
    result = _run("validate")
    assert result.returncode == 0, result.stderr
    for path in (MATRIX, LABELS):
        value = json.loads(path.read_text(encoding="utf-8"))
        assert value["seal"] == {"algorithm": "sha256", "canonical_payload": _digest(value)}
    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    assert labels["review_volume"] == {
        "cases": 12,
        "new_human_reviews": 0,
        "promotion_source": "Existing manually reviewed PR-C and PR-H ground-truth reports",
    }


def test_full_plan_is_fixed_and_keeps_unavailable_cells_visible() -> None:
    result = _run("plan", "--scope", "full")
    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert plan["counts"] == {"cells": 5083, "available": 3588, "unavailable": 1495}
    model_ids = {cell["model_id"] for cell in plan["cells"]}
    assert "github-copilot/claude-sonnet-5" in model_ids
    assert "github-copilot/gpt-5.3-codex" in model_ids
    assert any(cell["model_tier"] == "local-low" for cell in plan["cells"])


def test_b0a_schedules_enforce_bootstrap_exclusions_and_screening_contract() -> None:
    activation = _run("plan", "--scope", "b0a-activation")
    assert activation.returncode == 0, activation.stderr
    activation_plan = json.loads(activation.stdout)
    assert activation_plan["counts"] == {"cells": 4, "available": 4, "unavailable": 0}
    assert {item["arm"] for item in activation_plan["cells"]} == {"active"}
    assert {item["task_id"] for item in activation_plan["cells"]} == {"eca-symbol-001"}
    assert {item["model_tier"] for item in activation_plan["cells"]} == {
        "local-practical",
        "host-default",
        "frontier-sonnet",
        "frontier-codex",
    }
    assert all(item["pi_activation_gate"] for item in activation_plan["cells"])

    pilot = _run("plan", "--scope", "b0a-pilot")
    assert pilot.returncode == 0, pilot.stderr
    pilot_plan = json.loads(pilot.stdout)
    assert pilot_plan["counts"] == {"cells": 27, "available": 27, "unavailable": 0}
    assert {item["arm"] for item in pilot_plan["cells"]} == {"native", "off", "active"}
    assert {item["model_tier"] for item in pilot_plan["cells"]} == {"local-practical"}
    assert {item["task_id"] for item in pilot_plan["cells"]} == {
        "eca-symbol-001",
        "eca-impact-001",
        "eca-tests-001",
    }
    assert all(item["pi_effect_pilot"] for item in pilot_plan["cells"])
    assert [
        (item["repetition"], item["task_id"], item["arm"]) for item in pilot_plan["cells"][:9]
    ] == [
        (1, task_id, arm)
        for task_id in ("eca-symbol-001", "eca-impact-001", "eca-tests-001")
        for arm in ("native", "off", "active")
    ]

    baseline = _run("plan", "--scope", "b0a-baseline")
    assert baseline.returncode == 0, baseline.stderr
    baseline_plan = json.loads(baseline.stdout)
    assert baseline_plan["counts"] == {"cells": 306, "available": 216, "unavailable": 90}
    assert {item["arm"] for item in baseline_plan["cells"]} == {"native", "off"}
    assert {item["repository_id"] for item in baseline_plan["cells"]} == {
        "extendcodeagent",
        "controldeck",
    }
    assert baseline_plan["b0a"]["excluded_repositories"] == ["kasanecore", "peds"]

    screening = _run("plan", "--scope", "b0a-screening")
    assert screening.returncode == 0, screening.stderr
    screening_plan = json.loads(screening.stdout)
    assert screening_plan["counts"] == {"cells": 714, "available": 714, "unavailable": 0}
    assert {item["model_tier"] for item in screening_plan["cells"]} == {"local-practical"}
    assert {item["task_id"] for item in screening_plan["cells"]} == {
        "eca-symbol-001",
        "eca-impact-001",
        "eca-tests-001",
        "eca-refactor-001",
        "eca-negative-001",
        "cd-bug-001",
        "cd-cross-boundary-001",
    }
    assert "active" in {item["arm"] for item in screening_plan["cells"]}
    assert "ablation:semantic" in {item["arm"] for item in screening_plan["cells"]}
    depth_arms = {
        item["arm"] for item in screening_plan["cells"] if item["arm"].startswith("depth:")
    }
    assert len(depth_arms) == 20
    assert depth_arms == {
        f"depth:{capability}:{depth}"
        for capability in {"semantic", "impact", "test_selection", "context"}
        for depth in {"D0", "D1", "D2", "D3", "D4"}
    }


def test_activation_contract_blocks_comprehensive_run_until_every_route_is_reachable(
    tmp_path: Path,
) -> None:
    activation = json.loads(ACTIVATION_PLAN.read_text(encoding="utf-8"))
    gaps = [item for item in activation["capability_routes"] if item["status"] != "REACHABLE"]
    assert gaps == [
        {
            "tool": None,
            "capabilities": ["blueprint", "convergence", "traceability", "strategy"],
            "status": "MISSING_OPENCODE_RUNTIME_ROUTE",
        }
    ]

    output = tmp_path / "baseline.json"
    result = _run(
        "run",
        "--scope",
        "b0a-baseline",
        "--model-tier",
        "local-low",
        "--task",
        "eca-symbol-001",
        "--max-cells",
        "1",
        "--output",
        str(output),
        "--raw-root",
        str(tmp_path / "raw"),
    )
    assert result.returncode == 1
    assert "--activation-report is required" in result.stderr
    assert not output.exists()


def test_activation_gate_requires_observed_runtime_state_and_provenance() -> None:
    results = []
    for model in ("local-practical", "host-default", "frontier-sonnet", "frontier-codex"):
        result: dict[str, Any] = {
            "model_tier": model,
            "outcome": "FAIL",
            "process_exit": 0,
            "errors": [],
            "pi_tools": ["pi_status", "pi_symbol"],
            "observed_pi_readiness": "ready",
            "observed_capability_modes": {
                capability: "active" for capability in CONFIGURABLE_CAPABILITIES
            },
            "observed_capability_depths": {
                capability: "D2" for capability in CONFIGURABLE_CAPABILITIES
            },
            "twin_revision_ids": ["twin-1"],
            "selected_evidence_ids": ["canonical_ref:py://module#select_tests"],
            "pi_analysis_ms": 10,
        }
        result["pi_activation"] = _activation_assessment(result)
        results.append(result)

    gate = _activation_gate(results)
    assert gate["status"] == "PASS"
    assert gate["failed_models"] == []
    assert gate["pilot_permitted"] is True
    assert gate["comprehensive_evaluation_permitted"] is False

    results[0]["selected_evidence_ids"] = []
    failed = _activation_gate(results)
    assert failed["status"] == "FAIL"
    assert failed["failed_models"] == ["local-practical"]
    assert failed["assessment_mismatches"] == ["local-practical"]


def test_effect_pilot_requires_objective_gain_observed_pi_and_bounded_time() -> None:
    results = []
    tasks = {
        "eca-symbol-001": ["pi_status", "pi_symbol"],
        "eca-impact-001": ["pi_status", "pi_symbol", "pi_impact"],
        "eca-tests-001": ["pi_status", "pi_symbol", "pi_tests"],
    }
    for arm in ("native", "off", "active"):
        for task_id, required_tools in tasks.items():
            for repetition in range(1, 4):
                result: dict[str, Any] = {
                    "cell_id": f"b0a-pilot--{arm}--local-practical--{task_id}--r{repetition}",
                    "arm": arm,
                    "model_tier": "local-practical",
                    "task_id": task_id,
                    "repetition": repetition,
                    "outcome": "PASS" if arm == "active" and repetition == 1 else "FAIL",
                    "wall_ms": 100,
                    "process_exit": 0,
                    "errors": [],
                    "pi_tools": [],
                    "observed_pi_readiness": None,
                    "observed_capability_modes": {},
                    "observed_capability_depths": {},
                    "twin_revision_ids": [],
                    "selected_evidence_ids": [],
                    "pi_analysis_ms": 0,
                }
                if arm == "active":
                    result.update(
                        {
                            "pi_tools": required_tools,
                            "observed_pi_readiness": "ready",
                            "observed_capability_modes": {
                                capability: "active" for capability in CONFIGURABLE_CAPABILITIES
                            },
                            "observed_capability_depths": {
                                capability: "D2" for capability in CONFIGURABLE_CAPABILITIES
                            },
                            "twin_revision_ids": ["twin-1"],
                            "selected_evidence_ids": ["canonical_ref:py://module#symbol"],
                            "pi_analysis_ms": 10,
                        }
                    )
                    result["pi_effect_observation"] = _pilot_active_assessment(result)
                elif arm == "off":
                    result.update(
                        {
                            "pi_tools": ["pi_status"],
                            "observed_pi_readiness": "disabled",
                            "observed_capability_modes": {
                                capability: "off" for capability in CONFIGURABLE_CAPABILITIES
                            },
                            "pi_analysis_ms": 1,
                        }
                    )
                    result["pi_off_observation"] = _pilot_off_assessment(result)
                results.append(result)

    gate = _pilot_gate(results)
    assert gate["decision"] == "PROCEED_TO_COMPREHENSIVE"
    assert gate["active_pass_delta_over_best_control"] == 3
    assert gate["comprehensive_evaluation_permitted"] is True

    initial = [item for item in results if item["repetition"] == 1]
    initial_gate = _pilot_gate(initial)
    assert initial_gate["stage"] == "initial_complete"
    assert initial_gate["observed_cells"] == 9
    assert initial_gate["decision"] == "CONTINUE_TO_CONFIRMATION"
    assert initial_gate["comprehensive_evaluation_permitted"] is False

    for item in results:
        if item["arm"] == "active":
            item["wall_ms"] = 1_000
    repaired = _pilot_gate(results)
    assert repaired["decision"] == "REPAIR_AND_RETEST"
    assert "active_wall_time_abnormal" in repaired["reasons"]


def test_agent_environment_cannot_retarget_the_shared_runner_venv(
    monkeypatch: MonkeyPatch,
) -> None:
    root_venv_bin = str(ROOT / ".venv/bin")
    monkeypatch.setenv("PATH", f"{root_venv_bin}:/usr/local/bin:/usr/bin")
    monkeypatch.setenv("VIRTUAL_ENV", str(ROOT / ".venv"))
    monkeypatch.setenv("PYTHONPATH", str(ROOT / "src"))
    isolated = _isolated_agent_environment()
    assert root_venv_bin not in isolated["PATH"].split(":")
    assert isolated["PATH"] == "/usr/local/bin:/usr/bin"
    assert "VIRTUAL_ENV" not in isolated
    assert "PYTHONPATH" not in isolated
    assert isolated["PIP_REQUIRE_VIRTUALENV"] == "true"


def test_active_environment_uses_one_plugin_route_with_the_sealed_project_config(
    tmp_path: Path,
) -> None:
    env, _ = _environment("active", "local-practical", tmp_path / "workspace")
    project_config = Path(env["EXTENDCODEAGENT_PROJECT_CONFIG"])
    resolved = json.loads(project_config.read_text(encoding="utf-8"))
    assert resolved["project_intelligence"]["capabilities"] == {
        capability: "active" for capability in CONFIGURABLE_CAPABILITIES
    }
    opencode = json.loads(env["OPENCODE_CONFIG_CONTENT"])
    assert opencode["plugin"]
    assert "mcp" not in opencode

    native, _ = _environment("native", "local-practical", tmp_path / "native")
    assert "EXTENDCODEAGENT_PROJECT_CONFIG" not in native


def test_b0a_screening_table_uses_paired_threshold_without_adoption_decision(
    tmp_path: Path,
) -> None:
    schedule_result = _run("plan", "--scope", "b0a-screening")
    schedule = json.loads(schedule_result.stdout)
    active = [item for item in schedule["cells"] if item["arm"] == "active"]
    results = []
    for cell in schedule["cells"]:
        if cell["arm"] == "active":
            outcome = (
                "PASS" if cell["repetition"] == 1 and cell["task_id"].startswith("eca-") else "FAIL"
            )
        elif cell["arm"].startswith("ablation:"):
            active_id = cell["cell_id"].replace(f"{cell['arm']}--", "active--", 1)
            active_cell = next(item for item in active if item["cell_id"] == active_id)
            active_outcome = (
                "PASS"
                if active_cell["repetition"] == 1 and active_cell["task_id"].startswith("eca-")
                else "FAIL"
            )
            outcome = "FAIL" if cell["arm"] == "ablation:semantic" else active_outcome
        else:
            continue
        results.append({**cell, "outcome": outcome})
    input_path = tmp_path / "screening.json"
    output_path = tmp_path / "table.json"
    input_path.write_text(json.dumps({"source_revision": "head", "results": results}))
    screened = _run("screen", "--input", str(input_path), "--output", str(output_path))
    assert screened.returncode == 0, screened.stderr
    table = json.loads(output_path.read_text())
    entries = {item["capability"]: item for item in table["capabilities"]}
    assert table["expected_comparison_cells"] == 294
    assert table["effect_threshold_pass_delta"] == 2
    assert table["adoption_decisions_forbidden"] is True
    assert entries["semantic"]["decision"] == "proceed_to_b0b"
    assert entries["graph"]["decision"] == "no_screened_effect"


def test_plan_filters_select_a_resumable_bounded_slice() -> None:
    result = _run(
        "plan",
        "--scope",
        "base",
        "--arm",
        "advisory",
        "--model-tier",
        "frontier-codex",
        "--task",
        "eca-negative-001",
    )
    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert plan["counts"] == {"cells": 3, "available": 3, "unavailable": 0}
    assert {cell["arm"] for cell in plan["cells"]} == {"advisory"}
    assert {cell["task_id"] for cell in plan["cells"]} == {"eca-negative-001"}


def test_metric_projection_emits_every_versioned_key_as_not_tested() -> None:
    result = _run("metrics")
    assert result.returncode == 0, result.stderr
    projected = json.loads(result.stdout)
    contract = json.loads(METRICS.read_text(encoding="utf-8"))
    for group in (
        "correctness",
        "efficiency",
        "portfolio",
        "nondeterminism",
        "performance_obligations",
        "certificate",
    ):
        assert set(projected[group]) == set(contract[group])
        assert all(
            value == {"status": "NOT_TESTED", "value": None} for value in projected[group].values()
        )


def test_unavailable_cell_is_checkpointed_and_resume_does_not_duplicate(tmp_path: Path) -> None:
    output = tmp_path / "run.json"
    arguments = (
        "run",
        "--scope",
        "screening",
        "--arm",
        "native",
        "--model-tier",
        "local-low",
        "--task",
        "eca-symbol-001",
        "--max-cells",
        "1",
        "--output",
        str(output),
        "--raw-root",
        str(tmp_path / "raw"),
    )
    first = _run(*arguments)
    assert first.returncode == 0, first.stderr
    resumed = _run(*arguments, "--resume")
    assert resumed.returncode == 0, resumed.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["executed_cells"] == 1
    assert report["outcomes"] == {"UNAVAILABLE": 1}
    assert report["results"][0]["reason"] == "sealed model-tier status"
    assert report["results"][0]["trace_id"].startswith("trace-")
    assert report["trace_log"] == str((tmp_path / "raw/traces.jsonl").resolve())


def test_resume_rejects_a_different_source_revision(tmp_path: Path) -> None:
    output = tmp_path / "run.json"
    raw_root = tmp_path / "raw"
    arguments = (
        "run",
        "--scope",
        "screening",
        "--arm",
        "native",
        "--model-tier",
        "local-low",
        "--task",
        "eca-symbol-001",
        "--max-cells",
        "1",
        "--output",
        str(output),
        "--raw-root",
        str(raw_root),
    )
    assert _run(*arguments).returncode == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    report["source_revision"] = "different-head"
    output.write_text(json.dumps(report), encoding="utf-8")
    resumed = _run(*arguments, "--resume")
    assert resumed.returncode == 1
    assert "different source revision" in resumed.stderr


def test_every_arm_emits_trace_and_semantic_ablation_is_attributable(tmp_path: Path) -> None:
    output = tmp_path / "all-arms.json"
    result = _run(
        "run",
        "--scope",
        "full",
        "--model-tier",
        "local-low",
        "--task",
        "eca-symbol-001",
        "--output",
        str(output),
        "--raw-root",
        str(tmp_path / "raw"),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["executed_cells"] == 115
    assert len({item["arm"] for item in report["results"]}) == 23
    assert all(item["trace_id"].startswith("trace-") for item in report["results"])

    records = [
        json.loads(line)["record"]
        for line in (tmp_path / "raw/traces.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    active = next(item for item in records if item["cell_id"].startswith("active--"))
    ablated = next(item for item in records if item["cell_id"].startswith("ablation:semantic--"))
    assert active["capability_state_source"] == "planned_matrix"
    assert ablated["capability_state_source"] == "planned_matrix"
    assert active["task_id"] == ablated["task_id"] == "eca-symbol-001"
    assert active["oracle_id"] == ablated["oracle_id"]
    differences = {
        key
        for key in active["capability_modes"]
        if active["capability_modes"][key] != ablated["capability_modes"][key]
    }
    assert differences == {"semantic"}
    assert active["capability_modes"]["semantic"] == "active"
    assert ablated["capability_modes"]["semantic"] == "off"
