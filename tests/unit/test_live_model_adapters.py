from __future__ import annotations

from extendcodeagent.core.config.schema import ModelRole
from extendcodeagent.core.model_routing import (
    ModelRequest,
    OpenAICompatibleAdapter,
    OpenCodeHostAdapter,
)


def test_openai_compatible_adapter_uses_bounded_chat_completion_contract() -> None:
    calls: list[tuple[str, dict[str, object], dict[str, str]]] = []

    def transport(
        url: str, payload: dict[str, object], headers: dict[str, str]
    ) -> dict[str, object]:
        calls.append((url, payload, headers))
        return {
            "choices": [{"message": {"content": '{"answer":"ok"}'}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 4},
        }

    adapter = OpenAICompatibleAdapter("http://127.0.0.1:11434/v1", "qwen", transport=transport)
    response = adapter.complete(
        ModelRequest(
            ModelRole.SMALL_STRUCTURED,
            "one focused question",
            max_output_tokens=96,
            reasoning_effort="none",
            requires_structured_output=True,
        )
    )
    assert calls[0][0].endswith("/chat/completions")
    assert calls[0][1]["response_format"] == {"type": "json_object"}
    assert calls[0][1]["max_tokens"] == 96
    assert calls[0][1]["reasoning_effort"] == "none"
    assert response.text == '{"answer":"ok"}'
    assert (response.input_tokens, response.output_tokens) == (12, 4)


def test_opencode_host_adapter_uses_stable_session_model_contract() -> None:
    calls: list[tuple[str, str, dict[str, object] | None]] = []

    def transport(method: str, path: str, payload: dict[str, object] | None) -> object:
        calls.append((method, path, payload))
        if path == "/session":
            return {"id": "session-1"}
        response = {
            "info": {"role": "assistant", "tokens": {"input": 8, "output": 3}, "cost": 0.012},
            "parts": [{"type": "tool"}, {"type": "text", "text": "host answer"}],
        }
        return [response] if method == "GET" else response

    adapter = OpenCodeHostAdapter(
        "http://127.0.0.1:4096",
        "opencode",
        "big-pickle",
        transport=transport,
    )
    response = adapter.complete(ModelRequest(ModelRole.STRATEGY_REASONER, "bounded strategy"))
    message = calls[1][2]
    assert isinstance(message, dict)
    assert message["model"] == {"providerID": "opencode", "modelID": "big-pickle"}
    assert message["tools"] == {}
    assert response.text == "host answer"
    assert (response.input_tokens, response.output_tokens) == (8, 3)
    assert response.tool_calls == 1
    assert response.cost == 0.012
    assert calls[-1][:2] == ("DELETE", "/session/session-1")
