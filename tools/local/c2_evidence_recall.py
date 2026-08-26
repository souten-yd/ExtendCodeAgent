#!/usr/bin/env python3
"""Measure critical-evidence recall against the delivered envelope, per token budget.

C2's exit depends on whether a bounded envelope still carries the truth an answer needs.
That question is answerable without a model: an oracle states the facts a correct answer
must contain, so recall is computable at every budget on the compression curve.

Two recalls are reported and the gap between them is the point:

- `raw` — the fact appears verbatim in the delivered payload.
- `normalized` — the fact is recoverable from a delivered evidence item after expanding its
  canonical ref into the source path and qualname the Graph already holds.

`normalized - raw` is the projection burden the envelope pushes onto the model.
`1 - normalized` is the selection gap.

Two sources of cases:

- default — the sealed `task-suite-v1.json` tasks, whose `answer` oracles name required facts.
- `--corpus <file>` — an external corpus descriptor, so a public repository can be measured
  without touching the sealed suite. See docs/handoff/C2_EXTERNAL_VALIDATION_PLAN.md §4.2.

Results are grouped by `pi_value_class`. Pooling classes PI can move with classes it cannot is
what made the B0b effect undetectable, so this tool does not report a single pooled number.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
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

# Target refs for the sealed tasks, shared with tools/local/c2_evidence_protocol.py so both
# instruments describe one condition.
SEALED_TARGETS = {
    "eca-symbol-001": ("py://src.extendcodeagent.testing.service#select_tests",),
    "eca-impact-001": ("py://src.extendcodeagent.analysis.service#_edge_meets_confidence",),
    "eca-tests-001": (
        "py://src.extendcodeagent.verification.service#derive_required_verification_set",
    ),
}
SEALED_CLASSES = {
    "eca-symbol-001": ("symbol_location", "high"),
    "eca-impact-001": ("change_impact", "high"),
    "eca-tests-001": ("test_selection", "high"),
}


class RecallMeasurementError(RuntimeError):
    """The corpus cannot be trusted as an oracle."""


@dataclass(frozen=True, slots=True)
class Case:
    """One measurable question and the facts a correct answer must contain."""

    case_id: str
    objective: str
    target_refs: tuple[str, ...]
    required_facts: tuple[str, ...]
    task_class: str = "unclassified"
    pi_value_class: str = "unknown"
    split: str = "tuning"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise RecallMeasurementError(f"case {self.case_id} has no objective")
        if not self.required_facts:
            raise RecallMeasurementError(f"case {self.case_id} states no required facts")
        if self.pi_value_class not in {"high", "low", "unknown"}:
            raise RecallMeasurementError(
                f"case {self.case_id} pi_value_class must be high, low or unknown"
            )


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


def sealed_required_facts(task: dict[str, Any]) -> tuple[str, ...]:
    """The strings a correct answer must contain, taken from the sealed oracle."""

    facts: set[str] = set()
    for check in task["oracle"]["checks"]:
        if check["kind"] != "answer":
            continue
        for name, value in check["equals"].items():
            if name == "status":
                continue
            for item in value if isinstance(value, list) else [value]:
                if isinstance(item, str) and item.strip():
                    facts.add(item)
    return tuple(sorted(facts))


def sealed_cases() -> tuple[Case, ...]:
    suite = _load_sealed(TASK_SUITE)
    tasks = {str(item["id"]): item for item in suite["tasks"]}
    missing = sorted(set(SEALED_TARGETS) - set(tasks))
    if missing:
        raise RecallMeasurementError(f"targets missing from the sealed suite: {missing}")
    return tuple(
        Case(
            case_id=case_id,
            objective=str(tasks[case_id]["instruction"]),
            target_refs=targets,
            required_facts=sealed_required_facts(tasks[case_id]),
            task_class=SEALED_CLASSES[case_id][0],
            pi_value_class=SEALED_CLASSES[case_id][1],
            split=str(tasks[case_id]["split"]),
            metadata={"task_suite_seal": suite["seal"]["canonical_payload"]},
        )
        for case_id, targets in SEALED_TARGETS.items()
    )


def corpus_cases(path: Path) -> tuple[Path, tuple[Case, ...]]:
    """Load an external corpus descriptor.

    The descriptor names the repository and the commit the Twin must be built at. For a
    merged-pull-request oracle that commit is the change's **parent**: indexing the commit
    itself would let PI see the answer it is being asked to find.
    """

    document = json.loads(path.read_text(encoding="utf-8"))
    repository = document["repository"]
    repository_path = Path(str(repository["path"])).expanduser().resolve()
    if not repository_path.is_dir():
        raise RecallMeasurementError(f"corpus repository is not a directory: {repository_path}")
    pinned = str(repository.get("commit") or "")
    if pinned:
        head = subprocess.check_output(
            ["git", "-C", str(repository_path), "rev-parse", "HEAD"], text=True
        ).strip()
        if head != pinned:
            raise RecallMeasurementError(
                f"corpus pins {pinned} but the checkout is at {head}; check out the pin first"
            )
    cases = tuple(
        Case(
            case_id=str(item["case_id"]),
            objective=str(item["objective"]),
            target_refs=tuple(str(value) for value in item.get("target_refs", ())),
            required_facts=tuple(str(value) for value in item["required_facts"]),
            task_class=str(item.get("task_class", "unclassified")),
            pi_value_class=str(item.get("pi_value_class", "unknown")),
            split=str(item.get("split", "tuning")),
            metadata=dict(item.get("metadata", {})),
        )
        for item in document["cases"]
    )
    if not cases:
        raise RecallMeasurementError(f"corpus {path} declares no cases")
    return repository_path, cases


def _ref_expansions(snapshot: GraphSnapshot) -> dict[str, tuple[str, ...]]:
    """What each canonical ref resolves to when PI projects it deterministically."""

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
    case: Case,
    budget: int,
) -> dict[str, Any]:
    envelope = application.context(
        case.objective, case.target_refs, token_budget=budget, view="envelope"
    )
    evidence = envelope["task_evidence"]
    metrics = envelope["metrics"]
    delivered = json.dumps(evidence, ensure_ascii=False)
    recoverable = {
        value for item in evidence["items"] for value in expansions.get(item["ref"], (item["ref"],))
    }
    facts = case.required_facts
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
        "raw_recall": round(len(raw) / len(facts), 6),
        "normalized_recall": round(len(normalized) / len(facts), 6),
        "projection_burden": round((len(normalized) - len(raw)) / len(facts), 6),
        "missing_facts": sorted(set(facts) - set(normalized)),
    }


def _grouped(rows: list[dict[str, Any]]) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[row["pi_value_class"]].append(row)
    summary: dict[str, Any] = {}
    for value_class, group in sorted(buckets.items()):
        best = [max(row["curve"], key=lambda item: item["normalized_recall"]) for row in group]
        summary[value_class] = {
            "cases": len(group),
            "task_classes": sorted({row["task_class"] for row in group}),
            "best_normalized_recall_mean": round(
                sum(item["normalized_recall"] for item in best) / len(best), 6
            ),
            "best_raw_recall_mean": round(sum(item["raw_recall"] for item in best) / len(best), 6),
            "cases_fully_recovered": sum(1 for item in best if item["normalized_recall"] == 1.0),
            "max_delivered_evidence_tokens": max(
                item["delivered_evidence_tokens"] for item in best
            ),
        }
    return summary


def evaluate(cases: tuple[Case, ...], repository: Path, budgets: tuple[int, ...]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    with (
        tempfile.TemporaryDirectory(prefix="eca-c2-recall-") as temp,
        ProjectIntelligenceApplication(
            repository, Path(temp) / "graph.db", _policy()
        ) as application,
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
        for case in cases:
            rows.append(
                {
                    "case_id": case.case_id,
                    "task_class": case.task_class,
                    "pi_value_class": case.pi_value_class,
                    "split": case.split,
                    "required_facts": list(case.required_facts),
                    "curve": [_measure(application, expansions, case, b) for b in budgets],
                }
            )

    head = subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", "HEAD"], text=True
    ).strip()
    return _seal(
        {
            "schema": 2,
            "classification": "C2_CRITICAL_EVIDENCE_RECALL_CURVE",
            "captured_at": datetime.now(UTC).isoformat(),
            "repository": str(repository),
            "source_revision": head,
            "execution_scope": "local-only",
            "model_execution": "NOT_RUN_DETERMINISTIC_MEASUREMENT",
            "twin": twin,
            "budgets": list(budgets),
            "results": rows,
            "by_pi_value_class": _grouped(rows),
            "pooling_note": (
                "Classes are reported separately on purpose. Pooling tasks PI can move with "
                "tasks it cannot is what made the B0b effect undetectable."
            ),
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
    parser.add_argument(
        "--corpus",
        type=Path,
        default=None,
        help="external corpus descriptor; omit to use the sealed task suite",
    )
    args = parser.parse_args()

    if args.corpus is None:
        repository, cases = ROOT, sealed_cases()
    else:
        repository, cases = corpus_cases(args.corpus)

    result = evaluate(cases, repository, tuple(args.budgets))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    args.output.write_text(payload, encoding="utf-8")
    print(json.dumps(result["by_pi_value_class"], indent=2))
    print(json.dumps({"output": str(args.output), "seal": result["seal"]}, indent=2))


if __name__ == "__main__":
    main()
