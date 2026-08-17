from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from extendcodeagent.blueprint import BlueprintElement
from extendcodeagent.convergence import ActualElement, ActualSnapshot, ConvergenceDecision
from extendcodeagent.core.config import ConfigLayer, ConfigResolver
from extendcodeagent.core.config.schema import (
    CONFIGURABLE_CAPABILITIES,
    NOT_IMPLEMENTED_CAPABILITIES,
    CapabilityImplementation,
    CapabilityName,
)
from extendcodeagent.core.contracts import (
    CanonicalRef,
    EvidenceRef,
    EvidenceStatus,
    ProjectRef,
    SourceRevision,
    TwinRevisionRef,
)
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.graph import GraphSnapshot
from extendcodeagent.research import ResearchDepth
from extendcodeagent.service import CapabilityUnavailable, ProjectIntelligenceApplication
from extendcodeagent.traceability import Requirement, RequirementEvidence


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _policy(
    mode: str, *, depth: dict[str, object] | None = None, **overrides: str
) -> CapabilityPolicy:
    capabilities = {name.value: mode for name in CONFIGURABLE_CAPABILITIES}
    capabilities.update(overrides)
    resolved = ConfigResolver().resolve(
        ConfigLayer(
            "test",
            {
                "project_intelligence": {
                    "enabled": mode != "off",
                    "mode": mode,
                    "capabilities": capabilities,
                    **({"depth": depth} if depth is not None else {}),
                }
            },
        )
    )
    return CapabilityPolicy.from_config(resolved.project_intelligence)


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root, "service.py", "def leaf():\n    return 1\n\ndef caller():\n    return leaf()\n")
    _write(
        root,
        "test_service.py",
        "from service import caller\n\ndef test_caller():\n    assert caller() == 1\n",
    )
    return root


def test_off_is_inert_and_does_not_create_a_database(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    database = tmp_path / "graph.db"
    with ProjectIntelligenceApplication(root, database, _policy("off")) as application:
        assert application.status()["readiness"] == "disabled"
        assert application.process_event(("service.py",), "file.edited")["accepted"] is False
        with pytest.raises(CapabilityUnavailable):
            application.symbol("leaf")
    assert not database.exists()


def test_task_signal_records_shadow_plan_without_project_or_model_work(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    database = tmp_path / "graph.db"
    with ProjectIntelligenceApplication(root, database, _policy("shadow")) as application:
        application.connect_runtime(
            runtime_name="test-runtime",
            runtime_version="1",
            declarations=tuple(
                (name, "supported", "")
                for name in (
                    "observe_task",
                    "observe_session",
                    "observe_file_mutation",
                    "observe_tool_execution",
                    "observe_model_route",
                    "observe_verification",
                    "deliver_context",
                    "expose_tools",
                    "request_model",
                    "session_lifecycle",
                    "reconnect",
                    "mcp",
                )
            ),
        )
        result = application.ingest_runtime_signal(
            signal_id="task",
            kind="task",
            observed_at=datetime(2026, 8, 17, tzinfo=UTC),
            runtime_session_id="session",
            task_text="Locate the definition and direct callers of leaf.",
            producer="test-runtime",
            producer_version="1",
        )
        first_plan_id = result["shadow_plan_id"]
        model = application.ingest_runtime_signal(
            signal_id="model",
            kind="model",
            observed_at=datetime(2026, 8, 17, tzinfo=UTC),
            runtime_session_id="session",
            model_provider="local",
            model_id="qwen",
            producer="test-runtime",
            producer_version="1",
        )
        contract = application.runtime_contract()

    assert result["accepted"] is True
    assert result["shadow_plan_id"].startswith("shadow-")
    assert model["shadow_plan_id"] != first_plan_id
    assert contract["shadow_plan"]["intent"]["primary"] == "locate_explain"
    assert contract["shadow_plan"]["capabilities"] == ["graph", "twin", "semantic"]
    assert contract["shadow_plan"]["behavior_changed"] is False
    assert contract["shadow_plan"]["llm_calls"] == 0
    assert not database.exists()


def test_research_plan_and_project_traceability_use_central_policy(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    with ProjectIntelligenceApplication(
        root, tmp_path / "graph.db", _policy("advisory")
    ) as application:
        plan = application.research_plan("SQLite durability", ResearchDepth.MICRO, ("docs",))
        snapshot = application._explicit_snapshot(CapabilityName.TRACEABILITY)  # noqa: SLF001
        assert snapshot.revision is not None
        source = snapshot.revision.source_revision
        report = application.evaluate_project_requirements(
            "requirements-1",
            (Requirement("r1", "service exists", (CanonicalRef("file://service.py"),)),),
            (
                RequirementEvidence(
                    "r1",
                    (CanonicalRef("file://service.py"),),
                    (EvidenceRef("test:e1", EvidenceStatus.VERIFIED, source),),
                    source,
                ),
            ),
        )

    assert plan["max_queries"] == 2
    assert report[1].decision is ConvergenceDecision.COMPLETE


def test_advisory_queries_share_one_revisioned_graph(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    with ProjectIntelligenceApplication(
        root, tmp_path / "graph.db", _policy("advisory")
    ) as application:
        symbols = application.symbol("leaf")
        references = application.references("py://service#leaf")
        path = application.path("py://service#caller", "py://service#leaf")
        impact = application.impact(("py://service#leaf",))
        tests = application.tests(("py://service#leaf",))
        context = application.context("change leaf safely", ("py://service#leaf",), profile="weak")
        status = application.status()

    assert {item["canonical_ref"] for item in symbols["items"]} == {"py://service#leaf"}
    assert any(item["source"] == "py://service#caller" for item in references["items"])
    assert path["paths"][0]["min_confidence"] == 1.0
    assert any(item["canonical_ref"] == "py://service#caller" for item in impact["direct"])
    assert {item["canonical_ref"] for item in tests["items"]} == {"py://test_service#test_caller"}
    assert tests["fallback"] is None
    assert context["items"][0]["canonical_ref"] == "py://service#leaf"
    assert context["used_tokens"] <= context["token_budget"]
    assert status["revision_id"] == symbols["revision_id"] == impact["revision_id"]


def test_compact_views_project_task_ready_facts_and_explicit_gaps(tmp_path: Path) -> None:
    root = tmp_path / "compact"
    root.mkdir()
    _write(root, "pkg/service.py", "def leaf():\n    return 1\n")
    _write(root, "pkg/__init__.py", "from .service import leaf\n")
    _write(root, "app.py", "from pkg import leaf\n\ndef caller():\n    return leaf()\n")
    _write(
        root,
        "tests/test_leaf.py",
        "from app import caller\nfrom pkg import leaf\n\n"
        "def test_leaf():\n    assert leaf() == 1\n\n"
        "def test_caller():\n    assert caller() == 1\n",
    )
    with ProjectIntelligenceApplication(
        root, tmp_path / "compact.db", _policy("advisory")
    ) as application:
        symbol = application.symbol("leaf", view="compact")
        impact = application.impact(("py://pkg.service#leaf",), view="compact")
        tests = application.tests(("py://pkg.service#leaf",), view="compact")

    assert symbol["definition"] == ["pkg/service.py"]
    assert symbol["exports"] == ["pkg/__init__.py"]
    assert "app.py" in symbol["production_callers"]
    assert symbol["tests"] == ["tests/test_leaf.py"]
    assert symbol["coverage_complete"] is False
    assert symbol["unresolved"]
    assert impact["definition"] == ["pkg/service.py"]
    assert impact["production_methods"] == ["caller"]
    assert impact["direct_use_count"] == 1
    assert impact["focused_tests"] == ["tests/test_leaf.py"]
    assert impact["coverage_complete"] is False
    assert tests["selected_tests"] == ["tests/test_leaf.py"]
    assert tests["fallback_search_required"] is True
    assert tests["uncovered_obligations"]


def test_query_view_rejects_unknown_projection(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    with ProjectIntelligenceApplication(
        root, tmp_path / "graph.db", _policy("advisory")
    ) as application:
        with pytest.raises(ValueError, match="view must be compact or detail"):
            application.symbol("leaf", view="unknown")
        with pytest.raises(ValueError, match="view must be compact or detail"):
            application.impact(("py://service#leaf",), view="unknown")
        with pytest.raises(ValueError, match="view must be compact or detail"):
            application.tests(("py://service#leaf",), view="unknown")


def test_compact_tests_project_one_best_test_per_objective_obligation(tmp_path: Path) -> None:
    root = tmp_path / "objective-tests"
    root.mkdir()
    _write(root, "src/pkg/verification.py", "def project():\n    return True\n")
    _write(
        root,
        "tests/unit/test_verification.py",
        "def test_required_verification_projection():\n    assert True\n",
    )
    _write(
        root,
        "tests/unit/test_unrelated.py",
        "def test_unrelated_behavior():\n    assert True\n",
    )
    _write(
        root,
        "tests/integration/test_verification_twin_projection.py",
        "def test_twin_integration_projection():\n    assert True\n",
    )
    _write(
        root,
        "tests/architecture/test_verification_projection.py",
        "def test_no_second_truth_store_architecture_boundary():\n    assert True\n",
    )
    with ProjectIntelligenceApplication(
        root, tmp_path / "objective.db", _policy("advisory")
    ) as application:
        selected = application.tests(
            objective=(
                "required verification projection, Twin integration, and no second truth store "
                "architecture boundary"
            ),
            view="compact",
        )

    assert selected["selected_tests"] == [
        "tests/architecture/test_verification_projection.py",
        "tests/integration/test_verification_twin_projection.py",
        "tests/unit/test_verification.py",
    ]
    assert selected["coverage_complete"] is True
    assert selected["fallback_search_required"] is False


def test_compact_impact_counts_source_uses_and_tests_cover_structural_scope(
    tmp_path: Path,
) -> None:
    root = tmp_path / "obligations"
    root.mkdir()
    _write(root, "src/pkg/checks.py", "def allowed(value):\n    return bool(value)\n")
    _write(
        root,
        "src/pkg/service.py",
        "from src.pkg.checks import allowed\n\n"
        "def validate(left, right):\n"
        "    return allowed(left) and allowed(right)\n",
    )
    _write(
        root,
        "tests/unit/test_checks.py",
        "from src.pkg.checks import allowed\n\ndef test_allowed():\n    assert allowed(1)\n",
    )
    _write(
        root,
        "tests/integration/test_checks.py",
        "from src.pkg.service import validate\n\ndef test_validate():\n    assert validate(1, 2)\n",
    )
    _write(
        root,
        "tests/architecture/test_checks_projection.py",
        "from pathlib import Path\n\n"
        'PACKAGE = Path(__file__).parents[2] / "src" / "pkg"\n\n'
        "def test_package_projection():\n"
        '    assert list(PACKAGE.glob("*.py"))\n',
    )
    changed = ("py://src.pkg.checks#allowed",)
    with ProjectIntelligenceApplication(
        root, tmp_path / "obligations.db", _policy("advisory")
    ) as application:
        impact = application.impact(changed, view="compact")
        selected = application.tests(changed, view="compact")

    assert impact["production_methods"] == ["validate"]
    assert impact["direct_use_count"] == 2
    assert impact["focused_tests"] == [
        "tests/architecture/test_checks_projection.py",
        "tests/integration/test_checks.py",
        "tests/unit/test_checks.py",
    ]
    assert selected["selected_tests"] == impact["focused_tests"]
    assert selected["covered_obligations"] == [
        "architecture_boundary",
        "integration_boundary",
        "unit_behavior",
    ]
    assert selected["coverage_complete"] is True
    assert selected["uncovered_obligations"] == []
    assert selected["fallback_search_required"] is False


def test_revision_query_cache_reuses_and_invalidates_snapshot_and_indexes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repo(tmp_path)
    with ProjectIntelligenceApplication(
        root, tmp_path / "cache.db", _policy("active")
    ) as application:
        first = application.symbol("leaf", view="compact")
        store = application._ensure_store()  # noqa: SLF001
        original_snapshot = store.snapshot
        snapshot_calls = 0

        def counted_snapshot(project: ProjectRef, revision_id: str | None = None) -> GraphSnapshot:
            nonlocal snapshot_calls
            snapshot_calls += 1
            return original_snapshot(project, revision_id)

        monkeypatch.setattr(store, "snapshot", counted_snapshot)
        second = application.symbol("leaf", view="compact")
        snapshot = application._snapshot(open_if_missing=True)  # noqa: SLF001
        first_analysis = application._analysis_service(snapshot)  # noqa: SLF001
        second_analysis = application._analysis_service(snapshot)  # noqa: SLF001

        assert second["revision_id"] == first["revision_id"]
        assert snapshot_calls == 0
        assert first_analysis is second_analysis

        _write(
            root,
            "service.py",
            "def leaf():\n    return 2\n\ndef caller():\n    return leaf()\n",
        )
        refreshed = application.process_event(("service.py",), "file.edited")
        third = application.symbol("leaf", view="compact")

    assert refreshed["revision_id"] == third["revision_id"]
    assert third["revision_id"] != first["revision_id"]
    assert snapshot_calls >= 2


def test_runtime_ingest_persists_and_marks_old_green_test_stale(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    database = tmp_path / "graph.db"
    with ProjectIntelligenceApplication(root, database, _policy("active")) as application:
        before = application.tests(("py://service#leaf",))
        source_revision = application.source_revision()
        recorded = application.ingest_runtime(
            observation_id="pytest-1",
            kind="test",
            status="passed",
            started_at=datetime(2026, 8, 13, tzinfo=UTC),
            finished_at=datetime(2026, 8, 13, tzinfo=UTC),
            observed_refs=("py://test_service#test_caller", "py://service#leaf"),
            command="pytest test_service.py",
            source_revision=source_revision,
        )
        fresh = application.tests(("py://service#leaf",))
        _write(
            root,
            "service.py",
            "def leaf():\n    return 2\n\ndef caller():\n    return leaf()\n",
        )
        application.process_event(("service.py",), "file.edited")
        stale = application.tests(("py://service#leaf",))

    assert before["health"][0]["state"] == "suspect"
    assert recorded["accepted"] is True
    assert fresh["health"][0]["state"] == "healthy"
    assert stale["health"][0]["state"] == "stale"
    with ProjectIntelligenceApplication(root, database, _policy("active")) as reopened:
        evidence = reopened.runtime_evidence(("py://service#leaf",))
    assert evidence["items"][0]["observation_id"] == "pytest-1"


def test_test_obsolescence_switches_off_independently_of_test_selection(tmp_path: Path) -> None:
    """Ablating test_obsolescence must leave test_selection fully working."""

    root = _repo(tmp_path)
    with ProjectIntelligenceApplication(
        root, tmp_path / "graph.db", _policy("active", test_obsolescence="off")
    ) as application:
        selected = application.tests(("py://service#leaf",))

    assert {item["canonical_ref"] for item in selected["items"]} == {
        "py://test_service#test_caller"
    }
    assert selected["health"] == []


def test_test_selection_switches_off_without_disabling_the_rest(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    with ProjectIntelligenceApplication(
        root, tmp_path / "graph.db", _policy("active", test_selection="off")
    ) as application:
        with pytest.raises(CapabilityUnavailable, match="test_selection"):
            application.tests(("py://service#leaf",))
        assert application.impact(("py://service#leaf",))["direct"]


def test_status_reports_implementation_state_and_mode_for_every_capability(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    with ProjectIntelligenceApplication(
        root, tmp_path / "graph.db", _policy("advisory", strategy="off")
    ) as application:
        status = application.status()

    entries = {item["name"]: item for item in status["capabilities"]}
    assert set(entries) == {name.value for name in CapabilityName}
    for name in NOT_IMPLEMENTED_CAPABILITIES:
        assert entries[name.value]["implementation"] == CapabilityImplementation.NOT_IMPLEMENTED
        assert entries[name.value]["mode"] == "off"
    assert entries["impact"]["implementation"] == CapabilityImplementation.IMPLEMENTED
    assert entries["impact"]["mode"] == "advisory"
    assert entries["strategy"]["mode"] == "off"
    assert entries["call_graph"]["governed_by"] == "semantic"
    assert entries["call_graph"]["mode"] == entries["semantic"]["mode"]
    assert entries["impact"]["governed_by"] is None
    # Depth is reported for every capability, including ones that cannot run.
    assert all(item["depth"] == "D2" for item in status["capabilities"])
    assert entries["impact"]["min_inferred_confidence"] == pytest.approx(0.3)
    assert entries["ui_graph"]["depth"] == "D2"


def test_status_reports_capabilities_even_when_disabled(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    database = tmp_path / "graph.db"
    with ProjectIntelligenceApplication(root, database, _policy("off")) as application:
        status = application.status()

    assert status["readiness"] == "disabled"
    assert {item["name"] for item in status["capabilities"]} == {
        name.value for name in CapabilityName
    }
    assert all(item["mode"] == "off" for item in status["capabilities"])
    assert not database.exists()


def test_every_query_response_reports_the_depth_it_ran_at(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    with ProjectIntelligenceApplication(
        root, tmp_path / "graph.db", _policy("advisory")
    ) as application:
        responses = {
            "status": application.status(),
            "symbol": application.symbol("leaf"),
            "references": application.references("py://service#leaf"),
            "path": application.path("py://service#caller", "py://service#leaf"),
            "impact": application.impact(("py://service#leaf",)),
            "tests": application.tests(("py://service#leaf",)),
            "context": application.context("change leaf", ("py://service#leaf",)),
            "runtime_evidence": application.runtime_evidence(),
            "research_plan": application.research_plan("depth contract", ResearchDepth.MICRO),
        }

    for name, response in responses.items():
        expected = None if name == "status" else "D2"
        assert response["depth"] == expected, f"{name} did not report its depth"


def test_response_depth_follows_the_configured_profile(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    with ProjectIntelligenceApplication(
        root,
        tmp_path / "graph.db",
        _policy("advisory", depth={"profile": "quality", "capabilities": {}}),
    ) as application:
        assert application.impact(("py://service#leaf",))["depth"] == "D3"


def test_shallow_depth_drops_inferred_relations_that_deep_depth_keeps(tmp_path: Path) -> None:
    """The E1 `call_graph` folding decision made real: `may_call` is bounded at use time."""

    root = tmp_path / "dynamic"
    root.mkdir()
    _write(
        root,
        "service.py",
        "def leaf():\n    return 1\n\n\ndef caller(obj):\n    return obj.leaf()\n",
    )
    database = tmp_path / "graph.db"

    deep = _policy(
        "advisory",
        depth={
            "profile": "balanced",
            "capabilities": {
                "semantic": {"preferred": "D3"},
                "impact": {"preferred": "D3"},
            },
        },
    )
    with ProjectIntelligenceApplication(root, database, deep) as application:
        deep_paths = application.path("py://service#caller", max_depth=3)
    shallow = _policy(
        "advisory",
        depth={
            "profile": "balanced",
            "capabilities": {
                "semantic": {"preferred": "D1"},
                "impact": {"preferred": "D1"},
            },
        },
    )
    with ProjectIntelligenceApplication(root, database, shallow) as application:
        shallow_paths = application.path("py://service#caller", max_depth=3)

    assert deep_paths["depth"] == "D3"
    assert shallow_paths["depth"] == "D1"
    # D1 requires more confidence than the 0.35 an inferred `may_call` carries.
    assert any("may_call" in item["edge_types"] for item in deep_paths["paths"])
    assert all("may_call" not in item["edge_types"] for item in shallow_paths["paths"])

    with ProjectIntelligenceApplication(root, database, deep) as application:
        assert application.references("pyname://leaf")["items"]
    with ProjectIntelligenceApplication(root, database, shallow) as application:
        assert application.references("pyname://leaf")["items"] == []


def test_a_caller_cannot_widen_below_the_depth_confidence_floor(tmp_path: Path) -> None:
    root = tmp_path / "dynamic-impact"
    root.mkdir()
    _write(root, "service.py", "def caller(obj):\n    return obj.leaf()\n")
    with ProjectIntelligenceApplication(
        root,
        tmp_path / "graph.db",
        _policy(
            "advisory",
            depth={"profile": "balanced", "capabilities": {"impact": {"preferred": "D1"}}},
        ),
    ) as application:
        report = application.impact(("pyname://leaf",), min_confidence=0.0)

    assert report["direct"] == []


def test_runtime_off_is_inert(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    database = tmp_path / "graph.db"
    with ProjectIntelligenceApplication(root, database, _policy("off")) as application:
        result = application.ingest_runtime(
            observation_id="ignored",
            kind="test",
            status="passed",
            started_at=datetime(2026, 8, 13, tzinfo=UTC),
            finished_at=datetime(2026, 8, 13, tzinfo=UTC),
            observed_refs=("py://service#leaf",),
            command="pytest",
            source_revision="rev-1",
        )
    assert result["accepted"] is False
    assert not database.exists()


def test_shadow_computes_events_but_rejects_explicit_queries(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    with ProjectIntelligenceApplication(
        root, tmp_path / "graph.db", _policy("shadow")
    ) as application:
        first = application.process_event(("service.py",), "file.edited")
        _write(root, "service.py", "def replacement():\n    return 2\n")
        second = application.process_event(("service.py",), "file.edited")
        with pytest.raises(CapabilityUnavailable):
            application.impact(("py://service#leaf",))
    assert first["revision_id"] != second["revision_id"]


def test_active_event_refresh_invalidates_removed_symbol(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    with ProjectIntelligenceApplication(
        root, tmp_path / "graph.db", _policy("active")
    ) as application:
        application.process_event(("service.py",), "file.edited")
        _write(root, "service.py", "def replacement():\n    return 2\n")
        refreshed = application.process_event(("service.py",), "file.edited")
        assert application.symbol("leaf")["items"] == []
        assert {item["canonical_ref"] for item in application.symbol("replacement")["items"]} == {
            "py://service#replacement"
        }
    assert refreshed["accepted"] is True


def test_blueprint_and_convergence_use_policy_without_polluting_actual_graph(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    database = tmp_path / "graph.db"
    with ProjectIntelligenceApplication(root, database, _policy("advisory")) as application:
        before = application.status()
        created = application.create_blueprint(
            (
                BlueprintElement(
                    "planned",
                    CanonicalRef("bp://planned"),
                    "file",
                    expected_actual_refs=(CanonicalRef("file://planned.py"),),
                    requires_verification=False,
                ),
            )
        )
        assert created is not None
        after = application.status()
        actual = ActualSnapshot(
            application.project,
            TwinRevisionRef("twin-1", SourceRevision(application.source_revision())),
            (ActualElement(CanonicalRef("file://planned.py"), "file"),),
        )
        _, recommendation = application.evaluate_task_convergence(
            created.revision.revision_id, actual
        )

    assert before["nodes"] == after["nodes"]
    assert recommendation.decision is ConvergenceDecision.COMPLETE


def test_plan_and_verify_routes_use_project_truth_without_overclaiming_evidence(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    with ProjectIntelligenceApplication(
        root, tmp_path / "graph.db", _policy("active")
    ) as application:
        plan = application.plan_change("change leaf safely", ("py://service#leaf",))
        verification = application.verify_requirements(
            (
                Requirement(
                    "leaf-exists",
                    "leaf remains present",
                    (CanonicalRef("py://service#leaf"),),
                ),
            )
        )

    assert plan["capabilities_used"] == ["blueprint", "strategy"]
    assert plan["selected_alternative"] == "focused"
    assert plan["blueprint"]["persisted"] is False
    assert plan["blueprint"]["elements"][0]["expected_actual_refs"] == ["file://service.py"]
    assert verification["capabilities_used"] == ["convergence", "traceability"]
    assert verification["requirements"][0]["state"] == "materialized"
    assert verification["coverage_complete"] is False
    assert verification["unresolved"] == ["leaf-exists"]


def test_composite_routes_fail_when_either_owned_capability_is_off(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    with (
        ProjectIntelligenceApplication(
            root,
            tmp_path / "blueprint-off.db",
            _policy("active", blueprint="off"),
        ) as application,
        pytest.raises(CapabilityUnavailable, match="blueprint"),
    ):
        application.plan_change("change leaf", ("py://service#leaf",))

    with (
        ProjectIntelligenceApplication(
            root,
            tmp_path / "convergence-off.db",
            _policy("active", convergence="off"),
        ) as application,
        pytest.raises(CapabilityUnavailable, match="convergence"),
    ):
        application.verify_requirements(
            (
                Requirement(
                    "leaf-exists",
                    "leaf remains present",
                    (CanonicalRef("py://service#leaf"),),
                ),
            )
        )


def test_blueprint_off_is_inert(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    database = tmp_path / "graph.db"
    with (
        ProjectIntelligenceApplication(root, database, _policy("off")) as application,
        pytest.raises(CapabilityUnavailable),
    ):
        application.create_blueprint(())
    assert not database.exists()
