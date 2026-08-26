#!/usr/bin/env python3
"""Measure what a task costs an agent, with and without PI.

Recall says whether PI's answer is right. It does not say whether context got smaller,
and this programme's own numbers suggest that link is weak: PI's payload was 21% of the
held-out baseline's prompt, and the accumulating loop was the rest. An envelope that is
correct but never reduces reading has not addressed why context is long.

So this measures the loop instead. The model is given tools and works until it answers,
and what is counted is the cost of getting there:

- **turns** — every one re-sends the accumulated conversation, which is how a session grows
- **cumulative prompt tokens** — the number the 32k/64k target is actually about
- **bytes read** — whole files opened for what may be a seven-line function
- **answer quality** — the same oracle as every other instrument here

The PI arm gets the envelope up front and the same tools. It is free to ignore the
envelope and search anyway, which is itself worth seeing: published work found agents
reaching for grep even when a structural tool was available.

A text action protocol is used rather than the tool-calling API, so the measurement does
not depend on a particular server's function-calling support.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import tempfile
import time
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
MAX_GREP_HITS = 40
MAX_READ_BYTES = 20_000

PROTOCOL = """You are answering a question about a repository. Work one step at a time.

Each reply must be exactly one line, one of:
  GREP <pattern>          search the repository for a literal string
  READ <path>             read a file
  ANSWER {"tests": [...]} the repository-relative paths of every test that must run

Reply with the line only. No explanation, no code fences.

Answer when you have evidence for it. If what you have is not enough, search first --
an incomplete answer costs more than another step.
"""


class LoopError(RuntimeError):
    """The loop cannot be trusted."""


def _policy() -> CapabilityPolicy:
    layer = ConfigLayer(
        "c2-loop",
        {
            "project_intelligence": {
                "enabled": True,
                "mode": "active",
                "capabilities": {item.value: "active" for item in CONFIGURABLE_CAPABILITIES},
            }
        },
    )
    return CapabilityPolicy.from_config(ConfigResolver().resolve(layer).project_intelligence)


def complete(endpoint: str, model: str, messages: list[dict[str, str]], max_tokens: int) -> Any:
    request = urllib.request.Request(
        f"{endpoint.rstrip('/')}/chat/completions",
        data=json.dumps(
            {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0}
        ).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=1800) as response:
            raw = json.load(response)
    except (urllib.error.URLError, TimeoutError) as error:
        raise LoopError(f"model endpoint failed: {error}") from error
    choice = raw["choices"][0]
    usage = raw.get("usage", {})
    prompt = usage.get("prompt_tokens", 0)
    # A stable prefix is not paid for twice. Measured on this endpoint, re-sending an
    # identical 13,099-token prefix reports cached_tokens 13,095 -- 99.97% of it. Counting
    # prompt_tokens as cost charges an envelope again on every turn it was not reprocessed
    # for, which is what made a one-shot envelope look ruinous across twelve turns.
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
    return (
        str(choice.get("message", {}).get("content") or ""),
        prompt,
        max(prompt - cached, 0),
    )


def run_grep(repository: Path, pattern: str) -> tuple[str, int]:
    result = subprocess.run(
        ["git", "-C", str(repository), "grep", "-I", "-l", "-F", "--", pattern],
        capture_output=True,
        text=True,
        check=False,
    )
    hits = [line for line in result.stdout.splitlines() if line][:MAX_GREP_HITS]
    body = "\n".join(hits) if hits else "(no match)"
    return body, len(body)


def run_read(repository: Path, path: str) -> tuple[str, int]:
    candidate = (repository / path.strip()).resolve()
    if not candidate.is_relative_to(repository.resolve()) or not candidate.is_file():
        return f"(no such file: {path})", 0
    body = candidate.read_text(encoding="utf-8", errors="replace")[:MAX_READ_BYTES]
    return body, len(body)


def answered_paths(text: str) -> tuple[str, ...]:
    start = text.find("{")
    if start >= 0:
        try:
            parsed = json.loads(text[start : text.rindex("}") + 1])
            value = parsed.get("tests") if isinstance(parsed, dict) else None
            if isinstance(value, list):
                return tuple(
                    dict.fromkeys(
                        item.strip().lstrip("./") for item in value if isinstance(item, str)
                    )
                )
        except (json.JSONDecodeError, ValueError):
            pass
    return tuple(dict.fromkeys(re.findall(r"[\w./-]*tests?/[\w./-]+\.py", text)))


def run_loop(
    repository: Path,
    case: Case,
    endpoint: str,
    model: str,
    *,
    envelope: str | None,
    max_turns: int,
    max_output: int,
    absences: tuple[str, ...] = (),
    until_complete: bool = False,
) -> dict[str, Any]:
    opening = PROTOCOL
    if envelope is not None:
        opening += f"\n### PROJECT INTELLIGENCE\n{envelope}\n"
    if absences:
        # Established at this revision: searched for, and not there. Without it the same
        # ground gets covered again -- traced on Django, seventeen of twenty-two baseline
        # actions returned nothing and five repeated one that already had.
        listed = "\n".join(f"  {item}" for item in absences)
        opening += (
            "\n### ALREADY RULED OUT (searched at this revision, nothing found)\n"
            f"{listed}\nDo not search for these again.\n"
        )
    opening += f"\n### TASK\n{case.objective}\n"

    messages = [{"role": "user", "content": opening}]
    prompt_tokens = 0
    read_bytes = 0
    actions: list[str] = []
    trace: list[dict[str, Any]] = []
    answer: tuple[str, ...] = ()
    attempts = 0

    uncached_tokens = 0
    per_turn: list[int] = []
    uncached_per_turn: list[int] = []
    # Wall time is the axis tokens hide. A large envelope is re-sent every turn, so its
    # prefill is paid again every turn, and the arm with the smaller prompt can afford
    # more of them in the same wall clock.
    seconds_per_turn: list[float] = []
    for _ in range(max_turns):
        started = time.monotonic()
        text, used, fresh = complete(endpoint, model, messages, max_output)
        seconds_per_turn.append(round(time.monotonic() - started, 3))
        prompt_tokens += used
        uncached_tokens += fresh
        per_turn.append(used)
        uncached_per_turn.append(fresh)
        line = next((item.strip() for item in text.splitlines() if item.strip()), "")
        messages.append({"role": "assistant", "content": line or text[:200]})

        if line.upper().startswith("ANSWER") or "{" in line:
            actions.append("answer")
            answer = answered_paths(text)
            if not until_complete or set(case.required_facts) <= set(answer):
                break
            # The arm that has not finished keeps going, which is the only way this harness
            # ever accumulates: an arm that answers in one turn has no history to carry, so
            # comparing arms that reached different outcomes measured cost, not context.
            #
            # The signal deliberately does not say what is missing. Naming it would hand
            # over the oracle; a real agent learns only that its verification did not pass.
            attempts += 1
            body = (
                "That selection is incomplete. Keep looking, then answer again."
                if answer
                else "No answer given. Continue."
            )
            messages.append({"role": "user", "content": body})
            continue
        if line.upper().startswith("GREP"):
            actions.append("grep")
            argument = line[4:].strip()
            body, size = run_grep(repository, argument)
            trace.append(
                {
                    "kind": "grep",
                    "arg": argument,
                    "hits": 0 if body == "(no match)" else len(body.splitlines()),
                }
            )
        elif line.upper().startswith("READ"):
            actions.append("read")
            argument = line[4:].strip()
            body, size = run_read(repository, argument)
            read_bytes += size
            trace.append({"kind": "read", "arg": argument, "hits": 1 if size else 0})
        else:
            actions.append("malformed")
            body = "Reply with exactly one line: GREP, READ or ANSWER."
            size = 0
        messages.append({"role": "user", "content": body[:MAX_READ_BYTES]})

    need = set(case.required_facts)
    hit = need & set(answer)

    return {
        "turns": len(actions),
        "prompt_tokens": prompt_tokens,
        "read_bytes": read_bytes,
        "greps": actions.count("grep"),
        "reads": actions.count("read"),
        "malformed": actions.count("malformed"),
        "answered": bool(answer),
        # Everything the task cost to reach this outcome, which is the comparable number
        # once both arms are required to reach the same one.
        "cost_to_outcome": uncached_tokens,
        "billed_prompt_tokens": prompt_tokens,
        "complete": bool(answer) and need <= set(answer),
        "reanswers": attempts,
        "trace": trace,
        # Each turn re-sends everything before it, so this curve is the cost of holding a
        # task's own history in the conversation rather than beside it.
        "prompt_tokens_per_turn": per_turn,
        # What the model actually had to process, which is the honest cost of a turn.
        "uncached_prompt_tokens": uncached_tokens,
        "uncached_per_turn": uncached_per_turn,
        "seconds_per_turn": seconds_per_turn,
        "seconds": round(sum(seconds_per_turn), 2),
        # Work spent rediscovering that something is not there, or is where it already was.
        "empty_searches": sum(1 for item in trace if item["kind"] == "grep" and not item["hits"]),
        "repeated_actions": len(trace) - len({(item["kind"], item["arg"]) for item in trace}),
        "recall": round(len(hit) / len(need), 6),
        "precision": round(len(hit) / len(answer), 6) if answer else 0.0,
    }


def build_envelopes(repository: Path, cases: tuple[Case, ...]) -> dict[str, str]:
    out: dict[str, str] = {}
    with (
        tempfile.TemporaryDirectory(prefix="eca-loop-") as temp,
        ProjectIntelligenceApplication(
            repository, Path(temp) / "graph.db", _policy()
        ) as application,
    ):
        application._snapshot(open_if_missing=True)
        for case in cases:
            payload = application.context(
                case.objective, case.target_refs, token_budget=8_192, view="envelope"
            )
            out[case.case_id] = json.dumps(payload["task_evidence"], ensure_ascii=False, indent=2)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=None)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8098/v1")
    parser.add_argument("--model", required=True)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--max-turns", type=int, default=8)
    parser.add_argument("--max-output", type=int, default=2_048)
    parser.add_argument(
        "--until-complete",
        action="store_true",
        help=(
            "keep a task running until its answer is complete, so both arms are "
            "compared at the same outcome and an arm that struggles accumulates"
        ),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repository, cases = (ROOT, sealed_cases()) if args.corpus is None else corpus_cases(args.corpus)
    cases = cases[: args.limit]
    envelopes = build_envelopes(repository, cases)

    rows: list[dict[str, Any]] = []
    for case in cases:
        row: dict[str, Any] = {"case_id": case.case_id, "required": list(case.required_facts)}
        for arm, envelope in (("pi", envelopes[case.case_id]), ("baseline", None)):
            row[arm] = run_loop(
                repository,
                case,
                args.endpoint,
                args.model,
                envelope=envelope,
                max_turns=args.max_turns,
                max_output=args.max_output,
                until_complete=args.until_complete,
            )
        print(
            f"  {case.case_id:20} PI {row['pi']['turns']}t/{row['pi']['prompt_tokens']:>6}tok"
            f" r={row['pi']['recall']:.2f} {'ok' if row['pi']['complete'] else '--'}"
            f"  |  base {row['baseline']['turns']}t/"
            f"{row['baseline']['prompt_tokens']:>6}tok r={row['baseline']['recall']:.2f}"
            f" {'ok' if row['baseline']['complete'] else '--'}"
            f"  [{row['pi']['seconds']:.0f}s vs {row['baseline']['seconds']:.0f}s]",
            flush=True,
        )
        rows.append(row)

    def mean(arm: str, key: str) -> float:
        return round(statistics.mean(item[arm][key] for item in rows), 2)

    result = {
        "classification": "C2_AGENT_LOOP_DIAGNOSTIC",
        "note": (
            "Diagnostic. The sealed local-practical arm is port-8090; this endpoint is a "
            "different route and is not recorded as B0b/C2 evidence."
        ),
        "captured_at": datetime.now(UTC).isoformat(),
        "repository": str(repository),
        "model": args.model,
        "max_turns": args.max_turns,
        "until_complete": args.until_complete,
        "cases": len(rows),
        "summary": {
            arm: {
                "turns": mean(arm, "turns"),
                "prompt_tokens": mean(arm, "prompt_tokens"),
                "uncached_prompt_tokens": mean(arm, "uncached_prompt_tokens"),
                "read_bytes": mean(arm, "read_bytes"),
                "greps": mean(arm, "greps"),
                "reads": mean(arm, "reads"),
                "recall": mean(arm, "recall"),
                "precision": mean(arm, "precision"),
                "answered": sum(1 for item in rows if item[arm]["answered"]),
                "complete": sum(1 for item in rows if item[arm]["complete"]),
                "reanswers": mean(arm, "reanswers"),
                "seconds": mean(arm, "seconds"),
                "seconds_per_turn": round(
                    sum(item[arm]["seconds"] for item in rows)
                    / sum(item[arm]["turns"] for item in rows),
                    2,
                ),
                "seconds_per_completed_task": (
                    round(
                        sum(item[arm]["seconds"] for item in rows if item[arm]["complete"])
                        / finished,
                        1,
                    )
                    if (finished := sum(1 for item in rows if item[arm]["complete"]))
                    else None
                ),
                # Total spend to reach the stated outcome. Only comparable between arms
                # that reached the same one, which is what --until-complete enforces.
                "cost_to_outcome_total": sum(item[arm]["cost_to_outcome"] for item in rows),
                # What a task cost only where it actually finished; an arm that gives up
                # cheaply otherwise looks efficient.
                "cost_per_completed_task": (
                    round(
                        sum(item[arm]["cost_to_outcome"] for item in rows if item[arm]["complete"])
                        / completed,
                        1,
                    )
                    if (completed := sum(1 for item in rows if item[arm]["complete"]))
                    else None
                ),
            }
            for arm in ("pi", "baseline")
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
