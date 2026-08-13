from __future__ import annotations

import pytest

from extendcodeagent.core.config import ConfigLayer, ConfigResolver
from extendcodeagent.core.config.schema import ModelConfig, ModelRole
from extendcodeagent.core.model_routing import (
    FakeModelAdapter,
    ModelRequest,
    ModelUnavailable,
    PolicyModelRouter,
)


def _config(
    routing_mode: str,
    *,
    allow_remote: bool = True,
    allow_local_fallback: bool = True,
    remote_code_policy: str = "allow",
) -> ModelConfig:
    return (
        ConfigResolver()
        .resolve(
            ConfigLayer(
                "test",
                {
                    "models": {
                        "routing_mode": routing_mode,
                        "allow_remote_escalation": allow_remote,
                        "allow_local_fallback": allow_local_fallback,
                        "remote_code_policy": remote_code_policy,
                        "endpoints": {
                            "local-small": {
                                "provider_type": "fake",
                                "locality": "local",
                                "context_window": 100,
                                "cost_class": 1,
                                "latency_class": 1,
                                "capabilities": {"structured_output": True},
                            },
                            "host-default": {
                                "provider_type": "fake",
                                "locality": "host",
                                "context_window": 1_000,
                                "cost_class": 2,
                                "latency_class": 2,
                            },
                            "remote-strong": {
                                "provider_type": "fake",
                                "locality": "remote",
                                "context_window": 10_000,
                                "cost_class": 3,
                                "latency_class": 3,
                                "capabilities": {"reasoning_strength": 5},
                            },
                        },
                        "roles": {
                            "code_reasoner": ["remote-strong", "host-default", "local-small"]
                        },
                    }
                },
            )
        )
        .models
    )


def test_local_only_never_calls_host_or_remote() -> None:
    adapters = {
        "local-small": FakeModelAdapter("local"),
        "host-default": FakeModelAdapter("host"),
        "remote-strong": FakeModelAdapter("remote"),
    }
    result = PolicyModelRouter(_config("local_only"), adapters).execute(
        ModelRequest(ModelRole.CODE_REASONER, "bounded question")
    )
    assert result.response.text == "local"
    assert len(adapters["local-small"].calls) == 1
    assert adapters["host-default"].calls == []
    assert adapters["remote-strong"].calls == []


def test_host_only_never_calls_local_or_remote() -> None:
    adapters = {
        "local-small": FakeModelAdapter("local"),
        "host-default": FakeModelAdapter("host"),
        "remote-strong": FakeModelAdapter("remote"),
    }
    result = PolicyModelRouter(_config("host_only"), adapters).execute(
        ModelRequest(ModelRole.CODE_REASONER, "bounded question")
    )
    assert result.response.text == "host"
    assert adapters["local-small"].calls == []
    assert adapters["remote-strong"].calls == []


def test_local_first_falls_back_after_unavailable_local() -> None:
    adapters = {
        "local-small": FakeModelAdapter(available=False),
        "host-default": FakeModelAdapter("host"),
        "remote-strong": FakeModelAdapter("remote"),
    }
    result = PolicyModelRouter(_config("local_first"), adapters).execute(
        ModelRequest(ModelRole.CODE_REASONER, "bounded question")
    )
    assert result.response.text == "host"
    assert result.attempts == ("local-small", "host-default")


def test_remote_code_deny_blocks_remote_endpoint() -> None:
    config = _config("frontier_first", remote_code_policy="deny")
    decision = PolicyModelRouter(config, {}).route(
        ModelRequest(ModelRole.CODE_REASONER, "source", contains_source_code=True)
    )
    assert decision.selected_endpoint == "host-default"
    assert "remote_code_policy" in decision.rejected["remote-strong"]


def test_selected_context_requires_explicit_approval() -> None:
    config = _config("frontier_first", remote_code_policy="selected_context")
    router = PolicyModelRouter(config, {})
    denied = router.route(
        ModelRequest(ModelRole.CODE_REASONER, "source", contains_source_code=True)
    )
    allowed = router.route(
        ModelRequest(
            ModelRole.CODE_REASONER,
            "source",
            contains_source_code=True,
            remote_context_approved=True,
        )
    )
    assert denied.selected_endpoint == "host-default"
    assert allowed.selected_endpoint == "remote-strong"


def test_remote_escalation_disabled_is_explainable() -> None:
    config = _config("quality_optimized", allow_remote=False)
    decision = PolicyModelRouter(config, {}).route(
        ModelRequest(ModelRole.CODE_REASONER, "high risk", minimum_reasoning_strength=5)
    )
    assert decision.selected_endpoint is None
    assert "remote_escalation_disabled" in decision.rejected["remote-strong"]
    assert "reasoning_strength_insufficient" in decision.rejected["host-default"]


def test_no_fallback_when_local_fallback_is_forbidden() -> None:
    adapters = {
        "remote-strong": FakeModelAdapter(available=False),
        "host-default": FakeModelAdapter(available=False),
        "local-small": FakeModelAdapter("local"),
    }
    router = PolicyModelRouter(_config("frontier_first", allow_local_fallback=False), adapters)
    with pytest.raises(ModelUnavailable):
        router.execute(ModelRequest(ModelRole.CODE_REASONER, "question"))
    assert adapters["local-small"].calls == []


def test_context_and_structured_output_capabilities_filter_candidates() -> None:
    decision = PolicyModelRouter(_config("local_first"), {}).route(
        ModelRequest(
            ModelRole.CODE_REASONER,
            "structured",
            context_tokens=500,
            requires_structured_output=True,
        )
    )
    assert decision.selected_endpoint is None
    assert "context_exceeds_model" in decision.rejected["local-small"]
    assert "structured_output_unsupported" in decision.rejected["host-default"]


def test_configured_retry_is_bounded_before_fallback() -> None:
    config = (
        ConfigResolver()
        .resolve(
            ConfigLayer(
                "test",
                {
                    "models": {
                        "routing_mode": "local_first",
                        "allow_local_fallback": True,
                        "endpoints": {
                            "local": {
                                "provider_type": "fake",
                                "locality": "local",
                                "retry": 1,
                            },
                            "host": {"provider_type": "fake", "locality": "host"},
                        },
                        "roles": {"summarizer": ["local", "host"]},
                    }
                },
            )
        )
        .models
    )
    local = FakeModelAdapter(available=False)
    host = FakeModelAdapter("fallback")
    result = PolicyModelRouter(config, {"local": local, "host": host}).execute(
        ModelRequest(ModelRole.SUMMARIZER, "summarize")
    )
    assert result.response.text == "fallback"
    assert result.attempts == ("local", "local", "host")
    assert len(local.calls) == 2
