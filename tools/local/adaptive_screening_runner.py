#!/usr/bin/env python3
"""Evidence-directed B0a adaptive screening orchestration.

The sealed 714-cell matrix remains the hard maximum.  This runner creates a
model-free execution plan first, then executes only its unresolved frontier
with one model process at a time and CPU-side preparation/finalization workers.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from statistics import median
from typing import Any

from extendcodeagent.core.config import ConfigLayer, ConfigResolver
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.evaluation import EvaluationTraceLog
from extendcodeagent.evaluation.adaptive import (
    DEPTH_ORDER,
    TOOL_CAPABILITIES,
    capability_task_relevance,
    depth_equivalence_classes,
    efficiency_summary,
    next_depth,
    reasoning_input_fingerprint,
    representative_depths,
    sequential_ablation_decision,
)
from extendcodeagent.evaluation.causal import forced_use_compliance, selection_assessment
from extendcodeagent.service import ProjectIntelligenceApplication
from tools.local import evaluation_runner as legacy

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "docs/evaluation/b0a-adaptive-screening-policy-v1.json"
COMPATIBLE_PRODUCT_TRANSITIONS = ROOT / "docs/evaluation/b0a-compatible-product-transitions-v1.json"
DEFAULT_SUCCESS_REPORTS = (ROOT / ".evaluation/unified-v1/b0a-pilot-7e58751.json",)
DEPTH_CAPABILITIES = ("semantic", "impact", "test_selection", "context")


class AdaptiveError(RuntimeError):
    """Raised when adaptive evidence cannot support a truthful scheduling decision."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AdaptiveError(f"cannot read {path}: {error}") from error
    if not isinstance(value, dict):
        raise AdaptiveError(f"{path} root must be an object")
    return value


def _digest(value: Mapping[str, Any]) -> str:
    body = {key: item for key, item in value.items() if key != "seal"}
    payload = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _sealed(value: dict[str, Any]) -> dict[str, Any]:
    body = {key: item for key, item in value.items() if key != "seal"}
    return {
        **body,
        "seal": {"algorithm": "sha256", "canonical_payload": _digest(body)},
    }


def _verify_policy() -> dict[str, Any]:
    policy = _load(POLICY)
    legacy._verify_seal(policy, "B0a adaptive screening policy")
    base = _load(legacy.B0A_PLAN)
    quality = _load(legacy.B0A_QUALITY_TARGET)
    matrix = _load(legacy.MATRIX)
    suite = _load(legacy.TASK_SUITE)
    expected = {
        "base_screening_plan_seal": base["seal"]["canonical_payload"],
        "quality_target_seal": quality["seal"]["canonical_payload"],
    }
    for key, seal in expected.items():
        if policy.get(key) != seal:
            raise AdaptiveError(f"adaptive policy {key} is stale")
    unchanged = policy["unchanged_contracts"]
    if unchanged.get("matrix_seal") != matrix["seal"]["canonical_payload"]:
        raise AdaptiveError("adaptive policy matrix seal is stale")
    if unchanged.get("task_suite_seal") != suite["seal"]["canonical_payload"]:
        raise AdaptiveError("adaptive policy task-suite seal is stale")
    if policy.get("hard_maximum_cells") != 714:
        raise AdaptiveError("adaptive policy must retain the 714-cell hard maximum")
    return policy


def _json_lines(path: Path) -> Iterable[dict[str, Any]]:
    if not path.is_file():
        return ()
    values: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            values.append(value)
    return values


def _tool_inputs(log_path: Path) -> dict[str, list[dict[str, Any]]]:
    observed: defaultdict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for event in _json_lines(log_path):
        if event.get("type") != "tool_use" or not isinstance(event.get("part"), dict):
            continue
        part = event["part"]
        tool = str(part.get("tool") or "").removeprefix("extendcodeagent_")
        state = part.get("state")
        if tool not in TOOL_CAPABILITIES or not isinstance(state, dict):
            continue
        # The call itself establishes task relevance even when a sidecar error
        # prevented completion.  Replaying its structured input in deterministic
        # preflight distinguishes capability output from runtime-route failure.
        if not isinstance(state.get("input"), dict):
            continue
        values = state["input"]
        key = json.dumps(values, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        observed[tool][key] = values
    return {
        tool: [values[key] for key in sorted(values)] for tool, values in sorted(observed.items())
    }


def _steps(log_path: Path) -> int:
    return sum(
        event.get("type") == "step_finish"
        or (isinstance(event.get("part"), dict) and event["part"].get("type") == "step-finish")
        for event in _json_lines(log_path)
    )


def _nearest_rank(values: Sequence[int], percentile: float) -> int:
    if not values:
        raise AdaptiveError("cannot derive a percentile from an empty successful-run population")
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _report_log_path(report: Mapping[str, Any], cell_id: str) -> Path | None:
    trace = report.get("trace_log")
    if not isinstance(trace, str):
        return None
    return Path(trace).resolve().parent / "logs" / f"{cell_id}.jsonl"


def derive_success_limits(reports: Sequence[Path]) -> dict[str, Any]:
    population: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in reports:
        if not path.is_file():
            continue
        report = _load(path)
        for result in report.get("results", ()):
            if (
                not isinstance(result, dict)
                or result.get("outcome") != "PASS"
                or result.get("model_tier") != "local-practical"
            ):
                continue
            identity = str(
                result.get("original_result_sha256")
                or result.get("trace_id")
                or result.get("cell_id")
            )
            if identity in seen:
                continue
            log_path = _report_log_path(report, str(result.get("cell_id")))
            if log_path is None or not log_path.is_file():
                continue
            seen.add(identity)
            population.append(
                {
                    "cell_id": result["cell_id"],
                    "report": str(path.resolve()),
                    "steps": _steps(log_path),
                    "tool_calls": int(result.get("tool_calls") or 0),
                    "output_tokens": int(result.get("output_tokens") or 0),
                }
            )
    if not population:
        raise AdaptiveError("no successful local-practical logs are available for limit derivation")
    distributions = {
        name: [int(item[name]) for item in population]
        for name in ("steps", "tool_calls", "output_tokens")
    }
    percentiles = {
        name: {
            "p95": _nearest_rank(values, 0.95),
            "p99": _nearest_rank(values, 0.99),
        }
        for name, values in distributions.items()
    }
    step_margin = math.ceil(percentiles["steps"]["p99"] * 0.10)
    output_margin = math.ceil(percentiles["output_tokens"]["p99"] * 0.10)
    return {
        "population": population,
        "population_count": len(population),
        "percentiles": percentiles,
        "margin_policy": "ceil(p99 * 0.10)",
        "step_limit": percentiles["steps"]["p99"] + step_margin,
        "output_limit": min(8192, percentiles["output_tokens"]["p99"] + output_margin),
        "sealed_provider_output_ceiling": 8192,
    }


class WorkspaceTemplates:
    """Create isolated cell workspaces from one prepared template per task."""

    def __init__(self, root: Path, tasks: Mapping[str, dict[str, Any]]) -> None:
        root = root.resolve()
        self.root = root
        self.tasks = tasks
        self.template_root = root / "templates"
        self.workspace_root = root / "workspaces"
        self.template_root.mkdir(parents=True, exist_ok=True)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.strategy: str | None = None

    def ensure_template(self, task_id: str) -> Path:
        target = self.template_root / task_id
        if not target.exists():
            legacy._prepare(self.tasks[task_id], target)
        return target

    def _create(self, template: Path, target: Path, strategy: str) -> None:
        if target.exists():
            raise AdaptiveError(f"workspace already exists: {target}")
        if strategy == "git_worktree":
            result = subprocess.run(
                ["git", "-C", str(template), "worktree", "add", "--detach", str(target), "HEAD"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        elif strategy == "reflink":
            target.mkdir(parents=True)
            result = subprocess.run(
                ["cp", "-a", "--reflink=always", f"{template}/.", str(target)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        else:
            raise AdaptiveError(f"unknown workspace strategy: {strategy}")
        if result.returncode:
            if target.exists():
                shutil.rmtree(target)
            raise AdaptiveError(f"{strategy} workspace creation failed: {result.stderr[-500:]}")

    def _discard(self, template: Path, target: Path, strategy: str) -> None:
        if strategy == "git_worktree":
            subprocess.run(
                ["git", "-C", str(template), "worktree", "remove", "--force", str(target)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        if target.exists():
            shutil.rmtree(target)

    def benchmark(self, task_id: str, repetitions: int = 5) -> dict[str, Any]:
        template = self.ensure_template(task_id)
        measurements: dict[str, list[float]] = {}
        failures: dict[str, str] = {}
        for strategy in ("git_worktree", "reflink"):
            samples: list[float] = []
            try:
                for repetition in range(1, repetitions + 1):
                    target = self.root / "workspace-benchmark" / f"{strategy}-{repetition}"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    started = time.perf_counter()
                    self._create(template, target, strategy)
                    samples.append((time.perf_counter() - started) * 1000)
                    self._discard(template, target, strategy)
            except AdaptiveError as error:
                failures[strategy] = str(error)
            if samples:
                measurements[strategy] = samples
        if not measurements:
            raise AdaptiveError(f"no workspace template strategy succeeded: {failures}")
        selected = min(measurements, key=lambda item: median(measurements[item]))
        self.strategy = selected
        return {
            "task_id": task_id,
            "repetitions": repetitions,
            "samples_ms": {
                key: [round(item, 3) for item in value] for key, value in measurements.items()
            },
            "median_ms": {key: round(median(value), 3) for key, value in measurements.items()},
            "failures": failures,
            "selected": selected,
            "selection_rule": "lowest successful median preparation wall time",
        }

    def prepare(self, task_id: str, workspace_id: str) -> Path:
        if self.strategy is None:
            raise AdaptiveError("workspace strategy has not been benchmarked")
        template = self.ensure_template(task_id)
        safe_id = "".join(
            character if character.isalnum() or character in "-_." else "_"
            for character in workspace_id
        )
        if safe_id != workspace_id:
            digest = hashlib.sha256(workspace_id.encode()).hexdigest()[:8]
            safe_id = f"{safe_id}--{digest}"
        target = self.workspace_root / safe_id
        self._create(template, target, self.strategy)
        return target

    def prepare_retry_safe(self, task_id: str, workspace_id: str) -> Path:
        """Preserve an interrupted workspace and allocate a fresh isolated retry."""

        safe_id = "".join(
            character if character.isalnum() or character in "-_." else "_"
            for character in workspace_id
        )
        if safe_id != workspace_id:
            digest = hashlib.sha256(workspace_id.encode()).hexdigest()[:8]
            safe_id = f"{safe_id}--{digest}"
        candidate = safe_id
        attempt = 0
        while (self.workspace_root / candidate).exists():
            attempt += 1
            candidate = f"{safe_id}--retry{attempt}"
        return self.prepare(task_id, candidate)

    def discard(self, task_id: str, target: Path) -> None:
        """Remove one generated cell workspace after its evidence is durable."""

        if self.strategy is None:
            raise AdaptiveError("workspace strategy has not been benchmarked")
        resolved = target.resolve(strict=False)
        if resolved.parent != self.workspace_root.resolve():
            raise AdaptiveError(f"refusing to discard a non-cell workspace: {resolved}")
        template = self.ensure_template(task_id)
        self._discard(template, resolved, self.strategy)


def _policy_for_depth(capability: str, depth: str) -> tuple[CapabilityPolicy, Any]:
    values = {
        "project_intelligence": {
            "enabled": True,
            "mode": "active",
            "capabilities": {name: "active" for name in legacy.CONFIGURABLE_CAPABILITIES},
            "depth": {
                "profile": "balanced",
                "capabilities": {capability: {"preferred": depth}},
            },
        }
    }
    resolved = ConfigResolver().resolve(ConfigLayer("adaptive-preflight", values))
    config = resolved.project_intelligence
    return CapabilityPolicy.from_config(config), config


def _invoke_preflight(
    application: ProjectIntelligenceApplication, tool: str, values: dict[str, Any]
) -> dict[str, Any]:
    if tool == "pi_symbol":
        return application.symbol(str(values["query"]), view="compact")
    if tool == "pi_impact":
        return application.impact(
            tuple(values["changed_refs"]),
            min_confidence=float(values.get("min_confidence", 0.0)),
            max_depth=values.get("max_depth"),
            include_historical=bool(values.get("include_historical", False)),
            view="compact",
        )
    if tool == "pi_tests":
        return application.tests(
            tuple(values.get("changed_refs", ())),
            objective=str(values.get("objective", "")),
            view="compact",
        )
    if tool == "pi_context":
        return application.context(
            str(values["objective"]),
            tuple(values.get("target_refs", ())),
            profile=str(values.get("profile", "standard")),
            token_budget=int(values.get("token_budget") or 2_000),
        )
    raise AdaptiveError(f"no deterministic depth preflight adapter for {tool}")


def _preflight_one(
    templates: WorkspaceTemplates,
    task_id: str,
    capability: str,
    depth: str,
    tool: str,
    values: dict[str, Any],
) -> dict[str, Any]:
    workspace_id = f"preflight--{capability}--{task_id}--{depth}"
    started = time.perf_counter()
    workspace = templates.prepare(task_id, workspace_id)
    policy, config = _policy_for_depth(capability, depth)
    database = templates.root / "preflight-db" / f"{workspace_id}.db"
    database.parent.mkdir(parents=True, exist_ok=True)
    with ProjectIntelligenceApplication(
        workspace,
        database,
        policy,
        max_items=config.context.max_items,
        max_depth=config.analysis.max_depth,
        analyzers=config.analyzers,
    ) as application:
        opened = application.process_event((), "b0a-adaptive-preflight")
        output = _invoke_preflight(application, tool, values)
    return {
        "task_id": task_id,
        "capability": capability,
        "depth": depth,
        "tool": tool,
        "input": values,
        "twin_revision_id": opened.get("revision_id"),
        "output": output,
        "wall_ms": round((time.perf_counter() - started) * 1000, 3),
    }


def _active_tool_inputs(
    report: Mapping[str, Any], raw_root: Path
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    result: defaultdict[str, defaultdict[str, dict[str, dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    for cell in report.get("results", ()):
        if not isinstance(cell, dict) or cell.get("arm") != "active":
            continue
        task_id = str(cell["task_id"])
        log_path = raw_root / "logs" / f"{cell['cell_id']}.jsonl"
        for tool, variants in _tool_inputs(log_path).items():
            for values in variants:
                key = json.dumps(values, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                result[task_id][tool][key] = values
    return {
        task_id: {
            tool: [variants[key] for key in sorted(variants)]
            for tool, variants in sorted(tools.items())
        }
        for task_id, tools in sorted(result.items())
    }


def _depth_tool(
    capability: str, inputs: Mapping[str, Sequence[dict[str, Any]]]
) -> tuple[str, dict[str, Any]] | None:
    preferred = {
        "semantic": "pi_symbol",
        "impact": "pi_impact",
        "test_selection": "pi_tests",
        "context": "pi_context",
    }[capability]
    values = inputs.get(preferred)
    if not values:
        return None
    # Multiple observed inputs are retained in plan evidence.  The first
    # canonical variant is the deterministic representative for equivalence.
    return preferred, dict(values[0])


def _compatible_result(
    result: Mapping[str, Any], log_path: Path, limits: Mapping[str, Any]
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if result.get("model_tier") != "local-practical":
        reasons.append("model_tier_changed")
    if result.get("provider_failure") is not None:
        reasons.append("provider_failure")
    if not log_path.is_file():
        reasons.append("raw_log_missing")
    else:
        if _steps(log_path) > int(limits["step_limit"]):
            reasons.append("derived_step_limit_exceeded")
        shared_venv = str((ROOT / ".venv").resolve())
        if any(
            shared_venv in json.dumps(event.get("part", {}), ensure_ascii=False)
            for event in _json_lines(log_path)
            if event.get("type") == "tool_use"
        ):
            reasons.append("shared_evaluation_venv_access")
    if int(result.get("output_tokens") or 0) > int(limits["output_limit"]):
        reasons.append("derived_output_limit_exceeded")
    return not reasons, reasons


def analyze(
    source_report_path: Path,
    source_raw_root: Path,
    output: Path,
    analysis_root: Path,
    success_reports: Sequence[Path],
) -> None:
    started = time.perf_counter()
    policy = _verify_policy()
    source = _load(source_report_path)
    if source.get("schedule", {}).get("scope") != "b0a-screening":
        raise AdaptiveError("source checkpoint is not the preserved 714-cell B0a screen")
    schedule = legacy.plan("b0a-screening")
    if len(schedule["cells"]) != policy["hard_maximum_cells"]:
        raise AdaptiveError("legacy schedule no longer matches the 714-cell hard maximum")
    tasks = {item["id"]: item for item in _load(legacy.TASK_SUITE)["tasks"]}
    active = [
        item
        for item in source.get("results", ())
        if isinstance(item, dict) and item.get("arm") == "active"
    ]
    expected_active = {item["cell_id"] for item in schedule["cells"] if item["arm"] == "active"}
    if {item["cell_id"] for item in active} != expected_active:
        raise AdaptiveError("adaptive relevance requires the complete 21-cell active trace")
    relevance = capability_task_relevance(active)
    inputs = _active_tool_inputs(source, source_raw_root)
    reports = [source_report_path, *success_reports]
    limits = derive_success_limits(reports)

    templates = WorkspaceTemplates(analysis_root / "workspace-state", tasks)
    benchmark = templates.benchmark("eca-symbol-001")
    preflight_requests: list[tuple[str, str, str, str, dict[str, Any]]] = []
    for task_id, observed in relevance.items():
        task_inputs = inputs.get(task_id, {})
        for capability in DEPTH_CAPABILITIES:
            if capability not in observed["capabilities"]:
                continue
            selected = _depth_tool(capability, task_inputs)
            if selected is None:
                continue
            tool, values = selected
            for depth in DEPTH_ORDER:
                preflight_requests.append((task_id, capability, depth, tool, values))
    preflights: list[dict[str, Any]] = []
    # A task template is immutable after construction. Build each once before
    # worker fan-out so concurrent preflight never races inside git clone/setup.
    for task_id in sorted({request[0] for request in preflight_requests}):
        templates.ensure_template(task_id)
    with ThreadPoolExecutor(max_workers=min(4, os.cpu_count() or 1)) as workers:
        futures = [
            workers.submit(_preflight_one, templates, *request) for request in preflight_requests
        ]
        for future in futures:
            preflights.append(future.result())
    preflights.sort(
        key=lambda item: (item["task_id"], item["capability"], DEPTH_ORDER.index(item["depth"]))
    )

    depth_classes: dict[str, dict[str, Any]] = {}
    grouped: defaultdict[tuple[str, str], dict[str, Any]] = defaultdict(dict)
    for result in preflights:
        grouped[(result["task_id"], result["capability"])][result["depth"]] = result["output"]
    for (task_id, capability), outputs in sorted(grouped.items()):
        classes = depth_equivalence_classes(outputs)
        depth_classes[f"{capability}:{task_id}"] = {
            "classes": classes,
            "representatives": list(representative_depths(classes)),
        }

    source_results = {
        item["cell_id"]: item for item in source.get("results", ()) if isinstance(item, dict)
    }
    source_wall_ms = [
        int(item.get("wall_ms") or 0) for item in source_results.values() if item.get("wall_ms")
    ]
    source_total_wall_ms = sum(source_wall_ms)
    observed_cell_per_second = (
        len(source_wall_ms) / (source_total_wall_ms / 1000) if source_total_wall_ms else 0.0
    )
    migrated: list[dict[str, Any]] = []
    invalidated: list[dict[str, Any]] = []
    for cell_id, result in sorted(source_results.items()):
        log_path = source_raw_root / "logs" / f"{cell_id}.jsonl"
        compatible, reasons = _compatible_result(result, log_path, limits)
        if compatible:
            migrated.append(
                {
                    "cell_id": cell_id,
                    "source_result_sha256": hashlib.sha256(
                        json.dumps(
                            result, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                        ).encode()
                    ).hexdigest(),
                    "source_log_sha256": hashlib.sha256(log_path.read_bytes()).hexdigest(),
                }
            )
        else:
            invalidated.append({"cell_id": cell_id, "reasons": reasons})

    skips: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for cell in schedule["cells"]:
        arm = str(cell["arm"])
        task_id = str(cell["task_id"])
        reason: str | None = None
        if arm == "active":
            candidates.append(cell)
            continue
        kind, _, modifier = arm.partition(":")
        capability = modifier.split(":", 1)[0]
        relevant = capability in relevance.get(task_id, {}).get("capabilities", ())
        if not relevant:
            reason = "NOT_TESTED_NO_ACTIVE_USE"
        elif kind == "depth":
            _, depth = modifier.split(":", 1)
            key = f"{capability}:{task_id}"
            depth_info = depth_classes.get(key)
            if depth_info is None:
                reason = "NOT_TESTED_NO_ACTIVE_PREFLIGHT_INPUT"
            elif depth not in depth_info["representatives"]:
                reason = "SKIPPED_DEPTH_OUTPUT_EQUIVALENT"
        if reason is None:
            candidates.append(cell)
        else:
            skips.append(
                {
                    "cell_id": cell["cell_id"],
                    "arm": arm,
                    "task_id": task_id,
                    "reason": reason,
                    "avoids_llm_call": True,
                }
            )

    migrated_ids = {item["cell_id"] for item in migrated}
    candidate_ids = {item["cell_id"] for item in candidates}
    reusable_ids = migrated_ids & candidate_ids
    invalidated_ids = {item["cell_id"] for item in invalidated} & candidate_ids
    first_frontier = [
        item
        for item in candidates
        if int(item["repetition"]) == 1 and item["cell_id"] not in reusable_ids
    ]
    expected_new_calls = len(first_frontier)
    max_new_calls = len(candidate_ids - reusable_ids)
    result = _sealed(
        {
            "schema": 1,
            "classification": "B0A_ADAPTIVE_SCREENING_EXECUTION_PLAN",
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "policy": str(POLICY.relative_to(ROOT)),
            "policy_seal": policy["seal"]["canonical_payload"],
            "source_checkpoint": str(source_report_path.resolve()),
            "source_checkpoint_sha256": hashlib.sha256(source_report_path.read_bytes()).hexdigest(),
            "source_checkpoint_cells": source.get("executed_cells"),
            "source_checkpoint_preserved": True,
            "base_schedule": {
                "hard_maximum_cells": 714,
                "adaptive_candidate_max_cells": len(candidates),
                "expected_total_cells_before_first_decision": len(reusable_ids)
                + expected_new_calls,
                "expected_new_llm_calls_before_first_decision": expected_new_calls,
                "max_new_llm_calls": max_new_calls,
                "observed_source_cell_per_second": round(observed_cell_per_second, 6),
                "observed_source_wall_ms": {
                    "population_count": len(source_wall_ms),
                    "median": round(median(source_wall_ms), 3),
                    "p95": _nearest_rank(source_wall_ms, 0.95),
                    "p99": _nearest_rank(source_wall_ms, 0.99),
                },
                "estimated_new_model_wall_seconds": {
                    "expected_frontier_at_observed_median": round(
                        expected_new_calls * median(source_wall_ms) / 1000, 3
                    ),
                    "hard_adaptive_max_at_observed_median": round(
                        max_new_calls * median(source_wall_ms) / 1000, 3
                    ),
                    "hard_adaptive_max_at_observed_p95": round(
                        max_new_calls * _nearest_rank(source_wall_ms, 0.95) / 1000, 3
                    ),
                },
                "estimation_basis": (
                    "exact next sequential decision frontier after deterministic skips "
                    "and compatible reuse"
                ),
            },
            "execution_scope": "local-only",
            "model": "Qwen3.6 27B",
            "endpoint": "127.0.0.1:8090",
            "context": 262144,
            "limits": limits,
            "relevance": relevance,
            "active_tool_inputs": inputs,
            "depth_preflight": {
                "wall_ms": round(sum(item["wall_ms"] for item in preflights), 3),
                "results": preflights,
                "equivalence": depth_classes,
            },
            "workspace_benchmark": benchmark,
            "workspace_strategy": benchmark["selected"],
            "migration": {
                "source_cells_considered": len(source_results),
                "compatible_cells": sorted(reusable_ids),
                "compatible_cell_count": len(reusable_ids),
                "invalidated_cells": invalidated,
                "invalidated_candidate_count": len(invalidated_ids),
                "surplus_compatible_cells": sorted(migrated_ids - candidate_ids),
            },
            "candidate_cells": candidates,
            "skips": skips,
            "skip_counts": dict(Counter(item["reason"] for item in skips)),
            "analysis_wall_ms": round((time.perf_counter() - started) * 1000, 3),
            "adoption_decisions_forbidden": True,
        }
    )
    legacy._write_report(output, result)


def _steps_in_text(value: str) -> int:
    count = 0
    for line in value.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        part = event.get("part") if isinstance(event, dict) else None
        if event.get("type") == "step_finish" or (
            isinstance(part, dict) and part.get("type") == "step-finish"
        ):
            count += 1
    return count


def _run_opencode_limited(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout: int,
    step_limit: int | None,
) -> tuple[str, str, int | None, bool, bool, str | None]:
    """Run one model process and stop only after an evidence-derived step boundary."""

    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    deadline = time.monotonic() + timeout
    stdout = ""
    stderr = ""
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                legacy._terminate_process_group(process)
                return stdout, stderr, None, True, False, legacy._provider_failure(stderr)
            try:
                stdout, stderr = process.communicate(timeout=min(0.5, remaining))
                return (
                    stdout,
                    stderr,
                    process.returncode,
                    False,
                    False,
                    legacy._provider_failure(stderr),
                )
            except subprocess.TimeoutExpired as error:
                stdout = legacy._partial_text(error.stdout, stdout)
                stderr = legacy._partial_text(error.stderr, stderr)
                provider_failure = legacy._provider_failure(stderr)
                if provider_failure:
                    legacy._terminate_process_group(process)
                    final_stdout, final_stderr = process.communicate()
                    return (
                        final_stdout or stdout,
                        final_stderr or stderr,
                        process.returncode,
                        False,
                        False,
                        provider_failure,
                    )
                if step_limit is not None and _steps_in_text(stdout) >= step_limit:
                    legacy._terminate_process_group(process)
                    final_stdout, final_stderr = process.communicate()
                    return (
                        final_stdout or stdout,
                        final_stderr or stderr,
                        process.returncode,
                        False,
                        True,
                        None,
                    )
    except BaseException:
        legacy._terminate_process_group(process)
        raise


def _agent_only(
    cell: dict[str, Any],
    task: dict[str, Any],
    workspace: Path,
    *,
    output_limit: int,
    step_limit: int | None,
    attach_url: str | None = None,
) -> dict[str, Any]:
    env, model_id = legacy._environment(
        cell["arm"], cell["model_tier"], workspace, output_limit=output_limit
    )
    mode, _ = legacy._arm_mode(cell["arm"])
    instruction = legacy._task_instruction(cell, task, mode)
    command = [
        _load(legacy.MATRIX)["execution"]["opencode_executable"],
        "run",
        "--format",
        "json",
        "--print-logs",
        "--log-level",
        "ERROR",
        "--auto",
        "--model",
        model_id,
        "--dir",
        str(workspace),
    ]
    if mode == "native":
        command.append("--pure")
    if attach_url is not None:
        command.extend(["--attach", attach_url])
    command.append(instruction)
    started = time.monotonic()
    try:
        stdout, stderr, process_exit, timed_out, step_limited, provider_failure = (
            _run_opencode_limited(
                command,
                cwd=ROOT,
                env=env,
                timeout=task["timeout_seconds"],
                step_limit=step_limit,
            )
        )
        model_wall_ms = round((time.monotonic() - started) * 1000)
    finally:
        cleanup_started = time.monotonic()
        sidecars_terminated = _stop_evaluation_sidecars(workspace)
        sidecar_cleanup_wall_ms = round((time.monotonic() - cleanup_started) * 1000)
    return {
        "cell": cell,
        "task": task,
        "workspace": workspace,
        "model_id": model_id,
        "stdout": stdout,
        "stderr": stderr,
        "process_exit": process_exit,
        "timed_out": timed_out,
        "step_limited": step_limited,
        "provider_failure": provider_failure,
        "opencode_lifecycle": "persistent_attach" if attach_url else "per_cell_run",
        "model_wall_ms": model_wall_ms,
        "evaluation_sidecars_terminated": sidecars_terminated,
        "sidecar_cleanup_wall_ms": sidecar_cleanup_wall_ms,
    }


def _sidecar_matches_workspace(cmdline: Sequence[str], workspace: Path) -> bool:
    """Match only the evaluation sidecar rooted at one exact workspace."""

    try:
        module = cmdline.index("extendcodeagent.adapters.local_sidecar")
        root_flag = cmdline.index("--root")
        root_value = cmdline[root_flag + 1]
    except (ValueError, IndexError):
        return False
    if module == 0 or cmdline[module - 1] != "-m":
        return False
    return Path(root_value).resolve(strict=False) == workspace.resolve(strict=False)


def _evaluation_sidecar_pids(workspace: Path, proc_root: Path = Path("/proc")) -> list[int]:
    pids: list[int] = []
    for process_dir in proc_root.iterdir():
        if not process_dir.name.isdigit():
            continue
        try:
            raw = (process_dir / "cmdline").read_bytes()
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
            continue
        cmdline = [item.decode(errors="replace") for item in raw.split(b"\0") if item]
        if _sidecar_matches_workspace(cmdline, workspace):
            pids.append(int(process_dir.name))
    return sorted(pids)


def _stop_evaluation_sidecars(workspace: Path) -> int:
    """Bound one cell's sidecar lifetime without touching any other workspace."""

    pids = _evaluation_sidecar_pids(workspace)
    for pid in pids:
        with contextlib.suppress(ProcessLookupError):
            os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + 2.0
    remaining = set(pids)
    while remaining and time.monotonic() < deadline:
        remaining = {pid for pid in remaining if Path(f"/proc/{pid}").exists()}
        if remaining:
            time.sleep(0.02)
    for pid in remaining:
        with contextlib.suppress(ProcessLookupError):
            os.kill(pid, signal.SIGKILL)
    return len(pids)


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _finalize_agent(
    raw: dict[str, Any], raw_root: Path, *, persist_fragment: bool = True
) -> dict[str, Any]:
    cell = raw["cell"]
    task = raw["task"]
    workspace = Path(raw["workspace"])
    log_path = raw_root / "logs" / f"{cell['cell_id']}.jsonl"
    stderr_path = log_path.with_suffix(".stderr.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(raw["stdout"], encoding="utf-8")
    stderr_path.write_text(raw["stderr"], encoding="utf-8")
    oracle_started = time.monotonic()
    oracle = legacy._run(
        [
            str(legacy.PYTHON),
            str(legacy.E3_HARNESS),
            "oracle",
            "--manifest",
            str(legacy.TASK_SUITE),
            "--task",
            task["id"],
            "--workspace",
            str(workspace),
        ],
        ROOT,
        600,
    )
    oracle_wall_ms = round((time.monotonic() - oracle_started) * 1000)
    measured = legacy._metrics(log_path)
    if raw["provider_failure"]:
        outcome = "UNAVAILABLE"
    elif raw["timed_out"] or raw["step_limited"]:
        outcome = "TIMEOUT"
    elif measured["errors"]:
        outcome = "UNAVAILABLE" if "APIError" in measured["errors"] else "FAIL"
    elif raw["process_exit"] != 0 or oracle.returncode != 0:
        outcome = "FAIL"
    else:
        outcome = "PASS"
    result = {
        **cell,
        "model_id": raw["model_id"],
        "outcome": outcome,
        "process_exit": raw["process_exit"],
        "provider_failure": raw["provider_failure"],
        "oracle_exit": oracle.returncode,
        "oracle_diagnostic": oracle.stderr.strip()[-500:],
        "model_wall_ms": raw["model_wall_ms"],
        "evaluation_sidecars_terminated": raw.get("evaluation_sidecars_terminated", 0),
        "sidecar_cleanup_wall_ms": raw.get("sidecar_cleanup_wall_ms", 0),
        "oracle_wall_ms": oracle_wall_ms,
        "wall_ms": raw["model_wall_ms"] + oracle_wall_ms,
        "limit_reason": "STEP_LIMIT_P99_MARGIN" if raw["step_limited"] else None,
        "llm_call_execution": "executed",
        "log_sha256": hashlib.sha256(log_path.read_bytes()).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr_path.read_bytes()).hexdigest(),
        **measured,
    }
    result["outcome_attribution"] = legacy._outcome_attribution(
        task,
        workspace,
        arm=cell["arm"],
        oracle_exit=oracle.returncode,
        observed_pi_facts=measured["observed_pi_facts"],
    )
    modes, depths = legacy._trace_capabilities(cell["arm"])
    repository_revision = next(
        item["revision"]
        for item in _load(legacy.TASK_SUITE)["repositories"]
        if item["id"] == cell["repository_id"]
    )
    result["reasoning_input_fingerprint"] = reasoning_input_fingerprint(
        {
            "project_workspace": f"{cell['repository_id']}/{task['id']}",
            "revision": repository_revision,
            "task_intent": task["instruction"],
            "capability_depth": depths,
            "selected_evidence_ids": measured["selected_evidence_ids"],
            "relevant_environment": {
                "model": raw["model_id"],
                "execution_scope": "local-only",
                "capability_modes": modes,
            },
        }
    )
    evaluation_use_policy = str(cell.get("pi_use_policy") or "")
    if evaluation_use_policy in {"forced_pi", "forced_off", "forced_ablation", "auto_pi"}:
        evaluation_plan = _load(legacy.EVALUATION_PI_PLAN)
        entry = next(item for item in evaluation_plan["tasks"] if item["task_id"] == task["id"])
        if evaluation_use_policy in {"forced_pi", "forced_off", "forced_ablation"}:
            result["forced_use_compliance"] = forced_use_compliance(entry, result)
        else:
            result["selection_assessment"] = selection_assessment(
                entry, result["pi_tools"], result["pi_capabilities_used"]
            )
    if persist_fragment:
        fragment = raw_root / "result-fragments" / f"{cell['cell_id']}.json"
        _atomic_json(fragment, result)
    return result


def _persist_agent_capture(raw: Mapping[str, Any], raw_root: Path) -> Path:
    capture = {
        **raw,
        "workspace": str(raw["workspace"]),
    }
    path = raw_root / "agent-captures" / f"{raw['cell']['cell_id']}.json"
    _atomic_json(path, capture)
    return path


def _persist_provider_attempt(raw: Mapping[str, Any], raw_root: Path) -> Path:
    capture = {**raw, "workspace": str(raw["workspace"])}
    suffix = time.time_ns()
    path = raw_root / "provider-attempts" / f"{raw['cell']['cell_id']}--{suffix}.json"
    _atomic_json(path, capture)
    return path


def _execute_batch(
    cells: Sequence[dict[str, Any]],
    *,
    tasks: Mapping[str, dict[str, Any]],
    templates: WorkspaceTemplates,
    raw_root: Path,
    output_limit: int,
    step_limit: int | None,
) -> list[dict[str, Any]]:
    if not cells:
        return []
    for task_id in sorted({str(cell["task_id"]) for cell in cells}):
        templates.ensure_template(task_id)
    results: list[Future[dict[str, Any]]] = []
    prepared: dict[str, Future[Path]] = {}
    try:
        with ThreadPoolExecutor(max_workers=min(4, os.cpu_count() or 1)) as cpu:
            prepared = {
                cell["cell_id"]: cpu.submit(
                    templates.prepare_retry_safe, cell["task_id"], cell["cell_id"]
                )
                for cell in cells
            }
            for cell in cells:
                workspace = prepared[cell["cell_id"]].result()
                raw = _agent_only(
                    cell,
                    tasks[cell["task_id"]],
                    workspace,
                    output_limit=output_limit,
                    step_limit=step_limit,
                )
                # Persist completed model work before CPU oracle/parsing begins. A
                # resume can finish this capture without repeating identical reasoning.
                if raw["provider_failure"]:
                    _persist_provider_attempt(raw, raw_root)
                    results.append(
                        cpu.submit(_finalize_agent, raw, raw_root, persist_fragment=False)
                    )
                    break
                _persist_agent_capture(raw, raw_root)
                results.append(cpu.submit(_finalize_agent, raw, raw_root))
            return [future.result() for future in results]
    finally:
        discard = getattr(templates, "discard", None)
        if discard is not None:
            cells_by_id = {str(cell["cell_id"]): cell for cell in cells}
            for cell_id, future in prepared.items():
                if not future.done() or future.cancelled():
                    continue
                try:
                    workspace = future.result()
                except Exception:
                    continue
                discard(str(cells_by_id[cell_id]["task_id"]), workspace)


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _wait_for_server(process: subprocess.Popen[str], port: int, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            _, stderr = process.communicate()
            raise AdaptiveError(
                f"persistent OpenCode server exited before ready: {stderr.strip()[-500:]}"
            )
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.25):
                return
        except OSError:
            time.sleep(0.1)
    legacy._terminate_process_group(process)
    raise AdaptiveError("persistent OpenCode server readiness timed out")


def bridge_benchmark(
    plan_path: Path,
    reference_report_path: Path,
    raw_root: Path,
    output: Path,
    *,
    cell_id: str,
) -> None:
    """Compare one preserved per-cell result with one isolated attach result.

    One pair is intentionally insufficient to adopt a persistent lifecycle. It
    can reject the optimization on semantic drift, and records whether a later
    repeated Bridge would be justified without spending screening calls now.
    """

    legacy._require_clean_worktree()
    plan = _load(plan_path)
    legacy._verify_seal(plan, "B0a adaptive execution plan")
    current_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    if plan.get("source_revision") != current_revision:
        raise AdaptiveError("Bridge plan must be regenerated at the exact execution head")
    reference_report = _load(reference_report_path)
    reference = next(
        (
            item
            for item in reference_report.get("results", ())
            if isinstance(item, dict) and item.get("cell_id") == cell_id
        ),
        None,
    )
    if reference is None:
        raise AdaptiveError(f"Bridge reference cell is absent: {cell_id}")
    cell = next(
        (item for item in plan.get("candidate_cells", ()) if item.get("cell_id") == cell_id),
        None,
    )
    if cell is None:
        raise AdaptiveError(f"Bridge cell is outside the adaptive candidate set: {cell_id}")
    if cell.get("model_tier") != "local-practical":
        raise AdaptiveError("Bridge is restricted to the sealed local-practical route")
    if output.exists():
        raise AdaptiveError("Bridge output already exists")

    tasks = {item["id"]: item for item in _load(legacy.TASK_SUITE)["tasks"]}
    task = tasks[str(cell["task_id"])]
    templates = WorkspaceTemplates(raw_root / "workspace-state", tasks)
    templates.strategy = str(plan["workspace_strategy"])
    templates.ensure_template(str(cell["task_id"]))
    workspace = templates.prepare_retry_safe(str(cell["task_id"]), f"bridge--{cell_id}")
    env, _ = legacy._environment(
        str(cell["arm"]),
        str(cell["model_tier"]),
        workspace,
        output_limit=int(plan["limits"]["output_limit"]),
    )
    port = _free_loopback_port()
    executable = str(_load(legacy.MATRIX)["execution"]["opencode_executable"])
    server_command = [
        executable,
        "serve",
        "--hostname",
        "127.0.0.1",
        "--port",
        str(port),
        "--print-logs",
        "--log-level",
        "ERROR",
    ]
    mode, _ = legacy._arm_mode(str(cell["arm"]))
    if mode == "native":
        server_command.append("--pure")
    server = subprocess.Popen(
        server_command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        server_started = time.monotonic()
        _wait_for_server(server, port)
        startup_wall_ms = round((time.monotonic() - server_started) * 1000)
        raw = _agent_only(
            dict(cell),
            task,
            workspace,
            output_limit=int(plan["limits"]["output_limit"]),
            step_limit=int(plan["limits"]["step_limit"]),
            attach_url=f"http://127.0.0.1:{port}",
        )
        _persist_agent_capture(raw, raw_root)
        attached = _finalize_agent(raw, raw_root)
    finally:
        legacy._terminate_process_group(server)
        server_stdout, server_stderr = server.communicate()
        (raw_root / "server.stdout.log").write_text(server_stdout, encoding="utf-8")
        (raw_root / "server.stderr.log").write_text(server_stderr, encoding="utf-8")

    oracle_contract = task.get("oracle", {})
    oracle_contract_sha256 = hashlib.sha256(
        json.dumps(
            oracle_contract, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    same_oracle_result = reference.get("outcome") == attached.get("outcome") and reference.get(
        "oracle_exit"
    ) == attached.get("oracle_exit")
    reference_wall_ms = float(reference.get("model_wall_ms") or reference.get("wall_ms") or 0)
    attached_wall_ms = float(attached.get("model_wall_ms") or 0)
    reduction_ratio = (
        (reference_wall_ms - attached_wall_ms) / reference_wall_ms if reference_wall_ms else 0.0
    )
    result = _sealed(
        {
            "schema": 1,
            "classification": "B0A_OPENCODE_PERSISTENCE_BRIDGE",
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "source_revision": current_revision,
            "execution_scope": "local-only",
            "model": "Qwen3.6 27B",
            "endpoint": "127.0.0.1:8090",
            "context": 262144,
            "output_limit": int(plan["limits"]["output_limit"]),
            "cell_id": cell_id,
            "arm": cell["arm"],
            "workspace_isolation": "fresh_git_worktree",
            "session_isolation": "new_attach_session_no_continue",
            "evidence_isolation": "separate_raw_root",
            "control": {
                "source": str(reference_report_path),
                "lifecycle": "per_cell_run",
                "outcome": reference.get("outcome"),
                "oracle_exit": reference.get("oracle_exit"),
                "model_wall_ms": reference_wall_ms,
            },
            "persistent_attach": {
                "outcome": attached.get("outcome"),
                "oracle_exit": attached.get("oracle_exit"),
                "model_wall_ms": attached_wall_ms,
                "server_startup_wall_ms": startup_wall_ms,
                "result": attached,
            },
            "oracle_contract_sha256": oracle_contract_sha256,
            "oracle_result_equivalent": same_oracle_result,
            "model_wall_reduction_ratio": round(reduction_ratio, 6),
            "meaningful_reduction_threshold": 0.10,
            "persistent_mode_adopted": False,
            "decision": (
                "REJECT_ORACLE_OUTCOME_MISMATCH"
                if not same_oracle_result
                else "KEEP_PER_CELL_RUN_INSUFFICIENT_REPEATED_SPEEDUP_EVIDENCE"
            ),
            "decision_basis": (
                "Persistent lifecycle requires oracle equivalence and repeated meaningful speedup; "
                "one attach observation cannot establish the latter."
            ),
            "additional_llm_calls": 1,
        }
    )
    legacy._write_report(output, result)


def _product_semantics_compatible(source_revision: str) -> tuple[bool, list[str]]:
    changed = subprocess.check_output(
        [
            "git",
            "diff",
            "--name-only",
            source_revision,
            "HEAD",
            "--",
            "src/extendcodeagent",
            "adapters/opencode/src",
            "adapters/opencode/dist/src/plugin.js",
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    material = [path for path in changed if not path.startswith("src/extendcodeagent/evaluation/")]
    if not material:
        return True, []
    manifest = _load(COMPATIBLE_PRODUCT_TRANSITIONS)
    legacy._verify_seal(manifest, "compatible product transitions")
    transitions = manifest.get("transitions")
    if not isinstance(transitions, list):
        raise AdaptiveError("compatible product transitions must be a list")
    unresolved: list[str] = []
    for path in material:
        try:
            source = subprocess.check_output(["git", "show", f"{source_revision}:{path}"], cwd=ROOT)
            current = (ROOT / path).read_bytes()
        except (subprocess.CalledProcessError, OSError):
            unresolved.append(path)
            continue
        source_sha256 = hashlib.sha256(source).hexdigest()
        current_sha256 = hashlib.sha256(current).hexdigest()
        approved = any(
            isinstance(item, Mapping)
            and item.get("path") == path
            and item.get("source_sha256") == source_sha256
            and item.get("current_sha256") == current_sha256
            and item.get("change_class") == "PROCESS_LIFECYCLE_ONLY"
            for item in transitions
        )
        if not approved:
            unresolved.append(path)
    return not unresolved, unresolved


def _migrated_result(
    result: Mapping[str, Any], source_revision: str, current_revision: str
) -> dict[str, Any]:
    original = json.dumps(
        result, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return {
        **result,
        "result_origin": "COMPATIBILITY_MIGRATION",
        "original_runner_revision": source_revision,
        "validated_by_runner_revision": current_revision,
        "original_result_sha256": hashlib.sha256(original).hexdigest(),
        "latency_status": "LEGACY_RUNNER_SEPARATE",
        "llm_call_execution": "reused",
    }


def _adaptive_report(
    plan: Mapping[str, Any],
    results: Sequence[dict[str, Any]],
    skips: Sequence[dict[str, Any]],
    provider_attempts: Sequence[dict[str, Any]],
    decisions: Mapping[str, Any],
    trace_log: EvaluationTraceLog,
    started: float,
) -> dict[str, Any]:
    minimum_depths = {
        key: str(value["minimum_sufficient_depth"])
        for key, value in decisions.items()
        if isinstance(value, dict) and value.get("minimum_sufficient_depth")
    }
    migrated = sum(item.get("llm_call_execution") == "reused" for item in results)
    completed_ids = {item["cell_id"] for item in results}
    provider_gap_pending = any(
        item.get("cell_id") not in completed_ids for item in provider_attempts
    )
    efficiency = efficiency_summary(
        requested_calls=int(plan["base_schedule"]["hard_maximum_cells"]),
        results=results,
        skips=skips,
        deterministic_pi_wall_ms=float(plan["depth_preflight"]["wall_ms"]),
        total_wall_ms=(time.monotonic() - started) * 1000,
        reused_evidence_count=migrated,
        invalidated_evidence_count=int(plan["migration"]["invalidated_candidate_count"]),
        minimum_sufficient_depths=minimum_depths,
    )
    body = {
        "schema": 1,
        "classification": "B0A_ADAPTIVE_SCREENING_RESULT",
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "adaptive_plan": str(plan.get("seal", {}).get("canonical_payload")),
        "hard_maximum_cells": 714,
        "execution_scope": "local-only",
        "model": "Qwen3.6 27B",
        "endpoint": "127.0.0.1:8090",
        "context": 262144,
        "screening_output_limit": plan["limits"]["output_limit"],
        "screening_step_limit": plan["limits"]["step_limit"],
        "trace_log": str(trace_log.path),
        "executed_or_reused_cells": len(results),
        "outcomes": dict(Counter(item["outcome"] for item in results)),
        "results": list(results),
        "provider_attempts": list(provider_attempts),
        "provider_gap_pending": provider_gap_pending,
        "skips": list(skips),
        "skip_counts": dict(Counter(item["reason"] for item in skips)),
        "decisions": dict(decisions),
        "efficiency_metrics": efficiency,
        "adoption_decisions_forbidden": True,
    }
    return _sealed(body)


def run_adaptive(
    plan_path: Path,
    source_checkpoint: Path,
    raw_root: Path,
    output: Path,
    *,
    resume: bool,
) -> None:
    legacy._require_clean_worktree()
    plan = _load(plan_path)
    legacy._verify_seal(plan, "B0a adaptive execution plan")
    if plan.get("classification") != "B0A_ADAPTIVE_SCREENING_EXECUTION_PLAN":
        raise AdaptiveError("unsupported adaptive execution plan")
    source = _load(source_checkpoint)
    if hashlib.sha256(source_checkpoint.read_bytes()).hexdigest() != plan.get(
        "source_checkpoint_sha256"
    ):
        raise AdaptiveError("preserved source checkpoint no longer matches adaptive plan")
    current_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    if plan.get("source_revision") != current_revision:
        raise AdaptiveError("adaptive plan must be regenerated at the exact execution head")
    compatible, product_changes = _product_semantics_compatible(str(source["source_revision"]))
    if not compatible:
        raise AdaptiveError(
            f"product/adapter semantics changed; migration requires replay: {product_changes}"
        )
    if output.exists() and not resume:
        raise AdaptiveError("adaptive output exists; use --resume")
    raw_root.mkdir(parents=True, exist_ok=True)
    tasks = {item["id"]: item for item in _load(legacy.TASK_SUITE)["tasks"]}
    cell_map = {item["cell_id"]: item for item in plan["candidate_cells"]}
    compatible_ids = set(plan["migration"]["compatible_cells"])
    source_results = {
        item["cell_id"]: item
        for item in source.get("results", ())
        if isinstance(item, dict) and item["cell_id"] in compatible_ids
    }
    reusable = {
        cell_id: _migrated_result(result, source["source_revision"], current_revision)
        for cell_id, result in source_results.items()
    }
    results_by_id: dict[str, dict[str, Any]] = {}
    provider_attempts: list[dict[str, Any]] = []
    skips_by_id = {item["cell_id"]: dict(item) for item in plan.get("skips", ())}
    decisions: dict[str, Any] = {}
    if resume and output.is_file():
        previous = _load(output)
        if previous.get("adaptive_plan") != plan["seal"]["canonical_payload"]:
            raise AdaptiveError("resume output uses another adaptive plan")
        results_by_id.update({item["cell_id"]: item for item in previous.get("results", ())})
        provider_attempts.extend(previous.get("provider_attempts", ()))
        skips_by_id.update({item["cell_id"]: item for item in previous.get("skips", ())})
        decisions.update(previous.get("decisions", {}))
    fragment_root = raw_root / "result-fragments"
    if fragment_root.is_dir():
        for fragment in sorted(fragment_root.glob("*.json")):
            result = _load(fragment)
            if result.get("cell_id") in cell_map:
                results_by_id[result["cell_id"]] = result
    recovered_results: list[dict[str, Any]] = []
    capture_root = raw_root / "agent-captures"
    if capture_root.is_dir():
        for capture_path in sorted(capture_root.glob("*.json")):
            capture = _load(capture_path)
            cell_id = capture.get("cell", {}).get("cell_id")
            if cell_id in cell_map and cell_id not in results_by_id:
                recovered_results.append(_finalize_agent(capture, raw_root))

    templates = WorkspaceTemplates(raw_root / "workspace-state", tasks)
    templates.strategy = str(plan["workspace_strategy"])
    trace_log = EvaluationTraceLog(raw_root / "traces.jsonl")
    trace_log.replay()
    started = time.monotonic()

    def add_result(result: dict[str, Any]) -> None:
        results_by_id[result["cell_id"]] = result
        legacy._append_trace(trace_log, result, tasks[result["task_id"]])

    def add_skip(cell: Mapping[str, Any], reason: str, **details: Any) -> None:
        skips_by_id[str(cell["cell_id"])] = {
            "cell_id": cell["cell_id"],
            "arm": cell["arm"],
            "task_id": cell["task_id"],
            "reason": reason,
            "avoids_llm_call": True,
            **details,
        }

    def checkpoint() -> None:
        report = _adaptive_report(
            plan,
            list(results_by_id.values()),
            list(skips_by_id.values()),
            provider_attempts,
            decisions,
            trace_log,
            started,
        )
        legacy._write_report(output, report)

    def consume(batch: Sequence[dict[str, Any]]) -> bool:
        """Record quality results and stop the whole frontier on a local provider gap."""

        gap = False
        for result in batch:
            if result.get("provider_failure"):
                provider_attempts.append({**result, "cell_pending": True})
                gap = True
            else:
                add_result(result)
        return gap

    for recovered in recovered_results:
        add_result(recovered)

    active_cells = [cell for cell in cell_map.values() if cell["arm"] == "active"]
    active_pending: list[dict[str, Any]] = []
    for cell in active_cells:
        if cell["cell_id"] in results_by_id:
            continue
        if cell["cell_id"] in reusable:
            add_result(reusable[cell["cell_id"]])
            add_skip(cell, "REUSED_COMPATIBLE_EVIDENCE")
        else:
            active_pending.append(cell)
    active_batch = _execute_batch(
        active_pending,
        tasks=tasks,
        templates=templates,
        raw_root=raw_root,
        output_limit=int(plan["limits"]["output_limit"]),
        step_limit=int(plan["limits"]["step_limit"]),
    )
    if consume(active_batch):
        checkpoint()
        return
    checkpoint()

    active_results = {
        (item["task_id"], int(item["repetition"])): item
        for item in results_by_id.values()
        if item["arm"] == "active"
    }
    for capability in legacy.CONFIGURABLE_CAPABILITIES:
        arm = f"ablation:{capability}"
        cells = sorted(
            [item for item in cell_map.values() if item["arm"] == arm],
            key=lambda item: (int(item["repetition"]), item["task_id"]),
        )
        if not cells:
            decisions[f"ablation:{capability}"] = {"decision": "NOT_TESTED_NO_ACTIVE_USE"}
            continue
        pair_rows = []
        for cell in cells:
            active_result = active_results.get((cell["task_id"], int(cell["repetition"])))
            pair_rows.append(
                {
                    "cell": cell,
                    "task_id": cell["task_id"],
                    "task_class": cell["task_class"],
                    "repetition": int(cell["repetition"]),
                    "active_outcome": (active_result.get("outcome") if active_result else None),
                }
            )
        final: dict[str, Any] | None = None
        for repetition in (1, 2, 3):
            round_cells: list[dict[str, Any]] = []
            for row in pair_rows:
                cell = row["cell"]
                if row["repetition"] != repetition or cell["cell_id"] in results_by_id:
                    continue
                if row["active_outcome"] != "PASS":
                    add_skip(
                        cell,
                        "NOT_TESTED_ACTIVE_NOT_PASS",
                        active_outcome=row["active_outcome"],
                    )
                elif cell["cell_id"] in reusable:
                    add_result(reusable[cell["cell_id"]])
                    add_skip(cell, "REUSED_COMPATIBLE_EVIDENCE")
                else:
                    round_cells.append(cell)
            round_batch = _execute_batch(
                round_cells,
                tasks=tasks,
                templates=templates,
                raw_root=raw_root,
                output_limit=int(plan["limits"]["output_limit"]),
                step_limit=int(plan["limits"]["step_limit"]),
            )
            if consume(round_batch):
                checkpoint()
                return
            pairs = [
                {
                    **{key: value for key, value in row.items() if key != "cell"},
                    "ablation_outcome": results_by_id.get(row["cell"]["cell_id"], {}).get(
                        "outcome"
                    ),
                }
                for row in pair_rows
            ]
            final = sequential_ablation_decision(
                pairs,
                threshold=2,
                current_repetition=repetition,
            )
            decisions[f"ablation:{capability}"] = final
            checkpoint()
            if not final["needs_next_repetition"]:
                reason = (
                    "SKIPPED_EARLY_POSITIVE"
                    if final["decision"] == "PROCEED_TO_B0B_EARLY"
                    else "SKIPPED_SEQUENTIAL_NO_REMAINING_SIGNAL"
                )
                for row in pair_rows:
                    cell = row["cell"]
                    if (
                        int(cell["repetition"]) > repetition
                        and cell["cell_id"] not in results_by_id
                        and cell["cell_id"] not in skips_by_id
                    ):
                        add_skip(cell, reason, screening_decision=final["decision"])
                break
        if final is None:
            decisions[f"ablation:{capability}"] = {"decision": "NOT_TESTED_NO_ACTIVE_USE"}

    depth_groups: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for cell in cell_map.values():
        if str(cell["arm"]).startswith("depth:"):
            _, capability, _ = str(cell["arm"]).split(":", 2)
            depth_groups[(capability, str(cell["task_id"]))].append(cell)
    for (capability, task_id), cells in sorted(depth_groups.items()):
        key = f"{capability}:{task_id}"
        representatives = tuple(plan["depth_preflight"]["equivalence"][key]["representatives"])
        outcomes: dict[str, str] = {}
        minimum: str | None = None
        for depth in representatives:
            depth_cells = sorted(
                [cell for cell in cells if cell["arm"] == f"depth:{capability}:{depth}"],
                key=lambda item: int(item["repetition"]),
            )
            observed: list[str] = []
            for repetition in (1, 2, 3):
                cell = next(item for item in depth_cells if int(item["repetition"]) == repetition)
                if cell["cell_id"] in results_by_id:
                    result = results_by_id[cell["cell_id"]]
                elif cell["cell_id"] in reusable:
                    result = reusable[cell["cell_id"]]
                    add_result(result)
                    add_skip(cell, "REUSED_COMPATIBLE_EVIDENCE")
                else:
                    depth_batch = _execute_batch(
                        [cell],
                        tasks=tasks,
                        templates=templates,
                        raw_root=raw_root,
                        output_limit=int(plan["limits"]["output_limit"]),
                        step_limit=int(plan["limits"]["step_limit"]),
                    )
                    if consume(depth_batch):
                        checkpoint()
                        return
                    result = depth_batch[0]
                observed.append(result["outcome"])
                if repetition == 1 and result["outcome"] == "PASS":
                    minimum = depth
                    break
                if repetition == 2 and observed.count("PASS") == 0:
                    break
                if repetition >= 2 and observed.count("PASS") >= 2:
                    minimum = depth
                    break
            outcomes[depth] = "PASS" if minimum == depth else "FAIL"
            if minimum is not None:
                break
        depth_decision = next_depth(representatives, outcomes)
        decisions[f"depth:{key}"] = {
            **depth_decision,
            "minimum_sufficient_depth": minimum,
            "representatives": list(representatives),
            "outcomes": outcomes,
        }
        if minimum is not None:
            minimum_rank = DEPTH_ORDER.index(minimum)
            for cell in cells:
                _, _, depth = str(cell["arm"]).split(":", 2)
                if (
                    DEPTH_ORDER.index(depth) > minimum_rank
                    and cell["cell_id"] not in results_by_id
                    and cell["cell_id"] not in skips_by_id
                ):
                    add_skip(
                        cell,
                        "SKIPPED_MINIMUM_SUFFICIENT_DEPTH",
                        minimum_sufficient_depth=minimum,
                    )
        checkpoint()

    for cell_id, cell in cell_map.items():
        if cell_id not in results_by_id and cell_id not in skips_by_id:
            add_skip(cell, "SKIPPED_ADAPTIVE_FRONTIER_CLOSED")
    checkpoint()


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    analyze_parser = sub.add_parser("analyze")
    analyze_parser.add_argument("--source-checkpoint", type=Path, required=True)
    analyze_parser.add_argument("--source-raw-root", type=Path, required=True)
    analyze_parser.add_argument("--analysis-root", type=Path, required=True)
    analyze_parser.add_argument("--success-report", type=Path, action="append", default=[])
    analyze_parser.add_argument("--output", type=Path, required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--plan", type=Path, required=True)
    run_parser.add_argument("--source-checkpoint", type=Path, required=True)
    run_parser.add_argument("--raw-root", type=Path, required=True)
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--resume", action="store_true")
    bridge_parser = sub.add_parser("bridge")
    bridge_parser.add_argument("--plan", type=Path, required=True)
    bridge_parser.add_argument("--reference-report", type=Path, required=True)
    bridge_parser.add_argument("--raw-root", type=Path, required=True)
    bridge_parser.add_argument("--output", type=Path, required=True)
    bridge_parser.add_argument("--cell-id", required=True)
    args = parser.parse_args()
    try:
        if args.command == "analyze":
            analyze(
                args.source_checkpoint.resolve(),
                args.source_raw_root.resolve(),
                args.output.resolve(),
                args.analysis_root.resolve(),
                tuple(path.resolve() for path in args.success_report) or DEFAULT_SUCCESS_REPORTS,
            )
        elif args.command == "run":
            run_adaptive(
                args.plan.resolve(),
                args.source_checkpoint.resolve(),
                args.raw_root.resolve(),
                args.output.resolve(),
                resume=args.resume,
            )
        else:
            bridge_benchmark(
                args.plan.resolve(),
                args.reference_report.resolve(),
                args.raw_root.resolve(),
                args.output.resolve(),
                cell_id=args.cell_id,
            )
    except (
        AdaptiveError,
        legacy.EvaluationError,
        KeyError,
        TypeError,
        ValueError,
        subprocess.TimeoutExpired,
    ) as error:
        print(f"adaptive screening error: {error}", file=sys.stderr)
        return 1
    print(f"adaptive screening {args.command}: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
