from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from extendcodeagent.core.contracts import (
    CanonicalRef,
    ProjectRef,
    Provenance,
    SourceRevision,
)
from extendcodeagent.runtime import ObservationKind, ObservationStatus, RuntimeObservation
from extendcodeagent.storage import SqliteGraphStore, StoreError

NOW = datetime(2026, 8, 13, tzinfo=UTC)


def _project(workspace: str) -> ProjectRef:
    return ProjectRef("project", workspace, "file:///repo")


def _observation(
    project: ProjectRef, *, status: ObservationStatus = ObservationStatus.PASSED
) -> RuntimeObservation:
    revision = SourceRevision("rev-1")
    return RuntimeObservation(
        "obs-1",
        ObservationKind.TEST,
        project,
        revision,
        status,
        NOW,
        NOW,
        Provenance("tool", "pytest", "1", revision),
        observed_refs=(CanonicalRef("py://service#handler"),),
        command="pytest",
    )


def test_runtime_observations_are_idempotent_restart_safe_and_ref_indexed(tmp_path: Path) -> None:
    database = tmp_path / "graph.db"
    project = _project("one")
    with SqliteGraphStore(database) as store:
        assert store.put_observation(_observation(project)) is True
        assert store.put_observation(_observation(project)) is False
    with SqliteGraphStore(database) as reopened:
        values = reopened.observations(project, refs=(CanonicalRef("py://service#handler"),))
        assert len(values) == 1
        assert values[0].status is ObservationStatus.PASSED
        assert reopened.observations(project, refs=(CanonicalRef("py://missing"),)) == ()


def test_runtime_observations_reject_id_collision_and_isolate_workspaces(tmp_path: Path) -> None:
    with SqliteGraphStore(tmp_path / "graph.db") as store:
        one = _project("one")
        two = _project("two")
        store.put_observation(_observation(one))
        store.put_observation(_observation(two))
        with pytest.raises(StoreError, match="observation_id collision"):
            store.put_observation(_observation(one, status=ObservationStatus.FAILED))
        assert len(store.observations(one)) == 1
        assert len(store.observations(two)) == 1
