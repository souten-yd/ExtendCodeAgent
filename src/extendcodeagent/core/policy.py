"""Resolved capability behavior; feature modules never inspect raw configuration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from .config.schema import (
    DEFAULT_CAPABILITY_DEPTH,
    DEFAULT_DEPTH_PROFILE,
    NOT_IMPLEMENTED_CAPABILITIES,
    CapabilityImplementation,
    CapabilityName,
    Depth,
    DepthProfile,
    ProjectIntelligenceConfig,
    RolloutMode,
    capability_implementation,
    depth_min_inferred_confidence,
    governing_capability,
    resolve_depth,
)


class CapabilityUnavailable(RuntimeError):
    """Raised when a capability is used beyond the authority its rollout mode grants."""


@dataclass(frozen=True, slots=True)
class CapabilityPolicy:
    """Resolved authority (``modes``) and cost (``depths``) for every capability.

    The two axes are independent by construction: ``modes`` is never consulted when
    resolving a depth, and ``depths`` is never consulted when resolving authority.
    """

    modes: Mapping[CapabilityName, RolloutMode]
    depths: Mapping[CapabilityName, Depth] = field(default_factory=dict)
    profile: DepthProfile = DEFAULT_DEPTH_PROFILE

    def __post_init__(self) -> None:
        object.__setattr__(self, "modes", MappingProxyType(dict(self.modes)))
        resolved = dict(self.depths)
        for name in CapabilityName:
            resolved.setdefault(name, resolve_depth(self.profile, DEFAULT_CAPABILITY_DEPTH))
        object.__setattr__(self, "depths", MappingProxyType(resolved))

    @classmethod
    def from_config(cls, config: ProjectIntelligenceConfig) -> CapabilityPolicy:
        # Depth is resolved from the depth block alone. A globally disabled or off
        # deployment still reports the depth it would run at, because depth is a cost
        # declaration rather than an authority: mixing them would re-encode cost in
        # the rollout mode, which invariant 6 forbids.
        depths = {
            name: resolve_depth(
                config.depth_profile, config.depths.get(name, DEFAULT_CAPABILITY_DEPTH)
            )
            for name in CapabilityName
        }
        for name in CapabilityName:
            owner = governing_capability(name)
            if owner is not name:
                depths[name] = depths[owner]
        if not config.enabled or config.mode is RolloutMode.OFF:
            return cls(
                {name: RolloutMode.OFF for name in CapabilityName},
                depths,
                config.depth_profile,
            )
        bounded = {
            name: _bounded_mode(config.mode, configured_mode)
            for name, configured_mode in config.capabilities.items()
        }
        modes = {
            name: RolloutMode.OFF
            if name in NOT_IMPLEMENTED_CAPABILITIES
            else bounded[governing_capability(name)]
            for name in CapabilityName
        }
        return cls(modes, depths, config.depth_profile)

    def implementation(self, capability: CapabilityName) -> CapabilityImplementation:
        return capability_implementation(capability)

    def depth(self, capability: CapabilityName) -> Depth:
        return self.depths[capability]

    def min_inferred_confidence(self, capability: CapabilityName) -> float:
        """Confidence floor an inferred relation must clear at this capability's depth.

        This is the use-time bound the E1 `call_graph` folding decision depends on:
        inferred edges such as `may_call` are produced unconditionally so that a Twin
        revision never depends on configuration, and are filtered here instead.
        """

        return depth_min_inferred_confidence(self.depth(capability))

    def require_explicit_use(self, capability: CapabilityName) -> None:
        if not self.allows_explicit_use(capability):
            raise CapabilityUnavailable(f"{capability.value} is not available for explicit use")

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
