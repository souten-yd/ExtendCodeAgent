from __future__ import annotations

from datetime import UTC, datetime

import pytest

from extendcodeagent.core.contracts import Provenance, SourceRevision
from extendcodeagent.runtime import ObservedAbsence, established_absences

R1 = SourceRevision("rev-1")
R2 = SourceRevision("rev-2")
PROVENANCE = Provenance("runtime", "search", "1", R1)
AT = datetime(2026, 8, 26, tzinfo=UTC)


def _absent(pattern: str, scope: str = "", revision: SourceRevision = R1) -> ObservedAbsence:
    return ObservedAbsence(pattern, scope, revision, AT, PROVENANCE)


def test_an_absence_settles_the_question_it_was_asked() -> None:
    found = established_absences([_absent("retry_policy")], R1, ["retry_policy"])

    assert [item.pattern for item in found] == ["retry_policy"]


def test_an_absence_from_another_revision_is_not_offered() -> None:
    """An absence stops being true the moment anyone adds the thing."""

    assert established_absences([_absent("retry_policy", revision=R2)], R1, ["retry_policy"]) == ()


def test_a_narrow_absence_does_not_answer_a_wide_question() -> None:
    """Finding nothing under tests/ says nothing about the rest of the repository."""

    narrow = [_absent("retry_policy", scope="tests/")]

    assert established_absences(narrow, R1, ["retry_policy"], scope="tests/unit/")
    assert established_absences(narrow, R1, ["retry_policy"], scope="") == ()


def test_a_project_wide_absence_answers_any_subtree() -> None:
    wide = [_absent("retry_policy", scope="")]

    assert established_absences(wide, R1, ["retry_policy"], scope="src/deep/")


def test_a_different_pattern_is_a_different_question() -> None:
    assert established_absences([_absent("retry_policy")], R1, ["retry_budget"]) == ()


def test_an_absence_must_say_what_was_looked_for() -> None:
    with pytest.raises(ValueError, match="what was looked for"):
        ObservedAbsence("  ", "", R1, AT, PROVENANCE)
