#!/usr/bin/env python3
"""Which tests actually detect a change, established by removing the change.

The corpus oracle in `c2_pr_oracle.py` calls a commit's required tests the test files that
commit edited, and says in its own output that this is a lower bound. It is also an upper
bound, and neither direction is measured: a commit's edited tests are not the same set as
the tests that would have caught the bug.

This measures the real relation instead. For a commit that changed both production code and
tests, the production half is put back to its parent state while the tests stay at the
commit. Whatever fails is, by construction, a test that detects that change. Nothing about
graphs, names or imports enters into it.

Three numbers come out, and they audit the cheap oracle directly:

- **missed** — detecting tests the commit did not edit, which the cheap oracle cannot see.
- **spurious** — tests the commit edited that do not detect the change.
- **undetected** — commits no test catches at all, which are a false-sufficient result for
  any selection built on top.

There is a fourth number because this oracle has a failure mode of its own. Reverting a
foundational change does not remove a behaviour, it removes an API, and then most of the
suite fails: on flask, three commits produced 237 to 474 failing tests across sixteen or
more files. Those cases say nothing about which tests verify what, so they are counted and
reported apart rather than averaged in.

Runs the suite twice per commit, so it wants a project whose tests are fast.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

_OUTCOME = re.compile(r"^(FAILED|ERROR)\s+(\S+?)(?:\s+-.*)?$", re.M)
_COLLECTED = re.compile(r"^collected (\d+) items?", re.M)
_TEST_PATH = re.compile(r"(^|/)(tests?|testing)/|(^|/)test_[^/]*\.py$|_test\.py$")


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True)


def is_test_path(path: str) -> bool:
    return path.endswith(".py") and bool(_TEST_PATH.search(path))


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    production: tuple[str, ...]
    tests: tuple[str, ...]


def candidate_commits(repo: Path, limit: int, skip_merges: bool = True) -> list[Commit]:
    """Commits that changed production code and tests together.

    These are the ones where the question has an answer: the tests are present to catch
    something, and the something can be taken away.
    """

    # A record separator of its own: git puts a blank line between the format line and
    # the file list, so splitting on blank lines cuts each commit in half.
    args = ["log", f"-{limit * 6}", "--format=%x01%H%x00%s", "--name-only"]
    if skip_merges:
        args.insert(1, "--no-merges")
    blocks = _git(repo, *args).split("\x01")
    found: list[Commit] = []
    for block in blocks:
        lines = [line for line in block.strip().splitlines() if line]
        if not lines or "\x00" not in lines[0]:
            continue
        sha, _, subject = lines[0].partition("\x00")
        paths = [p for p in lines[1:] if p.endswith(".py")]
        tests = tuple(p for p in paths if is_test_path(p))
        production = tuple(p for p in paths if not is_test_path(p))
        if tests and production:
            found.append(Commit(sha, subject, production, tests))
        if len(found) >= limit:
            break
    return found


def run_suite(repo: Path, python: Path, timeout: int) -> tuple[set[str], bool, int]:
    """Node ids that failed or errored, and whether the run completed at all."""

    process = subprocess.run(
        [
            str(python),
            "-m",
            "pytest",
            "--no-header",
            "--tb=no",
            "-rfE",
            "-p",
            "no:cacheprovider",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    output = process.stdout + process.stderr
    match = _COLLECTED.search(output)
    count = int(match.group(1)) if match else 0
    ran = "INTERNALERROR" not in output and "Interrupted" not in output and count > 0
    return {m.group(2) for m in _OUTCOME.finditer(output)}, ran, count


def _node_file(node_id: str) -> str:
    return node_id.split("::", 1)[0]


# Above this share of the suite, a revert has removed an API rather than a behaviour, and
# the failing set is no longer evidence about verification.
WHOLESALE_SHARE = 0.25


def measure(repo: Path, python: Path, commit: Commit, timeout: int) -> dict[str, object] | None:
    """Revert the production half, and see what notices."""

    _git(repo, "checkout", "-q", "--force", commit.sha)
    before, ok, collected = run_suite(repo, python, timeout)
    # A stable pre-existing failure is harmless, because the comparison subtracts it. What
    # cannot be measured is a commit whose own tests do not run here: if they are already
    # erroring, asking whether they detect the change has no answer. That is a fact about
    # the installed dependencies, not about the tests.
    if not ok or any(_node_file(node) in set(commit.tests) for node in before):
        return None
    # Put production files back as they were, leaving the commit's tests in place. A file
    # the commit created has no parent version, so it is removed rather than restored.
    for path in commit.production:
        try:
            _git(repo, "checkout", "-q", f"{commit.sha}~1", "--", path)
        except subprocess.CalledProcessError:
            (repo / path).unlink(missing_ok=True)
    after, ok, _ = run_suite(repo, python, timeout)
    _git(repo, "checkout", "-q", "--force", commit.sha)
    if not ok:
        return None

    detecting = after - before
    edited = set(commit.tests)
    detecting_files = {_node_file(node) for node in detecting}
    return {
        "wholesale_breakage": len(detecting) > max(1, int(collected * WHOLESALE_SHARE)),
        "sha": commit.sha[:12],
        "subject": commit.subject[:70],
        "edited_test_files": sorted(edited),
        "detecting_tests": sorted(detecting),
        "detecting_files": sorted(detecting_files),
        "missed_by_cheap_oracle": sorted(detecting_files - edited),
        "spurious_in_cheap_oracle": sorted(edited - detecting_files),
        "undetected": not detecting,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    original = _git(args.repo, "rev-parse", "HEAD").strip()
    commits = candidate_commits(args.repo, args.limit)
    print(f"{len(commits)} commits changed production and tests together", file=sys.stderr)

    results: list[dict[str, object]] = []
    try:
        for index, commit in enumerate(commits, 1):
            try:
                result = measure(args.repo, args.python, commit, args.timeout)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
                print(
                    f"  [{index}] {commit.sha[:8]} skipped: {type(error).__name__}", file=sys.stderr
                )
                continue
            if result is None:
                print(
                    f"  [{index}] {commit.sha[:8]} skipped: the commit's own tests do not run here",
                    file=sys.stderr,
                )
                continue
            results.append(result)
            print(
                f"  [{index}] {commit.sha[:8]} detects={len(result['detecting_tests']):3} "
                f"missed={len(result['missed_by_cheap_oracle'])} "
                f"spurious={len(result['spurious_in_cheap_oracle'])}",
                file=sys.stderr,
            )
    finally:
        _git(args.repo, "checkout", "-q", "--force", original)

    detected = [r for r in results if not r["undetected"]]
    wholesale = [r for r in detected if r["wholesale_breakage"]]
    # Only the focused cases carry information about which tests verify which change.
    usable = [r for r in detected if not r["wholesale_breakage"]]
    payload = {
        "classification": "C2_REVERT_BASED_VERIFICATION_ORACLE",
        "execution_scope": "local-only",
        "model_execution": "NOT_RUN_DETERMINISTIC_MEASUREMENT",
        "repository": str(args.repo),
        "revision": original,
        "commits_measured": len(results),
        "commits_with_a_detecting_test": len(detected),
        "commits_with_wholesale_breakage": len(wholesale),
        "commits_usable_as_ground_truth": len(usable),
        "undetected_rate": round(1 - len(detected) / len(results), 3) if results else None,
        "cheap_oracle_missed_a_file": round(
            sum(1 for r in usable if r["missed_by_cheap_oracle"]) / len(usable), 3
        )
        if usable
        else None,
        "cheap_oracle_named_a_non_detecting_file": round(
            sum(1 for r in usable if r["spurious_in_cheap_oracle"]) / len(usable), 3
        )
        if usable
        else None,
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({k: v for k, v in payload.items() if k != "results"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
