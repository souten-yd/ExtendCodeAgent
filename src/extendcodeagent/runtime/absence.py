"""Facts about what a project does not contain.

A graph holds entities that exist. It has no way to say that something does not, because
absence has no node — and that is the fact an agent most often needs and most often has to
rediscover. Traced over six Django changes, seventeen of twenty-two baseline actions
returned nothing, and five repeated a search that had already returned nothing; one run
issued the same query four times across eight turns and never answered.

The fact those runs needed was "no test imports this module", which is true and
unrepresentable in the structural model. So it is represented here instead.

An absence is bound harder to its revision than a positive fact is. A symbol that exists
keeps existing through most edits; an absence stops being true the moment anyone adds the
thing, and adding is what changes to a project mostly are. Measured on flask, 18.1% of
positive facts were stale after 669 commits — a negative fact has no such margin, so one
is only ever answered for the exact revision it was observed at.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from extendcodeagent.core.contracts import Provenance, SourceRevision


@dataclass(frozen=True, slots=True)
class ObservedAbsence:
    """A search that was run and found nothing, at a stated revision.

    `scope` is the path prefix the search covered — empty means the whole project. A
    narrower observation cannot answer a wider question: finding nothing under `tests/`
    says nothing about the rest of the repository.
    """

    pattern: str
    scope: str
    source_revision: SourceRevision
    observed_at: datetime
    provenance: Provenance

    def __post_init__(self) -> None:
        if not self.pattern.strip():
            raise ValueError("an absence must say what was looked for")

    def answers(self, pattern: str, scope: str) -> bool:
        """Whether this observation settles that question, without widening it."""

        if self.pattern != pattern:
            return False
        # An absence over the whole project also settles any subtree of it; the reverse
        # is not true, and treating it as true would report a false absence.
        return self.scope == "" or scope.startswith(self.scope)


def established_absences(
    observations: Iterable[ObservedAbsence],
    revision: SourceRevision,
    patterns: Iterable[str],
    scope: str = "",
) -> tuple[ObservedAbsence, ...]:
    """Absences already settled for exactly this revision.

    Nothing observed at another revision is offered. An absence carried forward across a
    change is the failure mode this exists to prevent, not a saving.
    """

    wanted = tuple(dict.fromkeys(patterns))
    return tuple(
        observation
        for pattern in wanted
        for observation in observations
        if observation.source_revision == revision and observation.answers(pattern, scope)
    )
