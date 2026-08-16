"""Depth is a second, independent axis: every capability has one, and it is not the mode.

Stage E2. Invariant 6 requires rollout mode (authority) and depth (cost) to be
configured separately and never encoded in one another. These tests fail if a future
change couples them, or if a capability is added without a resolvable depth.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from extendcodeagent.core.config import ConfigLayer, ConfigResolver
from extendcodeagent.core.config.schema import (
    ALL_CAPABILITIES,
    ALL_DEPTHS,
    CONFIGURABLE_CAPABILITIES,
    DEFAULT_CAPABILITY_DEPTH,
    DEFAULT_DEPTH_PROFILE,
    CapabilityDepth,
    CapabilityName,
    ConfigError,
    Depth,
    DepthProfile,
    RolloutMode,
    depth_min_inferred_confidence,
    depth_rank,
    resolve_depth,
)
from extendcodeagent.core.policy import CapabilityPolicy

PACKAGE_ROOT = Path(__file__).parents[2] / "src" / "extendcodeagent"
SCHEMA = PACKAGE_ROOT / "core" / "config" / "schema.py"
POLICY = PACKAGE_ROOT / "core" / "policy.py"


def _policy(**layer: object) -> CapabilityPolicy:
    resolved = ConfigResolver().resolve(ConfigLayer("test", {"project_intelligence": layer}))
    return CapabilityPolicy.from_config(resolved.project_intelligence)


def test_every_capability_resolves_to_a_depth() -> None:
    policy = _policy()
    for name in ALL_CAPABILITIES:
        assert policy.depth(name) in ALL_DEPTHS


def test_depth_is_independent_of_rollout_mode() -> None:
    """The same depth configuration must resolve identically at every rollout mode."""

    depths_by_mode = {}
    for mode in ("off", "shadow", "advisory", "active"):
        policy = _policy(
            enabled=mode != "off",
            mode=mode,
            capabilities={name.value: mode for name in CONFIGURABLE_CAPABILITIES},
            depth={"profile": "quality", "capabilities": {}},
        )
        depths_by_mode[mode] = {name: policy.depth(name) for name in ALL_CAPABILITIES}

    reference = depths_by_mode["active"]
    for mode, depths in depths_by_mode.items():
        assert depths == reference, f"depth changed with rollout mode {mode}"
        assert all(depth is Depth.D3 for depth in depths.values())


def test_rollout_mode_is_independent_of_depth() -> None:
    """Changing the depth profile must not change any capability's authority."""

    modes_by_profile = {}
    for profile in DepthProfile:
        policy = _policy(
            enabled=True,
            mode="advisory",
            capabilities={name.value: "advisory" for name in CONFIGURABLE_CAPABILITIES},
            depth={"profile": profile.value, "capabilities": {}},
        )
        modes_by_profile[profile] = {name: policy.mode(name) for name in ALL_CAPABILITIES}

    reference = modes_by_profile[DepthProfile.BALANCED]
    for profile, modes in modes_by_profile.items():
        assert modes == reference, f"rollout mode changed with depth profile {profile.value}"


def test_policy_depth_resolution_never_reads_the_mode_table() -> None:
    """Structural guard: the depth resolver must not consult modes, or vice versa."""

    tree = ast.parse(POLICY.read_text(encoding="utf-8"), filename=str(POLICY))
    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)  # noqa: B006 - read-only inspection
    }
    for name in ("depth", "min_inferred_confidence"):
        source = ast.dump(functions[name])
        assert "modes" not in source, f"{name} must not read the rollout-mode table"
    for name in ("mode", "is_enabled", "allows_explicit_use", "allows_automatic_effect"):
        source = ast.dump(functions[name])
        assert "depths" not in source, f"{name} must not read the depth table"


def test_depth_ranks_are_a_total_order() -> None:
    ranks = [depth_rank(depth) for depth in ALL_DEPTHS]
    assert ranks == sorted(ranks)
    assert len(set(ranks)) == len(ALL_DEPTHS)


def test_inferred_confidence_floor_is_monotone_and_falls_with_depth() -> None:
    floors = [depth_min_inferred_confidence(depth) for depth in ALL_DEPTHS]
    assert floors == sorted(floors, reverse=True), "deeper analysis must not demand more certainty"
    assert all(0.0 <= value <= 1.0 for value in floors)


def test_d1_excludes_may_call_and_d3_admits_it() -> None:
    """The control point the E1 `call_graph` folding decision depends on.

    `may_call` is emitted at 0.35. It must survive a deep query and be dropped by a
    shallow one, otherwise folding `call_graph` into `semantic` left it unbounded.
    """

    assert depth_min_inferred_confidence(Depth.D1) > 0.35
    assert depth_min_inferred_confidence(Depth.D3) <= 0.35


def test_default_depth_admits_every_confidence_the_analyzers_emit() -> None:
    """No behavior change at the shipped default.

    Analyzers emit 1.0, 0.95, 0.9, 0.5 and 0.35 today. If the default floor ever rises
    above the lowest of those, the default configuration silently starts dropping facts.
    """

    emitted = (1.0, 0.95, 0.9, 0.5, 0.35)
    default = depth_min_inferred_confidence(
        resolve_depth(DEFAULT_DEPTH_PROFILE, DEFAULT_CAPABILITY_DEPTH)
    )
    assert default <= min(emitted)


def test_preferred_depth_is_clamped_into_bounds() -> None:
    bounds = CapabilityDepth(minimum=Depth.D1, maximum=Depth.D2, preferred=Depth.D4)
    assert resolve_depth(DepthProfile.BALANCED, bounds) is Depth.D2
    bounds = CapabilityDepth(minimum=Depth.D3, maximum=Depth.D4, preferred=Depth.D0)
    assert resolve_depth(DepthProfile.ECO, bounds) is Depth.D3


def test_profile_depth_is_clamped_when_no_preference_is_given() -> None:
    bounds = CapabilityDepth(minimum=Depth.D0, maximum=Depth.D1)
    assert resolve_depth(DepthProfile.MAX, bounds) is Depth.D1


def test_auto_is_declared_but_not_adaptive_yet() -> None:
    """`auto` must resolve deterministically until stage C3 makes it task-aware."""

    first = _policy(depth={"profile": "auto", "capabilities": {}})
    second = _policy(depth={"profile": "auto", "capabilities": {}})
    assert first.depths == second.depths


def test_per_capability_depth_overrides_the_profile() -> None:
    policy = _policy(
        depth={
            "profile": "eco",
            "capabilities": {"impact": {"min": "D2", "max": "D4", "preferred": "D3"}},
        }
    )
    assert policy.depth(CapabilityName.IMPACT) is Depth.D3
    assert policy.depth(CapabilityName.CONTEXT) is Depth.D1


def test_unconfigurable_capabilities_reject_depth_configuration() -> None:
    with pytest.raises(ConfigError, match="ui_graph is declared but not implemented"):
        _policy(depth={"profile": "balanced", "capabilities": {"ui_graph": {"min": "D1"}}})
    with pytest.raises(ConfigError, match="call_graph is governed by 'semantic'"):
        _policy(depth={"profile": "balanced", "capabilities": {"call_graph": {"min": "D1"}}})


def test_invalid_depth_bounds_fail_closed() -> None:
    with pytest.raises(ConfigError, match="must not exceed"):
        _policy(
            depth={"profile": "balanced", "capabilities": {"impact": {"min": "D3", "max": "D1"}}}
        )
    with pytest.raises(ConfigError, match="must lie within"):
        _policy(
            depth={
                "profile": "balanced",
                "capabilities": {"impact": {"min": "D1", "max": "D2", "preferred": "D4"}},
            }
        )
    with pytest.raises(ConfigError, match="invalid"):
        _policy(depth={"profile": "deep", "capabilities": {}})
    with pytest.raises(ConfigError, match="unknown keys"):
        _policy(depth={"profile": "balanced", "capabilities": {"impact": {"floor": "D1"}}})


def test_folded_capability_still_reports_its_governing_depth() -> None:
    policy = _policy(
        depth={
            "profile": "eco",
            "capabilities": {"semantic": {"min": "D0", "max": "D4", "preferred": "D3"}},
        }
    )
    assert policy.depth(CapabilityName.SEMANTIC) is Depth.D3
    assert policy.depth(CapabilityName.CALL_GRAPH) is Depth.D3


def test_depth_survives_a_globally_disabled_deployment() -> None:
    """Depth is a cost declaration, not an authority; `off` must not erase it."""

    policy = _policy(enabled=False, mode="off", depth={"profile": "quality", "capabilities": {}})
    assert policy.mode(CapabilityName.IMPACT) is RolloutMode.OFF
    assert policy.depth(CapabilityName.IMPACT) is Depth.D3


def test_schema_declares_a_floor_for_every_depth() -> None:
    source = SCHEMA.read_text(encoding="utf-8")
    for depth in ALL_DEPTHS:
        assert f"Depth.{depth.value}:" in source
    assert len(ALL_DEPTHS) == 5
