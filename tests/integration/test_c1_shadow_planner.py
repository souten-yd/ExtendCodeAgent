from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_c1_scores_tuning_and_held_out_without_model_or_behavior_effect(
    tmp_path: Path,
) -> None:
    output = tmp_path / "c1-result.json"
    subprocess.run(
        [
            sys.executable,
            "tools/local/c1_shadow_planner.py",
            "--output",
            str(output),
            "--latency-repetitions",
            "1",
        ],
        check=True,
    )
    report = json.loads(output.read_text(encoding="utf-8"))

    assert report["classification"] == "C1_DETERMINISTIC_SHADOW_PLANNER_RESULT"
    assert report["review_volume"] == {
        "expected_plans": 13,
        "tuning": 9,
        "held_out": 4,
        "new_manual_plans": 0,
        "basis": "reuse sealed EvaluationPIPlan manual review",
    }
    assert report["selection_quality"]["tuning"]["tasks"] == 9
    assert report["selection_quality"]["held-out"]["tasks"] == 4
    assert report["selection_quality"]["overall"]["intent_accuracy"] == 1.0
    assert report["selection_quality"]["overall"]["capability_selection_precision"] == 1.0
    assert report["selection_quality"]["overall"]["capability_selection_recall"] == 1.0
    assert all(item["task_id_supplied_to_planner"] is False for item in report["results"])
    assert report["native_behavior"]["authority"] == "shadow_only"
    assert report["native_behavior"]["capabilities_executed"] == 0
    assert report["efficiency"]["llm_calls_executed"] == 0
    assert all(report["gates"].values())
