from __future__ import annotations

import json
import platform
import resource
import statistics
import sys
import tempfile
import time
from pathlib import Path

from extendcodeagent.analysis import (
    GraphAnalysisService,
    ImpactQuery,
    JavaScriptTypeScriptCanonicalReferenceResolver,
)
from extendcodeagent.core.contracts import ProjectRef
from extendcodeagent.graph.analyzers import JavaScriptTypeScriptGraphAnalyzer
from extendcodeagent.storage import SqliteGraphStore
from extendcodeagent.twin import TwinService


def main(root: Path, changed_path: str) -> None:
    root = root.resolve()
    with tempfile.TemporaryDirectory(prefix="extendcodeagent-pr-h-") as temporary:
        database = Path(temporary) / "graph.db"
        project = ProjectRef("pr-h-benchmark", "default", root.as_uri())
        with SqliteGraphStore(database) as store:
            twin = TwinService(store, analyzer=JavaScriptTypeScriptGraphAnalyzer())
            started = time.perf_counter()
            cold = twin.open(project)
            cold_ms = (time.perf_counter() - started) * 1000
            snapshot = twin.snapshot(project)
            tests = {
                node.canonical_ref.value for node in snapshot.nodes if node.node_type == "test"
            }
            linked_tests = {
                edge.source.value
                for edge in snapshot.edges
                if edge.source.value in tests and edge.edge_type in {"calls", "references"}
            }
            targets = [
                edge.target.value
                for edge in snapshot.edges
                if edge.source.value in tests
                and edge.edge_type == "calls"
                and edge.target.value.startswith("js://")
            ][:20]
            analysis = GraphAnalysisService(
                snapshot, JavaScriptTypeScriptCanonicalReferenceResolver()
            )
            latencies: list[float] = []
            recommended = 0
            for target in targets:
                started = time.perf_counter()
                report = analysis.assess_impact(ImpactQuery((target,), max_depth=6))
                latencies.append((time.perf_counter() - started) * 1000)
                recommended += len(report.recommended_tests)
            started = time.perf_counter()
            refreshed = twin.refresh(project, changed_paths=(changed_path,))
            refresh_ms = (time.perf_counter() - started) * 1000
            wal = Path(f"{database}-wal")
            size = database.stat().st_size + (wal.stat().st_size if wal.exists() else 0)
            result = {
                "schema": "extendcodeagent.pr-h-benchmark.v1",
                "repository": str(root),
                "python": platform.python_version(),
                "platform": platform.platform(),
                "changed_path": changed_path,
                "source_files": len(
                    {node.source_ref for node in snapshot.nodes if node.node_type == "file"}
                ),
                "graph_nodes": len(snapshot.nodes),
                "graph_edges": len(snapshot.edges),
                "test_nodes": len(tests),
                "tests_with_static_evidence": len(linked_tests),
                "cold_ms": round(cold_ms, 3),
                "refresh_ms": round(refresh_ms, 3),
                "refresh_strategy": (
                    "full"
                    if any(
                        item.code == "auto_full_refresh_selected" for item in refreshed.diagnostics
                    )
                    else "incremental"
                ),
                "affected_paths": len(refreshed.affected_paths),
                "query_count": len(latencies),
                "impact_latency_mean_ms": (
                    round(statistics.mean(latencies), 4) if latencies else None
                ),
                "impact_latency_p50_ms": (
                    round(statistics.median(latencies), 4) if latencies else None
                ),
                "recommended_tests_total": recommended,
                "db_and_wal_size_bytes": size,
                "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "diagnostics": sorted(
                    {item.code for item in (*cold.diagnostics, *refreshed.diagnostics)}
                ),
            }
            print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2])
