"""Versioned authenticated local HTTP adapter for runtime integrations."""

from __future__ import annotations

import argparse
import json
import secrets
import signal
import threading
from collections.abc import Mapping
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from extendcodeagent.core.config import ConfigLayer, ConfigResolver, RolloutMode, load_jsonc
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.service import CapabilityUnavailable, ProjectIntelligenceApplication
from extendcodeagent.service.application import INTERFACE_VERSION

MAX_REQUEST_BYTES = 1_000_000
_ACTIVE_CAPABILITIES = ("graph", "twin", "semantic", "impact", "test_selection")


class LocalApiServer(HTTPServer):
    def __init__(
        self,
        application: ProjectIntelligenceApplication,
        token: str,
        address: tuple[str, int] = ("127.0.0.1", 0),
    ) -> None:
        self.application = application
        self.token = token
        super().__init__(address, _Handler)

    @property
    def url(self) -> str:
        host, port = self.server_address[:2]
        host_text = host.decode() if isinstance(host, bytes) else host
        return f"http://{host_text}:{port}"

    def serve_forever(self, poll_interval: float = 0.5) -> None:
        try:
            super().serve_forever(poll_interval)
        finally:
            self.application.close()


class _Handler(BaseHTTPRequestHandler):
    server: LocalApiServer

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/health":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not self._authorized():
            self._json(HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "unauthorized"})
            return
        self._json(
            HTTPStatus.OK,
            {
                "ok": True,
                "interface": INTERFACE_VERSION,
                "result": self.server.application.status(),
            },
        )

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/request":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not self._authorized():
            self._json(HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "unauthorized"})
            return
        try:
            request = self._request_json()
            if request.get("interface") != INTERFACE_VERSION:
                raise ValueError("unsupported interface version")
            operation = _required_string(request, "operation")
            raw_params = request.get("params", {})
            if not isinstance(raw_params, dict):
                raise ValueError("params must be an object")
            result = _dispatch(self.server.application, operation, raw_params)
        except CapabilityUnavailable as exc:
            self._json(
                HTTPStatus.CONFLICT,
                {"ok": False, "error": "capability_unavailable", "message": str(exc)},
            )
            return
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            self._json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "error": "invalid_request", "message": str(exc)},
            )
            return
        self._json(
            HTTPStatus.OK,
            {"ok": True, "interface": INTERFACE_VERSION, "result": result},
        )

    def log_message(self, format: str, *args: object) -> None:
        del format, args

    def _authorized(self) -> bool:
        return self.headers.get("Authorization") == f"Bearer {self.server.token}"

    def _request_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_REQUEST_BYTES:
            raise ValueError("invalid request size")
        value = json.loads(self.rfile.read(length))
        if not isinstance(value, dict):
            raise ValueError("request must be an object")
        return value

    def _json(self, status: HTTPStatus, value: Mapping[str, object]) -> None:
        payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def _dispatch(
    application: ProjectIntelligenceApplication, operation: str, params: dict[str, Any]
) -> dict[str, Any]:
    if operation == "status":
        return application.status()
    if operation == "event":
        return application.process_event(
            _string_tuple(params.get("paths", []), "paths"),
            _required_string(params, "kind"),
        )
    if operation == "symbol":
        return application.symbol(_required_string(params, "query"))
    if operation == "references":
        return application.references(_required_string(params, "canonical_ref"))
    if operation == "path":
        target = params.get("target_ref")
        if target is not None and not isinstance(target, str):
            raise ValueError("target_ref must be a string or null")
        return application.path(
            _required_string(params, "source_ref"),
            target,
            allowed_edge_types=_string_tuple(
                params.get("allowed_edge_types", []), "allowed_edge_types"
            ),
            min_confidence=_float(params.get("min_confidence", 0.0), "min_confidence"),
            max_depth=_optional_int(params.get("max_depth"), "max_depth"),
            max_paths=_integer(params.get("max_paths", 20), "max_paths"),
        )
    if operation == "impact":
        return application.impact(
            _string_tuple(params.get("changed_refs", []), "changed_refs"),
            min_confidence=_float(params.get("min_confidence", 0.0), "min_confidence"),
            max_depth=_optional_int(params.get("max_depth"), "max_depth"),
            include_historical=_boolean(
                params.get("include_historical", False), "include_historical"
            ),
        )
    if operation == "tests":
        return application.tests(_string_tuple(params.get("changed_refs", []), "changed_refs"))
    raise ValueError(f"unknown operation: {operation}")


def resolve_policy(
    *,
    user_config: Path | None = None,
    project_config: Path | None = None,
    mode: RolloutMode | None = None,
) -> tuple[CapabilityPolicy, int, int]:
    layers: list[ConfigLayer] = []
    for name, path in (("user", user_config), ("project", project_config)):
        if path is not None and path.is_file():
            layers.append(ConfigLayer(name, load_jsonc(path)))
    if mode is not None:
        layers.append(
            ConfigLayer(
                "command",
                {
                    "project_intelligence": {
                        "enabled": mode is not RolloutMode.OFF,
                        "mode": mode.value,
                        "capabilities": {name: mode.value for name in _ACTIVE_CAPABILITIES},
                    }
                },
            )
        )
    resolved = ConfigResolver().resolve(*layers)
    config = resolved.project_intelligence
    return (
        CapabilityPolicy.from_config(config),
        config.context.max_items,
        config.analysis.max_depth,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--user-config", type=Path)
    parser.add_argument("--project-config", type=Path)
    parser.add_argument("--mode", choices=[item.value for item in RolloutMode])
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    mode = RolloutMode(args.mode) if args.mode else None
    project_config = args.project_config or args.root / "extendcodeagent.jsonc"
    policy, max_items, max_depth = resolve_policy(
        user_config=args.user_config, project_config=project_config, mode=mode
    )
    application = ProjectIntelligenceApplication(
        args.root, args.database, policy, max_items=max_items, max_depth=max_depth
    )
    server = LocalApiServer(application, secrets.token_urlsafe(32), port_address(args.port))

    def stop(*_: object) -> None:
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    print(
        json.dumps(
            {
                "event": "ready",
                "interface": INTERFACE_VERSION,
                "url": server.url,
                "token": server.token,
            },
            separators=(",", ":"),
        ),
        flush=True,
    )
    try:
        server.serve_forever()
    finally:
        server.server_close()


def port_address(port: int) -> tuple[str, int]:
    if not 0 <= port <= 65535:
        raise ValueError("port must be between 0 and 65535")
    return ("127.0.0.1", port)


def _required_string(values: Mapping[str, Any], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _string_tuple(value: Any, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{name} must be an array of strings")
    return tuple(value)


def _float(value: Any, name: str) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    return float(value)


def _integer(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    return value


def _optional_int(value: Any, name: str) -> int | None:
    return None if value is None else _integer(value, name)


def _boolean(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


if __name__ == "__main__":
    main()
