"""Live transport adapters behind the provider-neutral ModelAdapter port."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from .contracts import ModelRequest, ModelResponse, ModelUnavailable

JsonObject = dict[str, object]
OpenAITransport = Callable[[str, JsonObject, dict[str, str]], JsonObject]
HostTransport = Callable[[str, str, JsonObject | None], JsonObject]


@dataclass(frozen=True, slots=True)
class OpenAICompatibleAdapter:
    base_url: str
    model_id: str
    api_key: str | None = None
    timeout_seconds: float = 120.0
    transport: OpenAITransport | None = None

    def complete(self, request: ModelRequest) -> ModelResponse:
        payload: JsonObject = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": request.max_output_tokens,
        }
        if request.requires_structured_output:
            payload["response_format"] = {"type": "json_object"}
        if request.reasoning_effort is not None:
            payload["reasoning_effort"] = request.reasoning_effort
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        raw = (self.transport or self._post)(
            f"{self.base_url.rstrip('/')}/chat/completions", payload, headers
        )
        try:
            choices = cast("list[JsonObject]", raw["choices"])
            message = cast("JsonObject", choices[0]["message"])
            usage = cast("JsonObject", raw.get("usage", {}))
            return ModelResponse(
                str(message["content"]),
                int(cast("int", usage.get("prompt_tokens", 0))),
                int(cast("int", usage.get("completion_tokens", 0))),
            )
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise ModelUnavailable("invalid OpenAI-compatible response") from error

    def _post(self, url: str, payload: JsonObject, headers: dict[str, str]) -> JsonObject:
        return _request_json("POST", url, payload, headers, self.timeout_seconds)


@dataclass(frozen=True, slots=True)
class OpenCodeHostAdapter:
    base_url: str
    provider_id: str
    model_id: str
    timeout_seconds: float = 180.0
    enable_native_tools: bool = False
    transport: HostTransport | None = None

    def complete(self, request: ModelRequest) -> ModelResponse:
        send = self.transport or self._send
        session = send("POST", "/session", {"title": "ExtendCodeAgent model routing"})
        session_id = str(session.get("id", ""))
        if not session_id:
            raise ModelUnavailable("OpenCode did not create a session")
        body: JsonObject = {
            "model": {"providerID": self.provider_id, "modelID": self.model_id},
            "parts": [{"type": "text", "text": request.prompt}],
        }
        if not self.enable_native_tools:
            body["tools"] = {}
        raw = send(
            "POST",
            f"/session/{session_id}/message",
            body,
        )
        try:
            parts = cast("list[JsonObject]", raw["parts"])
            text = "\n".join(
                str(item["text"]) for item in parts if item.get("type") == "text" and "text" in item
            )
            info = cast("JsonObject", raw.get("info", {}))
            tokens = cast("JsonObject", info.get("tokens", {}))
            return ModelResponse(
                text,
                int(cast("int", tokens.get("input", 0))),
                int(cast("int", tokens.get("output", 0))),
                sum(1 for item in parts if item.get("type") == "tool"),
                float(cast("float", info["cost"])) if info.get("cost") is not None else None,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ModelUnavailable("invalid OpenCode host response") from error

    def _send(self, method: str, path: str, payload: JsonObject | None) -> JsonObject:
        return _request_json(
            method,
            f"{self.base_url.rstrip('/')}{path}",
            payload,
            {"Content-Type": "application/json"},
            self.timeout_seconds,
        )


def _request_json(
    method: str,
    url: str,
    payload: JsonObject | None,
    headers: dict[str, str],
    timeout: float,
) -> JsonObject:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            value = json.loads(response.read())
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        raise ModelUnavailable(f"model transport unavailable: {url}") from error
    if not isinstance(value, dict):
        raise ModelUnavailable("model transport returned a non-object response")
    return cast("JsonObject", value)
