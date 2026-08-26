from __future__ import annotations

import pytest

from extendcodeagent.context import estimate_payload_tokens
from extendcodeagent.runtime import (
    Attempt,
    AttemptOutcome,
    TaskExecutionState,
    advance,
    remaining_after,
    task_state_json,
)


def _state(**kwargs: object) -> TaskExecutionState:
    return TaskExecutionState("t-1", "fix the login regression", **kwargs)  # type: ignore[arg-type]


def test_a_state_carries_what_a_next_step_would_otherwise_re_derive() -> None:
    payload = task_state_json(
        _state(
            stage="verification_failed",
            completed=("localized AuthService.login",),
            remaining=("inspect the API to browser boundary",),
        )
    )

    assert payload["stage"] == "verification_failed"
    assert payload["completed"] == ["localized AuthService.login"]
    assert payload["remaining"] == ["inspect the API to browser boundary"]


def test_what_was_ruled_out_is_what_stops_repetition() -> None:
    """A run not told a hypothesis was disproved tests it again."""

    state = advance(
        _state(),
        Attempt("searched UserService.create", AttemptOutcome.INCONCLUSIVE),
        Attempt("modified auth/cache.py", AttemptOutcome.FAILED, "test still fails"),
        Attempt("hypothesis: stale cookie", AttemptOutcome.DISPROVED),
    )

    ruled = task_state_json(state)["ruled_out"]

    assert ruled == [
        "modified auth/cache.py: failed (test still fails)",
        "hypothesis: stale cookie: disproved",
    ]


def test_an_inconclusive_attempt_is_not_ruled_out() -> None:
    """Not finding a root cause is not evidence the path is wrong."""

    state = advance(_state(), Attempt("searched widely", AttemptOutcome.INCONCLUSIVE))

    assert state.ruled_out == ()


def test_attempts_keep_the_order_they_were_made_in() -> None:
    state = advance(_state(), Attempt("first", AttemptOutcome.FAILED))
    state = advance(state, Attempt("second", AttemptOutcome.FAILED))

    assert [item.action for item in state.attempts] == ["first", "second"]


def test_remaining_drops_what_has_since_been_finished() -> None:
    state = _state(completed=("a",), remaining=("a", "b", "c"))

    assert remaining_after(state, ["b"]) == ("c",)


def test_the_whole_state_is_smaller_than_one_turn_of_re_sent_history() -> None:
    """Re-sent history was 94% of the cumulative prompt; this is what replaces it."""

    payload = task_state_json(
        advance(
            _state(
                stage="verification_failed",
                completed=("localized AuthService.login", "patched session validation"),
                remaining=("inspect the API to browser boundary",),
                open_gaps=("frontend session propagation",),
            ),
            Attempt("modified auth/cache.py", AttemptOutcome.FAILED, "test_login_redirect"),
        )
    )

    assert estimate_payload_tokens(payload) < 120


def test_a_state_without_a_goal_cannot_direct_a_next_step() -> None:
    with pytest.raises(ValueError, match="without a goal"):
        TaskExecutionState("t-1", "   ")
