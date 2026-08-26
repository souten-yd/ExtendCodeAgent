#!/usr/bin/env python3
"""Can the agent write the change, and does the evidence it started with help?

Every corpus so far asked which tests must run and said "Do not edit source", which is the
opposite of what this runtime exists for: the data a change needs, present at
code-generation time. This asks the question that was being avoided.

The scorer is the revert oracle's by-product. Taking a commit's production half back to its
parent leaves a repository whose tests fail for a known reason, and `c2_revert_oracle.py`
already recorded which tests detect it. So the task is "make these tests pass", the verdict
is the test run, and nothing is scored by resemblance to the original patch - a different
correct fix passes.

This is also the first task here that genuinely takes several turns. Write, run, read the
failure, write again: the accumulation the 32k target is about only exists in a loop that
has something to accumulate.

Two arms, same task and same tools:

- **PI** - the initial context carries the evidence envelope: the symbols to change with
  their bodies, their consumers, one test as the project's own example, and how to run.
- **baseline** - the objective alone, with GREP and READ to find all of it.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from extendcodeagent.core.config import ConfigLayer, ConfigResolver  # noqa: E402
from extendcodeagent.core.config.schema import CONFIGURABLE_CAPABILITIES  # noqa: E402
from extendcodeagent.core.policy import CapabilityPolicy  # noqa: E402
from extendcodeagent.service.application import ProjectIntelligenceApplication  # noqa: E402


def _policy() -> CapabilityPolicy:
    layer = ConfigLayer(
        "c2-codegen",
        {
            "project_intelligence": {
                "enabled": True,
                "mode": "active",
                "capabilities": {item.value: "active" for item in CONFIGURABLE_CAPABILITIES},
            }
        },
    )
    return CapabilityPolicy.from_config(ConfigResolver().resolve(layer).project_intelligence)


PROTOCOL = """You are fixing a repository so that its failing tests pass.

Each reply must be exactly one action, in one of these forms:

  GREP <pattern>
  READ <path>
  REPLACE <path>::<function>
  <the complete new source of that function, correctly indented>
  END

After each REPLACE the tests are run and you are told the result. Do not explain.
Change production code only. The tests are correct; do not edit them.
"""

MAX_READ = 6_000


class BenchError(RuntimeError):
    pass


@dataclass(frozen=True)
class Case:
    case_id: str
    commit: str
    subject: str
    production: tuple[str, ...]
    detecting: tuple[str, ...]


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True, errors="replace")


def cases_from(findings: Path, limit: int) -> list[Case]:
    payload = json.loads(findings.read_text())
    out: list[Case] = []
    for result in payload["results"]:
        if result["undetected"] or result["wholesale_breakage"]:
            continue
        out.append(
            Case(
                case_id=f"gen-{result['sha']}",
                commit=result["sha"],
                production=(),
                subject=result["subject"],
                detecting=tuple(result["detecting_tests"]),
            )
        )
        if len(out) >= limit:
            break
    return out


def _function_names(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }


def modifies_existing_functions_only(repo: Path, case: Case, paths: tuple[str, ...]) -> bool:
    """Whether REPLACE can express this change at all.

    The action vocabulary here swaps one existing function for another, so a commit that
    adds or removes a function cannot be written no matter how well the agent reasons.
    Leaving those in would score the protocol rather than the agent, so they are refused and
    reported. It is a real bound on what this measures: additions are ordinary work.
    """

    for path in paths:
        try:
            after = _function_names(_git(repo, "show", f"{case.commit}:{path}"))
            before = _function_names(_git(repo, "show", f"{case.commit}~1:{path}"))
        except subprocess.CalledProcessError:
            return False
        if after != before:
            return False
    return True


def break_repository(repo: Path, case: Case) -> tuple[str, ...]:
    """Put the commit's production half back, leaving its tests. Returns what was reverted."""

    _git(repo, "checkout", "-q", "--force", case.commit)
    changed = [
        path
        for path in _git(repo, "show", "--name-only", "--format=", case.commit).split()
        if path.endswith(".py") and "test" not in path
    ]
    reverted = []
    for path in changed:
        try:
            _git(repo, "checkout", "-q", f"{case.commit}~1", "--", path)
            reverted.append(path)
        except subprocess.CalledProcessError:
            continue
    return tuple(reverted)


def run_tests(repo: Path, python: Path, tests: tuple[str, ...], timeout: int) -> tuple[bool, str]:
    process = subprocess.run(
        [str(python), "-m", "pytest", "-x", "-q", "--no-header", "--tb=short", *tests],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    output = (process.stdout + process.stderr)[-1_800:]
    return process.returncode == 0, output


def replace_function(repo: Path, path: str, name: str, source: str) -> str:
    """Swap one function's body for the model's, by span. Returns a message for the model."""

    target = repo / path
    if not target.is_file():
        return f"no such file: {path}"
    text = target.read_text(errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError as error:
        return f"the file does not parse: {error}"
    spans = {
        node.name: (node.lineno, node.end_lineno or node.lineno)
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    if name not in spans:
        return f"{path} defines no function named {name}"
    if not source.strip():
        return "the replacement was empty"
    try:
        ast.parse(source.strip())
    except SyntaxError as error:
        # Indented methods do not parse alone; try them inside a class.
        try:
            ast.parse("class _C:\n" + "\n".join("    " + line for line in source.splitlines()))
        except SyntaxError:
            return f"the replacement does not parse: {error}"
    start, end = spans[name]
    lines = text.splitlines()
    indent = len(lines[start - 1]) - len(lines[start - 1].lstrip())
    body = [(" " * indent + line.lstrip()) if line.strip() else "" for line in source.splitlines()]
    # Re-indent only the first line; the model's own relative indentation is kept.
    shift = indent - (len(source.splitlines()[0]) - len(source.splitlines()[0].lstrip()))
    body = [(" " * max(shift, 0) + line) if line.strip() else "" for line in source.splitlines()]
    target.write_text("\n".join([*lines[: start - 1], *body, *lines[end:]]) + "\n")
    return "applied"


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
        raise BenchError(f"model endpoint failed: {error}") from error
    usage = raw.get("usage", {})
    prompt = usage.get("prompt_tokens", 0)
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
    return (
        str(raw["choices"][0].get("message", {}).get("content") or ""),
        max(prompt - cached, 0),
    )


_REPLACE = re.compile(r"^REPLACE\s+(\S+?)::(\S+)\s*$", re.M)


def run_arm(
    repo: Path,
    python: Path,
    case: Case,
    reverted: tuple[str, ...],
    endpoint: str,
    model: str,
    *,
    envelope: str | None,
    max_turns: int,
    max_output: int,
    test_timeout: int,
) -> dict[str, Any]:
    opening = PROTOCOL
    if envelope is not None:
        opening += f"\n### PROJECT INTELLIGENCE\n{envelope}\n"
    opening += (
        "\n### TASK\nThese tests fail and must pass:\n"
        + "\n".join(f"  {item}" for item in case.detecting[:8])
        + f"\n\nThe change belongs in: {', '.join(reverted)}\n"
    )

    messages = [{"role": "user", "content": opening}]
    uncached = 0
    edits = 0
    passed = False
    seconds = 0.0
    actions: list[str] = []

    for _ in range(max_turns):
        started = time.monotonic()
        text, fresh = complete(endpoint, model, messages, max_output)
        seconds += time.monotonic() - started
        uncached += fresh
        messages.append({"role": "assistant", "content": text[:4_000]})

        match = _REPLACE.search(text)
        if match:
            actions.append("replace")
            path, name = match.group(1), match.group(2)
            after = text[match.end() :]
            source = after.split("END")[0].strip("\n")
            source = re.sub(r"^```[a-z]*\n|```$", "", source, flags=re.M)
            note = replace_function(repo, path, name, source)
            edits += 1
            if note == "applied":
                passed, output = run_tests(repo, python, case.detecting[:8], test_timeout)
                if passed:
                    break
                note = f"tests still fail:\n{output}"
            messages.append({"role": "user", "content": note[:MAX_READ]})
            continue

        line = next((item.strip() for item in text.splitlines() if item.strip()), "")
        if line.upper().startswith("GREP"):
            actions.append("grep")
            pattern = line[4:].strip()
            found = subprocess.run(
                ["grep", "-rn", "--include=*.py", "-m", "20", pattern, "."],
                cwd=repo,
                capture_output=True,
                text=True,
            )
            body = found.stdout[:MAX_READ] or "(no match)"
        elif line.upper().startswith("READ"):
            actions.append("read")
            candidate = repo / line[4:].strip()
            body = (
                candidate.read_text(errors="replace")[:MAX_READ]
                if candidate.is_file()
                else "(no such file)"
            )
        else:
            actions.append("malformed")
            body = "Reply with one action: GREP, READ, or REPLACE <path>::<function>."
        messages.append({"role": "user", "content": body})

    return {
        "passed": passed,
        "turns": len(actions),
        "edits": edits,
        "greps": actions.count("grep"),
        "reads": actions.count("read"),
        "malformed": actions.count("malformed"),
        "uncached_prompt_tokens": uncached,
        "seconds": round(seconds, 1),
    }


def build_envelope(repo: Path, case: Case, reverted: tuple[str, ...]) -> str:
    objective = f"Change {', '.join(reverted)} so that the failing tests pass: {case.subject}"
    with (
        tempfile.TemporaryDirectory(prefix="eca-gen-") as temp,
        ProjectIntelligenceApplication(repo, Path(temp) / "graph.db", _policy()) as application,
    ):
        application._snapshot(open_if_missing=True)
        payload = application.context(
            objective,
            [f"file://{path}" for path in reverted],
            token_budget=8_192,
            view="envelope",
        )
    return json.dumps(payload["task_evidence"], ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--findings", type=Path, required=True)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8098/v1")
    parser.add_argument("--model", required=True)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--max-turns", type=int, default=14)
    parser.add_argument("--max-output", type=int, default=1_536)
    parser.add_argument("--test-timeout", type=int, default=300)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    original = _git(args.repo, "rev-parse", "HEAD").strip()
    rows: list[dict[str, Any]] = []
    try:
        for case in cases_from(args.findings, args.limit):
            reverted = break_repository(args.repo, case)
            if not reverted:
                continue
            if not modifies_existing_functions_only(args.repo, case, reverted):
                print(f"  {case.case_id} skipped: adds or removes a function", flush=True)
                continue
            broken, _ = run_tests(args.repo, args.python, case.detecting[:8], args.test_timeout)
            if broken:
                # Nothing to fix: the revert did not reproduce the failure here.
                print(f"  {case.case_id} skipped: tests pass with the change removed", flush=True)
                continue
            envelope = build_envelope(args.repo, case, reverted)

            row: dict[str, Any] = {"case_id": case.case_id, "subject": case.subject}
            for arm, given in (("pi", envelope), ("baseline", None)):
                break_repository(args.repo, case)
                row[arm] = run_arm(
                    args.repo,
                    args.python,
                    case,
                    reverted,
                    args.endpoint,
                    args.model,
                    envelope=given,
                    max_turns=args.max_turns,
                    max_output=args.max_output,
                    test_timeout=args.test_timeout,
                )
            rows.append(row)
            print(
                f"  {case.case_id:18} PI {'PASS' if row['pi']['passed'] else 'fail'}"
                f" {row['pi']['turns']}t/{row['pi']['uncached_prompt_tokens']:>6}tok"
                f"/{row['pi']['seconds']:.0f}s  |  base"
                f" {'PASS' if row['baseline']['passed'] else 'fail'}"
                f" {row['baseline']['turns']}t/{row['baseline']['uncached_prompt_tokens']:>6}tok"
                f"/{row['baseline']['seconds']:.0f}s",
                flush=True,
            )
    finally:
        _git(args.repo, "checkout", "-q", "--force", original)

    if not rows:
        raise SystemExit("no case reproduced a failure to fix")

    def summary(arm: str) -> dict[str, Any]:
        done = [r for r in rows if r[arm]["passed"]]
        return {
            "passed": len(done),
            "cases": len(rows),
            "turns": round(sum(r[arm]["turns"] for r in rows) / len(rows), 2),
            "edits": round(sum(r[arm]["edits"] for r in rows) / len(rows), 2),
            "greps": round(sum(r[arm]["greps"] for r in rows) / len(rows), 2),
            "reads": round(sum(r[arm]["reads"] for r in rows) / len(rows), 2),
            "uncached_prompt_tokens": round(
                sum(r[arm]["uncached_prompt_tokens"] for r in rows) / len(rows), 1
            ),
            "seconds": round(sum(r[arm]["seconds"] for r in rows) / len(rows), 1),
            # Only comparable where the arm actually finished.
            "tokens_per_pass": (
                round(sum(r[arm]["uncached_prompt_tokens"] for r in done) / len(done), 1)
                if done
                else None
            ),
            "seconds_per_pass": (
                round(sum(r[arm]["seconds"] for r in done) / len(done), 1) if done else None
            ),
        }

    payload = {
        "classification": "C2_CODE_GENERATION_DIAGNOSTIC",
        "note": (
            "Diagnostic. The sealed local-practical arm is port-8090; this endpoint is a "
            "different route and is not recorded as B0b/C2 evidence."
        ),
        "captured_at": datetime.now(UTC).isoformat(),
        "repository": str(args.repo),
        "model": args.model,
        "max_turns": args.max_turns,
        "summary": {arm: summary(arm) for arm in ("pi", "baseline")},
        "results": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
