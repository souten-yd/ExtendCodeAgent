"""Real Twin-to-V0a projection integration evidence."""

from __future__ import annotations

from pathlib import Path

from extendcodeagent.analysis import (
    GraphAnalysisService,
    ImpactQuery,
    PythonCanonicalReferenceResolver,
)
from extendcodeagent.core.contracts import ProjectRef
from extendcodeagent.graph.analyzers import PythonGraphAnalyzer
from extendcodeagent.storage import SqliteGraphStore
from extendcodeagent.twin import TwinService
from extendcodeagent.verification import (
    ObligationStatus,
    derive_required_verification_set,
    derive_semantic_change_set,
)


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_real_twin_delta_projects_a_shadow_required_verification_set(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "service.py", "def leaf():\n    return 1\n\ndef caller():\n    return leaf()\n")
    _write(
        root,
        "test_service.py",
        "from service import caller\n\ndef test_caller():\n    assert caller() == 1\n",
    )
    project = ProjectRef("project", "workspace", root.as_uri())

    with SqliteGraphStore(tmp_path / "graph.db") as store:
        twin = TwinService(store, analyzer=PythonGraphAnalyzer())
        first = twin.open(project)
        assert first.revision is not None
        base = twin.snapshot(project, first.revision.revision_id)
        _write(
            root,
            "service.py",
            "def leaf():\n    return 2\n\ndef caller():\n    return leaf()\n",
        )
        twin.refresh(project, changed_paths=("service.py",))
        candidate = twin.snapshot(project)

    change_set = derive_semantic_change_set(base, candidate)
    report = GraphAnalysisService(candidate, PythonCanonicalReferenceResolver()).assess_impact(
        ImpactQuery(tuple(item.value for item in change_set.changed_refs), max_depth=4)
    )
    required = derive_required_verification_set(change_set, report)

    assert "py://service#leaf" in {item.value for item in change_set.changed_refs}
    assert "py://service#leaf" in {item.value for item in change_set.unresolved_refs}
    assert [item.provider_id for item in required.providers] == [
        "test:py://test_service#test_caller"
    ]
    assert all(item.status is ObligationStatus.UNCOVERED for item in required.obligations)
    assert candidate.revision is not None
    assert required.candidate_revision.revision_id == candidate.revision.revision_id
