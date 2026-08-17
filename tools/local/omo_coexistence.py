#!/usr/bin/env python3
"""B2 OpenCode + OMO + ExtendCodeAgent coexistence runner.

The runner seals its exact runtime tuple before inference, performs the full
model-free lifecycle/tool/session preflight first, and only then permits the
five-stack local-practical coding/verification bridge.  Every stack receives an
isolated profile, workspace, server and session.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import shutil
import socket
import sqlite3
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ECA_PLUGIN = ROOT / "adapters/opencode/dist/src/plugin.js"
ECA_PYTHON = ROOT / ".venv/bin/python"
OMO_PACKAGE = "oh-my-openagent"
OMO_VERSION = "4.19.4"
MODEL_PROVIDER = "eca-local-practical"
MODEL_ID = "llama"
MODEL_ROUTE = f"{MODEL_PROVIDER}/{MODEL_ID}"
MODEL_ENDPOINT = "http://127.0.0.1:8090/v1"
MODEL_CONTEXT = 262_144
MODEL_OUTPUT = 8_192
MODEL_TASK_INSTRUCTION = (
    "Fix calc.py so add(2, 3) returns 5. Do not modify test_calc.py. "
    "Run python3 -m unittest -q and finish only after it passes."
)
EXPECTED_PI_TOOLS = {
    "pi_status",
    "pi_symbol",
    "pi_references",
    "pi_path",
    "pi_impact",
    "pi_tests",
    "pi_context",
    "pi_runtime_evidence",
    "pi_research_plan",
}
EXPECTED_OMO_TOOLS = {"background_output", "background_cancel", "call_omo_agent"}
EXPECTED_OMO_AGENT_PREFIXES = {"Sisyphus", "Hephaestus", "Prometheus"}
STACKS: dict[str, tuple[str, ...]] = {
    "native": (),
    "eca": ("eca",),
    "omo": ("omo",),
    "omo_eca": ("omo", "eca"),
    "eca_omo": ("eca", "omo"),
}
ERROR_TAXONOMY = {
    "duplicate_tool_id": "C0",
    "missing_pi_tool": "C0",
    "unexpected_pi_tool": "C0",
    "missing_omo_tool": "C0",
    "unexpected_omo_tool": "C0",
    "missing_omo_agent": "C0",
    "duplicate_tool_id_delta": "C0",
    "runtime_observation_count_not_one": "C1",
    "runtime_observation_not_observed_in_agent_flow": "C1",
    "verification_oracle_failed": "C2",
    "unexpected_changed_files": "C2",
    "omo_tools_lost_when_eca_sidecar_unavailable": "C3",
    "duplicate_tool_execution": "C3",
    "resolved_model_route_mismatch": "C4",
    "session_not_recovered": "C5",
    "tool_set_changed_after_restart": "C5",
    "sidecar_survived_first_shutdown": "C5",
    "sidecar_survived_restart_shutdown": "C5",
    "sidecar_survived_degraded_shutdown": "C5",
    "sidecar_survived_model_shutdown": "C5",
    "team_mode_not_off": "C6",
}


class CoexistenceError(RuntimeError):
    """B2 contract or runtime failure."""


@dataclass
class Server:
    process: subprocess.Popen[str]
    log_handle: Any
    url: str
    startup_ms: int


def _canonical_payload(value: Mapping[str, Any]) -> bytes:
    body = {key: item for key, item in value.items() if key != "seal"}
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    body = dict(value)
    body["seal"] = {
        "algorithm": "sha256",
        "canonical_payload": hashlib.sha256(_canonical_payload(body)).hexdigest(),
    }
    return body


def _verify_seal(value: Mapping[str, Any], label: str) -> None:
    expected = hashlib.sha256(_canonical_payload(value)).hexdigest()
    seal = value.get("seal")
    if not isinstance(seal, Mapping) or seal.get("canonical_payload") != expected:
        raise CoexistenceError(f"{label} seal mismatch")


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CoexistenceError(f"{path} root must be an object")
    return value


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _require_clean() -> None:
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise CoexistenceError("B2 plan/run requires a clean exact-head worktree")


def _opencode() -> Path:
    executable = shutil.which("opencode")
    if executable is None:
        raise CoexistenceError("opencode is unavailable")
    return Path(executable).resolve()


def _version(executable: Path) -> str:
    return subprocess.check_output([str(executable), "--version"], text=True).strip()


def _omo_root(explicit: Path | None = None) -> Path:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    configured = os.environ.get("EXTENDCODEAGENT_OMO_ROOT")
    if configured:
        candidates.append(Path(configured))
    candidates.extend(sorted(Path.home().glob(".npm/_npx/*/node_modules/oh-my-openagent")))
    for candidate in candidates:
        package = candidate / "package.json"
        plugin = candidate / "dist/index.js"
        if not package.is_file() or not plugin.is_file():
            continue
        metadata = _load(package)
        if metadata.get("name") == OMO_PACKAGE and metadata.get("version") == OMO_VERSION:
            return candidate.resolve()
    raise CoexistenceError(
        "exact oh-my-openagent@4.19.4 package not found; set EXTENDCODEAGENT_OMO_ROOT"
    )


def _fixture_fingerprint() -> str:
    return hashlib.sha256(
        b"calc.py:def add(left: int, right: int) -> int: return left - right\n"
        b"test_calc.py:unittest add(2,3)==5\n"
    ).hexdigest()


def create_plan(output: Path, omo_root: Path | None = None) -> dict[str, Any]:
    _require_clean()
    opencode = _opencode()
    omo = _omo_root(omo_root)
    plugin = omo / "dist/index.js"
    package = omo / "package.json"
    plan = _seal(
        {
            "schema": 1,
            "classification": "B2_OMO_COEXISTENCE_EXECUTION_PLAN",
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "source_revision": _head(),
            "execution_scope": "local-only",
            "model": "Qwen3.6 27B",
            "endpoint": "127.0.0.1:8090",
            "context": MODEL_CONTEXT,
            "output_limit": MODEL_OUTPUT,
            "claim_scope": "compatibility / active-scoped(local-practical)",
            "team_mode": "off",
            "opencode": {"path": str(opencode), "version": _version(opencode)},
            "omo": {
                "package": f"{OMO_PACKAGE}@{OMO_VERSION}",
                "root": str(omo),
                "package_sha256": _sha256(package),
                "plugin_sha256": _sha256(plugin),
            },
            "eca": {
                "revision": _head(),
                "plugin": str(ECA_PLUGIN),
                "plugin_sha256": _sha256(ECA_PLUGIN),
            },
            "stacks": {name: list(plugins) for name, plugins in STACKS.items()},
            "model_free_preflight_stacks": list(STACKS),
            "degraded_sidecar_orders": ["omo_eca", "eca_omo"],
            "model_bridge_stacks": list(STACKS),
            "maximum_agent_runs": len(STACKS),
            "model_parallelism": 1,
            "workspace_or_session_shared": False,
            "conflict_taxonomy_scope": {
                "C0": "IN_SCOPE_NAMESPACE_REGISTRATION",
                "C1": "IN_SCOPE_BOUNDED_LOAD_ORDER_HOOK_BEHAVIOR",
                "C2": "IN_SCOPE_BOUNDED_CONTEXT_AND_TASK_CORRECTNESS",
                "C3": "IN_SCOPE_TOOL_VISIBILITY_POLICY_AND_IDEMPOTENCE",
                "C4": "IN_SCOPE_FIXED_LOCAL_MODEL_ROUTE",
                "C5": "IN_SCOPE_SESSION_RESTART_AND_WORKSPACE_ISOLATION",
                "C6": "NOT_TESTED_TEAM_MODE_OFF",
            },
            "task_fixture_fingerprint": _fixture_fingerprint(),
            "task_instruction_sha256": hashlib.sha256(MODEL_TASK_INSTRUCTION.encode()).hexdigest(),
            "adoption_contract": {
                "compatible": "all preflight and model bridge stacks pass with equivalent oracles",
                "degraded": (
                    "core coexistence works but a documented non-critical limitation remains"
                ),
                "incompatible": (
                    "combined stack loses tools, duplicates execution, breaks isolation, "
                    "or regresses a passing control"
                ),
            },
            "unchanged": {
                "task_suite": True,
                "oracle": True,
                "corpus": True,
                "capability_design": True,
                "quality_thresholds": True,
            },
        }
    )
    _write(output, plan)
    return plan


def _verify_plan(plan: Mapping[str, Any]) -> None:
    _verify_seal(plan, "B2 plan")
    if plan.get("source_revision") != _head():
        raise CoexistenceError("B2 plan source revision is stale")
    if plan.get("execution_scope") != "local-only":
        raise CoexistenceError("B2 plan is not local-only")
    if plan.get("endpoint") != "127.0.0.1:8090":
        raise CoexistenceError("B2 plan does not use port 8090")
    if plan.get("team_mode") != "off":
        raise CoexistenceError("B2 requires Team Mode off")
    opencode = Path(str(plan["opencode"]["path"]))
    if _version(opencode) != plan["opencode"]["version"]:
        raise CoexistenceError("OpenCode version changed after plan seal")
    for section, key in (("omo", "plugin_sha256"), ("eca", "plugin_sha256")):
        path = (
            Path(str(plan[section]["root"])) / "dist/index.js"
            if section == "omo"
            else Path(str(plan[section]["plugin"]))
        )
        if _sha256(path) != plan[section][key]:
            raise CoexistenceError(f"{section} plugin changed after plan seal")


def _free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _request(
    base: str,
    path: str,
    *,
    method: str = "GET",
    body: Mapping[str, Any] | None = None,
    timeout: float = 30,
) -> Any:
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        base + path,
        data=data,
        method=method,
        headers={"content-type": "application/json"} if data else {},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _provider_readiness() -> dict[str, Any]:
    """Probe only the pinned local model inventory; this never requests inference."""

    started = time.perf_counter()
    try:
        response = _request(MODEL_ENDPOINT, "/models", timeout=10)
    except (OSError, urllib.error.URLError, TimeoutError) as error:
        return {
            "status": "UNAVAILABLE",
            "reason": type(error).__name__,
            "model_ids": [],
            "llm_calls": 0,
            "wall_ms": round((time.perf_counter() - started) * 1000),
        }
    data = response.get("data") if isinstance(response, Mapping) else None
    model_ids = sorted(
        str(item["id"])
        for item in data or []
        if isinstance(item, Mapping) and item.get("id") is not None
    )
    return {
        "status": "PASS" if MODEL_ID in model_ids else "MODEL_ID_MISSING",
        "reason": None if MODEL_ID in model_ids else f"required model id {MODEL_ID!r} absent",
        "model_ids": model_ids,
        "llm_calls": 0,
        "wall_ms": round((time.perf_counter() - started) * 1000),
    }


def _provider_config() -> dict[str, Any]:
    return {
        MODEL_PROVIDER: {
            "npm": "@ai-sdk/openai-compatible",
            "name": "B2 pinned local practical",
            "options": {"baseURL": MODEL_ENDPOINT},
            "models": {
                MODEL_ID: {
                    "name": "Qwen3.6 27B on port 8090",
                    "limit": {"context": MODEL_CONTEXT, "output": MODEL_OUTPUT},
                }
            },
        }
    }


def _plugin_paths(plan: Mapping[str, Any], stack: str) -> list[str]:
    values = {
        "eca": Path(str(plan["eca"]["plugin"])).as_uri(),
        "omo": (Path(str(plan["omo"]["root"])) / "dist/index.js").as_uri(),
    }
    return [values[item] for item in STACKS[stack]]


def _isolated_env(
    plan: Mapping[str, Any],
    stack: str,
    profile: Path,
    workspace: Path,
    *,
    degraded_sidecar: bool = False,
) -> dict[str, str]:
    home = profile / "home"
    config_home = profile / "config"
    data_home = profile / "data"
    cache_home = profile / "cache"
    for path in (home, config_home, data_home, cache_home):
        path.mkdir(parents=True, exist_ok=True)
    omo_config = config_home / "opencode/oh-my-openagent.json"
    omo_config.parent.mkdir(parents=True, exist_ok=True)
    omo_config.write_text(
        json.dumps(
            {
                "team_mode": {"enabled": False},
                "disabled_mcps": ["websearch", "context7", "grep_app"],
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    config = {
        "permission": {"external_directory": "deny"},
        "model": MODEL_ROUTE,
        "provider": _provider_config(),
        "plugin": _plugin_paths(plan, stack),
    }
    remote_credential_markers = ("API_KEY", "TOKEN", "SECRET", "CREDENTIAL", "COPILOT")
    env = {
        key: value
        for key, value in os.environ.items()
        if not any(marker in key.upper() for marker in remote_credential_markers)
    }
    env.update(
        {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(config_home),
            "XDG_DATA_HOME": str(data_home),
            "XDG_CACHE_HOME": str(cache_home),
            "OPENCODE_CONFIG_CONTENT": json.dumps(config, separators=(",", ":")),
            "OPENCODE_DISABLE_TELEMETRY": "1",
            "DO_NOT_TRACK": "1",
            "OMO_DISABLE_POSTHOG": "1",
            "OMO_SEND_ANONYMOUS_TELEMETRY": "0",
            "CODEGRAPH_NO_DOWNLOAD": "1",
            "CODEGRAPH_TELEMETRY": "0",
            "PYTHONPATH": str(ROOT / "src"),
            "EXTENDCODEAGENT_PYTHON": (
                str(profile / "missing-python") if degraded_sidecar else str(ECA_PYTHON)
            ),
            "EXTENDCODEAGENT_MODE": "advisory",
            "EXTENDCODEAGENT_ROOT": str(workspace),
        }
    )
    env.pop("VIRTUAL_ENV", None)
    env.pop("PYTHONHOME", None)
    return env


def _start(
    plan: Mapping[str, Any],
    stack: str,
    profile: Path,
    workspace: Path,
    log_path: Path,
    *,
    degraded_sidecar: bool = False,
) -> Server:
    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("w", encoding="utf-8")
    command = [
        str(plan["opencode"]["path"]),
        "serve",
        "--hostname",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    started = time.perf_counter()
    process = subprocess.Popen(
        command,
        cwd=workspace,
        env=_isolated_env(plan, stack, profile, workspace, degraded_sidecar=degraded_sidecar),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.monotonic() + 45
        last_error: BaseException | None = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                log_handle.flush()
                tail = log_path.read_text(errors="replace")[-2000:]
                raise CoexistenceError(f"{stack} OpenCode exited during startup: {tail}")
            try:
                health = _request(url, "/global/health", timeout=0.5)
                _request(url, "/project/current", timeout=15)
                if isinstance(health, Mapping) and health.get("healthy") is False:
                    raise CoexistenceError(f"{stack} health is false")
                return Server(
                    process=process,
                    log_handle=log_handle,
                    url=url,
                    startup_ms=round((time.perf_counter() - started) * 1000),
                )
            except (OSError, urllib.error.URLError, TimeoutError) as error:
                last_error = error
                time.sleep(0.05)
        raise CoexistenceError(f"{stack} startup timeout: {last_error}")
    except BaseException:
        _stop(Server(process, log_handle, url, 0))
        raise


def _stop(server: Server) -> int:
    if server.process.poll() is None:
        server.process.terminate()
        try:
            server.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.process.kill()
            server.process.wait(timeout=5)
    server.log_handle.close()
    return int(server.process.returncode or 0)


def _create_fixture(root: Path, *, broken: bool) -> None:
    root.mkdir(parents=True)
    operator = "-" if broken else "+"
    root.joinpath("calc.py").write_text(
        f"def add(left: int, right: int) -> int:\n    return left {operator} right\n",
        encoding="utf-8",
    )
    root.joinpath("test_calc.py").write_text(
        "import unittest\n\nfrom calc import add\n\n\n"
        "class AddTest(unittest.TestCase):\n"
        "    def test_add(self) -> None:\n"
        "        self.assertEqual(add(2, 3), 5)\n\n\n"
        "if __name__ == '__main__':\n"
        "    unittest.main()\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "calc.py", "test_calc.py"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=B2 Coexistence",
            "-c",
            "user.email=b2@localhost",
            "commit",
            "-qm",
            "fixture",
        ],
        check=True,
    )


def _agent_names(value: Any) -> set[str]:
    if isinstance(value, list):
        return {
            str(item.get("name"))
            for item in value
            if isinstance(item, Mapping) and item.get("name") is not None
        }
    if isinstance(value, Mapping):
        return {str(key) for key in value}
    return set()


def _sidecar_pids(workspace: Path) -> list[int]:
    expected = str(workspace.resolve())
    found: list[int] = []
    for cmdline in Path("/proc").glob("[0-9]*/cmdline"):
        try:
            value = cmdline.read_bytes().replace(b"\0", b" ").decode(errors="replace")
        except OSError:
            continue
        if "extendcodeagent.adapters.local_sidecar" in value and expected in value:
            found.append(int(cmdline.parent.name))
    return sorted(found)


def _wait_sidecar_exit(workspace: Path) -> list[int]:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        found = _sidecar_pids(workspace)
        if not found:
            return []
        time.sleep(0.05)
    return _sidecar_pids(workspace)


def _runtime_observations(database: Path) -> int:
    if not database.is_file():
        return 0
    try:
        with sqlite3.connect(database) as connection:
            row = connection.execute("SELECT COUNT(*) FROM runtime_observations").fetchone()
            return int(row[0])
    except sqlite3.OperationalError:
        return 0


def _wait_runtime_observations(database: Path, *, minimum: int, timeout: float = 10) -> int:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        count = _runtime_observations(database)
        if count >= minimum:
            return count
        time.sleep(0.05)
    return _runtime_observations(database)


def _user_omo_fingerprint() -> dict[str, Any]:
    path = Path.home() / ".omo"
    if not path.exists():
        return {"exists": False}
    digest = hashlib.sha256()
    entries = 0
    for item in sorted(path.rglob("*")):
        relative = item.relative_to(path).as_posix()
        digest.update(relative.encode())
        if item.is_symlink():
            digest.update(b"symlink:")
            digest.update(os.readlink(item).encode())
        elif item.is_file():
            digest.update(b"file:")
            with item.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
        elif item.is_dir():
            digest.update(b"dir:")
        entries += 1
    return {"exists": True, "entries": entries, "sha256": digest.hexdigest()}


def _preserve_logs(run_root: Path, destination: Path) -> None:
    for source in run_root.glob("**/*.log"):
        target = destination / source.relative_to(run_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _stack_expectations(stack: str, tools: Sequence[str], agents: set[str]) -> list[str]:
    errors: list[str] = []
    tool_set = set(tools)
    has_eca = "eca" in STACKS[stack]
    has_omo = "omo" in STACKS[stack]
    if has_eca and not tool_set >= EXPECTED_PI_TOOLS:
        errors.append("missing_pi_tool")
    if not has_eca and EXPECTED_PI_TOOLS & tool_set:
        errors.append("unexpected_pi_tool")
    if has_omo and not tool_set >= EXPECTED_OMO_TOOLS:
        errors.append("missing_omo_tool")
    if not has_omo and EXPECTED_OMO_TOOLS & tool_set:
        errors.append("unexpected_omo_tool")
    if has_omo and any(
        not any(agent.startswith(prefix) for agent in agents)
        for prefix in EXPECTED_OMO_AGENT_PREFIXES
    ):
        errors.append("missing_omo_agent")
    if any(item.startswith("team_") for item in tool_set):
        errors.append("team_mode_not_off")
    return errors


def _classified_conflicts(errors: Sequence[str]) -> list[dict[str, str]]:
    conflicts: list[dict[str, str]] = []
    for error in errors:
        key = error.split(":", 1)[0]
        if key in {"model_request", "message_capture", "operator_interrupted"}:
            taxonomy = "C4"
        elif key == "runtime":
            taxonomy = "C0"
        else:
            taxonomy = ERROR_TAXONOMY.get(key, "UNCLASSIFIED")
        conflicts.append({"conflict_class": taxonomy, "observation": error})
    return conflicts


def _preflight_stack(plan: Mapping[str, Any], stack: str, root: Path) -> dict[str, Any]:
    workspace = root / stack / "workspace"
    profile = root / stack / "profile"
    logs = root / stack / "logs"
    _create_fixture(workspace, broken=False)
    database = workspace / ".extendcodeagent/graph.db"
    first = _start(plan, stack, profile, workspace, logs / "first.log")
    errors: list[str] = []
    try:
        tools = [str(item) for item in _request(first.url, "/experimental/tool/ids")]
        agents = _agent_names(_request(first.url, "/agent"))
        errors.extend(_stack_expectations(stack, tools, agents))
        session = _request(first.url, "/session", method="POST", body={"title": f"B2 {stack}"})
        session_id = str(session["id"])
        shell = _request(
            first.url,
            f"/session/{session_id}/shell",
            method="POST",
            body={
                "agent": "build",
                "command": "python3 -c 'from calc import add; assert add(2, 3) == 5'",
            },
        )
        time.sleep(0.5)
        observations = _runtime_observations(database)
    finally:
        first_returncode = _stop(first)
    lingering_first = _wait_sidecar_exit(workspace)
    if lingering_first:
        errors.append("sidecar_survived_first_shutdown")

    second = _start(plan, stack, profile, workspace, logs / "restart.log")
    try:
        sessions = _request(second.url, "/session")
        session_ids = {
            str(item.get("id"))
            for item in sessions
            if isinstance(item, Mapping) and item.get("id") is not None
        }
        if session_id not in session_ids:
            errors.append("session_not_recovered")
        restart_tools = [str(item) for item in _request(second.url, "/experimental/tool/ids")]
        if set(restart_tools) != set(tools):
            errors.append("tool_set_changed_after_restart")
    finally:
        second_returncode = _stop(second)
    lingering_second = _wait_sidecar_exit(workspace)
    if lingering_second:
        errors.append("sidecar_survived_restart_shutdown")
    return {
        "stack": stack,
        "plugins": list(STACKS[stack]),
        "startup_ms": first.startup_ms,
        "restart_ms": second.startup_ms,
        "tool_count": len(tools),
        "pi_tools": sorted(EXPECTED_PI_TOOLS & set(tools)),
        "omo_tools": sorted(EXPECTED_OMO_TOOLS & set(tools)),
        "agent_count": len(agents),
        "omo_agents": sorted(
            agent
            for agent in agents
            if any(agent.startswith(prefix) for prefix in EXPECTED_OMO_AGENT_PREFIXES)
        ),
        "duplicate_tool_ids": sorted(item for item in set(tools) if tools.count(item) > 1),
        "team_tools": sorted(item for item in tools if item.startswith("team_")),
        "shell_response_observed": isinstance(shell, Mapping),
        "runtime_observation_count": observations,
        "runtime_observation_status": (
            "OBSERVED" if observations else "NOT_EXERCISED_BY_DIRECT_SHELL_ROUTE"
        ),
        "session_recovered": session_id in session_ids,
        "first_returncode": first_returncode,
        "second_returncode": second_returncode,
        "lingering_sidecars": sorted(set(lingering_first + lingering_second)),
        "errors": errors,
        "conflicts": _classified_conflicts(errors),
        "result": "PASS" if not errors else "FAIL",
    }


def _degraded_sidecar(plan: Mapping[str, Any], stack: str, root: Path) -> dict[str, Any]:
    workspace = root / f"{stack}-degraded" / "workspace"
    profile = root / f"{stack}-degraded" / "profile"
    logs = root / f"{stack}-degraded" / "logs"
    _create_fixture(workspace, broken=False)
    server = _start(
        plan,
        stack,
        profile,
        workspace,
        logs / "degraded.log",
        degraded_sidecar=True,
    )
    errors: list[str] = []
    try:
        tools = [str(item) for item in _request(server.url, "/experimental/tool/ids")]
        if not set(tools) >= EXPECTED_OMO_TOOLS:
            errors.append("omo_tools_lost_when_eca_sidecar_unavailable")
        session = _request(server.url, "/session", method="POST", body={"title": "B2 degraded"})
        _request(
            server.url,
            f"/session/{session['id']}/shell",
            method="POST",
            body={"agent": "build", "command": "python3 -c 'print(\"usable\")'"},
        )
    finally:
        returncode = _stop(server)
    lingering = _wait_sidecar_exit(workspace)
    if lingering:
        errors.append("sidecar_survived_degraded_shutdown")
    return {
        "stack": stack,
        "omo_tools_preserved": set(tools) >= EXPECTED_OMO_TOOLS,
        "session_usable": not errors,
        "returncode": returncode,
        "lingering_sidecars": lingering,
        "errors": errors,
        "conflicts": _classified_conflicts(errors),
        "result": "PASS" if not errors else "FAIL",
    }


def run_preflight(plan_path: Path, output: Path, raw_root: Path) -> dict[str, Any]:
    _require_clean()
    plan = _load(plan_path)
    _verify_plan(plan)
    user_omo_before = _user_omo_fingerprint()
    raw_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="eca-b2-preflight-", dir=raw_root) as directory:
        root = Path(directory)
        stacks = [_preflight_stack(plan, stack, root) for stack in STACKS]
        by_stack = {str(item["stack"]): item for item in stacks}
        limitations: list[dict[str, Any]] = []
        for stack in ("native", "eca"):
            if by_stack[stack]["duplicate_tool_ids"]:
                by_stack[stack]["errors"].append("duplicate_tool_id")
        omo_duplicates = set(by_stack["omo"]["duplicate_tool_ids"])
        for stack in ("omo_eca", "eca_omo"):
            if set(by_stack[stack]["duplicate_tool_ids"]) != omo_duplicates:
                by_stack[stack]["errors"].append("duplicate_tool_id_delta")
        if omo_duplicates:
            limitations.append(
                {
                    "conflict_class": "C0",
                    "observation": "omo_control_duplicate_tool_ids:"
                    + ",".join(sorted(omo_duplicates)),
                    "disposition": "INHERITED_OMO_CONTROL_LIMITATION",
                }
            )
        for item in stacks:
            item["errors"] = list(dict.fromkeys(item["errors"]))
            item["conflicts"] = _classified_conflicts(item["errors"])
            item["result"] = "PASS" if not item["errors"] else "FAIL"
        degraded = [_degraded_sidecar(plan, stack, root) for stack in ("omo_eca", "eca_omo")]
        _preserve_logs(root, raw_root / "logs/preflight")
    user_omo_after = _user_omo_fingerprint()
    if user_omo_before != user_omo_after:
        raise CoexistenceError("B2 isolated run changed the real user .omo directory")
    complete = all(item["result"] == "PASS" for item in [*stacks, *degraded])
    report = _seal(
        {
            "schema": 1,
            "classification": (
                "B2_MODEL_FREE_PREFLIGHT_PASS" if complete else "B2_MODEL_FREE_PREFLIGHT_FAIL"
            ),
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "source_revision": _head(),
            "execution_plan": plan["seal"]["canonical_payload"],
            "execution_scope": "local-only",
            "model_calls": 0,
            "team_mode": "off",
            "stacks": stacks,
            "degraded_sidecar": degraded,
            "limitations": limitations,
            "real_user_omo_unchanged": True,
            "pass": complete,
        }
    )
    _write(output, report)
    return report


def _message_parts(messages: Any) -> list[Mapping[str, Any]]:
    parts: list[Mapping[str, Any]] = []
    if not isinstance(messages, list):
        return parts
    for message in messages:
        if not isinstance(message, Mapping):
            continue
        value = message.get("parts")
        if isinstance(value, list):
            parts.extend(item for item in value if isinstance(item, Mapping))
    return parts


def _context_token_summary(values: list[int]) -> dict[str, int | float]:
    """Summarize full per-request prompts with nearest-rank tail percentiles."""

    if not values:
        return {
            "context_request_count": 0,
            "context_token_sum": 0,
            "average_context_tokens": 0,
            "p50_context_tokens": 0,
            "p90_context_tokens": 0,
            "p95_context_tokens": 0,
            "p99_context_tokens": 0,
            "max_context_tokens": 0,
        }
    ordered = sorted(values)

    def percentile(value: float) -> int:
        index = max(0, min(len(ordered) - 1, math.ceil(value * len(ordered)) - 1))
        return ordered[index]

    return {
        "context_request_count": len(ordered),
        "context_token_sum": sum(ordered),
        "average_context_tokens": round(mean(ordered), 3),
        "p50_context_tokens": percentile(0.50),
        "p90_context_tokens": percentile(0.90),
        "p95_context_tokens": percentile(0.95),
        "p99_context_tokens": percentile(0.99),
        "max_context_tokens": ordered[-1],
    }


def _token_metrics(messages: Any) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "llm_calls_executed": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "context_request_tokens": [],
    }
    if not isinstance(messages, list):
        return metrics
    for message in messages:
        if not isinstance(message, Mapping):
            continue
        info = message.get("info")
        if not isinstance(info, Mapping) or info.get("role") != "assistant":
            continue
        tokens = info.get("tokens")
        if not isinstance(tokens, Mapping):
            continue
        metrics["llm_calls_executed"] += 1
        input_tokens = int(tokens.get("input") or 0)
        output_tokens = int(tokens.get("output") or 0)
        reasoning_tokens = int(tokens.get("reasoning") or 0)
        cache_value = tokens.get("cache")
        cache: Mapping[str, Any] = cache_value if isinstance(cache_value, Mapping) else {}
        cache_read = int(cache.get("read") or 0)
        cache_write = int(cache.get("write") or 0)
        metrics["input_tokens"] += input_tokens
        metrics["output_tokens"] += output_tokens
        metrics["reasoning_tokens"] += reasoning_tokens
        metrics["cache_read_tokens"] += cache_read
        metrics["cache_write_tokens"] += cache_write
        metrics["context_request_tokens"].append(input_tokens + cache_read + cache_write)
    metrics.update(_context_token_summary(metrics["context_request_tokens"]))
    return metrics


def _tool_metrics(messages: Any) -> dict[str, Any]:
    calls: list[str] = []
    tools: list[str] = []
    for part in _message_parts(messages):
        if part.get("type") != "tool":
            continue
        call_id = part.get("callID") or part.get("call_id")
        tool = part.get("tool")
        if call_id is not None:
            calls.append(str(call_id))
        if tool is not None:
            tools.append(str(tool))
    return {
        "tool_calls": len(calls),
        "unique_tool_calls": len(set(calls)),
        "duplicate_call_ids": sorted(call for call in set(calls) if calls.count(call) > 1),
        "tools": tools,
    }


def _model_stack(plan: Mapping[str, Any], stack: str, root: Path) -> dict[str, Any]:
    workspace = root / stack / "workspace"
    profile = root / stack / "profile"
    logs = root / stack / "logs"
    _create_fixture(workspace, broken=True)
    database = workspace / ".extendcodeagent/graph.db"
    started = time.perf_counter()
    server = _start(plan, stack, profile, workspace, logs / "model.log")
    errors: list[str] = []
    response: Any = None
    messages: Any = []
    session_id: str | None = None
    request_failed = False
    runtime_observation_count = 0
    try:
        session = _request(
            server.url, "/session", method="POST", body={"title": f"B2 model {stack}"}
        )
        session_id = str(session["id"])
        response = _request(
            server.url,
            f"/session/{session_id}/message",
            method="POST",
            body={
                "model": {"providerID": MODEL_PROVIDER, "modelID": MODEL_ID},
                "agent": "build",
                "parts": [
                    {
                        "type": "text",
                        "text": MODEL_TASK_INSTRUCTION,
                    }
                ],
            },
            timeout=300,
        )
    except (OSError, urllib.error.URLError, TimeoutError) as error:
        errors.append(f"model_request:{type(error).__name__}")
        request_failed = True
    except KeyboardInterrupt:
        errors.append("operator_interrupted")
        request_failed = True
    finally:
        if session_id is not None:
            try:
                messages = _request(server.url, f"/session/{session_id}/message", timeout=30)
            except (OSError, urllib.error.URLError, TimeoutError) as error:
                errors.append(f"message_capture:{type(error).__name__}")
        if "eca" in STACKS[stack] and not request_failed:
            runtime_observation_count = _wait_runtime_observations(database, minimum=1)
        returncode = _stop(server)
    lingering = _wait_sidecar_exit(workspace)
    if lingering:
        errors.append("sidecar_survived_model_shutdown")
    oracle = subprocess.run(
        ["python3", "-m", "unittest", "-q"],
        cwd=workspace,
        text=True,
        capture_output=True,
        check=False,
    )
    changed = subprocess.check_output(
        ["git", "diff", "--name-only"], cwd=workspace, text=True
    ).splitlines()
    if oracle.returncode != 0:
        errors.append("verification_oracle_failed")
    if changed != ["calc.py"]:
        errors.append("unexpected_changed_files")
    tools = _tool_metrics(messages)
    if tools["duplicate_call_ids"]:
        errors.append("duplicate_tool_execution")
    if "eca" in STACKS[stack] and not request_failed and runtime_observation_count < 1:
        errors.append("runtime_observation_not_observed_in_agent_flow")
    tokens = _token_metrics(messages)
    response_info = response.get("info") if isinstance(response, Mapping) else None
    route = {
        "provider_id": (
            response_info.get("providerID") if isinstance(response_info, Mapping) else None
        ),
        "model_id": response_info.get("modelID") if isinstance(response_info, Mapping) else None,
    }
    request_gap = request_failed
    if not request_gap and route != {"provider_id": MODEL_PROVIDER, "model_id": MODEL_ID}:
        errors.append("resolved_model_route_mismatch")
    if "operator_interrupted" in errors:
        result = "OPERATOR_INTERRUPTED"
    elif request_gap:
        result = "PROVIDER_GAP" if tokens["llm_calls_executed"] == 0 else "REQUEST_GAP"
    else:
        result = "PASS" if not errors else "FAIL"
    return {
        "stack": stack,
        "plugins": list(STACKS[stack]),
        "result": result,
        "llm_call_execution": "executed",
        "errors": errors,
        "conflicts": _classified_conflicts(errors),
        "oracle_exit": oracle.returncode,
        "changed_files": changed,
        "route": route,
        "wall_ms": round((time.perf_counter() - started) * 1000),
        "startup_ms": server.startup_ms,
        "returncode": returncode,
        "lingering_sidecars": lingering,
        "runtime_observation_count": runtime_observation_count,
        "runtime_observation_status": (
            "OBSERVED"
            if runtime_observation_count
            else ("NOT_EVALUATED_REQUEST_GAP" if request_failed else "NOT_OBSERVED")
        ),
        **tokens,
        **tools,
    }


def _model_runtime_failure(stack: str, error: CoexistenceError) -> dict[str, Any]:
    errors = [f"runtime:{str(error)[-1000:]}"]
    return {
        "stack": stack,
        "plugins": list(STACKS[stack]),
        "result": "FAIL",
        "llm_call_execution": "executed",
        "errors": errors,
        "conflicts": _classified_conflicts(errors),
        "oracle_exit": None,
        "changed_files": [],
        "route": {"provider_id": None, "model_id": None},
        "wall_ms": 0,
        "startup_ms": 0,
        "returncode": None,
        "lingering_sidecars": [],
        "runtime_observation_count": 0,
        "runtime_observation_status": "NOT_EVALUATED_RUNTIME_FAILURE",
        "llm_calls_executed": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "context_request_tokens": [],
        **_context_token_summary([]),
        "tool_calls": 0,
        "unique_tool_calls": 0,
        "duplicate_call_ids": [],
        "tools": [],
    }


def _taxonomy_assessment(
    preflight: Mapping[str, Any],
    results: Sequence[Mapping[str, Any]],
    incomplete_attempts: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    records = [
        {
            "stack": "preflight",
            "conflicts": preflight.get("limitations", []),
        },
        *(item for item in preflight.get("stacks", []) if isinstance(item, Mapping)),
        *(item for item in preflight.get("degraded_sidecar", []) if isinstance(item, Mapping)),
        *results,
        *incomplete_attempts,
    ]
    observations: dict[str, list[dict[str, str]]] = {f"C{index}": [] for index in range(7)}
    unclassified: list[dict[str, str]] = []
    for record in records:
        stack = str(record.get("stack"))
        for conflict in record.get("conflicts", []):
            if not isinstance(conflict, Mapping):
                continue
            item = {"stack": stack, "observation": str(conflict.get("observation"))}
            conflict_class = str(conflict.get("conflict_class"))
            if conflict_class in observations:
                observations[conflict_class].append(item)
            else:
                unclassified.append(item)
    assessment: dict[str, dict[str, Any]] = {}
    for conflict_class, items in observations.items():
        if items:
            status = "CONFLICT_OBSERVED"
        elif conflict_class == "C6":
            status = "NOT_TESTED_TEAM_MODE_OFF"
        else:
            status = "NO_CONFLICT_OBSERVED_IN_BOUNDED_B2_SCOPE"
        assessment[conflict_class] = {"status": status, "observations": items}
    assessment["UNCLASSIFIED"] = {
        "status": "PASS" if not unclassified else "FAIL_UNCLASSIFIED_OBSERVATION",
        "observations": unclassified,
    }
    return assessment


def _task_instruction_at_revision(revision: str) -> str:
    try:
        source = subprocess.check_output(
            ["git", "show", f"{revision}:tools/local/omo_coexistence.py"],
            cwd=ROOT,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        raise CoexistenceError("cannot read source B2 runner for reuse audit") from error
    candidates = {
        value.value
        for value in ast.walk(ast.parse(source))
        if isinstance(value, ast.Constant)
        and isinstance(value.value, str)
        and value.value.startswith("Fix calc.py so add(2, 3) returns 5.")
    }
    if len(candidates) != 1:
        raise CoexistenceError("source B2 task instruction is ambiguous")
    return candidates.pop()


def _native_reuse_result(
    plan: Mapping[str, Any], source_plan_path: Path, source_report_path: Path
) -> dict[str, Any]:
    source_plan = _load(source_plan_path)
    source_report = _load(source_report_path)
    _verify_seal(source_plan, "source B2 plan")
    _verify_seal(source_report, "source B2 report")
    if source_report.get("execution_plan") != source_plan["seal"]["canonical_payload"]:
        raise CoexistenceError("source B2 report uses another plan")
    if source_report.get("source_revision") != source_plan.get("source_revision"):
        raise CoexistenceError("source B2 report revision does not match its plan")
    comparable_fields = (
        "execution_scope",
        "model",
        "endpoint",
        "context",
        "output_limit",
        "team_mode",
        "opencode",
        "omo",
        "stacks",
        "task_fixture_fingerprint",
    )
    if any(source_plan.get(key) != plan.get(key) for key in comparable_fields):
        raise CoexistenceError("source B2 native result has incompatible execution inputs")
    source_instruction = _task_instruction_at_revision(str(source_plan["source_revision"]))
    if source_instruction != MODEL_TASK_INSTRUCTION:
        raise CoexistenceError("source B2 native task instruction changed")
    native = [
        item
        for item in source_report.get("results", [])
        if isinstance(item, Mapping) and item.get("stack") == "native"
    ]
    if len(native) != 1:
        raise CoexistenceError("source B2 report does not contain one native result")
    result = dict(native[0])
    expected_route = {"provider_id": MODEL_PROVIDER, "model_id": MODEL_ID}
    if (
        result.get("result") != "PASS"
        or result.get("oracle_exit") != 0
        or result.get("changed_files") != ["calc.py"]
        or result.get("plugins") != []
        or result.get("route") != expected_route
        or result.get("errors")
    ):
        raise CoexistenceError("source B2 native result is not reusable successful evidence")
    original = json.dumps(
        result, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return {
        **result,
        "llm_call_execution": "reused",
        "result_origin": "COMPATIBILITY_MIGRATION",
        "original_source_revision": source_plan["source_revision"],
        "validated_by_revision": _head(),
        "original_result_sha256": hashlib.sha256(original).hexdigest(),
        "source_report_seal": source_report["seal"]["canonical_payload"],
        "migration_basis": {
            "stack_has_eca_plugin": False,
            "task_instruction_sha256": hashlib.sha256(source_instruction.encode()).hexdigest(),
            "execution_inputs_equal": list(comparable_fields),
            "reason": "ECA-only product change cannot affect the native no-plugin stack",
        },
    }


def _model_report(
    plan: Mapping[str, Any],
    preflight: Mapping[str, Any],
    results: list[dict[str, Any]],
    incomplete_attempts: list[dict[str, Any]],
    readiness_checks: list[dict[str, Any]],
) -> dict[str, Any]:
    completed_stacks = {str(item["stack"]) for item in results}
    pending_stacks = [stack for stack in STACKS if stack not in completed_stacks]
    complete = not pending_stacks
    by_stack = {str(item["stack"]): item for item in results}
    if not complete:
        compatibility = "NOT_EVALUATED_INCOMPLETE"
    else:
        combined_failed = any(by_stack[item]["result"] != "PASS" for item in ("omo_eca", "eca_omo"))
        control_passed = all(
            by_stack[item]["result"] == "PASS" for item in ("native", "eca", "omo")
        )
        if combined_failed and control_passed:
            compatibility = "incompatible"
        elif any(item["result"] != "PASS" for item in results) or preflight.get("limitations"):
            compatibility = "degraded"
        else:
            compatibility = "compatible"
    attempts = [*results, *incomplete_attempts]
    executed_attempts = [item for item in attempts if item.get("llm_call_execution") != "reused"]
    reused_results = [item for item in results if item.get("llm_call_execution") == "reused"]
    context_values = [
        int(value) for item in attempts for value in item.get("context_request_tokens", [])
    ]
    if complete:
        execution_stop_reason = None
    elif incomplete_attempts:
        execution_stop_reason = str(incomplete_attempts[-1]["result"])
    else:
        failed_control = next(
            (
                str(item["stack"])
                for item in results
                if item["stack"] in {"native", "eca", "omo"} and item["result"] != "PASS"
            ),
            None,
        )
        if failed_control is not None:
            execution_stop_reason = f"CONTROL_FAILURE_REPAIR_REQUIRED:{failed_control}"
        elif readiness_checks and readiness_checks[-1].get("status") != "PASS":
            execution_stop_reason = "LOCAL_PROVIDER_UNAVAILABLE"
        else:
            execution_stop_reason = "INCOMPLETE"
    return _seal(
        {
            "schema": 1,
            "classification": "B2_OMO_COEXISTENCE_RESULT",
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "source_revision": _head(),
            "execution_plan": plan["seal"]["canonical_payload"],
            "preflight": preflight["seal"]["canonical_payload"],
            "execution_scope": "local-only",
            "model": "Qwen3.6 27B",
            "endpoint": "127.0.0.1:8090",
            "context": MODEL_CONTEXT,
            "output_limit": MODEL_OUTPUT,
            "team_mode": "off",
            "results": results,
            "incomplete_attempts": incomplete_attempts,
            "provider_readiness_checks": readiness_checks,
            "conflict_taxonomy": _taxonomy_assessment(preflight, results, incomplete_attempts),
            "pending_stacks": pending_stacks,
            "complete": complete,
            "execution_stop_reason": execution_stop_reason,
            "provider_gap_pending": not complete
            and (
                any(
                    item.get("result") in {"PROVIDER_GAP", "REQUEST_GAP"}
                    for item in incomplete_attempts
                )
                or bool(readiness_checks and readiness_checks[-1].get("status") != "PASS")
            ),
            "agent_runs_requested": len(STACKS),
            "agent_runs_executed": len(executed_attempts),
            "agent_runs_reused": len(reused_results),
            "agent_runs_completed": len(results),
            "llm_calls_executed": sum(
                int(item["llm_calls_executed"]) for item in executed_attempts
            ),
            "llm_calls_reused": sum(int(item["llm_calls_executed"]) for item in reused_results),
            "input_tokens": sum(int(item["input_tokens"]) for item in attempts),
            "executed_input_tokens": sum(int(item["input_tokens"]) for item in executed_attempts),
            "reused_input_tokens": sum(int(item["input_tokens"]) for item in reused_results),
            "output_tokens": sum(int(item["output_tokens"]) for item in attempts),
            "reasoning_tokens": sum(int(item["reasoning_tokens"]) for item in attempts),
            "cache_read_tokens": sum(int(item["cache_read_tokens"]) for item in attempts),
            "cache_write_tokens": sum(int(item["cache_write_tokens"]) for item in attempts),
            "context_metric_basis": (
                "per-model-request input + cache-read + cache-write prompt tokens"
            ),
            **_context_token_summary(context_values),
            "compatibility": compatibility,
            "claim_scope": "compatibility / active-scoped(local-practical)",
            "recommended_stack_claim": False,
            "real_user_omo_unchanged": True,
        }
    )


def _validate_model_resume(
    previous: Mapping[str, Any], plan: Mapping[str, Any], preflight: Mapping[str, Any]
) -> None:
    _verify_seal(previous, "B2 model checkpoint")
    if previous.get("source_revision") != _head():
        raise CoexistenceError("B2 model checkpoint source revision is stale")
    if previous.get("execution_plan") != plan["seal"]["canonical_payload"]:
        raise CoexistenceError("B2 model checkpoint uses another plan")
    if previous.get("preflight") != preflight["seal"]["canonical_payload"]:
        raise CoexistenceError("B2 model checkpoint uses another preflight")
    completed = [str(item.get("stack")) for item in previous.get("results", [])]
    if len(completed) != len(set(completed)) or not set(completed) <= set(STACKS):
        raise CoexistenceError("B2 model checkpoint has invalid completed stacks")


def run_model_bridge(
    plan_path: Path,
    preflight_path: Path,
    output: Path,
    raw_root: Path,
    *,
    resume: bool,
    reuse_plan_path: Path | None = None,
    reuse_report_path: Path | None = None,
) -> dict[str, Any]:
    _require_clean()
    plan = _load(plan_path)
    preflight = _load(preflight_path)
    _verify_plan(plan)
    _verify_seal(preflight, "B2 preflight")
    if preflight.get("execution_plan") != plan["seal"]["canonical_payload"]:
        raise CoexistenceError("B2 preflight uses another plan")
    if preflight.get("pass") is not True:
        raise CoexistenceError("B2 model bridge is blocked by model-free preflight")
    if output.exists() and not resume:
        raise CoexistenceError("B2 model output exists; use --resume or a fresh path")
    if (reuse_plan_path is None) != (reuse_report_path is None):
        raise CoexistenceError("--reuse-plan and --reuse-report must be supplied together")
    if resume and reuse_plan_path is not None:
        raise CoexistenceError("reuse inputs are only valid for a fresh B2 model output")
    if output.is_file():
        previous = _load(output)
        _validate_model_resume(previous, plan, preflight)
        results = [dict(item) for item in previous.get("results", [])]
        incomplete_attempts = [dict(item) for item in previous.get("incomplete_attempts", [])]
        readiness_checks = [dict(item) for item in previous.get("provider_readiness_checks", [])]
        if previous.get("complete") is True:
            return dict(previous)
        if any(
            item.get("stack") in {"native", "eca", "omo"} and item.get("result") != "PASS"
            for item in results
        ):
            return dict(previous)
    else:
        results = (
            [_native_reuse_result(plan, reuse_plan_path, reuse_report_path)]
            if reuse_plan_path is not None and reuse_report_path is not None
            else []
        )
        incomplete_attempts = []
        readiness_checks = []
    raw_root.mkdir(parents=True, exist_ok=True)
    user_omo_before = _user_omo_fingerprint()
    completed_stacks = {str(item["stack"]) for item in results}
    for stack in STACKS:
        if stack in completed_stacks:
            continue
        readiness = {"stack": stack, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        readiness.update(_provider_readiness())
        readiness_checks.append(readiness)
        if readiness["status"] != "PASS":
            break
        attempt_number = len(results) + len(incomplete_attempts) + 1
        with tempfile.TemporaryDirectory(
            prefix=f"eca-b2-model-{stack}-", dir=raw_root
        ) as directory:
            root = Path(directory)
            try:
                result = _model_stack(plan, stack, root)
            except CoexistenceError as error:
                result = _model_runtime_failure(stack, error)
            _preserve_logs(root, raw_root / f"logs/model/attempt-{attempt_number:02d}-{stack}")
        if result["result"] in {"PROVIDER_GAP", "REQUEST_GAP", "OPERATOR_INTERRUPTED"}:
            incomplete_attempts.append(result)
        else:
            results.append(result)
            completed_stacks.add(stack)
        checkpoint = _model_report(plan, preflight, results, incomplete_attempts, readiness_checks)
        _write(output, checkpoint)
        if result["result"] in {"PROVIDER_GAP", "REQUEST_GAP", "OPERATOR_INTERRUPTED"}:
            break
        if stack in {"native", "eca", "omo"} and result["result"] != "PASS":
            break
    user_omo_after = _user_omo_fingerprint()
    if user_omo_before != user_omo_after:
        raise CoexistenceError("B2 isolated model run changed the real user .omo directory")
    report = _model_report(plan, preflight, results, incomplete_attempts, readiness_checks)
    _write(output, report)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan")
    plan.add_argument("--output", type=Path, required=True)
    plan.add_argument("--omo-root", type=Path)
    preflight = commands.add_parser("preflight")
    preflight.add_argument("--plan", type=Path, required=True)
    preflight.add_argument("--output", type=Path, required=True)
    preflight.add_argument("--raw-root", type=Path, required=True)
    run = commands.add_parser("run")
    run.add_argument("--plan", type=Path, required=True)
    run.add_argument("--preflight", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--raw-root", type=Path, required=True)
    run.add_argument("--resume", action="store_true")
    run.add_argument("--reuse-plan", type=Path)
    run.add_argument("--reuse-report", type=Path)
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        if args.command == "plan":
            value = create_plan(args.output, args.omo_root)
        elif args.command == "preflight":
            value = run_preflight(args.plan, args.output, args.raw_root)
        else:
            value = run_model_bridge(
                args.plan,
                args.preflight,
                args.output,
                args.raw_root,
                resume=args.resume,
                reuse_plan_path=args.reuse_plan,
                reuse_report_path=args.reuse_report,
            )
    except CoexistenceError as error:
        raise SystemExit(str(error)) from error
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
