#!/usr/bin/env python3
"""Does the envelope hold what this kind of task needs? Answered before a model is spent.

A code-generation benchmark was run against an envelope that carried 64 function names from
the target file and no source at all, because `attach_excerpts` attaches only to refs the
caller named and a `file://` target names no symbol. The arm under test was inert, and its
loss looked like evidence about the design. It was not; it was an unrun mechanism.

So this asserts what a task type requires, deterministically and without a model, in the
seconds before a run that costs tens of minutes. It is a gate, not a report: a failing
expectation means the number that run would produce is not worth having.

Expectations are per task kind, because they differ. Code generation needs the source it is
being asked to change. Verification needs tests. Both need an envelope that fits its budget
and gaps that name something a project could actually hold.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from extendcodeagent.context import estimate_payload_tokens  # noqa: E402
from extendcodeagent.core.config import ConfigLayer, ConfigResolver  # noqa: E402
from extendcodeagent.core.config.schema import CONFIGURABLE_CAPABILITIES  # noqa: E402
from extendcodeagent.core.policy import CapabilityPolicy  # noqa: E402
from extendcodeagent.service.application import ProjectIntelligenceApplication  # noqa: E402


def _policy() -> CapabilityPolicy:
    layer = ConfigLayer(
        "c2-preflight",
        {
            "project_intelligence": {
                "enabled": True,
                "mode": "active",
                "capabilities": {item.value: "active" for item in CONFIGURABLE_CAPABILITIES},
            }
        },
    )
    return CapabilityPolicy.from_config(ConfigResolver().resolve(layer).project_intelligence)


@dataclass(frozen=True)
class Expectation:
    name: str
    holds: bool
    detail: str

    def line(self) -> str:
        return f"  {'PASS' if self.holds else 'FAIL'}  {self.name:44} {self.detail}"


def _english_anchor_gaps(gaps: list[str]) -> list[str]:
    """Gaps naming ordinary words. A project cannot be missing the word `pass`."""

    return [
        gap
        for gap in gaps
        if gap.startswith("objective_anchor_missing:")
        and not any(mark in gap.split(":", 1)[1] for mark in "._/#")
        and gap.split(":", 1)[1].isalpha()
    ]


def check(
    envelope: dict, *, kind: str, target_paths: tuple[str, ...], budget: int
) -> list[Expectation]:
    items = envelope.get("items", [])
    gaps = list(envelope.get("unresolved_evidence_gaps", []))
    tokens = estimate_payload_tokens(envelope)
    # The emitted field is `source`; an earlier version of this gate looked for `excerpt`
    # and reported a working envelope as empty. A gate that checks the wrong key is
    # worse than no gate, because it is believed.
    with_source = [item for item in items if item.get("source")]
    in_target = [
        item for item in items if any(path in str(item.get("path", "")) for path in target_paths)
    ]
    checks = [
        Expectation("the envelope holds something", bool(items), f"{len(items)} items"),
        # Two bounds, reported apart. Conflating them hid which one was actually exceeded:
        # a verification envelope sits at a quarter of its token budget while carrying more
        # protected obligations than the item cap can hold, and those want different fixes.
        Expectation(
            "it fits its token budget",
            tokens <= budget,
            f"{tokens} of {budget} tokens",
        ),
        Expectation(
            "it stays within its item bound",
            "protected_evidence_exceeds_budget" not in gaps,
            f"{len(items)} items"
            + (
                "; protected obligations exceed the cap"
                if "protected_evidence_exceeds_budget" in gaps
                else ""
            ),
        ),
        Expectation(
            "every gap names something a project could hold",
            not _english_anchor_gaps(gaps),
            ", ".join(_english_anchor_gaps(gaps)) or f"{len(gaps)} gaps, all specific",
        ),
    ]
    if kind == "codegen":
        checks += [
            Expectation(
                "the target file is represented",
                bool(in_target),
                f"{len(in_target)} items from {', '.join(target_paths)}",
            ),
            Expectation(
                "the source to be changed is present, not just its names",
                bool(with_source),
                f"{len(with_source)} of {len(items)} items carry source",
            ),
            # Convention travels with real code from this project. When production is being
            # changed, the sibling bodies already carry it; a test exemplar is what a task
            # writing a *test* needs, and demanding one here failed a working envelope.
            Expectation(
                "a convention exemplar is included",
                any(item.get("source") and "test" in str(item.get("path", "")) for item in items)
                if any("test" in path for path in target_paths)
                else len(with_source) > 1,
                f"{len(with_source)} real examples from this project",
            ),
        ]
    elif kind == "verification":
        tests = [item for item in items if "test" in str(item.get("path", ""))]
        checks += [
            Expectation("tests are present", bool(tests), f"{len(tests)} test items"),
            Expectation(
                "the scope is the one that answers for tests",
                envelope.get("scope") == "verification",
                f"scope={envelope.get('scope')}",
            ),
        ]
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--kind", choices=("codegen", "verification"), required=True)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--target", action="append", required=True, help="repo-relative path")
    parser.add_argument("--budget", type=int, default=8_192)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    import tempfile

    with (
        tempfile.TemporaryDirectory(prefix="eca-preflight-") as temp,
        ProjectIntelligenceApplication(args.repo, Path(temp) / "graph.db", _policy()) as app,
    ):
        app._snapshot(open_if_missing=True)
        payload = app.context(
            args.objective,
            tuple(f"file://{path}" for path in args.target),
            token_budget=args.budget,
            view="envelope",
            # Declared, not inferred: the caller knows whether it is asking for a change.
            changing=args.kind == "codegen",
        )
    envelope = payload["task_evidence"]
    checks = check(envelope, kind=args.kind, target_paths=tuple(args.target), budget=args.budget)

    revision = subprocess.run(
        ["git", "-C", str(args.repo), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    print(f"envelope preflight — {args.kind} — {args.repo.name} @ {revision[:12]}")
    for item in checks:
        print(item.line())
    failed = [item for item in checks if not item.holds]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} expectations hold")

    if args.output:
        args.output.write_text(
            json.dumps(
                {
                    "classification": "C2_ENVELOPE_PREFLIGHT",
                    "execution_scope": "local-only",
                    "model_execution": "NOT_RUN_DETERMINISTIC_MEASUREMENT",
                    "repository": str(args.repo),
                    "revision": revision,
                    "kind": args.kind,
                    "objective": args.objective,
                    "targets": list(args.target),
                    "expectations": [
                        {"name": c.name, "holds": c.holds, "detail": c.detail} for c in checks
                    ],
                    "envelope_items": len(envelope.get("items", [])),
                },
                indent=2,
            )
            + "\n"
        )
    # Non-zero so a benchmark script can refuse to spend a run on an inert arm.
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
