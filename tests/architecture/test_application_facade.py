"""The application layer is a facade, and that has to be checked rather than asserted in prose.

`ProjectIntelligenceApplication` imports nearly every domain, so it is the path of least
resistance for any new algorithm. Once a heuristic lands there it is invisible to the domain's
own tests, cannot be reused by another consumer and cannot be ablated with its capability.
These tests pin the boundary so the C2 working-set work has to grow the domains instead.
"""

from __future__ import annotations

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[2] / "src" / "extendcodeagent"
APPLICATION = PACKAGE_ROOT / "service" / "application.py"

# Ratchet: lower this when the facade shrinks, never raise it to admit new domain logic.
APPLICATION_LINE_BUDGET = 1_600

# Domain behaviour that previously lived in the facade and now has a domain owner.
RELOCATED_HELPERS = {
    "_focused_test_paths": "extendcodeagent.testing.selection",
    "_objective_test_paths": "extendcodeagent.testing.selection",
    "_structural_test_paths": "extendcodeagent.testing.selection",
    "_intent_architecture_test_paths": "extendcodeagent.testing.selection",
    "_direct_use_count": "extendcodeagent.testing.selection",
    "_test_obligation": "extendcodeagent.testing.selection",
    "_context_json": "extendcodeagent.context.serialization",
    "_weak_local_evidence_json": "extendcodeagent.context.serialization",
}


def _application_tree() -> ast.Module:
    return ast.parse(APPLICATION.read_text(encoding="utf-8"), filename=str(APPLICATION))


def test_application_stays_within_its_facade_line_budget() -> None:
    lines = len(APPLICATION.read_text(encoding="utf-8").splitlines())

    assert lines <= APPLICATION_LINE_BUDGET, (
        f"service/application.py is {lines} lines against a budget of "
        f"{APPLICATION_LINE_BUDGET}. Move the new behaviour into its domain package "
        "instead of raising the budget."
    )


def test_relocated_domain_helpers_are_not_redefined_in_the_facade() -> None:
    defined = {
        node.name
        for node in ast.walk(_application_tree())
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    reintroduced = sorted(defined & set(RELOCATED_HELPERS))

    assert reintroduced == [], (
        "these helpers have a domain owner and must not be reintroduced in the facade: "
        + ", ".join(f"{name} -> {RELOCATED_HELPERS[name]}" for name in reintroduced)
    )


def test_module_level_facade_functions_do_not_traverse_the_graph() -> None:
    """The facade serializes; the domain computes.

    A line budget is a coarse backstop that can be satisfied by shuffling code. Graph
    traversal is the precise signal: a module-level function that walks `snapshot.nodes` or
    `snapshot.edges` is a domain heuristic, whatever it is named or how short it is.
    """

    source = APPLICATION.read_text(encoding="utf-8")
    offenders: list[str] = []
    for node in _application_tree().body:
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        body = ast.get_source_segment(source, node) or ""
        traversed = sorted({name for name in ("snapshot.nodes", "snapshot.edges") if name in body})
        if traversed:
            offenders.append(f"{node.name} (line {node.lineno}): {', '.join(traversed)}")

    assert offenders == [], (
        "these module-level facade functions traverse the Graph and belong in a domain "
        "package: " + "; ".join(offenders)
    )


def test_context_payload_and_its_cost_estimate_share_one_owner() -> None:
    """A budget enforced against a different shape than the one delivered is not a budget."""

    serialization = PACKAGE_ROOT / "context" / "serialization.py"
    source = serialization.read_text(encoding="utf-8")

    assert "def estimate_payload_tokens" in source
    assert "def context_item_json" in source
