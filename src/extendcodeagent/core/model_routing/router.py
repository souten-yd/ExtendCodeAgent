"""Deterministic endpoint selection with capability, privacy, and fallback gates."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from ..config.schema import (
    EndpointConfig,
    EndpointLocality,
    ModelConfig,
    RemoteCodePolicy,
    RoutingMode,
)
from .contracts import (
    ModelAdapter,
    ModelRequest,
    ModelUnavailable,
    RouteDecision,
    RoutedResponse,
)


@dataclass(frozen=True, slots=True)
class PolicyModelRouter:
    config: ModelConfig
    adapters: Mapping[str, ModelAdapter]

    def __post_init__(self) -> None:
        object.__setattr__(self, "adapters", MappingProxyType(dict(self.adapters)))

    def route(self, request: ModelRequest) -> RouteDecision:
        ordered = self._ordered_candidates(request)
        rejected: dict[str, tuple[str, ...]] = {}
        eligible: list[str] = []
        for endpoint_id in ordered:
            endpoint = self.config.endpoints[endpoint_id]
            failures = tuple(self._rejection_reasons(request, endpoint))
            if failures:
                rejected[endpoint_id] = failures
            else:
                eligible.append(endpoint_id)
        selected = eligible[0] if eligible else None
        reasons = (
            (f"initial_selection:{selected}", f"routing_mode:{self.config.routing_mode.value}")
            if selected
            else ("no_eligible_endpoint", f"routing_mode:{self.config.routing_mode.value}")
        )
        return RouteDecision(
            selected_endpoint=selected,
            candidates=tuple(eligible),
            rejected=MappingProxyType(rejected),
            reasons=reasons,
        )

    def execute(self, request: ModelRequest) -> RoutedResponse:
        decision = self.route(request)
        attempts: list[str] = []
        if not decision.candidates:
            raise ModelUnavailable("no eligible model endpoint")
        for index, endpoint_id in enumerate(decision.candidates):
            if index > 0 and not self._fallback_allowed(
                self.config.endpoints[decision.candidates[index - 1]],
                self.config.endpoints[endpoint_id],
            ):
                break
            response = None
            adapter = self.adapters.get(endpoint_id)
            for _ in range(self.config.endpoints[endpoint_id].retry + 1):
                attempts.append(endpoint_id)
                if adapter is None:
                    break
                try:
                    response = adapter.complete(request)
                except ModelUnavailable:
                    continue
                break
            if response is None:
                continue
            final_decision = RouteDecision(
                selected_endpoint=endpoint_id,
                candidates=decision.candidates,
                rejected=decision.rejected,
                reasons=decision.reasons + (f"completed:{endpoint_id}",),
            )
            return RoutedResponse(
                response=response, decision=final_decision, attempts=tuple(attempts)
            )
        raise ModelUnavailable(f"model endpoints unavailable after attempts: {attempts}")

    def _ordered_candidates(self, request: ModelRequest) -> list[str]:
        configured = list(self.config.roles.get(request.role, ()))
        if self.config.routing_mode is RoutingMode.MANUAL:
            if request.requested_endpoint is None:
                return []
            return [request.requested_endpoint] if request.requested_endpoint in configured else []
        endpoint = self.config.endpoints.__getitem__
        if self.config.routing_mode in {RoutingMode.LOCAL_FIRST, RoutingMode.ADAPTIVE}:
            return sorted(configured, key=lambda item: _locality_rank(endpoint(item).locality))
        if self.config.routing_mode is RoutingMode.FRONTIER_FIRST:
            return sorted(configured, key=lambda item: -_locality_rank(endpoint(item).locality))
        if self.config.routing_mode is RoutingMode.COST_OPTIMIZED:
            return sorted(configured, key=lambda item: endpoint(item).cost_class)
        if self.config.routing_mode is RoutingMode.LATENCY_OPTIMIZED:
            return sorted(configured, key=lambda item: endpoint(item).latency_class)
        if self.config.routing_mode is RoutingMode.QUALITY_OPTIMIZED:
            return sorted(
                configured,
                key=lambda item: (
                    -endpoint(item).capabilities.reasoning_strength,
                    -endpoint(item).capabilities.code_strength,
                ),
            )
        return configured

    def _rejection_reasons(self, request: ModelRequest, endpoint: EndpointConfig) -> list[str]:
        reasons: list[str] = []
        mode = self.config.routing_mode
        if mode is RoutingMode.LOCAL_ONLY and endpoint.locality is not EndpointLocality.LOCAL:
            reasons.append("local_only")
        if mode is RoutingMode.HOST_ONLY and endpoint.locality is not EndpointLocality.HOST:
            reasons.append("host_only")
        if endpoint.locality is EndpointLocality.REMOTE:
            if not self.config.allow_remote_escalation:
                reasons.append("remote_escalation_disabled")
            if request.contains_source_code and not _remote_source_allowed(self.config, request):
                reasons.append("remote_code_policy")
        if request.context_tokens > endpoint.context_window:
            reasons.append("context_exceeds_model")
        if request.requires_structured_output and not endpoint.capabilities.structured_output:
            reasons.append("structured_output_unsupported")
        if request.requires_tools and not endpoint.capabilities.tools:
            reasons.append("tools_unsupported")
        if endpoint.capabilities.reasoning_strength < request.minimum_reasoning_strength:
            reasons.append("reasoning_strength_insufficient")
        return reasons

    def _fallback_allowed(self, previous: EndpointConfig, following: EndpointConfig) -> bool:
        if following.locality is EndpointLocality.REMOTE:
            return self.config.allow_remote_escalation
        if (
            following.locality is EndpointLocality.LOCAL
            and previous.locality is not EndpointLocality.LOCAL
        ):
            return self.config.allow_local_fallback
        return True


def _remote_source_allowed(config: ModelConfig, request: ModelRequest) -> bool:
    policy = config.remote_code_policy
    if policy in {RemoteCodePolicy.DENY, RemoteCodePolicy.METADATA_ONLY}:
        return False
    if policy is RemoteCodePolicy.SELECTED_CONTEXT:
        return request.remote_context_approved
    return True


def _locality_rank(locality: EndpointLocality) -> int:
    return {
        EndpointLocality.LOCAL: 0,
        EndpointLocality.HOST: 1,
        EndpointLocality.REMOTE: 2,
    }[locality]
