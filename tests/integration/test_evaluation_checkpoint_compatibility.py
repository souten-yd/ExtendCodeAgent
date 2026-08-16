from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from extendcodeagent.evaluation import EvaluationTrace, EvaluationTraceLog  # noqa: E402
from extendcodeagent.evaluation.compatibility import (  # noqa: E402
    INVALID_PROVENANCE,
    INVALID_PROVIDER_GAP,
    INVALID_SEAL_MISMATCH,
    INVALID_TIMEOUT,
    REPLAY_REQUIRED,
    REUSABLE,
    audit_checkpoint,
    digest,
)

MANIFEST = ROOT / "docs/evaluation/b0a-checkpoint-compatibility-v1.json"
TASK_SUITE = ROOT / "docs/evaluation/task-suite-v1.json"


def _sealed(value: dict[str, Any]) -> dict[str, Any]:
    body = {key: item for key, item in value.items() if key != "seal"}
    return {**body, "seal": {"algorithm": "sha256", "canonical_payload": digest(body)}}


def _schedule_cell(cell_id: str, *, model_tier: str, model_id: str, task_id: str) -> dict[str, Any]:
    tasks = {item["id"]: item for item in json.loads(TASK_SUITE.read_text())["tasks"]}
    task = tasks[task_id]
    arm = cell_id.split("--", 1)[0]
    return {
        "cell_id": cell_id,
        "arm": arm,
        "model_tier": model_tier,
        "model_id": model_id,
        "model_status": "AVAILABLE",
        "repository_id": task["repository_id"],
        "task_id": task_id,
        "task_class": task["task_class"],
        "split": task["split"],
        "repetition": 1,
    }


def _result(cell: dict[str, Any], *, outcome: str, trace_id: str) -> dict[str, Any]:
    resolved = {
        "local-practical": "eca-local-practical/llama",
        "host-default": "opencode/big-pickle",
    }
    return {
        **cell,
        "model_id": resolved[cell["model_tier"]],
        "outcome": outcome,
        "process_exit": 0 if outcome in {"PASS", "FAIL"} else None,
        "oracle_exit": 0 if outcome == "PASS" else 1,
        "errors": [],
        "trace_id": trace_id,
    }


def _append_trace(path: Path, result: dict[str, Any], repository_revision: str) -> None:
    EvaluationTraceLog(path).append(
        EvaluationTrace(
            trace_id=result["trace_id"],
            plan_id="unified-evaluation-matrix-v1",
            cell_id=result["cell_id"],
            task_id=result["task_id"],
            task_class=result["task_class"],
            oracle_id=f"e3-oracle:{result['task_id']}",
            input_seals={
                "layer_a": "70710dfe82680afd8ab0c2ad3a735b7f82648c65554dbf93d878e0550a986427",
                "layer_b": "23bf76039ea1e95a29c31c09823f2501bd3658dea305a4e38868eb9e1e6f6632",
                "matrix": "7bfa9f1dd8be5bf44fcf3f018c4ccbe2b6a3266846cd7a994f08eb5d4886a0c5",
            },
            capability_state_source="planned_matrix",
            capability_modes={},
            capability_depths={},
            used_features={},
            selected_evidence_ids=(),
            source_revision_id=repository_revision,
            twin_revision_id=None,
            model_tier=result["model_tier"],
            model_id=result["model_id"],
            verification_outcome=result["outcome"],
            fallback=None,
        )
    )


def _fixture(tmp_path: Path) -> tuple[Path, list[dict[str, Any]]]:
    raw = tmp_path / "raw"
    trace_path = raw / "traces.jsonl"
    suite = json.loads(TASK_SUITE.read_text())
    repositories = {item["id"]: item["revision"] for item in suite["repositories"]}
    schedule = [
        _schedule_cell(
            "native--local-practical--eca-symbol-001--r1",
            model_tier="local-practical",
            model_id="llama",
            task_id="eca-symbol-001",
        ),
        _schedule_cell(
            "off--host-default--eca-symbol-001--r1",
            model_tier="host-default",
            model_id="opencode/big-pickle",
            task_id="eca-symbol-001",
        ),
        _schedule_cell(
            "native--host-default--eca-impact-001--r1",
            model_tier="host-default",
            model_id="opencode/big-pickle",
            task_id="eca-impact-001",
        ),
    ]
    results = [
        _result(schedule[0], outcome="PASS", trace_id="trace-pass"),
        _result(schedule[1], outcome="TIMEOUT", trace_id="trace-provider"),
        _result(schedule[2], outcome="TIMEOUT", trace_id="trace-timeout"),
    ]
    for result in results:
        _append_trace(trace_path, result, repositories[result["repository_id"]])
    log_dir = raw / "logs"
    log_dir.mkdir(parents=True)
    (log_dir / f"{results[1]['cell_id']}.stderr.log").write_text(
        "AI_RetryError: Failed after 3 attempts. Rate limit exceeded\n"
    )
    manifest = json.loads(MANIFEST.read_text())
    report = {
        "source_revision": manifest["source_runner_revision"],
        "inputs": {"layer_a_seal": manifest["input_seals"]["layer_a"]},
        "schedule": {
            "scope": "b0a-baseline",
            "matrix_seal": manifest["input_seals"]["matrix"],
            "task_suite_seal": manifest["input_seals"]["task_suite"],
            "b0a": {
                "screening_plan_seal": manifest["input_seals"]["screening_plan"],
                "activation_plan_seal": manifest["input_seals"]["activation_plan"],
            },
        },
        "executed_cells": len(results),
        "trace_log": str(trace_path),
        "results": results,
    }
    source = tmp_path / "checkpoint.json"
    source.write_text(json.dumps(report))
    return source, schedule


def test_checkpoint_audit_classifies_success_provider_gap_and_timeout(tmp_path: Path) -> None:
    source, schedule = _fixture(tmp_path)
    audit = audit_checkpoint(ROOT, source, MANIFEST, schedule)
    by_id = {item["cell_id"]: item for item in audit["cells"]}
    assert audit["counts"] == {
        INVALID_PROVIDER_GAP: 1,
        INVALID_TIMEOUT: 1,
        REUSABLE: 1,
    }
    assert by_id["native--local-practical--eca-symbol-001--r1"]["latency_status"] == (
        "LEGACY_RUNNER_LATENCY"
    )
    assert audit["bridge_required_before_migration"] is True
    assert audit["latency_merge_permitted"] is False


def test_checkpoint_audit_rejects_seal_and_repository_provenance_changes(
    tmp_path: Path,
) -> None:
    source, schedule = _fixture(tmp_path)
    report = json.loads(source.read_text())
    report["schedule"]["task_suite_seal"] = "changed"
    source.write_text(json.dumps(report))
    audit = audit_checkpoint(ROOT, source, MANIFEST, schedule)
    assert set(audit["counts"]) == {INVALID_SEAL_MISMATCH}

    source, schedule = _fixture(tmp_path / "repository")
    trace_path = Path(json.loads(source.read_text())["trace_log"])
    envelopes = [json.loads(line) for line in trace_path.read_text().splitlines()]
    envelopes[0]["record"]["source_revision_id"] = "changed"
    trace_path.write_text("\n".join(json.dumps(item) for item in envelopes) + "\n")
    audit = audit_checkpoint(ROOT, source, MANIFEST, schedule)
    assert audit["trace_integrity"].startswith("FAIL:")
    assert audit["counts"][INVALID_PROVENANCE] >= 1

    source, schedule = _fixture(tmp_path / "repository-pin")
    manifest = json.loads(MANIFEST.read_text())
    manifest["repository_revisions"]["extendcodeagent"] = "changed"
    changed = tmp_path / "repository-pin.json"
    changed.write_text(json.dumps(_sealed(manifest)))
    audit = audit_checkpoint(ROOT, source, changed, schedule)
    assert set(audit["counts"]) == {INVALID_SEAL_MISMATCH}


def test_checkpoint_audit_rejects_wrong_oracle_and_trace_input_seals(tmp_path: Path) -> None:
    for field, value in (
        ("oracle_id", "different-oracle"),
        ("input_seals", {"layer_a": "changed", "layer_b": "changed", "matrix": "changed"}),
    ):
        source, schedule = _fixture(tmp_path / field)
        trace_path = Path(json.loads(source.read_text())["trace_log"])
        envelopes = [json.loads(line) for line in trace_path.read_text().splitlines()]
        envelopes[0]["record"][field] = value
        previous_hash = None
        rewritten = []
        for envelope in envelopes:
            envelope["previous_hash"] = previous_hash
            payload = {
                "sequence": envelope["sequence"],
                "previous_hash": previous_hash,
                "record": envelope["record"],
            }
            envelope["record_hash"] = digest(payload)
            previous_hash = envelope["record_hash"]
            rewritten.append(envelope)
        trace_path.write_text("\n".join(json.dumps(item) for item in rewritten) + "\n")
        audit = audit_checkpoint(ROOT, source, MANIFEST, schedule)
        assert audit["counts"][INVALID_PROVENANCE] >= 1


def test_semantic_changes_require_replay_but_runner_only_change_is_compatible(
    tmp_path: Path,
) -> None:
    source, schedule = _fixture(tmp_path)
    compatible = audit_checkpoint(ROOT, source, MANIFEST, schedule)
    assert compatible["counts"][REUSABLE] == 1

    for key in ("model_limits", "eca_core_semantics"):
        manifest = json.loads(MANIFEST.read_text())
        manifest["compatibility"][key] = "CHANGED"
        changed = tmp_path / f"{key}.json"
        changed.write_text(json.dumps(_sealed(manifest)))
        audit = audit_checkpoint(ROOT, source, changed, schedule)
        assert set(audit["counts"]) == {REPLAY_REQUIRED}


def test_incomplete_checkpoint_and_missing_trace_never_reuse(tmp_path: Path) -> None:
    source, schedule = _fixture(tmp_path)
    report = json.loads(source.read_text())
    report["executed_cells"] += 1
    source.write_text(json.dumps(report))
    audit = audit_checkpoint(ROOT, source, MANIFEST, schedule)
    assert set(audit["counts"]) == {"INVALID_INCOMPLETE"}

    source, schedule = _fixture(tmp_path / "missing-trace")
    Path(json.loads(source.read_text())["trace_log"]).unlink()
    audit = audit_checkpoint(ROOT, source, MANIFEST, schedule)
    assert audit["trace_integrity"] == "FAIL:MISSING"
    assert audit["counts"][INVALID_PROVENANCE] == 1
