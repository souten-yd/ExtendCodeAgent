"""Blueprint repository adapter for the shared SQLite store."""

from __future__ import annotations

from extendcodeagent.core.contracts import ProjectRef
from extendcodeagent.storage.sqlite import SqliteGraphStore

from .contracts import BlueprintRevision, BlueprintStatus


class SqliteBlueprintRepository:
    def __init__(self, store: SqliteGraphStore) -> None:
        self._store = store

    def save_revision(self, revision: BlueprintRevision) -> None:
        self._store.put_blueprint_revision(revision)

    def get_revision(self, project: ProjectRef, revision_id: str) -> BlueprintRevision | None:
        return self._store.blueprint_revision(project, revision_id)

    def status(self, project: ProjectRef, revision_id: str) -> BlueprintStatus | None:
        return self._store.blueprint_status(project, revision_id)

    def set_status(self, project: ProjectRef, revision_id: str, status: BlueprintStatus) -> None:
        self._store.set_blueprint_status(project, revision_id, status)

    def set_active(self, project: ProjectRef, revision_id: str) -> None:
        self._store.set_active_blueprint(project, revision_id)

    def active_revision_id(self, project: ProjectRef) -> str | None:
        return self._store.active_blueprint_revision_id(project)

    def revisions(self, project: ProjectRef) -> tuple[BlueprintRevision, ...]:
        return self._store.blueprint_revisions(project)
