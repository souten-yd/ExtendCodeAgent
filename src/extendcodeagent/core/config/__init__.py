"""Centralized configuration schema and resolver."""

from .resolver import ConfigLayer, ConfigResolver, load_jsonc
from .schema import (
    ALL_CAPABILITIES,
    CAPABILITY_FOLDED_INTO,
    CONFIGURABLE_CAPABILITIES,
    NOT_IMPLEMENTED_CAPABILITIES,
    CapabilityImplementation,
    CapabilityName,
    ConfigError,
    EndpointConfig,
    ModelRole,
    ResolvedConfig,
    RolloutMode,
    RoutingMode,
    capability_implementation,
    governing_capability,
    unconfigurable_reason,
)

__all__ = [
    "ALL_CAPABILITIES",
    "CAPABILITY_FOLDED_INTO",
    "CONFIGURABLE_CAPABILITIES",
    "NOT_IMPLEMENTED_CAPABILITIES",
    "CapabilityImplementation",
    "CapabilityName",
    "ConfigError",
    "ConfigLayer",
    "ConfigResolver",
    "EndpointConfig",
    "ModelRole",
    "ResolvedConfig",
    "RolloutMode",
    "RoutingMode",
    "capability_implementation",
    "governing_capability",
    "load_jsonc",
    "unconfigurable_reason",
]
