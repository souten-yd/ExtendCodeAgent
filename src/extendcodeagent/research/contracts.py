"""Host-neutral research domain contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from extendcodeagent.core.contracts import Confidence, EvidenceStatus, ProjectRef, Provenance


class ResearchDepth(StrEnum):
    MICRO = "micro"
    STANDARD = "standard"
    DEEP = "deep"


class ClaimStatus(StrEnum):
    SUPPORTED_EXTERNAL = "supported_external"
    SUPPORTED_PROJECT = "supported_project"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"
    CONFLICTED = "conflicted"


@dataclass(frozen=True, slots=True)
class ResearchRequest:
    request_id: str
    project: ProjectRef
    query: str
    depth: ResearchDepth = ResearchDepth.MICRO
    allow_external: bool = True
    constraints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.request_id.strip() or not self.query.strip():
            raise ValueError("research request_id and query must not be empty")


@dataclass(frozen=True, slots=True)
class ResearchPlan:
    request_id: str
    queries: tuple[str, ...]
    max_queries: int
    max_sources: int
    max_time_seconds: int


@dataclass(frozen=True, slots=True)
class SourceCandidate:
    candidate_id: str
    uri: str
    title: str
    provenance: Provenance
    source_type: str = "web"


@dataclass(frozen=True, slots=True)
class Evidence:
    evidence_id: str
    candidate_id: str
    content_hash: str
    summary: str
    provenance: Provenance
    confidence: Confidence
    retrieved_at: datetime
    status: EvidenceStatus = EvidenceStatus.OBSERVED
    external: bool = True


@dataclass(frozen=True, slots=True)
class Claim:
    claim_id: str
    text: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EvaluatedClaim:
    claim_id: str
    text: str
    evidence_ids: tuple[str, ...]
    status: ClaimStatus
    confidence: Confidence
    verified_project_fact: bool = False


@dataclass(frozen=True, slots=True)
class CoverageGap:
    claim_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class RetrievalDeficit:
    required_claims: int
    supported_claims: int
    missing_evidence: int


@dataclass(frozen=True, slots=True)
class ResearchEvaluation:
    claims: tuple[EvaluatedClaim, ...]
    coverage_gaps: tuple[CoverageGap, ...]
    retrieval_deficit: RetrievalDeficit
