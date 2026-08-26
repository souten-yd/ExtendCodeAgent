#!/usr/bin/env python3
"""Derive recall-corpus cases from a repository's own merged history.

Labelling external corpora by hand does not scale, and a merged change is already a
labelled example: the tests a real change touched are tests that a correct answer to
"what must be verified for this change?" had to name.

The Twin is pinned at a **base** commit and every case is drawn from a commit *after* it,
so PI is asked about a change it cannot see. A file that did not exist at the base is
dropped from the case: PI cannot be expected to name something absent from the project it
was given.

Two bounds that must be reported rather than averaged away:

- tests changed with a commit are a **lower** bound on the tests that had to run — real
  changes under-test;
- source files changed together are an **upper** bound on impact — real commits bundle
  unrelated edits.

Output is a corpus descriptor for tools/local/c2_evidence_recall.py --corpus.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class OracleError(RuntimeError):
    """The repository history cannot support a trustworthy oracle."""


@dataclass(frozen=True, slots=True)
class Change:
    commit: str
    subject: str
    sources: tuple[str, ...]
    tests: tuple[str, ...]


def _git(repository: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise OracleError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _files_at(repository: Path, commit: str) -> frozenset[str]:
    return frozenset(_git(repository, "ls-tree", "-r", "--name-only", commit).split("\n")) - {""}


def _is_test(path: str) -> bool:
    """A test is a file that runs assertions, not everything living under `tests/`.

    Counting `__init__.py`, `conftest.py` or a fixture server as a test that "must run"
    inflates the oracle with files no answer should have named.
    """

    name = Path(path).name
    if not name.endswith(".py"):
        return False
    return name.startswith("test_") or name.endswith("_test.py")


def _under_test_tree(path: str) -> bool:
    return path.startswith("test") or "/test" in path


def _changes(
    repository: Path, base: str, *, source_globs: tuple[str, ...], limit: int
) -> list[Change]:
    present = _files_at(repository, base)
    log = _git(
        repository,
        "log",
        "--no-merges",
        "--reverse",
        "--format=%x00%H%x00%s",
        "--name-only",
        f"{base}..HEAD",
    )
    changes: list[Change] = []
    commit = subject = ""
    touched: list[str] = []

    def flush() -> None:
        if not commit:
            return
        # Only files the base actually contains: PI cannot name what it was never shown.
        sources = tuple(
            sorted(
                path
                for path in touched
                if path in present
                and not _under_test_tree(path)
                and any(Path(path).match(pattern) for pattern in source_globs)
            )
        )
        tests = tuple(sorted(path for path in touched if path in present and _is_test(path)))
        if sources and tests:
            changes.append(Change(commit, subject, sources, tests))

    for line in log.split("\n"):
        if line.startswith("\0"):
            flush()
            if len(changes) >= limit:
                return changes[:limit]
            _, commit, subject = line.split("\0", 2)
            touched = []
        elif line.strip():
            touched.append(line.strip())
    flush()
    return changes[:limit]


def _case(change: Change) -> dict[str, Any]:
    named = ", ".join(change.sources[:3]) + ("" if len(change.sources) <= 3 else ", ...")
    return {
        "case_id": f"pr-{change.commit[:12]}",
        "task_class": "test_selection",
        "pi_value_class": "high",
        "split": "tuning",
        "objective": (
            f"Select the existing tests that must run for a change to {named}. Do not edit source."
        ),
        "target_refs": [f"file://{path}" for path in change.sources],
        "required_facts": list(change.tests),
        "metadata": {
            "oracle": "merged_change",
            "commit": change.commit,
            "subject": change.subject,
            "changed_source_count": len(change.sources),
            "required_tests_are_a_lower_bound": True,
        },
    }


def build(
    repository: Path, base: str, *, source_globs: tuple[str, ...], limit: int
) -> dict[str, Any]:
    base_sha = _git(repository, "rev-parse", base).strip()
    changes = _changes(repository, base_sha, source_globs=source_globs, limit=limit)
    if not changes:
        raise OracleError(
            f"no commit after {base_sha[:12]} changed both a source file and a test that "
            "already existed at the base"
        )
    return {
        "schema": 1,
        "classification": "C2_RECALL_CORPUS",
        "generated_at": datetime.now(UTC).isoformat(),
        "repository": {
            "path": str(repository),
            "commit": base_sha,
            "origin": _git(repository, "remote", "get-url", "origin").strip(),
            "note": "Twin is built at this base; every case is drawn from a later commit.",
        },
        "bounds": {
            "required_tests": "lower bound - real changes under-test",
            "changed_sources": "upper bound - real commits bundle unrelated edits",
        },
        "cases": [_case(change) for change in changes],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path)
    parser.add_argument("--base", default="HEAD~200", help="commit the Twin is built at")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument(
        "--source-glob",
        nargs="+",
        default=["*.py"],
        help="which changed files count as source",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    document = build(
        args.repository.expanduser().resolve(),
        args.base,
        source_globs=tuple(args.source_glob),
        limit=args.limit,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "base": document["repository"]["commit"],
                "cases": len(document["cases"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
