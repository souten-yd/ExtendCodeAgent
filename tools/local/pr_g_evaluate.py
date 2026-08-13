#!/usr/bin/env python3
"""Reproducible real-model PR-G mode/tier evaluation with compact output."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from extendcodeagent.core.config import ConfigLayer, ConfigResolver
from extendcodeagent.core.config.schema import ModelRole
from extendcodeagent.core.model_routing import (
    ModelAdapter,
    ModelRequest,
    ModelUnavailable,
    OpenAICompatibleAdapter,
    OpenCodeHostAdapter,
)
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.service import ProjectIntelligenceApplication

REPO = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    question: str
    expected: tuple[str, ...]
    facts: dict[str, object]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tiers",
        default="local-low,local-medium,host,frontier",
        help="comma-separated local-low,local-medium,host,frontier",
    )
    parser.add_argument("--modes", default="off,advisory,active", help="comma-separated modes")
    parser.add_argument("--scenarios", default="", help="optional comma-separated scenario names")
    args = parser.parse_args()
    tiers = tuple(item for item in args.tiers.split(",") if item)
    modes = tuple(item for item in args.modes.split(",") if item)
    before = _worktree_state()
    scenarios = _scenarios()
    if args.scenarios:
        selected = set(args.scenarios.split(","))
        scenarios = tuple(item for item in scenarios if item.name in selected)
    server: subprocess.Popen[str] | None = None
    base_url: str | None = None
    results: list[dict[str, object]] = []
    try:
        if any(item in {"host", "frontier"} for item in tiers):
            server, base_url = _start_opencode()
        for tier in tiers:
            try:
                adapter = _adapter(tier, base_url)
            except Exception as error:
                results.append({"tier": tier, "available": False, "error": str(error)})
                continue
            tier_modes = (("native",) + modes) if tier == "host" else modes
            for mode in tier_modes:
                mode_adapter = (
                    OpenCodeHostAdapter(
                        base_url or "", "opencode", "big-pickle", enable_native_tools=True
                    )
                    if tier == "host" and mode == "native"
                    else adapter
                )
                for scenario in scenarios:
                    results.append(_evaluate(mode_adapter, tier, mode, scenario))
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
    after = _worktree_state()
    output = {
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        "opencode_version": subprocess.check_output(["opencode", "--version"], text=True).strip(),
        "repository": str(REPO),
        "worktree_mutated": before != after,
        "results": results,
        "summary": _summary(results),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


def _scenarios() -> tuple[Scenario, ...]:
    capabilities = {
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
    }
    config = ConfigResolver().resolve(
        ConfigLayer(
            "pr-g-evaluation",
            {
                "project_intelligence": {
                    "enabled": True,
                    "mode": "advisory",
                    "capabilities": capabilities,
                }
            },
        )
    )
    target = "py://src.extendcodeagent.core.model_routing.router#PolicyModelRouter"
    with (
        tempfile.TemporaryDirectory(prefix="extendcodeagent-pr-g-facts-") as directory,
        ProjectIntelligenceApplication(
            REPO,
            Path(directory) / "graph.db",
            CapabilityPolicy.from_config(config.project_intelligence),
        ) as application,
    ):
        symbols = application.symbol("PolicyModelRouter")
        impacts = application.impact((target,))
        tests = application.tests((target,))
        current = application.source_revision()
        application.ingest_runtime(
            observation_id="old-green",
            kind="test",
            status="passed",
            started_at=datetime(2026, 8, 1, tzinfo=UTC),
            finished_at=datetime(2026, 8, 1, tzinfo=UTC),
            observed_refs=(
                target,
                "py://tests.unit.test_model_routing#test_local_only_never_calls_host_or_remote",
            ),
            command="pytest tests/unit/test_model_routing.py",
            source_revision=f"older-than-{current}",
            automatic=False,
        )
        stale = application.tests((target,))
    test_files = sorted({item["source_ref"] for item in tests["items"]})
    return (
        Scenario(
            "implementation_location",
            "Where is PolicyModelRouter implemented? Return its repository-relative file path.",
            ("src/extendcodeagent/core/model_routing/router.py",),
            {"symbols": symbols["items"][:2]},
        ),
        Scenario(
            "impact_assessment",
            "Which test file is directly impacted by changing PolicyModelRouter?",
            ("tests/unit/test_model_routing.py",),
            {"direct_impacts": impacts["direct"][:4]},
        ),
        Scenario(
            "test_selection",
            "Which focused test file should run for a PolicyModelRouter change?",
            ("tests/unit/test_model_routing.py",),
            {"selected_test_files": test_files, "fallback": tests["fallback"]},
        ),
        Scenario(
            "multi_file_bug",
            "A new routing signal is ignored. Name the two implementation files most likely "
            "involved.",
            ("contracts.py", "router.py"),
            {
                "request_contract": "src/extendcodeagent/core/model_routing/contracts.py",
                "routing_policy": "src/extendcodeagent/core/model_routing/router.py",
            },
        ),
        Scenario(
            "medium_strategy",
            "Choose the safer scope: narrow router+contract extension or unrelated subsystem "
            "rewrite.",
            ("narrow",),
            {
                "deterministic_metrics": {
                    "narrow_files": 2,
                    "rewrite_files": 20,
                    "compatibility": "preserve ModelAdapter",
                }
            },
        ),
        Scenario(
            "stale_test_risk",
            "What is the test-health risk when green evidence is from an older source revision?",
            ("stale",),
            {"health": stale["health"][:1]},
        ),
    )


def _evaluate(adapter: ModelAdapter, tier: str, mode: str, scenario: Scenario) -> dict[str, object]:
    if mode == "native":
        prompt = "Inspect this repository read-only using native tools. " + scenario.question
    elif mode == "off":
        prompt = scenario.question
    else:
        prefix = "Use this bounded Project Intelligence evidence"
        if mode == "active":
            prefix += " as the primary context; avoid unnecessary reads"
        prompt = (
            f"{prefix}: {json.dumps(scenario.facts, separators=(',', ':'))}\n{scenario.question}"
        )
    prompt += '\nReturn only JSON: {"answer":"..."}.'
    started = time.perf_counter()
    try:
        response = adapter.complete(
            ModelRequest(
                ModelRole.CODE_REASONER,
                prompt,
                context_tokens=max(1, len(prompt) // 4),
                max_output_tokens=128,
                reasoning_effort="none" if tier.startswith("local") else None,
                requires_structured_output=tier.startswith("local"),
            )
        )
        answer = _answer(response.text)
        lowered = answer.casefold()
        success = all(item.casefold() in lowered for item in scenario.expected)
        return {
            "tier": tier,
            "mode": mode,
            "scenario": scenario.name,
            "available": True,
            "success": success,
            "answer": answer[:500],
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "tool_calls": response.tool_calls,
            "cost": response.cost,
            "wall_ms": round((time.perf_counter() - started) * 1_000, 1),
        }
    except (ModelUnavailable, ValueError, KeyError) as error:
        return {
            "tier": tier,
            "mode": mode,
            "scenario": scenario.name,
            "available": False,
            "success": False,
            "error": str(error),
            "wall_ms": round((time.perf_counter() - started) * 1_000, 1),
        }


def _answer(text: str) -> str:
    try:
        raw = json.loads(text)
        return str(raw["answer"])
    except (json.JSONDecodeError, KeyError, TypeError):
        return text.strip()


def _adapter(tier: str, base_url: str | None) -> ModelAdapter:
    if tier == "local-low":
        return OpenAICompatibleAdapter("http://127.0.0.1:11434/v1", "qwen3:0.6b")
    if tier == "local-medium":
        return OpenAICompatibleAdapter("http://127.0.0.1:11434/v1", "qwen3.6-27b-q5_k_m:latest")
    if base_url is None:
        raise RuntimeError("OpenCode server is unavailable")
    if tier == "host":
        return OpenCodeHostAdapter(base_url, "opencode", "big-pickle")
    if tier == "frontier":
        return OpenCodeHostAdapter(base_url, "llama", "llama-3.3-70b-instruct")
    raise ValueError(f"unknown tier: {tier}")


def _start_opencode() -> tuple[subprocess.Popen[str], str]:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = int(probe.getsockname()[1])
    process = subprocess.Popen(
        ["opencode", "serve", "--hostname", "127.0.0.1", "--port", str(port)],
        cwd=REPO,
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout is not None else ""
            raise RuntimeError(f"OpenCode exited: {output}")
        try:
            with urllib.request.urlopen(f"{url}/global/health", timeout=0.5):
                return process, url
        except OSError:
            time.sleep(0.05)
    process.terminate()
    raise TimeoutError("OpenCode startup timed out")


def _summary(results: list[dict[str, object]]) -> dict[str, dict[str, int]]:
    grouped: dict[str, dict[str, int]] = {}
    for item in results:
        if "mode" not in item:
            continue
        key = f"{item['tier']}:{item['mode']}"
        group = grouped.setdefault(key, {"tasks": 0, "successes": 0, "tokens": 0})
        group["tasks"] += 1
        group["successes"] += int(bool(item.get("success")))
        group["tokens"] += _as_int(item.get("input_tokens")) + _as_int(item.get("output_tokens"))
    return grouped


def _as_int(value: object) -> int:
    return value if isinstance(value, int) else 0


def _worktree_state() -> str:
    return subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=REPO, text=True)


if __name__ == "__main__":
    main()
