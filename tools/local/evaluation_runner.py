#!/usr/bin/env python3
"""Validate, schedule, and execute the unified versioned evaluation matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any

from extendcodeagent.evaluation import EvaluationTrace, EvaluationTraceLog
from extendcodeagent.evaluation.compatibility import (
    CompatibilityError,
    audit_checkpoint,
    create_bridge_plan,
    digest,
    migrate_checkpoint,
    prove_bridge,
    verify_seal,
)

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "docs/evaluation/evaluation-matrix-v1.json"
TASK_SUITE = ROOT / "docs/evaluation/task-suite-v1.json"
LABELS = ROOT / "docs/evaluation/labels-v1/graph-quality-labels.json"
METRICS = ROOT / "docs/evaluation/pi-verification-integrated-metrics-v1.json"
CORPUS = ROOT / "docs/evaluation/test-portfolio-corpus-v1.json"
B0A_PLAN = ROOT / "docs/evaluation/b0a-screening-plan-v1.json"
B0A_ACTIVATION_PLAN = ROOT / "docs/evaluation/b0a-activation-plan-v1.json"
B0A_BOOTSTRAP = ROOT / "docs/evidence/final/b0a-bootstrap-environment-v1.json"
B0A_CHECKPOINT_COMPATIBILITY = ROOT / "docs/evaluation/b0a-checkpoint-compatibility-v1.json"
E3_HARNESS = ROOT / "tools/local/e3_task_suite.py"
PYTHON = ROOT / ".venv/bin/python"
PLUGIN = ROOT / "adapters/opencode/dist/src/plugin.js"
CONFIGURABLE_CAPABILITIES = (
    "graph",
    "twin",
    "semantic",
    "impact",
    "test_selection",
    "test_obsolescence",
    "context",
    "runtime",
    "blueprint",
    "convergence",
    "research",
    "traceability",
    "strategy",
)
B0A_ACTIVATION_MODELS = (
    "local-practical",
    "host-default",
    "frontier-sonnet",
    "frontier-codex",
)
LOCAL_SOURCES = {
    "extendcodeagent": ROOT,
    "controldeck": Path("/home/souten/ControlDeck"),
    "kasanecore": Path("/home/souten/KasaneCore"),
}


class EvaluationError(RuntimeError):
    """A deterministic matrix or execution failure."""


def _provider_failure(stderr: str) -> str | None:
    """Return a stable provider-gap category without persisting provider detail."""
    if "Rate limit exceeded" in stderr:
        return "RATE_LIMIT"
    if "AuthenticationError" in stderr:
        return "AUTHENTICATION"
    if "ProviderModelNotFoundError" in stderr:
        return "MODEL_NOT_FOUND"
    if "AI_RetryError: Failed after" in stderr:
        return "PROVIDER_RETRY_EXHAUSTED"
    return None


def _partial_text(value: str | bytes | None, previous: str) -> str:
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    if isinstance(value, str):
        return value
    return previous


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def _run_opencode(
    command: list[str], *, cwd: Path, env: dict[str, str], timeout: int
) -> tuple[str, str, int | None, bool, str | None]:
    """Run OpenCode while failing fast after its provider retries are exhausted."""
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
                _terminate_process_group(process)
                return stdout, stderr, None, True, _provider_failure(stderr)
            try:
                stdout, stderr = process.communicate(timeout=min(1.0, remaining))
                return (
                    stdout,
                    stderr,
                    process.returncode,
                    False,
                    _provider_failure(stderr),
                )
            except subprocess.TimeoutExpired as error:
                stdout = _partial_text(error.stdout, stdout)
                stderr = _partial_text(error.stderr, stderr)
                provider_failure = _provider_failure(stderr)
                if provider_failure and "AI_RetryError: Failed after" in stderr:
                    _terminate_process_group(process)
                    final_stdout, final_stderr = process.communicate()
                    return (
                        final_stdout or stdout,
                        final_stderr or stderr,
                        process.returncode,
                        False,
                        provider_failure,
                    )
    except BaseException:
        _terminate_process_group(process)
        raise


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise EvaluationError(f"cannot read {path}: {error}") from error
    if not isinstance(value, dict):
        raise EvaluationError(f"{path} root must be an object")
    return value


def _payload(value: dict[str, Any]) -> bytes:
    body = {key: item for key, item in value.items() if key != "seal"}
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(_payload(value)).hexdigest()


def _verify_seal(value: dict[str, Any], label: str) -> None:
    if value.get("seal") != {"algorithm": "sha256", "canonical_payload": _digest(value)}:
        raise EvaluationError(f"{label} seal does not match canonical payload")


def seal(path: Path) -> None:
    value = _load(path)
    value["seal"] = {"algorithm": "sha256", "canonical_payload": _digest(value)}
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate() -> None:
    matrix = _load(MATRIX)
    tasks = _load(TASK_SUITE)
    labels = _load(LABELS)
    metrics = _load(METRICS)
    corpus = _load(CORPUS)
    b0a_plan = _load(B0A_PLAN)
    activation_plan = _load(B0A_ACTIVATION_PLAN)
    bootstrap = _load(B0A_BOOTSTRAP)
    compatibility = _load(B0A_CHECKPOINT_COMPATIBILITY)
    _verify_seal(matrix, "matrix")
    _verify_seal(labels, "Layer A labels")
    expected_inputs = {
        "layer_b_task_suite": TASK_SUITE.relative_to(ROOT).as_posix(),
        "layer_a_labels": LABELS.relative_to(ROOT).as_posix(),
        "quality_corpus": CORPUS.relative_to(ROOT).as_posix(),
        "metric_contract": METRICS.relative_to(ROOT).as_posix(),
    }
    for key, expected in expected_inputs.items():
        if matrix["inputs"].get(key) != expected:
            raise EvaluationError(f"matrix input {key} does not reference {expected}")
    if matrix["inputs"]["layer_b_seal"] != tasks["seal"]["canonical_payload"]:
        raise EvaluationError("matrix Layer B seal does not match the E3 task suite")
    if matrix["inputs"]["layer_a_seal"] != labels["seal"]["canonical_payload"]:
        raise EvaluationError("matrix Layer A seal does not match the label set")
    if len(labels["cases"]) != labels["review_volume"]["cases"]:
        raise EvaluationError("Layer A review volume does not match its cases")
    if len({item["id"] for item in labels["cases"]}) != len(labels["cases"]):
        raise EvaluationError("Layer A label IDs are not unique")
    if tuple(matrix["ablation_capabilities"]) != CONFIGURABLE_CAPABILITIES:
        raise EvaluationError("matrix does not contain the exact configurable capability set")
    models = {item["id"]: item for item in matrix["model_tiers"]}
    if models["local-practical"]["base_url"] != "http://127.0.0.1:8090/v1":
        raise EvaluationError("local-practical is not sealed to port 8090")
    if models["local-practical"].get("max_output_tokens") != 8192:
        raise EvaluationError("local-practical output must remain bounded to 8192 tokens")
    if models["local-practical"].get("context_window_tokens") != 262144:
        raise EvaluationError("local-practical context must match the port-8090 server")
    if models["frontier-sonnet"]["model_id"] != "github-copilot/claude-sonnet-5":
        raise EvaluationError("Sonnet is not routed through the sealed Copilot model")
    if models["frontier-codex"]["model_id"] != "github-copilot/gpt-5.3-codex":
        raise EvaluationError("Codex is not routed through the sealed Copilot model")
    if models["local-low"]["status"] != "UNAVAILABLE":
        raise EvaluationError("local-low must remain truthfully unavailable")
    if not matrix["execution"]["ollama_forbidden"]:
        raise EvaluationError("matrix must forbid Ollama")
    if metrics["anti_overfit"]["corpus_manifest"] != expected_inputs["quality_corpus"]:
        raise EvaluationError("metric contract does not bind the quality corpus")
    if not corpus.get("repositories") or corpus.get("corpus_id") != "test-portfolio-v1":
        raise EvaluationError("quality corpus is empty or unsupported")
    _verify_seal(b0a_plan, "B0a screening plan")
    _verify_seal(activation_plan, "B0a PI activation plan")
    verify_seal(compatibility, "B0a checkpoint compatibility manifest")
    if b0a_plan["inputs"]["matrix_seal"] != matrix["seal"]["canonical_payload"]:
        raise EvaluationError("B0a plan matrix seal is stale")
    if b0a_plan["inputs"]["task_suite_seal"] != tasks["seal"]["canonical_payload"]:
        raise EvaluationError("B0a plan task-suite seal is stale")
    if bootstrap["screening_plan_seal"] != b0a_plan["seal"]["canonical_payload"]:
        raise EvaluationError("B0a bootstrap evidence does not match the screening plan")
    activation_inputs = activation_plan["inputs"]
    if activation_inputs["matrix_seal"] != matrix["seal"]["canonical_payload"]:
        raise EvaluationError("B0a activation-plan matrix seal is stale")
    if activation_inputs["task_suite_seal"] != tasks["seal"]["canonical_payload"]:
        raise EvaluationError("B0a activation-plan task-suite seal is stale")
    if activation_inputs["screening_plan_seal"] != b0a_plan["seal"]["canonical_payload"]:
        raise EvaluationError("B0a activation plan does not match the screening plan")
    if tuple(activation_plan["models"]) != B0A_ACTIVATION_MODELS:
        raise EvaluationError("B0a activation plan does not cover every permitted model route")
    pilot = activation_plan["pilot"]
    if pilot["model"] != "local-practical" or pilot["repetitions"] != 3:
        raise EvaluationError("B0a PI pilot must use three port-8090 local-practical repetitions")
    if pilot.get("initial_tranche_repetitions") != 1:
        raise EvaluationError("B0a PI pilot must evaluate one interleaved repetition first")
    if pilot.get("execution_order") != ["repetition", "task", "arm"]:
        raise EvaluationError("B0a PI pilot must interleave controls and active cells")
    if tuple(pilot["arms"]) != ("native", "off", "active"):
        raise EvaluationError("B0a PI pilot must preserve native/off/active controls")
    if not set(pilot["tasks"]) <= {item["id"] for item in tasks["tasks"]}:
        raise EvaluationError("B0a PI pilot references an unknown task")
    route_capabilities = {
        capability
        for route in activation_plan["capability_routes"]
        for capability in route["capabilities"]
    }
    if route_capabilities != set(CONFIGURABLE_CAPABILITIES):
        raise EvaluationError("B0a activation plan does not classify every configurable capability")
    known_tasks = {item["id"] for item in tasks["tasks"]}
    if any(
        not set(route.get("covered_tasks", ())) <= known_tasks
        for route in activation_plan["capability_routes"]
    ):
        raise EvaluationError("B0a capability route references an unknown covered task")
    assigned_tiers = set(b0a_plan["screening"]["capability_model_tiers"].values())
    if assigned_tiers != {"local-practical"}:
        raise EvaluationError("B0a screening runner only supports the sealed local-practical tier")
    eligibility = {item["id"]: item["eligibility"] for item in bootstrap["repositories"]}
    if not eligibility or set(eligibility.values()) - {"INCLUDED", "EXCLUDED_BOOTSTRAP_GAP"}:
        raise EvaluationError("B0a bootstrap eligibility is incomplete or invalid")


def _arms(matrix: dict[str, Any], scope: str) -> list[str]:
    base = [item["id"] for item in matrix["base_arms"]]
    if scope == "b0a-activation":
        return ["active"]
    if scope == "b0a-pilot":
        return list(_load(B0A_ACTIVATION_PLAN)["pilot"]["arms"])
    if scope == "b0a-baseline":
        return ["native", "off"]
    if scope == "b0a-screening":
        b0a_plan = _load(B0A_PLAN)
        ablations = [f"ablation:{item}" for item in matrix["ablation_capabilities"]]
        depths = [
            f"depth:{capability}:{depth}"
            for capability in b0a_plan["screening"]["depth_claim_capabilities"]
            for depth in matrix["depths"]
        ]
        return ["active", *ablations, *depths]
    if scope in {"smoke", "base"}:
        return ["native"] if scope == "smoke" else base
    ablations = [f"ablation:{item}" for item in matrix["ablation_capabilities"]]
    depths = [f"depth:{item}" for item in matrix["depths"]]
    return base + ablations + depths


def plan(
    scope: str,
    *,
    selected_arms: set[str] | None = None,
    selected_models: set[str] | None = None,
    selected_tasks: set[str] | None = None,
) -> dict[str, Any]:
    validate()
    matrix = _load(MATRIX)
    suite = _load(TASK_SUITE)
    tasks = suite["tasks"]
    b0a: dict[str, Any] | None = None
    if scope == "smoke":
        tasks = [tasks[0]]
    elif scope == "screening":
        wanted = set(matrix["screening"]["tuning_task_subset"])
        tasks = [item for item in tasks if item["id"] in wanted]
    elif scope in {"b0a-activation", "b0a-pilot", "b0a-baseline", "b0a-screening"}:
        b0a_plan = _load(B0A_PLAN)
        bootstrap = _load(B0A_BOOTSTRAP)
        eligibility = {item["id"]: item["eligibility"] for item in bootstrap["repositories"]}
        included = {key for key, value in eligibility.items() if value == "INCLUDED"}
        tasks = [item for item in tasks if item["repository_id"] in included]
        if scope == "b0a-activation":
            wanted = {_load(B0A_ACTIVATION_PLAN)["task_id"]}
            tasks = [item for item in tasks if item["id"] in wanted]
        elif scope == "b0a-pilot":
            wanted = set(_load(B0A_ACTIVATION_PLAN)["pilot"]["tasks"])
            tasks = [item for item in tasks if item["id"] in wanted]
        elif scope == "b0a-screening":
            wanted = set(b0a_plan["screening"]["task_subset"])
            tasks = [item for item in tasks if item["id"] in wanted]
        b0a = {
            "screening_plan_seal": b0a_plan["seal"]["canonical_payload"],
            "activation_plan_seal": _load(B0A_ACTIVATION_PLAN)["seal"]["canonical_payload"],
            "included_repositories": sorted(included),
            "excluded_repositories": sorted(set(eligibility) - included),
        }
    arms = _arms(matrix, scope)
    if selected_arms is not None:
        unknown = selected_arms - set(arms)
        if unknown:
            raise EvaluationError(f"unknown arms for {scope}: {sorted(unknown)}")
        arms = [item for item in arms if item in selected_arms]
    models = matrix["model_tiers"]
    if scope == "smoke":
        models = [item for item in models if item["id"] == "host-default"]
    elif scope == "b0a-activation":
        models = [item for item in models if item["id"] in B0A_ACTIVATION_MODELS]
    elif scope == "b0a-pilot":
        pilot_model = _load(B0A_ACTIVATION_PLAN)["pilot"]["model"]
        models = [item for item in models if item["id"] == pilot_model]
    elif scope == "b0a-screening":
        models = [item for item in models if item["id"] == "local-practical"]
    elif scope == "screening":
        models = [item for item in models if item["id"] in {"local-low", "local-practical"}]
    if selected_models is not None:
        unknown = selected_models - {item["id"] for item in models}
        if unknown:
            raise EvaluationError(f"unknown model tiers for {scope}: {sorted(unknown)}")
        models = [item for item in models if item["id"] in selected_models]
    if selected_tasks is not None:
        unknown = selected_tasks - {item["id"] for item in tasks}
        if unknown:
            raise EvaluationError(f"unknown tasks for {scope}: {sorted(unknown)}")
        tasks = [item for item in tasks if item["id"] in selected_tasks]
    cells: list[dict[str, Any]] = []
    for arm in arms:
        for model in models:
            for task in tasks:
                repetitions = 1 if scope == "b0a-activation" else int(model["minimum_repetitions"])
                for repetition in range(1, repetitions + 1):
                    prefix = f"{scope}--" if scope in {"b0a-activation", "b0a-pilot"} else ""
                    cells.append(
                        {
                            "cell_id": (
                                f"{prefix}{arm}--{model['id']}--{task['id']}--r{repetition}"
                            ),
                            "arm": arm,
                            "model_tier": model["id"],
                            "model_id": model.get("model_id"),
                            "model_status": model["status"],
                            "repository_id": task["repository_id"],
                            "task_id": task["id"],
                            "task_class": task["task_class"],
                            "split": task["split"],
                            "repetition": repetition,
                            "pi_activation_gate": scope == "b0a-activation",
                            "pi_effect_pilot": scope == "b0a-pilot",
                            "pi_screening": scope == "b0a-screening",
                        }
                    )
    if scope == "b0a-pilot":
        arm_order = {arm: index for index, arm in enumerate(arms)}
        task_order = {task["id"]: index for index, task in enumerate(tasks)}
        cells.sort(
            key=lambda cell: (
                cell["repetition"],
                task_order[cell["task_id"]],
                arm_order[cell["arm"]],
            )
        )
    result = {
        "schema": 1,
        "matrix_id": matrix["matrix_id"],
        "matrix_seal": matrix["seal"]["canonical_payload"],
        "task_suite_seal": suite["seal"]["canonical_payload"],
        "scope": scope,
        "cells": cells,
        "counts": {
            "cells": len(cells),
            "available": sum(item["model_status"] != "UNAVAILABLE" for item in cells),
            "unavailable": sum(item["model_status"] == "UNAVAILABLE" for item in cells),
        },
    }
    if b0a is not None:
        result["b0a"] = b0a
    return result


def _run(argv: list[str], cwd: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False
    )


def _prepare(task: dict[str, Any], workspace: Path) -> None:
    source = LOCAL_SOURCES[task["repository_id"]]
    result = _run(
        [
            str(PYTHON),
            str(E3_HARNESS),
            "prepare",
            "--manifest",
            str(TASK_SUITE),
            "--task",
            task["id"],
            "--destination",
            str(workspace),
            "--source",
            f"{task['repository_id']}={source}",
        ],
        ROOT,
        600,
    )
    if result.returncode:
        raise EvaluationError(result.stderr.strip())


def _arm_mode(arm: str) -> tuple[str, str | None]:
    if arm in {"native", "off", "shadow", "advisory", "active"}:
        return arm, None
    kind, _, value = arm.partition(":")
    if kind == "ablation" and value in CONFIGURABLE_CAPABILITIES:
        return "active", value
    if kind == "depth":
        capability, separator, depth = value.partition(":")
        if (
            separator
            and capability in CONFIGURABLE_CAPABILITIES
            and depth in {"D0", "D1", "D2", "D3", "D4"}
        ):
            return "active", value
    if kind == "depth" and value in {"D0", "D1", "D2", "D3", "D4"}:
        return "active", value
    raise EvaluationError(f"unknown arm: {arm}")


def _trace_capabilities(arm: str) -> tuple[dict[str, str], dict[str, str]]:
    mode, modifier = _arm_mode(arm)
    if mode == "native":
        return {}, {}
    modes = {
        capability: ("off" if mode == "off" or modifier == capability else mode)
        for capability in CONFIGURABLE_CAPABILITIES
    }
    depths = {capability: "D2" for capability, value in modes.items() if value != "off"}
    if modifier in {"D0", "D1", "D2", "D3", "D4"}:
        depths = {capability: modifier for capability in depths}
    elif modifier and ":" in modifier:
        capability, depth = modifier.split(":", 1)
        depths[capability] = depth
    return modes, depths


def _environment(arm: str, model_tier: str, workspace: Path) -> tuple[dict[str, str], str]:
    matrix = _load(MATRIX)
    model = next(item for item in matrix["model_tiers"] if item["id"] == model_tier)
    mode, modifier = _arm_mode(arm)
    config: dict[str, Any] = {}
    model_id = str(model.get("model_id") or "")
    if model_tier == "local-practical":
        provider = "eca-local-practical"
        config["provider"] = {
            provider: {
                "npm": "@ai-sdk/openai-compatible",
                "name": "E3 pinned local practical",
                "options": {"baseURL": model["base_url"]},
                "models": {
                    model_id: {
                        "name": "Qwen3.6 27B on port 8090",
                        "limit": {
                            "context": model["context_window_tokens"],
                            "output": model["max_output_tokens"],
                        },
                    }
                },
            }
        }
        model_id = f"{provider}/{model_id}"
    if mode != "native":
        config["plugin"] = [PLUGIN.as_uri()]
        capabilities = {
            capability: ("off" if mode == "off" or modifier == capability else mode)
            for capability in CONFIGURABLE_CAPABILITIES
        }
        pi: dict[str, Any] = {
            "enabled": mode != "off",
            "mode": mode,
            "capabilities": capabilities,
        }
        if modifier in {"D0", "D1", "D2", "D3", "D4"}:
            pi["depth"] = {
                "profile": "balanced",
                "capabilities": {
                    capability: {"preferred": modifier} for capability in CONFIGURABLE_CAPABILITIES
                },
            }
        elif modifier and ":" in modifier:
            capability, depth = modifier.split(":", 1)
            pi["depth"] = {
                "profile": "balanced",
                "capabilities": {capability: {"preferred": depth}},
            }
        project_config = workspace.parent / f"{workspace.name}-eca-config.json"
        project_config.write_text(
            json.dumps({"project_intelligence": pi}, separators=(",", ":")), encoding="utf-8"
        )
    env = {
        **_isolated_agent_environment(),
        "OPENCODE_CONFIG_CONTENT": json.dumps(config, separators=(",", ":")),
        "EXTENDCODEAGENT_PYTHON": str(PYTHON),
        "EXTENDCODEAGENT_MODE": mode,
    }
    if mode != "native":
        # Evaluation uses one canonical OpenCode plugin tool route. Registering the
        # same tools again through MCP creates duplicate names and independent
        # sidecars, which makes an arm's observed state route-dependent.
        env["EXTENDCODEAGENT_PROJECT_CONFIG"] = str(project_config)
    return env, model_id


def _isolated_agent_environment() -> dict[str, str]:
    env = dict(os.environ)
    root_venv_bin = (ROOT / ".venv/bin").resolve()
    path_entries = []
    for entry in env.get("PATH", "").split(os.pathsep):
        if not entry:
            continue
        try:
            resolved = Path(entry).resolve()
        except OSError:
            resolved = Path(entry)
        if resolved != root_venv_bin:
            path_entries.append(entry)
    env["PATH"] = os.pathsep.join(path_entries)
    env.pop("VIRTUAL_ENV", None)
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    env["PIP_REQUIRE_VIRTUALENV"] = "true"
    return env


def _metrics(log_path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "events": 0,
        "tool_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "errors": [],
        "pi_tools": [],
        "pi_capabilities_used": [],
        "selected_evidence_ids": [],
        "twin_revision_ids": [],
        "observed_capability_modes": {},
        "observed_capability_depths": {},
        "observed_pi_readiness": None,
        "pi_analysis_ms": 0,
        "pi_timing_ms": {
            "cold_twin_build_ms": 0.0,
            "snapshot_load_ms": 0.0,
            "adjacency_index_build_ms": 0.0,
            "query_execution_ms": 0.0,
            "json_serialization_ms": 0.0,
            "model_reasoning_after_tool_ms": 0,
        },
        "observed_pi_facts": [],
    }
    pi_tools: set[str] = set()
    pi_capabilities_used: set[str] = set()
    evidence_ids: set[str] = set()
    revision_ids: set[str] = set()
    pi_facts: set[str] = set()
    first_pi_tool_end: int | None = None
    last_event_end: int | None = None
    tool_intervals: list[tuple[int, int]] = []
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        result["events"] += 1
        event_end = _event_end_ms(event)
        if event_end is not None:
            last_event_end = max(last_event_end or event_end, event_end)
        if event.get("type") == "tool_use":
            result["tool_calls"] += 1
            part = event.get("part")
            if isinstance(part, dict):
                state = part.get("state")
                if isinstance(state, dict) and isinstance(state.get("time"), dict):
                    start, end = state["time"].get("start"), state["time"].get("end")
                    if isinstance(start, int) and isinstance(end, int) and end >= start:
                        tool_intervals.append((start, end))
                tool_name = str(part.get("tool") or "")
                if tool_name.startswith("pi_") or "_pi_" in tool_name:
                    pi_tools.add(tool_name.removeprefix("extendcodeagent_"))
                    if isinstance(state, dict):
                        timing = state.get("time")
                        if isinstance(timing, dict):
                            start, end = timing.get("start"), timing.get("end")
                            if isinstance(start, int) and isinstance(end, int) and end >= start:
                                result["pi_analysis_ms"] += end - start
                                first_pi_tool_end = min(first_pi_tool_end or end, end)
                        output = state.get("output")
                        if isinstance(output, str):
                            _observe_pi_output(
                                tool_name,
                                output,
                                evidence_ids,
                                revision_ids,
                                pi_facts,
                                result,
                                pi_capabilities_used,
                            )
        if event.get("type") == "error":
            error = event.get("error")
            result["errors"].append(error.get("name") if isinstance(error, dict) else str(error))
        part = event.get("part")
        if isinstance(part, dict) and part.get("type") == "step-finish":
            tokens = part.get("tokens") or {}
            result["input_tokens"] += int(tokens.get("input") or 0)
            result["output_tokens"] += int(tokens.get("output") or 0)
            result["reasoning_tokens"] += int(tokens.get("reasoning") or 0)
            cache = tokens.get("cache") or {}
            result["cache_read_tokens"] += int(cache.get("read") or 0)
            result["cache_write_tokens"] += int(cache.get("write") or 0)
    result["pi_tools"] = sorted(pi_tools)
    result["pi_capabilities_used"] = sorted(pi_capabilities_used)
    result["selected_evidence_ids"] = sorted(evidence_ids)
    result["twin_revision_ids"] = sorted(revision_ids)
    result["observed_pi_facts"] = sorted(pi_facts)
    if first_pi_tool_end is not None and last_event_end is not None:
        later_tool_ms = sum(
            max(0, end - max(start, first_pi_tool_end))
            for start, end in tool_intervals
            if end > first_pi_tool_end
        )
        result["pi_timing_ms"]["model_reasoning_after_tool_ms"] = max(
            0, last_event_end - first_pi_tool_end - later_tool_ms
        )
    return result


def _event_end_ms(event: dict[str, Any]) -> int | None:
    part = event.get("part")
    if isinstance(part, dict):
        state = part.get("state")
        if isinstance(state, dict) and isinstance(state.get("time"), dict):
            end = state["time"].get("end")
            if isinstance(end, int):
                return end
        timing = part.get("time")
        if isinstance(timing, dict) and isinstance(timing.get("end"), int):
            return int(timing["end"])
    timestamp = event.get("timestamp")
    return timestamp if isinstance(timestamp, int) else None


def _observe_pi_output(
    tool_name: str,
    output: str,
    evidence_ids: set[str],
    revision_ids: set[str],
    pi_facts: set[str],
    metrics: dict[str, Any],
    pi_capabilities_used: set[str],
) -> None:
    try:
        value = json.loads(output)
    except json.JSONDecodeError:
        return
    if not isinstance(value, dict):
        return
    _collect_string_facts(value, pi_facts)
    capabilities_used = value.get("capabilities_used")
    if isinstance(capabilities_used, list):
        pi_capabilities_used.update(
            item for item in capabilities_used if isinstance(item, str) and item
        )
    timing_value = value.get("timing")
    if isinstance(timing_value, dict):
        for key in (
            "cold_twin_build_ms",
            "snapshot_load_ms",
            "adjacency_index_build_ms",
            "query_execution_ms",
            "json_serialization_ms",
        ):
            observed = timing_value.get(key)
            if not isinstance(observed, int | float) or observed < 0:
                continue
            if key == "cold_twin_build_ms":
                metrics["pi_timing_ms"][key] = max(metrics["pi_timing_ms"][key], float(observed))
            else:
                metrics["pi_timing_ms"][key] = round(
                    metrics["pi_timing_ms"][key] + float(observed), 3
                )
    revision = value.get("revision_id")
    if isinstance(revision, str) and revision:
        revision_ids.add(revision)
    if tool_name.endswith("pi_status"):
        readiness = value.get("readiness")
        if isinstance(readiness, str):
            metrics["observed_pi_readiness"] = readiness
        capabilities = value.get("capabilities")
        if isinstance(capabilities, list):
            for capability in capabilities:
                if not isinstance(capability, dict) or not isinstance(capability.get("name"), str):
                    continue
                name = capability["name"]
                mode, depth = capability.get("mode"), capability.get("depth")
                if isinstance(mode, str):
                    metrics["observed_capability_modes"][name] = mode
                if isinstance(depth, str) and mode != "off":
                    metrics["observed_capability_depths"][name] = depth
        return
    _collect_evidence_refs(value, evidence_ids)


def _collect_string_facts(value: object, facts: set[str]) -> None:
    if isinstance(value, str):
        facts.add(value)
    elif isinstance(value, dict):
        for item in value.values():
            _collect_string_facts(item, facts)
    elif isinstance(value, list):
        for item in value:
            _collect_string_facts(item, facts)


def _collect_evidence_refs(value: object, evidence_ids: set[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"canonical_ref", "evidence_id", "source_ref"} and isinstance(item, str):
                evidence_ids.add(f"{key}:{item}")
            elif (key == "symbols" or key.endswith("_refs")) and isinstance(item, list):
                evidence_ids.update(
                    f"canonical_ref:{ref}" for ref in item if isinstance(ref, str) and "://" in ref
                )
            elif key in {"selected_tests", "tests"} or key.endswith(("_path", "_paths")):
                paths = item if isinstance(item, list) else [item]
                evidence_ids.update(
                    f"repo_path:{path}"
                    for path in paths
                    if isinstance(path, str)
                    and "/" in path
                    and not path.startswith(("/", "."))
                    and "://" not in path
                )
            else:
                _collect_evidence_refs(item, evidence_ids)
    elif isinstance(value, list):
        for item in value:
            _collect_evidence_refs(item, evidence_ids)


def _screening_required_tool(cell: dict[str, Any], task: dict[str, Any]) -> str | None:
    arm = str(cell.get("arm", ""))
    task_id = str(task.get("id", ""))
    if task_id == "eca-refactor-001" and arm in {
        "active",
        "ablation:blueprint",
        "ablation:strategy",
    }:
        return "pi_plan"
    if task_id == "cd-cross-boundary-001" and arm in {
        "active",
        "ablation:convergence",
        "ablation:traceability",
    }:
        return "pi_verify"
    return None


def _task_instruction(cell: dict[str, Any], task: dict[str, Any], mode: str) -> str:
    instruction = str(task["instruction"])
    if any(check["kind"] == "answer" for check in task["oracle"]["checks"]):
        instruction = (
            "Treat the requested .eca-eval/answer.json keys as an exact schema: include every "
            "requested key, preserve the requested scalar/list types, and add no explanation, "
            "evidence, or other unrequested keys. " + instruction
        )
    if cell.get("pi_activation_gate"):
        return (
            "This is a Project Intelligence activation gate. You MUST first call pi_status, then "
            "call pi_symbol with query select_tests, use the returned PI evidence, and only then "
            "complete the task. " + instruction
        )
    if cell.get("pi_effect_pilot") and mode == "active":
        required = _load(B0A_ACTIVATION_PLAN)["pilot"]["tasks"][task["id"]]
        return (
            "This is a Project Intelligence effect pilot. You MUST call these PI tools before "
            f"completing the task: {', '.join(required)}. Use their returned evidence in your "
            "analysis. When a compact PI response contains a field requested by the answer, copy "
            "that field without removing paths or expanding scalar/path values into explanation "
            "objects; a singular requested field may use the sole item from a one-item PI list. "
            "Then complete the original task. " + instruction
        )
    if cell.get("pi_effect_pilot") and mode == "off":
        return (
            "This is the disabled-extension control. You MUST call pi_status once to confirm PI is "
            "disabled, must not call another pi_* tool, and then complete the original task using "
            "normal OpenCode capabilities. " + instruction
        )
    required_tool = _screening_required_tool(cell, task)
    if cell.get("pi_screening") and required_tool is not None:
        return (
            "This capability screening cell MUST use pi_status and "
            f"{required_tool}. Use pi_symbol or pi_path first when canonical refs are needed. "
            "Treat an unavailable capability as unavailable; do not fabricate its result. Then "
            "complete the original task and its exact output contract. " + instruction
        )
    if mode in {"advisory", "active"}:
        return (
            "Use the available pi_* Project Intelligence tools where relevant. Preserve compact PI "
            "fields that match requested answer fields without removing paths or expanding them "
            "into explanation objects. " + instruction
        )
    return instruction


def _execute(cell: dict[str, Any], task: dict[str, Any], raw_root: Path) -> dict[str, Any]:
    if cell["model_status"] == "UNAVAILABLE":
        return {**cell, "outcome": "UNAVAILABLE", "reason": "sealed model-tier status"}
    workspace = raw_root / "workspaces" / cell["cell_id"]
    log_path = raw_root / "logs" / f"{cell['cell_id']}.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if workspace.exists():
        archive = raw_root / "archive"
        archive.mkdir(parents=True, exist_ok=True)
        destination = archive / f"{workspace.name}-{time.time_ns()}"
        workspace.rename(destination)
    _prepare(task, workspace)
    env, model_id = _environment(cell["arm"], cell["model_tier"], workspace)
    mode, _ = _arm_mode(cell["arm"])
    instruction = _task_instruction(cell, task, mode)
    command = [
        _load(MATRIX)["execution"]["opencode_executable"],
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
    command.append(instruction)
    started = time.monotonic()
    stdout, stderr, process_exit, timed_out, provider_failure = _run_opencode(
        command,
        cwd=ROOT,
        env=env,
        timeout=task["timeout_seconds"],
    )
    log_path.write_text(stdout, encoding="utf-8")
    stderr_path = log_path.with_suffix(".stderr.log")
    stderr_path.write_text(stderr, encoding="utf-8")
    oracle = _run(
        [
            str(PYTHON),
            str(E3_HARNESS),
            "oracle",
            "--manifest",
            str(TASK_SUITE),
            "--task",
            task["id"],
            "--workspace",
            str(workspace),
        ],
        ROOT,
        600,
    )
    measured = _metrics(log_path)
    if provider_failure:
        outcome = "UNAVAILABLE"
    elif timed_out:
        outcome = "TIMEOUT"
    elif measured["errors"]:
        outcome = "UNAVAILABLE" if "APIError" in measured["errors"] else "FAIL"
    elif process_exit != 0 or oracle.returncode != 0:
        outcome = "FAIL"
    else:
        outcome = "PASS"
    result = {
        **cell,
        "model_id": model_id,
        "outcome": outcome,
        "process_exit": process_exit,
        "provider_failure": provider_failure,
        "oracle_exit": oracle.returncode,
        "oracle_diagnostic": oracle.stderr.strip()[-500:],
        "wall_ms": round((time.monotonic() - started) * 1000),
        **measured,
    }
    result["outcome_attribution"] = _outcome_attribution(
        task,
        workspace,
        arm=cell["arm"],
        oracle_exit=oracle.returncode,
        observed_pi_facts=measured["observed_pi_facts"],
    )
    if provider_failure:
        result["outcome_attribution"] = {
            "classification": "PROVIDER_GAP",
            "required_fact_recall": None,
            "pi_required_fact_recall": None,
            "schema_valid": None,
            "final_exact_pass": False,
        }
    if cell.get("pi_activation_gate"):
        result["pi_activation"] = _activation_assessment(result)
    if cell.get("pi_effect_pilot") and mode == "active":
        result["pi_effect_observation"] = _pilot_active_assessment(result)
    elif cell.get("pi_effect_pilot") and mode == "off":
        result["pi_off_observation"] = _pilot_off_assessment(result)
    return result


def _outcome_attribution(
    task: dict[str, Any],
    workspace: Path,
    *,
    arm: str,
    oracle_exit: int,
    observed_pi_facts: list[str],
) -> dict[str, Any]:
    answer_checks = [item for item in task["oracle"]["checks"] if item["kind"] == "answer"]
    if not answer_checks:
        return {
            "classification": "PASS" if oracle_exit == 0 else "AGENT_REASONING_ERROR",
            "required_fact_recall": None,
            "pi_required_fact_recall": None,
            "schema_valid": None,
            "final_exact_pass": oracle_exit == 0,
        }
    check = answer_checks[0]
    expected = check["equals"]
    answer_path = workspace / check.get("path", ".eca-eval/answer.json")
    try:
        answer = json.loads(answer_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        answer = None
    schema_valid = (
        isinstance(answer, dict)
        and set(answer) == set(expected)
        and all(type(answer[key]) is type(value) for key, value in expected.items())
    )
    expected_facts = _field_facts(expected)
    actual_facts = _field_facts(answer if isinstance(answer, dict) else {})
    matched = expected_facts & actual_facts
    required_fact_recall = len(matched) / len(expected_facts) if expected_facts else 1.0
    expected_strings = {
        atom for key, value in expected.items() if key != "status" for atom in _string_atoms(value)
    }
    observed = set(observed_pi_facts)
    pi_fact_recall = (
        len(expected_strings & observed) / len(expected_strings) if expected_strings else None
    )
    exact = oracle_exit == 0
    if exact:
        classification = "PASS"
    elif arm == "active" and (pi_fact_recall or 0.0) < 1.0:
        classification = "RETRIEVAL_MISSING"
    elif not schema_valid or required_fact_recall == 1.0:
        classification = "PROJECTION_SCHEMA_ERROR"
    else:
        classification = "AGENT_REASONING_ERROR"
    return {
        "classification": classification,
        "required_fact_recall": round(required_fact_recall, 6),
        "pi_required_fact_recall": (
            round(pi_fact_recall, 6) if pi_fact_recall is not None else None
        ),
        "schema_valid": schema_valid,
        "final_exact_pass": exact,
    }


def _field_facts(value: dict[str, Any]) -> set[str]:
    return {
        f"{key}:{json.dumps(atom, ensure_ascii=False, sort_keys=True)}"
        for key, item in value.items()
        if key != "status"
        for atom in _atoms(item)
    }


def _atoms(value: object) -> list[object]:
    if isinstance(value, dict):
        return [atom for item in value.values() for atom in _atoms(item)]
    if isinstance(value, list):
        return [atom for item in value for atom in _atoms(item)]
    return [value]


def _string_atoms(value: object) -> set[str]:
    return {str(atom) for atom in _atoms(value) if isinstance(atom, str)}


def _activation_assessment(result: dict[str, Any]) -> dict[str, Any]:
    contract = _load(B0A_ACTIVATION_PLAN)["required_observations"]
    reasons: list[str] = []
    required_tools = set(contract["tools"])
    observed_tools = set(result.get("pi_tools", ()))
    if not required_tools <= observed_tools:
        reasons.append("required_pi_tools_not_observed")
    if result.get("observed_pi_readiness") != contract["readiness"]:
        reasons.append("pi_readiness_not_ready")
    expected_mode = contract["configurable_capability_mode"]
    modes = result.get("observed_capability_modes") or {}
    if any(modes.get(capability) != expected_mode for capability in CONFIGURABLE_CAPABILITIES):
        reasons.append("configurable_capability_mode_not_observed")
    expected_depth = contract["configurable_capability_depth"]
    depths = result.get("observed_capability_depths") or {}
    if any(depths.get(capability) != expected_depth for capability in CONFIGURABLE_CAPABILITIES):
        reasons.append("configurable_capability_depth_not_observed")
    if contract["twin_revision"] and not result.get("twin_revision_ids"):
        reasons.append("twin_revision_not_observed")
    evidence = result.get("selected_evidence_ids") or []
    if contract["selected_canonical_evidence"] and not any(
        str(item).startswith("canonical_ref:") for item in evidence
    ):
        reasons.append("canonical_evidence_not_observed")
    if contract["positive_pi_analysis_time"] and int(result.get("pi_analysis_ms") or 0) <= 0:
        reasons.append("pi_analysis_time_not_observed")
    if result.get("process_exit") != 0:
        reasons.append("opencode_process_failed")
    if result.get("errors"):
        reasons.append("opencode_reported_error")
    return {
        "status": "PASS" if not reasons else "FAIL",
        "reasons": reasons,
        "task_oracle_outcome": result.get("outcome"),
    }


def _pilot_active_assessment(result: dict[str, Any]) -> dict[str, Any]:
    assessment = _activation_assessment(result)
    evidence = result.get("selected_evidence_ids") or []
    if any(str(item).startswith("repo_path:") for item in evidence):
        assessment["reasons"] = [
            reason
            for reason in assessment["reasons"]
            if reason != "canonical_evidence_not_observed"
        ]
        assessment["status"] = "PASS" if not assessment["reasons"] else "FAIL"
    required = set(_load(B0A_ACTIVATION_PLAN)["pilot"]["tasks"][result["task_id"]])
    if not required <= set(result.get("pi_tools", ())):
        reasons = [*assessment["reasons"], "task_required_pi_tools_not_observed"]
        return {**assessment, "status": "FAIL", "reasons": reasons}
    return assessment


def _pilot_off_assessment(result: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    tools = set(result.get("pi_tools", ()))
    if tools != {"pi_status"}:
        reasons.append("off_control_tool_use_invalid")
    if result.get("observed_pi_readiness") != "disabled":
        reasons.append("off_control_not_disabled")
    modes = result.get("observed_capability_modes") or {}
    if any(modes.get(capability) != "off" for capability in CONFIGURABLE_CAPABILITIES):
        reasons.append("off_capability_mode_not_observed")
    if result.get("twin_revision_ids"):
        reasons.append("off_control_created_twin_revision")
    if result.get("process_exit") != 0 or result.get("errors"):
        reasons.append("off_control_process_failed")
    return {"status": "PASS" if not reasons else "FAIL", "reasons": reasons}


def _activation_gate(results: list[dict[str, Any]]) -> dict[str, Any]:
    activation_plan = _load(B0A_ACTIVATION_PLAN)
    expected_models = set(activation_plan["models"])
    observed_models = {item["model_tier"] for item in results}
    missing_models = sorted(expected_models - observed_models)
    unexpected_models = sorted(observed_models - expected_models)
    duplicate_models = sorted(
        model
        for model, count in Counter(item["model_tier"] for item in results).items()
        if count != 1
    )
    assessment_mismatches = sorted(
        item["model_tier"]
        for item in results
        if item.get("pi_activation") != _activation_assessment(item)
    )
    failed_models = sorted(
        item["model_tier"]
        for item in results
        if _activation_assessment(item).get("status") != "PASS"
    )
    route_gaps = [
        {
            "capabilities": route["capabilities"],
            "status": route["status"],
        }
        for route in activation_plan["capability_routes"]
        if route["status"] != "REACHABLE"
    ]
    if (
        missing_models
        or unexpected_models
        or duplicate_models
        or assessment_mismatches
        or failed_models
    ):
        status = "FAIL"
    else:
        status = "PASS"
    return {
        "status": status,
        "activation_plan_seal": activation_plan["seal"]["canonical_payload"],
        "expected_models": sorted(expected_models),
        "observed_models": sorted(observed_models),
        "missing_models": missing_models,
        "unexpected_models": unexpected_models,
        "duplicate_models": duplicate_models,
        "assessment_mismatches": assessment_mismatches,
        "failed_models": failed_models,
        "capability_route_gaps": route_gaps,
        "pilot_permitted": status == "PASS",
        "comprehensive_evaluation_permitted": status == "PASS" and not route_gaps,
    }


def _pilot_gate(results: list[dict[str, Any]]) -> dict[str, Any]:
    contract = _load(B0A_ACTIVATION_PLAN)["pilot"]
    expected = {
        f"b0a-pilot--{arm}--{contract['model']}--{task_id}--r{repetition}"
        for arm in contract["arms"]
        for task_id in contract["tasks"]
        for repetition in range(1, int(contract["repetitions"]) + 1)
    }
    initial_expected = {
        f"b0a-pilot--{arm}--{contract['model']}--{task_id}--r{repetition}"
        for arm in contract["arms"]
        for task_id in contract["tasks"]
        for repetition in range(1, int(contract["initial_tranche_repetitions"]) + 1)
    }
    by_id = {item["cell_id"]: item for item in results}
    observed = set(by_id)
    if observed == expected:
        stage = "confirmation_complete"
        stage_expected = expected
    elif observed == initial_expected:
        stage = "initial_complete"
        stage_expected = initial_expected
    elif observed < initial_expected:
        stage = "collecting_initial"
        stage_expected = initial_expected
    else:
        stage = "collecting_confirmation"
        stage_expected = expected
    missing = sorted(stage_expected - observed)
    unexpected = sorted(set(by_id) - expected)
    active = [item for item in results if item["arm"] == "active"]
    off = [item for item in results if item["arm"] == "off"]
    native = [item for item in results if item["arm"] == "native"]
    active_observation_failures = sorted(
        item["cell_id"]
        for item in active
        if item.get("pi_effect_observation") != _pilot_active_assessment(item)
        or _pilot_active_assessment(item)["status"] != "PASS"
    )
    off_observation_failures = sorted(
        item["cell_id"]
        for item in off
        if item.get("pi_off_observation") != _pilot_off_assessment(item)
        or _pilot_off_assessment(item)["status"] != "PASS"
    )
    provider_or_timeout = sorted(
        item["cell_id"] for item in results if item.get("outcome") in {"UNAVAILABLE", "TIMEOUT"}
    )
    passes = {
        arm: sum(item.get("outcome") == "PASS" for item in results if item["arm"] == arm)
        for arm in contract["arms"]
    }
    control_pass = max(passes.get("native", 0), passes.get("off", 0))
    pass_delta = passes.get("active", 0) - control_pass
    medians = {
        "native": median([item["wall_ms"] for item in native]) if native else None,
        "off": median([item["wall_ms"] for item in off]) if off else None,
        "active": median([item["wall_ms"] for item in active]) if active else None,
    }
    control_medians = [value for value in (medians["native"], medians["off"]) if value is not None]
    slower_control = max(control_medians) if control_medians else None
    wall_ratio = (
        medians["active"] / slower_control
        if medians["active"] is not None and slower_control
        else None
    )
    effect = contract["effect_gate"]
    reasons: list[str] = []
    if missing or unexpected:
        reasons.append("pilot_cells_incomplete")
    if active_observation_failures:
        reasons.append("active_pi_not_observed")
    if off_observation_failures:
        reasons.append("off_inertness_not_observed")
    if provider_or_timeout:
        reasons.append("provider_error_or_timeout")
    if pass_delta < int(effect["minimum_active_pass_delta_over_best_control"]):
        reasons.append("no_objective_pass_effect")
    if wall_ratio is None or wall_ratio > float(
        effect["maximum_active_median_wall_ratio_over_slower_control"]
    ):
        reasons.append("active_wall_time_abnormal")
    if stage in {"collecting_initial", "collecting_confirmation"}:
        decision = "COLLECT_MORE_CELLS"
    elif reasons:
        decision = effect["no_effect_action"]
    elif stage == "initial_complete":
        decision = effect["initial_pass_action"]
    else:
        decision = effect["pass_action"]
    return {
        "decision": decision,
        "stage": stage,
        "activation_plan_seal": _load(B0A_ACTIVATION_PLAN)["seal"]["canonical_payload"],
        "stage_expected_cells": len(stage_expected),
        "full_expected_cells": len(expected),
        "observed_cells": len(expected & set(by_id)),
        "missing_cells": missing,
        "unexpected_cells": unexpected,
        "passes": passes,
        "active_pass_delta_over_best_control": pass_delta,
        "median_wall_ms": medians,
        "active_median_wall_ratio_over_slower_control": wall_ratio,
        "active_observation_failures": active_observation_failures,
        "off_observation_failures": off_observation_failures,
        "provider_or_timeout_cells": provider_or_timeout,
        "reasons": reasons,
        "comprehensive_evaluation_permitted": decision == effect["pass_action"],
    }


def _metric_projection() -> dict[str, Any]:
    contract = _load(METRICS)
    return {
        group: {key: {"status": "NOT_TESTED", "value": None} for key in contract[group]}
        for group in (
            "correctness",
            "efficiency",
            "portfolio",
            "nondeterminism",
            "performance_obligations",
            "certificate",
        )
    }


def run(
    scope: str,
    output: Path,
    max_cells: int | None,
    selected_arms: set[str] | None,
    selected_models: set[str] | None,
    selected_tasks: set[str] | None,
    resume: bool,
    raw_root_override: Path | None,
    activation_report: Path | None,
    pilot_report: Path | None,
    availability_proof_paths: list[Path],
) -> None:
    activation_evidence: dict[str, Any] | None = None
    pilot_evidence: dict[str, Any] | None = None
    if scope == "b0a-pilot":
        activation_evidence = _require_activation_report(
            activation_report, require_comprehensive=False
        )
    if scope in {"b0a-baseline", "b0a-screening"}:
        activation_evidence = _require_activation_report(
            activation_report, require_comprehensive=True
        )
        pilot_evidence = _require_pilot_report(pilot_report)
    if scope.startswith("b0a-"):
        _require_clean_worktree()
    schedule = plan(
        scope,
        selected_arms=selected_arms,
        selected_models=selected_models,
        selected_tasks=selected_tasks,
    )
    suite = _load(TASK_SUITE)
    tasks = {item["id"]: item for item in suite["tasks"]}
    cells = schedule["cells"][:max_cells] if max_cells is not None else schedule["cells"]
    raw_root = (
        raw_root_override.resolve()
        if raw_root_override is not None
        else ROOT / _load(MATRIX)["execution"]["raw_root"] / scope
    )
    raw_root.mkdir(parents=True, exist_ok=True)
    trace_log = EvaluationTraceLog(raw_root / "traces.jsonl")
    if not resume and (output.exists() or trace_log.path.exists()):
        raise EvaluationError(
            "evaluation output/raw trace already exists; use a fresh path or --resume"
        )
    if resume and output.is_file():
        previous = _load(output)
        _validate_resume(
            previous,
            scope,
            schedule,
            activation_evidence,
            pilot_evidence,
            trace_log.path,
        )
    elif resume and trace_log.path.exists():
        raise EvaluationError("resume trace exists without its atomic report checkpoint")
    trace_log.replay()
    results: list[dict[str, Any]] = []
    provider_attempts: list[dict[str, Any]] = []
    provider_queue: dict[str, dict[str, Any]] = {}
    migration_provenance: dict[str, Any] | None = None
    if resume and output.is_file():
        results = list(previous.get("results", []))
        provider_attempts = list(previous.get("provider_attempts", []))
        provider_queue = dict(previous.get("provider_queue", {}))
        if previous.get("result_origin") == "migrated_checkpoint":
            migration_provenance = {
                key: previous[key]
                for key in (
                    "result_origin",
                    "original_runner_revision",
                    "validated_by_runner_revision",
                    "compatibility_manifest",
                    "compatibility_audit",
                    "compatibility_audit_seal",
                    "compatibility_proof",
                    "compatibility_proof_seal",
                    "latency_status",
                    "latency_merge_permitted",
                    "migration_summary",
                )
            }
    current_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    for provider_tier in _available_provider_tiers(availability_proof_paths, current_revision):
        provider_queue[provider_tier] = {"status": "AVAILABLE"}
    completed = {item["cell_id"] for item in results}
    for cell in cells:
        if cell["cell_id"] in completed:
            continue
        if provider_queue.get(cell["model_tier"], {}).get("status") == ("PAUSED_PROVIDER_GAP"):
            continue
        result = _execute(cell, tasks[cell["task_id"]], raw_root)
        if result.get("provider_failure"):
            provider_attempts.append(result)
            provider_queue[cell["model_tier"]] = {
                "status": "PAUSED_PROVIDER_GAP",
                "failure": result["provider_failure"],
                "trigger_cell": cell["cell_id"],
            }
        else:
            _append_trace(trace_log, result, tasks[cell["task_id"]])
            results.append(result)
        _write_report(
            output,
            _report(
                scope,
                schedule,
                results,
                trace_log.path,
                activation_evidence,
                pilot_evidence,
                provider_queue,
                provider_attempts,
                migration_provenance,
            ),
        )
    report = _report(
        scope,
        schedule,
        results,
        trace_log.path,
        activation_evidence,
        pilot_evidence,
        provider_queue,
        provider_attempts,
        migration_provenance,
    )
    _write_report(output, report)
    if scope == "b0a-activation" and report["activation_gate"]["status"] != "PASS":
        raise EvaluationError(
            f"B0a PI activation gate did not pass: {report['activation_gate']['status']}"
        )
    if scope == "b0a-pilot":
        decision = report["pilot_gate"]["decision"]
        initial_cells = (
            len(_load(B0A_ACTIVATION_PLAN)["pilot"]["arms"])
            * len(_load(B0A_ACTIVATION_PLAN)["pilot"]["tasks"])
            * int(_load(B0A_ACTIVATION_PLAN)["pilot"]["initial_tranche_repetitions"])
        )
        if decision == "CONTINUE_TO_CONFIRMATION" and max_cells == initial_cells:
            return
        if decision != "PROCEED_TO_COMPREHENSIVE":
            raise EvaluationError(
                f"B0a PI effect pilot requires repair: {report['pilot_gate']['reasons']}"
            )


def run_bridge(
    bridge_plan_path: Path,
    output: Path,
    raw_root: Path,
    selected_models: set[str] | None,
    resume: bool,
    availability_proof_paths: list[Path],
) -> None:
    _require_clean_worktree()
    bridge_plan = _load(bridge_plan_path.resolve())
    verify_seal(bridge_plan, "bridge plan")
    current_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    if bridge_plan.get("bridge_runner_revision") != current_revision:
        raise EvaluationError("bridge plan was not generated at the current exact head")
    raw_root = raw_root.resolve()
    raw_root.mkdir(parents=True, exist_ok=True)
    trace_log = EvaluationTraceLog(raw_root / "traces.jsonl")
    results: list[dict[str, Any]] = []
    provider_attempts: list[dict[str, Any]] = []
    provider_queue: dict[str, dict[str, Any]] = {}
    if output.exists():
        if not resume:
            raise EvaluationError("bridge output exists; use a fresh path or --resume")
        previous = _load(output)
        verify_seal(previous, "bridge run")
        if previous.get("bridge_plan_seal") != bridge_plan["seal"]["canonical_payload"]:
            raise EvaluationError("bridge resume plan seal mismatch")
        if previous.get("source_revision") != current_revision:
            raise EvaluationError("bridge resume source revision mismatch")
        if previous.get("trace_log") != str(trace_log.path):
            raise EvaluationError("bridge resume trace log mismatch")
        results = list(previous.get("results", []))
        provider_attempts = list(previous.get("provider_attempts", []))
        provider_queue = dict(previous.get("provider_queue", {}))
    elif resume and trace_log.path.exists():
        raise EvaluationError("bridge trace exists without its atomic report checkpoint")
    elif trace_log.path.exists():
        raise EvaluationError("bridge trace already exists; use a fresh raw root")
    trace_log.replay()
    for provider_tier in _available_provider_tiers(availability_proof_paths, current_revision):
        provider_queue[provider_tier] = {
            "status": "AVAILABLE",
            "availability_proof": str(
                next(
                    path.resolve()
                    for path in availability_proof_paths
                    if _load(path.resolve()).get("model_tier") == provider_tier
                )
            ),
        }
    baseline_cells = {item["cell_id"]: item for item in plan("b0a-baseline")["cells"]}
    planned_ids = [item["cell_id"] for item in bridge_plan["cells"]]
    completed = {item["cell_id"] for item in results}
    tasks = {item["id"]: item for item in _load(TASK_SUITE)["tasks"]}
    for cell_id in planned_ids:
        cell = baseline_cells.get(cell_id)
        if cell is None:
            raise EvaluationError(f"bridge cell is absent from current baseline: {cell_id}")
        if selected_models and cell["model_tier"] not in selected_models:
            continue
        if provider_queue.get(cell["model_tier"], {}).get("status") == ("PAUSED_PROVIDER_GAP"):
            continue
        if cell_id in completed:
            continue
        result = _execute(cell, tasks[cell["task_id"]], raw_root)
        if result.get("provider_failure"):
            provider_attempts.append(result)
            provider_queue[cell["model_tier"]] = {
                "status": "PAUSED_PROVIDER_GAP",
                "failure": result["provider_failure"],
                "trigger_cell": cell_id,
            }
        else:
            _append_trace(trace_log, result, tasks[cell["task_id"]])
            results.append(result)
        body = {
            "schema": 1,
            "classification": "EVALUATION_CHECKPOINT_BRIDGE_RUN",
            "source_revision": current_revision,
            "bridge_plan": str(bridge_plan_path.resolve()),
            "bridge_plan_seal": bridge_plan["seal"]["canonical_payload"],
            "trace_log": str(trace_log.path),
            "executed_cells": len(results),
            "pending_cells": sorted(set(planned_ids) - {item["cell_id"] for item in results}),
            "provider_queue": provider_queue,
            "provider_attempts": provider_attempts,
            "results": results,
        }
        _write_report(
            output,
            {**body, "seal": {"algorithm": "sha256", "canonical_payload": digest(body)}},
        )
    if not output.exists():
        body = {
            "schema": 1,
            "classification": "EVALUATION_CHECKPOINT_BRIDGE_RUN",
            "source_revision": current_revision,
            "bridge_plan": str(bridge_plan_path.resolve()),
            "bridge_plan_seal": bridge_plan["seal"]["canonical_payload"],
            "trace_log": str(trace_log.path),
            "executed_cells": 0,
            "pending_cells": planned_ids,
            "provider_queue": provider_queue,
            "provider_attempts": provider_attempts,
            "results": [],
        }
        _write_report(
            output,
            {**body, "seal": {"algorithm": "sha256", "canonical_payload": digest(body)}},
        )


def _available_provider_tiers(paths: list[Path], current_revision: str) -> set[str]:
    available: set[str] = set()
    for path in paths:
        proof = _load(path.resolve())
        verify_seal(proof, "provider availability proof")
        if proof.get("classification") != "EVALUATION_PROVIDER_AVAILABILITY_PROBE":
            raise EvaluationError("availability proof has the wrong classification")
        if proof.get("source_revision") != current_revision:
            raise EvaluationError("availability proof was not produced at the current exact head")
        if proof.get("status") != "AVAILABLE":
            raise EvaluationError("availability proof did not establish provider recovery")
        available.add(str(proof["model_tier"]))
    return available


def probe_provider(model_tier: str, output: Path) -> None:
    """Run a small provider-only request that is never included in quality results."""
    _require_clean_worktree()
    current_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    with tempfile.TemporaryDirectory(prefix="eca-provider-probe-") as temporary:
        workspace = Path(temporary)
        env, model_id = _environment("native", model_tier, workspace)
        command = [
            _load(MATRIX)["execution"]["opencode_executable"],
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
            "--pure",
            "Reply with exactly AVAILABLE.",
        ]
        started = time.monotonic()
        stdout, stderr, process_exit, timed_out, provider_failure = _run_opencode(
            command, cwd=ROOT, env=env, timeout=60
        )
    status = (
        "AVAILABLE"
        if process_exit == 0 and not timed_out and provider_failure is None
        else "UNAVAILABLE"
    )
    body = {
        "schema": 1,
        "classification": "EVALUATION_PROVIDER_AVAILABILITY_PROBE",
        "source_revision": current_revision,
        "model_tier": model_tier,
        "model_id": model_id,
        "status": status,
        "provider_failure": provider_failure,
        "process_exit": process_exit,
        "timed_out": timed_out,
        "wall_ms": round((time.monotonic() - started) * 1000),
        "probe_only_not_quality_result": True,
        "response_observed": bool(stdout.strip()),
        "error_observed": bool(stderr.strip()),
    }
    _write_report(
        output,
        {**body, "seal": {"algorithm": "sha256", "canonical_payload": digest(body)}},
    )


def _validate_resume(
    previous: dict[str, Any],
    scope: str,
    schedule: dict[str, Any],
    activation_evidence: dict[str, Any] | None,
    pilot_evidence: dict[str, Any] | None,
    trace_path: Path,
) -> None:
    current_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    if previous.get("source_revision") != current_revision:
        raise EvaluationError("resume report was produced at a different source revision")
    expected_schedule = {key: value for key, value in schedule.items() if key != "cells"}
    if previous.get("schedule") != expected_schedule:
        raise EvaluationError("resume report schedule does not match the current sealed schedule")
    migrated_unbound = previous.get("result_origin") == "migrated_checkpoint"
    if migrated_unbound:
        verify_seal(previous, "migrated checkpoint")
    if not migrated_unbound and previous.get("activation_evidence") != activation_evidence:
        raise EvaluationError("resume report activation evidence does not match")
    if not migrated_unbound and previous.get("pilot_evidence") != pilot_evidence:
        raise EvaluationError("resume report pilot evidence does not match")
    if previous.get("trace_log") != str(trace_path):
        raise EvaluationError("resume report points at a different trace log")
    results = list(previous.get("results", ()))
    if results and not trace_path.is_file():
        raise EvaluationError("resume report has result cells but its trace log is missing")
    result_ids = [item.get("cell_id") for item in results]
    if len(result_ids) != len(set(result_ids)):
        raise EvaluationError("resume report contains duplicate cells")
    expected_ids = {item["cell_id"] for item in schedule["cells"]}
    if not set(result_ids) <= expected_ids:
        raise EvaluationError("resume report contains cells outside the current schedule")


def _require_clean_worktree() -> None:
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        text=True,
    ).strip()
    if dirty:
        raise EvaluationError("B0a evaluation requires a clean tracked worktree at an exact head")


def _require_activation_report(path: Path | None, *, require_comprehensive: bool) -> dict[str, Any]:
    if path is None:
        raise EvaluationError("--activation-report is required for comprehensive B0a execution")
    report = _load(path.resolve())
    gate = report.get("activation_gate")
    if report.get("schedule", {}).get("scope") != "b0a-activation":
        raise EvaluationError("B0a PI activation report has the wrong scope")
    recomputed = _activation_gate(list(report.get("results", ())))
    if gate != recomputed:
        raise EvaluationError("B0a PI activation report does not match its result cells")
    if (
        not isinstance(gate, dict)
        or gate.get("status") != "PASS"
        or gate.get("pilot_permitted") is not True
    ):
        raise EvaluationError("B0a PI activation report is absent or did not pass")
    if require_comprehensive and gate.get("comprehensive_evaluation_permitted") is not True:
        raise EvaluationError("B0a PI activation report has unresolved capability route gaps")
    current_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    if report.get("source_revision") != current_revision:
        raise EvaluationError("B0a PI activation report was not produced at the current exact head")
    expected_seal = _load(B0A_ACTIVATION_PLAN)["seal"]["canonical_payload"]
    if gate.get("activation_plan_seal") != expected_seal:
        raise EvaluationError("B0a PI activation report uses a stale activation contract")
    if set(gate.get("observed_models", ())) != set(B0A_ACTIVATION_MODELS):
        raise EvaluationError("B0a PI activation report is missing a permitted model route")
    return {
        "path": str(path.resolve()),
        "activation_plan_seal": expected_seal,
        "source_revision": current_revision,
        "status": "PASS",
    }


def _require_pilot_report(path: Path | None) -> dict[str, Any]:
    if path is None:
        raise EvaluationError("--pilot-report is required for comprehensive B0a execution")
    report = _load(path.resolve())
    if report.get("schedule", {}).get("scope") != "b0a-pilot":
        raise EvaluationError("B0a PI pilot report has the wrong scope")
    gate = report.get("pilot_gate")
    recomputed = _pilot_gate(list(report.get("results", ())))
    if gate != recomputed:
        raise EvaluationError("B0a PI pilot report does not match its result cells")
    if (
        not isinstance(gate, dict)
        or gate.get("decision") != "PROCEED_TO_COMPREHENSIVE"
        or gate.get("comprehensive_evaluation_permitted") is not True
    ):
        raise EvaluationError("B0a PI pilot requires repair and retest")
    current_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    if report.get("source_revision") != current_revision:
        raise EvaluationError("B0a PI pilot report was not produced at the current exact head")
    expected_seal = _load(B0A_ACTIVATION_PLAN)["seal"]["canonical_payload"]
    if gate.get("activation_plan_seal") != expected_seal:
        raise EvaluationError("B0a PI pilot report uses a stale effect contract")
    return {
        "path": str(path.resolve()),
        "activation_plan_seal": expected_seal,
        "source_revision": current_revision,
        "decision": gate["decision"],
    }


def _report(
    scope: str,
    schedule: dict[str, Any],
    results: list[dict[str, Any]],
    trace_path: Path,
    activation_evidence: dict[str, Any] | None = None,
    pilot_evidence: dict[str, Any] | None = None,
    provider_queue: dict[str, dict[str, Any]] | None = None,
    provider_attempts: list[dict[str, Any]] | None = None,
    migration_provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report = {
        "schema": 1,
        "run_id": f"unified-v1-{scope}",
        "classification": (
            "E4_RUNNER_PROOF"
            if scope == "smoke"
            else "B0A_PI_ACTIVATION_RESULT"
            if scope == "b0a-activation"
            else "B0A_PI_EFFECT_PILOT_RESULT"
            if scope == "b0a-pilot"
            else "B0A_EVALUATION_RESULT"
            if scope.startswith("b0a-")
            else "EVALUATION_RESULT"
        ),
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "schedule": {key: value for key, value in schedule.items() if key != "cells"},
        "inputs": _load(MATRIX)["inputs"],
        "trace_log": str(trace_path),
        "executed_cells": len(results),
        "outcomes": dict(Counter(item["outcome"] for item in results)),
        "integrated_metrics": _metric_projection(),
        "results": results,
    }
    if provider_queue:
        report["provider_queue"] = provider_queue
    if provider_attempts:
        report["provider_attempts"] = provider_attempts
    if migration_provenance:
        report.update(migration_provenance)
    report["failure_attribution"] = dict(
        Counter(
            item.get("outcome_attribution", {}).get("classification", "NOT_CLASSIFIED")
            for item in results
        )
    )
    timing_keys = (
        "cold_twin_build_ms",
        "snapshot_load_ms",
        "adjacency_index_build_ms",
        "query_execution_ms",
        "json_serialization_ms",
        "model_reasoning_after_tool_ms",
    )
    report["pi_timing_median_ms_by_arm"] = {
        arm: {
            key: median(
                [
                    float(item.get("pi_timing_ms", {}).get(key, 0.0))
                    for item in results
                    if item["arm"] == arm
                ]
            )
            for key in timing_keys
        }
        for arm in sorted({item["arm"] for item in results})
        if any(item["arm"] == arm for item in results)
    }
    if scope == "b0a-activation":
        report["activation_gate"] = _activation_gate(results)
    elif scope == "b0a-pilot":
        report["pilot_gate"] = _pilot_gate(results)
    if activation_evidence is not None:
        report["activation_evidence"] = activation_evidence
    if pilot_evidence is not None:
        report["pilot_evidence"] = pilot_evidence
    if migration_provenance:
        report["seal"] = {"algorithm": "sha256", "canonical_payload": digest(report)}
    return report


def _append_trace(
    trace_log: EvaluationTraceLog, result: dict[str, Any], task: dict[str, Any]
) -> None:
    matrix = _load(MATRIX)
    suite = _load(TASK_SUITE)
    repository = next(
        item for item in suite["repositories"] if item["id"] == result["repository_id"]
    )
    planned_modes, planned_depths = _trace_capabilities(result["arm"])
    observed_modes = result.get("observed_capability_modes") or {}
    observed_depths = result.get("observed_capability_depths") or {}
    capability_state_source = "observed_pi_status" if observed_modes else "planned_matrix"
    capability_modes = observed_modes or planned_modes
    capability_depths = observed_depths or planned_depths
    trace_id = (
        "trace-"
        + hashlib.sha256(
            f"{matrix['seal']['canonical_payload']}:{result['cell_id']}".encode()
        ).hexdigest()[:24]
    )
    input_seals = {
        "layer_a": matrix["inputs"]["layer_a_seal"],
        "layer_b": matrix["inputs"]["layer_b_seal"],
        "matrix": matrix["seal"]["canonical_payload"],
    }
    segmented = result.get("pi_timing_ms") or {}
    trace_log.append(
        EvaluationTrace(
            trace_id=trace_id,
            plan_id=matrix["matrix_id"],
            cell_id=result["cell_id"],
            task_id=result["task_id"],
            task_class=result["task_class"],
            oracle_id=f"e3-oracle:{result['task_id']}",
            input_seals=input_seals,
            capability_state_source=capability_state_source,
            capability_modes=capability_modes,
            capability_depths=capability_depths,
            used_features={
                f"capability:{capability}": "observed_tool_output"
                for capability in result.get("pi_capabilities_used", ())
            },
            selected_evidence_ids=tuple(result.get("selected_evidence_ids", ())),
            source_revision_id=repository["revision"],
            twin_revision_id=next(iter(result.get("twin_revision_ids", ())), None),
            model_tier=result["model_tier"],
            model_id=result.get("model_id"),
            verification_outcome=result["outcome"],
            fallback="model_unavailable" if result["outcome"] == "UNAVAILABLE" else None,
            timings_ms={
                "agent_wall": result.get("wall_ms"),
                "pi_analysis": result.get("pi_analysis_ms"),
                "cold_twin_build": segmented.get("cold_twin_build_ms"),
                "snapshot_load": segmented.get("snapshot_load_ms"),
                "adjacency_index_build": segmented.get("adjacency_index_build_ms"),
                "query_execution": segmented.get("query_execution_ms"),
                "json_serialization": segmented.get("json_serialization_ms"),
                "model_reasoning_after_tool": segmented.get("model_reasoning_after_tool_ms"),
            },
        )
    )
    result["trace_id"] = trace_id


def _write_report(output: Path, report: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)


def screening_table(report: dict[str, Any]) -> dict[str, Any]:
    schedule = plan("b0a-screening")
    comparison_cells = [
        item
        for item in schedule["cells"]
        if item["arm"] == "active" or item["arm"].startswith("ablation:")
    ]
    expected = {item["cell_id"] for item in comparison_cells}
    results = {item["cell_id"]: item for item in report.get("results", []) if "cell_id" in item}
    missing = sorted(expected - set(results))
    unexpected = sorted(set(results) - {item["cell_id"] for item in schedule["cells"]})
    plan_value = _load(B0A_PLAN)
    route_by_capability = {
        capability: route
        for route in _load(B0A_ACTIVATION_PLAN)["capability_routes"]
        if route.get("covered_tasks")
        for capability in route["capabilities"]
    }
    # The primary phrase is versioned for readers; derive the exact integer from the paired rate so
    # the machine decision cannot silently drift from 2/21.
    pair_count = len([item for item in comparison_cells if item["arm"] == "active"])
    threshold = round(
        float(plan_value["screening"]["effect_threshold"]["minimum_absolute_pass_rate_delta"])
        * pair_count
    )
    entries: list[dict[str, Any]] = []
    for capability in CONFIGURABLE_CAPABILITIES:
        ablation = f"ablation:{capability}"
        active_cells = [item for item in comparison_cells if item["arm"] == "active"]
        pairs = []
        for active in active_cells:
            ablated_id = active["cell_id"].replace("active--", f"{ablation}--", 1)
            if active["cell_id"] in results and ablated_id in results:
                pairs.append((results[active["cell_id"]], results[ablated_id]))
        unavailable = sum(
            active["outcome"] == "UNAVAILABLE" or ablated["outcome"] == "UNAVAILABLE"
            for active, ablated in pairs
        )
        active_pass = sum(active["outcome"] == "PASS" for active, _ in pairs)
        ablation_pass = sum(ablated["outcome"] == "PASS" for _, ablated in pairs)
        critical = any(
            active["outcome"] == "PASS"
            and ablated["outcome"] != "PASS"
            and active.get("task_class") in {"negative-control", "unsafe-or-insufficient-evidence"}
            for active, ablated in pairs
        )
        route = route_by_capability.get(capability)
        route_observation_failures: list[str] = []
        if route is not None:
            covered_tasks = set(route["covered_tasks"])
            tool = route["tool"]
            for active, ablated in pairs:
                if active["task_id"] not in covered_tasks:
                    continue
                if tool not in active.get("pi_tools", ()):
                    route_observation_failures.append(f"{active['cell_id']}:tool_not_observed")
                if capability not in active.get("pi_capabilities_used", ()):
                    route_observation_failures.append(
                        f"{active['cell_id']}:capability_not_observed"
                    )
                if tool not in ablated.get("pi_tools", ()):
                    route_observation_failures.append(f"{ablated['cell_id']}:tool_not_attempted")
        if missing or len(pairs) != pair_count:
            decision = "NOT_TESTED_INCOMPLETE"
        elif unavailable:
            decision = "NOT_TESTED_PROVIDER_GAP"
        elif route_observation_failures:
            decision = "NOT_TESTED_ROUTE_GAP"
        elif active_pass - ablation_pass >= threshold or critical:
            decision = "proceed_to_b0b"
        else:
            decision = "no_screened_effect"
        entries.append(
            {
                "capability": capability,
                "paired_cells": len(pairs),
                "active_pass": active_pass,
                "ablation_pass": ablation_pass,
                "pass_delta": active_pass - ablation_pass,
                "unavailable_pairs": unavailable,
                "critical_override": critical,
                "route_observation_failures": route_observation_failures,
                "decision": decision,
            }
        )
    return {
        "schema": 1,
        "classification": "B0A_SCREENING_TABLE" if not missing else "B0A_SCREENING_INCOMPLETE",
        "screening_plan_seal": plan_value["seal"]["canonical_payload"],
        "source_report_revision": report.get("source_revision"),
        "expected_comparison_cells": len(expected),
        "observed_comparison_cells": len(expected & set(results)),
        "missing_cells": missing,
        "unexpected_cells": unexpected,
        "effect_threshold_pass_delta": threshold,
        "adoption_decisions_forbidden": True,
        "capabilities": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    sub.add_parser("metrics")
    seal_parser = sub.add_parser("seal")
    seal_parser.add_argument("target", choices=["matrix", "labels", "activation", "compatibility"])
    plan_parser = sub.add_parser("plan")
    plan_parser.add_argument(
        "--scope",
        choices=[
            "smoke",
            "base",
            "screening",
            "full",
            "b0a-activation",
            "b0a-pilot",
            "b0a-baseline",
            "b0a-screening",
        ],
        default="full",
    )
    _selection_arguments(plan_parser)
    run_parser = sub.add_parser("run")
    run_parser.add_argument(
        "--scope",
        choices=[
            "smoke",
            "base",
            "screening",
            "full",
            "b0a-activation",
            "b0a-pilot",
            "b0a-baseline",
            "b0a-screening",
        ],
        required=True,
    )
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--max-cells", type=int)
    run_parser.add_argument("--resume", action="store_true")
    run_parser.add_argument("--raw-root", type=Path)
    run_parser.add_argument("--activation-report", type=Path)
    run_parser.add_argument("--pilot-report", type=Path)
    run_parser.add_argument("--availability-proof", type=Path, action="append")
    _selection_arguments(run_parser)
    screen_parser = sub.add_parser("screen")
    screen_parser.add_argument("--input", type=Path, required=True)
    screen_parser.add_argument("--output", type=Path, required=True)
    audit_parser = sub.add_parser("audit-checkpoint")
    audit_parser.add_argument("--source", type=Path, required=True)
    audit_parser.add_argument("--compatibility", type=Path, required=True)
    audit_parser.add_argument("--output", type=Path, required=True)
    bridge_plan_parser = sub.add_parser("bridge-plan")
    bridge_plan_parser.add_argument("--audit", type=Path, required=True)
    bridge_plan_parser.add_argument("--compatibility", type=Path, required=True)
    bridge_plan_parser.add_argument("--output", type=Path, required=True)
    bridge_run_parser = sub.add_parser("run-bridge")
    bridge_run_parser.add_argument("--bridge-plan", type=Path, required=True)
    bridge_run_parser.add_argument("--output", type=Path, required=True)
    bridge_run_parser.add_argument("--raw-root", type=Path, required=True)
    bridge_run_parser.add_argument("--model-tier", action="append")
    bridge_run_parser.add_argument("--resume", action="store_true")
    bridge_run_parser.add_argument("--availability-proof", type=Path, action="append")
    bridge_proof_parser = sub.add_parser("prove-bridge")
    bridge_proof_parser.add_argument("--bridge-plan", type=Path, required=True)
    bridge_proof_parser.add_argument("--bridge-run", type=Path, required=True)
    bridge_proof_parser.add_argument("--source", type=Path, required=True)
    bridge_proof_parser.add_argument("--output", type=Path, required=True)
    probe_parser = sub.add_parser("probe-provider")
    probe_parser.add_argument("--model-tier", required=True)
    probe_parser.add_argument("--output", type=Path, required=True)
    migrate_parser = sub.add_parser("migrate-checkpoint")
    migrate_parser.add_argument("--source", type=Path, required=True)
    migrate_parser.add_argument("--audit", type=Path, required=True)
    migrate_parser.add_argument("--bridge", type=Path, required=True)
    migrate_parser.add_argument("--output", type=Path, required=True)
    migrate_parser.add_argument("--raw-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "validate":
            validate()
        elif args.command == "metrics":
            validate()
            print(json.dumps(_metric_projection(), ensure_ascii=False, indent=2))
        elif args.command == "seal":
            target = {
                "matrix": MATRIX,
                "labels": LABELS,
                "activation": B0A_ACTIVATION_PLAN,
                "compatibility": B0A_CHECKPOINT_COMPATIBILITY,
            }[args.target]
            seal(target)
        elif args.command == "plan":
            print(
                json.dumps(
                    plan(
                        args.scope,
                        selected_arms=_selected(args.arm),
                        selected_models=_selected(args.model_tier),
                        selected_tasks=_selected(args.task),
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        elif args.command == "run":
            if args.max_cells is not None and args.max_cells < 1:
                raise EvaluationError("--max-cells must be positive")
            run(
                args.scope,
                args.output,
                args.max_cells,
                _selected(args.arm),
                _selected(args.model_tier),
                _selected(args.task),
                args.resume,
                args.raw_root,
                args.activation_report,
                args.pilot_report,
                args.availability_proof or [],
            )
        elif args.command == "screen":
            _write_report(args.output, screening_table(_load(args.input)))
        elif args.command == "audit-checkpoint":
            _require_clean_worktree()
            source_report = _load(args.source)
            source_scope = source_report.get("schedule", {}).get("scope")
            if not isinstance(source_scope, str):
                raise EvaluationError("source checkpoint has no schedule scope")
            _write_report(
                args.output,
                audit_checkpoint(
                    ROOT,
                    args.source.resolve(),
                    args.compatibility.resolve(),
                    plan(source_scope)["cells"],
                ),
            )
        elif args.command == "bridge-plan":
            _require_clean_worktree()
            _write_report(
                args.output,
                create_bridge_plan(ROOT, args.audit.resolve(), args.compatibility.resolve()),
            )
        elif args.command == "run-bridge":
            run_bridge(
                args.bridge_plan,
                args.output,
                args.raw_root,
                _selected(args.model_tier),
                args.resume,
                args.availability_proof or [],
            )
        elif args.command == "prove-bridge":
            _require_clean_worktree()
            _write_report(
                args.output,
                prove_bridge(
                    args.bridge_plan.resolve(),
                    args.bridge_run.resolve(),
                    args.source.resolve(),
                ),
            )
        elif args.command == "probe-provider":
            probe_provider(args.model_tier, args.output)
        else:
            _require_clean_worktree()
            _write_report(
                args.output,
                migrate_checkpoint(
                    ROOT,
                    args.source.resolve(),
                    args.audit.resolve(),
                    args.bridge.resolve(),
                    args.raw_root.resolve() / "traces.jsonl",
                ),
            )
    except (
        CompatibilityError,
        EvaluationError,
        KeyError,
        TypeError,
        ValueError,
        subprocess.TimeoutExpired,
    ) as error:
        print(f"unified evaluation error: {error}", file=sys.stderr)
        return 1
    if args.command not in {"plan", "metrics", "screen"}:
        print(f"unified evaluation {args.command}: PASS")
    return 0


def _selection_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--arm", action="append", default=[])
    parser.add_argument("--model-tier", action="append", default=[])
    parser.add_argument("--task", action="append", default=[])


def _selected(values: list[str]) -> set[str] | None:
    return set(values) if values else None


if __name__ == "__main__":
    raise SystemExit(main())
