"""Compose one answer envelope from the capabilities that supply its parts.

Selecting evidence, deciding which obligations must be carried, giving a named symbol its
body and serializing the result are four separate concerns, and the application would
otherwise wire them together by hand every time it is asked a question. The lookups are
injected so this stays a function of a snapshot, and so a different consumer can supply
them from somewhere else.
"""

from __future__ import annotations

from typing import Any

from extendcodeagent.core.contracts import CanonicalRef
from extendcodeagent.graph import GraphSnapshot

from .contracts import EvidenceScope, WeakLocalEvidenceRequest
from .obligations import Equivalents, ObservedTests, RecommendedTests, obligation_refs
from .serialization import estimate_payload_tokens, weak_local_evidence_json
from .service import (
    SourceReader,
    attach_excerpts,
    attach_exemplar,
    build_weak_local_evidence,
    infer_evidence_scope,
    stable_evidence_envelope,
)


def build_answer_envelope(
    snapshot: GraphSnapshot,
    objective: str,
    target_refs: tuple[str, ...],
    *,
    equivalents: Equivalents,
    recommended_tests: RecommendedTests,
    observed_tests: ObservedTests,
    read_source_span: SourceReader,
    token_budget: int,
    max_items: int,
    scope: str | None = None,
    changing: bool = False,
    prior_evidence_ids: tuple[str, ...] = (),
    unresolved_gaps: tuple[str, ...] = (),
) -> dict[str, Any]:
    # The ladder starts narrow; an explicit scope is a caller widening it because a
    # narrower answer did not hold.
    resolved = EvidenceScope(scope) if scope is not None else infer_evidence_scope(objective)
    # Whether this asks for the code to be different is declared, not inferred. Reading it
    # out of the words classified `Assess the change impact if X changes` as a change and
    # capped its tests at two, dropping sealed recall from 1.00 to 0.711 — a keyword cannot
    # tell a request to change something from a question about a change.
    package = build_weak_local_evidence(
        snapshot,
        WeakLocalEvidenceRequest(
            objective,
            tuple(CanonicalRef(item) for item in target_refs),
            token_budget,
            max_items,
            scope=resolved,
            required_refs=obligation_refs(
                snapshot,
                target_refs,
                objective,
                scope=resolved.value,
                changing=changing,
                equivalents=equivalents,
                recommended_tests=recommended_tests,
                observed_tests=observed_tests,
            ),
            prior_evidence_ids=prior_evidence_ids,
            unresolved_gaps=unresolved_gaps,
        ),
    )
    # A change names files; a question names symbols. Handing a change the file's symbol
    # names and no source leaves it nothing to write from — measured on flask, 64 names and
    # zero lines. Handing a question every body in the file was 49% of a retrieval envelope.
    if changing:
        # The exemplar goes first so it is inside the allowance rather than added after it.
        # Applied last it spent its own 400 tokens on top of a full envelope, which is how a
        # payload declared at 8,192 came to 8,496.
        #
        # One real test, because a convention cannot be stated from outside the project:
        # measured across five repositories, test and assertion style are 89% to 100%
        # consistent and disagree between projects.
        package = attach_exemplar(package, read_source_span)

    # Bodies are carved out of the stated budget, not added to it. Held separately they
    # composed into 8,208 tokens against a declared 8,192 the moment selection was allowed
    # its full ceiling — a budget that two mechanisms each spend in full is not a budget.
    #
    # What is left is measured on the payload rather than on `used_tokens`, which counts the
    # items and not the frame around them. Subtracting the items alone left room for 1,495
    # tokens that were already spoken for.
    frame = estimate_payload_tokens(weak_local_evidence_json(package, stable_evidence_envelope()))
    package = attach_excerpts(
        package,
        read_source_span,
        named_refs=frozenset(target_refs),
        token_budget=max(0, token_budget - frame),
        expand_files=changing,
    )
    return weak_local_evidence_json(package, stable_evidence_envelope())
