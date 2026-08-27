#!/usr/bin/env python3
"""Ask whether PI changes what a local model answers, not just what it is handed.

Every C2 measurement so far is delivery: did PI carry the facts an answer needs. None asks
the question the stage exists for — does handing them over change the answer. B0b found no
difference between forced-PI and off arms, and that has never been re-tested since the
delivery path was repaired.

Two arms, same task, same model, same output budget:

- **PI** — the bounded envelope, with its `answer` grouping.
- **baseline** — the objective and the repository's file listing, which is what an agent
  starts from when it has to find things itself.

The baseline is given the file listing rather than nothing, because "no PI" does not mean
"no eyes": a coding agent can list and search. A strawman baseline would prove nothing.

Scored on the same oracle as every other instrument here, and reported per
`pi_value_class`, never pooled.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import tempfile
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from c2_evidence_recall import Case, corpus_cases, sealed_cases

from extendcodeagent.core.config import ConfigLayer, ConfigResolver
from extendcodeagent.core.config.schema import CONFIGURABLE_CAPABILITIES
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.service import ProjectIntelligenceApplication

ROOT = Path(__file__).resolve().parents[2]

RULES = (
    "Answer the question about this repository.\n"
    'Reply with JSON only: {"tests": ["<repository-relative path>", ...]}\n'
    "List every existing test file that must run for the change described. Paths only.\n"
    "Do not invent paths. If you cannot tell, return an empty list.\n"
)


class TaskEffectError(RuntimeError):
    """The measurement cannot be trusted."""


def _policy() -> CapabilityPolicy:
    layer = ConfigLayer(
        "c2-effect",
        {
            "project_intelligence": {
                "enabled": True,
                "mode": "active",
                "capabilities": {item.value: "active" for item in CONFIGURABLE_CAPABILITIES},
            }
        },
    )
    return CapabilityPolicy.from_config(ConfigResolver().resolve(layer).project_intelligence)


def complete(endpoint: str, model: str, prompt: str, max_tokens: int) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0,
    }
    request = urllib.request.Request(
        f"{endpoint.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=1800) as response:
            raw = json.load(response)
    except (urllib.error.URLError, TimeoutError) as error:
        raise TaskEffectError(f"model endpoint failed: {error}") from error
    choice = raw["choices"][0]
    usage = raw.get("usage", {})
    return {
        "text": str(choice.get("message", {}).get("content") or ""),
        "finish_reason": choice.get("finish_reason"),
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
    }


def answered_paths(text: str) -> tuple[str, ...]:
    """Paths the model named, however it wrapped them."""

    found: list[str] = []
    start = text.find("{")
    if start >= 0:
        try:
            parsed = json.loads(text[start : text.rindex("}") + 1])
        except (json.JSONDecodeError, ValueError):
            parsed = None
        if isinstance(parsed, dict):
            value = parsed.get("tests")
            if isinstance(value, list):
                found = [item for item in value if isinstance(item, str)]
    if not found:
        import re

        found = re.findall(r"[\w./-]*tests?/[\w./-]+\.py", text)
    return tuple(dict.fromkeys(item.strip().lstrip("./") for item in found if item.strip()))


def _score(named: tuple[str, ...], case: Case, listing: set[str]) -> dict[str, Any]:
    need = set(case.required_facts)
    hit = need & set(named)
    invented = [path for path in named if path not in listing]
    return {
        "named": len(named),
        "recall": round(len(hit) / len(need), 6),
        "precision": round(len(hit) / len(named), 6) if named else 0.0,
        "invented_paths": len(invented),
        "missing": sorted(need - set(named)),
    }


def build_prompts(
    repository: Path, cases: tuple[Case, ...], listing_cap: int
) -> tuple[dict[str, dict[str, str]], set[str]]:
    listed = subprocess.check_output(
        ["git", "-C", str(repository), "ls-files"], text=True
    ).splitlines()
    listing = {item for item in listed if item}
    # The baseline sees the tests, which is what it would find by listing them itself.
    visible = sorted(item for item in listing if "test" in item and item.endswith(".py"))
    catalogue = "\n".join(visible[:listing_cap])

    prompts: dict[str, dict[str, str]] = {}
    with (
        tempfile.TemporaryDirectory(prefix="eca-effect-") as temp,
        ProjectIntelligenceApplication(
            repository, Path(temp) / "graph.db", _policy()
        ) as application,
    ):
        application._snapshot(open_if_missing=True)
        for case in cases:
            envelope = application.context(
                case.objective, case.target_refs, token_budget=8_192, view="envelope"
            )
            evidence = json.dumps(envelope["task_evidence"], ensure_ascii=False, indent=2)
            prompts[case.case_id] = {
                "pi": f"{RULES}\n### EVIDENCE\n{evidence}\n\n### TASK\n{case.objective}\n",
                "baseline": (
                    f"{RULES}\n### TEST FILES IN THIS REPOSITORY\n{catalogue}\n\n"
                    f"### TASK\n{case.objective}\n"
                ),
            }
    return prompts, listing


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=None)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8098/v1")
    parser.add_argument("--model", required=True)
    parser.add_argument("--max-output", type=int, default=4_096)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--listing-cap", type=int, default=400)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repository, cases = (ROOT, sealed_cases()) if args.corpus is None else corpus_cases(args.corpus)
    cases = cases[: args.limit]
    prompts, listing = build_prompts(repository, cases, args.listing_cap)

    rows: list[dict[str, Any]] = []
    for case in cases:
        row: dict[str, Any] = {
            "case_id": case.case_id,
            "task_class": case.task_class,
            "pi_value_class": case.pi_value_class,
            "required": list(case.required_facts),
        }
        for arm in ("pi", "baseline"):
            result = complete(
                args.endpoint, args.model, prompts[case.case_id][arm], args.max_output
            )
            named = answered_paths(result["text"])
            row[arm] = {
                **_score(named, case, listing),
                "prompt_tokens": result["prompt_tokens"],
                "completion_tokens": result["completion_tokens"],
                "finish_reason": result["finish_reason"],
                "empty_answer": not result["text"].strip(),
            }
        row["recall_delta"] = round(row["pi"]["recall"] - row["baseline"]["recall"], 6)
        rows.append(row)
        print(
            f"  {case.case_id:20} PI r={row['pi']['recall']:.2f} p={row['pi']['precision']:.2f}"
            f"  |  base r={row['baseline']['recall']:.2f} p={row['baseline']['precision']:.2f}",
            flush=True,
        )

    def mean(arm: str, key: str) -> float:
        return round(statistics.mean(item[arm][key] for item in rows), 6)

    result = {
        "classification": "C2_TASK_EFFECT_DIAGNOSTIC",
        "note": (
            "Diagnostic. The sealed local-practical arm is port-8090; this endpoint is a "
            "different route and is not recorded as B0b/C2 evidence."
        ),
        "captured_at": datetime.now(UTC).isoformat(),
        "repository": str(repository),
        "endpoint": args.endpoint,
        "model": args.model,
        "max_output_tokens": args.max_output,
        "cases": len(rows),
        "summary": {
            "pi_recall": mean("pi", "recall"),
            "baseline_recall": mean("baseline", "recall"),
            "pi_precision": mean("pi", "precision"),
            "baseline_precision": mean("baseline", "precision"),
            "pi_invented_paths": mean("pi", "invented_paths"),
            "baseline_invented_paths": mean("baseline", "invented_paths"),
            "pi_prompt_tokens": mean("pi", "prompt_tokens"),
            "baseline_prompt_tokens": mean("baseline", "prompt_tokens"),
            "pi_ahead": sum(1 for item in rows if item["recall_delta"] > 0),
            "tied": sum(1 for item in rows if item["recall_delta"] == 0),
            "baseline_ahead": sum(1 for item in rows if item["recall_delta"] < 0),
            "empty_answers": sum(
                1 for item in rows for arm in ("pi", "baseline") if item[arm]["empty_answer"]
            ),
        },
        "results": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
