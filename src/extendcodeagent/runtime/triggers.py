"""Find where Project Intelligence failed, from what the agent did next.

Every defect worth fixing in this stage was found the same way: not by reading code, but
by comparing a claim against what actually happened. The Twin claimed to hold the project
and held an evaluation corpus; the budget claimed to bound the payload and measured a
different object; `tests.py` was a test to the oracle and not to the analyzer.

An agent's own trace carries the same kind of disagreement. When PI has answered well the
agent acts on the answer; when it has not, the agent works around it, and the workaround
is visible. Reading a file twice in one session means something was delivered and lost.
Running the whole suite after touching two files means the required set was never offered
or was not believed. Searching for a path PI just delivered means the delivery did not
land.

These are triggers, not verdicts. Each names the capability whose answer was worked
around, so that improvement is aimed by evidence rather than by assumption.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum

from extendcodeagent.core.config.schema import CapabilityName

from .contracts import ObservationKind, RuntimeObservation, RuntimeSignal, RuntimeSignalKind

#: A path touched this many times in one session was delivered and then lost.
REPEATED_TOUCH_THRESHOLD = 3

#: Above this many mutated paths, running everything is a reasonable choice rather than a
#: sign that test selection went unused.
FOCUSED_CHANGE_PATHS = 5


class TriggerKind(StrEnum):
    REPEATED_TOUCH = "repeated_touch"
    UNSELECTED_VERIFICATION = "unselected_verification"
    DELIVERY_NOT_USED = "delivery_not_used"


@dataclass(frozen=True, slots=True)
class ImprovementTrigger:
    """One place an agent worked around PI, and the capability it worked around."""

    kind: TriggerKind
    capability: CapabilityName
    detail: str
    subjects: tuple[str, ...]
    occurrences: int
    session_id: str | None = None

    def __post_init__(self) -> None:
        if not self.detail.strip():
            raise ValueError("a trigger must say what was observed")
        if self.occurrences <= 0:
            raise ValueError("a trigger describes something that happened")


def detect_triggers(
    signals: Sequence[RuntimeSignal],
    observations: Iterable[RuntimeObservation] = (),
) -> tuple[ImprovementTrigger, ...]:
    """Every trigger the trace supports, ordered so the most repeated reads first."""

    found: list[ImprovementTrigger] = []
    found.extend(_repeated_touch(signals))
    found.extend(_unselected_verification(signals, tuple(observations)))
    found.extend(_delivery_not_used(signals))
    return tuple(
        sorted(found, key=lambda item: (-item.occurrences, item.kind.value, item.subjects))
    )


def _by_session(signals: Sequence[RuntimeSignal]) -> dict[str | None, list[RuntimeSignal]]:
    grouped: dict[str | None, list[RuntimeSignal]] = defaultdict(list)
    for signal in signals:
        grouped[signal.runtime_session_id].append(signal)
    return grouped


def _repeated_touch(signals: Sequence[RuntimeSignal]) -> list[ImprovementTrigger]:
    """A path handled repeatedly in one session was delivered and then lost.

    Re-reading is the agent rebuilding context it already had, and it is the mechanism
    behind session growth: measured on the held-out baseline, PI's own payload was 21% of
    the prompt and the accumulating loop was the rest.
    """

    triggers: list[ImprovementTrigger] = []
    for session, group in _by_session(signals).items():
        counts = Counter(path for signal in group for path in signal.paths)
        repeated = {
            path: count for path, count in counts.items() if count >= REPEATED_TOUCH_THRESHOLD
        }
        if not repeated:
            continue
        triggers.append(
            ImprovementTrigger(
                kind=TriggerKind.REPEATED_TOUCH,
                capability=CapabilityName.CONTEXT,
                detail=(
                    f"{len(repeated)} path(s) handled {max(repeated.values())} times or more "
                    "in one session; context delivered them and did not keep them"
                ),
                subjects=tuple(sorted(repeated)),
                occurrences=max(repeated.values()),
                session_id=session,
            )
        )
    return triggers


def _unselected_verification(
    signals: Sequence[RuntimeSignal], observations: Sequence[RuntimeObservation]
) -> list[ImprovementTrigger]:
    """A focused change verified by running everything means the required set went unused."""

    triggers: list[ImprovementTrigger] = []
    for session, group in _by_session(signals).items():
        mutated = {
            path
            for signal in group
            if signal.kind is RuntimeSignalKind.MUTATION
            for path in signal.paths
        }
        if not mutated or len(mutated) > FOCUSED_CHANGE_PATHS:
            continue
        offered = any(
            signal.kind is RuntimeSignalKind.ADVISORY_DELIVERY
            and (signal.tool or "").startswith("pi_test")
            for signal in group
        )
        ran = [
            item
            for item in observations
            if item.kind is ObservationKind.TEST and item.runtime_session_id == session
        ]
        if offered or not ran:
            continue
        triggers.append(
            ImprovementTrigger(
                kind=TriggerKind.UNSELECTED_VERIFICATION,
                capability=CapabilityName.TEST_SELECTION,
                detail=(
                    f"{len(mutated)} path(s) changed and tests were run without a required "
                    "set being offered"
                ),
                subjects=tuple(sorted(mutated)),
                occurrences=len(ran),
                session_id=session,
            )
        )
    return triggers


def _delivery_not_used(signals: Sequence[RuntimeSignal]) -> list[ImprovementTrigger]:
    """Handling a path again after PI delivered it means the delivery did not land."""

    triggers: list[ImprovementTrigger] = []
    for session, group in _by_session(signals).items():
        delivered: set[str] = set()
        ignored: Counter[str] = Counter()
        for signal in sorted(group, key=lambda item: item.observed_at):
            if signal.kind is RuntimeSignalKind.ADVISORY_DELIVERY:
                delivered.update(signal.paths)
                continue
            for path in signal.paths:
                if path in delivered:
                    ignored[path] += 1
        if not ignored:
            continue
        triggers.append(
            ImprovementTrigger(
                kind=TriggerKind.DELIVERY_NOT_USED,
                capability=CapabilityName.CONTEXT,
                detail=(
                    f"{len(ignored)} delivered path(s) were handled again afterwards; the "
                    "delivery was not in a form the agent could act on"
                ),
                subjects=tuple(sorted(ignored)),
                occurrences=sum(ignored.values()),
                session_id=session,
            )
        )
    return triggers
