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

Reply with the line only. No explanation, no code fences. Answer as soon as you can.
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
    return (
        str(choice.get("message", {}).get("content") or ""),
        raw.get("usage", {}).get("prompt_tokens", 0),
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
) -> dict[str, Any]:
    opening = PROTOCOL
    if envelope is not None:
        opening += f"\n### PROJECT INTELLIGENCE\n{envelope}\n"
    opening += f"\n### TASK\n{case.objective}\n"

    messages = [{"role": "user", "content": opening}]
    prompt_tokens = 0
    read_bytes = 0
    actions: list[str] = []
    answer: tuple[str, ...] = ()

    for _ in range(max_turns):
        text, used = complete(endpoint, model, messages, max_output)
        prompt_tokens += used
        line = next((item.strip() for item in text.splitlines() if item.strip()), "")
        messages.append({"role": "assistant", "content": line or text[:200]})

        if line.upper().startswith("ANSWER") or "{" in line:
            actions.append("answer")
            answer = answered_paths(text)
            break
        if line.upper().startswith("GREP"):
            actions.append("grep")
            body, size = run_grep(repository, line[4:].strip())
        elif line.upper().startswith("READ"):
            actions.append("read")
            body, size = run_read(repository, line[4:].strip())
            read_bytes += size
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
            )
        print(
            f"  {case.case_id:20} PI {row['pi']['turns']}t/{row['pi']['prompt_tokens']:>6}tok"
            f" r={row['pi']['recall']:.2f}  |  base {row['baseline']['turns']}t/"
            f"{row['baseline']['prompt_tokens']:>6}tok r={row['baseline']['recall']:.2f}",
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
        "cases": len(rows),
        "summary": {
            arm: {
                "turns": mean(arm, "turns"),
                "prompt_tokens": mean(arm, "prompt_tokens"),
                "read_bytes": mean(arm, "read_bytes"),
                "greps": mean(arm, "greps"),
                "reads": mean(arm, "reads"),
                "recall": mean(arm, "recall"),
                "precision": mean(arm, "precision"),
                "answered": sum(1 for item in rows if item[arm]["answered"]),
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
