#!/usr/bin/env python3
"""Bounded deterministic PR-F lifecycle and task-convergence benchmark."""

from __future__ import annotations

import json
import platform
import resource
import statistics
import subprocess
import tempfile
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from extendcodeagent.blueprint import BlueprintElement, BlueprintService
from extendcodeagent.blueprint.storage import SqliteBlueprintRepository
from extendcodeagent.convergence import (
    ActualElement,
    ActualSnapshot,
    ConvergenceDecision,
    TargetElement,
    TargetSnapshot,
    VerificationEvidence,
    decide_convergence,
    evaluate_convergence,
)
from extendcodeagent.convergence.storage import SqliteConvergenceRepository
from extendcodeagent.core.contracts import (
    CanonicalRef,
    EvidenceRef,
    EvidenceStatus,
    ProjectRef,
    SourceRevision,
    TwinRevisionRef,
)
from extendcodeagent.storage import SqliteGraphStore

REPO = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 8, 13, tzinfo=UTC)
T = TypeVar("T")


def main() -> None:
    project = ProjectRef("pr-f-benchmark", "default", REPO.as_uri())
    source = SourceRevision("benchmark-source")
    twin = TwinRevisionRef("benchmark-twin", source)
    blueprint_elements = tuple(
        BlueprintElement(
            f"element-{index}",
            CanonicalRef(f"bp://element-{index}"),
            "file",
            expected_actual_refs=(CanonicalRef(f"file://module_{index}.py"),),
            depends_on_element_ids=((f"element-{index - 1}",) if index else ()),
        )
        for index in range(200)
    )
    target_elements = tuple(
        TargetElement(
            item.element_id,
            item.planned_ref,
            item.expected_actual_refs,
            item.mandatory,
            item.requires_verification,
            item.depends_on_element_ids,
        )
        for item in blueprint_elements
    )
    actual = ActualSnapshot(
        project,
        twin,
        tuple(
            ActualElement(CanonicalRef(f"file://module_{index}.py"), "file") for index in range(200)
        ),
    )
    verification = tuple(
        VerificationEvidence(
            item.canonical_ref,
            EvidenceStatus.VERIFIED,
            source,
            (EvidenceRef(f"evidence-{index}", EvidenceStatus.VERIFIED, source),),
        )
        for index, item in enumerate(actual.elements)
    )
    with tempfile.TemporaryDirectory(prefix="extendcodeagent-pr-f-benchmark-") as directory:
        database = Path(directory) / "project.db"
        with SqliteGraphStore(database) as store:
            service = BlueprintService(SqliteBlueprintRepository(store), now=lambda: NOW)
            started = time.perf_counter()
            created = service.create(project, blueprint_elements, source_twin_revision=twin)
            assert created is not None
            service.review(project, created.revision.revision_id)
            service.approve(project, created.revision.revision_id)
            service.activate(project, created.revision.revision_id)
            lifecycle_ms = _elapsed_ms(started)
            target = TargetSnapshot(project, created.revision.revision_id, target_elements)
            report, samples = _measure(
                lambda: evaluate_convergence(target, actual, verification), repetitions=50
            )
            recommendation = decide_convergence(report)
            if recommendation.decision is not ConvergenceDecision.COMPLETE:
                raise RuntimeError("fully verified target did not converge")
            SqliteConvergenceRepository(store).put(report, recommendation)
        restart_started = time.perf_counter()
        with SqliteGraphStore(database) as reopened:
            active = BlueprintService(SqliteBlueprintRepository(reopened)).active(project)
            stored = SqliteConvergenceRepository(reopened).latest(project)
        restart_ms = _elapsed_ms(restart_started)
        if active is None or stored is None:
            raise RuntimeError("durable PR-F artifacts were not restored")
        output = {
            "commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
            ).strip(),
            "environment": {
                "os": f"{platform.system()} {platform.release()} {platform.machine()}",
                "python": platform.python_version(),
            },
            "elements": len(target_elements),
            "lifecycle_ms": lifecycle_ms,
            "evaluation": _latency_metrics(samples),
            "decision": recommendation.decision.value,
            "restart_ms": restart_ms,
            "database_bytes": database.stat().st_size,
            "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        }
        print(json.dumps(output, indent=2, sort_keys=True))


def _measure(operation: Callable[[], T], *, repetitions: int) -> tuple[T, list[float]]:
    samples: list[float] = []
    result = operation()
    for _ in range(repetitions):
        started = time.perf_counter()
        result = operation()
        samples.append(_elapsed_ms(started))
    return result, samples


def _latency_metrics(samples: list[float]) -> dict[str, float]:
    ordered = sorted(samples)
    return {
        "min_ms": ordered[0],
        "p50_ms": round(statistics.median(ordered), 4),
        "p95_ms": ordered[round(0.95 * (len(ordered) - 1))],
        "max_ms": ordered[-1],
    }


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1_000, 4)


if __name__ == "__main__":
    main()
