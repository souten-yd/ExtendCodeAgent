#!/usr/bin/env python3
"""Build the thing that was asked for, without being told where it goes.

The bug-fix benchmark hands the agent the failing tests and the file to change, which is
most of the work in a real change. What is left is patching a location someone else found,
and that is the case where evidence about a project matters least.

Here the agent gets what a person would have got: the sentence the author wrote in the
changelog. Not the tests, not the file list, not the diff. It has to decide where the change
belongs, follow the conventions already in the project, and know how to run anything.

Scoring is unchanged and still does not read the diff: the tests the revert oracle observed
to detect the change are run, and a different correct implementation passes. That is also
the sharpest limit here — the hidden tests were written against the author's design, so an
implementation that is reasonable and shaped differently can fail. Cases whose description
gives the answer away are as much a problem in the other direction, and are filtered by hand
rather than by a rule that pretends to be objective.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from c2_codegen_bench import (  # noqa: E402
    _git,
    is_test_path,
    run_tests,
)

#: Sphinx roles and directives in a changelog line, which say nothing to an agent.
_ROLE = re.compile(r":(?:issue|pr|ref|class|meth|attr|data|func|mod):`([^`]*)`")


def described_change(repo: Path, sha: str) -> str:
    """The sentence the author wrote for people, with the markup taken out."""

    diff = _git(repo, "show", sha, "--", "CHANGES.rst")
    lines = [
        line[1:].strip()
        for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++") and line[1:].strip()
    ]
    text = " ".join(lines)
    text = _ROLE.sub(r"\1", text)
    text = text.replace("``", "`").lstrip("- ").strip()
    # Version headers and dates are bookkeeping, not a request.
    return re.sub(r"^Version [\d.]+\s*-+\s*(Unreleased|Released \d{4}-\d\d-\d\d)\s*", "", text)


@dataclass(frozen=True)
class FeatureCase:
    case_id: str
    commit: str
    description: str
    detecting: tuple[str, ...]
    #: Where it actually went. Never shown to the agent; kept for reporting only.
    production: tuple[str, ...]


def cases_from(repo: Path, findings: Path, limit: int) -> list[FeatureCase]:
    payload = json.loads(findings.read_text())
    out: list[FeatureCase] = []
    for result in payload["results"]:
        if result["undetected"] or result["wholesale_breakage"]:
            continue
        sha = result["sha"]
        description = described_change(repo, sha)
        if not description:
            continue
        production = tuple(
            path
            for path in _git(repo, "show", "--name-only", "--format=", sha).split()
            if path.endswith(".py") and not is_test_path(path)
        )
        if not production:
            continue
        out.append(
            FeatureCase(
                case_id=f"feat-{sha}",
                commit=sha,
                description=description,
                detecting=tuple(result["detecting_tests"]),
                production=production,
            )
        )
        if len(out) >= limit:
            break
    return out


def undo(repo: Path, case: FeatureCase) -> tuple[str, ...]:
    """Put the production half back, leaving the tests. The agent is not told which files."""

    _git(repo, "checkout", "-q", "--force", case.commit)
    undone = []
    for path in case.production:
        try:
            _git(repo, "checkout", "-q", f"{case.commit}~1", "--", path)
            undone.append(path)
        except subprocess.CalledProcessError:
            (repo / path).unlink(missing_ok=True)
            undone.append(path)
    return tuple(undone)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--findings", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    original = _git(args.repo, "rev-parse", "HEAD").strip()
    rows = []
    try:
        for case in cases_from(args.repo, args.findings, args.limit):
            undone = undo(args.repo, case)
            broken, _ = run_tests(args.repo, args.python, case.detecting[:8], 300)
            rows.append(
                {
                    "case_id": case.case_id,
                    "description": case.description,
                    "reproduces": not broken,
                    "hidden_files": list(undone),
                    "hidden_tests": list(case.detecting[:4]),
                }
            )
            mark = "ok " if not broken else "no "
            print(f"  {mark}{case.case_id}  {case.description[:88]}", flush=True)
    finally:
        _git(args.repo, "checkout", "-q", "--force", original)

    payload = {
        "classification": "C2_FEATURE_TASK_CORPUS",
        "execution_scope": "local-only",
        "model_execution": "NOT_RUN_DETERMINISTIC_MEASUREMENT",
        "repository": str(args.repo),
        "cases": len(rows),
        "reproducing": sum(1 for r in rows if r["reproduces"]),
        "results": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in payload.items() if k != "results"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
