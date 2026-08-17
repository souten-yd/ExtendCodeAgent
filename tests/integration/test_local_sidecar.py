from __future__ import annotations

import json
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from extendcodeagent.adapters.local_sidecar import LocalApiServer
from extendcodeagent.core.config import ConfigLayer, ConfigResolver
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.service import ProjectIntelligenceApplication
from extendcodeagent.service.application import INTERFACE_VERSION


def _application(
    root: Path, database: Path, *, mode: str = "advisory"
) -> ProjectIntelligenceApplication:
    resolved = ConfigResolver().resolve(
        ConfigLayer(
            "test",
            {
                "project_intelligence": {
                    "enabled": True,
                    "mode": mode,
                    "capabilities": {
                        name: mode
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
                    },
                }
            },
        )
    )
    return ProjectIntelligenceApplication(
        root, database, CapabilityPolicy.from_config(resolved.project_intelligence)
    )


def _request(server: LocalApiServer, token: str, body: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{server.url}/v1/request",
        json.dumps(body).encode(),
        {"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        value = json.load(response)
    assert isinstance(value, dict)
    return value


def test_sidecar_round_trip_and_interface_rejection(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "service.py").write_text("def leaf():\n    return 1\n", encoding="utf-8")
    server = LocalApiServer(_application(root, tmp_path / "graph.db"), "secret")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        symbol = _request(
            server,
            "secret",
            {
                "interface": INTERFACE_VERSION,
                "operation": "symbol",
                "params": {"query": "leaf"},
            },
        )
        assert symbol["ok"] is True
        assert symbol["result"]["items"][0]["canonical_ref"] == "py://service#leaf"
        timing = symbol["result"]["timing"]
        assert set(timing) == {
            "cold_twin_build_ms",
            "snapshot_load_ms",
            "adjacency_index_build_ms",
            "query_execution_ms",
            "json_serialization_ms",
        }
        assert all(isinstance(value, int | float) and value >= 0 for value in timing.values())
        assert timing["cold_twin_build_ms"] > 0
        assert timing["snapshot_load_ms"] > 0
        compact = _request(
            server,
            "secret",
            {
                "interface": INTERFACE_VERSION,
                "operation": "symbol",
                "params": {"query": "leaf", "view": "compact"},
            },
        )
        assert compact["result"]["definition"] == ["service.py"]
        assert compact["result"]["coverage_complete"] is False
        with pytest.raises(urllib.error.HTTPError) as wrong_version:
            _request(
                server,
                "secret",
                {"interface": "future.v2", "operation": "status", "params": {}},
            )
        assert wrong_version.value.code == 400
        with pytest.raises(urllib.error.HTTPError) as unauthorized:
            _request(
                server,
                "wrong",
                {"interface": INTERFACE_VERSION, "operation": "status", "params": {}},
            )
        assert unauthorized.value.code == 401
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_sidecar_context_runtime_ingest_and_evidence_round_trip(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "service.py").write_text("def leaf():\n    return 1\n", encoding="utf-8")
    server = LocalApiServer(_application(root, tmp_path / "graph.db", mode="active"), "secret")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        context = _request(
            server,
            "secret",
            {
                "interface": INTERFACE_VERSION,
                "operation": "context",
                "params": {
                    "objective": "inspect leaf",
                    "target_refs": ["py://service#leaf"],
                    "profile": "weak",
                },
            },
        )
        ingest = _request(
            server,
            "secret",
            {
                "interface": INTERFACE_VERSION,
                "operation": "runtime_ingest",
                "params": {
                    "observation_id": "tool-call-1",
                    "kind": "runtime",
                    "status": "observed",
                    "started_at": "2026-08-13T00:00:00+00:00",
                    "finished_at": "2026-08-13T00:00:01+00:00",
                    "observed_refs": ["py://service#leaf"],
                    "tool": "shell",
                },
            },
        )
        evidence = _request(
            server,
            "secret",
            {
                "interface": INTERFACE_VERSION,
                "operation": "runtime_evidence",
                "params": {"refs": ["py://service#leaf"]},
            },
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    assert context["result"]["items"][0]["why_included"] == "target_ref"
    assert ingest["result"]["accepted"] is True
    assert evidence["result"]["items"][0]["status"] == "observed"


def test_sidecar_runtime_contract_negotiates_and_collects_host_neutral_signals(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "service.py").write_text("def leaf():\n    return 1\n", encoding="utf-8")
    server = LocalApiServer(_application(root, tmp_path / "graph.db", mode="active"), "secret")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    capabilities = [
        {"name": name, "status": "supported", "reason": ""}
        for name in (
            "observe_task",
            "observe_session",
            "observe_file_mutation",
            "observe_tool_execution",
            "observe_model_route",
            "observe_verification",
            "deliver_context",
            "expose_tools",
            "request_model",
            "session_lifecycle",
            "reconnect",
            "mcp",
        )
    ]
    try:
        connected = _request(
            server,
            "secret",
            {
                "interface": INTERFACE_VERSION,
                "operation": "runtime_connect",
                "params": {
                    "runtime_name": "test-runtime",
                    "runtime_version": "1",
                    "capabilities": capabilities,
                },
            },
        )
        for payload in (
            {
                "signal_id": "task",
                "kind": "task",
                "runtime_session_id": "session",
                "task_text": "fix leaf",
            },
            {
                "signal_id": "session",
                "kind": "session",
                "runtime_session_id": "session",
                "lifecycle_state": "created",
            },
            {
                "signal_id": "model",
                "kind": "model",
                "runtime_session_id": "session",
                "model_provider": "local",
                "model_id": "qwen",
            },
            {
                "signal_id": "delivery",
                "kind": "advisory_delivery",
                "runtime_session_id": "session",
                "delivery_channel": "tool",
                "tool": "pi_symbol",
            },
        ):
            _request(
                server,
                "secret",
                {
                    "interface": INTERFACE_VERSION,
                    "operation": "runtime_signal",
                    "params": {
                        **payload,
                        "observed_at": "2026-08-17T00:00:00+00:00",
                        "paths": [],
                        "producer": "test_adapter",
                        "producer_version": "1",
                    },
                },
            )
        _request(
            server,
            "secret",
            {
                "interface": INTERFACE_VERSION,
                "operation": "event",
                "params": {"kind": "file.edited", "paths": ["service.py"]},
            },
        )
        _request(
            server,
            "secret",
            {
                "interface": INTERFACE_VERSION,
                "operation": "event",
                "params": {"kind": "session.idle", "paths": []},
            },
        )
        _request(
            server,
            "secret",
            {
                "interface": INTERFACE_VERSION,
                "operation": "runtime_ingest",
                "params": {
                    "observation_id": "verification",
                    "kind": "test",
                    "status": "passed",
                    "started_at": "2026-08-17T00:00:00+00:00",
                    "finished_at": "2026-08-17T00:00:01+00:00",
                    "observed_refs": ["py://service#leaf"],
                    "command": "pytest",
                    "runtime_session_id": "session",
                    "runtime_call_id": "call",
                },
            },
        )
        contract = _request(
            server,
            "secret",
            {
                "interface": INTERFACE_VERSION,
                "operation": "runtime_contract",
                "params": {},
            },
        )["result"]
        evidence = _request(
            server,
            "secret",
            {
                "interface": INTERFACE_VERSION,
                "operation": "runtime_evidence",
                "params": {"refs": ["py://service#leaf"]},
            },
        )["result"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert connected["result"]["runtime"]["name"] == "test-runtime"
    assert contract["signals"]["task"]["task_text"] == "fix leaf"
    assert contract["signals"]["session"]["lifecycle_state"] == "created"
    assert contract["signals"]["mutation"]["paths"] == ["service.py"]
    assert contract["signals"]["model"]["model_id"] == "qwen"
    assert contract["signals"]["advisory_delivery"]["tool"] == "pi_symbol"
    assert contract["tool_execution_count"] == 1
    assert contract["verification_count"] == 1
    assert contract["diagnostics"] == []
    assert evidence["items"][0]["runtime_session_id"] == "session"
    assert evidence["items"][0]["runtime_call_id"] == "call"


def test_sidecar_stops_when_parent_pipe_closes(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "service.py").write_text("def leaf():\n    return 1\n", encoding="utf-8")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "extendcodeagent.adapters.local_sidecar",
            "--root",
            str(root),
            "--database",
            str(tmp_path / "graph.db"),
            "--mode",
            "advisory",
            "--parent-stdin-lifecycle",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert process.stdout is not None
        ready = json.loads(process.stdout.readline())
        assert ready["event"] == "ready"
        assert process.stdin is not None
        process.stdin.close()
        assert process.wait(timeout=5) == 0
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
