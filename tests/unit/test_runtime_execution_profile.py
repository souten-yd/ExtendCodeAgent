"""A profile is only useful if it is never confidently wrong."""

from __future__ import annotations

import pytest

from extendcodeagent.core.contracts import SourceRevision
from extendcodeagent.runtime import (
    ExecutionCommand,
    ExecutionProfile,
    KnowledgeSource,
    profile_json,
)

HEAD = SourceRevision("a" * 40)
LATER = SourceRevision("b" * 40)


def declared(command: str = "pytest", *files: str) -> ExecutionCommand:
    return ExecutionCommand(
        purpose="test",
        command=command,
        source=KnowledgeSource.DECLARED,
        source_revision=HEAD,
        source_files=files or ("pyproject.toml",),
    )


def observed(command: str = "uv run pytest") -> ExecutionCommand:
    return ExecutionCommand(
        purpose="test",
        command=command,
        source=KnowledgeSource.OBSERVED,
        source_revision=HEAD,
    )


def test_declared_knowledge_must_cite_its_files() -> None:
    with pytest.raises(ValueError):
        ExecutionCommand(
            purpose="test",
            command="pytest",
            source=KnowledgeSource.DECLARED,
            source_revision=HEAD,
        )


def test_observed_knowledge_needs_no_files_because_it_ran() -> None:
    assert observed().source_files == ()


def test_a_command_without_a_purpose_is_rejected() -> None:
    with pytest.raises(ValueError):
        ExecutionCommand(
            purpose="  ",
            command="pytest",
            source=KnowledgeSource.OBSERVED,
            source_revision=HEAD,
        )


def test_editing_the_file_it_was_read_from_invalidates_declared_knowledge() -> None:
    # The `pytest` → `uv run pytest` migration is exactly this: same revision, changed file.
    assert declared("pytest", "pyproject.toml").stale_against(HEAD, ["pyproject.toml"])


def test_editing_an_unrelated_file_leaves_declared_knowledge_standing() -> None:
    assert not declared("pytest", "pyproject.toml").stale_against(HEAD, ["src/app.py"])


def test_observed_knowledge_survives_a_config_edit_at_the_same_revision() -> None:
    assert not observed().stale_against(HEAD, ["pyproject.toml"])


def test_nothing_survives_a_change_of_revision() -> None:
    assert observed().stale_against(LATER, [])
    assert declared().stale_against(LATER, [])


def test_what_ran_is_preferred_over_what_was_read() -> None:
    profile = ExecutionProfile((declared("pytest"), observed("uv run pytest")))
    chosen = profile.for_purpose("test")
    assert chosen is not None
    assert chosen.command == "uv run pytest"


def test_declared_knowledge_answers_when_nothing_has_been_observed() -> None:
    chosen = ExecutionProfile((declared("pytest"),)).for_purpose("test")
    assert chosen is not None
    assert chosen.command == "pytest"


def test_an_unknown_purpose_is_reported_as_unknown_rather_than_guessed() -> None:
    assert ExecutionProfile((declared(),)).for_purpose("deploy") is None


def test_stale_commands_are_dropped_rather_than_downgraded() -> None:
    profile = ExecutionProfile((declared("pytest", "tox.ini"), observed()))
    fresh = profile.fresh(HEAD, ["tox.ini"])
    assert [item.source for item in fresh.commands] == [KnowledgeSource.OBSERVED]


def test_a_profile_at_a_new_revision_claims_nothing() -> None:
    profile = ExecutionProfile((declared(), observed()))
    assert profile.fresh(LATER).commands == ()


def test_the_emitted_shape_stays_small_and_omits_what_is_empty() -> None:
    payload = profile_json(ExecutionProfile((observed(),)))
    assert payload == {"test": {"command": "uv run pytest", "cwd": ".", "source": "observed"}}


def test_prerequisites_are_carried_because_a_command_that_needs_a_service_fails_without_it() -> (
    None
):
    command = ExecutionCommand(
        purpose="test",
        command="pytest",
        source=KnowledgeSource.OBSERVED,
        source_revision=HEAD,
        requires=("postgres:5432",),
    )
    assert profile_json(ExecutionProfile((command,)))["test"]["requires"] == ["postgres:5432"]
