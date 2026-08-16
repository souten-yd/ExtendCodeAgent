#!/usr/bin/env python3
"""Run the one-repetition E3 native OpenCode oracle proof serially."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/evaluation/task-suite-v1.json"
HARNESS = ROOT / "tools/local/e3_task_suite.py"
PYTHON = ROOT / ".venv/bin/python"
DEFAULT_ROOT = ROOT / ".evaluation/e3-native"
DEFAULT_BINARY = Path(
    "/home/souten/.local/share/control-deck/features/opencode/"
    "node_modules/opencode-ai/bin/opencode.exe"
)
LOCAL_SOURCES = {
    "extendcodeagent": Path("/home/souten/ExtendCodeAgent"),
    "controldeck": Path("/home/souten/ControlDeck"),
    "kasanecore": Path("/home/souten/KasaneCore"),
}


def _run(argv: list[str], *, cwd: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False
    )


def _prepare(task: dict[str, Any], workspace: Path) -> None:
    source = LOCAL_SOURCES[task["repository_id"]]
    result = _run(
        [
            str(PYTHON),
            str(HARNESS),
            "prepare",
            "--manifest",
            str(MANIFEST),
            "--task",
            task["id"],
            "--destination",
            str(workspace),
            "--source",
            f"{task['repository_id']}={source}",
        ],
        cwd=ROOT,
        timeout=600,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip())


def _oracle(task_id: str, workspace: Path) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            str(PYTHON),
            str(HARNESS),
            "oracle",
            "--manifest",
            str(MANIFEST),
            "--task",
            task_id,
            "--workspace",
            str(workspace),
        ],
        cwd=ROOT,
        timeout=600,
    )


def _metrics(log_path: Path) -> dict[str, Any]:
    tool_calls = 0
    tokens = {"input": 0, "output": 0, "reasoning": 0, "cache_read": 0, "cache_write": 0}
    errors: list[str] = []
    events = 0
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        events += 1
        if event.get("type") == "tool_use":
            tool_calls += 1
        if event.get("type") == "error":
            error = event.get("error")
            name = error.get("name") if isinstance(error, dict) else str(error)
            if name:
                errors.append(str(name))
        part = event.get("part")
        if isinstance(part, dict) and part.get("type") == "step-finish":
            usage = part.get("tokens")
            if isinstance(usage, dict):
                tokens["input"] += int(usage.get("input") or 0)
                tokens["output"] += int(usage.get("output") or 0)
                tokens["reasoning"] += int(usage.get("reasoning") or 0)
                cache = usage.get("cache")
                if isinstance(cache, dict):
                    tokens["cache_read"] += int(cache.get("read") or 0)
                    tokens["cache_write"] += int(cache.get("write") or 0)
    return {"events": events, "tool_calls": tool_calls, "tokens": tokens, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--model", default="opencode/big-pickle")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    manifest_check = _run(
        [str(PYTHON), str(HARNESS), "validate", "--manifest", str(MANIFEST)],
        cwd=ROOT,
        timeout=120,
    )
    if manifest_check.returncode:
        raise RuntimeError(manifest_check.stderr.strip())
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    args.root.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for task in manifest["tasks"]:
        task_id = task["id"]
        workspace = args.root / task_id
        log_path = args.root / f"{task_id}.jsonl"
        started = time.monotonic()
        process_exit: int | None = None
        timed_out = False
        if not (args.resume and workspace.exists() and log_path.exists()):
            _prepare(task, workspace)
            try:
                process = _run(
                    [
                        str(args.binary),
                        "run",
                        "--pure",
                        "--format",
                        "json",
                        "--auto",
                        "--model",
                        args.model,
                        "--dir",
                        str(workspace),
                        task["instruction"],
                    ],
                    cwd=ROOT,
                    timeout=task["timeout_seconds"],
                )
                process_exit = process.returncode
                log_path.write_text(process.stdout, encoding="utf-8")
            except subprocess.TimeoutExpired as error:
                timed_out = True
                output = error.stdout if isinstance(error.stdout, str) else ""
                log_path.write_text(output, encoding="utf-8")
        else:
            process_exit = 0
        oracle = _oracle(task_id, workspace)
        metrics = _metrics(log_path)
        if timed_out:
            outcome = "TIMEOUT"
        elif metrics["errors"]:
            outcome = "UNAVAILABLE" if "APIError" in metrics["errors"] else "FAIL"
        elif process_exit != 0 or oracle.returncode != 0:
            outcome = "FAIL"
        else:
            outcome = "PASS"
        result = {
            "task_id": task_id,
            "task_class": task["task_class"],
            "split": task["split"],
            "outcome": outcome,
            "process_exit": process_exit,
            "oracle_exit": oracle.returncode,
            "oracle_diagnostic": oracle.stderr.strip()[-500:],
            "wall_ms": round((time.monotonic() - started) * 1000),
            **metrics,
        }
        results.append(result)
        print(json.dumps(result, ensure_ascii=False), flush=True)
    outcome_counts = {
        outcome: sum(result["outcome"] == outcome for result in results)
        for outcome in ("PASS", "FAIL", "TIMEOUT", "UNAVAILABLE")
    }
    proof_status = (
        "PASS"
        if outcome_counts["PASS"] > 0
        and outcome_counts["FAIL"] > 0
        and outcome_counts["TIMEOUT"] == 0
        and outcome_counts["UNAVAILABLE"] == 0
        else "FAIL"
    )
    summary = {
        "schema": 1,
        "suite_id": manifest["suite_id"],
        "manifest_seal": manifest["seal"]["canonical_payload"],
        "runtime": "ControlDeck-managed OpenCode",
        "opencode_version": manifest["runtime_environment"]["opencode"]["version"],
        "mode": "native-pure",
        "model": args.model,
        "outcome_counts": outcome_counts,
        "native_success_rate": outcome_counts["PASS"] / len(results),
        "proof_status": proof_status,
        "results": results,
    }
    (args.root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0 if proof_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
