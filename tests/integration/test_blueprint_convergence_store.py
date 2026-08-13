from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from extendcodeagent.blueprint import (
    BlueprintElement,
    BlueprintService,
    BlueprintStatus,
    SqliteBlueprintRepository,
)
from extendcodeagent.convergence import (
    ActualElement,
    ActualSnapshot,
    ConvergenceDecision,
    SqliteConvergenceRepository,
    TargetElement,
    TargetSnapshot,
    decide_convergence,
    evaluate_convergence,
)
from extendcodeagent.core.contracts import CanonicalRef, ProjectRef, SourceRevision, TwinRevisionRef
from extendcodeagent.storage import SqliteGraphStore

NOW = datetime(2026, 8, 13, tzinfo=UTC)


def _project(workspace: str) -> ProjectRef:
    return ProjectRef("project", workspace, "file:///repo")


def test_blueprint_lifecycle_and_convergence_report_survive_restart_and_isolate_workspaces(
    tmp_path: Path,
) -> None:
    database = tmp_path / "project.db"
    one = _project("one")
    two = _project("two")
    element = BlueprintElement(
        "service",
        CanonicalRef("bp://service"),
        "file",
        expected_actual_refs=(CanonicalRef("file://service.py"),),
    )
    with SqliteGraphStore(database) as store:
        blueprints = BlueprintService(SqliteBlueprintRepository(store), now=lambda: NOW)
        created = blueprints.create(one, (element,))
        other = blueprints.create(two, (element,))
        assert created is not None and other is not None
        blueprints.review(one, created.revision.revision_id)
        blueprints.approve(one, created.revision.revision_id)
        blueprints.activate(one, created.revision.revision_id)

        target = TargetSnapshot(
            one,
            created.revision.revision_id,
            (
                TargetElement(
                    "service",
                    CanonicalRef("bp://service"),
                    (CanonicalRef("file://service.py"),),
                    requires_verification=False,
                ),
            ),
        )
        actual = ActualSnapshot(
            one,
            TwinRevisionRef("twin-1", SourceRevision("source-1")),
            (ActualElement(CanonicalRef("file://service.py"), "file"),),
        )
        report = evaluate_convergence(target, actual, ())
        SqliteConvergenceRepository(store).put(report, decide_convergence(report))

    with SqliteGraphStore(database) as reopened:
        blueprints = BlueprintService(SqliteBlueprintRepository(reopened), now=lambda: NOW)
        active = blueprints.active(one)
        assert active is not None and active.status is BlueprintStatus.ACTIVE
        assert blueprints.active(two) is None
        stored = SqliteConvergenceRepository(reopened).latest(one)
        assert stored is not None
        assert stored[0] == report
        assert stored[1].decision is ConvergenceDecision.COMPLETE
        assert SqliteConvergenceRepository(reopened).latest(two) is None
