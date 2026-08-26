#!/usr/bin/env python3
"""Measure critical-evidence recall against the delivered envelope, per token budget.

C2's exit depends on whether a bounded envelope still carries the truth an answer needs.
That question is answerable without a model: the sealed task oracle already states the facts
a correct answer must contain, so recall can be computed deterministically at every budget on
the compression curve.

Two recalls are reported and the gap between them is the point:

- `raw` — the fact appears verbatim in the delivered payload.
- `normalized` — the fact is recoverable from a delivered evidence item after expanding its
  canonical ref into the source path and qualname the Graph already holds.

`normalized - raw` is the projection burden the envelope currently pushes onto the model: work
PI can do deterministically and today does not. `1 - normalized` is the selection gap.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from extendcodeagent.core.config import ConfigLayer, ConfigResolver
from extendcodeagent.core.config.schema import CONFIGURABLE_CAPABILITIES
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.graph import GraphSnapshot
from extendcodeagent.service import ProjectIntelligenceApplication

ROOT = Path(__file__).resolve().parents[2]
TASK_SUITE = ROOT / "docs/evaluation/task-suite-v1.json"
DEFAULT_OUTPUT = ROOT / "docs/evidence/final/c2-evidence-recall-curve-v1.json"
BUDGETS = (1_024, 2_048, 4_096, 8_192, 16_384, 32_768)

# The same target refs the C2 preflight uses, so both instruments describe one condition.
TARGETS = {
    "eca-symbol-001": ("py://src.extendcodeagent.testing.service#select_tests",),
    "eca-impact-001": ("py://src.extendcodeagent.analysis.service#_edge_meets_confidence",),
    "eca-tests-001": (
        "py://src.extendcodeagent.verification.service#derive_required_verification_set",
    ),
}


class RecallMeasurementError(RuntimeError):
    """The sealed task suite cannot be trusted as an oracle."""


def _canonical(value: dict[str, Any]) -> bytes:
    body = {key: item for key, item in value.items() if key != "seal"}
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _load_sealed(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    expected = hashlib.sha256(_canonical(value)).hexdigest()
    if value.get("seal") != {"algorithm": "sha256", "canonical_payload": expected}:
        raise RecallMeasurementError(f"seal mismatch: {path}")
    return value


def _seal(value: dict[str, Any]) -> dict[str, Any]:
    return {
        **value,
        "seal": {
            "algorithm": "sha256",
            "canonical_payload": hashlib.sha256(_canonical(value)).hexdigest(),
        },
    }


def _policy() -> CapabilityPolicy:
    layer = ConfigLayer(
        "c2-recall",
        {
            "project_intelligence": {
                "enabled": True,
                "mode": "active",
                "capabilities": {item.value: "active" for item in CONFIGURABLE_CAPABILITIES},
            }
        },
    )
    return CapabilityPolicy.from_config(ConfigResolver().resolve(layer).project_intelligence)


def required_facts(task: dict[str, Any]) -> tuple[str, ...]:
    """The strings a correct answer must contain, taken from the sealed oracle."""

    facts: set[str] = set()
    for check in task["oracle"]["checks"]:
        if check["kind"] != "answer":
            continue
        for field, value in check["equals"].items():
            if field == "status":
                continue
            for item in value if isinstance(value, list) else [value]:
                if isinstance(item, str) and item.strip():
                    facts.add(item)
    return tuple(sorted(facts))


def _ref_expansions(snapshot: GraphSnapshot) -> dict[str, tuple[str, ...]]:
    """What each canonical ref would resolve to if PI projected it deterministically."""

    expansions: dict[str, tuple[str, ...]] = {}
    for node in snapshot.nodes:
        qualname = str(node.properties.get("qualname", ""))
        values = [node.canonical_ref.value, node.source_ref]
        if qualname:
            values.append(qualname)
        expansions[node.canonical_ref.value] = tuple(dict.fromkeys(values))
    return expansions


def _measure(
    application: ProjectIntelligenceApplication,
    expansions: dict[str, tuple[str, ...]],
    task: dict[str, Any],
    budget: int,
) -> dict[str, Any]:
    facts = required_facts(task)
    envelope = application.context(
        str(task["instruction"]),
        TARGETS[str(task["id"])],
        token_budget=budget,
        view="envelope",
    )
    evidence = envelope["task_evidence"]
    metrics = envelope["metrics"]
    delivered = json.dumps(evidence, ensure_ascii=False)
    recoverable = {
        value for item in evidence["items"] for value in expansions.get(item["ref"], (item["ref"],))
    }
    raw = tuple(fact for fact in facts if fact in delivered)
    normalized = tuple(fact for fact in facts if fact in recoverable)
    return {
        "token_budget": budget,
        "delivered_evidence_tokens": metrics["delivered_evidence_tokens"],
        "estimated_evidence_tokens": metrics["estimated_evidence_tokens"],
        "unused_budget_tokens": budget - metrics["estimated_evidence_tokens"],
        "selected_count": metrics["selected_count"],
        "candidate_count": metrics["candidate_count"],
        "excluded_count": metrics["excluded_count"],
        "required_fact_count": len(facts),
        "raw_recall": round(len(raw) / len(facts), 6) if facts else None,
        "normalized_recall": round(len(normalized) / len(facts), 6) if facts else None,
        "projection_burden": round((len(normalized) - len(raw)) / len(facts), 6) if facts else None,
        "missing_facts": sorted(set(facts) - set(normalized)),
    }


def evaluate(budgets: tuple[int, ...]) -> dict[str, Any]:
    suite = _load_sealed(TASK_SUITE)
    tasks = {str(item["id"]): item for item in suite["tasks"]}
    missing = sorted(set(TARGETS) - set(tasks))
    if missing:
        raise RecallMeasurementError(f"targets missing from the sealed suite: {missing}")

    rows: list[dict[str, Any]] = []
    with (
        tempfile.TemporaryDirectory(prefix="eca-c2-recall-") as temp,
        ProjectIntelligenceApplication(ROOT, Path(temp) / "graph.db", _policy()) as application,
    ):
        snapshot = application._snapshot(open_if_missing=True)
        expansions = _ref_expansions(snapshot)
        twin = {
            "nodes": len(snapshot.nodes),
            "edges": len(snapshot.edges),
            "source_directories": sorted(
                {node.source_ref.split("/")[0] for node in snapshot.nodes}
            )[:12],
        }
        for task_id in TARGETS:
            task = tasks[task_id]
            rows.append(
                {
                    "task_id": task_id,
                    "split": task["split"],
                    "required_facts": list(required_facts(task)),
                    "curve": [
                        _measure(application, expansions, task, budget) for budget in budgets
                    ],
                }
            )

    best = [max(row["curve"], key=lambda item: item["normalized_recall"] or 0.0) for row in rows]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    return _seal(
        {
            "schema": 1,
            "classification": "C2_CRITICAL_EVIDENCE_RECALL_CURVE",
            "captured_at": datetime.now(UTC).isoformat(),
            "source_revision": head,
            "execution_scope": "local-only",
            "model_execution": "NOT_RUN_DETERMINISTIC_MEASUREMENT",
            "task_suite_seal": suite["seal"]["canonical_payload"],
            "twin": twin,
            "budgets": list(budgets),
            "results": rows,
            "summary": {
                "tasks": len(rows),
                "best_normalized_recall_mean": round(
                    sum(item["normalized_recall"] or 0.0 for item in best) / len(best), 6
                ),
                "best_raw_recall_mean": round(
                    sum(item["raw_recall"] or 0.0 for item in best) / len(best), 6
                ),
                "recall_improves_with_budget": any(
                    (row["curve"][-1]["normalized_recall"] or 0.0)
                    > (row["curve"][0]["normalized_recall"] or 0.0)
                    for row in rows
                ),
                "max_unused_budget_tokens": max(
                    item["unused_budget_tokens"] for row in rows for item in row["curve"]
                ),
            },
            "efficiency": {
                "llm_calls_requested": 0,
                "llm_calls_executed": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "model_wall_time_ms": 0,
            },
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--budgets", type=int, nargs="+", default=list(BUDGETS))
    args = parser.parse_args()
    result = evaluate(tuple(args.budgets))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result["summary"], indent=2))
    print(json.dumps({"output": str(args.output), "seal": result["seal"]}, indent=2))


if __name__ == "__main__":
    main()
