from typing import TYPE_CHECKING

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
    SourceCandidate,
)
from .ports import EvidenceRepository, ExtractPort, FetchPort, SearchPort, SynthesisPort
from .service import build_research_plan, evaluate_claims, execute_research

if TYPE_CHECKING:
    from .storage import SqliteEvidenceRepository


def __getattr__(name: str) -> object:
    if name == "SqliteEvidenceRepository":
        from .storage import SqliteEvidenceRepository

        return SqliteEvidenceRepository
    raise AttributeError(name)


__all__ = [
    "Claim",
    "ClaimStatus",
    "CoverageGap",
    "EvaluatedClaim",
    "Evidence",
    "EvidenceRepository",
    "ExtractPort",
    "FetchPort",
    "ResearchDepth",
    "ResearchEvaluation",
    "ResearchPlan",
    "ResearchRequest",
    "RetrievalDeficit",
    "SearchPort",
    "SqliteEvidenceRepository",
    "SourceCandidate",
    "SynthesisPort",
    "build_research_plan",
    "evaluate_claims",
    "execute_research",
]
