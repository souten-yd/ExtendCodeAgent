"""Deterministic Blueprint lifecycle with immutable revision payloads."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol

from extendcodeagent.core.contracts import ProjectRef, TwinRevisionRef

from .contracts import (
    BlueprintElement,
    BlueprintError,
    BlueprintRevision,
    BlueprintScope,
    BlueprintStatus,
    BlueprintView,
)


class BlueprintRepository(Protocol):
    def save_revision(self, revision: BlueprintRevision) -> None: ...
    def get_revision(self, project: ProjectRef, revision_id: str) -> BlueprintRevision | None: ...
    def status(self, project: ProjectRef, revision_id: str) -> BlueprintStatus | None: ...
    def set_status(
        self, project: ProjectRef, revision_id: str, status: BlueprintStatus
    ) -> None: ...
    def set_active(self, project: ProjectRef, revision_id: str) -> None: ...
    def active_revision_id(self, project: ProjectRef) -> str | None: ...
    def revisions(self, project: ProjectRef) -> tuple[BlueprintRevision, ...]: ...


class InMemoryBlueprintRepository:
    def __init__(self) -> None:
        self._revisions: dict[tuple[str, str, str], BlueprintRevision] = {}
        self._statuses: dict[tuple[str, str, str], BlueprintStatus] = {}
        self._active: dict[tuple[str, str], str] = {}

    def save_revision(self, revision: BlueprintRevision) -> None:
        key = _revision_key(revision.project, revision.revision_id)
        existing = self._revisions.get(key)
        if existing is not None and existing != revision:
            raise BlueprintError(f"immutable revision collision: {revision.revision_id}")
        self._revisions[key] = revision
        self._statuses.setdefault(key, revision.status)

    def get_revision(self, project: ProjectRef, revision_id: str) -> BlueprintRevision | None:
        return self._revisions.get(_revision_key(project, revision_id))

    def status(self, project: ProjectRef, revision_id: str) -> BlueprintStatus | None:
        return self._statuses.get(_revision_key(project, revision_id))

    def set_status(self, project: ProjectRef, revision_id: str, status: BlueprintStatus) -> None:
        key = _revision_key(project, revision_id)
        if key not in self._revisions:
            raise BlueprintError(f"revision not found: {revision_id}")
        self._statuses[key] = status

    def set_active(self, project: ProjectRef, revision_id: str) -> None:
        if self.get_revision(project, revision_id) is None:
            raise BlueprintError(f"revision not found: {revision_id}")
        self._active[_scope(project)] = revision_id

    def active_revision_id(self, project: ProjectRef) -> str | None:
        return self._active.get(_scope(project))

    def revisions(self, project: ProjectRef) -> tuple[BlueprintRevision, ...]:
        return tuple(value for key, value in self._revisions.items() if key[:2] == _scope(project))


class BlueprintService:
    def __init__(
        self,
        repository: BlueprintRepository,
        *,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self._now = now or (lambda: datetime.now(UTC))

    def create(
        self,
        project: ProjectRef,
        elements: tuple[BlueprintElement, ...],
        *,
        scope: BlueprintScope = BlueprintScope.CHANGE_SET,
        source_twin_revision: TwinRevisionRef | None = None,
        durable: bool = True,
    ) -> BlueprintView | None:
        if not durable:
            return None
        revision = BlueprintRevision(
            f"bp:{uuid.uuid4().hex}",
            f"bprev:{uuid.uuid4().hex}",
            project,
            scope,
            elements,
            self._now(),
            source_twin_revision=source_twin_revision,
        )
        self.repository.save_revision(revision)
        return BlueprintView(revision, BlueprintStatus.PROPOSED)

    def revise(
        self,
        project: ProjectRef,
        parent_revision_id: str,
        elements: tuple[BlueprintElement, ...],
    ) -> BlueprintView:
        parent = self._revision(project, parent_revision_id)
        revision = BlueprintRevision(
            parent.blueprint_id,
            f"bprev:{uuid.uuid4().hex}",
            project,
            parent.scope,
            elements,
            self._now(),
            parent_revision_id=parent.revision_id,
            source_twin_revision=parent.source_twin_revision,
        )
        self.repository.save_revision(revision)
        return BlueprintView(revision, BlueprintStatus.PROPOSED)

    def review(self, project: ProjectRef, revision_id: str) -> BlueprintView:
        revision = self._revision(project, revision_id)
        if self.repository.status(project, revision_id) is not BlueprintStatus.PROPOSED:
            raise BlueprintError("review requires proposed status")
        _validate(revision)
        self.repository.set_status(project, revision_id, BlueprintStatus.REVIEWED)
        return BlueprintView(revision, BlueprintStatus.REVIEWED)

    def approve(self, project: ProjectRef, revision_id: str) -> BlueprintView:
        revision = self._revision(project, revision_id)
        if self.repository.status(project, revision_id) is not BlueprintStatus.REVIEWED:
            raise BlueprintError("approval requires reviewed status")
        self.repository.set_status(project, revision_id, BlueprintStatus.APPROVED)
        return BlueprintView(revision, BlueprintStatus.APPROVED)

    def activate(self, project: ProjectRef, revision_id: str) -> BlueprintView:
        revision = self._revision(project, revision_id)
        if self.repository.status(project, revision_id) is not BlueprintStatus.APPROVED:
            raise BlueprintError("activation requires approved status")
        _validate(revision)
        prior_id = self.repository.active_revision_id(project)
        if prior_id is not None and prior_id != revision_id:
            self.repository.set_status(project, prior_id, BlueprintStatus.SUPERSEDED)
        self.repository.set_status(project, revision_id, BlueprintStatus.ACTIVE)
        self.repository.set_active(project, revision_id)
        return BlueprintView(revision, BlueprintStatus.ACTIVE)

    def get(self, project: ProjectRef, revision_id: str) -> BlueprintView:
        revision = self._revision(project, revision_id)
        status = self.repository.status(project, revision_id)
        if status is None:
            raise BlueprintError(f"status not found: {revision_id}")
        return BlueprintView(revision, status)

    def active(self, project: ProjectRef) -> BlueprintView | None:
        revision_id = self.repository.active_revision_id(project)
        return self.get(project, revision_id) if revision_id else None

    def _revision(self, project: ProjectRef, revision_id: str) -> BlueprintRevision:
        revision = self.repository.get_revision(project, revision_id)
        if revision is None:
            raise BlueprintError(f"revision not found: {revision_id}")
        return revision


def _validate(revision: BlueprintRevision) -> None:
    identifiers = [item.element_id for item in revision.elements]
    known = set(identifiers)
    if len(known) != len(identifiers):
        raise BlueprintError("validation failed: duplicate element_id")
    missing = sorted(
        {dependency for item in revision.elements for dependency in item.depends_on_element_ids}
        - known
    )
    if missing:
        raise BlueprintError(f"validation failed: missing dependencies {missing}")


def _scope(project: ProjectRef) -> tuple[str, str]:
    return project.project_id, project.workspace_id


def _revision_key(project: ProjectRef, revision_id: str) -> tuple[str, str, str]:
    return project.project_id, project.workspace_id, revision_id
