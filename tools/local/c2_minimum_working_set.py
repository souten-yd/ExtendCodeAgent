#!/usr/bin/env python3
"""What of the envelope a run that succeeded actually needed.

An arm that passes says the envelope was enough. It does not say the envelope was necessary,
and 17,262 tokens went out for runs whose changed functions needed 1,218. The difference is
either working or being carried.

So the successful envelope is cut down and the run repeated: halve the items, and if it still
passes, halve again. What survives is the working set that task needed, measured rather than
designed. What does not survive being removed was doing something; what does was not, and a
selector that stops sending it loses nothing.

This is delta debugging over evidence, so it inherits its assumption: the run has to be
repeatable enough that a pass means the context sufficed. Temperature is zero and the same
commit is checked out each time, but a model is not a pure function, so a single pass at a
smaller size is checked twice before it is believed.

Runs the model many times per case. It is for the few cases that succeeded, not for a corpus.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from c2_codegen_bench import (  # noqa: E402
    Case,
    _git,
    break_repository,
    build_envelope,
    executed_at_commit,
    run_arm,
)

from extendcodeagent.context import estimate_payload_tokens  # noqa: E402


def keep_items(envelope: str, keep: int) -> str:
    """The same envelope with only its first `keep` items.

    First, not a sample: the order is the one selection chose, so cutting from the end asks
    whether what it ranked last was needed.
    """

    payload = json.loads(envelope)
    payload["items"] = payload["items"][:keep]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def passes(
    repo: Path, python: Path, case: Case, reverted: tuple[str, ...], envelope: str, args
) -> bool:
    break_repository(repo, case)
    result = run_arm(
        repo,
        python,
        case,
        reverted,
        args.endpoint,
        args.model,
        envelope=envelope,
        reissue=None,
        max_turns=args.max_turns,
        max_output=1_536,
        test_timeout=args.test_timeout,
    )
    return bool(result["passed"])


def minimise(repo: Path, python: Path, case: Case, reverted: tuple[str, ...], full: str, args):
    """Halve until it stops passing, then report the smallest size that still did."""

    items = len(json.loads(full)["items"])
    steps = [{"items": items, "tokens": estimate_payload_tokens(json.loads(full)), "passed": True}]
    smallest, keep = full, items
    while keep > 1:
        candidate = keep // 2
        trimmed = keep_items(full, candidate)
        tokens = estimate_payload_tokens(json.loads(trimmed))
        # A model is not a pure function; one pass at a smaller size is confirmed before the
        # search commits to it and throws away everything above.
        ok = passes(repo, python, case, reverted, trimmed, args) and passes(
            repo, python, case, reverted, trimmed, args
        )
        steps.append({"items": candidate, "tokens": tokens, "passed": ok})
        print(
            f"    {candidate:>3} items / {tokens:>6} tok  {'passed' if ok else 'failed'}",
            flush=True,
        )
        if not ok:
            break
        smallest, keep = trimmed, candidate
    return smallest, steps


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--findings", type=Path, required=True)
    parser.add_argument("--commits", nargs="+", required=True, help="the runs that passed")
    parser.add_argument("--endpoint", default="http://127.0.0.1:8097/v1")
    parser.add_argument("--model", required=True)
    parser.add_argument("--max-turns", type=int, default=14)
    parser.add_argument("--test-timeout", type=int, default=300)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.findings.read_text())
    by_sha = {r["sha"]: r for r in payload["results"]}
    original = _git(args.repo, "rev-parse", "HEAD").strip()
    rows = []
    try:
        for sha in args.commits:
            found = next((v for k, v in by_sha.items() if k.startswith(sha)), None)
            if found is None:
                print(f"  {sha}: not in the findings", flush=True)
                continue
            case = Case(
                f"min-{sha}", found["sha"], found["subject"], (), tuple(found["detecting_tests"])
            )
            _git(args.repo, "checkout", "-q", "--force", found["sha"])
            executed = executed_at_commit(args.repo, args.python, case, args.test_timeout)
            reverted = break_repository(args.repo, case)
            full = build_envelope(args.repo, case, reverted, executed, 8_192)
            print(f"  {sha} {found['subject'][:50]}", flush=True)
            smallest, steps = minimise(args.repo, args.python, case, reverted, full, args)
            kept = json.loads(smallest)
            rows.append(
                {
                    "commit": found["sha"],
                    "subject": found["subject"],
                    "from_items": steps[0]["items"],
                    "from_tokens": steps[0]["tokens"],
                    "to_items": len(kept["items"]),
                    "to_tokens": estimate_payload_tokens(kept),
                    "steps": steps,
                    "kept": [i.get("summary") for i in kept["items"]],
                }
            )
    finally:
        _git(args.repo, "checkout", "-q", "--force", original)

    result = {
        "classification": "C2_MINIMUM_WORKING_SET_DIAGNOSTIC",
        "note": (
            "Diagnostic. The sealed local-practical arm is port-8090; this endpoint is a "
            "different route and is not recorded as B0b/C2 evidence."
        ),
        "model": args.model,
        "results": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    for row in rows:
        print(
            f"{row['commit'][:12]}  {row['from_tokens']:>6} -> {row['to_tokens']:>6} tok"
            f"   {row['from_items']} -> {row['to_items']} items"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
