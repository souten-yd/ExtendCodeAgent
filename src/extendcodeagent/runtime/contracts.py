"""Host-neutral runtime observations and truthful reconciliation results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from extendcodeagent.core.contracts import (
    CanonicalRef,
    EvidenceRef,
    ProjectRef,
    Provenance,
    SourceRevision,
)


class ObservationKind(StrEnum):
    TEST = "test"
    LINT = "lint"
    BUILD = "build"
    TYPECHECK = "typecheck"
    SMOKE = "smoke"
    BENCHMARK = "benchmark"
    RUNTIME = "runtime"


class ObservationStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    OBSERVED = "observed"
    UNAVAILABLE = "unavailable"


class ReconciliationDecision(StrEnum):
    VERIFIED = "verified"
    CONTRADICTED = "contradicted"
    OBSERVED = "observed"
    STALE = "stale"
    UNAVAILABLE = "unavailable"
    NOT_OBSERVED = "not_observed"


@dataclass(frozen=True, slots=True)
class RuntimeObservation:
    observation_id: str
    kind: ObservationKind
    project: ProjectRef
    source_revision: SourceRevision
    status: ObservationStatus
    started_at: datetime
    finished_at: datetime
    provenance: Provenance
    observed_refs: tuple[CanonicalRef, ...] = ()
    command: str | None = None
    tool: str | None = None
    artifacts: tuple[EvidenceRef, ...] = ()
    summary: str = ""

    def __post_init__(self) -> None:
        if not self.observation_id.strip():
            raise ValueError("observation_id must not be empty")
        if self.finished_at < self.started_at:
            raise ValueError("finished_at must not precede started_at")
        if not self.command and not self.tool and self.status is not ObservationStatus.UNAVAILABLE:
            raise ValueError("command or tool is required for an available observation")


@dataclass(frozen=True, slots=True)
class ReconciliationOutcome:
    canonical_ref: CanonicalRef
    source_revision: SourceRevision
    decision: ReconciliationDecision
    verified: bool
    observation_ids: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ObservationRollup:
    success: bool
    passed: int
    failed: int
    observed: int
    unavailable: int
    diagnostics: tuple[str, ...] = ()
