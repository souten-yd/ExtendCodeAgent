"""Durable convergence report adapter for the shared SQLite store."""

from __future__ import annotations

from extendcodeagent.core.contracts import ProjectRef
from extendcodeagent.storage.sqlite import SqliteGraphStore

from .contracts import ConvergenceRecommendation, ConvergenceReport


class SqliteConvergenceRepository:
    def __init__(self, store: SqliteGraphStore) -> None:
        self._store = store

    def put(self, report: ConvergenceReport, recommendation: ConvergenceRecommendation) -> None:
        self._store.put_convergence(report, recommendation)

    def latest(
        self, project: ProjectRef
    ) -> tuple[ConvergenceReport, ConvergenceRecommendation] | None:
        return self._store.latest_convergence(project)
