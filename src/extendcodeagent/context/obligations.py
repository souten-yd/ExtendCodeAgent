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

from collections import Counter
from collections.abc import Callable, Iterable
from itertools import zip_longest

from extendcodeagent.core.contracts import CanonicalRef
from extendcodeagent.graph import GraphSnapshot
from extendcodeagent.testing import focused_test_paths, objective_test_paths

from .contracts import EvidenceRole, RequiredRef

_CONSUMER_EDGES = frozenset({"calls", "may_call", "references", "imports"})

# "Never rank away required truth" holds for a handful of obligations. A file-level target
# in a large project reaches thousands, and an envelope of thousands answers nothing: on
# django/db/models/sql/query.py the closure is 24,428 symbols. Past this bound obligations
# are ranked like anything else, and the envelope reports that it had to.
DEFAULT_MAX_OBLIGATIONS = 64

# How far Impact may walk for each rung of the evidence ladder. Measured on thirty Django
# changes, the recommended-test precision is 0.068 at depth 1, peaks at 0.112 at depth 2 and
# falls to 0.104 at depth 6 while recall climbs 0.19 -> 0.47. Starting wide therefore pays
# the worst case every time; starting narrow and widening only when the narrow answer did
# not hold pays it when it is actually earned.
SCOPE_IMPACT_DEPTH = {
    "symbol": 1,
    "neighborhood": 1,
    "impact": 2,
    "verification": 3,
    "subsystem": 6,
}

Equivalents = Callable[[str], Iterable[str]]
RecommendedTests = Callable[[int], Iterable[str]]
ObservedTests = Callable[[Iterable[str]], Iterable[str]]


def obligation_refs(
    snapshot: GraphSnapshot,
    target_refs: tuple[str, ...],
    objective: str,
    *,
    scope: str = "impact",
    equivalents: Equivalents,
    recommended_tests: RecommendedTests,
    observed_tests: ObservedTests | None = None,
    changing: bool = False,
    executed_refs: frozenset[str] = frozenset(),
    requested_refs: frozenset[str] = frozenset(),
    max_obligations: int = DEFAULT_MAX_OBLIGATIONS,
) -> tuple[RequiredRef, ...]:
    if not target_refs:
        return ()

    targets: list[str] = []
    # A ref standing for the symbols in a file: they answer the question, but the obligation
    # was to the file, not to everything that happens to live inside it.
    from_expansion: set[str] = set()
    per_file: list[list[str]] = []
    for ref in target_refs:
        targets.append(ref)
        expanded = [item for item in equivalents(ref) if item != ref]
        from_expansion.update(expanded)
        per_file.append(expanded)
    # Round-robin across the named files rather than one file at a time. Concatenated, a
    # change touching four production files spent the whole obligation budget inside the
    # first of them, and every symbol the other three changed went unselected — all four
    # such misses on flask came from two- and four-file commits.
    targets.extend(
        ref for group in zip_longest(*per_file, fillvalue=None) for ref in group if ref is not None
    )
    equivalent = set(targets)

    consumers = [
        edge.source.value
        for edge in snapshot.edges
        if edge.target.value in equivalent and edge.edge_type in _CONSUMER_EDGES
    ]
    # A consumer reached only through an expanded file inherits the expansion's standing.
    # Naming a file made everything calling anything inside it required, and thirty-one
    # protected call sites is the same dilution as twenty-nine protected members: nobody
    # asked about them, they were reached by asking about the file.
    from_expansion.update(
        edge.source.value
        for edge in snapshot.edges
        if edge.target.value in from_expansion and edge.edge_type in _CONSUMER_EDGES
    )

    # Observed first: a test that was seen touching this ref is fact, while everything
    # below it is inference. It is also the only signal that reaches a test which never
    # names its subject -- Django's tests reach theirs through the runner and the app
    # registry, so no call or import edge joins them and static analysis cannot recover it.
    observed = list(observed_tests(equivalent) if observed_tests else ())
    inferred = [
        ref
        for ref in recommended_tests(SCOPE_IMPACT_DEPTH.get(scope, 2))
        if ref not in set(observed)
    ]

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
    inferred.extend(
        node.canonical_ref.value
        for node in snapshot.nodes
        if node.node_type == "file" and node.source_ref in intent_paths
    )

    # What the consumer asked for by name is admitted before the budget is divided. It is
    # kept separate from `executed_refs` because the two differ in width: the failing tests
    # run 103 symbols, and ranking admission by those replaced the obligation set with most
    # of the framework, while a search names four and names them for a reason.
    requested = tuple(ref for ref in dict.fromkeys(targets) if ref in requested_refs)[
        :REQUESTED_LIMIT
    ]
    return _by_role_budget(
        from_expansion,
        requested,
        # A change is told which tests fail; it has to be told what the code currently is.
        # Splitting the budget evenly gave 21 of 32 protected slots to tests that the task
        # statement had already named, and the source to be written was pushed out.
        changing,
        (
            (EvidenceRole.TARGET, targets),
            # Observed and inferred tests hold separate floors. Coverage is fact and ranks
            # first, but on a project whose tests do import their subjects it is not
            # better than the static answer, and letting it consume the whole test budget
            # displaced correct inferences -- measured on seventeen changes here, recall
            # 0.86 -> 0.50 while precision rose 0.18 -> 0.22.
            (EvidenceRole.TEST, observed),
            (EvidenceRole.TEST, inferred),
            (EvidenceRole.CONSUMER, consumers),
        ),
        max_obligations,
    )


#: The most a change is told about tests. Not zero, because one real test carries the
#: project's convention; small, because the failing ones are named in the task itself.
CHANGE_TEST_LIMIT = 2

#: How many named requests are honoured ahead of the budget. Bounded, because a request
#: that admits everything is the wide-net failure again in another form.
REQUESTED_LIMIT = 8


def _by_role_budget(
    from_expansion: set[str],
    requested: tuple[str, ...],
    changing: bool,
    roles: tuple[tuple[EvidenceRole, list[str]], ...],
    budget: int,
) -> tuple[RequiredRef, ...]:
    """Give every role a floor, then spend what is left in priority order.

    First-come allocation starves whichever role sorts last. On
    django/db/models/sql/query.py a file target expands to 117 symbols with 107 consumers,
    so a flat budget of 64 was spent before the 21 tests Impact had already found were
    reached — the envelope answered "which tests?" without a single test in it.
    """

    # Not ranked by execution. Sorting these so executed refs come first was tried and cost
    # a case: the failing tests run 103 symbols where the obligation budget is 64, so
    # "executed first" replaces the obligation set with most of the framework and drops the
    # members of the changed file that were being carried. Coverage is a useful ordering for
    # bodies, where the set competes only with itself, and too wide a net for admission.
    populated = [(role, values) for role, values in roles if values]
    if not populated:
        return ()
    floor = max(1, budget // len(populated))

    def cap_for(role: EvidenceRole) -> int:
        # A ceiling, not a floor. Capping only the first pass left the second pass free to
        # fill the budget with tests anyway: twenty of them, on a task whose statement had
        # already named the ones that fail.
        if changing and role is EvidenceRole.TEST:
            return CHANGE_TEST_LIMIT
        return floor

    taken: list[RequiredRef] = []
    seen: set[str] = set()
    per_role: Counter[EvidenceRole] = Counter()
    role_of = {value: role for role, values in populated for value in values}

    def admit(value: str, role: EvidenceRole) -> None:
        seen.add(value)
        per_role[role] += 1
        taken.append(RequiredRef(CanonicalRef(value), role, value not in from_expansion))

    for value in requested:
        if value not in seen and value in role_of:
            admit(value, role_of[value])
    for role, values in populated:
        for value in values[: cap_for(role)]:
            if value not in seen:
                admit(value, role)
    for role, values in populated:
        capped = changing and role is EvidenceRole.TEST
        for value in values:
            if len(taken) >= budget:
                return tuple(taken[:budget])
            if capped and per_role[role] >= CHANGE_TEST_LIMIT:
                break
            if value not in seen:
                admit(value, role)
    return tuple(taken[:budget])
