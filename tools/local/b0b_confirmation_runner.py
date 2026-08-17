#!/usr/bin/env python3
"""Local-only, relevance-gated B0b held-out confirmation runner."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from extendcodeagent.evaluation import EvaluationTraceLog
from tools.local import adaptive_screening_runner as adaptive
from tools.local import evaluation_runner as legacy

ROOT = Path(__file__).resolve().parents[2]
BASE_ARMS = {"native", "off", "active"}
B0A_EXECUTION_EVIDENCE = ROOT / "docs/evidence/final/b0a-adaptive-screening-execution-v1.json"


class ConfirmationError(RuntimeError):
    """Raised when B0b cannot preserve its sealed confirmation contract."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfirmationError(f"cannot read {path}: {error}") from error
    if not isinstance(value, dict):
        raise ConfirmationError(f"{path} root must be an object")
    return value


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def create_plan(output: Path) -> None:
    schedule = legacy.plan("b0b-confirmation")
    execution_evidence = _load(B0A_EXECUTION_EVIDENCE)
    legacy._verify_seal(execution_evidence, "B0a adaptive execution evidence")
    cells = schedule["cells"]
    base = [item for item in cells if item["arm"] in BASE_ARMS]
    conditional = [item for item in cells if item["arm"].startswith("ablation:")]
    if len(cells) != 108 or len(base) != 36 or len(conditional) != 72:
        raise ConfirmationError("B0b contract must remain 108 = 36 base + 72 conditional cells")
    result = adaptive._sealed(
        {
            "schema": 1,
            "classification": "B0B_LOCAL_CONFIRMATION_EXECUTION_PLAN",
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "source_revision": _head(),
            "matrix_seal": schedule["matrix_seal"],
            "task_suite_seal": schedule["task_suite_seal"],
            "adaptive_screening_result_seal": schedule["b0a"][
                "adaptive_screening_result_seal"
            ],
            "quality_target_seal": schedule["b0a"]["quality_target_seal"],
            "workspace_evidence_seal": execution_evidence["seal"]["canonical_payload"],
            "execution_scope": "local-only",
            "model": "Qwen3.6 27B",
            "endpoint": "127.0.0.1:8090",
            "context": 262144,
            "output_limit": 8192,
            "claim_scope": "active-scoped(local-practical)",
            "held_out_tasks": sorted({item["task_id"] for item in cells}),
            "candidates": list(schedule["b0a"]["confirmation_candidates"]),
            "repetitions": 3,
            "hard_maximum_calls": len(cells),
            "expected_calls_before_active_trace": len(cells),
            "mandatory_base_calls": len(base),
            "conditional_ablation_maximum_calls": len(conditional),
            "reused_calls": 0,
            "reuse_reason": "NO_COMPATIBLE_HELD_OUT_CONFIRMATION_EVIDENCE",
            "relevance_rule": (
                "run a capability-task ablation for all three repetitions only when all three "
                "active repetitions PASS and actively exercise the capability"
            ),
            "full_repetition_rule": True,
            "sequential_screening_stop_forbidden": True,
            "step_limit": None,
            "step_limit_reason": (
                "confirmation correctness uses the task timeout and sealed model output limit"
            ),
            "workspace_strategy": execution_evidence["workspace_benchmark"]["selected"],
            "cells": cells,
        }
    )
    legacy._write_report(output, result)


def _verify_plan(plan: Mapping[str, Any]) -> None:
    legacy._verify_seal(dict(plan), "B0b confirmation plan")
    if plan.get("classification") != "B0B_LOCAL_CONFIRMATION_EXECUTION_PLAN":
        raise ConfirmationError("unsupported B0b confirmation plan")
    if plan.get("source_revision") != _head():
        raise ConfirmationError("B0b plan must be regenerated at the exact execution head")
    schedule = legacy.plan("b0b-confirmation")
    execution_evidence = _load(B0A_EXECUTION_EVIDENCE)
    legacy._verify_seal(execution_evidence, "B0a adaptive execution evidence")
    expected = {
        "matrix_seal": schedule["matrix_seal"],
        "task_suite_seal": schedule["task_suite_seal"],
        "adaptive_screening_result_seal": schedule["b0a"][
            "adaptive_screening_result_seal"
        ],
        "quality_target_seal": schedule["b0a"]["quality_target_seal"],
        "workspace_evidence_seal": execution_evidence["seal"]["canonical_payload"],
    }
    for key, value in expected.items():
        if plan.get(key) != value:
            raise ConfirmationError(f"B0b plan {key} is stale")
    if plan.get("cells") != schedule["cells"]:
        raise ConfirmationError("B0b plan cells differ from the sealed schedule")


def _decisions(
    plan: Mapping[str, Any],
    results: Mapping[str, Mapping[str, Any]],
    skips: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    cells = list(plan["cells"])
    by_id = {item["cell_id"]: item for item in cells}
    threshold_rate = float(
        _load(legacy.B0A_PLAN)["screening"]["effect_threshold"][
            "minimum_absolute_pass_rate_delta"
        ]
    )
    decisions: dict[str, Any] = {}
    for capability in plan["candidates"]:
        ablation_cells = [
            item for item in cells if item["arm"] == f"ablation:{capability}"
        ]
        paired: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
        for cell in ablation_cells:
            if cell["cell_id"] not in results:
                continue
            active_id = cell["cell_id"].replace(
                f"ablation:{capability}--", "active--", 1
            )
            if active_id in results:
                paired.append((results[active_id], results[cell["cell_id"]]))
        active_pass = sum(active["outcome"] == "PASS" for active, _ in paired)
        ablation_pass = sum(ablated["outcome"] == "PASS" for _, ablated in paired)
        critical = any(
            active["outcome"] == "PASS"
            and ablated["outcome"] != "PASS"
            and by_id[active["cell_id"]]["task_class"]
            in {"negative-control", "unsafe-or-insufficient-evidence"}
            for active, ablated in paired
        )
        threshold = max(1, math.ceil(threshold_rate * len(paired))) if paired else None
        skip_reasons = Counter(
            str(skips[item["cell_id"]]["reason"])
            for item in ablation_cells
            if item["cell_id"] in skips
        )
        if not paired:
            decision = "NOT_TESTED_NO_RELEVANT_COMPLETE_ACTIVE_BASELINE"
        elif len(paired) % 3:
            decision = "NOT_TESTED_INCOMPLETE_REPETITIONS"
        elif active_pass - ablation_pass >= int(threshold or 1) or critical:
            decision = "CONFIRMED_POSITIVE_LOCAL_PRACTICAL"
        else:
            decision = "NO_CONFIRMED_EFFECT_LOCAL_PRACTICAL"
        decisions[capability] = {
            "decision": decision,
            "paired_cells": len(paired),
            "active_pass": active_pass,
            "ablation_pass": ablation_pass,
            "pass_delta": active_pass - ablation_pass,
            "effect_threshold_pass_delta": threshold,
            "critical_override": critical,
            "skip_reasons": dict(skip_reasons),
            "claim_scope": "active-scoped(local-practical)",
        }
    return decisions


def _report(
    plan: Mapping[str, Any],
    results: Mapping[str, dict[str, Any]],
    skips: Mapping[str, dict[str, Any]],
    provider_attempts: Sequence[dict[str, Any]],
    trace_log: EvaluationTraceLog,
    started: float,
) -> dict[str, Any]:
    executed = len(results)
    avoided = len(skips)
    accounted = set(results) | set(skips)
    provider_gap_pending = any(
        item.get("cell_id") not in results for item in provider_attempts
    )
    active_results = [item for item in results.values() if item["arm"] == "active"]
    required_set_quality = [
        item["outcome_attribution"]["required_verification_set_quality"]
        for item in active_results
        if item["task_id"] == "kasane-tests-001"
        and isinstance(item.get("outcome_attribution"), dict)
        and isinstance(
            item["outcome_attribution"].get("required_verification_set_quality"), dict
        )
    ]
    cross_boundary = [
        item for item in active_results if item["task_id"] == "kasane-cross-boundary-001"
    ]
    unsafe = [item for item in active_results if item["task_id"] == "kasane-unsafe-001"]
    phase = (
        "COMPLETE"
        if len(accounted) == int(plan["hard_maximum_calls"])
        else "COLLECTING_BASE"
        if any(
            item["arm"] in BASE_ARMS and item["cell_id"] not in accounted
            for item in plan["cells"]
        )
        else "COLLECTING_RELEVANT_ABLATIONS"
    )
    body = {
        "schema": 1,
        "classification": f"B0B_LOCAL_CONFIRMATION_{phase}",
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "source_revision": _head(),
        "confirmation_plan": plan["seal"]["canonical_payload"],
        "execution_scope": "local-only",
        "model": "Qwen3.6 27B",
        "endpoint": "127.0.0.1:8090",
        "context": 262144,
        "output_limit": 8192,
        "claim_scope": "active-scoped(local-practical)",
        "hard_maximum_calls": plan["hard_maximum_calls"],
        "expected_calls_before_active_trace": plan["expected_calls_before_active_trace"],
        "llm_calls_executed": executed + len(provider_attempts),
        "quality_results_completed": executed,
        "llm_calls_avoided": avoided,
        "avoided_call_ratio": round(avoided / int(plan["hard_maximum_calls"]), 6),
        "unique_cells_accounted": len(accounted),
        "results": list(results.values()),
        "outcomes": dict(Counter(item["outcome"] for item in results.values())),
        "skips": list(skips.values()),
        "skip_counts": dict(Counter(item["reason"] for item in skips.values())),
        "provider_attempts": list(provider_attempts),
        "provider_gap_pending": provider_gap_pending,
        "decisions": _decisions(plan, results, skips),
        "held_out_measurements": {
            "required_verification_set_quality": {
                "measured_repetitions": len(required_set_quality),
                "precision": [item["precision"] for item in required_set_quality],
                "recall": [item["recall"] for item in required_set_quality],
                "source": "sealed kasane-tests-001 oracle",
            },
            "cross_boundary_gui_runtime_follow_through": {
                "measured_repetitions": len(cross_boundary),
                "exact_pass": sum(item["outcome"] == "PASS" for item in cross_boundary),
                "classifications": dict(
                    Counter(
                        item.get("outcome_attribution", {}).get("classification", "UNKNOWN")
                        for item in cross_boundary
                    )
                ),
            },
            "unsafe_claim_completion_correctness": {
                "measured_repetitions": len(unsafe),
                "exact_pass": sum(item["outcome"] == "PASS" for item in unsafe),
            },
        },
        "efficiency": {
            "llm_calls_requested": int(plan["hard_maximum_calls"]),
            "llm_calls_executed": executed + len(provider_attempts),
            "llm_calls_avoided": avoided,
            "avoided_call_ratio": round(avoided / int(plan["hard_maximum_calls"]), 6),
            "input_tokens": sum(int(item.get("input_tokens") or 0) for item in results.values()),
            "output_tokens": sum(int(item.get("output_tokens") or 0) for item in results.values()),
            "reasoning_tokens": sum(
                int(item.get("reasoning_tokens") or 0) for item in results.values()
            ),
            "model_wall_time_ms": sum(
                float(item.get("model_wall_ms") or item.get("wall_ms") or 0)
                for item in results.values()
            ),
            "deterministic_pi_wall_time_ms": sum(
                float(item.get("pi_analysis_ms") or 0) for item in results.values()
            ),
            "total_observed_cell_wall_time_ms": sum(
                float(item.get("wall_ms") or 0) for item in results.values()
            ),
            "checkpoint_session_wall_time_ms": round((time.monotonic() - started) * 1000, 3),
            "deterministic_resolution_ratio": round(
                avoided / int(plan["hard_maximum_calls"]), 6
            ),
            "escalation_rate": round(
                sum(item["arm"].startswith("ablation:") for item in results.values())
                / int(plan["hard_maximum_calls"]),
                6,
            ),
            "average_context_tokens": round(
                sum(int(item.get("input_tokens") or 0) for item in results.values()) / executed,
                3,
            )
            if executed
            else 0.0,
            "max_context_tokens": max(
                (int(item.get("input_tokens") or 0) for item in results.values()), default=0
            ),
            "minimum_sufficient_depth": "INHERITED_SCREENED_CONFIGURATION",
            "reused_evidence_count": 0,
            "invalidated_evidence_count": 0,
        },
        "trace_log": str(trace_log.path),
        "promotion_or_demotion_pending_gap_report": True,
    }
    return adaptive._sealed(body)


def run(plan_path: Path, raw_root: Path, output: Path, *, resume: bool) -> None:
    legacy._require_clean_worktree()
    plan = _load(plan_path)
    _verify_plan(plan)
    if output.exists() and not resume:
        raise ConfirmationError("B0b output exists; use --resume")
    raw_root.mkdir(parents=True, exist_ok=True)
    tasks = {item["id"]: item for item in _load(legacy.TASK_SUITE)["tasks"]}
    cells = list(plan["cells"])
    cell_map = {item["cell_id"]: item for item in cells}
    results: dict[str, dict[str, Any]] = {}
    skips: dict[str, dict[str, Any]] = {}
    provider_attempts: list[dict[str, Any]] = []
    if resume and output.is_file():
        previous = _load(output)
        if previous.get("confirmation_plan") != plan["seal"]["canonical_payload"]:
            raise ConfirmationError("resume output uses another B0b plan")
        results.update({item["cell_id"]: item for item in previous.get("results", ())})
        skips.update({item["cell_id"]: item for item in previous.get("skips", ())})
        provider_attempts.extend(previous.get("provider_attempts", ()))
    fragments = raw_root / "result-fragments"
    if fragments.is_dir():
        for path in sorted(fragments.glob("*.json")):
            result = _load(path)
            if result.get("cell_id") in cell_map:
                results[str(result["cell_id"])] = result
    captures = raw_root / "agent-captures"
    recovered: list[dict[str, Any]] = []
    if captures.is_dir():
        for path in sorted(captures.glob("*.json")):
            capture = _load(path)
            cell_id = capture.get("cell", {}).get("cell_id")
            if cell_id in cell_map and cell_id not in results:
                recovered.append(adaptive._finalize_agent(capture, raw_root))

    templates = adaptive.WorkspaceTemplates(raw_root / "workspace-state", tasks)
    templates.strategy = str(plan["workspace_strategy"])
    trace_log = EvaluationTraceLog(raw_root / "traces.jsonl")
    trace_log.replay()
    started = time.monotonic()

    def checkpoint() -> None:
        legacy._write_report(
            output, _report(plan, results, skips, provider_attempts, trace_log, started)
        )

    def add_result(result: dict[str, Any]) -> None:
        results[result["cell_id"]] = result
        legacy._append_trace(trace_log, result, tasks[result["task_id"]])

    # A crash may occur after the durable result fragment is written but before
    # its trace append. Re-appending every recovered result is idempotent and
    # closes that checkpoint boundary without another model call.
    for result in results.values():
        legacy._append_trace(trace_log, result, tasks[result["task_id"]])
    for result in recovered:
        add_result(result)
    if recovered:
        checkpoint()

    def execute(batch: Sequence[dict[str, Any]]) -> bool:
        pending = [item for item in batch if item["cell_id"] not in results]
        if not pending:
            return True
        batch_results = adaptive._execute_batch(
            pending,
            tasks=tasks,
            templates=templates,
            raw_root=raw_root,
            output_limit=8192,
            step_limit=None,
        )
        for result in batch_results:
            if result.get("provider_failure"):
                provider_attempts.append(
                    {
                        "cell_id": result["cell_id"],
                        "provider_failure": result["provider_failure"],
                        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    }
                )
                checkpoint()
                return False
            add_result(result)
        checkpoint()
        return True

    base_cells = [item for item in cells if item["arm"] in BASE_ARMS]
    for index in range(0, len(base_cells), 3):
        if not execute(base_cells[index : index + 3]):
            return

    active_by_task: dict[str, list[dict[str, Any]]] = {}
    for task_id in plan["held_out_tasks"]:
        active_by_task[task_id] = sorted(
            [
                results[item["cell_id"]]
                for item in cells
                if item["arm"] == "active"
                and item["task_id"] == task_id
                and item["cell_id"] in results
            ],
            key=lambda item: int(item["repetition"]),
        )

    for capability in plan["candidates"]:
        for task_id in plan["held_out_tasks"]:
            ablations = [
                item
                for item in cells
                if item["arm"] == f"ablation:{capability}" and item["task_id"] == task_id
            ]
            active = active_by_task[task_id]
            if any(item["cell_id"] in results for item in ablations):
                if not execute(ablations):
                    return
                continue
            if len(active) != 3 or any(item["outcome"] != "PASS" for item in active):
                reason = "NOT_TESTED_ACTIVE_NOT_PASS"
            elif all(capability in item.get("pi_capabilities_used", ()) for item in active):
                if not execute(ablations):
                    return
                continue
            elif any(capability in item.get("pi_capabilities_used", ()) for item in active):
                reason = "NOT_TESTED_INCONSISTENT_ACTIVE_USE"
            else:
                reason = "NOT_TESTED_NO_ACTIVE_USE"
            for item in ablations:
                skips[item["cell_id"]] = {
                    "cell_id": item["cell_id"],
                    "arm": item["arm"],
                    "task_id": item["task_id"],
                    "repetition": item["repetition"],
                    "reason": reason,
                    "avoids_llm_call": True,
                }
            checkpoint()
    checkpoint()


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    plan_parser = sub.add_parser("plan")
    plan_parser.add_argument("--output", type=Path, required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--plan", type=Path, required=True)
    run_parser.add_argument("--raw-root", type=Path, required=True)
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "plan":
            create_plan(args.output)
        else:
            run(args.plan, args.raw_root, args.output, resume=args.resume)
    except (ConfirmationError, legacy.EvaluationError, adaptive.AdaptiveError) as error:
        print(str(error), file=__import__("sys").stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
