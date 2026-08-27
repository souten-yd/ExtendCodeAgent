"""Reading a project's execution knowledge out of the files that hold it.

Where that is was measured rather than assumed. Across flask, httpx, scrapy, django and
requests, the conventional set an agent is expected to consult — `AGENTS.md`, `CLAUDE.md`,
`pyproject.toml`, `package.json`, the README — contained a runnable test command in
**none of the five**. The answer was in `tox.ini`, a `Makefile`, `CONTRIBUTING.rst`, a
`conftest.py`, and for httpx in `scripts/test`, a shell script named by no configuration
at all. Django's runner is `runtests.py`, not pytest.

That last pair is why this exists. An agent that defaults to `pytest` is not merely slow on
Django, it is wrong, and the failure reads as a broken checkout rather than a bad guess.

So nothing here guesses. Every command returned cites the file it was read from, and a
project whose command cannot be read reports nothing rather than a plausible default.
"""

from __future__ import annotations

import configparser
import json
import re
import tomllib
from collections.abc import Callable
from pathlib import Path

from extendcodeagent.core.contracts import SourceRevision

from .execution_profile import ExecutionCommand, ExecutionProfile, KnowledgeSource

# Free-form so a bespoke runner survives: httpx's `scripts/test`, Django's `runtests.py`.
_MAKE_TARGET = re.compile(r"^([a-zA-Z][\w-]*)\s*:(?!=)")
# tox writes commands against its own environment. Left as-is they are not runnable,
# and a command that cannot be run is the failure this module exists to prevent.
_TOX_OPTIONAL = re.compile(r"\{posargs:?[^}]*\}")
_TOX_SUBSTITUTIONS = {"{envpython}": "python", "{envbindir}/": "", "{toxinidir}": "."}
_PURPOSE_ALIASES = {
    "test": "test",
    "tests": "test",
    "lint": "lint",
    "format": "format",
    "typecheck": "typecheck",
    "mypy": "typecheck",
    "build": "build",
    "docs": "docs",
}

ReadText = Callable[[str], str]


def _purpose(name: str) -> str | None:
    return _PURPOSE_ALIASES.get(name.strip().lower())


def _resolve_tox(command: str) -> str:
    """Turn a tox command into one that runs outside tox."""

    resolved = _TOX_OPTIONAL.sub("", command)
    for placeholder, value in _TOX_SUBSTITUTIONS.items():
        resolved = resolved.replace(placeholder, value)
    # An argument still holding a tox variable is dropped, because it is nearly always
    # an optional flag — flask's `--basetemp={envtmpdir}` costs nothing to lose, and
    # keeping it would emit a command that fails as though the project were broken.
    words = [word for word in resolved.split() if "{" not in word]
    # If the executable itself is a variable, nothing here can say what runs.
    return "" if not words or "{" in resolved.split()[0] else " ".join(words)


def _from_tox(text: str) -> list[tuple[str, str]]:
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read_string(text)
    except configparser.Error:
        return []
    found: list[tuple[str, str]] = []
    for section in parser.sections():
        raw = parser.get(section, "commands", fallback="")
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if not lines:
            continue
        # `[testenv]` is tox's default environment; a suffixed one is a variant.
        purpose = _purpose(section.removeprefix("testenv:")) or (
            "test" if section == "testenv" else None
        )
        if purpose and (command := _resolve_tox(lines[0])):
            found.append((purpose, command))
    return found


def _from_makefile(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    target: str | None = None
    for line in text.splitlines():
        match = _MAKE_TARGET.match(line)
        if match:
            target = _purpose(match.group(1))
            continue
        if target and line.startswith("\t"):
            found.append((target, line.strip().lstrip("@-")))
            target = None
    return found


def _from_package_json(text: str) -> list[tuple[str, str]]:
    try:
        scripts = json.loads(text).get("scripts", {})
    except (json.JSONDecodeError, AttributeError):
        return []
    if not isinstance(scripts, dict):
        return []
    return [
        (purpose, f"npm run {name}")
        for name, value in scripts.items()
        if isinstance(value, str) and (purpose := _purpose(name))
    ]


def _from_pyproject(text: str) -> list[tuple[str, str]]:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return []
    tools = data.get("tool", {})
    if not isinstance(tools, dict):
        return []
    found: list[tuple[str, str]] = []
    for runner in ("poe", "hatch", "pdm", "rye"):
        tasks = tools.get(runner, {})
        scripts = tasks.get("scripts", tasks.get("tasks", {})) if isinstance(tasks, dict) else {}
        if isinstance(scripts, dict):
            found += [
                (purpose, f"{runner} run {name}")
                for name in scripts
                if (purpose := _purpose(str(name)))
            ]
    return found


_READERS: tuple[tuple[str, Callable[[str], list[tuple[str, str]]]], ...] = (
    ("tox.ini", _from_tox),
    ("Makefile", _from_makefile),
    ("package.json", _from_package_json),
    ("pyproject.toml", _from_pyproject),
)

# httpx keeps its commands here and names them nowhere else, so the directory is the fact.
_SCRIPT_DIR = "scripts"


def declared_profile(
    revision: SourceRevision,
    tracked_paths: frozenset[str],
    read_text: ReadText,
) -> ExecutionProfile:
    """The commands a project states about itself, each citing where it was read.

    `tracked_paths` is the repository's own file list, so an untracked local script is
    never mistaken for a project convention.
    """

    commands: list[ExecutionCommand] = []
    claimed: set[str] = set()

    def offer(purpose: str, command: str, source_file: str) -> None:
        # First reader to answer a purpose wins; the order in `_READERS` is the order of
        # specificity, and a later, vaguer statement should not displace a precise one.
        if purpose in claimed or not command.strip():
            return
        claimed.add(purpose)
        commands.append(
            ExecutionCommand(
                purpose=purpose,
                command=command.strip(),
                source=KnowledgeSource.DECLARED,
                source_revision=revision,
                source_files=(source_file,),
            )
        )

    for path, reader in _READERS:
        if path not in tracked_paths:
            continue
        try:
            text = read_text(path)
        except OSError:
            continue
        for purpose, command in reader(text):
            offer(purpose, command, path)

    for path in sorted(tracked_paths):
        parent, _, name = path.rpartition("/")
        if parent == _SCRIPT_DIR and (script_purpose := _purpose(name)):
            offer(script_purpose, path, path)

    return ExecutionProfile(tuple(commands))


def discover_from_root(revision: SourceRevision, root: Path) -> ExecutionProfile:
    """The same, for a checkout on disk."""

    tracked = frozenset(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())

    def read(path: str) -> str:
        return (root / path).read_text(errors="replace")

    return declared_profile(revision, tracked, read)
