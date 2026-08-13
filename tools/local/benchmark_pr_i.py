from __future__ import annotations

import json
import resource
import statistics
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from extendcodeagent.convergence import ConvergenceDecision
from extendcodeagent.core.contracts import (
    Confidence,
    EvidenceRef,
    EvidenceStatus,
    ProjectRef,
    Provenance,
    TwinRevisionRef,
)
from extendcodeagent.graph.analyzers import (
    CompositeGraphAnalyzer,
    JavaScriptTypeScriptGraphAnalyzer,
    PythonGraphAnalyzer,
)
from extendcodeagent.research import (
    Evidence,
    ResearchDepth,
    ResearchRequest,
    SqliteEvidenceRepository,
    build_research_plan,
)
from extendcodeagent.storage import SqliteGraphStore
from extendcodeagent.traceability import (
    Requirement,
    RequirementEvidence,
    evaluate_project_requirements,
)
from extendcodeagent.twin import TwinService

COUNT = 200
REPETITIONS = 20


def main(root: Path) -> None:
    root = root.resolve()
    project = ProjectRef("pr-i-benchmark", "default", root.as_uri())
    with tempfile.TemporaryDirectory(prefix="extendcodeagent-pr-i-") as temporary:
        database = Path(temporary) / "graph.db"
        with SqliteGraphStore(database) as store:
            twin = TwinService(
                store,
                analyzer=CompositeGraphAnalyzer(
                    (PythonGraphAnalyzer(), JavaScriptTypeScriptGraphAnalyzer())
                ),
            )
            twin.open(project)
            snapshot = twin.snapshot(project)
            if snapshot.revision is None:
                raise RuntimeError("benchmark requires a Twin revision")
            file_refs = [node.canonical_ref for node in snapshot.nodes if node.node_type == "file"]
            requirements = tuple(
                Requirement(
                    f"r{index}",
                    f"requirement {index}",
                    (file_refs[index % len(file_refs)],),
                )
                for index in range(COUNT)
            )
            revision = snapshot.revision.source_revision
            evidence = tuple(
                RequirementEvidence(
                    f"r{index}",
                    (file_refs[index % len(file_refs)],),
                    (EvidenceRef(f"test:{index}", EvidenceStatus.VERIFIED, revision),),
                    revision,
                )
                for index in range(COUNT)
            )
            latencies: list[float] = []
            decision = None
            for _ in range(REPETITIONS):
                started = time.perf_counter()
                report = evaluate_project_requirements(
                    project,
                    "requirements-1",
                    requirements,
                    tuple(file_refs),
                    TwinRevisionRef(snapshot.revision.revision_id, revision),
                    evidence,
                )
                latencies.append((time.perf_counter() - started) * 1000)
                decision = report.recommendation.decision
            repository = SqliteEvidenceRepository(store, project)
            provenance = Provenance("https://example.test", "benchmark", "1")
            started = time.perf_counter()
            for index in range(COUNT):
                repository.put(
                    Evidence(
                        f"external:{index}",
                        f"source:{index}",
                        f"hash:{index}",
                        f"summary {index}",
                        provenance,
                        Confidence(0.8),
                        datetime(2026, 8, 14, tzinfo=UTC),
                    )
                )
            persistence_ms = (time.perf_counter() - started) * 1000
            plan_latencies: list[float] = []
            for index in range(1_000):
                started = time.perf_counter()
                build_research_plan(
                    ResearchRequest(
                        f"request:{index}", project, "atomic storage", ResearchDepth.MICRO
                    ),
                    ("official docs", "release notes"),
                )
                plan_latencies.append((time.perf_counter() - started) * 1000)
            wal = Path(f"{database}-wal")
            size = database.stat().st_size + (wal.stat().st_size if wal.exists() else 0)
        with SqliteGraphStore(database) as reopened:
            restart_ok = SqliteEvidenceRepository(reopened, project).get("external:199") is not None
        result = {
            "schema": "extendcodeagent.pr-i-benchmark.v1",
            "repository": str(root),
            "requirements": COUNT,
            "convergence_repetitions": REPETITIONS,
            "convergence_decision": decision.value if decision else None,
            "convergence_mean_ms": round(statistics.mean(latencies), 4),
            "convergence_p50_ms": round(statistics.median(latencies), 4),
            "research_plans": len(plan_latencies),
            "research_plan_mean_ms": round(statistics.mean(plan_latencies), 4),
            "external_evidence_records": COUNT,
            "evidence_persistence_ms": round(persistence_ms, 3),
            "restart_lookup_passed": restart_ok,
            "db_and_wal_size_bytes": size,
            "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "complete_expected": decision is ConvergenceDecision.COMPLETE,
        }
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    import sys

    main(Path(sys.argv[1]))
