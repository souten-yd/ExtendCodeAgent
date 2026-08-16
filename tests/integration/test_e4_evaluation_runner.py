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
