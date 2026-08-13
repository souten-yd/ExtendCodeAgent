from __future__ import annotations

from datetime import UTC, datetime

from extendcodeagent.core.contracts import Confidence, ProjectRef, Provenance
from extendcodeagent.research import (
    Claim,
    ClaimStatus,
    Evidence,
    ResearchDepth,
    ResearchRequest,
    SourceCandidate,
    build_research_plan,
    evaluate_claims,
)


def _project() -> ProjectRef:
    return ProjectRef("p", "w", "file:///repo")


def test_research_plan_is_deterministically_bounded() -> None:
    request = ResearchRequest("r1", _project(), "SQLite atomic migration", ResearchDepth.MICRO)
    plan = build_research_plan(request, ("official docs", "release notes", "duplicate"))

    assert plan.request_id == "r1"
    assert plan.queries == ("SQLite atomic migration official docs", "SQLite atomic migration release notes")
    assert plan.max_queries == 2
    assert plan.max_sources == 4


def test_external_evidence_supports_claim_but_is_not_verified_project_fact() -> None:
    provenance = Provenance("https://example.test/docs", "fake-search", "1")
    candidate = SourceCandidate("s1", "https://example.test/docs", "Official docs", provenance)
    evidence = Evidence(
        "e1",
        candidate.candidate_id,
        "content-hash",
        "SQLite transactions are atomic.",
        provenance,
        Confidence(0.9, "official source"),
        datetime.now(UTC),
        external=True,
    )
    result = evaluate_claims((Claim("c1", "Transactions are atomic", ("e1",)),), (evidence,))

    assert result.claims[0].status is ClaimStatus.SUPPORTED_EXTERNAL
    assert result.claims[0].verified_project_fact is False
    assert result.coverage_gaps == ()


def test_missing_and_conflicting_claim_evidence_are_explicit() -> None:
    result = evaluate_claims(
        (Claim("missing", "No evidence", ()), Claim("lost", "Missing ref", ("unknown",))),
        (),
    )

    assert {gap.claim_id for gap in result.coverage_gaps} == {"missing", "lost"}
    assert result.retrieval_deficit.missing_evidence == 2
