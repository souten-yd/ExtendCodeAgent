"""Requirement-to-project evidence contracts."""

from __future__ import annotations

from dataclasses import dataclass

from extendcodeagent.convergence import ConvergenceRecommendation, ConvergenceReport
from extendcodeagent.core.contracts import CanonicalRef, EvidenceRef, SourceRevision


@dataclass(frozen=True, slots=True)
class Requirement:
    requirement_id: str
    description: str
    expected_actual_refs: tuple[CanonicalRef, ...]
    mandatory: bool = True
    requires_verification: bool = True


@dataclass(frozen=True, slots=True)
class RequirementEvidence:
    requirement_id: str
    actual_refs: tuple[CanonicalRef, ...]
    evidence: tuple[EvidenceRef, ...]
    source_revision: SourceRevision | None
    external: bool = False


@dataclass(frozen=True, slots=True)
class ProjectRequirementReport:
    convergence: ConvergenceReport
    recommendation: ConvergenceRecommendation
