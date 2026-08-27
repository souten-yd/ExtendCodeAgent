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

#: Any word that could be an identifier, for grounding against what the project declares.
_WORD = re.compile(r"\b([a-z][a-z_]{3,})\b")

#: More than this and the description is not pointing anywhere in particular. Measured on
#: fifteen flask changes: at 8 the bound refused two locatable ones for a candidate set that
#: was only slightly wider, and at 16 every changed file is found in 10 of 15 while the
#: average candidate set is 3.9 files. Past that the set stops being a location.
DEFAULT_MAX_FILES = 16

#: A family stem shorter than this matches most of a codebase.
_MIN_STEM = 4

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

    # Tests mention the names a description marks out as much as the code does, and a
    # change is not made in them. Counting them pushed a locatable change over the bound
    # that says "this is not a location": `encoding` matched seven files where the source
    # holds three.
    paths = tuple(
        dict.fromkeys(
            node.source_ref
            for node in snapshot.nodes
            if node.source_ref.endswith(".py") and not _is_test_path(node.source_ref)
        )
    )

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
            if name in str(node.properties.get("name", "")) and not _is_test_path(node.source_ref)
        }
        mentioned = {path for path in paths if path.endswith(".py") and name in text_of(path)}
        return frozenset(declared | mentioned)

    return search


def declares_in(snapshot: Any) -> Callable[[str], bool]:
    """Whether the project declares something by exactly this name."""

    declared = {
        str(node.properties.get("name", ""))
        for node in snapshot.nodes
        if not _is_test_path(node.source_ref)
    }
    return lambda name: name in declared


_TEST_PATH = re.compile(r"(^|/)(tests?|testing)/|(^|/)test_[^/]*\.py$|_test\.py$")


def _is_test_path(path: str) -> bool:
    return bool(_TEST_PATH.search(path))


def _family(name: str) -> str:
    """The name a new sibling would join, or the name itself when it has no family."""

    parts = name.split("_")
    stem = "_".join(parts[:-1]) if len(parts) > 1 else name
    return stem if len(stem) >= _MIN_STEM else name


def grounded_names(description: str, declares: Callable[[str], bool]) -> tuple[str, ...]:
    """Ordinary words in the description that the project declares as symbols.

    Some descriptions mark nothing out: "the session is marked as accessed for operations
    that only access the keys" names `session` and `accessed` in prose, and both are symbols
    here. Five of fifteen flask changes are described that way, and matching only what the
    author chose to quote left the envelope empty for all five.

    The project decides, not a word list: a word counts when something is declared with
    exactly that name, so prose stays prose unless the code says otherwise.

    What the project declares is functions, classes and methods. `session` and `accessed`
    are an attribute and a class variable, so neither is grounded and that description still
    locates nothing. Recovering those means indexing attributes, which is a change to the
    graph rather than to this.
    """

    return tuple(sorted({word for word in _WORD.findall(description) if declares(word)}))


def files_for(
    description: str,
    search: FileSearch,
    *,
    declares: Callable[[str], bool] | None = None,
    max_files: int = DEFAULT_MAX_FILES,
) -> tuple[str, ...]:
    """Files a described change is likely to touch, or nothing when it cannot tell.

    Returning nothing is a real answer: a description that names something the project does
    not contain yet is describing an addition, and pretending to have located it would send
    the consumer somewhere arbitrary.
    """

    names = described_names(description)
    if declares is not None:
        names = tuple(dict.fromkeys((*names, *grounded_names(description, declares))))
    if not names:
        return ()
    found: set[str] = set()
    for name in names:
        hits = search(name)
        if not hits:
            # The name is what the change introduces, and its family is already there:
            # `SESSION_COOKIE_PARTITIONED` joins `SESSION_COOKIE_SECURE` and the rest, so
            # the file its siblings live in is where it goes. Tried only when the exact name
            # finds nothing, because a stem on its own matches far more.
            hits = search(_family(name))
        found |= hits
    if not found or len(found) > max_files:
        return ()
    return tuple(sorted(found))
