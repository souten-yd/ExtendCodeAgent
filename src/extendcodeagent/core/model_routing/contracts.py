"""Logical model request/response and adapter interfaces."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Protocol

from ..config.schema import ModelRole


class ModelUnavailable(RuntimeError):
    """An endpoint could not satisfy a request without implying task success."""


@dataclass(frozen=True, slots=True)
class ModelRequest:
    role: ModelRole
    prompt: str
    context_tokens: int = 0
    contains_source_code: bool = False
    remote_context_approved: bool = False
    requires_structured_output: bool = False
    requires_tools: bool = False
    minimum_reasoning_strength: int = 0
    requested_endpoint: str | None = None

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("model prompt must not be empty")
        if self.context_tokens < 0:
            raise ValueError("context_tokens must not be negative")
        if self.minimum_reasoning_strength < 0:
            raise ValueError("minimum_reasoning_strength must not be negative")


@dataclass(frozen=True, slots=True)
class ModelResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0

    def __post_init__(self) -> None:
        if self.input_tokens < 0 or self.output_tokens < 0:
            raise ValueError("model token counts must not be negative")


@dataclass(frozen=True, slots=True)
class RouteDecision:
    selected_endpoint: str | None
    candidates: tuple[str, ...]
    rejected: Mapping[str, tuple[str, ...]]
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "rejected", MappingProxyType(dict(self.rejected)))


@dataclass(frozen=True, slots=True)
class RoutedResponse:
    response: ModelResponse
    decision: RouteDecision
    attempts: tuple[str, ...]


class ModelAdapter(Protocol):
    def complete(self, request: ModelRequest) -> ModelResponse: ...


class ModelRouter(Protocol):
    def route(self, request: ModelRequest) -> RouteDecision: ...

    def execute(self, request: ModelRequest) -> RoutedResponse: ...
