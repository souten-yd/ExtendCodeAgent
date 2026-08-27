"""What a task has already learned about itself, kept beside the conversation.

A turn re-sends everything before it. Traced over Django cases, that re-sent history is
94% of the cumulative prompt: by the fourth turn a prompt is 4.8x its first, and in one
run 8x, carrying nothing but what the run had already done. A project being large is not
what grew it — holding the task's own history in the conversation is.

So the history is held here instead, structured rather than summarised. A summary of a
conversation is still prose to re-read; an attempt that failed is a fact with a shape, and
the next step only needs the shape.

This is a projection, not a new owner. `PlanOutcome` already records what was planned,
`convergence` what has and has not been reached, `EditReceipt` what was changed, and
`ObservedAbsence` what the project turned out not to contain. What was missing is the
record of what this task tried and what came of it.

`ObservedAbsence` and `Attempt` are close and are deliberately separate: an absence is a
fact about the project, invalidated by a revision, while an attempt is a fact about this
task, invalidated by nothing — a hypothesis that was disproved stays disproved.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum


class AttemptOutcome(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DISPROVED = "disproved"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True, slots=True)
class Attempt:
    """One thing this task tried, and what came of it."""

    action: str
    outcome: AttemptOutcome
    detail: str = ""

    def __post_init__(self) -> None:
        if not self.action.strip():
            raise ValueError("an attempt must say what was tried")


@dataclass(frozen=True, slots=True)
class TaskExecutionState:
    """A task's own history, in the form the next step needs it.

    Kept small on purpose. Everything here is something a later turn would otherwise
    re-derive by reading the conversation that produced it.
    """

    task_id: str
    goal: str
    stage: str = "started"
    attempts: tuple[Attempt, ...] = ()
    completed: tuple[str, ...] = ()
    remaining: tuple[str, ...] = ()
    open_gaps: tuple[str, ...] = ()
    decisions: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id must not be empty")
        if not self.goal.strip():
            raise ValueError("a task state without a goal cannot direct a next step")

    @property
    def ruled_out(self) -> tuple[Attempt, ...]:
        """Attempts that settled something negatively.

        This is the half that stops repetition: a run that is not told a hypothesis was
        disproved tests it again, which is the same failure the project-level absence
        record prevents one level up.
        """

        return tuple(
            item
            for item in self.attempts
            if item.outcome in {AttemptOutcome.FAILED, AttemptOutcome.DISPROVED}
        )


def task_state_json(state: TaskExecutionState) -> dict[str, object]:
    """The consumer-facing shape. Empty fields are omitted rather than sent as null."""

    payload: dict[str, object] = {
        "task": state.task_id,
        "goal": state.goal,
        "stage": state.stage,
    }
    ruled_out = [
        f"{item.action}: {item.outcome.value}" + (f" ({item.detail})" if item.detail else "")
        for item in state.ruled_out
    ]
    for name, values in (
        ("completed", list(state.completed)),
        ("remaining", list(state.remaining)),
        ("ruled_out", ruled_out),
        ("open_gaps", list(state.open_gaps)),
        ("decisions", list(state.decisions)),
    ):
        if values:
            payload[name] = values
    return payload


def advance(state: TaskExecutionState, *attempts: Attempt) -> TaskExecutionState:
    """Record what a step tried, keeping the order it tried it in."""

    from dataclasses import replace

    return replace(state, attempts=(*state.attempts, *attempts))


def remaining_after(state: TaskExecutionState, done: Iterable[str]) -> tuple[str, ...]:
    """What is left once these are finished, without re-listing what is not."""

    finished = set(state.completed) | set(done)
    return tuple(item for item in state.remaining if item not in finished)
