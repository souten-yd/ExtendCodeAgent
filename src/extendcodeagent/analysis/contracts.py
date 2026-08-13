"""Host-neutral contracts for bounded graph path and impact queries."""

from __future__ import annotations

from dataclasses import dataclass

from extendcodeagent.core.contracts import Diagnostic
from extendcodeagent.graph import FactStatus, GraphRevision


@dataclass(frozen=True, slots=True)
class PathQuery:
    source_ref: str
    target_ref: str | None = None
    allowed_edge_types: tuple[str, ...] = ()
    statuses: tuple[FactStatus, ...] = (
        FactStatus.DECLARED,
        FactStatus.INFERRED,
        FactStatus.OBSERVED,
        FactStatus.VERIFIED,
    )
    min_confidence: float = 0.0
    max_depth: int = 6
    max_paths: int = 20

    def __post_init__(self) -> None:
        if not self.source_ref:
            raise ValueError("source_ref is required")
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be between zero and one")
        if self.max_depth < 0 or self.max_paths <= 0:
            raise ValueError("path bounds are invalid")


@dataclass(frozen=True, slots=True)
class GraphPath:
    node_refs: tuple[str, ...]
    edge_types: tuple[str, ...]
    min_confidence: float
    contains_inferred: bool
    explanation: str


@dataclass(frozen=True, slots=True)
class PathResult:
    revision: GraphRevision | None
    paths: tuple[GraphPath, ...]
    truncated: bool
    diagnostics: tuple[Diagnostic, ...] = ()


@dataclass(frozen=True, slots=True)
class ImpactQuery:
    changed_refs: tuple[str, ...]
    min_confidence: float = 0.0
    max_depth: int = 6
    include_historical: bool = False
    forward_implementation_edges: tuple[str, ...] = ("handled_by",)

    def __post_init__(self) -> None:
        if not self.changed_refs or any(not item for item in self.changed_refs):
            raise ValueError("changed_refs must not be empty")
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be between zero and one")
        if self.max_depth < 0:
            raise ValueError("max_depth must not be negative")


@dataclass(frozen=True, slots=True)
class ImpactItem:
    canonical_ref: str
    item_type: str
    status: FactStatus
    confidence: float
    path_confidence: float
    source_ref: str
    reason: str


@dataclass(frozen=True, slots=True)
class ImpactReport:
    revision: GraphRevision | None
    direct_impacts: tuple[ImpactItem, ...] = ()
    transitive_impacts: tuple[ImpactItem, ...] = ()
    affected_requirements: tuple[ImpactItem, ...] = ()
    side_effects: tuple[ImpactItem, ...] = ()
    recommended_tests: tuple[ImpactItem, ...] = ()
    historical_risks: tuple[ImpactItem, ...] = ()
    uncertainty: tuple[ImpactItem, ...] = ()
    explanation_paths: tuple[GraphPath, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
