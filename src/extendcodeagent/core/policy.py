"""Resolved capability behavior; feature modules never inspect raw configuration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .config.schema import CapabilityName, ProjectIntelligenceConfig, RolloutMode


@dataclass(frozen=True, slots=True)
class CapabilityPolicy:
    modes: Mapping[CapabilityName, RolloutMode]

    def __post_init__(self) -> None:
        object.__setattr__(self, "modes", MappingProxyType(dict(self.modes)))

    @classmethod
    def from_config(cls, config: ProjectIntelligenceConfig) -> CapabilityPolicy:
        if not config.enabled or config.mode is RolloutMode.OFF:
            return cls({name: RolloutMode.OFF for name in CapabilityName})
        modes = {
            name: _bounded_mode(config.mode, configured_mode)
            for name, configured_mode in config.capabilities.items()
        }
        return cls(modes)

    def mode(self, capability: CapabilityName) -> RolloutMode:
        return self.modes[capability]

    def is_enabled(self, capability: CapabilityName) -> bool:
        return self.mode(capability) is not RolloutMode.OFF

    def computes_automatically(self, capability: CapabilityName) -> bool:
        return self.mode(capability) in {RolloutMode.SHADOW, RolloutMode.ACTIVE}

    def allows_explicit_use(self, capability: CapabilityName) -> bool:
        return self.mode(capability) in {RolloutMode.ADVISORY, RolloutMode.ACTIVE}

    def allows_automatic_effect(self, capability: CapabilityName) -> bool:
        return self.mode(capability) is RolloutMode.ACTIVE


_MODE_RANK = {
    RolloutMode.OFF: 0,
    RolloutMode.SHADOW: 1,
    RolloutMode.ADVISORY: 2,
    RolloutMode.ACTIVE: 3,
}


def _bounded_mode(global_mode: RolloutMode, capability_mode: RolloutMode) -> RolloutMode:
    if _MODE_RANK[capability_mode] <= _MODE_RANK[global_mode]:
        return capability_mode
    return global_mode
