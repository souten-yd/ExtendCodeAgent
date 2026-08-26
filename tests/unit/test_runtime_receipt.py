from __future__ import annotations

import pytest

from extendcodeagent.context import estimate_payload_tokens
from extendcodeagent.core.contracts import CanonicalRef, SourceRevision
from extendcodeagent.runtime import EditReceipt, completed_paths, receipt_json

REVISION = SourceRevision("abc123")


def _receipt(*paths: str, **kwargs: object) -> EditReceipt:
    return EditReceipt(REVISION, paths, **kwargs)  # type: ignore[arg-type]


def test_a_receipt_addresses_the_diff_it_replaces() -> None:
    """Dropping the text is a decision about the conversation, not about the record."""

    payload = receipt_json(_receipt("src/app.py", "src/util.py"))

    assert payload["revision"] == "abc123"
    assert payload["files_changed"] == ["src/app.py", "src/util.py"]


def test_empty_fields_are_omitted_rather_than_sent_as_null() -> None:
    payload = receipt_json(_receipt("src/app.py"))

    assert set(payload) == {"revision", "files_changed", "verification"}


def test_a_receipt_is_far_cheaper_than_the_diff_it_stands_for() -> None:
    """Measured over 184 real commits the ratio is 82.5x; the shape has to earn that."""

    payload = receipt_json(
        _receipt(
            "src/app.py",
            changed_refs=(CanonicalRef("py://app#handler"),),
            semantic_changes=("handler signature gained a context argument",),
            verification="unit PASS",
        )
    )

    assert estimate_payload_tokens(payload) < 120


def test_a_receipt_must_name_what_changed() -> None:
    with pytest.raises(ValueError, match="names what changed"):
        EditReceipt(REVISION, ())


def test_receipts_report_what_a_task_has_already_done() -> None:
    """A long edit otherwise spends turns re-establishing its own progress."""

    done = completed_paths([_receipt("src/a.py", "src/b.py"), _receipt("src/b.py", "src/c.py")])

    assert done == ("src/a.py", "src/b.py", "src/c.py")
