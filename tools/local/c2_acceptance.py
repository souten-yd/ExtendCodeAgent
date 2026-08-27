#!/usr/bin/env python3
"""Score a change by what it must do, not by the shape the author gave it.

Using the author's tests as the oracle pins the design: an implementation that is reasonable
and shaped differently fails, which is fine while the task is "reproduce this patch" and
wrong once the task includes deciding what to build.

So each case carries acceptance criteria written from the description alone, before any
implementation is seen, and scoring is those criteria plus the project's own suite still
passing. Two implementations of `max_content_length can be customized per-request` - the
author's and one written here from the description - both satisfy the same three.

The criteria are written by whoever runs this, which is the honest weakness: the same person
scores both arms. It is stated rather than hidden, and the guard is that a criterion is
fixed before an implementation exists, phrased as behaviour a caller could observe.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Criterion:
    """One observable thing the change must make true.

    `check` is python run inside the repository under test. It asserts; anything it raises is
    a failure, and its text is reported so a near-miss can be told from a crash.
    """

    name: str
    check: str


@dataclass(frozen=True)
class AcceptanceCase:
    case_id: str
    commit: str
    description: str
    criteria: tuple[Criterion, ...]


def run_criterion(repo: Path, python: Path, criterion: Criterion, timeout: int = 120) -> str:
    process = subprocess.run(
        [str(python), "-c", criterion.check],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if process.returncode == 0:
        return "met"
    tail = (process.stderr or process.stdout).strip().splitlines()
    return tail[-1][:160] if tail else "failed with no output"


def suite_passes(repo: Path, python: Path, known_failures: int, timeout: int = 900) -> str:
    """Whether the project's own suite is no worse than it was before the change."""

    process = subprocess.run(
        [str(python), "-m", "pytest", "-q", "--no-header", "--tb=no", "-p", "no:cacheprovider"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    text = process.stdout + process.stderr
    failed = 0
    for line in text.splitlines():
        if " failed" in line and " passed" in line:
            failed = int(line.split(" failed")[0].strip().split()[-1])
            break
    if failed <= known_failures:
        return "met"
    return f"{failed} failing against {known_failures} before the change"


def score(repo: Path, python: Path, case: AcceptanceCase, known_failures: int) -> dict[str, object]:
    results = {c.name: run_criterion(repo, python, c) for c in case.criteria}
    results["no regression"] = suite_passes(repo, python, known_failures)
    met = sum(1 for v in results.values() if v == "met")
    return {
        "case_id": case.case_id,
        "met": met,
        "of": len(results),
        "passed": met == len(results),
        "detail": results,
    }


def load(path: Path) -> tuple[AcceptanceCase, ...]:
    payload = json.loads(path.read_text())
    return tuple(
        AcceptanceCase(
            case_id=item["case_id"],
            commit=item["commit"],
            description=item["description"],
            criteria=tuple(Criterion(c["name"], c["check"]) for c in item["criteria"]),
        )
        for item in payload["cases"]
    )
