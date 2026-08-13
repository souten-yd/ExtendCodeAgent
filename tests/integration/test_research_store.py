from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from extendcodeagent.core.contracts import Confidence, ProjectRef, Provenance
from extendcodeagent.research import Evidence, SqliteEvidenceRepository
from extendcodeagent.storage import SqliteGraphStore, StoreError


def _project(workspace: str) -> ProjectRef:
    return ProjectRef("project", workspace, "file:///repo")


def _evidence(summary: str = "supported") -> Evidence:
    return Evidence(
        "external:e1",
        "source:s1",
        "hash",
        summary,
        Provenance("https://example.test", "fake", "1"),
        Confidence(0.8),
        datetime(2026, 8, 14, tzinfo=UTC),
    )


def test_evidence_survives_restart_isolates_workspace_and_rejects_collision(
    tmp_path: Path,
) -> None:
    database = tmp_path / "project.db"
    one, two = _project("one"), _project("two")
    with SqliteGraphStore(database) as store:
        repository = SqliteEvidenceRepository(store, one)
        repository.put(_evidence())
        repository.put(_evidence())
        with pytest.raises(StoreError, match="immutable research evidence collision"):
            repository.put(_evidence("different"))

    with SqliteGraphStore(database) as reopened:
        assert SqliteEvidenceRepository(reopened, one).get("external:e1") == _evidence()
        assert SqliteEvidenceRepository(reopened, two).get("external:e1") is None
