#!/usr/bin/env python3
"""Acquire pinned B0 repositories and record truthful initial baselines."""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from extendcodeagent.core.config import ConfigLayer, ConfigResolver
from extendcodeagent.core.config.schema import CONFIGURABLE_CAPABILITIES
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.service import ProjectIntelligenceApplication

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "docs/evaluation/b0a-screening-plan-v1.json"
MATRIX = ROOT / "docs/evaluation/evaluation-matrix-v1.json"
TASKS = ROOT / "docs/evaluation/task-suite-v1.json"
CORPUS = ROOT / "docs/evaluation/test-portfolio-corpus-v1.json"


class BootstrapError(RuntimeError):
    """A pinned input or bootstrap invariant failed."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BootstrapError(f"cannot read {path}: {error}") from error
    if not isinstance(value, dict):
        raise BootstrapError(f"{path} root must be an object")
    return value


def _digest(value: dict[str, Any]) -> str:
    body = {key: item for key, item in value.items() if key != "seal"}
    payload = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def validate() -> None:
    plan, matrix, tasks = _load(PLAN), _load(MATRIX), _load(TASKS)
    if plan.get("seal") != {"algorithm": "sha256", "canonical_payload": _digest(plan)}:
        raise BootstrapError("B0a screening-plan seal does not match canonical payload")
    if plan["inputs"]["matrix_seal"] != matrix["seal"]["canonical_payload"]:
        raise BootstrapError("B0a plan matrix seal is stale")
    if plan["inputs"]["task_suite_seal"] != tasks["seal"]["canonical_payload"]:
        raise BootstrapError("B0a plan task-suite seal is stale")
    configured = set(plan["screening"]["capability_model_tiers"])
    expected = {item.value for item in CONFIGURABLE_CAPABILITIES}
    if configured != expected:
        raise BootstrapError("B0a plan must assign exactly one tier to every ablatable capability")
    task_ids = {item["id"] for item in tasks["tasks"]}
    if not set(plan["screening"]["task_subset"]) <= task_ids:
        raise BootstrapError("B0a screening subset contains an unknown task")
    if set(plan["decision_policy"]["forbidden"]) != {"promote", "demote", "reject"}:
        raise BootstrapError("B0a screening must forbid adoption decisions")


def _repositories() -> list[dict[str, Any]]:
    task_repositories = {
        item["id"]: {
            "id": item["id"],
            "repository": item["repository"],
            "revision": item["revision"],
            "role": item["role"],
            "source_manifest": TASKS.relative_to(ROOT).as_posix(),
        }
        for item in _load(TASKS)["repositories"]
    }
    for item in _load(CORPUS)["repositories"]:
        if item["id"] in task_repositories:
            raise BootstrapError(f"repository ID collision: {item['id']}")
        task_repositories[item["id"]] = {
            "id": item["id"],
            "repository": f"https://github.com/{item['repository']}.git",
            "revision": item["ref"],
            "role": item["role"],
            "source_manifest": CORPUS.relative_to(ROOT).as_posix(),
        }
    return [task_repositories[key] for key in sorted(task_repositories)]


def _run(argv: list[str], cwd: Path, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False
    )


def acquire(repository: dict[str, Any], corpus_root: Path) -> Path:
    destination = corpus_root / str(repository["id"])
    if (destination / ".git").exists():
        origin = _git(destination, "remote", "get-url", "origin")
        dirty = bool(_git(destination, "status", "--porcelain"))
        expected_origin = str(repository["repository"])
        if _normalized_remote(origin) != _normalized_remote(expected_origin) or dirty:
            archive = corpus_root / "archive"
            archive.mkdir(parents=True, exist_ok=True)
            destination.rename(archive / f"{destination.name}-{time.time_ns()}")
    if not (destination / ".git").exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        result = _run(
            [
                "git",
                "clone",
                "--filter=blob:none",
                "--no-checkout",
                repository["repository"],
                str(destination),
            ],
            ROOT,
            1800,
        )
        if result.returncode:
            raise BootstrapError(f"clone failed for {repository['id']}: {result.stderr.strip()}")
    fetch = _run(["git", "fetch", "--force", "origin", repository["revision"]], destination, 1800)
    if fetch.returncode:
        raise BootstrapError(f"fetch failed for {repository['id']}: {fetch.stderr.strip()}")
    checkout = _run(["git", "checkout", "--detach", repository["revision"]], destination)
    if checkout.returncode:
        raise BootstrapError(f"checkout failed for {repository['id']}: {checkout.stderr.strip()}")
    head = _git(destination, "rev-parse", "HEAD")
    if head != repository["revision"]:
        raise BootstrapError(f"pin mismatch for {repository['id']}: {head}")
    return destination


def _normalized_remote(value: str) -> str:
    return value.rstrip("/").removesuffix(".git")


def _git(root: Path, *args: str) -> str:
    result = _run(["git", *args], root)
    if result.returncode:
        raise BootstrapError(result.stderr.strip())
    return result.stdout.strip()


def _policy() -> CapabilityPolicy:
    modes = {item.value: "active" for item in CONFIGURABLE_CAPABILITIES}
    resolved = ConfigResolver().resolve(
        ConfigLayer(
            "b0a-bootstrap",
            {"project_intelligence": {"enabled": True, "mode": "active", "capabilities": modes}},
        )
    )
    return CapabilityPolicy.from_config(resolved.project_intelligence)


def _tracked_files(root: Path) -> list[str]:
    result = _run(["git", "ls-files", "-z"], root)
    if result.returncode:
        raise BootstrapError(result.stderr.strip())
    return sorted(item for item in result.stdout.split("\0") if item)


def _discovery(files: list[str]) -> tuple[list[str], list[str], list[str], list[str]]:
    names = set(files)
    runners: set[str] = set()
    commands: set[str] = set()
    if "pyproject.toml" in names or "pytest.ini" in names or "tox.ini" in names:
        runners.add("pytest")
        commands.add("pytest")
    if "package.json" in names:
        runners.add("package-script")
        commands.add("npm test")
    if any(path.endswith(("vitest.config.ts", "vitest.config.js")) for path in files):
        runners.add("vitest")
    if any(path.endswith(("playwright.config.ts", "playwright.config.js")) for path in files):
        runners.add("playwright")
    test_files = [
        path
        for path in files
        if "/test" in f"/{path.casefold()}"
        or path.casefold().startswith("test")
        or path.casefold().endswith((".test.js", ".test.ts", ".spec.js", ".spec.ts", ".spec.tsx"))
    ]
    languages = sorted(
        {
            suffix
            for path in files
            if (suffix := Path(path).suffix.casefold()) in {".py", ".js", ".jsx", ".ts", ".tsx"}
        }
    )
    return sorted(runners), sorted(commands), test_files, languages


def bootstrap(repository: dict[str, Any], root: Path, state_root: Path) -> dict[str, Any]:
    files = _tracked_files(root)
    runners, commands, test_files, languages = _discovery(files)
    database = state_root / f"{repository['id']}.db"
    database.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with ProjectIntelligenceApplication(root, database, _policy()) as application:
        opened = application.process_event((), "b0a-initial-bootstrap")
        status = application.status()
        project_id = application.project.project_id
        workspace_id = application.project.workspace_id
    build_ms = round((time.monotonic() - started) * 1000)
    exact_pin = _git(root, "rev-parse", "HEAD") == repository["revision"]
    clean = not _git(root, "status", "--porcelain")
    ready = exact_pin and opened["accepted"] and status["readiness"] == "ready"
    unsupported = [
        item["name"]
        for item in status["capabilities"]
        if item["implementation"] == "not_implemented"
    ]
    return {
        **repository,
        "eligibility": "INCLUDED" if ready else "EXCLUDED_BOOTSTRAP_GAP",
        "workspace_identity": {"project_id": project_id, "workspace_id": workspace_id},
        "source_revision": {
            "expected": repository["revision"],
            "observed": _git(root, "rev-parse", "HEAD"),
            "exact": exact_pin,
        },
        "worktree": {"clean": clean, "fingerprint_classification": "observed"},
        "twin": {
            "readiness": status["readiness"],
            "revision_id": status["revision_id"],
            "nodes": status["nodes"],
            "edges": status["edges"],
            "build_time_ms": build_ms,
            "diagnostics": opened.get("diagnostics", []),
        },
        "discovery": {
            "languages": languages,
            "test_runners": {"status": "inferred" if runners else "unavailable", "items": runners},
            "commands": {"status": "inferred" if commands else "unavailable", "items": commands},
            "test_inventory": {
                "status": "inferred" if test_files else "unavailable",
                "count": len(test_files),
            },
        },
        "baseline_evidence": {
            "repository_identity": "observed",
            "graph_and_test_inventory": "inferred",
            "runtime_execution": "unknown",
            "correctness": "unknown",
        },
        "unsupported_or_degraded_analysis": unsupported,
    }


def environment() -> dict[str, Any]:
    matrix = _load(MATRIX)
    executable = Path(matrix["execution"]["opencode_executable"])
    version = _run([str(executable), "--version"], ROOT, 60)
    return {
        "eca_revision": _git(ROOT, "rev-parse", "HEAD"),
        "opencode": {
            "executable": str(executable),
            "version": version.stdout.strip() if version.returncode == 0 else None,
            "status": "AVAILABLE" if version.returncode == 0 else "UNAVAILABLE",
        },
        "model_tiers": matrix["model_tiers"],
        "hardware": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cpu_count": os.cpu_count(),
        },
    }


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _bootstrap_worker(
    repository: dict[str, Any], source: Path, state_root: Path, checkpoint: Path
) -> None:
    try:
        result = bootstrap(repository, source, state_root)
    except Exception as error:
        result = _gap(repository, "bootstrap_error", f"{type(error).__name__}: {error}")
    _write_json(checkpoint, result)


def _gap(repository: dict[str, Any], reason: str, diagnostic: str) -> dict[str, Any]:
    return {
        **repository,
        "eligibility": "EXCLUDED_BOOTSTRAP_GAP",
        "gap_reason": reason,
        "diagnostic": diagnostic[-1000:],
        "baseline_evidence": {
            "repository_identity": "unknown",
            "graph_and_test_inventory": "unknown",
            "runtime_execution": "unknown",
            "correctness": "unknown",
        },
    }


def run_bootstraps(
    repositories: list[dict[str, Any]],
    raw_root: Path,
    output: Path,
    *,
    timeout_seconds: int,
    resume: bool,
) -> None:
    checkpoints = raw_root / "checkpoints"
    results: list[dict[str, Any]] = []
    for repository in repositories:
        checkpoint = checkpoints / f"{repository['id']}.json"
        if resume and checkpoint.is_file():
            results.append(_load(checkpoint))
            continue
        try:
            source = acquire(repository, raw_root / "corpus")
        except (BootstrapError, subprocess.TimeoutExpired) as error:
            result = _gap(repository, "acquisition_error", str(error))
            _write_json(checkpoint, result)
            results.append(result)
            _write_bootstrap_report(output, results)
            continue
        process = multiprocessing.Process(
            target=_bootstrap_worker,
            args=(repository, source, raw_root / "state", checkpoint),
        )
        process.start()
        process.join(timeout_seconds)
        if process.is_alive():
            process.terminate()
            process.join(30)
            result = _gap(
                repository,
                "twin_timeout",
                f"initial Twin exceeded {timeout_seconds} seconds",
            )
            _write_json(checkpoint, result)
        elif checkpoint.is_file():
            result = _load(checkpoint)
        else:
            result = _gap(
                repository,
                "bootstrap_worker_exit",
                f"worker exited {process.exitcode} without a checkpoint",
            )
            _write_json(checkpoint, result)
        results.append(result)
        _write_bootstrap_report(output, results)


def _write_bootstrap_report(output: Path, results: list[dict[str, Any]]) -> None:
    report = {
        "schema": 1,
        "classification": "B0A_BOOTSTRAP",
        "screening_plan_seal": _load(PLAN)["seal"]["canonical_payload"],
        "environment": environment(),
        "repositories": results,
        "summary": {
            "attempted": len(results),
            "included": sum(item["eligibility"] == "INCLUDED" for item in results),
            "excluded_bootstrap_gap": sum(item["eligibility"] != "INCLUDED" for item in results),
        },
    }
    _write_json(output, report)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    sub.add_parser("repositories")
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--raw-root", type=Path, required=True)
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--repository", action="append", default=[])
    run_parser.add_argument("--timeout-seconds", type=int, default=600)
    run_parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    try:
        validate()
        if args.command == "repositories":
            print(json.dumps(_repositories(), ensure_ascii=False, indent=2))
        elif args.command == "run":
            selected = set(args.repository)
            repositories = _repositories()
            unknown = selected - {item["id"] for item in repositories}
            if unknown:
                raise BootstrapError(f"unknown repositories: {sorted(unknown)}")
            if selected:
                repositories = [item for item in repositories if item["id"] in selected]
            if args.timeout_seconds < 1:
                raise BootstrapError("--timeout-seconds must be positive")
            run_bootstraps(
                repositories,
                args.raw_root.resolve(),
                args.output,
                timeout_seconds=args.timeout_seconds,
                resume=args.resume,
            )
        else:
            print("B0a bootstrap validate: PASS")
    except (BootstrapError, KeyError, TypeError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"B0a bootstrap error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
