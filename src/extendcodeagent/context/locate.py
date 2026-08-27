"""Where a described change belongs, before anyone has said which file.

The envelope answers "you are changing this file — what else do you need". Asked without a
target it returns nothing, which is correct for what it was built to do and useless for the
way a change actually arrives: as a sentence about behaviour, with the location still to be
found. Measured on fifteen flask changes described only by their changelog entry, that first
step cost the consumer a search and a round trip every time.

The sentence names things. A changelog says `template_filter` and `SECRET_KEY_FALLBACKS`
because those are what the reader has to recognise, and both are in the source: one as a
symbol the graph indexes, the other as a string literal it does not. Matching the marked
names against declared symbols alone found every file in 5 of 15; against the text as well,
9 of 15, with two to twelve candidate files rather than the repository.

The six it cannot reach are the ones where the named thing is what the change introduces —
`TRUSTED_HOSTS` is a config key that does not exist yet, and no search finds what is not
there. That is a bound, not a tuning problem.

This does not compete with the consumer's own search: measured on thirty Django changes,
plain grep reaches recall 0.96 where selection reaches 0.428, so localisation is not a place
to be clever. It exists so the consumer does not have to spend a turn asking.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

#: Names a description marks out: backticked, or an all-caps configuration key. Prose is
#: excluded by construction rather than by a stop-list that has to grow.
_MARKED = re.compile(r"`([A-Za-z_][\w.]*)`|\b([A-Z][A-Z_]{3,})\b")

#: More than this and the description is not pointing anywhere in particular.
DEFAULT_MAX_FILES = 8

#: Reading a source file to look for a name. Supplied by the caller so this stays pure.
FileSearch = Callable[[str], frozenset[str]]


def described_names(description: str) -> tuple[str, ...]:
    """The names a description marks out, unqualified.

    `Request.trusted_hosts` is written for a reader who knows the class; what a file holds
    is `trusted_hosts`, so the qualifier is dropped.
    """

    found = {
        (backticked or shouted).rsplit(".", 1)[-1]
        for backticked, shouted in _MARKED.findall(description)
    }
    return tuple(sorted(name for name in found if len(name) > 3))


def files_naming(snapshot: Any, root: Path) -> FileSearch:
    """A search over a snapshot's files, by declaration and by text.

    Both, because a changelog names two kinds of thing: `template_filter` is a symbol the
    graph indexes, and `SECRET_KEY_FALLBACKS` is a string literal it does not. Declarations
    alone located every file of 5 changes in 15; with the text as well, 9.
    """

    paths = tuple(dict.fromkeys(node.source_ref for node in snapshot.nodes))

    def text_of(path: str) -> str:
        candidate = (root / path).resolve()
        if not candidate.is_relative_to(root) or not candidate.is_file():
            return ""
        try:
            return candidate.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    def search(name: str) -> frozenset[str]:
        declared = {
            node.source_ref
            for node in snapshot.nodes
            if name in str(node.properties.get("name", ""))
        }
        mentioned = {path for path in paths if path.endswith(".py") and name in text_of(path)}
        return frozenset(declared | mentioned)

    return search


def files_for(
    description: str,
    search: FileSearch,
    *,
    max_files: int = DEFAULT_MAX_FILES,
) -> tuple[str, ...]:
    """Files a described change is likely to touch, or nothing when it cannot tell.

    Returning nothing is a real answer: a description that names something the project does
    not contain yet is describing an addition, and pretending to have located it would send
    the consumer somewhere arbitrary.
    """

    names = described_names(description)
    if not names:
        return ()
    found: set[str] = set()
    for name in names:
        found |= search(name)
    if not found or len(found) > max_files:
        return ()
    return tuple(sorted(found))
