from __future__ import annotations

import json
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


def _application(root: Path, database: Path) -> ProjectIntelligenceApplication:
    resolved = ConfigResolver().resolve(
        ConfigLayer(
            "test",
            {
                "project_intelligence": {
                    "enabled": True,
                    "mode": "advisory",
                    "capabilities": {
                        name: "advisory"
                        for name in ("graph", "twin", "semantic", "impact", "test_selection")
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
