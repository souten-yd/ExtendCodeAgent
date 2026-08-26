"""What to keep after an edit, instead of the edit.

An agent that changes a file leaves the diff in its conversation, and every later turn
re-sends it. Measured over 184 real commits across five repositories, a diff averages
6,564 tokens against 80 for a record of what it did — 82.5x — and at p90 a single diff is
4,513 tokens, heavier than the whole evidence envelope.

The diff itself is not lost by dropping it. It is in the repository, addressed by the
revision the receipt names, and can be fetched if anything ever needs it. What the
conversation keeps is what the next step actually reasons about: which revision, what
moved, whether it verified, and what is still open.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from extendcodeagent.core.contracts import CanonicalRef, SourceRevision


@dataclass(frozen=True, slots=True)
class EditReceipt:
    """One applied change, in the form a later turn needs it.

    `revision` is what makes the receipt sufficient rather than lossy: it addresses the
    real diff, so dropping the text is a decision about the conversation and not about
    the record.
    """

    revision: SourceRevision
    changed_paths: tuple[str, ...]
    changed_refs: tuple[CanonicalRef, ...] = ()
    semantic_changes: tuple[str, ...] = ()
    verification: str = "pending"
    open_gaps: tuple[str, ...] = ()
    unmatched_sites: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.changed_paths:
            raise ValueError("a receipt records a change, so it names what changed")
        if any(not path.strip() for path in self.changed_paths):
            raise ValueError("changed_paths must not contain empty values")


def receipt_json(receipt: EditReceipt) -> dict[str, object]:
    """The consumer-facing shape. Empty fields are omitted rather than sent as null."""

    payload: dict[str, object] = {
        "revision": receipt.revision.value,
        "files_changed": list(receipt.changed_paths),
        "verification": receipt.verification,
    }
    for name, values in (
        ("changed_refs", [ref.value for ref in receipt.changed_refs]),
        ("semantic_changes", list(receipt.semantic_changes)),
        ("open_gaps", list(receipt.open_gaps)),
        ("unmatched_sites", list(receipt.unmatched_sites)),
    ):
        if values:
            payload[name] = values
    return payload


def completed_paths(receipts: Iterable[EditReceipt]) -> tuple[str, ...]:
    """Everything already changed across a task, so a later step does not revisit it.

    A long edit spends turns re-establishing what it has already done. The receipts are
    that record, and reading it back is cheaper than reading the files again.
    """

    return tuple(dict.fromkeys(path for receipt in receipts for path in receipt.changed_paths))
