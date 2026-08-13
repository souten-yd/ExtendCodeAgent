"""Small shared contracts that are safe for every Project Intelligence domain."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType


class ContractError(ValueError):
    """Raised when a shared contract violates a structural invariant."""


class FreshnessPolicy(StrEnum):
    REQUIRED = "required"
    BEST_EFFORT = "best_effort"
    STALE_OK = "stale_ok"


class EvidenceStatus(StrEnum):
    OBSERVED = "observed"
    VERIFIED = "verified"
    FAILED = "failed"
    STALE = "stale"
    UNAVAILABLE = "unavailable"


class DiagnosticSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


def _required(value: str, field_name: str) -> None:
    if not value.strip():
        raise ContractError(f"{field_name} must not be empty")


@dataclass(frozen=True, slots=True)
class ProjectRef:
    project_id: str
    workspace_id: str
    root_uri: str
    repository_id: str | None = None
    branch: str | None = None
    source_revision: str | None = None
    worktree_fingerprint: str | None = None

    def __post_init__(self) -> None:
        _required(self.project_id, "project_id")
        _required(self.workspace_id, "workspace_id")
        _required(self.root_uri, "root_uri")


@dataclass(frozen=True, slots=True)
class SourceRevision:
    value: str
    kind: str = "git"

    def __post_init__(self) -> None:
        _required(self.value, "source revision")
        _required(self.kind, "source revision kind")


@dataclass(frozen=True, slots=True)
class TwinRevisionRef:
    revision_id: str
    source_revision: SourceRevision

    def __post_init__(self) -> None:
        _required(self.revision_id, "twin revision_id")


@dataclass(frozen=True, slots=True)
class CanonicalRef:
    value: str

    def __post_init__(self) -> None:
        _required(self.value, "canonical ref")


@dataclass(frozen=True, slots=True)
class Confidence:
    value: float
    rationale: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ContractError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class Provenance:
    source: str
    producer: str
    producer_version: str
    source_revision: SourceRevision | None = None
    attributes: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _required(self.source, "provenance source")
        _required(self.producer, "provenance producer")
        _required(self.producer_version, "provenance producer_version")
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    evidence_id: str
    status: EvidenceStatus
    revision: SourceRevision | None = None

    def __post_init__(self) -> None:
        _required(self.evidence_id, "evidence_id")


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    message: str
    severity: DiagnosticSeverity = DiagnosticSeverity.INFO
    refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _required(self.code, "diagnostic code")
        _required(self.message, "diagnostic message")


@dataclass(frozen=True, slots=True)
class QueryBounds:
    max_items: int = 100
    max_depth: int = 6

    def __post_init__(self) -> None:
        if self.max_items <= 0:
            raise ContractError("max_items must be positive")
        if self.max_depth < 0:
            raise ContractError("max_depth must not be negative")
