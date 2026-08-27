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

Two conditions are expected to fail, and are left failing. A retrieval envelope carries more
protected obligations than `_PROTOCOL_MAX_ITEMS = 32` allows, because obligations may produce
64 refs and a protected ref is never dropped. Raising the constant is a product behaviour
change already adopted as a plan item, and that item requires a before/after recall curve
first: if recall at 64 items is no better than at 32, the defect is ranking rather than the
cap. Silently raising it here would be that measurement's answer written in advance.

`--suite` runs several conditions at once, chosen to fail in different ways rather than to
agree. One small target and one large one separate "the source arrives" from "the budget
degrades gracefully". A target no test mentions asks whether an empty answer is reported or
disguised. A question *about* a change sits beside a request to make one, because confusing
those is what dropped sealed recall from 1.00 to 0.711. A target that does not exist asks
whether the envelope fails loudly instead of returning a confident nothing.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
            # A file that defines nothing has no body to send. `flask/__main__.py` is two
            # lines of module-level code, and failing it for that measured the file.
            Expectation(
                "the source to be changed is present, not just its names",
                bool(with_source) or not any(item.get("lines") for item in in_target),
                f"{len(with_source)} of {len(items)} items carry source"
                + ("; the target defines no symbols" if not with_source else ""),
            ),
            # Convention travels with real code from this project. When production is being
            # changed, the sibling bodies already carry it; a test exemplar is what a task
            # writing a *test* needs, and demanding one here failed a working envelope.
            Expectation(
                "a convention exemplar is included",
                any(item.get("source") and "test" in str(item.get("path", "")) for item in items)
                if any("test" in path for path in target_paths)
                else len(with_source) > 1 or not any(item.get("lines") for item in in_target),
                f"{len(with_source)} real examples from this project",
            ),
        ]
    elif kind == "impact":
        # `role` is not an emitted field; the role-shaped payload carries `reason` instead.
        # Checking the wrong key is how this gate reported a working envelope as empty once
        # already, so it reads what is actually sent.
        consumers = [item for item in items if str(item.get("reason", "")).endswith(":consumer")]
        checks += [
            # Saying it has none is a correct answer. `Scaffold` is a base class whose
            # methods are reached through subclasses, so no consumer edge joins them, and
            # the envelope reports `no_consumer_evidence` rather than implying it looked.
            Expectation(
                "consumers are present, or their absence is stated",
                bool(consumers) or "no_consumer_evidence" in gaps,
                f"{len(consumers)} consumer items of {len(items)}"
                + ("; absence stated" if "no_consumer_evidence" in gaps else ""),
            ),
            Expectation(
                "it did not take a question about a change for a request to make one",
                envelope.get("scope") != "symbol",
                f"scope={envelope.get('scope')}",
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


@dataclass(frozen=True)
class Condition:
    name: str
    kind: str
    objective: str
    targets: tuple[str, ...]
    #: What this condition exists to catch, beyond its kind's expectations.
    must_report_absence: bool = False
    must_not_exist: bool = False


#: Conditions for flask, named by what each would catch on its own.
FLASK_SUITE: tuple[Condition, ...] = (
    Condition(
        "codegen, ordinary target",
        "codegen",
        "Change src/flask/sansio/scaffold.py so that the failing tests pass",
        ("src/flask/sansio/scaffold.py",),
    ),
    Condition(
        # 1,628 lines. The excerpt budget cannot hold it, so this asks what is dropped.
        "codegen, large target",
        "codegen",
        "Change src/flask/app.py so that the failing tests pass",
        ("src/flask/app.py",),
    ),
    Condition(
        # No test file mentions it. An envelope that says nothing about that is claiming an
        # answer it does not have.
        "codegen, target no test mentions",
        "codegen",
        "Change src/flask/__main__.py so that the failing tests pass",
        ("src/flask/__main__.py",),
        must_report_absence=True,
    ),
    Condition(
        "verification, which tests must run",
        "verification",
        "Select the existing tests that must run for a change to "
        "src/flask/sansio/scaffold.py. Do not edit source.",
        ("src/flask/sansio/scaffold.py",),
    ),
    Condition(
        # A question *about* a change. Reading intent out of the words put this on the
        # change path and capped its tests at two.
        "question about a change",
        "impact",
        "Assess the change impact if src/flask/sansio/scaffold.py changes its route "
        "registration semantics. Do not edit source.",
        ("src/flask/sansio/scaffold.py",),
    ),
    Condition(
        "target that does not exist",
        "codegen",
        "Change src/flask/does_not_exist.py so that the failing tests pass",
        ("src/flask/does_not_exist.py",),
        must_not_exist=True,
    ),
)


def run_condition(app: Any, condition: Condition, budget: int) -> list[Expectation]:
    payload = app.context(
        condition.objective,
        tuple(f"file://{path}" for path in condition.targets),
        token_budget=budget,
        view="envelope",
        changing=condition.kind == "codegen",
    )
    envelope = payload["task_evidence"]
    checks = check(envelope, kind=condition.kind, target_paths=condition.targets, budget=budget)
    items = envelope.get("items", [])
    gaps = list(envelope.get("unresolved_evidence_gaps", []))
    if condition.must_report_absence:
        checks.append(
            Expectation(
                "it says so when it has no tests to offer",
                any("test" in str(item.get("path", "")) for item in items) or bool(gaps),
                f"{len(gaps)} gaps: {', '.join(gaps) or 'none'}",
            )
        )
    if condition.must_not_exist:
        # A confident empty envelope is the worst answer: the consumer stops looking.
        checks = [
            Expectation(
                "a target that does not exist is not answered confidently",
                not items or bool(gaps),
                f"{len(items)} items, {len(gaps)} gaps",
            )
        ]
    return checks


def run_suite(repo: Path, budget: int) -> dict[str, list[Expectation]]:
    import tempfile

    results: dict[str, list[Expectation]] = {}
    with (
        tempfile.TemporaryDirectory(prefix="eca-suite-") as temp,
        ProjectIntelligenceApplication(repo, Path(temp) / "graph.db", _policy()) as app,
    ):
        app._snapshot(open_if_missing=True)
        for condition in FLASK_SUITE:
            results[condition.name] = run_condition(app, condition, budget)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--suite", action="store_true", help="run every condition")
    parser.add_argument("--kind", choices=("codegen", "verification", "impact"))
    parser.add_argument("--objective")
    parser.add_argument("--target", action="append", help="repo-relative path")
    parser.add_argument("--budget", type=int, default=8_192)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    if args.suite:
        results = run_suite(args.repo, args.budget)
        failed_total = 0
        for name, checks in results.items():
            failures = [item for item in checks if not item.holds]
            failed_total += len(failures)
            print(f"\n{name}  —  {len(checks) - len(failures)}/{len(checks)}")
            for item in checks:
                print(item.line())
        print(f"\n{failed_total} expectations failed across {len(results)} conditions")
        return 1 if failed_total else 0

    if not (args.kind and args.objective and args.target):
        parser.error("--kind, --objective and --target are required without --suite")

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
