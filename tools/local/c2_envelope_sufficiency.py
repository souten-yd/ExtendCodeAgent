#!/usr/bin/env python3
"""Does the envelope carry the code the change actually had to touch?

Running the two arms by hand answers this one case at a time and lets the person running
them carry knowledge between the arms. This asks the same question of every case at once
and cannot be contaminated: for each commit, the functions its production diff modified are
known, and either their bodies are in the initial envelope or they are not.

It is not a claim that an agent will succeed. It is the precondition for one — an arm that
was never given the code cannot be said to have failed at writing it.
"""

from __future__ import annotations

import argparse
import ast
import inspect
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from c2_codegen_bench import (  # noqa: E402
    Case,
    break_repository,
    build_envelope,
    executed_at_commit,
)
from c2_revert_oracle import is_test_path  # noqa: E402

from extendcodeagent.context import attach_excerpts  # noqa: E402

# Read, not repeated: this said "over the 120-line limit" after the limit became 400.
EXCERPT_LINE_LIMIT = inspect.signature(attach_excerpts).parameters["max_lines"].default


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True, errors="replace")


def _functions(source: str) -> dict[str, tuple[int, int]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    return {
        node.name: (node.lineno, node.end_lineno or node.lineno)
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }


def touched_functions(repo: Path, sha: str, path: str) -> set[str]:
    """Functions whose body the commit changed, and whether it changed anything outside one."""

    try:
        after, before = _git(repo, "show", f"{sha}:{path}"), _git(repo, "show", f"{sha}~1:{path}")
    except subprocess.CalledProcessError:
        return set()
    now, then = _functions(after), _functions(before)
    after_lines, before_lines = after.splitlines(), before.splitlines()
    changed = set()
    for name, (start, end) in now.items():
        if name not in then:
            changed.add(name)
            continue
        old_start, old_end = then[name]
        if after_lines[start - 1 : end] != before_lines[old_start - 1 : old_end]:
            changed.add(name)
    return changed


def _span_of(repo: Path, paths: tuple[str, ...], name: str) -> int | None:
    """How many lines the function occupies in the working tree, or None if it is not there."""

    for path in paths:
        try:
            source = (repo / path).read_text(errors="replace")
        except OSError:
            continue
        found = _functions(source).get(name)
        if found:
            return found[1] - found[0] + 1
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--findings", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.findings.read_text())
    usable = [r for r in payload["results"] if not r["undetected"] and not r["wholesale_breakage"]]
    original = _git(args.repo, "rev-parse", "HEAD").strip()
    rows = []
    try:
        for result in usable:
            sha = result["sha"]
            case = Case(f"s-{sha}", sha, result["subject"], (), tuple(result["detecting_tests"]))
            _git(args.repo, "checkout", "-q", "--force", sha)
            executed = executed_at_commit(args.repo, args.python, case, 300)
            reverted = break_repository(args.repo, case)
            if not reverted:
                continue
            wanted: set[str] = set()
            for path in reverted:
                if not is_test_path(path):
                    wanted |= touched_functions(args.repo, sha, path)
            if not wanted:
                # Module-level only: no function body to carry, so the question does not apply.
                rows.append({"sha": sha, "subject": result["subject"], "applicable": False})
                continue
            envelope = json.loads(build_envelope(args.repo, case, reverted, executed))
            items = envelope.get("items", [])
            with_source = {
                str(item.get("summary", "")).rsplit(".", 1)[-1]
                for item in items
                if item.get("source")
            }
            named = {str(item.get("summary", "")).rsplit(".", 1)[-1] for item in items}
            # Why each missing body is missing. `lines` is not emitted for a role-shaped
            # item, so the span has to come from the source, not from the payload - reading
            # it from the payload said every target had no span and sent me after the wrong
            # cause twice.
            reasons: dict[str, str] = {}
            for name in sorted(wanted - with_source):
                span = _span_of(args.repo, reverted, name)
                if span is None:
                    reasons[name] = "not found in the changed files"
                elif span > EXCERPT_LINE_LIMIT:
                    reasons[name] = f"{span} lines, over the {EXCERPT_LINE_LIMIT}-line limit"
                elif name not in named:
                    reasons[name] = "not selected into the envelope"
                else:
                    reasons[name] = "selected, and the excerpt allowance ran out"
            rows.append(
                {
                    "sha": sha,
                    "subject": result["subject"][:44],
                    "applicable": True,
                    "functions_changed": sorted(wanted),
                    "carried_as_source": sorted(wanted & with_source),
                    "named_only": sorted((wanted & named) - with_source),
                    "absent": sorted(wanted - named),
                    "why_missing": reasons,
                    "items": len(items),
                    "items_with_source": sum(1 for item in items if item.get("source")),
                }
            )
            print(
                f"  {sha}  source {len(wanted & with_source)}/{len(wanted)}"
                f"  named {len(wanted & named)}/{len(wanted)}  {result['subject'][:38]}",
                flush=True,
            )
    finally:
        _git(args.repo, "checkout", "-q", "--force", original)

    applicable = [r for r in rows if r["applicable"]]
    complete = [r for r in applicable if not r.get("why_missing")]
    partial = [r for r in applicable if r["carried_as_source"] and r not in complete]
    result = {
        "classification": "C2_ENVELOPE_SUFFICIENCY",
        "execution_scope": "local-only",
        "model_execution": "NOT_RUN_DETERMINISTIC_MEASUREMENT",
        "repository": str(args.repo),
        "cases": len(rows),
        "applicable": len(applicable),
        "every_changed_function_carried_as_source": len(complete),
        "some_carried": len(partial),
        "none_carried": len(applicable) - len(complete) - len(partial),
        "results": rows,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "results"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
