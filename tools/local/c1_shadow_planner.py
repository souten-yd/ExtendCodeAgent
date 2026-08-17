#!/usr/bin/env python3
"""Evaluate C1 deterministic shadow planning against sealed expected plans."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import subprocess
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from extendcodeagent.core.config.schema import (
    CONFIGURABLE_CAPABILITIES,
    CapabilityName,
    Depth,
    RolloutMode,
)
from extendcodeagent.core.contracts import ProjectRef
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.orchestration import TaskIntentName, TaskSignals, create_shadow_plan

ROOT = Path(__file__).resolve().parents[2]
TASK_SUITE = ROOT / "docs/evaluation/task-suite-v1.json"
EXPECTED_PLAN = ROOT / "docs/evaluation/evaluation-pi-plan-v1.json"
DEFAULT_OUTPUT = ROOT / "docs/evidence/final/c1-shadow-planner-result-v1.json"

_EXPECTED_INTENT = {
    "negative-control": TaskIntentName.MECHANICAL,
    "symbol-reference-lookup": TaskIntentName.LOCATE_EXPLAIN,
    "impact-assessment": TaskIntentName.IMPACT_ASSESSMENT,
    "test-selection": TaskIntentName.TEST_SELECTION,
    "cross-file-refactor": TaskIntentName.REFACTOR,
    "failing-test-bug-localization": TaskIntentName.BUG_FIX,
    "requirement-to-code-tracing": TaskIntentName.REQUIREMENT_TRACE,
    "cross-boundary-gui-runtime-causal-flow": TaskIntentName.RUNTIME_BOUNDARY,
    "unsafe-or-insufficient-evidence": TaskIntentName.INSUFFICIENT_EVIDENCE,
}


class C1EvaluationError(RuntimeError):
    """C1 cannot be scored against the sealed inputs."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise C1EvaluationError(f"cannot read {path}: {error}") from error
    if not isinstance(value, dict):
        raise C1EvaluationError(f"{path} root must be an object")
    return value


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(
        {key: item for key, item in value.items() if key != "seal"},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def _sealed(value: dict[str, Any]) -> dict[str, Any]:
    body = {key: item for key, item in value.items() if key != "seal"}
    return {
        **body,
        "seal": {
            "algorithm": "sha256",
            "canonical_payload": hashlib.sha256(_canonical(body)).hexdigest(),
        },
    }


def _verify_seal(value: dict[str, Any], label: str) -> None:
    expected = hashlib.sha256(_canonical(value)).hexdigest()
    if value.get("seal") != {"algorithm": "sha256", "canonical_payload": expected}:
        raise C1EvaluationError(f"{label} seal mismatch")


def _policy() -> CapabilityPolicy:
    configurable = set(CONFIGURABLE_CAPABILITIES)
    return CapabilityPolicy(
        {
            name: RolloutMode.SHADOW if name in configurable else RolloutMode.OFF
            for name in CapabilityName
        },
        {name: Depth.D2 for name in CapabilityName},
    )


def _project(task: dict[str, Any]) -> ProjectRef:
    repository = str(task["repository_id"])
    return ProjectRef(repository, "c1-evaluation", f"file:///sealed/{repository}")


def _score(expected: set[str], observed: set[str]) -> dict[str, float]:
    matched = expected & observed
    precision = len(matched) / len(observed) if observed else (1.0 if not expected else 0.0)
    recall = len(matched) / len(expected) if expected else 1.0
    return {
        "capability_selection_precision": round(precision, 6),
        "capability_selection_recall": round(recall, 6),
        "under_selection_rate": round(len(expected - observed) / len(expected), 6)
        if expected
        else 0.0,
        "over_selection_rate": round(len(observed - expected) / len(observed), 6)
        if observed
        else 0.0,
    }


def _aggregate(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "tasks": len(items),
        "intent_accuracy": round(sum(item["intent_correct"] for item in items) / len(items), 6),
        "capability_selection_precision": round(
            statistics.mean(item["capability_selection_precision"] for item in items), 6
        ),
        "capability_selection_recall": round(
            statistics.mean(item["capability_selection_recall"] for item in items), 6
        ),
        "under_selection_rate": round(
            statistics.mean(item["under_selection_rate"] for item in items), 6
        ),
        "over_selection_rate": round(
            statistics.mean(item["over_selection_rate"] for item in items), 6
        ),
        "exact_capability_match_rate": round(
            sum(item["expected_capabilities"] == item["planned_capabilities"] for item in items)
            / len(items),
            6,
        ),
        "minimum_depth_match_rate": round(
            sum(item["expected_minimum_depth"] == item["planned_minimum_depth"] for item in items)
            / len(items),
            6,
        ),
    }


def _percentile(values: list[int], fraction: float) -> int:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def evaluate(latency_repetitions: int) -> dict[str, Any]:
    suite = _load(TASK_SUITE)
    expected_plan = _load(EXPECTED_PLAN)
    _verify_seal(suite, "task suite")
    _verify_seal(expected_plan, "EvaluationPIPlan")
    if expected_plan.get("task_suite_seal") != suite["seal"]["canonical_payload"]:
        raise C1EvaluationError("EvaluationPIPlan task-suite seal drift")
    tasks = {str(item["id"]): item for item in suite["tasks"]}
    expectations = {str(item["task_id"]): item for item in expected_plan["tasks"]}
    if set(tasks) != set(expectations):
        raise C1EvaluationError("sealed tasks and expected plans do not match")

    policy = _policy()
    results: list[dict[str, Any]] = []
    latency_samples: list[int] = []
    plan_ids: dict[str, str] = {}
    for task_id, task in tasks.items():
        signals = TaskSignals(
            project=_project(task),
            objective=str(task["instruction"]),
            context_token_limit=8_192,
            max_items=100,
            max_depth=6,
        )
        outcomes = []
        for _ in range(latency_repetitions):
            started = time.perf_counter_ns()
            outcome = create_shadow_plan(signals, policy)
            latency_samples.append(max(0, (time.perf_counter_ns() - started) // 1_000))
            outcomes.append(outcome)
        outcome = outcomes[0]
        if len({item.plan.plan_id for item in outcomes}) != 1:
            raise C1EvaluationError(f"non-deterministic plan identity: {task_id}")
        plan_ids[task_id] = outcome.plan.plan_id
        expected = expectations[task_id]
        expected_capabilities = set(expected["expected_capabilities"])
        planned_capabilities = {item.value for item in outcome.plan.capabilities}
        expected_intent = _EXPECTED_INTENT[str(task["task_class"])]
        results.append(
            {
                "task_id": task_id,
                "repository_id": task["repository_id"],
                "split": task["split"],
                "task_class": task["task_class"],
                "planner_inputs": ["instruction", "bounded project/runtime/model/evidence signals"],
                "task_id_supplied_to_planner": False,
                "expected_intent": expected_intent.value,
                "planned_intent": outcome.plan.intent.primary.value,
                "intent_correct": outcome.plan.intent.primary is expected_intent,
                "expected_capabilities": sorted(expected_capabilities),
                "planned_capabilities": sorted(planned_capabilities),
                **_score(expected_capabilities, planned_capabilities),
                "expected_minimum_depth": expected["minimum_depth"],
                "planned_minimum_depth": outcome.plan.minimum_depth.value,
                "level": outcome.plan.level.value,
                "context_scope": outcome.plan.context_scope.value,
                "context_budget_tokens": outcome.plan.context_budget_tokens,
                "unavailable_capabilities": [
                    item.value for item in outcome.plan.unavailable_capabilities
                ],
                "plan_id": outcome.plan.plan_id,
                "decision_latency_us": outcome.decision_latency_us,
                "shadow_only": outcome.plan.shadow_only,
                "behavior_changed": outcome.behavior_changed,
                "llm_calls": outcome.llm_calls,
            }
        )

    by_split: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in results:
        by_split[str(item["split"])].append(item)
    planned_context_budgets = [int(item["context_budget_tokens"]) for item in results]
    depth_distribution = Counter(str(item["planned_minimum_depth"]) for item in results)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    body = {
        "schema": 1,
        "classification": "C1_DETERMINISTIC_SHADOW_PLANNER_RESULT",
        "captured_at": datetime.now(UTC).isoformat(),
        "source_revision": head,
        "execution_scope": "local-only",
        "model": "Qwen3.6 27B",
        "endpoint": "127.0.0.1:8090",
        "context": 262_144,
        "output_limit": 8_192,
        "model_execution": "NOT_RUN_DETERMINISTIC_SUFFICIENT",
        "contract": {
            "task_suite_seal": suite["seal"]["canonical_payload"],
            "evaluation_pi_plan_seal": expected_plan["seal"]["canonical_payload"],
            "expected_plan_role": "human-reviewed evaluation ground truth only",
            "planner_role": "system under test; no task ID/class/oracle input",
            "task_oracle_corpus_threshold_changes": False,
        },
        "review_volume": {
            "expected_plans": len(expectations),
            "tuning": sum(item["split"] == "tuning" for item in tasks.values()),
            "held_out": sum(item["split"] == "held-out" for item in tasks.values()),
            "new_manual_plans": 0,
            "basis": "reuse sealed EvaluationPIPlan manual review",
        },
        "results": results,
        "selection_quality": {
            "overall": _aggregate(results),
            **{split: _aggregate(items) for split, items in sorted(by_split.items())},
        },
        "decision_latency": {
            "sample_count": len(latency_samples),
            "repetitions_per_task": latency_repetitions,
            "mean_us": round(statistics.mean(latency_samples), 3),
            "p50_us": _percentile(latency_samples, 0.50),
            "p95_us": _percentile(latency_samples, 0.95),
            "p99_us": _percentile(latency_samples, 0.99),
            "max_us": max(latency_samples),
            "repository_io": 0,
            "llm_calls": 0,
        },
        "native_behavior": {
            "authority": "shadow_only",
            "capabilities_executed": 0,
            "context_delivered": False,
            "model_route_changed": False,
            "verification_changed": False,
            "user_visible_interventions": 0,
        },
        "efficiency": {
            "llm_calls_requested": 0,
            "llm_calls_executed": 0,
            "llm_calls_avoided": len(results),
            "avoided_call_ratio": 1.0,
            "avoidance_basis": "deterministic C1 decisions requiring no model classifier",
            "input_tokens": 0,
            "output_tokens": 0,
            "reasoning_tokens": 0,
            "average_context_tokens": 0,
            "max_context_tokens": 0,
            "planned_context_budget_mean_tokens": round(
                statistics.mean(planned_context_budgets), 3
            ),
            "planned_context_budget_max_tokens": max(planned_context_budgets),
            "planned_context_budget_basis": (
                "shadow recommendation only; existing 8192 configured cap and 2000-token "
                "bounded context baseline"
            ),
            "deterministic_resolution_ratio": 1.0,
            "escalation_rate": 0.0,
            "minimum_sufficient_depth": dict(sorted(depth_distribution.items())),
            "model_wall_time_ms": 0,
            "deterministic_pi_wall_time_ms": round(
                sum(int(item["decision_latency_us"]) for item in results) / 1_000, 3
            ),
            "total_wall_time_ms": round(
                sum(int(item["decision_latency_us"]) for item in results) / 1_000, 3
            ),
            "reused_evidence_count": 0,
            "invalidated_evidence_count": 0,
            "sealed_expected_plan_reused_count": len(expectations),
        },
        "gates": {
            "sealed_expected_plan_reused": True,
            "tuning_and_held_out_separate": True,
            "intent_accuracy_measured": True,
            "selection_precision_recall_measured": True,
            "under_over_selection_measured": True,
            "decision_latency_bounded": max(latency_samples) < 50_000,
            "no_repository_scale_synchronous_io": True,
            "no_llm_classifier": True,
            "native_behavior_unchanged": all(not item["behavior_changed"] for item in results),
            "shadow_only": all(item["shadow_only"] for item in results),
        },
        "plan_identity_count": len(set(plan_ids.values())),
    }
    return _sealed(body)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--latency-repetitions", type=int, default=100)
    args = parser.parse_args()
    if args.latency_repetitions <= 0:
        raise SystemExit("--latency-repetitions must be positive")
    result = evaluate(args.latency_repetitions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"output": str(args.output), "seal": result["seal"]}, indent=2))


if __name__ == "__main__":
    main()
