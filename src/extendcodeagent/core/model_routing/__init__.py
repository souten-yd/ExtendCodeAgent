"""Provider-neutral model routing contracts and deterministic foundation router."""

from .contracts import (
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
    "FakeModelAdapter",
    "ModelAdapter",
    "ModelRequest",
    "ModelResponse",
    "ModelUnavailable",
    "PolicyModelRouter",
    "RouteDecision",
    "RoutedResponse",
]
