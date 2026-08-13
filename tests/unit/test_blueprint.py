from __future__ import annotations

from datetime import UTC, datetime

import pytest

from extendcodeagent.blueprint import (
    BlueprintElement,
    BlueprintError,
    BlueprintService,
    BlueprintStatus,
    InMemoryBlueprintRepository,
)
from extendcodeagent.core.contracts import CanonicalRef, ProjectRef, SourceRevision, TwinRevisionRef

NOW = datetime(2026, 8, 13, tzinfo=UTC)
PROJECT = ProjectRef("project", "workspace", "file:///repo")
TWIN = TwinRevisionRef("twin-1", SourceRevision("source-1"))


def _element(element_id: str = "service") -> BlueprintElement:
    return BlueprintElement(
        element_id,
        CanonicalRef(f"bp://{element_id}"),
        "file",
        expected_actual_refs=(CanonicalRef(f"file://{element_id}.py"),),
        acceptance_criteria=("focused test passes",),
    )


def test_planned_elements_cannot_claim_actual_project_refs() -> None:
    with pytest.raises(BlueprintError, match="planned namespace"):
        BlueprintElement("service", CanonicalRef("file://service.py"), "file")


def test_revision_payload_is_immutable_and_lifecycle_moves_only_operational_state() -> None:
    repository = InMemoryBlueprintRepository()
    service = BlueprintService(repository, now=lambda: NOW)
    created = service.create(PROJECT, (_element(),), source_twin_revision=TWIN)
    assert created is not None and created.status is BlueprintStatus.PROPOSED

    reviewed = service.review(PROJECT, created.revision.revision_id)
    approved = service.approve(PROJECT, created.revision.revision_id)
    active = service.activate(PROJECT, created.revision.revision_id)

    assert reviewed.status is BlueprintStatus.REVIEWED
    assert approved.status is BlueprintStatus.APPROVED
    assert active.status is BlueprintStatus.ACTIVE
    assert repository.get_revision(PROJECT, created.revision.revision_id) == created.revision
    assert created.revision.status is BlueprintStatus.PROPOSED


def test_revise_creates_child_and_activation_supersedes_prior_without_rewriting_it() -> None:
    service = BlueprintService(InMemoryBlueprintRepository(), now=lambda: NOW)
    first = service.create(PROJECT, (_element(),), source_twin_revision=TWIN)
    assert first is not None
    service.review(PROJECT, first.revision.revision_id)
    service.approve(PROJECT, first.revision.revision_id)
    service.activate(PROJECT, first.revision.revision_id)

    child = service.revise(
        PROJECT,
        first.revision.revision_id,
        (_element(), _element("worker")),
    )
    assert child.revision.parent_revision_id == first.revision.revision_id
    assert first.revision.elements == (_element(),)
    service.review(PROJECT, child.revision.revision_id)
    service.approve(PROJECT, child.revision.revision_id)
    service.activate(PROJECT, child.revision.revision_id)

    assert service.get(PROJECT, first.revision.revision_id).status is BlueprintStatus.SUPERSEDED
    assert service.active(PROJECT).revision == child.revision  # type: ignore[union-attr]


def test_invalid_or_unreviewed_blueprint_cannot_activate() -> None:
    service = BlueprintService(InMemoryBlueprintRepository(), now=lambda: NOW)
    created = service.create(
        PROJECT,
        (
            BlueprintElement(
                "worker",
                CanonicalRef("bp://worker"),
                "file",
                depends_on_element_ids=("missing",),
            ),
        ),
    )
    assert created is not None
    with pytest.raises(BlueprintError, match="validation"):
        service.review(PROJECT, created.revision.revision_id)
    with pytest.raises(BlueprintError, match="approved"):
        service.activate(PROJECT, created.revision.revision_id)


def test_simple_task_can_bypass_durable_blueprint() -> None:
    repository = InMemoryBlueprintRepository()
    service = BlueprintService(repository, now=lambda: NOW)
    assert service.create(PROJECT, (_element(),), durable=False) is None
    assert repository.revisions(PROJECT) == ()
