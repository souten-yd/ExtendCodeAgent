from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/local/evaluation-runner"
MATRIX = ROOT / "docs/evaluation/evaluation-matrix-v1.json"
LABELS = ROOT / "docs/evaluation/labels-v1/graph-quality-labels.json"
METRICS = ROOT / "docs/evaluation/pi-verification-integrated-metrics-v1.json"


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
