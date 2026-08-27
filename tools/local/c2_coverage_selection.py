#!/usr/bin/env python3
"""Whether execution recovers the verification relation the graph cannot hold, and at what width.

Measured against the revert oracle, evidence selection recovers half of httpx's detecting
tests. The misses are not mis-ranked; they are absent. `tests/models/test_url.py` imports
`httpx` and nothing else, so no import or call edge reaches `httpx/_urlparse.py`, and six of
thirteen misses are that one file.

Coverage holds the pair the graph cannot. The question this answers is what it costs, since
a relation wide enough to recover everything selects everything: at file granularity 269
tests execute the average changed file, which is a third of the suite.

So it compares two widths of the same question -- which tests executed the changed file,
and which executed the changed functions -- against the tests observed to detect the change.
Run it after a coverage run made with `dynamic_context = test_function`.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
from pathlib import Path

import coverage


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


def _changed_functions(repo: Path, sha: str, path: str) -> set[str]:
    """Functions whose body differs from the parent, by name."""

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


def _context_files(contexts: set[str]) -> set[str]:
    """`tests.models.test_url.test_idna` names a file; recover it."""

    return {context.rsplit(".", 1)[0].replace(".", "/") + ".py" for context in contexts if context}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--coverage-data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    corpus = json.loads(args.corpus.read_text())
    base = corpus["repository"]["commit"]
    reader = coverage.Coverage(data_file=str(args.coverage_data))
    reader.load()
    data = reader.get_data()
    measured = {name.split(f"/{args.repo.name}/")[-1]: name for name in data.measured_files()}

    results = []
    for case in corpus["cases"]:
        sha = case["metadata"]["commit"]
        required = set(case["required_facts"])
        paths = [ref.removeprefix("file://") for ref in case["target_refs"]]
        spans: dict[str, list[tuple[int, int]]] = {}
        for path in paths:
            names = _changed_functions(args.repo, sha, path)
            if not names:
                continue
            try:
                at_base = _functions(_git(args.repo, "show", f"{base}:{path}"))
            except subprocess.CalledProcessError:
                continue
            spans[path] = [at_base[name] for name in names if name in at_base]
        if not spans:
            continue

        by_file: set[str] = set()
        by_symbol: set[str] = set()
        for path in paths:
            key = measured.get(path)
            if key is None:
                continue
            for line, contexts in data.contexts_by_lineno(key).items():
                present = {context for context in contexts if context}
                by_file |= present
                if any(start <= line <= end for start, end in spans.get(path, ())):
                    by_symbol |= present
        results.append(
            {
                "case_id": case["case_id"],
                "required": sorted(required),
                "file_candidates": len(by_file),
                "symbol_candidates": len(by_symbol),
                "file_recovers": bool(required & _context_files(by_file)),
                "symbol_recovers": bool(required & _context_files(by_symbol)),
            }
        )

    total = len(results)
    payload = {
        "classification": "C2_COVERAGE_SELECTION_WIDTH",
        "execution_scope": "local-only",
        "model_execution": "NOT_RUN_DETERMINISTIC_MEASUREMENT",
        "repository": str(args.repo),
        "base": base,
        "cases": total,
        "mean_file_candidates": round(sum(r["file_candidates"] for r in results) / total, 1),
        "mean_symbol_candidates": round(sum(r["symbol_candidates"] for r in results) / total, 1),
        "file_recall": round(sum(r["file_recovers"] for r in results) / total, 3),
        "symbol_recall": round(sum(r["symbol_recovers"] for r in results) / total, 3),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({k: v for k, v in payload.items() if k != "results"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
