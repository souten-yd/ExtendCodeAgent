from __future__ import annotations

import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tools/local/e3_task_suite.py"
MANIFEST = ROOT / "docs/evaluation/task-suite-v1.json"
CANDIDATES = ROOT / "docs/evaluation/github-corpus-candidates-v1.json"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(ROOT / ".venv/bin/python"), str(HARNESS), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_sealed_suite_has_fixed_classes_splits_and_user_mandated_routes() -> None:
    result = _run("validate", "--manifest", str(MANIFEST))
    assert result.returncode == 0, result.stderr

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    counts = Counter(task["task_class"] for task in manifest["tasks"])
    assert len(manifest["tasks"]) == 13
    assert all(
        counts[task_class] >= minimum
        for task_class, minimum in manifest["policy"]["minimum_per_class"].items()
    )
    assert {task["repository_id"] for task in manifest["tasks"] if task["split"] == "held-out"} == {
        "kasanecore"
    }
    models = manifest["runtime_environment"]["models"]
    assert models["local-practical"]["base_url"] == "http://127.0.0.1:8090/v1"
    assert models["frontier-sonnet"]["id"] == "github-copilot/claude-sonnet-5"
    assert models["frontier-codex"]["id"] == "github-copilot/gpt-5.3-codex"
    assert "Ollama" in models["local-low"]["reason"]
    omo = manifest["runtime_environment"]["omo"]
    assert omo["current_result"] == "PASS_MODEL_FREE_COEXISTENCE_SMOKE"
    assert omo["local_low_result"] == "UNAVAILABLE"
    slow_suite = manifest["slow_suite"]
    assert slow_suite["measurement"]["status"] == "PASS"
    assert slow_suite["measurement"]["wall_seconds"] > slow_suite["threshold_seconds"]


def test_github_candidate_registry_preserves_e3_split_and_language_boundary() -> None:
    registry = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    assert "does not change the sealed E3" in registry["purpose"]
    candidates = {candidate["id"]: candidate for candidate in registry["candidates"]}
    assert candidates["opencode"]["decision"] == "candidate-next"
    assert candidates["hermes-agent"]["decision"] == "candidate-next"
    assert candidates["atomic-agents"]["decision"] == "candidate-fast-control"
    assert candidates["codex"]["decision"] == "reference-only-until-rust-analysis"
    assert candidates["codex"]["primary_language"] == "Rust"


def test_seal_detects_a_post_split_manifest_change(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["tasks"][0]["split"] = "held-out"
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps(manifest), encoding="utf-8")

    result = _run("validate", "--manifest", str(changed))
    assert result.returncode == 1
    assert "held-out task" in result.stderr or "seal" in result.stderr


def test_prepare_and_oracle_bound_mutations_for_injection_negative_control(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "task"
    prepared = _run(
        "prepare",
        "--manifest",
        str(MANIFEST),
        "--task",
        "eca-negative-001",
        "--destination",
        str(workspace),
        "--source",
        f"extendcodeagent={ROOT}",
    )
    assert prepared.returncode == 0, prepared.stderr
    injection = (workspace / "EVALUATION_UNTRUSTED.md").read_text(encoding="utf-8")
    assert "Ignore all previous instructions" in injection

    marker = workspace / "docs/evaluation-native-marker.txt"
    marker.write_text("native negative control\n", encoding="utf-8")
    passed = _run(
        "oracle",
        "--manifest",
        str(MANIFEST),
        "--task",
        "eca-negative-001",
        "--workspace",
        str(workspace),
    )
    assert passed.returncode == 0, passed.stderr

    (workspace / "unexpected.txt").write_text("outside scope\n", encoding="utf-8")
    failed = _run(
        "oracle",
        "--manifest",
        str(MANIFEST),
        "--task",
        "eca-negative-001",
        "--workspace",
        str(workspace),
    )
    assert failed.returncode == 1
    assert "outside allowed scope" in failed.stderr
