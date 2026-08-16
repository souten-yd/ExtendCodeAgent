"""Every declared capability must be gated by a real service or declared unimplemented.

This is the E1 conformance boundary. Adding a member to ``CapabilityName`` without
either wiring a ``CapabilityPolicy`` gate or declaring it unimplemented fails here,
because an ungated capability cannot be ablated and therefore silently invalidates
every later per-capability evaluation claim.
"""

from __future__ import annotations

import ast
from pathlib import Path

from extendcodeagent.core.config.schema import (
    ALL_CAPABILITIES,
    CAPABILITY_FOLDED_INTO,
    CONFIGURABLE_CAPABILITIES,
    NOT_IMPLEMENTED_CAPABILITIES,
    CapabilityImplementation,
    CapabilityName,
    capability_implementation,
    governing_capability,
)

PACKAGE_ROOT = Path(__file__).parents[2] / "src" / "extendcodeagent"

#: Modules that read ``CapabilityName`` for declaration/reporting purposes rather
#: than to gate a service. Mentions here do not count as a gate.
NON_GATING_MODULES = (PACKAGE_ROOT / "core" / "config" / "schema.py",)

#: ``CapabilityPolicy`` gate predicates, plus the application-side wrappers that
#: delegate to them (``_require_explicit`` -> ``policy.require_explicit_use``).
GATE_METHODS = frozenset(
    {
        "mode",
        "is_enabled",
        "computes_automatically",
        "allows_explicit_use",
        "allows_automatic_effect",
        "require_explicit_use",
        "_require_explicit",
        "_explicit_snapshot",
    }
)


def _is_gate_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in GATE_METHODS
    )


def _gated_capabilities() -> set[CapabilityName]:
    """Collect capabilities passed to a CapabilityPolicy gate method in real source."""

    gated: set[CapabilityName] = set()
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        if path in NON_GATING_MODULES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            # Direct form: policy.allows_explicit_use(CapabilityName.X)
            if _is_gate_call(node):
                assert isinstance(node, ast.Call)
                for argument in node.args:
                    name = _capability_from(argument)
                    if name is not None:
                        gated.add(name)
            # Comprehension form: all(policy.f(item) for item in (CapabilityName.X, ...))
            if isinstance(node, ast.GeneratorExp | ast.ListComp | ast.SetComp) and any(
                _is_gate_call(inner) for inner in ast.walk(node.elt)
            ):
                for generator in node.generators:
                    for inner in ast.walk(generator.iter):
                        name = _capability_from(inner)
                        if name is not None:
                            gated.add(name)
    return gated


def _capability_from(node: ast.AST) -> CapabilityName | None:
    """Resolve a literal ``CapabilityName.X`` attribute reference."""

    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "CapabilityName"
    ):
        return CapabilityName[node.attr]
    return None


def test_every_capability_is_gated_or_declared_unimplemented() -> None:
    gated = _gated_capabilities()
    unclassified = [
        name.value
        for name in ALL_CAPABILITIES
        if name not in NOT_IMPLEMENTED_CAPABILITIES
        and governing_capability(name) not in gated
        and name not in gated
    ]
    assert unclassified == [], (
        "capabilities are neither policy-gated nor declared not_implemented: "
        f"{unclassified}. Gate them through CapabilityPolicy, fold them into a gated "
        "capability via CAPABILITY_FOLDED_INTO, or add them to NOT_IMPLEMENTED_CAPABILITIES."
    )


def test_unimplemented_capabilities_are_never_gated() -> None:
    """A capability declared unimplemented must not have a live gate anywhere."""

    gated = _gated_capabilities()
    contradictions = sorted(name.value for name in NOT_IMPLEMENTED_CAPABILITIES if name in gated)
    assert contradictions == [], (
        f"declared not_implemented but gated in source: {contradictions}. "
        "Remove them from NOT_IMPLEMENTED_CAPABILITIES."
    )


def test_capability_classification_partitions_all_capabilities() -> None:
    implemented = {name for name in ALL_CAPABILITIES if name not in NOT_IMPLEMENTED_CAPABILITIES}
    assert implemented | NOT_IMPLEMENTED_CAPABILITIES == set(ALL_CAPABILITIES)
    assert implemented & NOT_IMPLEMENTED_CAPABILITIES == set()
    for name in ALL_CAPABILITIES:
        expected = (
            CapabilityImplementation.NOT_IMPLEMENTED
            if name in NOT_IMPLEMENTED_CAPABILITIES
            else CapabilityImplementation.IMPLEMENTED
        )
        assert capability_implementation(name) is expected


def test_folded_capabilities_are_implemented_and_point_at_a_gated_host() -> None:
    gated = _gated_capabilities()
    for folded, host in CAPABILITY_FOLDED_INTO.items():
        assert folded not in NOT_IMPLEMENTED_CAPABILITIES
        assert host not in NOT_IMPLEMENTED_CAPABILITIES
        assert host not in CAPABILITY_FOLDED_INTO, "folding must not chain"
        assert host in gated, f"{folded.value} is folded into ungated {host.value}"


def test_configurable_capabilities_exclude_unimplemented_and_folded() -> None:
    configurable = set(CONFIGURABLE_CAPABILITIES)
    assert configurable & NOT_IMPLEMENTED_CAPABILITIES == set()
    assert configurable & set(CAPABILITY_FOLDED_INTO) == set()
    assert configurable | NOT_IMPLEMENTED_CAPABILITIES | set(CAPABILITY_FOLDED_INTO) == set(
        ALL_CAPABILITIES
    )


def test_inventory_matches_the_master_plan_counts() -> None:
    """Guard the numbers the master plan section 6 and the E1 stage are written against."""

    assert len(ALL_CAPABILITIES) == 21
    assert len(NOT_IMPLEMENTED_CAPABILITIES) == 7
    assert len(CAPABILITY_FOLDED_INTO) == 1
    assert len(CONFIGURABLE_CAPABILITIES) == 13
