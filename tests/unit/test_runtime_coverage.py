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
    RuntimeObservation,
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

    covering = covering_tests(
        (observation,), (CanonicalRef("py://mod#late"),), lambda ref: "tests" in ref.value
    )
    assert [ref.value for ref in covering] == ["py://tests.test_mod#test_late_path"]


def _observation(observed: tuple[str, ...]) -> RuntimeObservation:
    return RuntimeObservation(
        observation_id="o-1",
        kind=ObservationKind.TEST,
        project=PROJECT,
        source_revision=REVISION,
        status=ObservationStatus.PASSED,
        started_at=AT,
        finished_at=AT,
        provenance=PROVENANCE,
        observed_refs=tuple(CanonicalRef(ref) for ref in observed),
        command="pytest",
    )


def _is_test(ref: CanonicalRef) -> bool:
    return "test" in ref.value


def test_the_file_is_asked_only_when_the_symbols_answer_nothing() -> None:
    """A change that adds a function has no symbol at the base for coverage to have reached."""

    observations = [_observation(("py://app#test_a", "file://app.py"))]
    found = covering_tests(
        observations,
        [CanonicalRef("py://app#brand_new")],
        _is_test,
        fallback_refs=[CanonicalRef("file://app.py")],
    )
    assert found == (CanonicalRef("py://app#test_a"),)


def test_the_narrower_question_wins_when_it_has_an_answer() -> None:
    observations = [_observation(("py://app#test_narrow", "py://app#changed"))]
    found = covering_tests(
        observations,
        [CanonicalRef("py://app#changed")],
        _is_test,
        fallback_refs=[CanonicalRef("file://app.py")],
    )
    assert found == (CanonicalRef("py://app#test_narrow"),)


def test_without_a_fallback_an_unknown_symbol_still_answers_nothing() -> None:
    observations = [_observation(("py://app#test_a", "file://app.py"))]
    assert covering_tests(observations, [CanonicalRef("py://app#brand_new")], _is_test) == ()
