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

        server, url, startup_ms = _start(opencode, root, "shadow", with_mcp=True)
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

            source.write_text("def value() -> int:\n    return 2\n", encoding="utf-8")
            third, external_ms = _wait_revision(database, minimum=3)
            evidence["external_edit_revision"] = third
            evidence["external_refresh_ms"] = external_ms
            evidence["plugin_tools"] = [
                item for item in _request(url, "/experimental/tool/ids") if item.startswith("pi_")
            ]
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
        finally:
            _stop(server)

        before = _revision_count(database)
        server, url, _ = _start(opencode, root, "off", with_mcp=False)
        try:
            _request(url, "/session", method="POST", body={"title": "PR-D off smoke"})
            source.write_text("def value() -> int:\n    return 3\n", encoding="utf-8")
            time.sleep(0.5)
            evidence["off_revision_count_before"] = before
            evidence["off_revision_count_after"] = _revision_count(database)
        finally:
            _stop(server)

        if evidence["stable_revision_count"] != evidence["revision_count_after_edits"]:
            raise RuntimeError("unexpected refresh loop")
        if evidence["off_revision_count_after"] != before:
            raise RuntimeError("off mode changed the Twin")
        print(json.dumps(evidence, indent=2, sort_keys=True))


def _start(
    opencode: str, root: Path, mode: str, *, with_mcp: bool, pure: bool = False
) -> tuple[subprocess.Popen[str], str, int]:
    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    config: dict[str, Any] = {} if pure else {"plugin": [PLUGIN.as_uri()]}
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


def _free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


if __name__ == "__main__":
    main()
