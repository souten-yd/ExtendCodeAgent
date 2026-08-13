from __future__ import annotations

import json
import platform
import resource
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from extendcodeagent.analysis import (
    GraphAnalysisService,
    ImpactQuery,
    PythonCanonicalReferenceResolver,
)
from extendcodeagent.core.contracts import ProjectRef
from extendcodeagent.graph.analyzers import PythonGraphAnalyzer
from extendcodeagent.storage import SqliteGraphStore
from extendcodeagent.twin import TwinService

REPETITIONS = 5
MAX_SYMBOLS = 20


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(len(ordered) * fraction))
    return ordered[index]


def main(root: Path) -> None:
    root = root.resolve()
    with tempfile.TemporaryDirectory(prefix="extendcodeagent-pr-c-") as temporary:
        database = Path(temporary) / "graph.db"
        project = ProjectRef("benchmark", "default", root.as_uri())
        with SqliteGraphStore(database) as store:
            twin = TwinService(store, analyzer=PythonGraphAnalyzer())
            started = time.perf_counter()
            cold = twin.open(project)
            cold_ms = (time.perf_counter() - started) * 1000
            snapshot = twin.snapshot(project)
            incoming_targets = {edge.target.value for edge in snapshot.edges}
            symbols = [
                node.canonical_ref.value
                for node in snapshot.nodes
                if node.node_type in {"function", "method"}
                and node.canonical_ref.value in incoming_targets
            ][:MAX_SYMBOLS]
            if not symbols:
                raise RuntimeError("benchmark repository has no referenced Python symbols")

            analysis = GraphAnalysisService(snapshot, PythonCanonicalReferenceResolver())
            impact_latencies: list[float] = []
            impact_items = 0
            for _ in range(REPETITIONS):
                for symbol in symbols:
                    started = time.perf_counter()
                    report = analysis.assess_impact(ImpactQuery((symbol,), max_depth=6))
                    impact_latencies.append((time.perf_counter() - started) * 1000)
                    impact_items += len(report.direct_impacts) + len(report.transitive_impacts)

            grep_latencies: list[float] = []
            grep_files = 0
            for _ in range(REPETITIONS):
                for symbol in symbols:
                    short_name = symbol.rsplit("#", 1)[-1].rsplit(".", 1)[-1]
                    started = time.perf_counter()
                    result = subprocess.run(
                        [
                            "rg",
                            "--files-with-matches",
                            "--word-regexp",
                            "--glob",
                            "*.py",
                            short_name,
                            str(root),
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    grep_latencies.append((time.perf_counter() - started) * 1000)
                    grep_files += len(result.stdout.splitlines())

            changed_path = "src/extendcodeagent/core/contracts.py"
            started = time.perf_counter()
            incremental = twin.refresh(project, changed_paths=(changed_path,))
            incremental_ms = (time.perf_counter() - started) * 1000
            wal = Path(f"{database}-wal")
            storage_bytes = database.stat().st_size + (wal.stat().st_size if wal.exists() else 0)
            benchmark_report = {
                "schema": "extendcodeagent.pr-c-benchmark.v1",
                "repository": str(root),
                "python": platform.python_version(),
                "platform": platform.platform(),
                "source_files": len(
                    {node.source_ref for node in snapshot.nodes if node.node_type == "file"}
                ),
                "graph_nodes": len(snapshot.nodes),
                "graph_edges": len(snapshot.edges),
                "cold_semantic_index_ms": round(cold_ms, 3),
                "incremental_semantic_refresh_ms": round(incremental_ms, 3),
                "incremental_affected_paths": list(incremental.affected_paths),
                "db_and_wal_size_bytes": storage_bytes,
                "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "query_symbols": len(symbols),
                "query_repetitions": REPETITIONS,
                "impact_queries": len(impact_latencies),
                "impact_latency_mean_ms": round(statistics.mean(impact_latencies), 4),
                "impact_latency_p50_ms": round(statistics.median(impact_latencies), 4),
                "impact_latency_p95_ms": round(_percentile(impact_latencies, 0.95), 4),
                "impact_items_total": impact_items,
                "native_rg_queries": len(grep_latencies),
                "native_rg_latency_mean_ms": round(statistics.mean(grep_latencies), 4),
                "native_rg_latency_p50_ms": round(statistics.median(grep_latencies), 4),
                "native_rg_latency_p95_ms": round(_percentile(grep_latencies, 0.95), 4),
                "native_rg_files_total": grep_files,
                "cold_revision_created": cold.revision is not None,
                "incremental_revision_changed": incremental.revision != cold.revision,
                "comparison_note": (
                    "rg is a lexical file-candidate baseline, not an equivalent impact engine; "
                    "quality is reviewed separately in ground-truth-report.md"
                ),
            }
            print(json.dumps(benchmark_report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
