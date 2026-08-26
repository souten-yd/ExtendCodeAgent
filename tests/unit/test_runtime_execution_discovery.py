"""Reading execution knowledge from the places it actually lives.

The cases here are the shapes the five measured repositories turned out to have, including
the two that break the usual assumption: httpx states its commands only in `scripts/`, and
Django's runner is not pytest.
"""

from __future__ import annotations

from extendcodeagent.core.contracts import SourceRevision
from extendcodeagent.runtime import KnowledgeSource
from extendcodeagent.runtime.execution_discovery import declared_profile

HEAD = SourceRevision("c" * 40)


def discover(files: dict[str, str]):
    return declared_profile(HEAD, frozenset(files), files.__getitem__)


def command_for(files: dict[str, str], purpose: str = "test") -> str | None:
    found = discover(files).for_purpose(purpose)
    return found.command if found else None


def test_a_project_stating_nothing_yields_nothing_rather_than_a_default() -> None:
    assert discover({"README.md": "# hello"}).commands == ()


def test_tox_default_environment_is_the_test_command() -> None:
    ini = "[testenv]\ncommands =\n    pytest tests\n"
    assert command_for({"tox.ini": ini}) == "pytest tests"


def test_djangos_runner_is_reported_as_itself_and_not_as_pytest() -> None:
    ini = "[testenv]\ncommands =\n    {envpython} runtests.py {posargs}\n"
    assert command_for({"tox.ini": ini}) == "python runtests.py"


def test_an_optional_tox_argument_is_dropped_rather_than_breaking_the_command() -> None:
    # flask's real line; `--basetemp={envtmpdir}` costs nothing to lose.
    ini = "[testenv]\ncommands =\n    pytest -v --tb=short --basetemp={envtmpdir}\n"
    assert command_for({"tox.ini": ini}) == "pytest -v --tb=short"


def test_an_unresolvable_executable_yields_nothing_rather_than_a_broken_command() -> None:
    ini = "[testenv]\ncommands =\n    {custom_runner} tests\n"
    assert command_for({"tox.ini": ini}) is None


def test_a_named_tox_environment_supplies_its_own_purpose() -> None:
    ini = "[testenv:lint]\ncommands =\n    flake8 .\n"
    assert command_for({"tox.ini": ini}, "lint") == "flake8 ."


def test_a_script_directory_is_read_because_httpx_states_its_commands_nowhere_else() -> None:
    assert command_for({"scripts/test": "#!/bin/sh\npytest\n"}) == "scripts/test"


def test_an_ambiguous_script_name_claims_no_purpose() -> None:
    # httpx's `scripts/check` is its linter; treating it as the test command was a real bug.
    files = {"scripts/check": "ruff check .", "scripts/test": "#!/bin/sh\npytest\n"}
    assert command_for(files) == "scripts/test"


def test_an_untracked_script_is_not_mistaken_for_a_project_convention() -> None:
    profile = declared_profile(HEAD, frozenset(), lambda path: "pytest")
    assert profile.commands == ()


def test_a_makefile_target_supplies_its_recipe() -> None:
    makefile = "test:\n\t@pytest tests/\n\nlint:\n\truff check .\n"
    assert command_for({"Makefile": makefile}) == "pytest tests/"
    assert command_for({"Makefile": makefile}, "lint") == "ruff check ."


def test_package_json_scripts_are_read_as_npm_invocations() -> None:
    assert command_for({"package.json": '{"scripts": {"test": "jest"}}'}) == "npm run test"


def test_a_task_runner_declared_in_pyproject_is_read() -> None:
    toml = '[tool.hatch.scripts]\ntest = "pytest"\n'
    assert command_for({"pyproject.toml": toml}) == "hatch run test"


def test_the_more_specific_statement_wins_when_two_files_disagree() -> None:
    files = {"tox.ini": "[testenv]\ncommands =\n    pytest tests\n", "Makefile": "test:\n\ttox\n"}
    assert command_for(files) == "pytest tests"


def test_everything_read_cites_the_file_it_came_from() -> None:
    profile = discover({"tox.ini": "[testenv]\ncommands =\n    pytest\n"})
    assert all(
        item.source is KnowledgeSource.DECLARED and item.source_files == ("tox.ini",)
        for item in profile.commands
    )


def test_a_malformed_file_is_skipped_instead_of_raising() -> None:
    assert discover({"pyproject.toml": "not [ valid toml", "package.json": "{oops"}).commands == ()
