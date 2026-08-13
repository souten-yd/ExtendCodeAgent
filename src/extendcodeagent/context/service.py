"""Deterministic bounded context construction from a Graph snapshot."""

from __future__ import annotations

from math import ceil

from extendcodeagent.graph import GraphNode, GraphSnapshot

from .contracts import ContextItem, ContextPackage, ContextProfile, ContextRequest

_WEAK_MAX_TOKENS = 512
_WEAK_MAX_ITEMS = 8


def build_context(snapshot: GraphSnapshot, request: ContextRequest) -> ContextPackage:
    token_budget = (
        min(request.token_budget, _WEAK_MAX_TOKENS)
        if request.profile is ContextProfile.WEAK
        else request.token_budget
    )
    max_items = (
        min(request.max_items, _WEAK_MAX_ITEMS)
        if request.profile is ContextProfile.WEAK
        else request.max_items
    )
    targets = set(request.target_refs)
    candidates = [
        node for node in snapshot.nodes if node.confidence.value >= request.min_confidence
    ]
    candidates.sort(
        key=lambda node: (
            0 if node.canonical_ref in targets else 1,
            -node.confidence.value,
            node.canonical_ref.value,
        )
    )
    items: list[ContextItem] = []
    used_tokens = 0
    for node in candidates:
        if len(items) >= max_items:
            break
        item = _context_item(node, is_target=node.canonical_ref in targets)
        if used_tokens + item.token_estimate > token_budget:
            continue
        items.append(item)
        used_tokens += item.token_estimate
    return ContextPackage(
        request.objective,
        tuple(items),
        used_tokens,
        token_budget,
        len(items) < len(candidates),
        len(candidates) - len(items),
    )


def _context_item(node: GraphNode, *, is_target: bool) -> ContextItem:
    why = "target_ref" if is_target else "high-confidence project fact"
    summary = str(node.properties.get("name") or node.canonical_ref.value)
    token_estimate = max(
        1,
        ceil((len(node.canonical_ref.value) + len(summary) + len(why)) / 4),
    )
    return ContextItem(
        node.canonical_ref,
        node.node_type,
        summary,
        why,
        node.confidence.value,
        node.revision,
        node.provenance,
        token_estimate,
        node.status.value,
    )
