"""Immutable resolved configuration used by composition and policies."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType


class ConfigError(ValueError):
    """Raised for invalid or internally inconsistent configuration."""


class RolloutMode(StrEnum):
    OFF = "off"
    SHADOW = "shadow"
    ADVISORY = "advisory"
    ACTIVE = "active"


class CapabilityName(StrEnum):
    GRAPH = "graph"
    TWIN = "twin"
    SEMANTIC = "semantic"
    CALL_GRAPH = "call_graph"
    CFG = "cfg"
    DATA_FLOW = "data_flow"
    STATE_EVENT = "state_event"
    SIDE_EFFECTS = "side_effects"
    API_SCHEMA_DB = "api_schema_db"
    UI_GRAPH = "ui_graph"
    RUNTIME = "runtime"
    IMPACT = "impact"
    TEST_SELECTION = "test_selection"
    TEST_OBSOLESCENCE = "test_obsolescence"
    CONTEXT = "context"
    BLUEPRINT = "blueprint"
    STRATEGY = "strategy"
    CONVERGENCE = "convergence"
    RESEARCH = "research"
    TRACEABILITY = "traceability"
    MEMORY = "memory"


ALL_CAPABILITIES = tuple(CapabilityName)
KNOWN_ANALYZERS = ("python", "javascript_typescript")


class CapabilityImplementation(StrEnum):
    """Whether a declared capability has a real implementation behind it."""

    IMPLEMENTED = "implemented"
    NOT_IMPLEMENTED = "not_implemented"


#: Capabilities that are declared but have no implementation. Configuring one to
#: anything other than ``off`` is rejected rather than silently ignored, so an
#: evaluation arm can never believe it enabled a capability that does not run.
NOT_IMPLEMENTED_CAPABILITIES: frozenset[CapabilityName] = frozenset(
    {
        CapabilityName.CFG,
        CapabilityName.DATA_FLOW,
        CapabilityName.STATE_EVENT,
        CapabilityName.SIDE_EFFECTS,
        CapabilityName.API_SCHEMA_DB,
        CapabilityName.UI_GRAPH,
        CapabilityName.MEMORY,
    }
)

#: Capabilities that are implemented but whose authority is owned by another
#: capability, because they cannot be switched independently without making the
#: artifact they contribute to depend on the rollout mode. The key is governed by
#: the value's rollout mode and is not separately configurable.
CAPABILITY_FOLDED_INTO: Mapping[CapabilityName, CapabilityName] = MappingProxyType(
    {CapabilityName.CALL_GRAPH: CapabilityName.SEMANTIC}
)


def capability_implementation(capability: CapabilityName) -> CapabilityImplementation:
    if capability in NOT_IMPLEMENTED_CAPABILITIES:
        return CapabilityImplementation.NOT_IMPLEMENTED
    return CapabilityImplementation.IMPLEMENTED


def governing_capability(capability: CapabilityName) -> CapabilityName:
    """Return the capability whose rollout mode decides this one."""

    return CAPABILITY_FOLDED_INTO.get(capability, capability)


def unconfigurable_reason(capability: CapabilityName) -> str | None:
    """Explain why a capability may only be left at ``off``, or ``None`` if it is free."""

    if capability in NOT_IMPLEMENTED_CAPABILITIES:
        return "is declared but not implemented"
    folded = CAPABILITY_FOLDED_INTO.get(capability)
    if folded is not None:
        return f"is governed by '{folded.value}'; configure that capability instead"
    return None


#: Capabilities a user may set to a non-``off`` rollout mode.
CONFIGURABLE_CAPABILITIES = tuple(
    name for name in ALL_CAPABILITIES if unconfigurable_reason(name) is None
)


class ModelRole(StrEnum):
    FAST_CLASSIFIER = "fast_classifier"
    SMALL_STRUCTURED = "small_structured"
    SUMMARIZER = "summarizer"
    CODE_REASONER = "code_reasoner"
    STRATEGY_REASONER = "strategy_reasoner"
    RESEARCH_SYNTHESIZER = "research_synthesizer"
    VERIFICATION_REVIEWER = "verification_reviewer"
    FALLBACK = "fallback"


class RoutingMode(StrEnum):
    MANUAL = "manual"
    LOCAL_FIRST = "local_first"
    FRONTIER_FIRST = "frontier_first"
    COST_OPTIMIZED = "cost_optimized"
    LATENCY_OPTIMIZED = "latency_optimized"
    QUALITY_OPTIMIZED = "quality_optimized"
    ADAPTIVE = "adaptive"
    HOST_ONLY = "host_only"
    LOCAL_ONLY = "local_only"


class ProviderType(StrEnum):
    HOST_MODEL = "host_model"
    LOCAL_OPENAI_API = "local_openai_api"
    LOCAL_CUSTOM = "local_custom"
    REMOTE_API = "remote_api"
    MCP_MODEL_SERVICE = "mcp_model_service"
    FAKE = "fake"


class EndpointLocality(StrEnum):
    LOCAL = "local"
    HOST = "host"
    REMOTE = "remote"


class RemoteCodePolicy(StrEnum):
    DENY = "deny"
    METADATA_ONLY = "metadata_only"
    SELECTED_CONTEXT = "selected_context"
    ALLOW = "allow"


@dataclass(frozen=True, slots=True)
class AnalysisBudgets:
    max_files: int
    max_file_bytes: int
    max_graph_nodes: int
    max_graph_edges: int
    max_depth: int
    incremental_batch_ms: int
    background_workers: int
    memory_budget_mb: int


@dataclass(frozen=True, slots=True)
class ContextBudgets:
    max_tokens: int
    max_items: int
    min_confidence: float
    include_runtime: bool
    include_tests: bool
    include_uncertainty: bool
    auto_inject: str


@dataclass(frozen=True, slots=True)
class EndpointCapabilities:
    structured_output: bool = False
    tools: bool = False
    reasoning_strength: int = 0
    code_strength: int = 0


@dataclass(frozen=True, slots=True)
class EndpointConfig:
    endpoint_id: str
    provider_type: ProviderType
    locality: EndpointLocality
    model_id: str | None = None
    endpoint: str | None = None
    context_window: int = 8192
    max_output: int = 2048
    timeout_seconds: float = 30.0
    retry: int = 0
    cost_class: int = 0
    latency_class: int = 0
    privacy_class: str = "standard"
    capabilities: EndpointCapabilities = field(default_factory=EndpointCapabilities)


@dataclass(frozen=True, slots=True)
class ModelConfig:
    routing_mode: RoutingMode
    allow_remote_escalation: bool
    allow_local_fallback: bool
    remote_code_policy: RemoteCodePolicy
    roles: Mapping[ModelRole, tuple[str, ...]]
    endpoints: Mapping[str, EndpointConfig]

    def __post_init__(self) -> None:
        object.__setattr__(self, "roles", MappingProxyType(dict(self.roles)))
        object.__setattr__(self, "endpoints", MappingProxyType(dict(self.endpoints)))


@dataclass(frozen=True, slots=True)
class ProjectIntelligenceConfig:
    enabled: bool
    mode: RolloutMode
    capabilities: Mapping[CapabilityName, RolloutMode]
    analyzers: tuple[str, ...]
    analysis: AnalysisBudgets
    context: ContextBudgets

    def __post_init__(self) -> None:
        object.__setattr__(self, "capabilities", MappingProxyType(dict(self.capabilities)))


@dataclass(frozen=True, slots=True)
class ResolvedConfig:
    project_intelligence: ProjectIntelligenceConfig
    models: ModelConfig
    applied_layers: tuple[str, ...]
