from __future__ import annotations

import json
import platform
import resource
import sys
import tempfile
import time
from pathlib import Path

from extendcodeagent.core.contracts import ProjectRef
from extendcodeagent.storage import SqliteGraphStore
from extendcodeagent.twin import TwinService


def main(root: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="extendcodeagent-pr-b-") as temporary:
        database = Path(temporary) / "graph.db"
        project = ProjectRef("benchmark", "default", root.resolve().as_uri())
        with SqliteGraphStore(database) as store:
            twin = TwinService(store)
            started = time.perf_counter()
            cold = twin.open(project)
            cold_ms = (time.perf_counter() - started) * 1000
            started = time.perf_counter()
            incremental = twin.refresh(project, changed_paths=("pyproject.toml",))
            incremental_ms = (time.perf_counter() - started) * 1000
            started = time.perf_counter()
            snapshot = twin.snapshot(project)
            query_ms = (time.perf_counter() - started) * 1000
            wal = Path(f"{database}-wal")
            storage_bytes = database.stat().st_size + (wal.stat().st_size if wal.exists() else 0)
            report = {
                "schema": "extendcodeagent.pr-b-benchmark.v1",
                "repository": str(root.resolve()),
                "source_files": len(snapshot.nodes),
                "cold_snapshot_ms": round(cold_ms, 3),
                "incremental_refresh_ms": round(incremental_ms, 3),
                "snapshot_query_ms": round(query_ms, 3),
                "db_and_wal_size_bytes": storage_bytes,
                "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "cold_revision": cold.revision is not None,
                "incremental_revision_changed": incremental.revision != cold.revision,
                "python": platform.python_version(),
                "platform": platform.platform(),
                "limitation": "File-level graph refresh still performs a bounded workspace fingerprint scan.",
            }
            print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
