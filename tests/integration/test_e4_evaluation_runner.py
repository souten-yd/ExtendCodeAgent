from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest
from pytest import MonkeyPatch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import tools.local.evaluation_runner as evaluation_runner  # noqa: E402
from extendcodeagent.evaluation import EvaluationTrace, EvaluationTraceLog  # noqa: E402
from tools.local import adaptive_screening_runner  # noqa: E402
from tools.local.evaluation_runner import (  # noqa: E402
    CONFIGURABLE_CAPABILITIES,
    _activation_assessment,
    _activation_gate,
    _bind_migrated_checkpoint_to_local_schedule,
    _environment,
    _execute,
    _isolated_agent_environment,
    _metrics,
    _outcome_attribution,
    _pilot_active_assessment,
    _pilot_gate,
    _pilot_off_assessment,
    _provider_failure,
    _require_activation_report,
    _require_baseline_report,
    _run_opencode,
    _task_instruction,
    promote_pilot,
    requeue_provider_gaps,
)

RUNNER = ROOT / "tools/local/evaluation-runner"
MATRIX = ROOT / "docs/evaluation/evaluation-matrix-v1.json"
LABELS = ROOT / "docs/evaluation/labels-v1/graph-quality-labels.json"
METRICS = ROOT / "docs/evaluation/pi-verification-integrated-metrics-v1.json"
ACTIVATION_PLAN = ROOT / "docs/evaluation/b0a-activation-plan-v1.json"
QUALITY_TARGET_V1 = ROOT / "docs/evaluation/b0a-quality-target-v1.json"
QUALITY_TARGET_V2 = ROOT / "docs/evaluation/b0a-quality-target-v2.json"


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


def test_adaptive_policy_is_sealed_to_unchanged_evaluation_contracts() -> None:
    policy = adaptive_screening_runner._verify_policy()

    assert policy["hard_maximum_cells"] == 714
    assert policy["unchanged_contracts"]["effect_threshold"] == "inherited"
    assert policy["unchanged_contracts"]["oracle"] == "inherited"


def test_adaptive_step_limit_counts_only_completed_json_steps() -> None:
    log = "\n".join(
        [
            '{"type":"step_start"}',
            '{"type":"step_finish"}',
            '{"part":{"type":"step-finish"}}',
            "not-json",
        ]
    )

    assert adaptive_screening_runner._steps_in_text(log) == 2


def test_adaptive_batch_keeps_model_serial_while_cpu_finalization_pipelines(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    cells = [
        {"cell_id": "one", "task_id": "task"},
        {"cell_id": "two", "task_id": "task"},
    ]
    tasks = {"task": {"id": "task"}}
    first_finalizer_started = threading.Event()
    second_model_started = threading.Event()
    model_active = 0
    max_model_active = 0
    discarded: list[str] = []

    class Templates:
        def ensure_template(self, task_id: str) -> None:
            assert task_id == "task"

        def prepare_retry_safe(self, task_id: str, cell_id: str) -> Path:
            workspace = tmp_path / cell_id
            workspace.mkdir()
            return workspace

        def discard(self, task_id: str, workspace: Path) -> None:
            assert task_id == "task"
            discarded.append(workspace.name)
            workspace.rmdir()

    def agent(cell: dict[str, Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal model_active, max_model_active
        model_active += 1
        max_model_active = max(max_model_active, model_active)
        if cell["cell_id"] == "two":
            assert first_finalizer_started.wait(1)
            second_model_started.set()
        model_active -= 1
        return {"cell": cell, "provider_failure": False}

    def finalize(raw: dict[str, Any], *args: Any) -> dict[str, Any]:
        if raw["cell"]["cell_id"] == "one":
            first_finalizer_started.set()
            assert second_model_started.wait(1)
        return {"cell_id": raw["cell"]["cell_id"]}

    monkeypatch.setattr(adaptive_screening_runner, "_agent_only", agent)
    monkeypatch.setattr(adaptive_screening_runner, "_finalize_agent", finalize)
    monkeypatch.setattr(adaptive_screening_runner, "_persist_agent_capture", lambda *args: None)

    results = adaptive_screening_runner._execute_batch(
        cells,
        tasks=tasks,
        templates=Templates(),  # type: ignore[arg-type]
        raw_root=tmp_path,
        output_limit=10,
        step_limit=2,
    )

    assert [item["cell_id"] for item in results] == ["one", "two"]
    assert max_model_active == 1
    assert discarded == ["one", "two"]


def test_adaptive_migration_rejects_shared_runner_venv_access(tmp_path: Path) -> None:
    log = tmp_path / "cell.jsonl"
    log.write_text(
        json.dumps(
            {
                "type": "tool_use",
                "part": {
                    "state": {
                        "input": {
                            "command": (
                                f"source {(ROOT / '.venv').resolve()}/bin/activate "
                                "&& pip install -e ."
                            )
                        }
                    }
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    compatible, reasons = adaptive_screening_runner._compatible_result(
        {"model_tier": "local-practical", "output_tokens": 1},
        log,
        {"step_limit": 2, "output_limit": 10},
    )

    assert compatible is False
    assert reasons == ["shared_evaluation_venv_access"]


def test_adaptive_provider_gap_stops_batch_and_is_not_a_reusable_capture(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    cells = [
        {"cell_id": "gap", "task_id": "task"},
        {"cell_id": "must-remain-pending", "task_id": "task"},
    ]
    invoked: list[str] = []
    provider_captures: list[str] = []
    discarded: list[str] = []

    class Templates:
        def ensure_template(self, task_id: str) -> None:
            pass

        def prepare_retry_safe(self, task_id: str, cell_id: str) -> Path:
            workspace = tmp_path / cell_id
            workspace.mkdir()
            return workspace

        def discard(self, task_id: str, workspace: Path) -> None:
            discarded.append(workspace.name)
            workspace.rmdir()

    def agent(cell: dict[str, Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
        invoked.append(cell["cell_id"])
        return {"cell": cell, "provider_failure": "LOCAL_ENDPOINT_UNAVAILABLE"}

    def finalize(raw: dict[str, Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "cell_id": raw["cell"]["cell_id"],
            "provider_failure": raw["provider_failure"],
        }

    def persist_provider(raw: dict[str, Any], root: Path) -> Path:
        provider_captures.append(raw["cell"]["cell_id"])
        return root / "provider-attempt.json"

    monkeypatch.setattr(adaptive_screening_runner, "_agent_only", agent)
    monkeypatch.setattr(adaptive_screening_runner, "_finalize_agent", finalize)
    monkeypatch.setattr(
        adaptive_screening_runner,
        "_persist_provider_attempt",
        persist_provider,
    )
    monkeypatch.setattr(
        adaptive_screening_runner,
        "_persist_agent_capture",
        lambda *args: pytest.fail("provider gap must not become a reusable agent capture"),
    )

    results = adaptive_screening_runner._execute_batch(
        cells,
        tasks={"task": {"id": "task"}},
        templates=Templates(),  # type: ignore[arg-type]
        raw_root=tmp_path,
        output_limit=10,
        step_limit=2,
    )

    assert invoked == ["gap"]
    assert provider_captures == ["gap"]
    assert results == [{"cell_id": "gap", "provider_failure": "LOCAL_ENDPOINT_UNAVAILABLE"}]
    assert discarded == ["gap", "must-remain-pending"]


def test_provider_gap_pauses_only_its_queue_and_other_models_continue(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    planned = evaluation_runner.plan("base")["cells"]
    host = [item for item in planned if item["model_tier"] == "host-default"][:2]
    local = next(item for item in planned if item["model_tier"] == "local-practical")
    schedule = {"scope": "base", "counts": {"cells": 3}, "cells": [*host, local]}
    invoked: list[str] = []

    monkeypatch.setattr(evaluation_runner, "plan", lambda *args, **kwargs: schedule)
    monkeypatch.setattr(evaluation_runner, "_append_trace", lambda *args: None)

    def execute(cell: dict[str, Any], task: dict[str, Any], raw_root: Path) -> dict[str, Any]:
        invoked.append(cell["cell_id"])
        return {
            **cell,
            "outcome": "UNAVAILABLE" if cell["model_tier"] == "host-default" else "FAIL",
            "provider_failure": ("RATE_LIMIT" if cell["model_tier"] == "host-default" else None),
        }

    monkeypatch.setattr(evaluation_runner, "_execute", execute)
    output = tmp_path / "result.json"
    evaluation_runner.run(
        "base",
        output,
        None,
        None,
        None,
        None,
        False,
        tmp_path / "raw",
        None,
        None,
        None,
        [],
    )
    report = json.loads(output.read_text())
    assert invoked == [host[0]["cell_id"], local["cell_id"]]
    assert report["provider_queue"]["host-default"]["status"] == "PAUSED_PROVIDER_GAP"
    assert len(report["provider_attempts"]) == 1
    assert [item["cell_id"] for item in report["results"]] == [local["cell_id"]]
    assert report["execution_scope"] == "local-only"
    assert report["model"] == "Qwen3.6 27B"
    assert report["endpoint"] == "127.0.0.1:8090"
    assert report["context"] == 262144
    assert report["output_limit"] == 8192


def test_local_only_policy_blocks_new_nonlocal_provider_execution(tmp_path: Path) -> None:
    cell = {
        "model_status": "AVAILABLE",
        "model_tier": "frontier-codex",
    }
    with pytest.raises(evaluation_runner.EvaluationError, match="local-only execution policy"):
        _execute(cell, {}, tmp_path)

    probe = _run(
        "probe-provider",
        "--model-tier",
        "frontier-sonnet",
        "--output",
        str(tmp_path / "probe.json"),
    )
    assert probe.returncode == 1
    assert "local-only execution policy" in probe.stderr
    assert not (tmp_path / "probe.json").exists()


def test_opencode_provider_failure_is_classified_and_stops_early(tmp_path: Path) -> None:
    script = tmp_path / "provider-gap.py"
    script.write_text(
        "import sys, time\n"
        "message = 'Rate limit exceeded. Please try again later.'\n"
        "print(f'AI_APICallError: {message}', file=sys.stderr, flush=True)\n"
        "print(f'AI_RetryError: Failed after 3 attempts. Last error: {message}', "
        "file=sys.stderr, flush=True)\n"
        "time.sleep(30)\n",
        encoding="utf-8",
    )
    started = time.monotonic()
    stdout, stderr, process_exit, timed_out, provider_failure = _run_opencode(
        [sys.executable, str(script)], cwd=ROOT, env=dict(os.environ), timeout=20
    )
    assert time.monotonic() - started < 5
    assert stdout == ""
    assert "AI_RetryError" in stderr
    assert process_exit is not None
    assert timed_out is False
    assert provider_failure == "RATE_LIMIT"
    assert _provider_failure("AuthenticationError") == "AUTHENTICATION"
    assert _provider_failure("You have exceeded your monthly quota") == "QUOTA_EXHAUSTED"


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
    quality_v1 = json.loads(QUALITY_TARGET_V1.read_text(encoding="utf-8"))
    quality_v2 = json.loads(QUALITY_TARGET_V2.read_text(encoding="utf-8"))
    assert quality_v1["seal"]["canonical_payload"] == (
        "64f9ec41f05f245e5e13d89a99dfccae8adce3a8902ed739c7203cd63fa98667"
    )
    assert quality_v2["seal"] == {
        "algorithm": "sha256",
        "canonical_payload": _digest(quality_v2),
    }
    assert quality_v2["quality_models"] == ["local-practical"]


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
    assert activation_plan["counts"] == {"cells": 1, "available": 1, "unavailable": 0}
    assert {item["arm"] for item in activation_plan["cells"]} == {"active"}
    assert {item["task_id"] for item in activation_plan["cells"]} == {"eca-symbol-001"}
    assert {item["model_tier"] for item in activation_plan["cells"]} == {"local-practical"}
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
    assert baseline_plan["counts"] == {"cells": 54, "available": 54, "unavailable": 0}
    assert {item["model_tier"] for item in baseline_plan["cells"]} == {"local-practical"}
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
    assert gaps == []

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
    for model in ("local-practical",):
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
    assert gate["comprehensive_evaluation_permitted"] is True
    assert gate["capability_route_gaps"] == []

    results[0]["selected_evidence_ids"] = []
    failed = _activation_gate(results)
    assert failed["status"] == "FAIL"
    assert failed["failed_models"] == ["local-practical"]
    assert failed["assessment_mismatches"] == ["local-practical"]


def test_activation_requires_only_the_local_first_quality_model(tmp_path: Path) -> None:
    results = []
    for model in ("local-practical",):
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
    report = {
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "schedule": {"scope": "b0a-activation"},
        "results": results,
        "activation_gate": _activation_gate(results),
        "provider_queue": {},
    }
    path = tmp_path / "activation.json"
    path.write_text(json.dumps(report))
    evidence = _require_activation_report(path, require_comprehensive=True)
    assert evidence["status"] == "PASS"
    assert evidence["activated_models"] == ["local-practical"]


def test_screening_requires_a_complete_sealed_exact_head_baseline(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    cell = evaluation_runner.plan("b0a-baseline")["cells"][0]
    schedule = {
        "scope": "b0a-baseline",
        "matrix_id": "matrix",
        "counts": {"cells": 1},
        "cells": [cell],
    }
    monkeypatch.setattr(evaluation_runner, "plan", lambda *args, **kwargs: schedule)
    trace_path = tmp_path / "traces.jsonl"
    trace_id = "baseline-trace"
    EvaluationTraceLog(trace_path).append(
        EvaluationTrace(
            trace_id=trace_id,
            plan_id="plan",
            cell_id=cell["cell_id"],
            task_id=cell["task_id"],
            task_class=cell["task_class"],
            oracle_id=f"e3-oracle:{cell['task_id']}",
            input_seals={"matrix": "seal"},
            capability_state_source="planned_matrix",
            capability_modes={},
            capability_depths={},
            used_features={},
            selected_evidence_ids=(),
            source_revision_id="repo",
            twin_revision_id=None,
            model_tier=cell["model_tier"],
            model_id=cell["model_id"],
            verification_outcome="PASS",
            fallback=None,
        )
    )
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    completion: dict[str, Any] = {
        "model_tiers": sorted(evaluation_runner.B0A_QUALITY_MODELS),
        "expected_cells": 1,
        "completed_cells": 1,
        "pending_cells": 0,
    }
    body: dict[str, Any] = {
        "schedule": {key: value for key, value in schedule.items() if key != "cells"},
        "source_revision": revision,
        "trace_log": str(trace_path),
        "results": [{**cell, "outcome": "PASS", "trace_id": trace_id}],
        "target_completion": completion,
    }
    path = tmp_path / "baseline.json"
    path.write_text(
        json.dumps(
            {
                **body,
                "seal": {"algorithm": "sha256", "canonical_payload": _digest(body)},
            }
        )
    )
    evidence = _require_baseline_report(path)
    assert evidence["completed_cells"] == 1
    assert evidence["trace_integrity"] == "PASS"

    incomplete = {
        **body,
        "results": [],
        "target_completion": {
            **completion,
            "completed_cells": 0,
            "pending_cells": 1,
        },
    }
    path.write_text(
        json.dumps(
            {
                **incomplete,
                "seal": {"algorithm": "sha256", "canonical_payload": _digest(incomplete)},
            }
        )
    )
    with pytest.raises(evaluation_runner.EvaluationError, match="incomplete"):
        _require_baseline_report(path)


def test_requeue_moves_quota_failures_out_of_quality_results(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    planned = evaluation_runner.plan("b0a-baseline")["cells"][:3]
    raw = tmp_path / "source-raw"
    trace_path = raw / "traces.jsonl"
    results = []
    for index, cell in enumerate(planned):
        result = {
            **cell,
            "outcome": "UNAVAILABLE" if index == 0 else "FAIL",
            "trace_id": f"trace-{index}",
            **({"result_origin": "migrated_checkpoint"} if index == 1 else {}),
        }
        results.append(result)
        EvaluationTraceLog(trace_path).append(
            EvaluationTrace(
                trace_id=result["trace_id"],
                plan_id="plan",
                cell_id=cell["cell_id"],
                task_id=cell["task_id"],
                task_class=cell["task_class"],
                oracle_id=f"e3-oracle:{cell['task_id']}",
                input_seals={"matrix": "seal"},
                capability_state_source="planned_matrix",
                capability_modes={},
                capability_depths={},
                used_features={},
                selected_evidence_ids=(),
                source_revision_id="repo",
                twin_revision_id=None,
                model_tier=cell["model_tier"],
                model_id=cell["model_id"],
                verification_outcome=result["outcome"],
                fallback=None,
            )
        )
    logs = raw / "logs"
    logs.mkdir(parents=True)
    (logs / f"{planned[0]['cell_id']}.stderr.log").write_text(
        "AI_APICallError: You have exceeded your monthly quota"
    )
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps(
            {
                "schedule": {"scope": "b0a-baseline"},
                "trace_log": str(trace_path),
                "result_origin": "migrated_checkpoint",
                "latency_status": "LEGACY_RUNNER_SEPARATE",
                "latency_merge_permitted": False,
                "migration_summary": {"migrated_cells": 3},
                "results": results,
            }
        )
    )
    schedule = {"scope": "b0a-baseline", "counts": {"cells": 3}, "cells": planned}
    monkeypatch.setattr(evaluation_runner, "plan", lambda *args, **kwargs: schedule)
    monkeypatch.setattr(evaluation_runner, "_require_clean_worktree", lambda: None)
    repaired = requeue_provider_gaps(source, tmp_path / "repaired.json", tmp_path / "repaired-raw")
    assert repaired["executed_cells"] == 2
    assert repaired["target_completion"]["pending_cells"] == 1
    assert repaired["provider_queue"][planned[0]["model_tier"]]["failure"] == ("QUOTA_EXHAUSTED")
    assert repaired["provider_requeue"]["requeued_count"] == 1
    assert repaired["result_origin"] == "mixed_checkpoint"
    assert repaired["latency_status"] == "MIXED_LEGACY_AND_CURRENT_SEPARATE"
    assert repaired["migration_summary"]["migrated_cells"] == 1
    assert repaired["migration_summary"]["current_runner_cells"] == 1
    assert len(EvaluationTraceLog(Path(repaired["trace_log"])).replay()) == 2


def test_migration_binds_only_local_cells_to_the_v2_baseline(
    monkeypatch: MonkeyPatch,
) -> None:
    cell = evaluation_runner.plan("b0a-baseline")["cells"][0]
    schedule = {
        "scope": "b0a-baseline",
        "counts": {"cells": 2, "available": 2, "unavailable": 0},
        "b0a": {"quality_target_seal": "v2"},
        "cells": [cell, {**cell, "cell_id": f"{cell['cell_id']}-second"}],
    }
    monkeypatch.setattr(evaluation_runner, "plan", lambda *args, **kwargs: schedule)
    migrated = {
        "results": [{**cell, "outcome": "PASS"}],
        "migration_summary": {"migrated_cells": 1},
        "provider_queue": {"frontier-codex": {"status": "PAUSED_PROVIDER_GAP"}},
        "provider_attempts": [{"model_tier": "frontier-codex"}],
    }
    bound = _bind_migrated_checkpoint_to_local_schedule(migrated)
    assert bound["schedule"] == {key: value for key, value in schedule.items() if key != "cells"}
    assert bound["target_completion"] == {
        "model_tiers": ["local-practical"],
        "expected_cells": 2,
        "completed_cells": 1,
        "pending_cells": 1,
    }
    assert bound["migration_summary"]["quality_target_cells"] == 2
    assert bound["migration_summary"]["historical_provider_queue_tiers_excluded"] == [
        "frontier-codex"
    ]
    assert bound["migration_summary"]["historical_provider_attempts_excluded"] == 1
    assert bound["provider_queue"] == {}
    assert bound["provider_attempts"] == []
    assert bound["execution_scope"] == "local-only"
    assert bound["seal"] == {
        "algorithm": "sha256",
        "canonical_payload": _digest(bound),
    }


def test_promoted_pilot_requires_a_fully_reusable_sealed_audit(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    gate = {
        "decision": "PROCEED_TO_COMPREHENSIVE",
        "activation_plan_seal": json.loads(ACTIVATION_PLAN.read_text())["seal"][
            "canonical_payload"
        ],
        "passes": {"native": 0, "off": 0, "active": 1},
        "active_pass_delta_over_best_control": 1,
    }
    source = {
        "source_revision": "old",
        "schedule": {"scope": "b0a-pilot"},
        "executed_cells": 1,
        "results": [{"cell_id": "cell"}],
        "pilot_gate": gate,
    }
    source_path = tmp_path / "pilot.json"
    source_path.write_text(json.dumps(source))
    audit_body: dict[str, Any] = {
        "source_checkpoint_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "trace_integrity": "PASS",
        "counts": {"REUSABLE": 1},
        "compatibility_manifest": "manifest.json",
        "compatibility_manifest_seal": "manifest-seal",
    }
    audit_path = tmp_path / "audit.json"
    audit_path.write_text(
        json.dumps(
            {
                **audit_body,
                "seal": {"algorithm": "sha256", "canonical_payload": _digest(audit_body)},
            }
        )
    )
    monkeypatch.setattr(evaluation_runner, "_require_clean_worktree", lambda: None)
    monkeypatch.setattr(evaluation_runner, "_pilot_gate", lambda results: gate)
    promoted = promote_pilot(source_path, audit_path)
    assert promoted["decision"] == "PROCEED_TO_COMPREHENSIVE"
    assert promoted["latency_merge_permitted"] is False


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


def test_effect_pilot_accepts_task_ready_repository_path_evidence() -> None:
    result: dict[str, Any] = {
        "task_id": "eca-tests-001",
        "outcome": "PASS",
        "process_exit": 0,
        "errors": [],
        "pi_tools": ["pi_status", "pi_symbol", "pi_tests"],
        "observed_pi_readiness": "ready",
        "observed_capability_modes": {
            capability: "active" for capability in CONFIGURABLE_CAPABILITIES
        },
        "observed_capability_depths": {
            capability: "D2" for capability in CONFIGURABLE_CAPABILITIES
        },
        "twin_revision_ids": ["twin-1"],
        "selected_evidence_ids": ["repo_path:tests/unit/test_verification.py"],
        "pi_analysis_ms": 10,
    }

    assert _activation_assessment(result)["status"] == "FAIL"
    assert _pilot_active_assessment(result) == {
        "status": "PASS",
        "reasons": [],
        "task_oracle_outcome": "PASS",
    }


def test_answer_instruction_is_exact_for_all_arms_and_preserves_compact_pi_fields() -> None:
    suite = json.loads((ROOT / "docs/evaluation/task-suite-v1.json").read_text())
    task = next(item for item in suite["tasks"] if item["id"] == "eca-impact-001")

    native = _task_instruction({"arm": "native"}, task, "native")
    active = _task_instruction({"arm": "active", "pi_effect_pilot": True}, task, "active")

    assert "keys as an exact schema" in native
    assert "add no explanation" in native
    assert "copy that field without removing paths" in active
    assert "expanding scalar/path values into explanation objects" in active


def test_local_practical_output_is_bounded_for_every_arm(tmp_path: Path) -> None:
    assert evaluation_runner.plan("b0a-baseline")["cells"][0]["model_id"] == (
        "eca-local-practical/llama"
    )
    for arm in ("native", "off", "active"):
        arm_root = tmp_path / arm
        arm_root.mkdir()
        env, model_id = _environment(arm, "local-practical", arm_root / "workspace")
        config = json.loads(env["OPENCODE_CONFIG_CONTENT"])

        assert model_id == "eca-local-practical/llama"
        assert config["provider"]["eca-local-practical"]["models"]["llama"]["limit"] == {
            "context": 262144,
            "output": 8192,
        }
        assert config["permission"]["external_directory"] == "deny"


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


def test_metrics_split_pi_and_post_tool_model_time(tmp_path: Path) -> None:
    log_path = tmp_path / "events.jsonl"
    events = [
        {
            "type": "tool_use",
            "part": {
                "tool": "extendcodeagent_pi_symbol",
                "state": {
                    "input": {"query": "select_tests"},
                    "time": {"start": 1_000, "end": 1_120},
                    "output": json.dumps(
                        {
                            "items": [
                                {
                                    "path": "src/extendcodeagent/testing/service.py",
                                    "canonical_ref": "py://testing.service#select_tests",
                                }
                            ],
                            "symbols": ["py://testing.service#select_tests"],
                            "selected_tests": ["tests/unit/test_test_intelligence.py"],
                            "revision_id": "twin-1",
                            "capabilities_used": ["blueprint", "strategy"],
                            "timing": {
                                "cold_twin_build_ms": 80.0,
                                "snapshot_load_ms": 7.0,
                                "adjacency_index_build_ms": 0.0,
                                "query_execution_ms": 4.0,
                                "json_serialization_ms": 1.0,
                            },
                        }
                    ),
                },
            },
        },
        {
            "type": "tool_use",
            "part": {
                "tool": "grep",
                "state": {
                    "time": {"start": 1_220, "end": 1_270},
                    "output": "native search output",
                },
            },
        },
        {
            "type": "text",
            "part": {"type": "text", "time": {"start": 1_120, "end": 1_420}},
        },
        {
            "type": "tool_use",
            "part": {
                "tool": "pi_references",
                "state": {
                    "time": {"start": 1_300, "end": 1_320},
                    "output": "{}",
                },
            },
        },
    ]
    log_path.write_text("\n".join(json.dumps(event) for event in events), encoding="utf-8")

    measured = _metrics(log_path)

    assert measured["pi_analysis_ms"] == 140
    assert measured["pi_timing_ms"] == {
        "cold_twin_build_ms": 80.0,
        "snapshot_load_ms": 7.0,
        "adjacency_index_build_ms": 0.0,
        "query_execution_ms": 4.0,
        "json_serialization_ms": 1.0,
        "model_reasoning_after_tool_ms": 230,
    }
    assert "src/extendcodeagent/testing/service.py" in measured["observed_pi_facts"]
    assert measured["pi_capabilities_used"] == ["blueprint", "strategy"]
    assert measured["pi_tool_requests"][0] == {
        "tool": "pi_symbol",
        "input": {"query": "select_tests"},
    }
    assert "canonical_ref:py://testing.service#select_tests" in measured["selected_evidence_ids"]
    assert "repo_path:tests/unit/test_test_intelligence.py" in measured["selected_evidence_ids"]


def test_metrics_report_request_context_distribution_not_cell_total(tmp_path: Path) -> None:
    log_path = tmp_path / "events.jsonl"
    inputs = [17, 1_175, 16_825, 37_718, 41_742]
    cache_reads = [0, 100, 2_000, 4_000, 8_000]
    cache_writes = [0, 0, 0, 0, 1_000]
    log_path.write_text(
        "\n".join(
            json.dumps(
                {
                    "type": "step_finish",
                    "part": {
                        "type": "step-finish",
                        "tokens": {
                            "input": value,
                            "output": 1,
                            "cache": {"read": cache_read, "write": cache_write},
                        },
                    },
                }
            )
            for value, cache_read, cache_write in zip(
                inputs, cache_reads, cache_writes, strict=True
            )
        ),
        encoding="utf-8",
    )

    measured = _metrics(log_path)

    assert measured["input_tokens"] == sum(inputs)
    assert measured["cache_read_tokens"] == sum(cache_reads)
    assert measured["cache_write_tokens"] == sum(cache_writes)
    assert measured["context_request_count"] == 5
    assert measured["context_token_sum"] == 112_577
    assert measured["average_context_tokens"] == 22_515.4
    assert measured["p50_context_tokens"] == 18_825
    assert measured["p90_context_tokens"] == 50_742
    assert measured["p95_context_tokens"] == 50_742
    assert measured["p99_context_tokens"] == 50_742
    assert measured["max_context_tokens"] == 50_742


def test_metrics_preserve_pi_tool_error_reason_for_expected_disabled_route(
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "events.jsonl"
    log_path.write_text(
        json.dumps(
            {
                "type": "tool_use",
                "part": {
                    "tool": "pi_impact",
                    "state": {
                        "status": "error",
                        "input": {"changed_refs": ["py://example#symbol"]},
                        "error": "capability_unavailable: impact is not available for explicit use",
                    },
                },
            }
        )
    )

    measured = _metrics(log_path)

    assert measured["pi_tool_failures"] == [
        {
            "tool": "pi_impact",
            "reason": "capability_unavailable: impact is not available for explicit use",
        }
    ]


def test_outcome_attribution_measures_required_verification_set_without_weakening_oracle(
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

    attribution = _outcome_attribution(
        task, tmp_path, arm="active", oracle_exit=1, observed_pi_facts=[]
    )

    assert attribution["final_exact_pass"] is False
    assert attribution["required_verification_set_quality"] == {
        "status": "MEASURED_BY_SEALED_TASK_ORACLE",
        "true_positive": 1,
        "false_positive": 1,
        "false_negative": 1,
        "precision": 0.5,
        "recall": 0.5,
    }


def test_outcome_attribution_separates_retrieval_projection_and_reasoning(
    tmp_path: Path,
) -> None:
    expected = {
        "status": "completed",
        "definition": "src/service.py",
        "tests": ["tests/unit/test_service.py"],
    }
    task = {
        "oracle": {
            "checks": [
                {
                    "kind": "answer",
                    "path": ".eca-eval/answer.json",
                    "equals": expected,
                }
            ]
        }
    }
    answer_path = tmp_path / ".eca-eval/answer.json"
    answer_path.parent.mkdir()
    answer_path.write_text(
        json.dumps({"status": "completed", "definition": "src/service.py", "tests": []}),
        encoding="utf-8",
    )

    retrieval = _outcome_attribution(
        task,
        tmp_path,
        arm="active",
        oracle_exit=1,
        observed_pi_facts=["src/service.py"],
    )
    assert retrieval == {
        "classification": "RETRIEVAL_MISSING",
        "required_fact_recall": 0.5,
        "pi_required_fact_recall": 0.5,
        "schema_valid": True,
        "final_exact_pass": False,
    }

    answer_path.write_text(
        json.dumps({**expected, "tests": "tests/unit/test_service.py"}), encoding="utf-8"
    )
    projection = _outcome_attribution(
        task,
        tmp_path,
        arm="active",
        oracle_exit=1,
        observed_pi_facts=["src/service.py", "tests/unit/test_service.py"],
    )
    assert projection["classification"] == "PROJECTION_SCHEMA_ERROR"
    assert projection["required_fact_recall"] == 1.0
    assert projection["pi_required_fact_recall"] == 1.0
    assert projection["schema_valid"] is False

    answer_path.write_text(
        json.dumps(
            {"status": "completed", "definition": "src/other.py", "tests": expected["tests"]}
        ),
        encoding="utf-8",
    )
    reasoning = _outcome_attribution(
        task,
        tmp_path,
        arm="active",
        oracle_exit=1,
        observed_pi_facts=["src/service.py", "tests/unit/test_service.py"],
    )
    assert reasoning["classification"] == "AGENT_REASONING_ERROR"
    assert reasoning["schema_valid"] is True

    answer_path.write_text(json.dumps(expected), encoding="utf-8")
    passed = _outcome_attribution(
        task,
        tmp_path,
        arm="active",
        oracle_exit=0,
        observed_pi_facts=["src/service.py", "tests/unit/test_service.py"],
    )
    assert passed["classification"] == "PASS"
    assert passed["final_exact_pass"] is True


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
    assert entries["blueprint"]["decision"] == "NOT_TESTED_ROUTE_GAP"


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
    assert set(active["timings_ms"]) == {
        "agent_wall",
        "pi_analysis",
        "cold_twin_build",
        "snapshot_load",
        "adjacency_index_build",
        "query_execution",
        "json_serialization",
        "model_reasoning_after_tool",
    }
