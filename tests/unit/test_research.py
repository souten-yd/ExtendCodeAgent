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
    execute_research,
)


def _project() -> ProjectRef:
    return ProjectRef("p", "w", "file:///repo")


def test_research_plan_is_deterministically_bounded() -> None:
    request = ResearchRequest("r1", _project(), "SQLite atomic migration", ResearchDepth.MICRO)
    plan = build_research_plan(request, ("official docs", "release notes", "duplicate"))

    assert plan.request_id == "r1"
    assert plan.queries == (
        "SQLite atomic migration official docs",
        "SQLite atomic migration release notes",
    )
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


def test_research_execution_uses_ports_with_plan_bounds() -> None:
    provenance = Provenance("https://example.test", "fake", "1")
    candidate = SourceCandidate("s1", "https://example.test", "Docs", provenance)
    evidence = Evidence(
        "e1",
        "s1",
        "hash",
        "summary",
        provenance,
        Confidence(0.8),
        datetime.now(UTC),
    )

    class Ports:
        stored: list[Evidence] = []

        def search(self, query: str, *, limit: int) -> tuple[SourceCandidate, ...]:
            assert limit == 4
            return (candidate,)

        def fetch(self, source: SourceCandidate) -> bytes:
            return source.title.encode()

        def extract(self, source: SourceCandidate, content: bytes) -> Evidence:
            assert content == b"Docs"
            return evidence

        def put(self, item: Evidence) -> None:
            self.stored.append(item)

        def get(self, evidence_id: str) -> Evidence | None:
            return evidence if evidence_id == "e1" else None

        def synthesize(self, plan: object, items: tuple[Evidence, ...]) -> tuple[Claim, ...]:
            assert items == (evidence,)
            return (Claim("c1", "supported", ("e1",)),)

    ports = Ports()
    result = execute_research(
        ResearchRequest("r1", _project(), "topic"),
        ports,
        ports,
        ports,
        ports,
        ports,
    )

    assert result.retrieval_deficit.missing_evidence == 0
    assert ports.stored == [evidence]
