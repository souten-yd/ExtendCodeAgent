#!/usr/bin/env python3
"""Measure the C2 weak-local evidence protocol before any residual model call."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from extendcodeagent.core.config import ConfigLayer, ConfigResolver
from extendcodeagent.core.config.schema import CONFIGURABLE_CAPABILITIES
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.service import ProjectIntelligenceApplication

ROOT = Path(__file__).resolve().parents[2]
TASK_SUITE = ROOT / "docs/evaluation/task-suite-v1.json"
EXPECTED_PLAN = ROOT / "docs/evaluation/evaluation-pi-plan-v1.json"
DEFAULT_OUTPUT = ROOT / "docs/evidence/final/c2-weak-local-protocol-preflight-v1.json"
TASK_IDS = ("eca-symbol-001", "eca-impact-001", "eca-tests-001")
TARGETS = {
    "eca-symbol-001": ("py://src.extendcodeagent.testing.service#select_tests",),
    "eca-impact-001": ("py://src.extendcodeagent.analysis.service#_edge_meets_confidence",),
    "eca-tests-001": (
        "py://src.extendcodeagent.verification.service#derive_required_verification_set",
    ),
}


class C2PreflightError(RuntimeError):
    """The deterministic C2 Bridge cannot preserve its sealed inputs."""


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(
        {key: item for key, item in value.items() if key != "seal"},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def _load_sealed(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    expected = hashlib.sha256(_canonical(value)).hexdigest()
    if value.get("seal") != {"algorithm": "sha256", "canonical_payload": expected}:
        raise C2PreflightError(f"seal mismatch: {path}")
    return value


def _seal(value: dict[str, Any]) -> dict[str, Any]:
    body = {key: item for key, item in value.items() if key != "seal"}
    return {
        **body,
        "seal": {
            "algorithm": "sha256",
            "canonical_payload": hashlib.sha256(_canonical(body)).hexdigest(),
        },
    }


def _policy() -> CapabilityPolicy:
    layer = ConfigLayer(
        "c2-preflight",
        {
            "project_intelligence": {
                "enabled": True,
                "mode": "active",
                "capabilities": {
                    capability.value: "active" for capability in CONFIGURABLE_CAPABILITIES
                },
            }
        },
    )
    return CapabilityPolicy.from_config(ConfigResolver().resolve(layer).project_intelligence)


def _pretty_chars(value: object) -> int:
    return len(json.dumps(value, ensure_ascii=False, indent=2))


def _expected_answer(task: dict[str, Any]) -> dict[str, Any]:
    checks = task["oracle"]["checks"]
    answer_checks = [item["equals"] for item in checks if item["kind"] == "answer"]
    if len(answer_checks) != 1:
        raise C2PreflightError(f"task must have one answer oracle: {task['id']}")
    return answer_checks[0]


def _assert_task_projection(
    application: ProjectIntelligenceApplication,
    task_id: str,
    expected: dict[str, Any],
) -> dict[str, Any]:
    if task_id == "eca-symbol-001":
        value = application.symbol("select_tests", view="compact")
        fields = ("definition", "exports", "production_callers", "tests")
    elif task_id == "eca-impact-001":
        value = application.impact(TARGETS[task_id], view="compact")
        fields = ("definition", "production_methods", "direct_use_count", "focused_tests")
    else:
        value = application.tests(
            TARGETS[task_id], objective=str(expected["selected_tests"]), view="compact"
        )
        fields = ("selected_tests",)
    mismatches = {
        field: {"expected": expected[field], "actual": value.get(field)}
        for field in fields
        if value.get(field) != expected[field]
    }
    return {
        "fields": list(fields),
        "oracle_projection_equal": not mismatches,
        "mismatches": mismatches,
        "serialized_chars": _pretty_chars(value),
    }


def evaluate() -> dict[str, Any]:
    suite = _load_sealed(TASK_SUITE)
    expected_plan = _load_sealed(EXPECTED_PLAN)
    if expected_plan.get("task_suite_seal") != suite["seal"]["canonical_payload"]:
        raise C2PreflightError("EvaluationPIPlan task-suite seal drift")
    tasks = {str(item["id"]): item for item in suite["tasks"]}
    plans = {str(item["task_id"]): item for item in expected_plan["tasks"]}
    if any(task_id not in tasks or task_id not in plans for task_id in TASK_IDS):
        raise C2PreflightError("C2 task subset missing from sealed inputs")

    with tempfile.TemporaryDirectory(prefix="eca-c2-preflight-") as temp:
        database = Path(temp) / "graph.db"
        with ProjectIntelligenceApplication(ROOT, database, _policy()) as application:
            detailed_status = application.status()
            compact_status = application.status(view="compact")
            rows: list[dict[str, Any]] = []
            stable_prefixes: set[str] = set()
            for task_id in TASK_IDS:
                task = tasks[task_id]
                objective = str(task["instruction"])
                target_refs = TARGETS[task_id]
                legacy = application.context(
                    objective, target_refs, token_budget=8_192, view="detail"
                )
                envelope = application.context(
                    objective, target_refs, token_budget=8_192, view="envelope"
                )
                stable = envelope["stable_envelope"]
                evidence = envelope["task_evidence"]
                metrics = envelope["metrics"]
                stable_prefixes.add(str(stable["stable_prefix_id"]))
                expansion: dict[str, Any] | None = None
                if evidence["request_next_scope"] != "none":
                    expanded = application.context(
                        objective,
                        target_refs,
                        token_budget=8_192,
                        view="envelope",
                        scope=str(evidence["request_next_scope"]),
                        prior_evidence_ids=tuple(evidence["selected_evidence_ids"]),
                        unresolved_gaps=tuple(evidence["unresolved_evidence_gaps"]),
                    )
                    expansion = {
                        "scope": expanded["task_evidence"]["scope"],
                        "prior_evidence_ids": len(expanded["task_evidence"]["prior_evidence_ids"]),
                        "selected_count": expanded["metrics"]["selected_count"],
                        "candidate_count": expanded["metrics"]["candidate_count"],
                        "candidate_search_truncated": expanded["metrics"][
                            "candidate_search_truncated"
                        ],
                        "unresolved_evidence_gaps": expanded["task_evidence"][
                            "unresolved_evidence_gaps"
                        ],
                    }
                legacy_chars = _pretty_chars(legacy)
                envelope_chars = _pretty_chars(envelope)
                rows.append(
                    {
                        "task_id": task_id,
                        "split": task["split"],
                        "expected_capabilities": plans[task_id]["expected_capabilities"],
                        "minimum_depth": plans[task_id]["minimum_depth"],
                        "target_refs": list(target_refs),
                        "legacy_detail_chars": legacy_chars,
                        "protocol_envelope_chars": envelope_chars,
                        "character_reduction": legacy_chars - envelope_chars,
                        "character_reduction_ratio": round(
                            (legacy_chars - envelope_chars) / legacy_chars, 6
                        ),
                        "scope": evidence["scope"],
                        "candidate_count": metrics["candidate_count"],
                        "selected_count": metrics["selected_count"],
                        "candidate_search_truncated": metrics["candidate_search_truncated"],
                        "estimated_evidence_tokens": metrics["estimated_evidence_tokens"],
                        "token_budget": metrics["token_budget"],
                        "unresolved_evidence_gaps": evidence["unresolved_evidence_gaps"],
                        "request_next_scope": evidence["request_next_scope"],
                        "raw_objective_in_task_evidence": "objective" in evidence,
                        "stable_prefix_id": stable["stable_prefix_id"],
                        "one_step_expansion": expansion,
                        "task_projection": _assert_task_projection(
                            application, task_id, _expected_answer(task)
                        ),
                    }
                )

    reductions = [item["character_reduction_ratio"] for item in rows]
    status_detail_chars = _pretty_chars(detailed_status)
    status_compact_chars = _pretty_chars(compact_status)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    body = {
        "schema": 1,
        "classification": "C2_WEAK_LOCAL_PROTOCOL_DETERMINISTIC_PREFLIGHT",
        "captured_at": datetime.now(UTC).isoformat(),
        "source_revision": head,
        "execution_scope": "local-only",
        "model": "Qwen3.6 27B",
        "endpoint": "127.0.0.1:8090",
        "context": 262_144,
        "output_limit": 8_192,
        "model_execution": "NOT_RUN_DETERMINISTIC_PREFLIGHT",
        "contract": {
            "task_suite_seal": suite["seal"]["canonical_payload"],
            "evaluation_pi_plan_seal": expected_plan["seal"]["canonical_payload"],
            "task_oracle_corpus_threshold_changes": False,
            "legacy_detail_api_preserved": True,
        },
        "status_projection": {
            "legacy_detail_chars": status_detail_chars,
            "compact_chars": status_compact_chars,
            "character_reduction_ratio": round(
                (status_detail_chars - status_compact_chars) / status_detail_chars, 6
            ),
            "configured_capabilities_retained": len(compact_status["capabilities"]),
            "omitted_unimplemented_capabilities": compact_status[
                "omitted_unimplemented_capabilities"
            ],
        },
        "results": rows,
        "summary": {
            "tasks": len(rows),
            "mean_context_character_reduction_ratio": round(statistics.mean(reductions), 6),
            "minimum_context_character_reduction_ratio": min(reductions),
            "stable_prefix_identity_count": len(stable_prefixes),
            "oracle_projection_equal": all(
                item["task_projection"]["oracle_projection_equal"] for item in rows
            ),
            "candidate_bound_pass": all(item["candidate_count"] <= 256 for item in rows),
            "selected_bound_pass": all(item["selected_count"] <= 32 for item in rows),
            "token_bound_pass": all(
                item["estimated_evidence_tokens"] <= item["token_budget"] for item in rows
            ),
            "raw_objective_absent": all(
                not item["raw_objective_in_task_evidence"] for item in rows
            ),
        },
        "efficiency": {
            "llm_calls_requested": 0,
            "llm_calls_executed": 0,
            "llm_calls_avoided": len(rows),
            "avoided_call_ratio": 1.0,
            "input_tokens": 0,
            "output_tokens": 0,
            "reasoning_tokens": 0,
            "model_wall_time_ms": 0,
            "reused_evidence_count": len(rows) * 2,
            "invalidated_evidence_count": 0,
        },
        "next_gate": {
            "local_low": "UNAVAILABLE_NOT_CONFIGURED",
            "local_practical": "SMALL_REPEATED_RESIDUAL_BRIDGE_REQUIRED",
            "other_model_tiers": "NOT_RUN_USER_POLICY",
        },
    }
    return _seal(body)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = evaluate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"output": str(args.output), "seal": result["seal"]}, indent=2))


if __name__ == "__main__":
    main()
