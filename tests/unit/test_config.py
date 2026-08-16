from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from extendcodeagent.core.config import CapabilityName, ConfigLayer, ConfigResolver, load_jsonc
from extendcodeagent.core.config.schema import (
    NOT_IMPLEMENTED_CAPABILITIES,
    ConfigError,
    ModelRole,
    RolloutMode,
    RoutingMode,
)


def test_precedence_and_deep_merge_are_deterministic() -> None:
    resolver = ConfigResolver()
    resolved = resolver.resolve(
        ConfigLayer(
            "user",
            {
                "project_intelligence": {
                    "enabled": True,
                    "mode": "shadow",
                    "capabilities": {"graph": "shadow", "impact": "shadow"},
                },
                "models": {"routing_mode": "local_first"},
            },
        ),
        ConfigLayer(
            "project",
            {"project_intelligence": {"capabilities": {"impact": "off"}}},
        ),
        ConfigLayer("runtime", {"models": {"routing_mode": "adaptive"}}),
        ConfigLayer("session", {"project_intelligence": {"mode": "advisory"}}),
        ConfigLayer("command", {"project_intelligence": {"mode": "active"}}),
    )

    assert resolved.project_intelligence.mode is RolloutMode.ACTIVE
    assert resolved.project_intelligence.capabilities[CapabilityName.GRAPH] is RolloutMode.SHADOW
    assert resolved.project_intelligence.capabilities[CapabilityName.IMPACT] is RolloutMode.OFF
    assert resolved.models.routing_mode is RoutingMode.ADAPTIVE
    assert resolved.applied_layers == (
        "defaults",
        "user",
        "project",
        "runtime",
        "session",
        "command",
    )


def test_resolved_configuration_is_immutable() -> None:
    resolved = ConfigResolver().resolve()
    with pytest.raises(dataclasses.FrozenInstanceError):
        resolved.models.routing_mode = RoutingMode.LOCAL_ONLY  # type: ignore[misc]
    with pytest.raises(TypeError):
        resolved.project_intelligence.capabilities[CapabilityName.GRAPH] = RolloutMode.ACTIVE  # type: ignore[index]


def test_language_analyzers_are_selected_independently_in_central_config() -> None:
    resolved = ConfigResolver().resolve(
        ConfigLayer(
            "project",
            {"project_intelligence": {"analyzers": ["javascript_typescript"]}},
        )
    )
    assert resolved.project_intelligence.analyzers == ("javascript_typescript",)

    with pytest.raises(ConfigError, match="unknown analyzer"):
        ConfigResolver().resolve(
            ConfigLayer(
                "project",
                {"project_intelligence": {"analyzers": ["unknown"]}},
            )
        )


def test_invalid_and_unknown_values_fail_closed() -> None:
    resolver = ConfigResolver()
    with pytest.raises(ConfigError, match="unknown keys"):
        resolver.resolve(ConfigLayer("project", {"surprise": True}))
    with pytest.raises(ConfigError, match="invalid project_intelligence.mode"):
        resolver.resolve(ConfigLayer("project", {"project_intelligence": {"mode": "auto"}}))
    with pytest.raises(ConfigError, match="must be a boolean"):
        resolver.resolve(ConfigLayer("project", {"project_intelligence": {"enabled": "true"}}))


@pytest.mark.parametrize(
    "capability", sorted(NOT_IMPLEMENTED_CAPABILITIES), ids=lambda item: item.value
)
@pytest.mark.parametrize("mode", ["shadow", "advisory", "active"])
def test_unimplemented_capability_cannot_be_enabled(capability: CapabilityName, mode: str) -> None:
    """Configuring a capability that does not exist fails loudly instead of being ignored."""

    with pytest.raises(ConfigError, match=f"{capability.value} is declared but not implemented"):
        ConfigResolver().resolve(
            ConfigLayer(
                "project",
                {
                    "project_intelligence": {
                        "enabled": True,
                        "mode": "active",
                        "capabilities": {capability.value: mode},
                    }
                },
            )
        )


def test_folded_capability_must_be_configured_through_its_owner() -> None:
    with pytest.raises(ConfigError, match="call_graph is governed by 'semantic'"):
        ConfigResolver().resolve(
            ConfigLayer(
                "project",
                {
                    "project_intelligence": {
                        "enabled": True,
                        "mode": "active",
                        "capabilities": {"call_graph": "active"},
                    }
                },
            )
        )


def test_unimplemented_and_folded_capabilities_accept_off() -> None:
    """The shipped default sets every capability to off, so off must stay valid."""

    resolved = ConfigResolver().resolve(
        ConfigLayer(
            "project",
            {
                "project_intelligence": {
                    "capabilities": {
                        **{name.value: "off" for name in NOT_IMPLEMENTED_CAPABILITIES},
                        "call_graph": "off",
                    }
                }
            },
        )
    )
    assert resolved.project_intelligence.capabilities[CapabilityName.UI_GRAPH] is RolloutMode.OFF


def test_endpoint_references_must_resolve() -> None:
    with pytest.raises(ConfigError, match="unknown endpoints"):
        ConfigResolver().resolve(
            ConfigLayer("project", {"models": {"roles": {"summarizer": ["missing"]}}})
        )


def test_jsonc_loader_preserves_comment_like_string_and_allows_trailing_comma(
    tmp_path: Path,
) -> None:
    path = tmp_path / "config.jsonc"
    path.write_text(
        """
        {
          // local endpoint
          "models": {
            "endpoints": {
              "small": {
                "provider_type": "fake",
                "locality": "local",
                "endpoint": "http://127.0.0.1:8080/v1", /* not a comment */
              },
            },
            "roles": {"small_structured": ["small"],},
          },
        }
        """,
        encoding="utf-8",
    )
    resolved = ConfigResolver().resolve(ConfigLayer("project", load_jsonc(path)))
    endpoint = resolved.models.endpoints["small"]
    assert endpoint.endpoint == "http://127.0.0.1:8080/v1"
    assert resolved.models.roles[ModelRole.SMALL_STRUCTURED] == ("small",)


def test_jsonc_comment_cannot_join_adjacent_tokens(tmp_path: Path) -> None:
    path = tmp_path / "invalid.jsonc"
    path.write_text('{"project_intelligence": {"enabled": t/*x*/rue}}', encoding="utf-8")
    with pytest.raises(ConfigError, match="invalid JSONC"):
        load_jsonc(path)
