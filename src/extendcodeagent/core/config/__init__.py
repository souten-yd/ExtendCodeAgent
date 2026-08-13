"""Centralized configuration schema and resolver."""

from .resolver import ConfigLayer, ConfigResolver, load_jsonc
from .schema import (
    ALL_CAPABILITIES,
    CapabilityName,
    EndpointConfig,
    ModelRole,
    ResolvedConfig,
    RolloutMode,
    RoutingMode,
)

__all__ = [
    "ALL_CAPABILITIES",
    "CapabilityName",
    "ConfigLayer",
    "ConfigResolver",
    "EndpointConfig",
    "ModelRole",
    "ResolvedConfig",
    "RolloutMode",
    "RoutingMode",
    "load_jsonc",
]
