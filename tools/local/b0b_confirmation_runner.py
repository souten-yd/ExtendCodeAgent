#!/usr/bin/env python3
"""Held-out, local-practical-only B0b causal confirmation runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from extendcodeagent.evaluation import EvaluationTraceLog
from extendcodeagent.evaluation.causal import (
    auto_forced_diagnosis,
    paired_causal_assessment,
    selection_assessment,
)
from tools.local import adaptive_screening_runner as adaptive
from tools.local import causal_correction_runner as correction
from tools.local import evaluation_runner as legacy

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CAUSAL_EVIDENCE = ROOT / "docs/evidence/final/b0a-causal-correction-result-v1.json"
LOCAL_MODEL = "local-practical"
REPETITIONS = 3
EFFECT_PASS_DELTA = 2


class B0bConfirmationError(RuntimeError):
    """B0b confirmation cannot produce attributable held-out evidence."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise B0bConfirmationError(f"cannot read {path}: {error}") from error
    if not isinstance(value, dict):
        raise B0bConfirmationError(f"{path} root must be an object")
    return value


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
        "cell_id": f"b0b--{arm}--{LOCAL_MODEL}--{task['id']}--r{repetition}",
        "arm": arm,
        "model_tier": LOCAL_MODEL,
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
        "pi_confirmation": True,
        "pi_use_policy": "forced_ablation" if capability else use_policy,
        "ablation_capability": capability,
        "causal_correction": False,
    }


def _candidate_union(causal_evidence: dict[str, Any]) -> list[str]:
    policy = causal_evidence.get("candidate_policy", {})
    candidates = policy.get("b0b_candidate_union")
    if not isinstance(candidates, list) or not candidates:
        raise B0bConfirmationError("causal evidence has no B0b candidate union")
    unknown = set(candidates) - set(legacy.CONFIGURABLE_CAPABILITIES)
    if unknown:
        raise B0bConfirmationError(f"unknown B0b candidates: {sorted(unknown)}")
    return sorted(set(str(item) for item in candidates))


def create_plan(causal_evidence_path: Path, output: Path) -> None:
    legacy.validate()
    causal_evidence = _load(causal_evidence_path)
    legacy._verify_seal(causal_evidence, "B0a causal correction evidence")
    if causal_evidence.get("classification") != "B0A_CAUSAL_CAPABILITY_CORRECTION_COMPLETE":
        raise B0bConfirmationError("B0b requires completed causal-correction evidence")
    if causal_evidence.get("execution_scope") != "local-only":
        raise B0bConfirmationError("B0b input must be local-only evidence")

    matrix = _load(legacy.MATRIX)
    suite = _load(legacy.TASK_SUITE)
    expected_plan, entries = correction._plan_entries()
    quality = _load(legacy.B0A_QUALITY_TARGET)
    screening = _load(legacy.B0A_PLAN)
    for artifact, label in (
        (matrix, "matrix"),
        (suite, "task suite"),
        (quality, "quality target"),
        (screening, "screening plan"),
    ):
        legacy._verify_seal(artifact, label)
    if quality.get("quality_models") != [LOCAL_MODEL]:
        raise B0bConfirmationError("B0b quality target is not local-practical-only")
    local_tier = next(item for item in matrix["model_tiers"] if item["id"] == LOCAL_MODEL)
    if int(local_tier["minimum_repetitions"]) != REPETITIONS:
        raise B0bConfirmationError("local-practical repetition contract drifted")
    threshold = screening["screening"]["effect_threshold"]
    if (
        threshold["primary"]
        != "at least 2 more objective PASS outcomes for active than ablation(X)"
    ):
        raise B0bConfirmationError("effect threshold wording drifted")
    if float(threshold["minimum_absolute_pass_rate_delta"]) != 2 / 21:
        raise B0bConfirmationError("effect threshold value drifted")

    candidates = _candidate_union(causal_evidence)
    tasks = {item["id"]: item for item in suite["tasks"]}
    held_out = sorted(
        (item for item in expected_plan["tasks"] if tasks[item["task_id"]]["split"] == "held-out"),
        key=lambda item: item["task_id"],
    )
    coverage = {
        capability: sorted(
            item["task_id"] for item in held_out if capability in item["expected_capabilities"]
        )
        for capability in candidates
    }
    covered = {capability: task_ids for capability, task_ids in coverage.items() if task_ids}
    uncovered = {
        capability: "NO_HELD_OUT_TASK_COVERAGE"
        for capability, task_ids in coverage.items()
        if not task_ids
    }
    eligible_tasks = sorted({task_id for task_ids in covered.values() for task_id in task_ids})
    cells: list[dict[str, Any]] = []
    for repetition in range(1, REPETITIONS + 1):
        for task_id in eligible_tasks:
            task = tasks[task_id]
            cells.extend(
                [
                    _cell("auto_pi", task, repetition),
                    _cell("forced_pi", task, repetition),
                    _cell("forced_off", task, repetition),
                ]
            )
        for capability, task_ids in covered.items():
            for task_id in task_ids:
                cells.append(_cell("forced_ablation", tasks[task_id], repetition, capability))
    if len(cells) != 57 or len({item["cell_id"] for item in cells}) != 57:
        raise B0bConfirmationError("B0b schedule drifted from the bounded 57-cell contract")

    plan = adaptive._sealed(
        {
            "schema": 1,
            "classification": "B0B_HELD_OUT_CONFIRMATION_EXECUTION_PLAN",
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "source_revision": _head(),
            "execution_scope": "local-only",
            "model": "Qwen3.6 27B",
            "endpoint": "127.0.0.1:8090",
            "context": 262144,
            "output_limit": 8192,
            "claim_scope": "active-scoped(local-practical)",
            "causal_evidence": str(causal_evidence_path),
            "causal_evidence_sha256": _sha256(causal_evidence_path),
            "causal_evidence_seal": causal_evidence["seal"]["canonical_payload"],
            "evaluation_pi_plan_seal": expected_plan["seal"]["canonical_payload"],
            "task_suite_seal": suite["seal"]["canonical_payload"],
            "matrix_seal": matrix["seal"]["canonical_payload"],
            "quality_target_seal": quality["seal"]["canonical_payload"],
            "screening_plan_seal": screening["seal"]["canonical_payload"],
            "tasks_changed": False,
            "oracle_changed": False,
            "corpus_changed": False,
            "effect_threshold_changed": False,
            "capability_design_changed": False,
            "repetitions": REPETITIONS,
            "effect_threshold_pass_delta": EFFECT_PASS_DELTA,
            "critical_override": threshold["critical_override"],
            "candidate_union": candidates,
            "capability_task_coverage": coverage,
            "covered_capabilities": sorted(covered),
            "no_held_out_task_coverage": uncovered,
            "eligible_tasks": eligible_tasks,
            "excluded_held_out_tasks": sorted(
                set(item["task_id"] for item in held_out) - set(eligible_tasks)
            ),
            "cell_count": len(cells),
            "model_parallelism": 1,
            "workspace_strategy": "git_worktree",
            "persistent_opencode_adopted": False,
            "reuse_policy": "same-head result fragments and captures only",
            "task_plan_fingerprints": {
                task_id: hashlib.sha256(
                    json.dumps(
                        entries[task_id]["tool_requests"],
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode()
                ).hexdigest()
                for task_id in eligible_tasks
            },
            "minimum_depth_by_task": {
                task_id: entries[task_id]["minimum_depth"] for task_id in eligible_tasks
            },
            "cells": cells,
        }
    )
    legacy._write_report(output, plan)


def _verify_plan(plan: dict[str, Any]) -> None:
    legacy._verify_seal(plan, "B0b execution plan")
    if plan.get("classification") != "B0B_HELD_OUT_CONFIRMATION_EXECUTION_PLAN":
        raise B0bConfirmationError("unsupported B0b confirmation plan")
    if plan.get("source_revision") != _head():
        raise B0bConfirmationError("B0b plan must match exact execution HEAD")
    if plan.get("execution_scope") != "local-only" or plan.get("cell_count") != 57:
        raise B0bConfirmationError("B0b local-only cell contract drifted")
    cells = plan.get("cells", ())
    if (
        len(cells) != 57
        or len({item.get("cell_id") for item in cells}) != 57
        or any(item.get("model_tier") != LOCAL_MODEL for item in cells)
        or any(item.get("split") != "held-out" for item in cells)
    ):
        raise B0bConfirmationError("B0b cells violate the sealed local held-out contract")
    path = Path(plan["causal_evidence"])
    if _sha256(path) != plan["causal_evidence_sha256"]:
        raise B0bConfirmationError("causal evidence changed after plan creation")
    evidence = _load(path)
    legacy._verify_seal(evidence, "B0a causal correction evidence")
    if evidence["seal"]["canonical_payload"] != plan["causal_evidence_seal"]:
        raise B0bConfirmationError("causal evidence seal mismatch")
    expected, _ = correction._plan_entries()
    if plan["evaluation_pi_plan_seal"] != expected["seal"]["canonical_payload"]:
        raise B0bConfirmationError("B0b plan uses a stale EvaluationPIPlan")
    current_artifacts = (
        ("task_suite_seal", legacy.TASK_SUITE, "task suite"),
        ("matrix_seal", legacy.MATRIX, "matrix"),
        ("quality_target_seal", legacy.B0A_QUALITY_TARGET, "quality target"),
        ("screening_plan_seal", legacy.B0A_PLAN, "screening plan"),
    )
    for field, artifact_path, label in current_artifacts:
        artifact = _load(artifact_path)
        legacy._verify_seal(artifact, label)
        if plan[field] != artifact["seal"]["canonical_payload"]:
            raise B0bConfirmationError(f"B0b plan uses a stale {label}")


def _valid_pair(on: dict[str, Any], off: dict[str, Any]) -> dict[str, Any]:
    return paired_causal_assessment(on, off)


def _aggregate_pairs(
    pairs: list[dict[str, Any]], *, expected_pairs: int | None = None
) -> dict[str, Any]:
    invalid = [
        item
        for item in pairs
        if item["assessment"]["classification"]
        in {"FORCED_USE_COMPLIANCE_FAILURE", "FORCED_PLAN_INPUT_MISMATCH", "PI_TOOL_API_GAP"}
    ]
    unavailable = [
        item
        for item in pairs
        if item["on_outcome"] in {"UNAVAILABLE", "TIMEOUT"}
        or item["off_outcome"] in {"UNAVAILABLE", "TIMEOUT"}
    ]
    on_pass = sum(item["on_outcome"] == "PASS" for item in pairs)
    off_pass = sum(item["off_outcome"] == "PASS" for item in pairs)
    critical = any(
        item["on_outcome"] == "PASS"
        and item["off_outcome"] != "PASS"
        and item["task_class"] in {"negative-control", "unsafe-or-insufficient-evidence"}
        for item in pairs
    )
    if expected_pairs is not None and len(pairs) < expected_pairs:
        decision = "NOT_TESTED_INCOMPLETE"
    elif invalid:
        decision = "NOT_TESTED_FORCED_USE_COMPLIANCE_FAILURE"
    elif unavailable:
        decision = "NOT_TESTED_PROVIDER_OR_TIMEOUT_GAP"
    elif on_pass - off_pass >= EFFECT_PASS_DELTA or critical:
        decision = "CONFIRMED_CAUSAL_EFFECT_PENDING_LAYER_C_BUDGET"
    else:
        decision = "NO_CONFIRMED_CAUSAL_EFFECT"
    return {
        "decision": decision,
        "paired_cells": len(pairs),
        "expected_pairs": expected_pairs,
        "on_pass": on_pass,
        "off_pass": off_pass,
        "pass_delta": on_pass - off_pass,
        "effect_threshold_pass_delta": EFFECT_PASS_DELTA,
        "critical_override": critical,
        "invalid_pairs": len(invalid),
        "unavailable_pairs": len(unavailable),
        "pairs": pairs,
    }


def _pair_result(
    on: dict[str, Any], off: dict[str, Any], capability: str | None = None
) -> dict[str, Any]:
    return {
        "task_id": on["task_id"],
        "task_class": on["task_class"],
        "repetition": on["repetition"],
        "capability": capability,
        "on_cell_id": on["cell_id"],
        "off_cell_id": off["cell_id"],
        "on_outcome": on["outcome"],
        "off_outcome": off["outcome"],
        "assessment": _valid_pair(on, off),
    }


def _report(
    plan: dict[str, Any],
    results: dict[str, dict[str, Any]],
    provider_attempts: list[dict[str, Any]],
    trace_log: EvaluationTraceLog,
    started: float,
) -> dict[str, Any]:
    complete = len(results) == len(plan["cells"]) and not any(
        item["cell_id"] not in results for item in provider_attempts
    )
    forced_by_task_rep = {
        (item["task_id"], item["repetition"]): item
        for item in results.values()
        if item.get("pi_use_policy") == "forced_pi"
    }
    off_by_task_rep = {
        (item["task_id"], item["repetition"]): item
        for item in results.values()
        if item.get("pi_use_policy") == "forced_off"
    }
    intrinsic_pairs = [
        _pair_result(forced, off_by_task_rep[key])
        for key, forced in forced_by_task_rep.items()
        if key in off_by_task_rep
    ]
    intrinsic = {
        task_id: _aggregate_pairs(
            [item for item in intrinsic_pairs if item["task_id"] == task_id],
            expected_pairs=REPETITIONS,
        )
        for task_id in plan["eligible_tasks"]
    }
    capability_results: dict[str, Any] = {}
    for capability in plan["candidate_union"]:
        task_ids = plan["capability_task_coverage"][capability]
        if not task_ids:
            capability_results[capability] = {
                "decision": "NO_HELD_OUT_TASK_COVERAGE",
                "paired_cells": 0,
            }
            continue
        pairs: list[dict[str, Any]] = []
        for result in results.values():
            if (
                result.get("pi_use_policy") != "forced_ablation"
                or result.get("ablation_capability") != capability
            ):
                continue
            key = (result["task_id"], result["repetition"])
            if key in forced_by_task_rep:
                pairs.append(_pair_result(forced_by_task_rep[key], result, capability))
        capability_results[capability] = _aggregate_pairs(
            pairs, expected_pairs=len(task_ids) * REPETITIONS
        )

    expected_plan, entries = correction._plan_entries()
    del expected_plan
    selections: list[dict[str, Any]] = []
    diagnoses: list[dict[str, Any]] = []
    for item in results.values():
        if item.get("pi_use_policy") != "auto_pi":
            continue
        assessment = selection_assessment(
            entries[item["task_id"]], item.get("pi_tools", ()), item.get("pi_capabilities_used", ())
        )
        selections.append(
            {"task_id": item["task_id"], "repetition": item["repetition"], **assessment}
        )
        forced = forced_by_task_rep.get((item["task_id"], item["repetition"]))
        if forced is not None:
            diagnoses.append(
                {
                    "task_id": item["task_id"],
                    "repetition": item["repetition"],
                    "diagnosis": auto_forced_diagnosis(item, forced),
                }
            )
    compliance = [
        item.get("forced_use_compliance", {})
        for item in results.values()
        if item.get("pi_use_policy") in {"forced_pi", "forced_off", "forced_ablation"}
    ]
    selection_metrics = {
        "measured_cells": len(selections),
        "mean_capability_selection_precision": round(
            mean(item["capability_selection_precision"] for item in selections), 6
        )
        if selections
        else None,
        "mean_capability_selection_recall": round(
            mean(item["capability_selection_recall"] for item in selections), 6
        )
        if selections
        else None,
        "mean_under_selection_rate": round(
            mean(item["under_selection_rate"] for item in selections), 6
        )
        if selections
        else None,
        "mean_over_selection_rate": round(
            mean(item["over_selection_rate"] for item in selections), 6
        )
        if selections
        else None,
        "expected_but_not_used_states": sum(
            state == "EXPECTED_BUT_NOT_USED"
            for item in selections
            for state in item["states"].values()
        ),
    }
    context_tokens = [int(item.get("input_tokens") or 0) for item in results.values()]
    body = {
        "schema": 1,
        "classification": "B0B_HELD_OUT_CONFIRMATION_COMPLETE"
        if complete
        else "B0B_HELD_OUT_CONFIRMATION_IN_PROGRESS",
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "source_revision": _head(),
        "execution_plan": plan["seal"]["canonical_payload"],
        "execution_scope": "local-only",
        "model": "Qwen3.6 27B",
        "endpoint": "127.0.0.1:8090",
        "context": 262144,
        "output_limit": 8192,
        "claim_scope": "active-scoped(local-practical)",
        "results": list(results.values()),
        "outcomes": dict(Counter(item["outcome"] for item in results.values())),
        "provider_attempts": provider_attempts,
        "provider_gap_pending": any(item["cell_id"] not in results for item in provider_attempts),
        "cells_expected": len(plan["cells"]),
        "cells_accounted": len(results),
        "forced_cells": len(compliance),
        "forced_use_compliant": sum(item.get("compliant") is True for item in compliance),
        "forced_use_noncompliant": sum(item.get("compliant") is not True for item in compliance),
        "intrinsic_pi_results": intrinsic,
        "capability_confirmation_results": capability_results,
        "selection_evidence": selections,
        "selection_metrics": selection_metrics,
        "auto_forced_diagnoses": diagnoses,
        "no_held_out_task_coverage": plan["no_held_out_task_coverage"],
        "promotion_or_demotion_decision": False,
        "promotion_gate": "PENDING_LAYER_C_BUDGET",
        "efficiency": {
            "llm_calls_requested": len(plan["cells"]),
            "llm_calls_executed": len(results) + len(provider_attempts),
            "llm_calls_reused": 0,
            "llm_calls_avoided": 0,
            "avoided_call_ratio": 0.0,
            "input_tokens": sum(int(item.get("input_tokens") or 0) for item in results.values()),
            "output_tokens": sum(int(item.get("output_tokens") or 0) for item in results.values()),
            "reasoning_tokens": sum(
                int(item.get("reasoning_tokens") or 0) for item in results.values()
            ),
            "model_wall_time_ms": sum(
                float(item.get("model_wall_ms") or 0) for item in results.values()
            ),
            "deterministic_pi_wall_time_ms": sum(
                sum(float(value) for value in (item.get("pi_timing_ms") or {}).values())
                for item in results.values()
            ),
            "sidecar_cleanup_wall_time_ms": sum(
                float(item.get("sidecar_cleanup_wall_ms") or 0) for item in results.values()
            ),
            "evaluation_sidecars_terminated": sum(
                int(item.get("evaluation_sidecars_terminated") or 0) for item in results.values()
            ),
            "checkpoint_session_wall_time_ms": round((time.monotonic() - started) * 1000, 3),
            "total_wall_time_ms": round((time.monotonic() - started) * 1000, 3),
            "average_context_tokens": round(mean(context_tokens), 3) if context_tokens else 0,
            "max_context_tokens": max(context_tokens, default=0),
            "deterministic_resolution_ratio": 0.0,
            "escalation_rate": 1.0 if results else 0.0,
            "minimum_sufficient_depth": plan["minimum_depth_by_task"],
            "reused_evidence_count": 0,
            "invalidated_evidence_count": 0,
        },
        "trace_log": str(trace_log.path),
    }
    return adaptive._sealed(body)


def run(plan_path: Path, raw_root: Path, output: Path, *, resume: bool) -> None:
    legacy._require_clean_worktree()
    plan = _load(plan_path)
    _verify_plan(plan)
    if output.exists() and not resume:
        raise B0bConfirmationError("B0b output exists; use --resume")
    raw_root.mkdir(parents=True, exist_ok=True)
    tasks = {item["id"]: item for item in _load(legacy.TASK_SUITE)["tasks"]}
    cell_map = {item["cell_id"]: item for item in plan["cells"]}
    results: dict[str, dict[str, Any]] = {}
    provider_attempts: list[dict[str, Any]] = []
    if resume and output.is_file():
        previous = _load(output)
        if previous.get("execution_plan") != plan["seal"]["canonical_payload"]:
            raise B0bConfirmationError("resume output uses another B0b plan")
        results.update({item["cell_id"]: item for item in previous.get("results", ())})
        provider_attempts.extend(previous.get("provider_attempts", ()))
    fragment_root = raw_root / "result-fragments"
    if fragment_root.is_dir():
        for path in sorted(fragment_root.glob("*.json")):
            result = _load(path)
            cell_id = result.get("cell_id")
            if isinstance(cell_id, str) and cell_id in cell_map and cell_id not in results:
                results[cell_id] = result
    capture_root = raw_root / "agent-captures"
    if capture_root.is_dir():
        for path in sorted(capture_root.glob("*.json")):
            capture = _load(path)
            cell_id = capture.get("cell", {}).get("cell_id")
            if isinstance(cell_id, str) and cell_id in cell_map and cell_id not in results:
                result = adaptive._finalize_agent(capture, raw_root)
                results[result["cell_id"]] = result
    unexpected_results = sorted(set(results) - set(cell_map))
    if unexpected_results:
        raise B0bConfirmationError(
            f"resume output contains cells outside the B0b plan: {unexpected_results}"
        )

    templates = adaptive.WorkspaceTemplates(raw_root / "workspace-state", tasks)
    templates.strategy = "git_worktree"
    trace_log = EvaluationTraceLog(raw_root / "traces.jsonl")
    correction._append_missing_traces(trace_log, results, tasks)
    started = time.monotonic()

    def checkpoint() -> None:
        legacy._write_report(output, _report(plan, results, provider_attempts, trace_log, started))

    for cell in plan["cells"]:
        if cell["cell_id"] in results:
            continue
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
            return
        results[result["cell_id"]] = result
        legacy._append_trace(trace_log, result, tasks[result["task_id"]])
        checkpoint()
    checkpoint()


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    plan_parser = sub.add_parser("plan")
    plan_parser.add_argument("--causal-evidence", type=Path, default=DEFAULT_CAUSAL_EVIDENCE)
    plan_parser.add_argument("--output", type=Path, required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--plan", type=Path, required=True)
    run_parser.add_argument("--raw-root", type=Path, required=True)
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "plan":
            create_plan(args.causal_evidence, args.output)
        else:
            run(args.plan, args.raw_root, args.output, resume=args.resume)
    except (
        B0bConfirmationError,
        correction.CausalCorrectionError,
        legacy.EvaluationError,
        adaptive.AdaptiveError,
    ) as error:
        print(str(error), file=__import__("sys").stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
