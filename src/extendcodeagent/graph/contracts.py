"""Immutable graph facts and revision envelopes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from types import MappingProxyType

from extendcodeagent.core.contracts import (
    CanonicalRef,
    Confidence,
    EvidenceRef,
    ProjectRef,
    Provenance,
    SourceRevision,
)


class FactStatus(StrEnum):
    DECLARED = "declared"
    INFERRED = "inferred"
    OBSERVED = "observed"
    VERIFIED = "verified"
    SUPERSEDED = "superseded"
    INVALIDATED = "invalidated"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class GraphNode:
    node_id: str
    canonical_ref: CanonicalRef
    node_type: str
    source_ref: str
    provenance: Provenance
    confidence: Confidence
    status: FactStatus
    revision: SourceRevision
    properties: Mapping[str, object] = field(default_factory=dict)
    evidence: tuple[EvidenceRef, ...] = ()

    def __post_init__(self) -> None:
        if not self.node_id or not self.node_type or not self.source_ref:
            raise ValueError("node id, type, and source_ref are required")
        object.__setattr__(self, "properties", MappingProxyType(dict(self.properties)))


@dataclass(frozen=True, slots=True)
class GraphEdge:
    edge_id: str
    source: CanonicalRef
    target: CanonicalRef
    edge_type: str
    source_ref: str
    provenance: Provenance
    confidence: Confidence
    status: FactStatus
    revision: SourceRevision
    properties: Mapping[str, object] = field(default_factory=dict)
    evidence: tuple[EvidenceRef, ...] = ()

    def __post_init__(self) -> None:
        if not self.edge_id or not self.edge_type or not self.source_ref:
            raise ValueError("edge id, type, and source_ref are required")
        object.__setattr__(self, "properties", MappingProxyType(dict(self.properties)))


@dataclass(frozen=True, slots=True)
class GraphEvidence:
    evidence_id: str
    evidence_type: str
    source_ref: str
    provenance: Provenance
    confidence: Confidence
    status: FactStatus
    revision: SourceRevision
    summary: str = ""


@dataclass(frozen=True, slots=True)
class GraphRevision:
    revision_id: str
    project: ProjectRef
    source_revision: SourceRevision
    worktree_fingerprint: str
    analyzer_versions: Mapping[str, str]
    created_at: datetime = field(default_factory=utcnow)
    parent_revision_id: str | None = None

    def __post_init__(self) -> None:
        if not self.revision_id or not self.worktree_fingerprint:
            raise ValueError("revision_id and worktree_fingerprint are required")
        object.__setattr__(
            self, "analyzer_versions", MappingProxyType(dict(self.analyzer_versions))
        )


@dataclass(frozen=True, slots=True)
class GraphDelta:
    project: ProjectRef
    source_revision: SourceRevision
    worktree_fingerprint: str
    idempotency_key: str
    analyzer_versions: Mapping[str, str]
    nodes: tuple[GraphNode, ...] = ()
    edges: tuple[GraphEdge, ...] = ()
    evidence: tuple[GraphEvidence, ...] = ()
    invalidate_node_ids: tuple[str, ...] = ()
    invalidate_edge_ids: tuple[str, ...] = ()
    expected_revision_id: str | None = None

    def __post_init__(self) -> None:
        if not self.idempotency_key or not self.worktree_fingerprint:
            raise ValueError("idempotency_key and worktree_fingerprint are required")
        object.__setattr__(
            self, "analyzer_versions", MappingProxyType(dict(self.analyzer_versions))
        )


@dataclass(frozen=True, slots=True)
class GraphSnapshot:
    project: ProjectRef
    revision: GraphRevision | None
    nodes: tuple[GraphNode, ...] = ()
    edges: tuple[GraphEdge, ...] = ()
    evidence: tuple[GraphEvidence, ...] = ()
