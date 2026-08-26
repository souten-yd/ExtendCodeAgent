from __future__ import annotations

from datetime import UTC, datetime

from extendcodeagent.core.contracts import (
    CanonicalRef,
    Confidence,
    ProjectRef,
    Provenance,
    SourceRevision,
)
from extendcodeagent.graph import FactStatus, GraphNode, GraphSnapshot
from extendcodeagent.runtime import (
    ObservationKind,
    ObservationStatus,
    covering_tests,
    observation_from_coverage,
    symbols_touched,
)

PROJECT = ProjectRef("project", "workspace", "file:///repo")
REVISION = SourceRevision("rev-1")
PROVENANCE = Provenance("source", "python-ast", "1", REVISION)
AT = datetime(2026, 8, 26, tzinfo=UTC)


def _node(ref: str, path: str, kind: str, start: int, end: int) -> GraphNode:
    return GraphNode(
        ref,
        CanonicalRef(ref),
        kind,
        path,
        PROVENANCE,
        Confidence(1.0),
        FactStatus.DECLARED,
        REVISION,
        {"start_line": start, "end_line": end},
    )


SNAPSHOT = GraphSnapshot(
    PROJECT,
    None,
    (
        _node("py://mod#early", "mod.py", "function", 1, 10),
        _node("py://mod#late", "mod.py", "function", 20, 30),
        _node("file://mod.py", "mod.py", "file", 1, 30),
        _node("py://other#untouched", "other.py", "function", 1, 5),
    ),
)


def test_only_the_symbols_whose_span_was_executed_are_recorded() -> None:
    touched = symbols_touched(SNAPSHOT, {"mod.py": {22, 23}})

    assert [ref.value for ref in touched] == ["py://mod#late"]


def test_the_containing_file_is_not_reported_as_a_symbol() -> None:
    """A path was already known; admitting the container adds nothing and dilutes."""

    touched = symbols_touched(SNAPSHOT, {"mod.py": {5}})

    assert [ref.value for ref in touched] == ["py://mod#early"]


def test_a_file_with_no_executed_line_contributes_nothing() -> None:
    assert symbols_touched(SNAPSHOT, {"other.py": set()}) == ()


def test_a_run_pairs_the_test_with_what_it_reached() -> None:
    """The pair is the point: an obligation asks what covers a symbol."""

    observation = observation_from_coverage(
        SNAPSHOT,
        project=PROJECT,
        source_revision=REVISION,
        test_id="py://tests.test_mod#test_late_path",
        executed={"mod.py": {21, 25}},
        status=ObservationStatus.PASSED,
        started_at=AT,
        finished_at=AT,
        command="pytest",
    )

    assert observation.kind is ObservationKind.TEST
    assert [ref.value for ref in observation.observed_refs] == [
        "py://tests.test_mod#test_late_path",
        "py://mod#late",
    ]

    covering = covering_tests((observation,), (CanonicalRef("py://mod#late"),))
    assert [ref.value for ref in covering] == ["py://tests.test_mod#test_late_path"]
