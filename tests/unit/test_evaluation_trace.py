from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from extendcodeagent.evaluation import EvaluationTrace, EvaluationTraceLog, TraceIntegrityError


def _trace(trace_id: str = "trace-1", *, arm_mode: str = "active") -> EvaluationTrace:
    return EvaluationTrace(
        trace_id=trace_id,
        plan_id="unified-evaluation-matrix-v1",
        cell_id=f"{arm_mode}--host-default--eca-symbol-001--r1",
        task_id="eca-symbol-001",
        task_class="symbol-reference-lookup",
        oracle_id="e3-oracle:eca-symbol-001",
        input_seals={"layer_a": "a", "layer_b": "b", "matrix": "m"},
        capability_modes={"semantic": arm_mode},
        capability_depths={"semantic": "D2"},
        used_features={
            "evidence_reuse": "D2",
            "oracle_assessment": "D1",
            "environment_selection": "off",
        },
        selected_evidence_ids=("evidence:1",),
        source_revision_id="a" * 40,
        twin_revision_id="revision-1",
        model_tier="host-default",
        model_id="opencode/big-pickle",
        verification_outcome="PASS",
        fallback=None,
        timings_ms={"agent_wall": 10, "pi_analysis": 2},
    )


def test_trace_log_is_append_only_hash_chained_and_replayable(tmp_path: Path) -> None:
    log = EvaluationTraceLog(tmp_path / "trace.jsonl")
    first = _trace()
    second = replace(first, trace_id="trace-2", cell_id="ablation:semantic--host--task--r1")
    log.append(first)
    log.append(second)
    log.append(second)

    replayed = log.replay()
    assert replayed == (first, second)
    envelopes = [json.loads(line) for line in log.path.read_text().splitlines()]
    assert envelopes[0]["previous_hash"] is None
    assert envelopes[1]["previous_hash"] == envelopes[0]["record_hash"]


def test_trace_id_conflict_and_history_tampering_fail_closed(tmp_path: Path) -> None:
    log = EvaluationTraceLog(tmp_path / "trace.jsonl")
    first = _trace()
    log.append(first)
    with pytest.raises(TraceIntegrityError, match="trace_id conflict"):
        log.append(replace(first, verification_outcome="FAIL"))

    content = log.path.read_text(encoding="utf-8").replace('"PASS"', '"FAIL"', 1)
    log.path.write_text(content, encoding="utf-8")
    with pytest.raises(TraceIntegrityError, match="hash mismatch"):
        log.replay()


def test_trace_shape_reserves_verification_features_without_implementing_them() -> None:
    value = _trace().to_dict()
    assert value["used_features"] == {
        "environment_selection": "off",
        "evidence_reuse": "D2",
        "oracle_assessment": "D1",
    }
    assert "prompt" not in value
    assert "transcript" not in value
