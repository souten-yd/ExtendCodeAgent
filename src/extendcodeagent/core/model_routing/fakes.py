"""Deterministic adapters for offline routing and composition tests."""

from __future__ import annotations

from dataclasses import dataclass, field

from .contracts import ModelRequest, ModelResponse, ModelUnavailable


@dataclass(slots=True)
class FakeModelAdapter:
    response_text: str = "ok"
    available: bool = True
    calls: list[ModelRequest] = field(default_factory=list)

    def complete(self, request: ModelRequest) -> ModelResponse:
        self.calls.append(request)
        if not self.available:
            raise ModelUnavailable("fake endpoint unavailable")
        return ModelResponse(text=self.response_text)
