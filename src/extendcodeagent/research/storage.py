"""Research evidence repository backed by the shared project SQLite store."""

from __future__ import annotations

from extendcodeagent.core.contracts import ProjectRef
from extendcodeagent.storage.sqlite import SqliteGraphStore

from .contracts import Evidence


class SqliteEvidenceRepository:
    def __init__(self, store: SqliteGraphStore, project: ProjectRef) -> None:
        self._store = store
        self._project = project

    def put(self, evidence: Evidence) -> None:
        self._store.put_research_evidence(self._project, evidence)

    def get(self, evidence_id: str) -> Evidence | None:
        return self._store.research_evidence(self._project, evidence_id)
