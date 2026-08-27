"""One real example instead of a rule the runtime cannot know."""

from __future__ import annotations

from extendcodeagent.context import attach_exemplar
from extendcodeagent.context.contracts import (
    EvidenceRole,
    EvidenceScope,
    WeakLocalEvidenceItem,
    WeakLocalEvidencePackage,
)
from extendcodeagent.core.contracts import CanonicalRef


def item(
    ref: str,
    role: EvidenceRole,
    *,
    start: int | None = 1,
    end: int | None = 8,
    excerpt: str | None = None,
) -> WeakLocalEvidenceItem:
    return WeakLocalEvidenceItem(
        f"e-{ref}",
        CanonicalRef(f"py://tests.test_thing#{ref}"),
        "tests/test_thing.py",
        "test",
        "",
        "required:test",
        1.0,
        "p1",
        "declared",
        12,
        role,
        start,
        end,
        excerpt,
    )


def package(*items: WeakLocalEvidenceItem) -> WeakLocalEvidencePackage:
    return WeakLocalEvidencePackage(
        scope=EvidenceScope.VERIFICATION,
        revision_id=None,
        source_revision=None,
        objective_fingerprint="f",
        items=items,
        provenance=(),
        selected_evidence_ids=(),
        prior_evidence_ids=(),
        unresolved_gaps=(),
        next_scope=None,
        used_tokens=0,
        token_budget=4096,
        candidate_count=len(items),
        excluded_count=0,
        truncated=False,
        candidate_search_truncated=False,
        deterministic_resolution=True,
    )


def reader(text: str = "def test_thing():\n    assert True\n"):
    return lambda ref, start, end: text


def excerpts(result: WeakLocalEvidencePackage) -> list[str | None]:
    return [entry.excerpt for entry in result.items]


def test_one_test_is_given_its_body() -> None:
    result = attach_exemplar(package(item("a", EvidenceRole.TEST)), reader())
    assert excerpts(result) == ["def test_thing():\n    assert True\n"]


def test_a_second_example_adds_nothing_and_is_not_sent() -> None:
    result = attach_exemplar(
        package(item("a", EvidenceRole.TEST), item("b", EvidenceRole.TEST)), reader()
    )
    assert [bool(entry) for entry in excerpts(result)] == [True, False]


def test_a_package_without_tests_is_unchanged() -> None:
    original = package(item("a", EvidenceRole.SUPPORTING))
    assert attach_exemplar(original, reader()) == original


def test_an_item_that_already_has_its_body_is_left_alone() -> None:
    original = package(item("a", EvidenceRole.TEST, excerpt="kept"))
    assert excerpts(attach_exemplar(original, reader())) == ["kept"]


def test_an_item_without_line_information_cannot_supply_an_example() -> None:
    original = package(item("a", EvidenceRole.TEST, start=None, end=None))
    assert attach_exemplar(original, reader()) == original


def test_a_long_test_is_not_used_as_the_example() -> None:
    original = package(item("a", EvidenceRole.TEST, start=1, end=500))
    assert attach_exemplar(original, reader()) == original


def test_an_example_over_budget_is_refused_rather_than_truncated() -> None:
    # A cut-off test teaches the wrong convention, which is worse than sending none.
    original = package(item("a", EvidenceRole.TEST))
    assert attach_exemplar(original, reader("x " * 4000)) == original


def test_an_unreadable_source_leaves_the_package_alone() -> None:
    original = package(item("a", EvidenceRole.TEST))
    assert attach_exemplar(original, lambda ref, start, end: "") == original


def test_the_role_is_selectable_so_other_conventions_can_be_shown() -> None:
    result = attach_exemplar(
        package(item("a", EvidenceRole.SUPPORTING)), reader(), role="supporting"
    )
    assert excerpts(result) == ["def test_thing():\n    assert True\n"]
