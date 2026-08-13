#!/usr/bin/env python3
"""Real OpenCode stable plugin/MCP/off/reconnect smoke, with no model call."""

from __future__ import annotations

import json
import os
import shutil
import socket
import sqlite3
import statistics
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
PLUGIN = REPO / "adapters/opencode/dist/src/plugin.js"
MCP = REPO / "adapters/opencode/dist/src/mcp.js"
PYTHON = REPO / ".venv/bin/python"
RUFF = REPO / ".venv/bin/ruff"


def main() -> None:
    opencode = shutil.which("opencode")
    if not opencode:
        raise SystemExit("opencode is required; install the tested stable version first")
    version = subprocess.check_output([opencode, "--version"], text=True).strip()
    runtime_model = os.environ.get("EXTENDCODEAGENT_SMOKE_MODEL")
    with tempfile.TemporaryDirectory(prefix="extendcodeagent-opencode-") as directory:
        root = Path(directory)
        source = root / "service.py"
        source.write_text("def value()->int:\n return 1\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "add", "service.py"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "-c",
                "user.name=ExtendCodeAgent Smoke",
                "-c",
                "user.email=smoke@localhost",
                "commit",
                "-qm",
                "fixture",
            ],
            check=True,
        )
        database = root / ".extendcodeagent/graph.db"
        evidence: dict[str, Any] = {"opencode_version": version}

        native_samples: list[int] = []
        plugin_samples: list[int] = []
        for index in range(3):
            order = ((True, native_samples), (False, plugin_samples))
            if index % 2:
                order = tuple(reversed(order))
            for pure, samples in order:
                server, _, elapsed = _start(
                    opencode,
                    root,
                    "off" if pure else "shadow",
                    with_mcp=False,
                    pure=pure,
                )
                samples.append(elapsed)
                _stop(server)
        native_median = round(statistics.median(native_samples))
        plugin_median = round(statistics.median(plugin_samples))
        evidence["native_startup_samples_ms"] = native_samples
        evidence["plugin_startup_samples_ms"] = plugin_samples
        evidence["native_startup_median_ms"] = native_median
        evidence["plugin_startup_median_ms"] = plugin_median
        evidence["startup_median_overhead_ms"] = plugin_median - native_median

        server, url, startup_ms = _start(
            opencode, root, "shadow", with_mcp=True, model=runtime_model
        )
        try:
            evidence["integration_startup_ms"] = startup_ms
            session = _request(url, "/session", method="POST", body={"title": "PR-D smoke"})
            session_id = session["id"]
            first, initial_ms = _wait_revision(database, minimum=1)
            evidence["initial_revision"] = first
            evidence["initial_revision_ms"] = initial_ms

            _request(
                url,
                f"/session/{session_id}/shell",
                method="POST",
                body={"agent": "build", "command": f"{RUFF} format service.py"},
            )
            second, tool_edit_ms = _wait_revision(database, minimum=2)
            evidence["tool_edit_revision"] = second
            evidence["tool_edit_refresh_ms"] = tool_edit_ms
            time.sleep(0.5)
            evidence["session_shell_runtime_observation_count"] = _observation_count(database)

            if runtime_model:
                before_model = _observation_count(database)
                provider_id, model_id = _model_parts(runtime_model)
                model_started = time.perf_counter()
                model_response = _request(
                    url,
                    f"/session/{session_id}/message",
                    method="POST",
                    body={
                        "model": {"providerID": provider_id, "modelID": model_id},
                        "agent": "build",
                        "tools": {"bash": True},
                        "parts": [
                            {
                                "type": "text",
                                "text": (
                                    "Use the bash tool exactly once to run "
                                    "python -m py_compile service.py. Then report the result."
                                ),
                            }
                        ],
                    },
                    timeout=180,
                )
                evidence["runtime_model_wall_ms"] = round(
                    (time.perf_counter() - model_started) * 1000
                )
                model_info = model_response.get("info", {})
                if isinstance(model_info, dict):
                    evidence["runtime_model_cost"] = model_info.get("cost")
                    evidence["runtime_model_tokens"] = model_info.get("tokens")
                observation_count, observation = _wait_observation(
                    database, minimum=before_model + 1
                )
                evidence["runtime_model"] = runtime_model
                evidence["runtime_observation_count"] = observation_count
                evidence["runtime_observation_status"] = observation["status"]
                evidence["runtime_observation_kind"] = observation["kind"]
                evidence["runtime_observation_tool"] = observation["tool"]
                evidence["runtime_observation_source_revision"] = observation["source_revision"][
                    "value"
                ]

            source.write_text("def value() -> int:\n    return 2\n", encoding="utf-8")
            third, external_ms = _wait_revision(database, minimum=3)
            evidence["external_edit_revision"] = third
            evidence["external_refresh_ms"] = external_ms
            evidence["plugin_tools"] = [
                item for item in _request(url, "/experimental/tool/ids") if item.startswith("pi_")
            ]
            expected_tools = {
                "pi_status",
                "pi_symbol",
                "pi_references",
                "pi_path",
                "pi_impact",
                "pi_tests",
                "pi_context",
                "pi_runtime_evidence",
            }
            if set(evidence["plugin_tools"]) != expected_tools:
                raise RuntimeError("unexpected Project Intelligence tool set")
            evidence["mcp_status"] = _request(url, "/mcp")["extendcodeagent"]["status"]
            time.sleep(0.5)
            evidence["revision_count_after_edits"] = _revision_count(database)
            time.sleep(0.5)
            evidence["stable_revision_count"] = _revision_count(database)
        finally:
            _stop(server)

        server, url, reconnect_ms = _start(opencode, root, "shadow", with_mcp=True)
        try:
            evidence["reconnect_ms"] = reconnect_ms
            evidence["reconnect_mcp_status"] = _request(url, "/mcp")["extendcodeagent"]["status"]
            evidence["persisted_revision_count"] = _revision_count(database)
            evidence["persisted_runtime_observation_count"] = _observation_count(database)
        finally:
            _stop(server)

        before = _revision_count(database)
        observations_before = _observation_count(database)
        server, url, _ = _start(opencode, root, "off", with_mcp=False)
        try:
            _request(url, "/session", method="POST", body={"title": "PR-D off smoke"})
            source.write_text("def value() -> int:\n    return 3\n", encoding="utf-8")
            time.sleep(0.5)
            evidence["off_revision_count_before"] = before
            evidence["off_revision_count_after"] = _revision_count(database)
            evidence["off_observation_count_before"] = observations_before
            evidence["off_observation_count_after"] = _observation_count(database)
        finally:
            _stop(server)

        if evidence["stable_revision_count"] != evidence["revision_count_after_edits"]:
            raise RuntimeError("unexpected refresh loop")
        if evidence["off_revision_count_after"] != before:
            raise RuntimeError("off mode changed the Twin")
        if evidence["off_observation_count_after"] != observations_before:
            raise RuntimeError("off mode recorded runtime evidence")
        print(json.dumps(evidence, indent=2, sort_keys=True))


def _start(
    opencode: str,
    root: Path,
    mode: str,
    *,
    with_mcp: bool,
    pure: bool = False,
    model: str | None = None,
) -> tuple[subprocess.Popen[str], str, int]:
    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    config: dict[str, Any] = {} if pure else {"plugin": [PLUGIN.as_uri()]}
    if model:
        provider_id, model_id = _model_parts(model)
        if provider_id != "ollama":
            raise ValueError("the runtime smoke currently supports ollama models")
        config["model"] = model
        config["provider"] = {
            "ollama": {
                "npm": "@ai-sdk/openai-compatible",
                "name": "Ollama local",
                "options": {"baseURL": "http://127.0.0.1:11434/v1"},
                "models": {model_id: {"name": model_id}},
            }
        }
    if with_mcp:
        config["mcp"] = {
            "extendcodeagent": {
                "type": "local",
                "command": [shutil.which("node") or "node", str(MCP)],
                "enabled": True,
                "environment": {
                    "PYTHONPATH": str(REPO / "src"),
                    "EXTENDCODEAGENT_ROOT": str(root),
                    "EXTENDCODEAGENT_PYTHON": str(PYTHON),
                    "EXTENDCODEAGENT_MODE": "advisory",
                },
            }
        }
    env = {
        **os.environ,
        "OPENCODE_CONFIG_CONTENT": json.dumps(config, separators=(",", ":")),
        "PYTHONPATH": str(REPO / "src"),
        "EXTENDCODEAGENT_PYTHON": str(PYTHON),
        "EXTENDCODEAGENT_MODE": mode,
    }
    started = time.perf_counter()
    command = [opencode, "serve", "--hostname", "127.0.0.1", "--port", str(port)]
    if pure:
        command.append("--pure")
    process = subprocess.Popen(
        command,
        cwd=root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.monotonic() + 15
        last_error: OSError | None = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"OpenCode exited early: {process.stdout.read()}")
            try:
                _request(url, "/global/health", timeout=0.5)
                _request(url, "/project/current", timeout=15)
                return process, url, round((time.perf_counter() - started) * 1000)
            except OSError as error:
                last_error = error
                time.sleep(0.05)
        raise TimeoutError(f"OpenCode startup timed out: {last_error}")
    except BaseException as error:
        _stop(process)
        output = process.stdout.read() if process.stdout else ""
        raise RuntimeError(f"{error}: {output}") from error


def _stop(process: subprocess.Popen[str]) -> None:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _request(
    base: str,
    path: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
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


def _wait_revision(database: Path, *, minimum: int) -> tuple[str, int]:
    started = time.perf_counter()
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if database.is_file():
            try:
                with sqlite3.connect(database) as connection:
                    count = connection.execute("SELECT COUNT(*) FROM revisions").fetchone()[0]
                    if count >= minimum:
                        head = connection.execute(
                            "SELECT head_revision_id FROM projects"
                        ).fetchone()[0]
                        return head, round((time.perf_counter() - started) * 1000)
            except sqlite3.OperationalError:
                pass
        time.sleep(0.05)
    raise TimeoutError(f"Twin revision {minimum} was not observed")


def _revision_count(database: Path) -> int:
    with sqlite3.connect(database) as connection:
        return connection.execute("SELECT COUNT(*) FROM revisions").fetchone()[0]


def _wait_observation(database: Path, *, minimum: int) -> tuple[int, dict[str, Any]]:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            with sqlite3.connect(database) as connection:
                count = connection.execute("SELECT COUNT(*) FROM runtime_observations").fetchone()[
                    0
                ]
                if count >= minimum:
                    payload = connection.execute(
                        "SELECT payload FROM runtime_observations ORDER BY finished_at DESC LIMIT 1"
                    ).fetchone()[0]
                    return count, json.loads(payload)
        except sqlite3.OperationalError:
            pass
        time.sleep(0.05)
    raise TimeoutError(f"runtime observation {minimum} was not observed")


def _observation_count(database: Path) -> int:
    with sqlite3.connect(database) as connection:
        return connection.execute("SELECT COUNT(*) FROM runtime_observations").fetchone()[0]


def _model_parts(model: str) -> tuple[str, str]:
    provider, separator, model_id = model.partition("/")
    if not separator or not provider or not model_id:
        raise ValueError("model must use provider/model format")
    return provider, model_id


def _free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


if __name__ == "__main__":
    main()
