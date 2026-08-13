from __future__ import annotations

from extendcodeagent.context import ContextProfile, ContextRequest, build_context
from extendcodeagent.core.contracts import (
    CanonicalRef,
    Confidence,
    ProjectRef,
    Provenance,
    SourceRevision,
)
from extendcodeagent.graph import FactStatus, GraphNode, GraphSnapshot

PROJECT = ProjectRef("project", "workspace", "file:///repo")
REVISION = SourceRevision("rev-1")
PROVENANCE = Provenance("source", "python-ast", "1", REVISION)


def _snapshot(size: int = 30) -> GraphSnapshot:
    nodes = tuple(
        GraphNode(
            f"node-{index}",
            CanonicalRef(f"py://module#function_{index}"),
            "function",
            "module.py",
            PROVENANCE,
            Confidence(1.0),
            FactStatus.DECLARED,
            REVISION,
            {"name": f"function_{index}"},
        )
        for index in range(size)
    )
    return GraphSnapshot(PROJECT, None, nodes)


def test_context_is_bounded_and_every_item_is_explainable_and_revisioned() -> None:
    package = build_context(
        _snapshot(),
        ContextRequest(
            objective="change function zero",
            target_refs=(CanonicalRef("py://module#function_0"),),
            token_budget=80,
            max_items=5,
        ),
    )
    assert package.used_tokens <= package.token_budget == 80
    assert len(package.items) <= 5
    assert package.truncated is True
    assert package.items[0].canonical_ref.value == "py://module#function_0"
    assert all(item.why_included and item.revision == REVISION for item in package.items)
    assert all(item.provenance == PROVENANCE and item.token_estimate > 0 for item in package.items)


def test_weak_profile_is_materially_smaller_than_standard() -> None:
    snapshot = _snapshot()
    standard = build_context(
        snapshot,
        ContextRequest("inspect", token_budget=2_000, max_items=30),
    )
    weak = build_context(
        snapshot,
        ContextRequest("inspect", token_budget=2_000, max_items=30, profile=ContextProfile.WEAK),
    )
    assert weak.used_tokens < standard.used_tokens
    assert len(weak.items) <= 8 < len(standard.items)
