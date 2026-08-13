"""Deterministic research planning and claim coverage evaluation."""

from __future__ import annotations

from extendcodeagent.core.contracts import Confidence, EvidenceStatus

from .contracts import (
    Claim,
    ClaimStatus,
    CoverageGap,
    EvaluatedClaim,
    Evidence,
    ResearchDepth,
    ResearchEvaluation,
    ResearchPlan,
    ResearchRequest,
    RetrievalDeficit,
)

_BUDGETS = {
    ResearchDepth.MICRO: (2, 4, 30),
    ResearchDepth.STANDARD: (5, 10, 90),
    ResearchDepth.DEEP: (10, 25, 300),
}


def build_research_plan(
    request: ResearchRequest, query_facets: tuple[str, ...] = ()
) -> ResearchPlan:
    max_queries, max_sources, max_time = _BUDGETS[request.depth]
    facets = tuple(dict.fromkeys(item.strip() for item in query_facets if item.strip()))
    queries = tuple(f"{request.query} {item}" for item in facets[:max_queries])
    if not queries:
        queries = (request.query,)
    return ResearchPlan(request.request_id, queries, max_queries, max_sources, max_time)


def evaluate_claims(
    claims: tuple[Claim, ...], evidence: tuple[Evidence, ...]
) -> ResearchEvaluation:
    evidence_by_id = {item.evidence_id: item for item in evidence}
    evaluated: list[EvaluatedClaim] = []
    gaps: list[CoverageGap] = []
    for claim in claims:
        supporting = tuple(
            evidence_by_id[item] for item in claim.evidence_ids if item in evidence_by_id
        )
        missing = len(claim.evidence_ids) - len(supporting)
        if not supporting:
            status = ClaimStatus.UNSUPPORTED
            confidence = Confidence(0.0, "no available evidence")
            gaps.append(CoverageGap(claim.claim_id, "evidence_unavailable"))
        elif any(item.status is EvidenceStatus.FAILED for item in supporting):
            status = ClaimStatus.CONFLICTED
            confidence = Confidence(min(item.confidence.value for item in supporting), "conflict")
            gaps.append(CoverageGap(claim.claim_id, "conflicting_evidence"))
        elif missing:
            status = ClaimStatus.PARTIAL
            confidence = Confidence(min(item.confidence.value for item in supporting), "partial")
            gaps.append(CoverageGap(claim.claim_id, "referenced_evidence_missing"))
        else:
            external = any(item.external for item in supporting)
            status = ClaimStatus.SUPPORTED_EXTERNAL if external else ClaimStatus.SUPPORTED_PROJECT
            confidence = Confidence(
                min(item.confidence.value for item in supporting), "weakest supporting evidence"
            )
        evaluated.append(
            EvaluatedClaim(
                claim.claim_id,
                claim.text,
                claim.evidence_ids,
                status,
                confidence,
                verified_project_fact=(
                    status is ClaimStatus.SUPPORTED_PROJECT
                    and all(item.status is EvidenceStatus.VERIFIED for item in supporting)
                ),
            )
        )
    supported = sum(
        item.status in {ClaimStatus.SUPPORTED_EXTERNAL, ClaimStatus.SUPPORTED_PROJECT}
        for item in evaluated
    )
    return ResearchEvaluation(
        tuple(evaluated),
        tuple(gaps),
        RetrievalDeficit(len(claims), supported, len(gaps)),
    )
