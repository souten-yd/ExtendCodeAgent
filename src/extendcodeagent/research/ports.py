"""Ports implemented by local, MCP, OpenCode-hosted, or remote infrastructure."""

from __future__ import annotations

from typing import Protocol

from .contracts import Claim, Evidence, ResearchPlan, SourceCandidate


class SearchPort(Protocol):
    def search(self, query: str, *, limit: int) -> tuple[SourceCandidate, ...]: ...


class FetchPort(Protocol):
    def fetch(self, candidate: SourceCandidate) -> bytes: ...


class ExtractPort(Protocol):
    def extract(self, candidate: SourceCandidate, content: bytes) -> Evidence: ...


class EvidenceRepository(Protocol):
    def put(self, evidence: Evidence) -> None: ...

    def get(self, evidence_id: str) -> Evidence | None: ...


class SynthesisPort(Protocol):
    def synthesize(
        self, plan: ResearchPlan, evidence: tuple[Evidence, ...]
    ) -> tuple[Claim, ...]: ...
