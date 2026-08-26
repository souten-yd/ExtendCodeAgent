"""Graph-level test-path projections used by compact test and impact answers.

`select_tests` ranks the Impact report's graph-linked candidates. These functions answer the
adjacent question the compact views ask — which *source paths* an objective or a changed ref
implicates, and which verification obligation each path discharges. They live beside
`select_tests` because they are test-domain heuristics over the same Graph facts, not
application wiring.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from extendcodeagent.graph import GraphSnapshot

REQUIRED_OBLIGATIONS = frozenset({"architecture_boundary", "integration_boundary", "unit_behavior"})

_GENERIC_SOURCE_TOKENS = frozenset(
    {"src", "lib", "app", "service", "index", "main", "py", "extendcodeagent"}
)
_GENERIC_CHANGE_TOKENS = frozenset({"meets", "service", "source", "extendcodeagent"})
_IGNORED_OBJECTIVE_TOKENS = frozenset(
    {"and", "covers", "existing", "for", "its", "set", "smallest", "test", "tests", "the"}
)
_WORD = re.compile(r"[a-z0-9]+")


def test_obligation(path: str) -> str:
    """Classify which verification obligation a test path discharges."""

    parts = set(Path(path).parts)
    if "architecture" in parts:
        return "architecture_boundary"
    if "integration" in parts:
        return "integration_boundary"
    return "unit_behavior"


def uncovered_obligations(paths: Iterable[str]) -> list[str]:
    return sorted(REQUIRED_OBLIGATIONS - {test_obligation(path) for path in paths})


def _path_tokens(value: str) -> set[str]:
    return {
        token
        for part in Path(value).parts
        for token in Path(part).stem.casefold().split("_")
        if token
    }


def focused_test_paths(
    changed_refs: tuple[str, ...], nodes: dict[str, Any], candidate_tests: list[str]
) -> list[str]:
    """Narrow candidates to tests sharing a distinctive token with the changed source."""

    source_tokens = {
        token
        for ref in changed_refs
        if ref in nodes
        for token in _path_tokens(nodes[ref].source_ref)
        if token not in _GENERIC_SOURCE_TOKENS
    }
    focused = [path for path in candidate_tests if source_tokens & _path_tokens(path)]
    return focused or candidate_tests


def objective_test_paths(snapshot: GraphSnapshot, objective: str) -> set[str]:
    """Pick the best-matching test path per obligation for a stated objective."""

    if not objective.strip():
        return set()
    objective_tokens = {
        token
        for token in _WORD.findall(objective.casefold().replace("_", " "))
        if token not in _IGNORED_OBJECTIVE_TOKENS and len(token) > 2
    }
    by_path: dict[str, set[str]] = {}
    for node in snapshot.nodes:
        if node.node_type != "test":
            continue
        tokens = by_path.setdefault(node.source_ref, set())
        intent_tokens = node.properties.get("intent_tokens", ())
        if isinstance(intent_tokens, list | tuple | set):
            tokens.update(str(item).casefold() for item in intent_tokens)
        tokens.update(
            token
            for part in Path(node.source_ref).parts
            for token in _WORD.findall(part.casefold().replace("_", " "))
        )
    selected: set[str] = set()
    for obligation in sorted(REQUIRED_OBLIGATIONS):
        ranked = sorted(
            (
                (len(objective_tokens & tokens), path)
                for path, tokens in by_path.items()
                if test_obligation(path) == obligation
            ),
            key=lambda item: (-item[0], item[1]),
        )
        if ranked and ranked[0][0] > 0:
            selected.add(ranked[0][1])
    return selected


def structural_test_paths(snapshot: GraphSnapshot, candidate_refs: set[str]) -> set[str]:
    return {
        edge.source_ref
        for edge in snapshot.edges
        if edge.edge_type == "structurally_covers" and edge.source.value in candidate_refs
    }


def intent_architecture_test_paths(
    changed_refs: tuple[str, ...], nodes: dict[str, Any]
) -> set[str]:
    """Architecture tests are only relevant when the change shares their stated intent."""

    changed_tokens = {
        token
        for ref in changed_refs
        for value in (ref.rsplit("#", 1)[-1], nodes[ref].source_ref if ref in nodes else "")
        for token in _path_tokens(value)
        if len(token) >= 4 and token not in _GENERIC_CHANGE_TOKENS
    }
    return {
        node.source_ref
        for node in nodes.values()
        if node.node_type == "test"
        and "architecture" in Path(node.source_ref).parts
        and changed_tokens
        & (
            set(node.properties.get("intent_tokens", ()))
            | set(Path(node.source_ref).stem.casefold().split("_"))
        )
    }


def direct_use_count(
    snapshot: GraphSnapshot, changed_refs: set[str], production_refs: set[str]
) -> int:
    short_names = {ref.rsplit("#", 1)[-1].rsplit(".", 1)[-1] for ref in changed_refs}
    return sum(
        _edge_occurrences(edge)
        for edge in snapshot.edges
        if edge.source.value in production_refs
        and edge.edge_type in {"calls", "may_call", "references"}
        and (
            edge.target.value in changed_refs
            or edge.target.value.rsplit("#", 1)[-1].rsplit("/", 1)[-1] in short_names
        )
    )


def _edge_occurrences(edge: Any) -> int:
    value = edge.properties.get("occurrences", 1)
    return value if isinstance(value, int) else 1
