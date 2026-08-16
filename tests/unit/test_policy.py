from __future__ import annotations

from collections.abc import Callable

import pytest

from extendcodeagent.core.config import CapabilityName, ConfigLayer, ConfigResolver
from extendcodeagent.core.config.schema import (
    CONFIGURABLE_CAPABILITIES,
    NOT_IMPLEMENTED_CAPABILITIES,
    CapabilityImplementation,
    RolloutMode,
    governing_capability,
)
from extendcodeagent.core.policy import CapabilityPolicy, CapabilityUnavailable


@pytest.mark.parametrize("enabled,mode", [(False, "active"), (True, "off")])
def test_global_off_makes_every_capability_inert(enabled: bool, mode: str) -> None:
    config = ConfigResolver().resolve(
        ConfigLayer(
            "project",
            {
                "project_intelligence": {
                    "enabled": enabled,
                    "mode": mode,
                    "capabilities": {"graph": "active"},
                }
            },
        )
    )
    policy = CapabilityPolicy.from_config(config.project_intelligence)
    assert all(policy.mode(name) is RolloutMode.OFF for name in CapabilityName)


def test_capability_mode_cannot_exceed_global_rollout() -> None:
    config = ConfigResolver().resolve(
        ConfigLayer(
            "project",
            {
                "project_intelligence": {
                    "enabled": True,
                    "mode": "advisory",
                    "capabilities": {"graph": "active", "impact": "shadow"},
                }
            },
        )
    )
    policy = CapabilityPolicy.from_config(config.project_intelligence)
    assert policy.mode(CapabilityName.GRAPH) is RolloutMode.ADVISORY
    assert policy.allows_explicit_use(CapabilityName.GRAPH)
    assert not policy.allows_automatic_effect(CapabilityName.GRAPH)
    assert policy.computes_automatically(CapabilityName.IMPACT)


def test_disabled_feature_has_no_use_or_compute_path() -> None:
    config = ConfigResolver().resolve(
        ConfigLayer(
            "project",
            {"project_intelligence": {"enabled": True, "mode": "active"}},
        )
    )
    policy = CapabilityPolicy.from_config(config.project_intelligence)
    assert not policy.is_enabled(CapabilityName.GRAPH)
    assert not policy.computes_automatically(CapabilityName.GRAPH)
    assert not policy.allows_explicit_use(CapabilityName.GRAPH)


@pytest.mark.parametrize("capability", CONFIGURABLE_CAPABILITIES, ids=lambda item: item.value)
def test_each_capability_can_be_switched_off_independently(
    policy_factory: Callable[..., CapabilityPolicy], capability: CapabilityName
) -> None:
    """Per-capability ablation: switching one off must not disturb the others."""

    policy = policy_factory("active", overrides={capability: "off"})
    assert policy.mode(capability) is RolloutMode.OFF
    assert not policy.is_enabled(capability)
    assert not policy.computes_automatically(capability)
    assert not policy.allows_explicit_use(capability)
    assert not policy.allows_automatic_effect(capability)
    with pytest.raises(CapabilityUnavailable):
        policy.require_explicit_use(capability)

    others = [
        name
        for name in CONFIGURABLE_CAPABILITIES
        if name is not capability and governing_capability(name) is name
    ]
    assert all(policy.mode(name) is RolloutMode.ACTIVE for name in others)


def test_unimplemented_capabilities_are_always_off_even_at_global_active() -> None:
    config = ConfigResolver().resolve(
        ConfigLayer(
            "project",
            {
                "project_intelligence": {
                    "enabled": True,
                    "mode": "active",
                    "capabilities": {name.value: "active" for name in CONFIGURABLE_CAPABILITIES},
                }
            },
        )
    )
    policy = CapabilityPolicy.from_config(config.project_intelligence)
    for name in NOT_IMPLEMENTED_CAPABILITIES:
        assert policy.mode(name) is RolloutMode.OFF
        assert policy.implementation(name) is CapabilityImplementation.NOT_IMPLEMENTED


def test_folded_capability_follows_its_governing_capability() -> None:
    for mode in ("off", "shadow", "advisory", "active"):
        config = ConfigResolver().resolve(
            ConfigLayer(
                "project",
                {
                    "project_intelligence": {
                        "enabled": True,
                        "mode": "active",
                        "capabilities": {CapabilityName.SEMANTIC.value: mode},
                    }
                },
            )
        )
        policy = CapabilityPolicy.from_config(config.project_intelligence)
        assert policy.mode(CapabilityName.CALL_GRAPH) is policy.mode(CapabilityName.SEMANTIC)
        assert policy.mode(CapabilityName.CALL_GRAPH) is RolloutMode(mode)
        assert policy.implementation(CapabilityName.CALL_GRAPH) is (
            CapabilityImplementation.IMPLEMENTED
        )
