#!/usr/bin/env python3
"""Turn the revert oracle's findings into a corpus whose required tests really verify.

`c2_pr_oracle.py` builds cases whose required tests are the test files a commit edited.
Measured by `c2_revert_oracle.py`, that set names a non-detecting file in 11.9% of commits
and misses a detecting one in 2.4%. Recall against it is therefore understated, and the
understatement is not uniform across cases.

This builds the same corpus shape from the tests that were observed to fail when the
change was taken away. Where the cheap oracle asks "which tests did the author touch",
this asks "which tests would have caught it", and only the second is what selection is for.

Cases are dropped rather than adjusted when the Twin cannot answer for them: a detecting
test that did not exist at the base commit is not something evidence selection could have
found, and counting it would measure history rather than selection.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True)


def _files_at(repo: Path, commit: str) -> frozenset[str]:
    return frozenset(_git(repo, "ls-tree", "-r", "--name-only", commit).split())


def build(repo: Path, findings: Path, base: str | None) -> dict[str, Any]:
    payload = json.loads(findings.read_text())
    usable = [
        result
        for result in payload["results"]
        if not result["undetected"] and not result["wholesale_breakage"]
    ]
    if not usable:
        raise SystemExit(f"{findings} holds no case with a focused detecting test")

    # The oldest measured commit fixes the base, so every case is drawn from a later one.
    oldest = usable[-1]["sha"]
    base_sha = _git(repo, "rev-parse", base or f"{oldest}~1").strip()
    present = _files_at(repo, base_sha)

    cases: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for result in usable:
        sha = result["sha"]
        changed = [
            path
            for path in _git(repo, "show", "--name-only", "--format=", sha).split()
            if path.endswith(".py") and path not in set(result["edited_test_files"])
        ]
        sources = [path for path in changed if path in present]
        required = [path for path in result["detecting_files"] if path in present]
        missing = sorted(set(result["detecting_files"]) - present)
        if not sources or not required:
            dropped.append({"sha": sha, "reason": "nothing to select from at the base"})
            continue
        if missing:
            # A test written by the commit itself cannot be selected from the base Twin.
            dropped.append({"sha": sha, "reason": "a detecting test postdates the base"})
            continue
        named = ", ".join(sources[:3]) + ("" if len(sources) <= 3 else ", ...")
        cases.append(
            {
                "case_id": f"revert-{sha}",
                "task_class": "test_selection",
                "pi_value_class": "high",
                "split": "tuning",
                "objective": (
                    f"Select the existing tests that must run for a change to {named}. "
                    "Do not edit source."
                ),
                "target_refs": [f"file://{path}" for path in sources],
                "required_facts": required,
                "metadata": {
                    "oracle": "revert_observed_failure",
                    "commit": sha,
                    "subject": result["subject"],
                    "detecting_test_count": len(result["detecting_tests"]),
                    "cheap_oracle_would_have_missed": result["missed_by_cheap_oracle"],
                    "cheap_oracle_would_have_added": result["spurious_in_cheap_oracle"],
                },
            }
        )

    return {
        "schema": 1,
        "classification": "C2_RECALL_CORPUS",
        "generated_at": datetime.now(UTC).isoformat(),
        "repository": {
            "path": str(repo),
            "commit": base_sha,
            "origin": _git(repo, "remote", "get-url", "origin").strip(),
            "note": "Twin is built at this base; every case is drawn from a later commit.",
        },
        "bounds": {
            "required_tests": "observed - a test that failed when the change was removed",
            "changed_sources": "upper bound - real commits bundle unrelated edits",
        },
        "dropped": dropped,
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--findings", type=Path, required=True)
    parser.add_argument("--base", default=None)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build(args.repo, args.findings, args.base)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(
        f"{len(payload['cases'])} cases, {len(payload['dropped'])} dropped, "
        f"base {payload['repository']['commit'][:12]}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
