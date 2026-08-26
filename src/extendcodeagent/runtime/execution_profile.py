"""How this project is built, tested and run — stated once instead of rediscovered.

An agent that does not know the test command reads until it finds one, and there is no
one place to look. Measured across five repositories, the files that might hold it come to
1,089–6,330 tokens before counting CI, and the answer sits somewhere different each time:
`setup.cfg` in httpx, `pyproject.toml` in scrapy, and for Django mostly inside 10,709
tokens of workflow files. A stated profile is about 50 tokens — two orders of magnitude
less, and it does not depend on the agent looking in the right file.

Two kinds of knowledge, kept apart because they age differently:

- **declared** — read out of `pyproject.toml`, `tox.ini`, a Makefile, a workflow. Its
  truth is the truth of those files, so it is invalidated when they change.
- **observed** — this command actually ran, this port was taken, this service was needed.
  Runtime evidence, invalidated by a later observation rather than by a file edit.

Both carry the revision they were established at. A profile that says `pytest` when the
project has moved to `uv run pytest` is worse than no profile: an agent trusts it, and
the failure looks like a broken project rather than a stale fact.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from extendcodeagent.core.contracts import SourceRevision


class KnowledgeSource(StrEnum):
    DECLARED = "declared"
    OBSERVED = "observed"


@dataclass(frozen=True, slots=True)
class ExecutionCommand:
    """One thing that can be run, and the grounds for believing it works."""

    purpose: str
    command: str
    source: KnowledgeSource
    source_revision: SourceRevision
    source_files: tuple[str, ...] = ()
    working_directory: str = "."
    requires: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.purpose.strip() or not self.command.strip():
            raise ValueError("a command needs a purpose and something to run")
        if self.source is KnowledgeSource.DECLARED and not self.source_files:
            raise ValueError("declared knowledge must say which files it was read from")

    def stale_against(self, revision: SourceRevision, changed_paths: Iterable[str]) -> bool:
        """Whether this should no longer be trusted.

        Declared knowledge ages with the files it was read from, so a change to one of them
        invalidates it even at the same revision. Observed knowledge ages with the revision
        it was observed at, because what ran is what ran.
        """

        if self.source_revision != revision:
            return True
        if self.source is KnowledgeSource.OBSERVED:
            return False
        touched = set(changed_paths)
        return any(path in touched for path in self.source_files)


@dataclass(frozen=True, slots=True)
class ExecutionProfile:
    """Everything runnable about a project, with each claim's grounds attached."""

    commands: tuple[ExecutionCommand, ...] = ()

    def for_purpose(self, purpose: str) -> ExecutionCommand | None:
        """The best command for a purpose: something observed to work beats something read.

        A command that ran is evidence; a command found in a config file is a claim about
        what should run, and the two are not equally trustworthy.
        """

        matching = [item for item in self.commands if item.purpose == purpose]
        if not matching:
            return None
        observed = [item for item in matching if item.source is KnowledgeSource.OBSERVED]
        return (observed or matching)[0]

    def fresh(
        self, revision: SourceRevision, changed_paths: Iterable[str] = ()
    ) -> ExecutionProfile:
        """The profile with everything stale dropped rather than downgraded.

        A stale command is worse than a missing one: an agent trusts it, and the failure
        reads as a broken project instead of an out-of-date fact.
        """

        touched = tuple(changed_paths)
        return ExecutionProfile(
            tuple(item for item in self.commands if not item.stale_against(revision, touched))
        )


def profile_json(profile: ExecutionProfile) -> dict[str, object]:
    return {
        item.purpose: {
            "command": item.command,
            "cwd": item.working_directory,
            "source": str(item.source),
            **({"requires": list(item.requires)} if item.requires else {}),
        }
        for item in profile.commands
    }
