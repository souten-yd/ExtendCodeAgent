"""Provider-neutral model routing contracts and deterministic foundation router."""

from .adapters import OpenAICompatibleAdapter, OpenCodeHostAdapter
from .contracts import (
    AdaptiveSignals,
    ModelAdapter,
    ModelRequest,
    ModelResponse,
    ModelUnavailable,
    RouteDecision,
    RoutedResponse,
)
from .fakes import FakeModelAdapter
from .router import PolicyModelRouter

__all__ = [
    "AdaptiveSignals",
    "FakeModelAdapter",
    "ModelAdapter",
    "ModelRequest",
    "ModelResponse",
    "ModelUnavailable",
    "OpenAICompatibleAdapter",
    "OpenCodeHostAdapter",
    "PolicyModelRouter",
    "RouteDecision",
    "RoutedResponse",
]
