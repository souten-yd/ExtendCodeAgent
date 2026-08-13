from __future__ import annotations

import pytest

from extendcodeagent.core.config import CapabilityName, ConfigLayer, ConfigResolver
from extendcodeagent.core.config.schema import RolloutMode
from extendcodeagent.core.policy import CapabilityPolicy


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
