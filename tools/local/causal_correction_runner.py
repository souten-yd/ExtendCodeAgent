#!/usr/bin/env python3
"""Small forced-use causal correction gate before B0b confirmation."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from collections import Counter
from pathlib import Path
from typing import Any

from extendcodeagent.evaluation import EvaluationTraceLog
from extendcodeagent.evaluation.causal import (
    auto_forced_diagnosis,
    intrinsic_pi_assessment,
    paired_causal_assessment,
    selection_assessment,
    validate_evaluation_pi_plan,
)
from tools.local import adaptive_screening_runner as adaptive
from tools.local import evaluation_runner as legacy

ROOT = Path(__file__).resolve().parents[2]


class CausalCorrectionError(RuntimeError):
    """The corrective gate cannot produce attributable evidence."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CausalCorrectionError(f"cannot read {path}: {error}") from error
    if not isinstance(value, dict):
        raise CausalCorrectionError(f"{path} root must be an object")
    return value


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _plan_entries() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    plan = _load(legacy.EVALUATION_PI_PLAN)
    legacy._verify_seal(plan, "EvaluationPIPlan")
    suite = _load(legacy.TASK_SUITE)
    validate_evaluation_pi_plan(plan, suite, legacy.CONFIGURABLE_CAPABILITIES)
    return plan, {item["task_id"]: item for item in plan["tasks"]}


def _cell(
    use_policy: str,
    task: dict[str, Any],
    repetition: int,
    capability: str | None = None,
) -> dict[str, Any]:
    arm = (
        "off"
        if use_policy == "forced_off"
        else use_policy
        if capability is None
        else f"forced_ablation:{capability}"
    )
    return {
        "cell_id": f"causal--{arm}--local-practical--{task['id']}--r{repetition}",
        "arm": arm,
        "model_tier": "local-practical",
        "model_id": "eca-local-practical/llama",
        "model_status": "AVAILABLE",
        "repository_id": task["repository_id"],
        "task_id": task["id"],
        "task_class": task["task_class"],
        "split": task["split"],
        "repetition": repetition,
        "pi_activation_gate": False,
        "pi_effect_pilot": False,
        "pi_screening": False,
        "pi_confirmation": False,
        "pi_use_policy": "forced_ablation" if capability else use_policy,
        "ablation_capability": capability,
        "causal_correction": True,
    }


def create_plan(observational_report_path: Path, pilot_report_path: Path, output: Path) -> None:
    legacy.validate()
    expected_plan, entries = _plan_entries()
    suite = _load(legacy.TASK_SUITE)
    tasks = {item["id"]: item for item in suite["tasks"]}
    correction = expected_plan["causal_correction"]
    representatives = correction["representative_tasks"]
    representative_tasks = sorted(set(representatives.values()))
    observational = _load(observational_report_path)
    pilot = _load(pilot_report_path)
    compatible, changed = adaptive._product_semantics_compatible(
        str(observational["source_revision"])
    )
    if not compatible:
        raise CausalCorrectionError(
            f"observational auto-use evidence needs replay after product changes: {changed}"
        )
    active_r1 = {
        item["task_id"]: item
        for item in observational.get("results", ())
        if item.get("arm") == "active" and item.get("repetition") == 1
    }
    reusable_auto = sorted(set(representative_tasks) & set(active_r1))
    missing_auto = sorted(set(representative_tasks) - set(reusable_auto))
    auto_cells = [_cell("auto_pi", tasks[task_id], 1) for task_id in missing_auto]
    forced_cells: list[dict[str, Any]] = []
    for repetition in (1, 2, 3):
        for task_id in representative_tasks:
            forced_cells.append(_cell("forced_pi", tasks[task_id], repetition))
            if repetition == 1:
                forced_cells.append(_cell("forced_off", tasks[task_id], repetition))
        for capability, task_id in representatives.items():
            forced_cells.append(_cell("forced_ablation", tasks[task_id], repetition, capability))
    if len(forced_cells) != 57 or len(auto_cells) > len(representative_tasks):
        raise CausalCorrectionError("corrective schedule size drifted from the sealed bounded plan")
    pilot_forced_candidates = [
        item
        for item in pilot.get("results", ())
        if item.get("arm") == "active"
        and item.get("task_id")
        in {
            "eca-symbol-001",
            "eca-impact-001",
            "eca-tests-001",
        }
    ]
    result = adaptive._sealed(
        {
            "schema": 1,
            "classification": "CAUSAL_CAPABILITY_CORRECTION_EXECUTION_PLAN",
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "source_revision": _head(),
            "execution_scope": "local-only",
            "model": "Qwen3.6 27B",
            "endpoint": "127.0.0.1:8090",
            "context": 262144,
            "output_limit": 8192,
            "evaluation_pi_plan_seal": expected_plan["seal"]["canonical_payload"],
            "task_suite_seal": suite["seal"]["canonical_payload"],
            "matrix_seal": _load(legacy.MATRIX)["seal"]["canonical_payload"],
            "quality_target_seal": _load(legacy.B0A_QUALITY_TARGET)["seal"]["canonical_payload"],
            "observational_report": str(observational_report_path),
            "observational_report_sha256": _sha256(observational_report_path),
            "pilot_report": str(pilot_report_path),
            "pilot_report_sha256": _sha256(pilot_report_path),
            "observational_auto_reuse_tasks": reusable_auto,
            "new_auto_tasks": missing_auto,
            "pilot_forced_audit": {
                "cells_considered": len(pilot_forced_candidates),
                "classification": "REPLAY_REQUIRED_INPUT_PROVENANCE_MISSING",
                "reason": (
                    "required tools were forced, but historical results do not retain exact "
                    "tool request inputs for ON/ablation equality"
                ),
            },
            "initial_new_calls": 23 + len(auto_cells),
            "maximum_new_calls": 57 + len(auto_cells),
            "forced_initial_calls": 23,
            "forced_maximum_calls": 57,
            "model_parallelism": 1,
            "workspace_strategy": "git_worktree",
            "step_limit": None,
            "auto_cells": auto_cells,
            "forced_cells": forced_cells,
            "existing_observational_candidates": correction["existing_observational_candidates"],
            "no_task_coverage": correction["no_task_coverage"],
            "representative_tasks": representatives,
            "task_plan_fingerprints": {
                task_id: hashlib.sha256(
                    json.dumps(
                        entries[task_id]["tool_requests"],
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode()
                ).hexdigest()
                for task_id in representative_tasks
            },
        }
    )
    legacy._write_report(output, result)


def _verify_plan(plan: dict[str, Any]) -> None:
    legacy._verify_seal(plan, "causal correction execution plan")
    if plan.get("classification") != "CAUSAL_CAPABILITY_CORRECTION_EXECUTION_PLAN":
        raise CausalCorrectionError("unsupported causal correction plan")
    if plan.get("source_revision") != _head():
        raise CausalCorrectionError("causal correction plan must match exact execution HEAD")
    expected, _ = _plan_entries()
    if plan.get("evaluation_pi_plan_seal") != expected["seal"]["canonical_payload"]:
        raise CausalCorrectionError("causal correction plan uses stale EvaluationPIPlan")
    for key in ("observational_report", "pilot_report"):
        path = Path(plan[key])
        if _sha256(path) != plan[f"{key}_sha256"]:
            raise CausalCorrectionError(f"{key} changed after plan creation")


def _pair_decision(
    plan: dict[str, Any], results: dict[str, dict[str, Any]], capability: str, repetition: int
) -> dict[str, Any] | None:
    task_id = plan["representative_tasks"][capability]
    on_id = f"causal--forced_pi--local-practical--{task_id}--r{repetition}"
    off_id = f"causal--forced_ablation:{capability}--local-practical--{task_id}--r{repetition}"
    if on_id not in results or off_id not in results:
        return None
    return paired_causal_assessment(results[on_id], results[off_id])


def _capability_state(
    plan: dict[str, Any], results: dict[str, dict[str, Any]], capability: str
) -> dict[str, Any]:
    pairs = [
        pair
        for repetition in (1, 2, 3)
        if (pair := _pair_decision(plan, results, capability, repetition)) is not None
    ]
    classes = [item["classification"] for item in pairs]
    if "POSITIVE_CAUSAL_SIGNAL" in classes:
        decision = "PROCEED_TO_B0B_CAUSAL"
    elif any(
        item
        in {
            "FORCED_USE_COMPLIANCE_FAILURE",
            "FORCED_PLAN_INPUT_MISMATCH",
            "PI_TOOL_API_GAP",
            "PI_CAPABILITY_GAP",
        }
        for item in classes
    ):
        decision = classes[-1]
    elif len(pairs) == 3:
        decision = "NO_CORRECTED_CAUSAL_SIGNAL"
    else:
        decision = "BOUNDARY_REQUIRES_NEXT_REPETITION"
    return {"decision": decision, "pairs": pairs}


def _selection_evidence(
    plan: dict[str, Any], results: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    expected, entries = _plan_entries()
    observational = _load(Path(plan["observational_report"]))
    active = {
        item["task_id"]: item
        for item in observational.get("results", ())
        if item.get("arm") == "active" and item.get("repetition") == 1
    }
    for result in results.values():
        if result.get("pi_use_policy") == "auto_pi":
            active[result["task_id"]] = result
    evidence: list[dict[str, Any]] = []
    for task in expected["tasks"]:
        task_id = task["task_id"]
        auto_result = active.get(task_id)
        if auto_result is None:
            evidence.append(
                {
                    "task_id": task_id,
                    "classification": "UNRESOLVED",
                    "states": {
                        capability: "UNRESOLVED" for capability in legacy.CONFIGURABLE_CAPABILITIES
                    },
                }
            )
            continue
        assessment = selection_assessment(
            entries[task_id],
            auto_result.get("pi_tools", ()),
            auto_result.get("pi_capabilities_used", ()),
        )
        evidence.append(
            {
                "task_id": task_id,
                "source": "new_auto_pi"
                if auto_result.get("pi_use_policy") == "auto_pi"
                else ("compatible_observational_b0a"),
                "outcome": auto_result.get("outcome"),
                **assessment,
            }
        )
    return evidence


def _report(
    plan: dict[str, Any],
    results: dict[str, dict[str, Any]],
    skips: dict[str, dict[str, Any]],
    provider_attempts: list[dict[str, Any]],
    trace_log: EvaluationTraceLog,
    started: float,
) -> dict[str, Any]:
    states = {
        capability: _capability_state(plan, results, capability)
        for capability in plan["representative_tasks"]
    }
    positives = sorted(
        capability
        for capability, state in states.items()
        if state["decision"] == "PROCEED_TO_B0B_CAUSAL"
    )
    candidate_union = sorted(set(plan["existing_observational_candidates"]) | set(positives))
    selections = _selection_evidence(plan, results)
    measured_selection = [item for item in selections if "capability_selection_recall" in item]
    forced_r1_by_task = {
        item["task_id"]: item
        for item in results.values()
        if item.get("pi_use_policy") == "forced_pi" and item.get("repetition") == 1
    }
    off_r1_by_task = {
        item["task_id"]: item
        for item in results.values()
        if item.get("pi_use_policy") == "forced_off" and item.get("repetition") == 1
    }
    auto_by_task = {
        item["task_id"]: item for item in results.values() if item.get("pi_use_policy") == "auto_pi"
    }
    observational = _load(Path(plan["observational_report"]))
    for item in observational.get("results", ()):
        if item.get("arm") == "active" and item.get("repetition") == 1:
            auto_by_task.setdefault(item["task_id"], item)
    diagnoses = {
        task_id: auto_forced_diagnosis(auto_by_task.get(task_id), forced)
        for task_id, forced in forced_r1_by_task.items()
    }
    total_cells = len(plan["auto_cells"]) + len(plan["forced_cells"])
    accounted = set(results) | set(skips)
    model_results = [
        item
        for item in results.values()
        if any(
            int(item.get(key) or 0) > 0
            for key in (
                "input_tokens",
                "output_tokens",
                "reasoning_tokens",
                "cache_read_tokens",
                "cache_write_tokens",
            )
        )
    ]
    reused_model_results = [
        item for item in model_results if item.get("result_origin") == "COMPATIBILITY_MIGRATION"
    ]
    new_model_results = [item for item in model_results if item not in reused_model_results]
    complete = len(accounted) == total_cells and not any(
        item.get("cell_id") not in results for item in provider_attempts
    )
    body = {
        "schema": 1,
        "classification": (
            "CAUSAL_CAPABILITY_CORRECTION_COMPLETE"
            if complete
            else "CAUSAL_CAPABILITY_CORRECTION_IN_PROGRESS"
        ),
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "source_revision": _head(),
        "execution_plan": plan["seal"]["canonical_payload"],
        "execution_scope": "local-only",
        "model": "Qwen3.6 27B",
        "endpoint": "127.0.0.1:8090",
        "context": 262144,
        "output_limit": 8192,
        "results": list(results.values()),
        "outcomes": dict(Counter(item["outcome"] for item in results.values())),
        "skips": list(skips.values()),
        "skip_counts": dict(Counter(item["reason"] for item in skips.values())),
        "provider_attempts": provider_attempts,
        "provider_gap_pending": any(
            item.get("cell_id") not in results for item in provider_attempts
        ),
        "unique_new_cells_accounted": len(accounted),
        "capability_causal_results": states,
        "existing_observational_candidates_preserved": plan["existing_observational_candidates"],
        "new_causal_candidates": positives,
        "b0b_candidate_union": candidate_union,
        "no_task_coverage": plan["no_task_coverage"],
        "selection_evidence": selections,
        "selection_metrics": {
            "measured_tasks": len(measured_selection),
            "capability_selection_precision": [
                item["capability_selection_precision"] for item in measured_selection
            ],
            "capability_selection_recall": [
                item["capability_selection_recall"] for item in measured_selection
            ],
            "under_selection_rate": [item["under_selection_rate"] for item in measured_selection],
            "over_selection_rate": [item["over_selection_rate"] for item in measured_selection],
        },
        "auto_forced_diagnoses": diagnoses,
        "intrinsic_pi_results": {
            task_id: intrinsic_pi_assessment(forced, off_r1_by_task[task_id])
            for task_id, forced in forced_r1_by_task.items()
            if task_id in off_r1_by_task
        },
        "pilot_forced_audit": plan["pilot_forced_audit"],
        "efficiency": {
            "llm_calls_requested": total_cells,
            "llm_calls_executed": len(new_model_results) + len(provider_attempts),
            "llm_calls_reused": len(reused_model_results),
            "llm_calls_not_executed_pre_model": len(results) - len(model_results),
            "llm_calls_avoided": len(skips),
            "avoided_call_ratio": round(len(skips) / total_cells, 6),
            "input_tokens": sum(int(item.get("input_tokens") or 0) for item in results.values()),
            "output_tokens": sum(int(item.get("output_tokens") or 0) for item in results.values()),
            "reasoning_tokens": sum(
                int(item.get("reasoning_tokens") or 0) for item in results.values()
            ),
            "model_wall_time_ms": sum(
                float(item.get("model_wall_ms") or 0) for item in new_model_results
            ),
            "reused_model_wall_time_ms": sum(
                float(item.get("model_wall_ms") or 0) for item in reused_model_results
            ),
            "checkpoint_session_wall_time_ms": round((time.monotonic() - started) * 1000, 3),
            "reused_auto_selection_evidence_count": len(plan["observational_auto_reuse_tasks"]),
            "reused_causal_evidence_count": sum(
                item.get("result_origin") == "COMPATIBILITY_MIGRATION" for item in results.values()
            ),
        },
        "trace_log": str(trace_log.path),
        "promotion_or_demotion_forbidden": True,
    }
    return adaptive._sealed(body)


def run(
    plan_path: Path,
    raw_root: Path,
    output: Path,
    *,
    resume: bool,
    capture_source_revision: str | None = None,
) -> None:
    legacy._require_clean_worktree()
    plan = _load(plan_path)
    _verify_plan(plan)
    if capture_source_revision is not None:
        compatible, changed = adaptive._product_semantics_compatible(capture_source_revision)
        if not compatible:
            raise CausalCorrectionError(
                f"capture reuse changes product semantics and requires replay: {changed}"
            )
    if output.exists() and not resume:
        raise CausalCorrectionError("causal correction output exists; use --resume")
    raw_root.mkdir(parents=True, exist_ok=True)
    tasks = {item["id"]: item for item in _load(legacy.TASK_SUITE)["tasks"]}
    all_cells = [*plan["auto_cells"], *plan["forced_cells"]]
    cell_map = {item["cell_id"]: item for item in all_cells}
    results: dict[str, dict[str, Any]] = {}
    skips: dict[str, dict[str, Any]] = {}
    provider_attempts: list[dict[str, Any]] = []
    if resume and output.is_file():
        previous = _load(output)
        if previous.get("execution_plan") != plan["seal"]["canonical_payload"]:
            raise CausalCorrectionError("resume output uses another causal correction plan")
        results.update({item["cell_id"]: item for item in previous.get("results", ())})
        skips.update({item["cell_id"]: item for item in previous.get("skips", ())})
        provider_attempts.extend(previous.get("provider_attempts", ()))
    fragment_root = raw_root / "result-fragments"
    if fragment_root.is_dir():
        for path in sorted(fragment_root.glob("*.json")):
            result = _load(path)
            if result.get("cell_id") in cell_map and result.get("cell_id") not in results:
                results[result["cell_id"]] = result
    capture_root = raw_root / "agent-captures"
    if capture_root.is_dir():
        for path in sorted(capture_root.glob("*.json")):
            capture = _load(path)
            cell_id = capture.get("cell", {}).get("cell_id")
            should_reclassify = capture_source_revision is not None and not resume
            if cell_id in cell_map and (cell_id not in results or should_reclassify):
                result = adaptive._finalize_agent(capture, raw_root)
                if should_reclassify:
                    assert capture_source_revision is not None
                    result = adaptive._migrated_result(result, capture_source_revision, _head())
                results[result["cell_id"]] = result

    templates = adaptive.WorkspaceTemplates(raw_root / "workspace-state", tasks)
    templates.strategy = "git_worktree"
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

    for result in results.values():
        legacy._append_trace(trace_log, result, tasks[result["task_id"]])

    def execute(cells: list[dict[str, Any]]) -> bool:
        pending = [item for item in cells if item["cell_id"] not in results]
        if not pending:
            return True
        for cell in pending:
            batch = adaptive._execute_batch(
                [cell],
                tasks=tasks,
                templates=templates,
                raw_root=raw_root,
                output_limit=8192,
                step_limit=None,
            )
            result = batch[0]
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

    if not execute(plan["auto_cells"]):
        return
    representatives = plan["representative_tasks"]
    for repetition in (1, 2, 3):
        if repetition == 1:
            capabilities = list(representatives)
        else:
            capabilities = [
                capability
                for capability in representatives
                if _capability_state(plan, results, capability)["decision"]
                == "BOUNDARY_REQUIRES_NEXT_REPETITION"
            ]
        needed_tasks = sorted({representatives[item] for item in capabilities})
        on_cells = [
            item
            for item in plan["forced_cells"]
            if item["pi_use_policy"] == "forced_pi"
            and item["repetition"] == repetition
            and item["task_id"] in needed_tasks
        ]
        off_control_cells = [
            item
            for item in plan["forced_cells"]
            if item["pi_use_policy"] == "forced_off" and item["repetition"] == repetition
        ]
        off_cells = [
            item
            for item in plan["forced_cells"]
            if item["pi_use_policy"] == "forced_ablation"
            and item["repetition"] == repetition
            and item["ablation_capability"] in capabilities
        ]
        if not execute([*on_cells, *off_control_cells, *off_cells]):
            return
        for item in plan["forced_cells"]:
            if item["repetition"] <= repetition or item["cell_id"] in results:
                continue
            capability = item.get("ablation_capability")
            if capability is None:
                continue
            state = _capability_state(plan, results, capability)["decision"]
            if state == "PROCEED_TO_B0B_CAUSAL":
                reason = "SKIPPED_CORRECTIVE_EARLY_POSITIVE"
            elif state != "BOUNDARY_REQUIRES_NEXT_REPETITION":
                reason = "SKIPPED_CORRECTIVE_DIAGNOSTIC"
            else:
                continue
            skips[item["cell_id"]] = {
                "cell_id": item["cell_id"],
                "arm": item["arm"],
                "task_id": item["task_id"],
                "reason": reason,
                "avoids_llm_call": True,
            }
        # A shared forced_pi cell is unnecessary when every capability for its
        # task has already stopped. Classify it after capability-specific stops.
        for item in plan["forced_cells"]:
            if (
                item["pi_use_policy"] != "forced_pi"
                or item["repetition"] <= repetition
                or item["cell_id"] in results
            ):
                continue
            task_capabilities = [
                capability
                for capability, task_id in representatives.items()
                if task_id == item["task_id"]
            ]
            if all(
                _capability_state(plan, results, capability)["decision"]
                != "BOUNDARY_REQUIRES_NEXT_REPETITION"
                for capability in task_capabilities
            ):
                skips[item["cell_id"]] = {
                    "cell_id": item["cell_id"],
                    "arm": item["arm"],
                    "task_id": item["task_id"],
                    "reason": "SKIPPED_NO_REMAINING_CAUSAL_BOUNDARY",
                    "avoids_llm_call": True,
                }
        checkpoint()
    checkpoint()


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    plan_parser = sub.add_parser("plan")
    plan_parser.add_argument("--observational-report", type=Path, required=True)
    plan_parser.add_argument("--pilot-report", type=Path, required=True)
    plan_parser.add_argument("--output", type=Path, required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--plan", type=Path, required=True)
    run_parser.add_argument("--raw-root", type=Path, required=True)
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--resume", action="store_true")
    run_parser.add_argument("--capture-source-revision")
    args = parser.parse_args()
    try:
        if args.command == "plan":
            create_plan(args.observational_report, args.pilot_report, args.output)
        else:
            run(
                args.plan,
                args.raw_root,
                args.output,
                resume=args.resume,
                capture_source_revision=args.capture_source_revision,
            )
    except (CausalCorrectionError, legacy.EvaluationError, adaptive.AdaptiveError) as error:
        print(str(error), file=__import__("sys").stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
