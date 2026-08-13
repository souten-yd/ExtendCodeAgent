from __future__ import annotations

from pathlib import Path

import pytest

from extendcodeagent.core.config import ConfigLayer, ConfigResolver
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.service import CapabilityUnavailable, ProjectIntelligenceApplication


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _policy(mode: str) -> CapabilityPolicy:
    capabilities = {
        name: mode for name in ("graph", "twin", "semantic", "impact", "test_selection")
    }
    resolved = ConfigResolver().resolve(
        ConfigLayer(
            "test",
            {
                "project_intelligence": {
                    "enabled": mode != "off",
                    "mode": mode,
                    "capabilities": capabilities,
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
        status = application.status()

    assert {item["canonical_ref"] for item in symbols["items"]} == {"py://service#leaf"}
    assert any(item["source"] == "py://service#caller" for item in references["items"])
    assert path["paths"][0]["min_confidence"] == 1.0
    assert any(item["canonical_ref"] == "py://service#caller" for item in impact["direct"])
    assert {item["canonical_ref"] for item in tests["items"]} == {"py://test_service#test_caller"}
    assert status["revision_id"] == symbols["revision_id"] == impact["revision_id"]


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
