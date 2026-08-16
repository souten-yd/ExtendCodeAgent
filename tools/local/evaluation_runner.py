#!/usr/bin/env python3
"""Validate, schedule, and execute the unified versioned evaluation matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from extendcodeagent.evaluation import EvaluationTrace, EvaluationTraceLog

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "docs/evaluation/evaluation-matrix-v1.json"
TASK_SUITE = ROOT / "docs/evaluation/task-suite-v1.json"
LABELS = ROOT / "docs/evaluation/labels-v1/graph-quality-labels.json"
METRICS = ROOT / "docs/evaluation/pi-verification-integrated-metrics-v1.json"
CORPUS = ROOT / "docs/evaluation/test-portfolio-corpus-v1.json"
E3_HARNESS = ROOT / "tools/local/e3_task_suite.py"
PYTHON = ROOT / ".venv/bin/python"
PLUGIN = ROOT / "adapters/opencode/dist/src/plugin.js"
MCP = ROOT / "adapters/opencode/dist/src/mcp.js"
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
LOCAL_SOURCES = {
    "extendcodeagent": ROOT,
    "controldeck": Path("/home/souten/ControlDeck"),
    "kasanecore": Path("/home/souten/KasaneCore"),
}


class EvaluationError(RuntimeError):
    """A deterministic matrix or execution failure."""


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


def _arms(matrix: dict[str, Any], scope: str) -> list[str]:
    base = [item["id"] for item in matrix["base_arms"]]
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
    if scope == "smoke":
        tasks = [tasks[0]]
    elif scope == "screening":
        wanted = set(matrix["screening"]["tuning_task_subset"])
        tasks = [item for item in tasks if item["id"] in wanted]
    arms = _arms(matrix, scope)
    if selected_arms is not None:
        unknown = selected_arms - set(arms)
        if unknown:
            raise EvaluationError(f"unknown arms for {scope}: {sorted(unknown)}")
        arms = [item for item in arms if item in selected_arms]
    models = matrix["model_tiers"]
    if scope in {"smoke", "screening"}:
        models = (
            [item for item in models if item["id"] == "host-default"]
            if scope == "smoke"
            else [item for item in models if item["id"] in {"local-low", "local-practical"}]
        )
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
                for repetition in range(1, int(model["minimum_repetitions"]) + 1):
                    cells.append(
                        {
                            "cell_id": f"{arm}--{model['id']}--{task['id']}--r{repetition}",
                            "arm": arm,
                            "model_tier": model["id"],
                            "model_id": model.get("model_id"),
                            "model_status": model["status"],
                            "repository_id": task["repository_id"],
                            "task_id": task["id"],
                            "task_class": task["task_class"],
                            "split": task["split"],
                            "repetition": repetition,
                        }
                    )
    return {
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
    depth = modifier if modifier in {"D0", "D1", "D2", "D3", "D4"} else "D2"
    depths = {capability: depth for capability, value in modes.items() if value != "off"}
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
                "models": {model_id: {"name": "Qwen3.6 27B on port 8090"}},
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
        project_config = workspace.parent / f"{workspace.name}-eca-config.json"
        project_config.write_text(
            json.dumps({"project_intelligence": pi}, separators=(",", ":")), encoding="utf-8"
        )
        config["mcp"] = {
            "extendcodeagent": {
                "type": "local",
                "command": ["node", str(MCP)],
                "enabled": True,
                "environment": {
                    "PYTHONPATH": str(ROOT / "src"),
                    "EXTENDCODEAGENT_ROOT": str(workspace),
                    "EXTENDCODEAGENT_PYTHON": str(PYTHON),
                    "EXTENDCODEAGENT_MODE": mode,
                    "EXTENDCODEAGENT_PROJECT_CONFIG": str(project_config),
                },
            }
        }
    env = {
        **os.environ,
        "OPENCODE_CONFIG_CONTENT": json.dumps(config, separators=(",", ":")),
        "PYTHONPATH": str(ROOT / "src"),
        "EXTENDCODEAGENT_PYTHON": str(PYTHON),
        "EXTENDCODEAGENT_MODE": mode,
    }
    return env, model_id


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
    }
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        result["events"] += 1
        if event.get("type") == "tool_use":
            result["tool_calls"] += 1
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
    return result


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
    instruction = task["instruction"]
    if mode in {"advisory", "active"}:
        instruction = (
            "Use the available pi_* Project Intelligence tools where relevant. " + instruction
        )
    command = [
        _load(MATRIX)["execution"]["opencode_executable"],
        "run",
        "--format",
        "json",
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
    timed_out = False
    process_exit: int | None = None
    try:
        process = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=task["timeout_seconds"],
            check=False,
        )
        process_exit = process.returncode
        log_path.write_text(process.stdout, encoding="utf-8")
    except subprocess.TimeoutExpired as error:
        timed_out = True
        output = error.stdout if isinstance(error.stdout, str) else ""
        log_path.write_text(output, encoding="utf-8")
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
    if timed_out:
        outcome = "TIMEOUT"
    elif measured["errors"]:
        outcome = "UNAVAILABLE" if "APIError" in measured["errors"] else "FAIL"
    elif process_exit != 0 or oracle.returncode != 0:
        outcome = "FAIL"
    else:
        outcome = "PASS"
    return {
        **cell,
        "model_id": model_id,
        "outcome": outcome,
        "process_exit": process_exit,
        "oracle_exit": oracle.returncode,
        "oracle_diagnostic": oracle.stderr.strip()[-500:],
        "wall_ms": round((time.monotonic() - started) * 1000),
        **measured,
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
) -> None:
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
    trace_log.replay()
    results: list[dict[str, Any]] = []
    if resume and output.is_file():
        previous = _load(output)
        results = list(previous.get("results", []))
    completed = {item["cell_id"] for item in results}
    for cell in cells:
        if cell["cell_id"] in completed:
            continue
        result = _execute(cell, tasks[cell["task_id"]], raw_root)
        _append_trace(trace_log, result, tasks[cell["task_id"]])
        results.append(result)
        _write_report(output, _report(scope, schedule, results, trace_log.path))
    _write_report(output, _report(scope, schedule, results, trace_log.path))


def _report(
    scope: str,
    schedule: dict[str, Any],
    results: list[dict[str, Any]],
    trace_path: Path,
) -> dict[str, Any]:
    return {
        "schema": 1,
        "run_id": f"unified-v1-{scope}",
        "classification": "E4_RUNNER_PROOF" if scope == "smoke" else "EVALUATION_RESULT",
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


def _append_trace(
    trace_log: EvaluationTraceLog, result: dict[str, Any], task: dict[str, Any]
) -> None:
    matrix = _load(MATRIX)
    suite = _load(TASK_SUITE)
    repository = next(
        item for item in suite["repositories"] if item["id"] == result["repository_id"]
    )
    capability_modes, capability_depths = _trace_capabilities(result["arm"])
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
    trace_log.append(
        EvaluationTrace(
            trace_id=trace_id,
            plan_id=matrix["matrix_id"],
            cell_id=result["cell_id"],
            task_id=result["task_id"],
            task_class=result["task_class"],
            oracle_id=f"e3-oracle:{result['task_id']}",
            input_seals=input_seals,
            capability_modes=capability_modes,
            capability_depths=capability_depths,
            used_features={},
            selected_evidence_ids=(),
            source_revision_id=repository["revision"],
            twin_revision_id=None,
            model_tier=result["model_tier"],
            model_id=result.get("model_id"),
            verification_outcome=result["outcome"],
            fallback="model_unavailable" if result["outcome"] == "UNAVAILABLE" else None,
            timings_ms={"agent_wall": result.get("wall_ms")},
        )
    )
    result["trace_id"] = trace_id


def _write_report(output: Path, report: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    sub.add_parser("metrics")
    seal_parser = sub.add_parser("seal")
    seal_parser.add_argument("target", choices=["matrix", "labels"])
    plan_parser = sub.add_parser("plan")
    plan_parser.add_argument(
        "--scope", choices=["smoke", "base", "screening", "full"], default="full"
    )
    _selection_arguments(plan_parser)
    run_parser = sub.add_parser("run")
    run_parser.add_argument(
        "--scope", choices=["smoke", "base", "screening", "full"], required=True
    )
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--max-cells", type=int)
    run_parser.add_argument("--resume", action="store_true")
    run_parser.add_argument("--raw-root", type=Path)
    _selection_arguments(run_parser)
    args = parser.parse_args()
    try:
        if args.command == "validate":
            validate()
        elif args.command == "metrics":
            validate()
            print(json.dumps(_metric_projection(), ensure_ascii=False, indent=2))
        elif args.command == "seal":
            seal(MATRIX if args.target == "matrix" else LABELS)
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
        else:
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
            )
    except (EvaluationError, KeyError, TypeError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"unified evaluation error: {error}", file=sys.stderr)
        return 1
    if args.command not in {"plan", "metrics"}:
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
