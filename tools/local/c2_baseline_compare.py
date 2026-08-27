#!/usr/bin/env python3
"""Compare what PI delivers against what plain search delivers, at the same token budget.

Every C2 measurement so far asks whether PI handed over the required facts. None asks
whether a model without PI would have found them anyway. B0b's null result is consistent
with "PI delivers what grep already finds", and that possibility has never been tested.

This is the delivery-layer half of the comparison and it needs no model:

- **PI arm** — the bounded envelope from `pi_context view=envelope`.
- **Search arm** — the objective's distinctive terms grepped over the repository, ranked by
  hit count, emitted until the same token budget the PI arm actually used.

Both arms are scored against the same oracle. The search arm is deliberately built to be
strong: it searches the changed file's stem, which is what a coding agent would do first,
and it emits paths, which is what the oracle asks for. A weak baseline would prove nothing.

If the search arm matches the PI arm, PI is not adding truth on this task class and no
model experiment can rescue it. If the PI arm is ahead, the model experiment is worth its
cost.

Diagnostic; not a substitute for the paired task-outcome comparison in
docs/handoff/C2_EXTERNAL_VALIDATION_PLAN.md §4.3.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from c2_evidence_recall import Case, corpus_cases, sealed_cases  # noqa: E402

from extendcodeagent.context import estimate_payload_tokens
from extendcodeagent.core.config import ConfigLayer, ConfigResolver
from extendcodeagent.core.config.schema import CONFIGURABLE_CAPABILITIES
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.service import ProjectIntelligenceApplication

ROOT = Path(__file__).resolve().parents[2]
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,}")
_GENERIC = frozenset(
    {
        "and",
        "are",
        "change",
        "changes",
        "def",
        "did",
        "does",
        "existing",
        "file",
        "files",
        "for",
        "from",
        "has",
        "have",
        "must",
        "not",
        "now",
        "run",
        "select",
        "should",
        "source",
        "src",
        "test",
        "tests",
        "that",
        "the",
        "this",
        "use",
        "used",
        "with",
    }
)


def _policy() -> CapabilityPolicy:
    layer = ConfigLayer(
        "c2-baseline",
        {
            "project_intelligence": {
                "enabled": True,
                "mode": "active",
                "capabilities": {item.value: "active" for item in CONFIGURABLE_CAPABILITIES},
            }
        },
    )
    return CapabilityPolicy.from_config(ConfigResolver().resolve(layer).project_intelligence)


def _search_terms(case: Case) -> tuple[str, ...]:
    """What a coding agent would grep for: the changed file's stem, then the objective's nouns."""

    terms: list[str] = []
    for ref in case.target_refs:
        stem = Path(ref.removeprefix("file://").split("#")[0]).stem
        if stem and stem not in _GENERIC:
            terms.append(stem)
        tail = ref.split("#")[-1]
        if tail != ref and tail not in _GENERIC:
            terms.append(tail)
    terms.extend(
        word
        for word in _WORD.findall(case.objective)
        if word.casefold() not in _GENERIC and not word.startswith(("src", "file"))
    )
    return tuple(dict.fromkeys(terms))


def _grep(repository: Path, term: str) -> dict[str, int]:
    result = subprocess.run(
        ["git", "-C", str(repository), "grep", "-I", "-c", "-F", "--", term],
        capture_output=True,
        text=True,
        check=False,
    )
    hits: dict[str, int] = {}
    for line in result.stdout.splitlines():
        path, _, count = line.rpartition(":")
        if path and count.isdigit():
            hits[path] = int(count)
    return hits


def search_arm(repository: Path, case: Case, token_budget: int) -> dict[str, Any]:
    """Rank files by how often the objective's terms appear, then fill the same budget."""

    scored: dict[str, int] = defaultdict(int)
    for term in _search_terms(case)[:8]:
        for path, count in _grep(repository, term).items():
            scored[path] += count
    ranked = sorted(scored.items(), key=lambda item: (-item[1], item[0]))

    delivered: list[dict[str, Any]] = []
    used = 0
    for path, count in ranked:
        item = {"path": path, "hits": count}
        cost = estimate_payload_tokens(item)
        if used + cost > token_budget:
            continue
        delivered.append(item)
        used += cost

    blob = json.dumps(delivered, ensure_ascii=False)
    found = tuple(fact for fact in case.required_facts if fact in blob)
    return {
        "delivered_paths": len(delivered),
        "delivered_tokens": used,
        "candidates": len(ranked),
        # If everything the search found also fit, the arm never had to choose, and a
        # selection mechanism cannot be shown to help where there is nothing to select.
        "budget_constrained": len(delivered) < len(ranked),
        "recall": round(len(found) / len(case.required_facts), 6),
        "missing_facts": sorted(set(case.required_facts) - set(found)),
    }


def pi_arm(
    application: ProjectIntelligenceApplication, case: Case, token_budget: int
) -> dict[str, Any]:
    envelope = application.context(
        case.objective, case.target_refs, token_budget=token_budget, view="envelope"
    )
    blob = json.dumps(envelope["task_evidence"], ensure_ascii=False)
    found = tuple(fact for fact in case.required_facts if fact in blob)
    return {
        "delivered_items": envelope["metrics"]["selected_count"],
        "delivered_tokens": envelope["metrics"]["delivered_evidence_tokens"],
        "recall": round(len(found) / len(case.required_facts), 6),
        "missing_facts": sorted(set(case.required_facts) - set(found)),
    }


def compare(cases: tuple[Case, ...], repository: Path, token_budget: int) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    with (
        tempfile.TemporaryDirectory(prefix="eca-c2-baseline-") as temp,
        ProjectIntelligenceApplication(
            repository, Path(temp) / "graph.db", _policy()
        ) as application,
    ):
        application._snapshot(open_if_missing=True)
        for case in cases:
            pi = pi_arm(application, case, token_budget)
            # The search arm gets exactly what PI spent, so neither wins on volume.
            search = search_arm(repository, case, pi["delivered_tokens"])
            rows.append(
                {
                    "case_id": case.case_id,
                    "task_class": case.task_class,
                    "pi_value_class": case.pi_value_class,
                    "required_fact_count": len(case.required_facts),
                    "pi": pi,
                    "search": search,
                    "delta": round(pi["recall"] - search["recall"], 6),
                }
            )

    grouped: dict[str, Any] = {}
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[row["pi_value_class"]].append(row)
    for value_class, group in sorted(buckets.items()):
        grouped[value_class] = {
            "cases": len(group),
            "pi_recall_mean": round(sum(r["pi"]["recall"] for r in group) / len(group), 6),
            "search_recall_mean": round(sum(r["search"]["recall"] for r in group) / len(group), 6),
            "mean_delta": round(sum(r["delta"] for r in group) / len(group), 6),
            "pi_ahead": sum(1 for r in group if r["delta"] > 0),
            "tied": sum(1 for r in group if r["delta"] == 0),
            "search_ahead": sum(1 for r in group if r["delta"] < 0),
            "discriminating_cases": sum(1 for r in group if r["search"]["budget_constrained"]),
            "verdict": (
                "NOT_DISCRIMINATING: the search arm was never budget-constrained, so this "
                "corpus cannot separate selection from listing everything. Use a repository "
                "whose candidate set does not fit the budget."
                if not any(r["search"]["budget_constrained"] for r in group)
                else "comparison is meaningful for the budget-constrained cases"
            ),
        }

    head = subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", "HEAD"], text=True
    ).strip()
    return {
        "classification": "C2_DELIVERY_BASELINE_COMPARISON",
        "note": "Diagnostic. Delivery layer only; task outcome is not measured here.",
        "repository": str(repository),
        "source_revision": head,
        "token_budget": token_budget,
        "model_execution": "NOT_RUN_DETERMINISTIC_COMPARISON",
        "by_pi_value_class": grouped,
        "results": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=None)
    parser.add_argument("--budget", type=int, default=8_192)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.corpus is None:
        repository, cases = ROOT, sealed_cases()
    else:
        repository, cases = corpus_cases(args.corpus)

    result = compare(cases, repository, args.budget)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    args.output.write_text(payload, encoding="utf-8")
    print(json.dumps(result["by_pi_value_class"], indent=2))


if __name__ == "__main__":
    main()
