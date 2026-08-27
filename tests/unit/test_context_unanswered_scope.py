"""An envelope that has no answer must say so, not look complete."""

from __future__ import annotations

from extendcodeagent.context.contracts import EvidenceRole, EvidenceScope
from extendcodeagent.context.service import _unanswered_scope
from tests.unit.test_context_exemplar import item


def test_a_verification_envelope_without_a_test_says_it_has_none() -> None:
    gaps = _unanswered_scope(EvidenceScope.VERIFICATION, [item("a", EvidenceRole.SUPPORTING)])
    assert gaps == ("no_test_evidence",)


def test_a_verification_envelope_holding_a_test_reports_nothing() -> None:
    assert _unanswered_scope(EvidenceScope.VERIFICATION, [item("a", EvidenceRole.TEST)]) == ()


def test_an_empty_verification_envelope_says_it_has_none() -> None:
    assert _unanswered_scope(EvidenceScope.VERIFICATION, []) == ("no_test_evidence",)


def test_an_impact_envelope_without_a_consumer_says_it_has_none() -> None:
    gaps = _unanswered_scope(EvidenceScope.IMPACT, [item("a", EvidenceRole.TARGET)])
    assert gaps == ("no_consumer_evidence",)


def test_a_scope_that_promises_nothing_in_particular_is_not_faulted() -> None:
    # A symbol lookup answers with the symbol; there is no second kind of thing owed.
    assert _unanswered_scope(EvidenceScope.SYMBOL, []) == ()
    assert _unanswered_scope(EvidenceScope.NEIGHBORHOOD, []) == ()


def test_asking_for_tests_reaches_the_rung_that_answers_for_tests() -> None:
    """The Django corpus objective inferred `symbol`, a rung that cannot answer it."""

    from extendcodeagent.context.service import infer_evidence_scope

    asked = "Select the existing tests that must run for a change to django/views/base.py."
    assert infer_evidence_scope(asked) is EvidenceScope.VERIFICATION
    assert infer_evidence_scope("Which tests cover this?") is EvidenceScope.VERIFICATION
    assert infer_evidence_scope("test selection for the parser") is EvidenceScope.VERIFICATION


def test_merely_mentioning_tests_does_not_widen_the_scope() -> None:
    from extendcodeagent.context.service import infer_evidence_scope

    assert infer_evidence_scope("Rename the parser. Do not edit tests.") is EvidenceScope.SYMBOL
    assert infer_evidence_scope("Fix the failing test_parse case") is EvidenceScope.SYMBOL


def test_ordinary_english_is_not_reported_as_a_missing_anchor() -> None:
    """`objective_anchor_missing:must` appeared on every Django envelope."""

    from extendcodeagent.context.service import _objective_terms

    terms = _objective_terms("Select the existing tests that must run. Do not edit source.")
    assert terms == ()


def test_a_name_survives_term_extraction_with_its_punctuation_trimmed() -> None:
    from extendcodeagent.context.service import _objective_terms

    assert _objective_terms("Change django/views/base.py.") == ("django/views/base.py",)
