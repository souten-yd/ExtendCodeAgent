#!/usr/bin/env python3
"""Run a Python suite once with per-test coverage contexts and record what each test reached.

Cause 4 in docs/handoff/C2_EXTERNAL_VALIDATION_PLAN.md — which tests must run — is not a
ranking problem. A test reaches its subject through a runner, a registry or a fixture and
leaves no call or import edge behind, so the pair is absent from the graph rather than
mis-ranked in it. Coverage is where the pair exists.

It also costs nothing extra to obtain. A test is executed when it is written and again on
every suite run; this only asks that run to record which test was executing, which is one
coverage setting.

`coverage` is a tool dependency here, not a dependency of the core: the core takes an
already-parsed mapping so that a JavaScript or Go project can feed it from its own
tooling.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from extendcodeagent.core.config import ConfigLayer, ConfigResolver
from extendcodeagent.core.config.schema import CONFIGURABLE_CAPABILITIES
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.runtime import ObservationStatus, observation_from_coverage
from extendcodeagent.service import ProjectIntelligenceApplication

ROOT = Path(__file__).resolve().parents[2]

# A dynamic context is `module.test_function`, with an optional `|phase` suffix naming
# setup, run or teardown — which says nothing about the test the line belongs to.
_CONTEXT = re.compile(r"^(?P<module>[\w.]+)\.(?P<name>test_[\w]+)(\|.*)?$")

_RCFILE = """[run]
dynamic_context = test_function
branch = True
"""


class CoverageIngestError(RuntimeError):
    """The suite did not produce usable per-test coverage."""


def run_suite(repository: Path, data_file: Path, runner: tuple[str, ...]) -> int:
    """Run the suite under coverage, tagging every line with the test that reached it.

    The runner is configurable because most projects do not invoke pytest directly:
    Django has `tests/runtests.py`, and a `manage.py test` or `tox` entry point is just as
    common. `dynamic_context = test_function` keys on the executing function's name, so it
    works for any framework whose tests are named `test_*`.
    """

    # `dynamic_context` has no command-line form, so the setting travels in an rcfile.
    rcfile = data_file.with_suffix(".rc")
    rcfile.write_text(_RCFILE, encoding="utf-8")
    command = (
        sys.executable,
        "-m",
        "coverage",
        "run",
        f"--rcfile={rcfile}",
        f"--data-file={data_file}",
        *runner,
    )
    result = subprocess.run(command, cwd=repository, capture_output=True, text=True, check=False)
    if result.returncode not in (0, 1):  # 1 is "tests failed", still usable coverage
        raise CoverageIngestError(
            f"suite could not run: {result.stderr.strip()[:600] or result.stdout.strip()[:600]}"
        )
    return result.returncode


def executed_by_test(repository: Path, data_file: Path) -> dict[str, dict[str, set[int]]]:
    """Per test, the source lines it reached, keyed by repository-relative path."""

    import coverage

    data = coverage.CoverageData(basename=str(data_file))
    data.read()
    contexts = [value for value in data.measured_contexts() if value]
    if not contexts:
        raise CoverageIngestError(
            "coverage recorded no test contexts; the run needs --context=test"
        )

    executed: dict[str, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))
    for measured in data.measured_files():
        try:
            relative = Path(measured).resolve().relative_to(repository).as_posix()
        except ValueError:
            continue  # outside the project: site-packages, the interpreter itself
        # coverage maps line -> contexts that reached it, which is the inverse of what a
        # per-test view needs.
        for lineno, contexts_here in (data.contexts_by_lineno(measured) or {}).items():
            for context in contexts_here:
                match = _CONTEXT.match(context)
                if not match:
                    continue
                key = f"{match['module'].rsplit('.', 1)[-1]}::{match['name']}"
                executed[key][relative].add(lineno)
    if not executed:
        raise CoverageIngestError("no coverage line mapped back into the repository")
    return {test: dict(files) for test, files in executed.items()}


def resolve_test_refs(snapshot: Any, keys: Iterable[str]) -> dict[str, str]:
    """Map `module::test_name` onto the canonical ref the Twin already has for that test.

    Recording the observation under the graph's own identifier is what lets an obligation
    match it: everything else in the envelope is keyed by canonical ref.
    """

    by_pair: dict[tuple[str, str], str] = {}
    for node in snapshot.nodes:
        if node.node_type != "test":
            continue
        name = str(node.properties.get("name") or "")
        if name:
            by_pair[(Path(node.source_ref).stem, name)] = node.canonical_ref.value
    resolved: dict[str, str] = {}
    for key in keys:
        module, _, name = key.partition("::")
        ref = by_pair.get((module, name))
        if ref:
            resolved[key] = ref
    return resolved


def _policy() -> CapabilityPolicy:
    layer = ConfigLayer(
        "c2-coverage",
        {
            "project_intelligence": {
                "enabled": True,
                "mode": "active",
                "capabilities": {item.value: "active" for item in CONFIGURABLE_CAPABILITIES},
            }
        },
    )
    return CapabilityPolicy.from_config(ConfigResolver().resolve(layer).project_intelligence)


def ingest(repository: Path, database: Path, executed: dict[str, dict[str, set[int]]]) -> dict:
    now = datetime.now(UTC)
    with ProjectIntelligenceApplication(repository, database, _policy()) as application:
        snapshot = application._snapshot(open_if_missing=True)
        revision = snapshot.revision.source_revision if snapshot.revision else None
        if revision is None:
            raise CoverageIngestError("the project has no Twin revision to bind coverage to")
        store = application._ensure_store()

        resolved = resolve_test_refs(snapshot, executed)
        stored = 0
        empty = 0
        unresolved = 0
        reached: list[int] = []
        for key, files in sorted(executed.items()):
            test_id = resolved.get(key)
            if test_id is None:
                unresolved += 1
                continue
            observation = observation_from_coverage(
                snapshot,
                project=application.project,
                source_revision=revision,
                test_id=test_id,
                executed=files,
                status=ObservationStatus.PASSED,
                started_at=now,
                finished_at=now,
                command="test suite under coverage",
            )
            # The test's own ref is always there; one ref alone means it reached nothing
            # the Twin models, which is worth counting rather than storing.
            if len(observation.observed_refs) <= 1:
                empty += 1
                continue
            store.put_observation(observation)
            stored += 1
            reached.append(len(observation.observed_refs) - 1)

        return {
            "revision": revision.value,
            "twin_nodes": len(snapshot.nodes),
            "tests_measured": len(executed),
            "tests_not_in_the_twin": unresolved,
            "observations_stored": stored,
            "tests_reaching_nothing_modelled": empty,
            "symbols_per_test_mean": round(sum(reached) / len(reached), 1) if reached else 0.0,
            "symbols_per_test_max": max(reached, default=0),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path)
    parser.add_argument("--database", type=Path, required=True, help="graph store to ingest into")
    parser.add_argument(
        "--runner",
        nargs=argparse.REMAINDER,
        default=None,
        help="what to run under coverage, after `coverage run` (default: -m pytest -q)",
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    repository = args.repository.expanduser().resolve()
    with tempfile.TemporaryDirectory(prefix="eca-coverage-") as temp:
        data_file = Path(temp) / "coverage.data"
        runner = tuple(args.runner) if args.runner else ("-m", "pytest", "-q")
        exit_code = run_suite(repository, data_file, runner)
        executed = executed_by_test(repository, data_file)
    summary = {
        "classification": "C2_COVERAGE_INGEST",
        "repository": str(repository),
        "suite_exit_code": exit_code,
        **ingest(repository, args.database.expanduser().resolve(), executed),
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
