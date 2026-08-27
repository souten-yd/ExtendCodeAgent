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
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from extendcodeagent.core.config import ConfigLayer, ConfigResolver  # noqa: E402
from extendcodeagent.core.config.schema import CONFIGURABLE_CAPABILITIES  # noqa: E402
from extendcodeagent.core.policy import CapabilityPolicy  # noqa: E402
from extendcodeagent.runtime import symbols_touched  # noqa: E402
from extendcodeagent.service.application import ProjectIntelligenceApplication  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c2_revert_oracle import is_test_path  # noqa: E402


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
  WRITE <path>::<function>
  <the complete source of that function, correctly indented>
  END
  EDIT <path>
  <<<OLD
  <text to find, exactly as it appears, including indentation>
  ===
  <text to put in its place>
  >>>NEW

WRITE replaces that function, or adds it to the file if it is not there yet. EDIT replaces
one exact passage anywhere in the file, which is how an import, a decorator or a line
outside any function gets changed.

After each WRITE or EDIT the tests are run and you are told the result. Do not explain.
Change production code only. The tests are correct; do not edit them.

You have a limited number of steps and are told how many remain. Searching costs a step,
so stop searching and write once you can see what the change must be.
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


def break_repository(repo: Path, case: Case) -> tuple[str, ...]:
    """Put the commit's production half back, leaving its tests. Returns what was reverted."""

    _git(repo, "checkout", "-q", "--force", case.commit)
    changed = [
        path
        for path in _git(repo, "show", "--name-only", "--format=", case.commit).split()
        # The oracle's own rule, not a substring check: `src/flask/testing.py` is production
        # and was being taken for a test file, which silently dropped two of seventeen cases
        # and left the repository unbroken for them.
        if path.endswith(".py") and not is_test_path(path)
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


def _can_append(tree: ast.Module, name: str) -> bool:
    """A name that is not there yet can still be written; adding one is ordinary work.

    Refusing additions left half the corpus unscored -- two of every four flask cases -- and
    what it scored was the action vocabulary rather than the agent.
    """

    return name.isidentifier()


def replace_function(repo: Path, path: str, name: str, source: str) -> str:
    """Put the model's function into the file, replacing or adding it.

    Returns a message for the model, because a rejection it cannot read is a turn wasted.
    """

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
    if name not in spans and not _can_append(tree, name):
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
    lines = text.splitlines()
    written = source.splitlines()
    if name not in spans:
        # Adding a function is ordinary work. Refusing it left half the flask corpus
        # unscored, which measured the action vocabulary rather than the agent.
        blank = [""] if lines and lines[-1].strip() else []
        target.write_text("\n".join([*lines, *blank, *written]) + "\n")
        return "applied"

    span_start, span_end = spans[name]
    # Shift the block to where the function actually sits, keeping the relative indentation
    # the model wrote. A method returned at column zero is valid Python in the wrong place,
    # and the file then stops parsing for a reason that is not the model's mistake.
    indent = len(lines[span_start - 1]) - len(lines[span_start - 1].lstrip())
    shift = max(indent - (len(written[0]) - len(written[0].lstrip())), 0)
    body = [(" " * shift + line) if line.strip() else "" for line in written]
    target.write_text("\n".join([*lines[: span_start - 1], *body, *lines[span_end:]]) + "\n")
    return "applied"


def _api_key() -> str | None:
    """The gateway key, from the environment or from a file named by it.

    A file, because a shell export does not survive between processes and a key on a command
    line reaches the process table and the logs. Whatever supplies it, the value is read here
    and nowhere else.
    """

    direct = os.environ.get("ECA_LLM_API_KEY")
    if direct:
        return direct.strip()
    path = os.environ.get("ECA_LLM_API_KEY_FILE")
    if path and Path(path).is_file():
        return Path(path).read_text().strip() or None
    return None


def apply_edit(repo: Path, path: str, body: str) -> str:
    """Replace one exact passage. Returns a message for the model, never a silent failure."""

    target = repo / path
    if not target.is_file():
        return f"no such file: {path}"
    if "<<<OLD" not in body or "===" not in body:
        return "an EDIT needs <<<OLD, then ===, then the replacement"
    _, _, rest = body.partition("<<<OLD")
    old, _, new = rest.partition("===")
    old = old.strip("\n")
    new = new.split(">>>NEW")[0].strip("\n")
    text = target.read_text(errors="replace")
    if not old.strip():
        return "the text to find was empty"
    if old not in text:
        # Reported rather than guessed at: a near-miss silently applied is a wrong edit the
        # agent cannot see, and it would spend its remaining turns on the consequences.
        return f"that exact text is not in {path}"
    if text.count(old) > 1:
        return f"that text appears {text.count(old)} times in {path}; include more context"
    updated = text.replace(old, new, 1)
    try:
        ast.parse(updated)
    except SyntaxError as error:
        return f"the result would not parse: {error}"
    target.write_text(updated)
    return "applied"


def complete(endpoint: str, model: str, messages: list[dict[str, str]], max_tokens: int) -> Any:
    # The key is read from the environment so it never travels through a prompt, a log or
    # a command line. A gateway that wants none is unaffected.
    headers = {"Content-Type": "application/json"}
    key = _api_key()
    if key:
        headers["Authorization"] = f"Bearer {key}"
        headers["X-API-Key"] = key
    request = urllib.request.Request(
        f"{endpoint.rstrip('/')}/chat/completions",
        data=json.dumps(
            {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0}
        ).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
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


_WRITE = re.compile(r"^\s*(?:REPLACE|WRITE)\s+(\S+?)::(\S+?)\s*$", re.M)
# Exact-passage replacement. Without it 9 of 17 flask cases could not be written at all:
# the IPv6 fix needs `from urllib.parse import urlsplit` added at the top of the file, and
# a vocabulary that only replaces function bodies cannot say that. Scoring an agent on a
# change it has no way to express measures the protocol.
#: (evidence, kind) -> a fresh envelope, or None when there is nothing new to say.
ReissueEnvelope = Callable[[str, str], str | None]

_EDIT = re.compile(r"^\s*EDIT\s+(\S+)\s*$", re.M)


def run_arm(
    repo: Path,
    python: Path,
    case: Case,
    reverted: tuple[str, ...],
    endpoint: str,
    model: str,
    *,
    envelope: str | None,
    reissue: ReissueEnvelope | None,
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

    for index in range(max_turns):
        remaining = max_turns - index
        messages[-1] = {
            "role": messages[-1]["role"],
            "content": f"{messages[-1]['content']}\n\n[{remaining} steps remain]",
        }
        started = time.monotonic()
        text, fresh = complete(endpoint, model, messages, max_output)
        seconds += time.monotonic() - started
        uncached += fresh
        messages.append({"role": "assistant", "content": text[:4_000]})

        edit = _EDIT.search(text)
        if edit and "<<<OLD" in text:
            actions.append("edit")
            note = apply_edit(repo, edit.group(1), text[edit.end() :])
            edits += 1
            if note == "applied":
                passed, output = run_tests(repo, python, case.detecting[:8], test_timeout)
                if passed:
                    break
                note = f"tests still fail:\n{output}"
                # A test failure is the most informative thing this loop produces, and the
                # envelope was written before it existed. Re-issued here, the allowance moves
                # from naming the file to the code the failure points at.
                if reissue is not None:
                    fresh = reissue(output, "failure")
                    if fresh:
                        note += f"\n\n### PROJECT INTELLIGENCE (updated)\n{fresh}\n"
            messages.append({"role": "user", "content": note[:MAX_READ]})
            continue

        match = _WRITE.search(text)
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
                if reissue is not None:
                    fresh = reissue(output, "failure")
                    if fresh:
                        note += f"\n\n### PROJECT INTELLIGENCE (updated)\n{fresh}\n"
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
            # The search is the agent saying what it needs; the envelope answers it.
            if reissue is not None and found.stdout:
                fresh = reissue(found.stdout, "search")
                if fresh:
                    body += f"\n\n### PROJECT INTELLIGENCE (updated)\n{fresh}\n"
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
            body = "Reply with one action: GREP, READ, or WRITE <path>::<function>."
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


def executed_at_commit(repo: Path, python: Path, case: Case, timeout: int) -> tuple[str, ...]:
    """Canonical refs the detecting tests run *while they still pass*.

    Coverage has to be taken here, before the change is taken away. A failing test truncates
    its own run - the one that proves `Flask.url_for` is broken raises at the call and never
    enters the body - so the broken state names everything except the code in question. Line
    numbers are the second reason: a database built at the fixed revision maps onto spans the
    reverted file does not have.

    Assumes the repository is at the commit, which is the only point where both hold.
    """

    with tempfile.TemporaryDirectory(prefix="eca-cov-") as temp:
        config = Path(temp) / "coveragerc"
        # dynamic_context has no command-line form, so the setting travels in a file.
        config.write_text("[run]\ndynamic_context = test_function\nsource = .\n")
        data_file = Path(temp) / "coverage.db"
        try:
            subprocess.run(
                [
                    str(python),
                    "-m",
                    "coverage",
                    "run",
                    f"--rcfile={config}",
                    f"--data-file={data_file}",
                    "-m",
                    "pytest",
                    "-q",
                    "--no-header",
                    "--tb=no",
                    *case.detecting[:8],
                ],
                cwd=repo,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except (subprocess.TimeoutExpired, OSError):
            return ()
        return _symbols_from(repo, data_file, case.detecting)


def _symbols_from(repo: Path, coverage_data: Path, tests: tuple[str, ...]) -> tuple[str, ...]:
    if not coverage_data.is_file():
        return ()
    try:
        import coverage as coverage_lib
    except ImportError:
        return ()
    reader = coverage_lib.Coverage(data_file=str(coverage_data))
    reader.load()
    data = reader.get_data()
    names = {test.rsplit("::", 1)[-1] for test in tests}
    executed: dict[str, set[int]] = {}
    for measured in data.measured_files():
        relative = measured.split(f"/{repo.name}/")[-1]
        for line, contexts in data.contexts_by_lineno(measured).items():
            if any(context.rsplit(".", 1)[-1] in names for context in contexts if context):
                executed.setdefault(relative, set()).add(line)
    if not executed:
        return ()
    with (
        tempfile.TemporaryDirectory(prefix="eca-cov-") as temp,
        ProjectIntelligenceApplication(repo, Path(temp) / "graph.db", _policy()) as application,
    ):
        snapshot = application._snapshot(open_if_missing=True)
        return tuple(ref.value for ref in symbols_touched(snapshot, executed))


_TRACEBACK_FRAME = re.compile(r"^\s*([\w./-]+\.py):(\d+): in (\w+)", re.M)


def refs_from_search(repo: Path, pattern: str, hits: str) -> tuple[str, ...]:
    """Canonical refs a search turned up, as the agent's own statement of what it needs.

    After one search the agent knows something the envelope was written without: where it
    thinks the answer is. Waiting for a failed edit to re-issue throws that away, and the
    arm with no envelope was at least keeping what its searches returned.

    The search argument is the request; the files and lines it matched are the answer.
    """

    executed: dict[str, set[int]] = {}
    for line in hits.splitlines():
        path, _, rest = line.partition(":")
        number, _, _ = rest.partition(":")
        if not number.isdigit() or not path.endswith(".py") or is_test_path(path):
            continue
        executed.setdefault(path.removeprefix("./"), set()).add(int(number))
    if not executed:
        return ()
    with (
        tempfile.TemporaryDirectory(prefix="eca-search-") as temp,
        ProjectIntelligenceApplication(repo, Path(temp) / "graph.db", _policy()) as application,
    ):
        snapshot = application._snapshot(open_if_missing=True)
        return tuple(ref.value for ref in symbols_touched(snapshot, executed))


def refs_from_failure(repo: Path, output: str) -> tuple[str, ...]:
    """Canonical refs the failure names, read out of the traceback.

    The first envelope is written before any test has run, so it can only guess which of a
    file's members matter. A failure is not a guess: it names the file, the line and the
    frame, and re-issuing against that moves the allowance onto the code the failure points
    at rather than the code the file happens to define first.
    """

    frames = _TRACEBACK_FRAME.findall(output)
    if not frames:
        return ()
    executed: dict[str, set[int]] = {}
    for path, line, _ in frames:
        if is_test_path(path):
            continue
        executed.setdefault(path, set()).add(int(line))
    if not executed:
        return ()
    with (
        tempfile.TemporaryDirectory(prefix="eca-fail-") as temp,
        ProjectIntelligenceApplication(repo, Path(temp) / "graph.db", _policy()) as application,
    ):
        snapshot = application._snapshot(open_if_missing=True)
        return tuple(ref.value for ref in symbols_touched(snapshot, executed))


def build_envelope(
    repo: Path,
    case: Case,
    reverted: tuple[str, ...],
    executed: tuple[str, ...] = (),
    token_budget: int = 8_192,
) -> str:
    objective = f"Change {', '.join(reverted)} so that the failing tests pass: {case.subject}"
    with (
        tempfile.TemporaryDirectory(prefix="eca-gen-") as temp,
        ProjectIntelligenceApplication(repo, Path(temp) / "graph.db", _policy()) as application,
    ):
        application._snapshot(open_if_missing=True)
        payload = application.context(
            objective,
            [f"file://{path}" for path in reverted],
            token_budget=token_budget,
            view="envelope",
            executed_by_failing_tests=executed,
            # Declared, because this benchmark exists to ask for a change. Omitting it left
            # the arm with names and no source, which is the state the whole preflight was
            # built to catch — and the preflight was wired while this caller was not.
            changing=True,
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
    parser.add_argument(
        "--coverage-data",
        type=Path,
        default=None,
        help="a coverage database with dynamic_context=test_function, to rank bodies",
    )
    parser.add_argument("--budget", type=int, default=8_192)
    parser.add_argument(
        "--arms",
        choices=("both", "pi", "baseline", "wrong"),
        default="both",
        help=(
            "run one arm alone, to ask whether it converges given more budget rather "
            "than whether it is faster than the other"
        ),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    original = _git(args.repo, "rev-parse", "HEAD").strip()
    rows: list[dict[str, Any]] = []
    previous_envelope: str | None = None
    try:
        for case in cases_from(args.findings, args.limit):
            # Coverage first: it is only meaningful while the tests still pass.
            _git(args.repo, "checkout", "-q", "--force", case.commit)
            executed = executed_at_commit(args.repo, args.python, case, args.test_timeout)
            reverted = break_repository(args.repo, case)
            if not reverted:
                print(f"  {case.case_id} skipped: nothing production to revert", flush=True)
                continue
            broken, _ = run_tests(args.repo, args.python, case.detecting[:8], args.test_timeout)
            if broken:
                # Nothing to fix: the revert did not reproduce the failure here.
                print(f"  {case.case_id} skipped: tests pass with the change removed", flush=True)
                continue
            # Building one for a run that will not use it costs a Twin build per case.
            envelope = (
                build_envelope(args.repo, case, reverted, executed, args.budget)
                if args.arms != "baseline"
                else None
            )

            def reissue(
                output: str, _case: Case = case, _rev: tuple[str, ...] = reverted
            ) -> str | None:
                named = refs_from_failure(args.repo, output)
                if not named:
                    return None
                return build_envelope(args.repo, _case, _rev, named)

            row: dict[str, Any] = {"case_id": case.case_id, "subject": case.subject}
            # The control. Same shape, same construction, same size, other case's content:
            # if it scores like the real one, the model is being helped by the length of the
            # prompt rather than by what is in it, and none of the rest means what it looks
            # like it means.
            arms = (
                ("pi", envelope),
                ("baseline", None),
                ("wrong", previous_envelope if args.arms in ("both", "wrong") else None),
            )
            previous_envelope = envelope or previous_envelope
            if args.arms != "both":
                arms = tuple(item for item in arms if item[0] == args.arms)
            elif previous_envelope is None:
                # Nothing to be wrong with yet on the first case.
                arms = tuple(item for item in arms if item[0] != "wrong")
            for arm, given in arms:
                break_repository(args.repo, case)
                row[arm] = run_arm(
                    args.repo,
                    args.python,
                    case,
                    reverted,
                    args.endpoint,
                    args.model,
                    envelope=given,
                    # A fresh envelope only where the envelope is the real one; the
                    # control must stay wrong for the whole run.
                    reissue=reissue if arm == "pi" else None,
                    max_turns=args.max_turns,
                    max_output=args.max_output,
                    test_timeout=args.test_timeout,
                )
            rows.append(row)
            if args.arms != "both":
                item = row[args.arms]
                print(
                    f"  {case.case_id:18} {args.arms} "
                    f"{'PASS' if item['passed'] else 'fail'} {item['turns']}t/"
                    f"{item['uncached_prompt_tokens']:>6}tok/{item['seconds']:.0f}s",
                    flush=True,
                )
                rows.append(row)
                continue
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
        "summary": {
            arm: summary(arm)
            for arm in (("pi", "baseline", "wrong") if args.arms == "both" else (args.arms,))
            if any(arm in item for item in rows)
        },
        "results": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
