#!/usr/bin/env python3
"""Real-repository PR-E context and test-selection benchmark."""

from __future__ import annotations

import json
import platform
import resource
import statistics
import subprocess
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from extendcodeagent.core.config import ConfigLayer, ConfigResolver
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.service import ProjectIntelligenceApplication

REPO = Path(__file__).resolve().parents[2]


def main() -> None:
    resolved = ConfigResolver().resolve(
        ConfigLayer(
            "benchmark",
            {
                "project_intelligence": {
                    "enabled": True,
                    "mode": "advisory",
                    "capabilities": {
                        name: "advisory"
                        for name in (
                            "graph",
                            "twin",
                            "semantic",
                            "impact",
                            "test_selection",
                            "test_obsolescence",
                            "runtime",
                            "context",
                        )
                    },
                }
            },
        )
    )
    config = resolved.project_intelligence
    with tempfile.TemporaryDirectory(prefix="extendcodeagent-pr-e-benchmark-") as directory:
        database = Path(directory) / "graph.db"
        with ProjectIntelligenceApplication(
            REPO,
            database,
            CapabilityPolicy.from_config(config),
            max_items=config.context.max_items,
            max_depth=config.analysis.max_depth,
        ) as application:
            started = time.perf_counter()
            symbols = application.symbol("reconcile_observations")
            cold_ms = _elapsed_ms(started)
            if not symbols["items"]:
                raise RuntimeError("benchmark target symbol was not indexed")
            target = symbols["items"][0]["canonical_ref"]
            standard, standard_samples = _measure(
                lambda: application.context(
                    "change runtime freshness safely",
                    (target,),
                    profile="standard",
                    token_budget=config.context.max_tokens,
                )
            )
            weak, weak_samples = _measure(
                lambda: application.context(
                    "change runtime freshness safely",
                    (target,),
                    profile="weak",
                    token_budget=config.context.max_tokens,
                )
            )
            selection, selection_samples = _measure(lambda: application.tests((target,)))
        if weak["used_tokens"] >= standard["used_tokens"]:
            raise RuntimeError("weak context was not smaller than standard context")
        if not selection["items"] or selection["fallback"] is not None:
            raise RuntimeError("real-repository test selection did not find safe candidates")
        evidence = {
            "commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
            ).strip(),
            "environment": {
                "os": f"{platform.system()} {platform.release()} {platform.machine()}",
                "python": platform.python_version(),
            },
            "repository": str(REPO),
            "target_ref": target,
            "cold_graph_and_symbol_ms": cold_ms,
            "standard_context": _context_metrics(standard, standard_samples),
            "weak_context": _context_metrics(weak, weak_samples),
            "test_selection": {
                **_latency_metrics(selection_samples),
                "candidate_count": len(selection["items"]),
                "candidate_refs": [item["canonical_ref"] for item in selection["items"]],
                "fallback": selection["fallback"],
                "health_states": [item["state"] for item in selection["health"]],
            },
            "database_bytes": database.stat().st_size,
            "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        }
        print(json.dumps(evidence, indent=2, sort_keys=True))


def _measure(operation: Callable[[], dict[str, Any]]) -> tuple[dict[str, Any], list[float]]:
    samples: list[float] = []
    result: dict[str, Any] = {}
    for _ in range(20):
        started = time.perf_counter()
        result = operation()
        samples.append(round((time.perf_counter() - started) * 1_000, 4))
    return result, samples


def _context_metrics(value: dict[str, Any], samples: list[float]) -> dict[str, Any]:
    return {
        **_latency_metrics(samples),
        "items": len(value["items"]),
        "used_tokens": value["used_tokens"],
        "token_budget": value["token_budget"],
        "truncated": value["truncated"],
    }


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
