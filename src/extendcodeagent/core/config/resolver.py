"""Layered configuration loading, merge, validation, and immutable materialization."""

from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, TypeVar, cast

from .schema import (
    ALL_CAPABILITIES,
    KNOWN_ANALYZERS,
    AnalysisBudgets,
    CapabilityDepth,
    CapabilityName,
    ConfigError,
    ContextBudgets,
    Depth,
    DepthProfile,
    EndpointCapabilities,
    EndpointConfig,
    EndpointLocality,
    ModelConfig,
    ModelRole,
    ProjectIntelligenceConfig,
    ProviderType,
    RemoteCodePolicy,
    ResolvedConfig,
    RolloutMode,
    RoutingMode,
    depth_rank,
    unconfigurable_reason,
)

RawConfig = Mapping[str, Any]
EnumT = TypeVar("EnumT", bound=StrEnum)

DEFAULT_CONFIG: dict[str, Any] = {
    "project_intelligence": {
        "enabled": False,
        "mode": "off",
        "capabilities": {name.value: "off" for name in ALL_CAPABILITIES},
        "analyzers": list(KNOWN_ANALYZERS),
        "analysis": {
            "max_files": 10_000,
            "max_file_bytes": 2_000_000,
            "max_graph_nodes": 1_000_000,
            "max_graph_edges": 4_000_000,
            "max_depth": 6,
            "incremental_batch_ms": 100,
            "background_workers": 2,
            "memory_budget_mb": 1024,
        },
        "depth": {
            "profile": "balanced",
            "capabilities": {},
        },
        "context": {
            "max_tokens": 8_192,
            "max_items": 100,
            "min_confidence": 0.25,
            "include_runtime": True,
            "include_tests": True,
            "include_uncertainty": True,
            "auto_inject": "false",
        },
    },
    "models": {
        "routing_mode": "host_only",
        "allow_remote_escalation": False,
        "allow_local_fallback": False,
        "remote_code_policy": "deny",
        "roles": {},
        "endpoints": {},
    },
}

_ROOT_KEYS = frozenset(DEFAULT_CONFIG)
_PI_KEYS = frozenset(DEFAULT_CONFIG["project_intelligence"])
_MODEL_KEYS = frozenset(DEFAULT_CONFIG["models"])
_ANALYSIS_KEYS = frozenset(DEFAULT_CONFIG["project_intelligence"]["analysis"])
_CONTEXT_KEYS = frozenset(DEFAULT_CONFIG["project_intelligence"]["context"])
_ENDPOINT_KEYS = frozenset(
    {
        "provider_type",
        "locality",
        "model_id",
        "endpoint",
        "context_window",
        "max_output",
        "timeout_seconds",
        "retry",
        "cost_class",
        "latency_class",
        "privacy_class",
        "capabilities",
    }
)
_ENDPOINT_CAPABILITY_KEYS = frozenset(
    {"structured_output", "tools", "reasoning_strength", "code_strength"}
)


@dataclass(frozen=True, slots=True)
class ConfigLayer:
    name: str
    values: RawConfig


class ConfigResolver:
    """Resolve ordered layers; later layers override earlier ones."""

    def resolve(self, *layers: ConfigLayer) -> ResolvedConfig:
        merged = deepcopy(DEFAULT_CONFIG)
        applied = ["defaults"]
        for layer in layers:
            if not layer.name.strip():
                raise ConfigError("configuration layer name must not be empty")
            _validate_mapping(layer.values, "configuration layer")
            _deep_merge(merged, layer.values)
            applied.append(layer.name)
        return _materialize(merged, tuple(applied))


def load_jsonc(path: str | Path) -> dict[str, Any]:
    source = Path(path).read_text(encoding="utf-8")
    try:
        decoded = json.loads(_remove_trailing_commas(_remove_comments(source)))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSONC in {path}: {exc.msg} at line {exc.lineno}") from exc
    if not isinstance(decoded, dict):
        raise ConfigError(f"configuration root in {path} must be an object")
    return decoded


def _remove_comments(source: str) -> str:
    result: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""
        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue
        if char == "/" and next_char == "/":
            index += 2
            while index < len(source) and source[index] not in "\r\n":
                index += 1
            continue
        if char == "/" and next_char == "*":
            result.append(" ")
            index += 2
            while index + 1 < len(source) and source[index : index + 2] != "*/":
                if source[index] in "\r\n":
                    result.append(source[index])
                index += 1
            if index + 1 >= len(source):
                raise ConfigError("unterminated block comment in JSONC")
            index += 2
            continue
        result.append(char)
        index += 1
    return "".join(result)


def _remove_trailing_commas(source: str) -> str:
    result: list[str] = []
    in_string = False
    escaped = False
    index = 0
    while index < len(source):
        char = source[index]
        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue
        if char == ",":
            lookahead = index + 1
            while lookahead < len(source) and source[lookahead].isspace():
                lookahead += 1
            if lookahead < len(source) and source[lookahead] in "}]":
                index += 1
                continue
        result.append(char)
        index += 1
    return "".join(result)


def _deep_merge(target: dict[str, Any], source: RawConfig) -> None:
    for key, value in source.items():
        current = target.get(key)
        if isinstance(current, dict) and isinstance(value, Mapping):
            _deep_merge(current, value)
        else:
            target[key] = deepcopy(value)


def _materialize(raw: dict[str, Any], applied: tuple[str, ...]) -> ResolvedConfig:
    _reject_unknown(raw, _ROOT_KEYS, "root")
    pi = _mapping(raw["project_intelligence"], "project_intelligence")
    models = _mapping(raw["models"], "models")
    _reject_unknown(pi, _PI_KEYS, "project_intelligence")
    _reject_unknown(models, _MODEL_KEYS, "models")

    enabled = _boolean(pi["enabled"], "project_intelligence.enabled")
    mode = _enum(RolloutMode, pi["mode"], "project_intelligence.mode")
    capabilities_raw = _mapping(pi["capabilities"], "project_intelligence.capabilities")
    known_capabilities = {item.value for item in ALL_CAPABILITIES}
    _reject_unknown(capabilities_raw, known_capabilities, "project_intelligence.capabilities")
    capabilities = {
        name: _enum(
            RolloutMode,
            capabilities_raw.get(name.value, "off"),
            f"project_intelligence.capabilities.{name.value}",
        )
        for name in ALL_CAPABILITIES
    }
    rejected = [
        f"project_intelligence.capabilities.{name.value} {reason}"
        for name, mode in capabilities.items()
        if mode is not RolloutMode.OFF and (reason := unconfigurable_reason(name)) is not None
    ]
    if rejected:
        raise ConfigError("; ".join(sorted(rejected)))
    depth_profile, depths = _depths(pi["depth"])
    analyzers_raw = pi["analyzers"]
    if not isinstance(analyzers_raw, list) or not all(
        isinstance(item, str) for item in analyzers_raw
    ):
        raise ConfigError("project_intelligence.analyzers must be a list of strings")
    unknown_analyzers = sorted(set(analyzers_raw) - set(KNOWN_ANALYZERS))
    if unknown_analyzers:
        raise ConfigError(f"unknown analyzer: {unknown_analyzers}")
    if len(set(analyzers_raw)) != len(analyzers_raw):
        raise ConfigError("project_intelligence.analyzers must not contain duplicates")

    analysis_raw = _mapping(pi["analysis"], "project_intelligence.analysis")
    context_raw = _mapping(pi["context"], "project_intelligence.context")
    _reject_unknown(analysis_raw, _ANALYSIS_KEYS, "project_intelligence.analysis")
    _reject_unknown(context_raw, _CONTEXT_KEYS, "project_intelligence.context")
    analysis = AnalysisBudgets(
        **{key: _positive_int(value, f"analysis.{key}") for key, value in analysis_raw.items()}
    )
    confidence = _number(context_raw["min_confidence"], "context.min_confidence")
    if not 0 <= confidence <= 1:
        raise ConfigError("context.min_confidence must be between 0 and 1")
    auto_inject_value = context_raw["auto_inject"]
    auto_inject = "false" if auto_inject_value is False else str(auto_inject_value)
    if auto_inject not in {"false", "planning", "generation", "both"}:
        raise ConfigError("context.auto_inject must be false, planning, generation, or both")
    context = ContextBudgets(
        max_tokens=_positive_int(context_raw["max_tokens"], "context.max_tokens"),
        max_items=_positive_int(context_raw["max_items"], "context.max_items"),
        min_confidence=confidence,
        include_runtime=_boolean(context_raw["include_runtime"], "context.include_runtime"),
        include_tests=_boolean(context_raw["include_tests"], "context.include_tests"),
        include_uncertainty=_boolean(
            context_raw["include_uncertainty"], "context.include_uncertainty"
        ),
        auto_inject=auto_inject,
    )

    endpoints_raw = _mapping(models["endpoints"], "models.endpoints")
    endpoints = {
        endpoint_id: _endpoint(endpoint_id, _mapping(value, f"models.endpoints.{endpoint_id}"))
        for endpoint_id, value in endpoints_raw.items()
    }
    roles_raw = _mapping(models["roles"], "models.roles")
    known_roles = {role.value for role in ModelRole}
    _reject_unknown(roles_raw, known_roles, "models.roles")
    roles: dict[ModelRole, tuple[str, ...]] = {}
    for role_name, endpoint_ids in roles_raw.items():
        if not isinstance(endpoint_ids, list) or not all(
            isinstance(endpoint_id, str) for endpoint_id in endpoint_ids
        ):
            raise ConfigError(f"models.roles.{role_name} must be a list of endpoint ids")
        missing = [endpoint_id for endpoint_id in endpoint_ids if endpoint_id not in endpoints]
        if missing:
            raise ConfigError(f"models.roles.{role_name} references unknown endpoints: {missing}")
        roles[ModelRole(role_name)] = tuple(endpoint_ids)

    model_config = ModelConfig(
        routing_mode=_enum(RoutingMode, models["routing_mode"], "models.routing_mode"),
        allow_remote_escalation=_boolean(
            models["allow_remote_escalation"], "models.allow_remote_escalation"
        ),
        allow_local_fallback=_boolean(
            models["allow_local_fallback"], "models.allow_local_fallback"
        ),
        remote_code_policy=_enum(
            RemoteCodePolicy, models["remote_code_policy"], "models.remote_code_policy"
        ),
        roles=roles,
        endpoints=endpoints,
    )
    return ResolvedConfig(
        project_intelligence=ProjectIntelligenceConfig(
            enabled=enabled,
            mode=mode,
            capabilities=capabilities,
            analyzers=tuple(analyzers_raw),
            analysis=analysis,
            context=context,
            depth_profile=depth_profile,
            depths=depths,
        ),
        models=model_config,
        applied_layers=applied,
    )


def _endpoint(endpoint_id: str, raw: Mapping[str, Any]) -> EndpointConfig:
    if not endpoint_id.strip():
        raise ConfigError("model endpoint id must not be empty")
    _reject_unknown(raw, _ENDPOINT_KEYS, f"models.endpoints.{endpoint_id}")
    required = {"provider_type", "locality"}
    missing = required - raw.keys()
    if missing:
        raise ConfigError(f"models.endpoints.{endpoint_id} missing: {sorted(missing)}")
    capability_raw = _mapping(raw.get("capabilities", {}), f"endpoint {endpoint_id} capabilities")
    _reject_unknown(
        capability_raw, _ENDPOINT_CAPABILITY_KEYS, f"models.endpoints.{endpoint_id}.capabilities"
    )
    capabilities = EndpointCapabilities(
        structured_output=_boolean(
            capability_raw.get("structured_output", False), "capabilities.structured_output"
        ),
        tools=_boolean(capability_raw.get("tools", False), "capabilities.tools"),
        reasoning_strength=_nonnegative_int(
            capability_raw.get("reasoning_strength", 0), "capabilities.reasoning_strength"
        ),
        code_strength=_nonnegative_int(
            capability_raw.get("code_strength", 0), "capabilities.code_strength"
        ),
    )
    context_window = _positive_int(raw.get("context_window", 8192), "context_window")
    max_output = _positive_int(raw.get("max_output", 2048), "max_output")
    if max_output >= context_window:
        # Output headroom comes out of the same window as the prompt. An endpoint that
        # reserves all of it can never answer, so this fails closed rather than routing
        # work to a model that will always truncate.
        raise ConfigError(
            f"endpoint {endpoint_id} reserves max_output={max_output} of a "
            f"context_window={context_window}; no room remains for a prompt"
        )
    return EndpointConfig(
        endpoint_id=endpoint_id,
        provider_type=_enum(ProviderType, raw["provider_type"], f"endpoint {endpoint_id} provider"),
        locality=_enum(EndpointLocality, raw["locality"], f"endpoint {endpoint_id} locality"),
        model_id=_optional_string(raw.get("model_id"), "model_id"),
        endpoint=_optional_string(raw.get("endpoint"), "endpoint"),
        context_window=context_window,
        max_output=max_output,
        timeout_seconds=_positive_number(raw.get("timeout_seconds", 30), "timeout_seconds"),
        retry=_nonnegative_int(raw.get("retry", 0), "retry"),
        cost_class=_nonnegative_int(raw.get("cost_class", 0), "cost_class"),
        latency_class=_nonnegative_int(raw.get("latency_class", 0), "latency_class"),
        privacy_class=str(raw.get("privacy_class", "standard")),
        capabilities=capabilities,
    )


def _validate_mapping(value: object, name: str) -> None:
    if not isinstance(value, Mapping):
        raise ConfigError(f"{name} must be an object")


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    _validate_mapping(value, name)
    return value  # type: ignore[return-value]


_DEPTH_KEYS = frozenset({"profile", "capabilities"})
_DEPTH_BOUND_KEYS = frozenset({"min", "max", "preferred"})


def _depths(raw: object) -> tuple[DepthProfile, dict[CapabilityName, CapabilityDepth]]:
    """Resolve the depth block. Depth is the cost axis and never touches RolloutMode."""

    block = _mapping(raw, "project_intelligence.depth")
    _reject_unknown(block, _DEPTH_KEYS, "project_intelligence.depth")
    profile = _enum(DepthProfile, block["profile"], "project_intelligence.depth.profile")
    per_capability = _mapping(block["capabilities"], "project_intelligence.depth.capabilities")
    _reject_unknown(
        per_capability,
        {item.value for item in ALL_CAPABILITIES},
        "project_intelligence.depth.capabilities",
    )

    depths: dict[CapabilityName, CapabilityDepth] = {}
    for name in ALL_CAPABILITIES:
        configured = per_capability.get(name.value)
        if configured is None:
            continue
        label = f"project_intelligence.depth.capabilities.{name.value}"
        # A capability that may not be enabled may not be tuned either; otherwise a
        # configuration could describe depth for something that never runs.
        reason = unconfigurable_reason(name)
        if reason is not None:
            raise ConfigError(f"{label} {reason}")
        bounds = _mapping(configured, label)
        _reject_unknown(bounds, _DEPTH_BOUND_KEYS, label)
        minimum = _enum(Depth, bounds.get("min", Depth.D0.value), f"{label}.min")
        maximum = _enum(Depth, bounds.get("max", Depth.D4.value), f"{label}.max")
        if depth_rank(minimum) > depth_rank(maximum):
            raise ConfigError(f"{label}.min must not exceed {label}.max")
        preferred_raw = bounds.get("preferred")
        preferred = (
            None
            if preferred_raw is None or preferred_raw == "auto"
            else _enum(Depth, preferred_raw, f"{label}.preferred")
        )
        if preferred is not None and not (
            depth_rank(minimum) <= depth_rank(preferred) <= depth_rank(maximum)
        ):
            raise ConfigError(f"{label}.preferred must lie within min..max")
        depths[name] = CapabilityDepth(minimum, maximum, preferred)
    return profile, depths


def _reject_unknown(raw: Mapping[str, Any], allowed: set[str] | frozenset[str], name: str) -> None:
    unknown = set(raw) - set(allowed)
    if unknown:
        raise ConfigError(f"unknown keys in {name}: {sorted(unknown)}")


def _boolean(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ConfigError(f"{name} must be a boolean")
    return value


def _positive_int(value: object, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise ConfigError(f"{name} must be a positive integer")
    return value


def _nonnegative_int(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ConfigError(f"{name} must be a non-negative integer")
    return value


def _number(value: object, name: str) -> float:
    if type(value) not in {int, float}:
        raise ConfigError(f"{name} must be a number")
    return float(cast("int | float", value))


def _positive_number(value: object, name: str) -> float:
    result = _number(value, name)
    if result <= 0:
        raise ConfigError(f"{name} must be positive")
    return result


def _optional_string(value: object, name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{name} must be a non-empty string or null")
    return value


def _enum(enum_type: type[EnumT], value: object, name: str) -> EnumT:
    if not isinstance(value, str):
        raise ConfigError(f"invalid {name}: {value!r}")
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"invalid {name}: {value!r}") from exc
