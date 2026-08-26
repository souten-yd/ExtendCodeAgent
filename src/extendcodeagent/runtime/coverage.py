"""Turn a test run's coverage into the relation static analysis cannot hold.

A test reaches its subject through whatever the framework provides — a runner, an app
registry, a fixture, a dependency injector — and leaves no call or import edge behind.
Measured on django/django, that is why recommended tests reach recall 0.30: the pair is
absent from the graph, not mis-ranked in it.

Coverage supplies the missing pair, and it does not need a separate indexing pass. A test
is run at least once when it is written, and again on every suite run, so the relation
accumulates as a by-product of work already being done.

This module takes a mapping that is already parsed. Producing it is the host's job and
differs per language — `coverage.py` contexts, `jest --coverage`, `go test -coverprofile` —
so no coverage library is a dependency of the core.
"""

from __future__ import annotations

from collections.abc import Mapping, Set
from datetime import datetime

from extendcodeagent.core.contracts import CanonicalRef, ProjectRef, Provenance, SourceRevision
from extendcodeagent.graph import GraphSnapshot

from .contracts import ObservationKind, ObservationStatus, RuntimeObservation

COVERAGE_PRODUCER = "runtime.coverage"
COVERAGE_PRODUCER_VERSION = "1"

#: What one test executed: source path -> the line numbers it reached.
ExecutedLines = Mapping[str, Set[int]]

_STRUCTURAL = frozenset({"file", "directory", "repository", "module"})


def symbols_touched(snapshot: GraphSnapshot, executed: ExecutedLines) -> tuple[CanonicalRef, ...]:
    """Symbols whose declared span contains at least one executed line.

    Structural nodes are excluded: knowing a file was entered says nothing a path did not
    already say, and admitting them would put every symbol's container into the evidence.
    """

    touched: list[CanonicalRef] = []
    for node in snapshot.nodes:
        lines = executed.get(node.source_ref)
        if not lines or node.node_type in _STRUCTURAL:
            continue
        start = node.properties.get("start_line")
        end = node.properties.get("end_line")
        if not isinstance(start, int) or not isinstance(end, int):
            continue
        if any(start <= line <= end for line in lines):
            touched.append(node.canonical_ref)
    return tuple(dict.fromkeys(touched))


def observation_from_coverage(
    snapshot: GraphSnapshot,
    *,
    project: ProjectRef,
    source_revision: SourceRevision,
    test_id: str,
    executed: ExecutedLines,
    status: ObservationStatus,
    started_at: datetime,
    finished_at: datetime,
    command: str = "",
) -> RuntimeObservation:
    """One test run, recorded as the symbols it actually reached.

    The test's own ref is recorded alongside them, because the pair is the point: an
    obligation asks "what covers this symbol?" and the answer is the other end of an
    observation that named both.
    """

    if not test_id.strip():
        raise ValueError("test_id must not be empty")
    refs = symbols_touched(snapshot, executed)
    return RuntimeObservation(
        observation_id=f"coverage:{source_revision.value}:{test_id}",
        kind=ObservationKind.TEST,
        project=project,
        source_revision=source_revision,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        provenance=Provenance(
            source="runtime",
            producer=COVERAGE_PRODUCER,
            producer_version=COVERAGE_PRODUCER_VERSION,
            source_revision=source_revision,
        ),
        observed_refs=(CanonicalRef(test_id), *refs),
        command=command or "test",
        summary=f"{test_id} reached {len(refs)} symbols",
    )
