from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from pytest import MonkeyPatch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/local"))

import b0a_bootstrap  # type: ignore[import-not-found]  # noqa: E402

HARNESS = ROOT / "tools/local/b0a-bootstrap"
PLAN = ROOT / "docs/evaluation/b0a-screening-plan-v1.json"


def _slow_bootstrap(*_args: object) -> dict[str, object]:
    time.sleep(5)
    return {}


def test_screening_contract_is_sealed_and_assigns_every_capability_once() -> None:
    result = subprocess.run(
        [str(HARNESS), "validate"], cwd=ROOT, text=True, capture_output=True, check=False
    )
    assert result.returncode == 0, result.stderr
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    assert plan["screening"]["effect_threshold"]["minimum_absolute_pass_rate_delta"] == 2 / 21
    assert len(plan["screening"]["capability_model_tiers"]) == 13
    assert set(plan["decision_policy"]["forbidden"]) == {"promote", "demote", "reject"}


def test_pinned_existing_project_bootstrap_is_truthful(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=source, check=True)
    (source / "pyproject.toml").write_text("[tool.pytest.ini_options]\n", encoding="utf-8")
    (source / "sample.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
    tests = source / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text(
        "from sample import answer\n\ndef test_answer():\n    assert answer() == 42\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=source, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=B0a",
            "-c",
            "user.email=b0a@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=source,
        check=True,
    )
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    repository = {
        "id": "fixture",
        "repository": str(source),
        "revision": revision,
        "role": "test",
        "source_manifest": "fixture",
    }

    acquired = b0a_bootstrap.acquire(repository, tmp_path / "corpus")
    result = b0a_bootstrap.bootstrap(repository, acquired, tmp_path / "state")

    assert result["eligibility"] == "INCLUDED"
    assert result["source_revision"] == {
        "expected": revision,
        "observed": revision,
        "exact": True,
    }
    assert result["twin"]["revision_id"]
    assert result["twin"]["nodes"] >= 3
    assert result["discovery"]["test_runners"] == {"status": "inferred", "items": ["pytest"]}
    assert result["discovery"]["test_inventory"] == {"status": "inferred", "count": 1}
    assert result["baseline_evidence"]["correctness"] == "unknown"

    (acquired / "uncommitted.txt").write_text("preserve me\n", encoding="utf-8")
    reacquired = b0a_bootstrap.acquire(repository, tmp_path / "corpus")
    archived = list((tmp_path / "corpus/archive").glob("fixture-*/uncommitted.txt"))
    assert len(archived) == 1
    assert archived[0].read_text(encoding="utf-8") == "preserve me\n"
    assert not (reacquired / "uncommitted.txt").exists()

    monkeypatch.setattr(b0a_bootstrap, "bootstrap", _slow_bootstrap)
    monkeypatch.setattr(b0a_bootstrap, "environment", lambda: {})
    output = tmp_path / "timeout-report.json"
    b0a_bootstrap.run_bootstraps(
        [repository],
        tmp_path / "timeout-run",
        output,
        timeout_seconds=1,
        resume=False,
    )
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["summary"] == {"attempted": 1, "included": 0, "excluded_bootstrap_gap": 1}
    assert report["repositories"][0]["gap_reason"] == "twin_timeout"
    assert (tmp_path / "timeout-run/checkpoints/fixture.json").is_file()
