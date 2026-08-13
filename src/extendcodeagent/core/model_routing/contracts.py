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
class AdaptiveSignals:
    impact_size: int = 0
    file_count: int = 0
    language_count: int = 1
    uncertainty: float = 0.0
    strategy_scope: int = 0
    evidence_conflict: bool = False
    context_requirement: int = 0
    security_sensitive: bool = False

    def required_reasoning_strength(self) -> int:
        values = [0]
        if self.impact_size >= 20 or self.file_count >= 10 or self.language_count >= 3:
            values.append(3)
        if self.strategy_scope >= 3 or self.evidence_conflict or self.uncertainty >= 0.75:
            values.append(4)
        if self.security_sensitive or self.context_requirement >= 50_000:
            values.append(5)
        return max(values)


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
    adaptive_signals: AdaptiveSignals | None = None

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
