"""What an envelope must carry, taken from the capabilities that already derive it.

A generic term-and-neighbourhood search cannot reach a caller that reaches the target
through a re-export, has no reason to prefer the recommended tests over any other
neighbour, and cannot see a test that guards its target through a value flowing across
several modules. Each of those is already answered somewhere in the project: by the
reference resolver, by Impact, and by test-intent matching. This composes those answers
rather than re-deriving them worse.

The lookups are supplied by the caller so this stays a pure function over a snapshot.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from extendcodeagent.core.contracts import CanonicalRef
from extendcodeagent.graph import GraphSnapshot
from extendcodeagent.testing import focused_test_paths, objective_test_paths

_CONSUMER_EDGES = frozenset({"calls", "may_call", "references", "imports"})

# "Never rank away required truth" holds for a handful of obligations. A file-level target
# in a large project reaches thousands, and an envelope of thousands answers nothing: on
# django/db/models/sql/query.py the closure is 24,428 symbols. Past this bound obligations
# are ranked like anything else, and the envelope reports that it had to.
DEFAULT_MAX_OBLIGATIONS = 64

Equivalents = Callable[[str], Iterable[str]]
RecommendedTests = Callable[[], Iterable[str]]


def obligation_refs(
    snapshot: GraphSnapshot,
    target_refs: tuple[str, ...],
    objective: str,
    *,
    equivalents: Equivalents,
    recommended_tests: RecommendedTests,
    max_obligations: int = DEFAULT_MAX_OBLIGATIONS,
) -> tuple[CanonicalRef, ...]:
    if not target_refs:
        return ()

    refs: list[str] = []
    for ref in target_refs:
        refs.append(ref)
        refs.extend(equivalents(ref))
    equivalent = set(refs)

    for edge in snapshot.edges:
        if edge.target.value in equivalent and edge.edge_type in _CONSUMER_EDGES:
            refs.append(edge.source.value)

    refs.extend(recommended_tests())

    # Two independent test signals, because each fails where the other works. Objective
    # matching needs the objective to name something distinctive; stem correspondence
    # (`utils.py` -> `test_utils.py`) needs only the changed file. On a flat test tree
    # objective matching collapses to one path per obligation class.
    all_tests = sorted({node.source_ref for node in snapshot.nodes if node.node_type == "test"})
    nodes_by_ref = {node.canonical_ref.value: node for node in snapshot.nodes}
    intent_paths = set(objective_test_paths(snapshot, objective))
    intent_paths.update(focused_test_paths(tuple(equivalent), nodes_by_ref, all_tests))

    # One ref per path, not every symbol sharing it: a test file holds many nodes, and
    # naming the path would admit all of them, crowding out the precise obligations.
    refs.extend(
        node.canonical_ref.value
        for node in snapshot.nodes
        if node.node_type == "file" and node.source_ref in intent_paths
    )
    # Insertion order is the priority order: the targets themselves, then what they
    # equivalate to, then their consumers, then the tests Impact recommends, then the
    # tests matched by intent. Truncation therefore drops the weakest claims first.
    ordered = list(dict.fromkeys(refs))
    return tuple(CanonicalRef(value) for value in ordered[:max_obligations])
