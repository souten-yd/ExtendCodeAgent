#!/usr/bin/env python3
"""Validate, prepare and score the sealed E3 Layer B task suite."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "docs/evaluation/task-suite-v1.json"
ANSWER_PATH = ".eca-eval/answer.json"


class SuiteError(RuntimeError):
    """A deterministic manifest, preparation, or oracle failure."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SuiteError(f"cannot read manifest: {error}") from error
    if not isinstance(value, dict):
        raise SuiteError("manifest root must be an object")
    return value


def _canonical_payload(manifest: dict[str, Any]) -> bytes:
    payload = {key: value for key, value in manifest.items() if key != "seal"}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _digest(manifest: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_payload(manifest)).hexdigest()


def validate(manifest: dict[str, Any], *, require_seal: bool = True) -> None:
    required_root = {
        "schema",
        "suite_id",
        "policy",
        "runtime_environment",
        "slow_suite",
        "repositories",
        "tasks",
    }
    missing = required_root - manifest.keys()
    if missing:
        raise SuiteError(f"missing root fields: {sorted(missing)}")
    if manifest["schema"] != 1 or manifest["suite_id"] != "layer-b-task-suite-v1":
        raise SuiteError("unsupported schema or suite_id")

    repositories = manifest["repositories"]
    tasks = manifest["tasks"]
    if not isinstance(repositories, list) or not isinstance(tasks, list):
        raise SuiteError("repositories and tasks must be arrays")
    repo_by_id: dict[str, dict[str, Any]] = {}
    for repository in repositories:
        _require_keys(repository, {"id", "repository", "revision", "role"}, "repository")
        repo_id = _string(repository["id"], "repository.id")
        revision = _string(repository["revision"], f"repository {repo_id} revision")
        if len(revision) != 40 or any(char not in "0123456789abcdef" for char in revision):
            raise SuiteError(f"repository {repo_id} revision must be a full lowercase SHA")
        if repo_id in repo_by_id:
            raise SuiteError(f"duplicate repository id: {repo_id}")
        repo_by_id[repo_id] = repository

    ids: set[str] = set()
    classes: Counter[str] = Counter()
    splits: Counter[str] = Counter()
    held_out_repositories = set(manifest["policy"]["held_out_repositories"])
    for task in tasks:
        _require_keys(
            task,
            {
                "id",
                "repository_id",
                "instruction",
                "task_class",
                "split",
                "allowed_mutations",
                "timeout_seconds",
                "oracle",
            },
            "task",
        )
        task_id = _string(task["id"], "task.id")
        if task_id in ids:
            raise SuiteError(f"duplicate task id: {task_id}")
        ids.add(task_id)
        repository_id = _string(task["repository_id"], f"task {task_id} repository_id")
        if repository_id not in repo_by_id:
            raise SuiteError(f"task {task_id} references unknown repository {repository_id}")
        task_class = _string(task["task_class"], f"task {task_id} class")
        split = _string(task["split"], f"task {task_id} split")
        if split not in {"tuning", "held-out"}:
            raise SuiteError(f"task {task_id} has invalid split {split}")
        if split == "held-out" and repository_id not in held_out_repositories:
            raise SuiteError(f"held-out task {task_id} uses a tuning repository")
        if split == "tuning" and repository_id in held_out_repositories:
            raise SuiteError(f"tuning task {task_id} leaks a held-out repository")
        if not isinstance(task["allowed_mutations"], list) or not task["allowed_mutations"]:
            raise SuiteError(f"task {task_id} must bound allowed mutations")
        timeout = task["timeout_seconds"]
        if not isinstance(timeout, int) or not 30 <= timeout <= 3600:
            raise SuiteError(f"task {task_id} timeout must be 30..3600 seconds")
        oracle = task["oracle"]
        _require_keys(oracle, {"command", "expected", "checks"}, f"task {task_id} oracle")
        if oracle["command"] != [
            "python3",
            "{harness}",
            "oracle",
            "--manifest",
            "{manifest}",
            "--task",
            task_id,
            "--workspace",
            "{workspace}",
        ]:
            raise SuiteError(f"task {task_id} oracle command is not the stable harness command")
        if oracle["expected"] != {"exit_code": 0}:
            raise SuiteError(f"task {task_id} oracle expected result must be exit_code 0")
        classes[task_class] += 1
        splits[split] += 1

    policy = manifest["policy"]
    minimum = policy["minimum_tasks"]
    if len(tasks) < minimum:
        raise SuiteError(f"suite has {len(tasks)} tasks, below minimum {minimum}")
    for task_class, count in policy["minimum_per_class"].items():
        if classes[task_class] < count:
            raise SuiteError(f"class {task_class} has {classes[task_class]}, requires {count}")
    if not splits["tuning"] or not splits["held-out"]:
        raise SuiteError("both tuning and held-out tasks are required")

    runtime = manifest["runtime_environment"]
    models = runtime["models"]
    if models["local-practical"]["base_url"] != "http://127.0.0.1:8090/v1":
        raise SuiteError("local-practical must use the existing port 8090 service")
    if models["frontier-sonnet"]["id"] != "github-copilot/claude-sonnet-5":
        raise SuiteError("frontier Sonnet ID is not sealed to the discovered Copilot model")
    if models["frontier-codex"]["id"] != "github-copilot/gpt-5.3-codex":
        raise SuiteError("frontier Codex ID is not sealed to the discovered Copilot model")
    if runtime["opencode"]["version"] != "1.18.16":
        raise SuiteError("OpenCode must be the discovered ControlDeck-managed version")

    omo = runtime["omo"]
    if omo["current_result"] != "PASS_MODEL_FREE_COEXISTENCE_SMOKE":
        raise SuiteError("OMO and ECA model-free coexistence smoke is not recorded")
    if omo["local_low_result"] != "UNAVAILABLE":
        raise SuiteError("the unavailable local-low arm must not be promoted to PASS")

    slow_suite = manifest["slow_suite"]
    _require_keys(
        slow_suite,
        {"repository_id", "threshold_seconds", "commands", "measurement"},
        "slow_suite",
    )
    slow_repository_id = _string(slow_suite["repository_id"], "slow_suite.repository_id")
    if slow_repository_id not in repo_by_id:
        raise SuiteError("slow_suite references an unknown repository")
    commands = slow_suite["commands"]
    if not isinstance(commands, list) or not commands:
        raise SuiteError("slow_suite.commands must contain at least one argv array")
    if any(
        not isinstance(command, list) or not all(isinstance(arg, str) for arg in command)
        for command in commands
    ):
        raise SuiteError("slow_suite commands must be shell-free argv arrays")
    measurement = slow_suite["measurement"]
    _require_keys(measurement, {"status", "wall_seconds", "revision"}, "slow_suite.measurement")
    threshold = slow_suite["threshold_seconds"]
    if measurement["status"] != "PASS":
        raise SuiteError("slow_suite measurement must PASS on the pinned revision")
    if not isinstance(threshold, int) or not isinstance(measurement["wall_seconds"], int):
        raise SuiteError("slow_suite threshold and wall time must be integer seconds")
    if measurement["wall_seconds"] <= threshold:
        raise SuiteError("slow_suite wall time does not exceed the threshold")
    if measurement["revision"] != repo_by_id[slow_repository_id]["revision"]:
        raise SuiteError("slow_suite measurement revision does not match the repository pin")

    if require_seal:
        seal = manifest.get("seal")
        if seal != {"algorithm": "sha256", "canonical_payload": _digest(manifest)}:
            raise SuiteError("manifest seal does not match canonical payload")


def _require_keys(value: object, keys: set[str], label: str) -> None:
    if not isinstance(value, dict):
        raise SuiteError(f"{label} must be an object")
    missing = keys - value.keys()
    if missing:
        raise SuiteError(f"{label} missing fields: {sorted(missing)}")


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SuiteError(f"{label} must be a non-empty string")
    return value


def _task(manifest: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in manifest["tasks"]:
        if task["id"] == task_id:
            return cast(dict[str, Any], task)
    raise SuiteError(f"unknown task: {task_id}")


def _repository(manifest: dict[str, Any], repo_id: str) -> dict[str, Any]:
    for repository in manifest["repositories"]:
        if repository["id"] == repo_id:
            return cast(dict[str, Any], repository)
    raise SuiteError(f"unknown repository: {repo_id}")


def _run(argv: list[str], cwd: Path, *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False
    )


def prepare(
    manifest: dict[str, Any], task_id: str, destination: Path, sources: dict[str, Path]
) -> None:
    validate(manifest)
    task = _task(manifest, task_id)
    repository = _repository(manifest, task["repository_id"])
    if destination.exists():
        raise SuiteError(f"destination already exists: {destination}")
    source = sources.get(repository["id"])
    clone_source = str(source if source is not None else repository["repository"])
    clone = _run(
        ["git", "clone", "--no-checkout", clone_source, str(destination)], ROOT, timeout=600
    )
    if clone.returncode:
        raise SuiteError(f"clone failed: {clone.stderr.strip()[-500:]}")
    checkout = _run(["git", "checkout", "--detach", repository["revision"]], destination)
    if checkout.returncode:
        raise SuiteError(f"checkout failed: {checkout.stderr.strip()[-500:]}")

    setup = task.get("setup", {})
    for item in setup.get("files", []):
        path = _safe_path(destination, item["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(item["content"], encoding="utf-8")
    for item in setup.get("replacements", []):
        path = _safe_path(destination, item["path"])
        content = path.read_text(encoding="utf-8")
        old = item["old"]
        if content.count(old) != 1:
            raise SuiteError(f"setup replacement in {item['path']} did not match exactly once")
        path.write_text(content.replace(old, item["new"], 1), encoding="utf-8")
    if setup:
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "ECA Evaluation",
            "GIT_AUTHOR_EMAIL": "evaluation@invalid.local",
            "GIT_COMMITTER_NAME": "ECA Evaluation",
            "GIT_COMMITTER_EMAIL": "evaluation@invalid.local",
            "GIT_AUTHOR_DATE": "2026-08-16T00:00:00Z",
            "GIT_COMMITTER_DATE": "2026-08-16T00:00:00Z",
        }
        add = subprocess.run(["git", "add", "-A"], cwd=destination, env=env, check=False)
        commit = subprocess.run(
            ["git", "commit", "-m", f"E3 setup {task_id}"],
            cwd=destination,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if add.returncode or commit.returncode:
            raise SuiteError(f"setup commit failed: {commit.stderr.strip()[-500:]}")


def _safe_path(workspace: Path, relative: str) -> Path:
    path = (workspace / relative).resolve()
    if not path.is_relative_to(workspace.resolve()):
        raise SuiteError(f"path escapes workspace: {relative}")
    return path


def oracle(manifest: dict[str, Any], task_id: str, workspace: Path) -> None:
    validate(manifest)
    task = _task(manifest, task_id)
    if not workspace.is_dir():
        raise SuiteError(f"workspace is not a directory: {workspace}")
    status = _run(["git", "status", "--porcelain", "--untracked-files=all"], workspace)
    if status.returncode:
        raise SuiteError("cannot inspect workspace mutations")
    changed = [line[3:] for line in status.stdout.splitlines() if len(line) >= 4]
    allowed = task["allowed_mutations"]
    disallowed = [
        path for path in changed if not any(_matches_scope(path, scope) for scope in allowed)
    ]
    if disallowed:
        raise SuiteError(f"mutations outside allowed scope: {disallowed}")

    for check in task["oracle"]["checks"]:
        kind = check["kind"]
        if kind == "answer":
            answer_path = _safe_path(workspace, check.get("path", ANSWER_PATH))
            try:
                answer = json.loads(answer_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise SuiteError(f"invalid answer file: {error}") from error
            for key, expected in check["equals"].items():
                actual = answer.get(key)
                if actual != expected:
                    raise SuiteError(f"answer {key} mismatch: {actual!r} != {expected!r}")
        elif kind == "file_content":
            actual = _safe_path(workspace, check["path"]).read_text(encoding="utf-8")
            if actual != check["equals"]:
                raise SuiteError(f"file content mismatch: {check['path']}")
        elif kind == "path_exists":
            if not _safe_path(workspace, check["path"]).exists():
                raise SuiteError(f"required path missing: {check['path']}")
        elif kind == "path_absent":
            if _safe_path(workspace, check["path"]).exists():
                raise SuiteError(f"forbidden path exists: {check['path']}")
        elif kind == "command":
            result = _run(check["argv"], workspace, timeout=check.get("timeout_seconds", 300))
            if result.returncode != check.get("exit_code", 0):
                tail = (result.stdout + "\n" + result.stderr).strip()[-1000:]
                raise SuiteError(f"oracle command failed ({result.returncode}): {tail}")
        else:
            raise SuiteError(f"unknown oracle check kind: {kind}")


def _matches_scope(path: str, scope: str) -> bool:
    normalized = scope.rstrip("/")
    return path == normalized or path.startswith(normalized + "/")


def _sources(values: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        repo_id, separator, raw_path = value.partition("=")
        if not separator:
            raise SuiteError(f"source must be REPOSITORY_ID=PATH: {value}")
        result[repo_id] = Path(raw_path).resolve()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    seal_parser = subparsers.add_parser("seal")
    seal_parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    prepare_parser.add_argument("--task", required=True)
    prepare_parser.add_argument("--destination", type=Path, required=True)
    prepare_parser.add_argument("--source", action="append", default=[])
    oracle_parser = subparsers.add_parser("oracle")
    oracle_parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    oracle_parser.add_argument("--task", required=True)
    oracle_parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()

    try:
        manifest = _load(args.manifest)
        if args.command == "validate":
            validate(manifest)
        elif args.command == "seal":
            validate(manifest, require_seal=False)
            manifest["seal"] = {"algorithm": "sha256", "canonical_payload": _digest(manifest)}
            args.manifest.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        elif args.command == "prepare":
            prepare(manifest, args.task, args.destination.resolve(), _sources(args.source))
        else:
            oracle(manifest, args.task, args.workspace.resolve())
    except (SuiteError, KeyError, TypeError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"E3 task suite error: {error}", file=sys.stderr)
        return 1
    print(f"E3 task suite {args.command}: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
