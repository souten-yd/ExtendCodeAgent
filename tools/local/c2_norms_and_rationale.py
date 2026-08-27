#!/usr/bin/env python3
"""Are a project's norms derivable, and is the reason for its code recoverable from it?

Two factors have been carried as unaddressed on the strength of being plausible rather than
measured: that an agent needs a project's conventions stated, and that it needs the
reasoning behind decisions. Both were assumed to resemble negative knowledge — a fact the
structural model cannot hold, so it must be stored. This asks whether they do.

They are separable by one question: can the fact be recomputed from the code?

**Norms.** A convention is a fact *about* positive facts, so it is derivable by counting
them. What matters is not whether a norm exists but how consistent it is: at 98% one
sibling shows an agent the pattern, and nothing needs storing; at 55% there is no norm to
state and storing one would assert a rule the project does not follow. So the measurement
is the dominant share of each convention, per repository.

**Rationale.** A reason is not derivable — no amount of reading current code recovers why an
alternative was rejected. But it may still be recorded in the code, as a comment. So the
measurement is how often a commit states a constraint that does not survive into the file
it changed, because only that residue is genuinely unrecoverable.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

# Phrasing that states a constraint rather than describing a change.
_CONSTRAINT = re.compile(
    r"\b(because|otherwise|must not|should not|do not|don't|avoid|"
    r"workaround|in order to|so that|keep .{0,20}in sync|instead of|"
    r"breaks? \w+|relies on|depends on|for backwards compat\w*)\b",
    re.I,
)
_WORD = re.compile(r"[a-z_][a-z0-9_]{3,}", re.I)


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True, errors="replace")


def _sources(repo: Path) -> list[Path]:
    tracked = _git(repo, "ls-files", "*.py").split()
    return [repo / path for path in tracked]


def norm_shares(repo: Path) -> dict[str, dict[str, object]]:
    """How consistently the project follows each of a few observable conventions."""

    counters: dict[str, Counter[str]] = {
        "test style": Counter(),
        "assertion style": Counter(),
        "import style": Counter(),
        "public function annotated": Counter(),
        "public function has docstring": Counter(),
    }
    for path in _sources(repo):
        try:
            tree = ast.parse(path.read_text(errors="replace"))
        except (SyntaxError, OSError, ValueError):
            continue
        is_test = "test" in path.name or "/tests/" in str(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and is_test:
                bases = {ast.unparse(base) for base in node.bases}
                if any("TestCase" in base for base in bases):
                    counters["test style"]["unittest.TestCase"] += 1
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                if is_test and node.name.startswith("test_"):
                    counters["test style"]["bare test_ function"] += 1
                if not node.name.startswith("_"):
                    annotated = node.returns is not None or any(
                        arg.annotation is not None for arg in node.args.args
                    )
                    counters["public function annotated"]["yes" if annotated else "no"] += 1
                    has_doc = ast.get_docstring(node) is not None
                    counters["public function has docstring"]["yes" if has_doc else "no"] += 1
            elif isinstance(node, ast.Assert) and is_test:
                counters["assertion style"]["bare assert"] += 1
            elif isinstance(node, ast.Call) and is_test:
                name = ast.unparse(node.func)
                if name.startswith("self.assert"):
                    counters["assertion style"]["self.assert*"] += 1
            elif isinstance(node, ast.Import):
                counters["import style"]["import x"] += len(node.names)
            elif isinstance(node, ast.ImportFrom):
                counters["import style"]["from x import y"] += len(node.names)

    result: dict[str, dict[str, object]] = {}
    for name, counter in counters.items():
        total = sum(counter.values())
        if total < 20:
            continue
        dominant, count = counter.most_common(1)[0]
        result[name] = {
            "dominant": dominant,
            "share": round(count / total, 3),
            "observations": total,
        }
    return result


def rationale_residue(repo: Path, limit: int) -> dict[str, object]:
    """How often a commit states a constraint the code it changed does not keep.

    A constraint that survives as a comment is recoverable by reading the file. Only what
    does not survive has to come from somewhere else, and that residue is the whole of the
    case for holding decision history.
    """

    log = _git(repo, "log", "--no-merges", f"-{limit}", "--format=%x01%H%x00%B%x00", "--name-only")
    stated = 0
    residual = 0
    total = 0
    examples: list[str] = []
    for block in log.split("\x01"):
        if "\x00" not in block:
            continue
        sha, _, rest = block.partition("\x00")
        message, _, files = rest.partition("\x00")
        total += 1
        sentences = [s for s in re.split(r"[.\n]", message) if _CONSTRAINT.search(s)]
        if not sentences:
            continue
        stated += 1
        # The words that carry the constraint, minus what any English sentence contains.
        claim = {w.lower() for s in sentences for w in _WORD.findall(s)}
        changed = [f for f in files.split() if f.endswith(".py")]
        comments: set[str] = set()
        for name in changed:
            try:
                text = _git(repo, "show", f"{sha}:{name}")
            except subprocess.CalledProcessError:
                continue
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("#"):
                    comments.update(w.lower() for w in _WORD.findall(stripped))
        # Recoverable if most of the constraint's vocabulary survives in comments.
        overlap = len(claim & comments) / len(claim) if claim else 1.0
        if overlap < 0.5:
            residual += 1
            if len(examples) < 5:
                examples.append(f"{sha[:10]} {sentences[0].strip()[:90]}")
    return {
        "commits": total,
        "stated_a_constraint": stated,
        "constraint_not_kept_in_code": residual,
        "rate_stating": round(stated / total, 3) if total else None,
        "rate_residual": round(residual / total, 3) if total else None,
        "examples": examples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, action="append", required=True)
    parser.add_argument("--commits", type=int, default=300)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = {
        "classification": "C2_NORM_CONSISTENCY_AND_RATIONALE_RESIDUE",
        "execution_scope": "local-only",
        "model_execution": "NOT_RUN_DETERMINISTIC_MEASUREMENT",
        "repositories": {},
    }
    for repo in args.repo:
        name = repo.name.replace("corpus-", "")
        norms = norm_shares(repo)
        rationale = rationale_residue(repo, args.commits)
        payload["repositories"][name] = {"norms": norms, "rationale": rationale}
        print(f"=== {name} ===")
        for norm, data in norms.items():
            print(
                f"  {norm:32} {data['share']:.3f}  {data['dominant']}  (n={data['observations']})"
            )
        print(
            f"  commits stating a constraint     {rationale['rate_stating']}"
            f"   not kept in code {rationale['rate_residual']}"
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
