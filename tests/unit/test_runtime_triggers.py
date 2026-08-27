from __future__ import annotations

from datetime import UTC, datetime, timedelta

from extendcodeagent.core.config.schema import CapabilityName
from extendcodeagent.core.contracts import ProjectRef, Provenance, SourceRevision
from extendcodeagent.runtime import (
    ObservationKind,
    ObservationStatus,
    RuntimeObservation,
    RuntimeSignal,
    RuntimeSignalKind,
    TriggerKind,
    detect_triggers,
)

PROJECT = ProjectRef("project", "workspace", "file:///repo")
REVISION = SourceRevision("rev-1")
PROVENANCE = Provenance("runtime", "opencode", "1", REVISION)
START = datetime(2026, 8, 26, tzinfo=UTC)
SESSION = "session-1"


def _mutation(index: int, *paths: str) -> RuntimeSignal:
    return RuntimeSignal(
        f"sig-{index}",
        RuntimeSignalKind.MUTATION,
        PROJECT,
        START + timedelta(seconds=index),
        PROVENANCE,
        runtime_session_id=SESSION,
        source_category="edit",
        paths=paths,
    )


def _delivery(index: int, tool: str, *paths: str) -> RuntimeSignal:
    return RuntimeSignal(
        f"sig-{index}",
        RuntimeSignalKind.ADVISORY_DELIVERY,
        PROJECT,
        START + timedelta(seconds=index),
        PROVENANCE,
        runtime_session_id=SESSION,
        delivery_channel="tool",
        tool=tool,
        paths=paths,
    )


def _test_run(index: int) -> RuntimeObservation:
    return RuntimeObservation(
        f"obs-{index}",
        ObservationKind.TEST,
        PROJECT,
        REVISION,
        ObservationStatus.PASSED,
        START,
        START,
        PROVENANCE,
        command="pytest",
        runtime_session_id=SESSION,
    )


def test_a_path_handled_again_and_again_names_the_context_capability() -> None:
    """Re-reading is the agent rebuilding what it was already given."""

    triggers = detect_triggers(
        [_mutation(i, "src/app.py") for i in range(3)] + [_mutation(9, "src/other.py")]
    )

    assert len(triggers) == 1
    assert triggers[0].kind is TriggerKind.REPEATED_TOUCH
    assert triggers[0].capability is CapabilityName.CONTEXT
    assert triggers[0].subjects == ("src/app.py",)
    assert triggers[0].occurrences == 3


def test_two_touches_are_ordinary_work() -> None:
    assert detect_triggers([_mutation(i, "src/app.py") for i in range(2)]) == ()


def test_running_tests_after_a_focused_change_without_an_offer_is_a_trigger() -> None:
    triggers = detect_triggers([_mutation(1, "src/app.py")], [_test_run(1)])

    assert [item.kind for item in triggers] == [TriggerKind.UNSELECTED_VERIFICATION]
    assert triggers[0].capability is CapabilityName.TEST_SELECTION


def test_no_trigger_when_a_required_set_was_offered() -> None:
    """PI answered; whatever the agent then chose is the agent's call, not a PI failure."""

    triggers = detect_triggers(
        [_mutation(1, "src/app.py"), _delivery(2, "pi_tests")], [_test_run(1)]
    )

    assert all(item.kind is not TriggerKind.UNSELECTED_VERIFICATION for item in triggers)


def test_a_sprawling_change_verified_broadly_is_not_a_trigger() -> None:
    """Running everything after touching a dozen files is a reasonable choice."""

    spread = [_mutation(i, f"src/mod{i}.py") for i in range(8)]

    triggers = detect_triggers(spread, [_test_run(1)])

    assert all(item.kind is not TriggerKind.UNSELECTED_VERIFICATION for item in triggers)


def test_handling_a_delivered_path_again_says_the_delivery_did_not_land() -> None:
    triggers = detect_triggers(
        [_delivery(1, "pi_context", "src/app.py"), _mutation(2, "src/app.py")]
    )

    assert [item.kind for item in triggers] == [TriggerKind.DELIVERY_NOT_USED]
    assert triggers[0].subjects == ("src/app.py",)


def test_work_before_a_delivery_is_not_ignoring_it() -> None:
    triggers = detect_triggers(
        [_mutation(1, "src/app.py"), _delivery(2, "pi_context", "src/app.py")]
    )

    assert all(item.kind is not TriggerKind.DELIVERY_NOT_USED for item in triggers)
