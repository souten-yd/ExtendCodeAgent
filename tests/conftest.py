"""Shared fixtures for capability-policy construction."""

from __future__ import annotations

from collections.abc import Callable, Mapping

import pytest

from extendcodeagent.core.config import ConfigLayer, ConfigResolver
from extendcodeagent.core.config.schema import CONFIGURABLE_CAPABILITIES, CapabilityName
from extendcodeagent.core.policy import CapabilityPolicy

PolicyFactory = Callable[..., CapabilityPolicy]


def build_policy(
    mode: str = "advisory",
    *,
    overrides: Mapping[CapabilityName, str] | None = None,
) -> CapabilityPolicy:
    """Resolve a policy through the real resolver so declarations stay authoritative."""

    capabilities = {name.value: mode for name in CONFIGURABLE_CAPABILITIES}
    for name, value in (overrides or {}).items():
        capabilities[name.value] = value
    resolved = ConfigResolver().resolve(
        ConfigLayer(
            "test",
            {
                "project_intelligence": {
                    "enabled": mode != "off",
                    "mode": mode,
                    "capabilities": capabilities,
                }
            },
        )
    )
    return CapabilityPolicy.from_config(resolved.project_intelligence)


@pytest.fixture
def policy_factory() -> PolicyFactory:
    return build_policy


@pytest.fixture
def policy() -> CapabilityPolicy:
    """A policy granting explicit use of every configurable capability."""

    return build_policy("advisory")
