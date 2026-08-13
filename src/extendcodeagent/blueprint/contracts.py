"""Immutable host-neutral Blueprint contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from extendcodeagent.core.contracts import CanonicalRef, ProjectRef, TwinRevisionRef


class BlueprintError(ValueError):
    """Raised when a Blueprint contract or lifecycle transition is invalid."""


class BlueprintStatus(StrEnum):
    PROPOSED = "proposed"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    ACTIVE = "active"
    SUPERSEDED = "superseded"


class BlueprintScope(StrEnum):
    FULL_PROJECT = "full_project"
    CHANGE_SET = "change_set"
    REPAIR = "repair"


@dataclass(frozen=True, slots=True)
class BlueprintElement:
    element_id: str
    planned_ref: CanonicalRef
    element_type: str
    mandatory: bool = True
    expected_actual_refs: tuple[CanonicalRef, ...] = ()
    acceptance_criteria: tuple[str, ...] = ()
    depends_on_element_ids: tuple[str, ...] = ()
    requires_verification: bool = True

    def __post_init__(self) -> None:
        if not self.element_id.strip() or not self.element_type.strip():
            raise BlueprintError("element_id and element_type must not be empty")
        if not self.planned_ref.value.startswith(("bp://", "planned://")):
            raise BlueprintError("planned_ref must use a planned namespace")
        if any(
            item.value.startswith(("bp://", "planned://")) for item in self.expected_actual_refs
        ):
            raise BlueprintError("expected_actual_refs must use actual namespaces")


@dataclass(frozen=True, slots=True)
class BlueprintRevision:
    blueprint_id: str
    revision_id: str
    project: ProjectRef
    scope: BlueprintScope
    elements: tuple[BlueprintElement, ...]
    created_at: datetime
    status: BlueprintStatus = BlueprintStatus.PROPOSED
    parent_revision_id: str | None = None
    source_twin_revision: TwinRevisionRef | None = None


@dataclass(frozen=True, slots=True)
class BlueprintView:
    revision: BlueprintRevision
    status: BlueprintStatus
