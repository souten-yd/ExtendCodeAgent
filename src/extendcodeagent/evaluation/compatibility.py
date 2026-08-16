"""Strict checkpoint compatibility audit for evaluation-only result migration."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from extendcodeagent.evaluation import EvaluationTraceLog
from extendcodeagent.evaluation.trace import TraceIntegrityError

REUSABLE = "REUSABLE"
REPLAY_REQUIRED = "REPLAY_REQUIRED"
INVALID_PROVIDER_GAP = "INVALID_PROVIDER_GAP"
INVALID_TIMEOUT = "INVALID_TIMEOUT"
INVALID_INCOMPLETE = "INVALID_INCOMPLETE"
INVALID_SEAL_MISMATCH = "INVALID_SEAL_MISMATCH"
INVALID_PROVENANCE = "INVALID_PROVENANCE"

PROVIDER_MARKERS = (
    "Rate limit exceeded",
    "AI_RetryError",
    "AI_APICallError",
    "AuthenticationError",
    "ProviderModelNotFoundError",
)


class CompatibilityError(ValueError):
    """The manifest or source checkpoint cannot support a safe audit."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def verify_seal(value: dict[str, Any], label: str) -> None:
    body = {key: item for key, item in value.items() if key != "seal"}
    expected = {"algorithm": "sha256", "canonical_payload": digest(body)}
    if value.get("seal") != expected:
        raise CompatibilityError(f"{label} seal does not match canonical payload")


def git_tree_fingerprint(root: Path, revision: str, pathspecs: list[str]) -> str:
    process = subprocess.run(
        ["git", "ls-tree", "-r", revision, "--", *pathspecs],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode:
        raise CompatibilityError(f"cannot fingerprint {revision}: {process.stderr.strip()}")
    lines = sorted(line for line in process.stdout.splitlines() if line)
    return hashlib.sha256(("\n".join(lines) + ("\n" if lines else "")).encode()).hexdigest()


def _provider_text(result: dict[str, Any], raw_root: Path) -> str:
    parts = [json.dumps(result.get("errors", []), ensure_ascii=False)]
    cell_id = str(result.get("cell_id", ""))
    for suffix in (".jsonl", ".stderr.log"):
        path = raw_root / "logs" / f"{cell_id}{suffix}"
        if path.is_file():
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def _trace_reason(
    result: dict[str, Any],
    trace_by_id: dict[str, Any],
    repositories: dict[str, str],
    expected_input_seals: dict[str, str],
) -> str | None:
    trace = trace_by_id.get(str(result.get("trace_id", "")))
    if trace is None:
        return "trace_missing"
    if trace.cell_id != result.get("cell_id"):
        return "trace_cell_mismatch"
    if trace.task_id != result.get("task_id") or trace.task_class != result.get("task_class"):
        return "trace_task_mismatch"
    if trace.model_tier != result.get("model_tier") or trace.model_id != result.get("model_id"):
        return "trace_model_mismatch"
    if trace.verification_outcome != result.get("outcome"):
        return "trace_outcome_mismatch"
    if trace.oracle_id != f"e3-oracle:{result.get('task_id')}":
        return "trace_oracle_mismatch"
    if dict(trace.input_seals) != expected_input_seals:
        return "trace_input_seal_mismatch"
    expected_revision = repositories.get(str(result.get("repository_id")))
    if expected_revision is None or trace.source_revision_id != expected_revision:
        return "trace_repository_revision_mismatch"
    return None


def _global_compatibility(
    root: Path, source: dict[str, Any], manifest: dict[str, Any]
) -> tuple[str | None, list[str]]:
    reasons: list[str] = []
    required_unchanged = {
        "eca_core_semantics": "UNCHANGED",
        "opencode_adapter_semantics": "UNCHANGED",
        "task_suite": "IDENTICAL",
        "oracles": "IDENTICAL",
        "repository_pins": "IDENTICAL",
        "model_limits": "IDENTICAL",
    }
    semantic_contract_changes = [
        key
        for key, expected in required_unchanged.items()
        if manifest.get("compatibility", {}).get(key) != expected
    ]
    reasons.extend(f"semantic_contract_changed:{key}" for key in semantic_contract_changes)
    if source.get("source_revision") != manifest["source_runner_revision"]:
        reasons.append("source_runner_revision_mismatch")
    task_suite = json.loads((root / manifest["artifacts"]["task_suite"]).read_text())
    observed_repositories = {
        item["id"]: item["revision"] for item in task_suite.get("repositories", [])
    }
    if observed_repositories != manifest["repository_revisions"]:
        reasons.append("repository_pin_manifest_mismatch")
    expected_seals = {
        key: manifest["input_seals"][key]
        for key in ("matrix", "task_suite", "layer_a", "screening_plan", "activation_plan")
    }
    schedule = source.get("schedule", {})
    inputs = source.get("inputs", {})
    observed_seals = {
        "matrix": schedule.get("matrix_seal"),
        "task_suite": schedule.get("task_suite_seal"),
        "layer_a": inputs.get("layer_a_seal"),
        "screening_plan": schedule.get("b0a", {}).get("screening_plan_seal"),
        "activation_plan": schedule.get("b0a", {}).get("activation_plan_seal"),
    }
    if observed_seals != expected_seals:
        reasons.append("input_seal_mismatch")
    for item in manifest["semantic_fingerprints"]:
        source_actual = git_tree_fingerprint(
            root, manifest["source_runner_revision"], item["pathspecs"]
        )
        target_actual = git_tree_fingerprint(
            root, manifest["target_runner_revision"], item["pathspecs"]
        )
        if source_actual != item["source"] or target_actual != item["target"]:
            reasons.append(f"semantic_fingerprint_manifest_mismatch:{item['id']}")
        elif source_actual != target_actual:
            reasons.append(f"semantic_change:{item['id']}")
    changed = subprocess.check_output(
        [
            "git",
            "diff",
            "--name-only",
            manifest["source_runner_revision"],
            manifest["target_runner_revision"],
        ],
        cwd=root,
        text=True,
    ).splitlines()
    declared = sorted(
        path for group in manifest["change_classification"] for path in group["files"]
    )
    if sorted(changed) != declared:
        reasons.append("changed_file_classification_mismatch")
    if semantic_contract_changes or any(
        reason.startswith("semantic_change:") for reason in reasons
    ):
        return REPLAY_REQUIRED, reasons
    if reasons:
        return INVALID_SEAL_MISMATCH, reasons
    return None, []


def audit_checkpoint(
    root: Path,
    source_path: Path,
    manifest_path: Path,
    expected_schedule_cells: list[dict[str, Any]],
) -> dict[str, Any]:
    source = json.loads(source_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    verify_seal(manifest, "compatibility manifest")
    global_classification, global_reasons = _global_compatibility(root, source, manifest)
    results = source.get("results", [])
    if not isinstance(results, list):
        raise CompatibilityError("source checkpoint results must be a list")
    if any(not isinstance(item, dict) for item in results):
        raise CompatibilityError("source checkpoint result must be an object")
    if source.get("executed_cells") != len(results):
        global_classification = INVALID_INCOMPLETE
        global_reasons = [*global_reasons, "executed_cell_count_mismatch"]
    result_ids = [str(item.get("cell_id", "")) for item in results if isinstance(item, dict)]
    duplicate_ids = {cell_id for cell_id, count in Counter(result_ids).items() if count > 1}

    task_suite_path = root / manifest["artifacts"]["task_suite"]
    task_suite = json.loads(task_suite_path.read_text(encoding="utf-8"))
    tasks = {item["id"]: item for item in task_suite["tasks"]}
    repositories = {item["id"]: item["revision"] for item in task_suite["repositories"]}
    task_fingerprints = manifest["task_fingerprints"]
    expected_trace_seals = {
        key: manifest["input_seals"][key] for key in ("layer_a", "layer_b", "matrix")
    }
    raw_root = Path(str(source.get("trace_log", ""))).parent
    trace_path = raw_root / "traces.jsonl"
    try:
        if not trace_path.is_file():
            raise FileNotFoundError(trace_path)
        traces = EvaluationTraceLog(trace_path).replay()
        trace_by_id = {item.trace_id: item for item in traces}
        trace_integrity = "PASS"
    except FileNotFoundError:
        trace_by_id = {}
        trace_integrity = "FAIL:MISSING"
    except (TraceIntegrityError, OSError) as error:
        trace_by_id = {}
        trace_integrity = f"FAIL:{type(error).__name__}"

    evidence_path = root / manifest["artifacts"]["provider_gap_evidence"]
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence_hash = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    if evidence_hash != manifest["provider_gap_evidence_sha256"]:
        raise CompatibilityError("provider-gap evidence hash mismatch")
    known_provider_gaps = set(evidence["superseded_checkpoint"].get("affected_observed_cells", []))
    schedule_by_id = {item["cell_id"]: item for item in expected_schedule_cells}
    cells: list[dict[str, Any]] = []
    for result in results:
        cell_id = str(result.get("cell_id", ""))
        reasons: list[str] = []
        classification = REUSABLE
        if global_classification is not None:
            classification = global_classification
            reasons.extend(global_reasons)
        elif cell_id in duplicate_ids:
            classification = INVALID_PROVENANCE
            reasons.append("duplicate_cell_result")
        elif cell_id not in schedule_by_id:
            classification = INVALID_PROVENANCE
            reasons.append("cell_not_in_source_schedule")
        elif any(
            result.get(key) != schedule_by_id[cell_id].get(key)
            for key in (
                "arm",
                "model_tier",
                "model_status",
                "repository_id",
                "task_id",
                "task_class",
                "split",
                "repetition",
            )
        ):
            classification = INVALID_PROVENANCE
            reasons.append("cell_schedule_fields_mismatch")
        elif result.get("model_id") != manifest["resolved_model_ids"].get(result.get("model_tier")):
            classification = INVALID_PROVENANCE
            reasons.append("resolved_model_id_mismatch")
        elif result.get("task_id") not in tasks:
            classification = INVALID_PROVENANCE
            reasons.append("task_not_in_sealed_suite")
        elif digest(tasks[str(result["task_id"])]) != task_fingerprints.get(result["task_id"]):
            classification = INVALID_SEAL_MISMATCH
            reasons.append("task_fingerprint_mismatch")
        else:
            provider_text = _provider_text(result, raw_root)
            if cell_id in known_provider_gaps or any(
                marker in provider_text for marker in PROVIDER_MARKERS
            ):
                classification = INVALID_PROVIDER_GAP
                reasons.append("provider_gap_evidence")
            elif result.get("outcome") == "TIMEOUT":
                classification = INVALID_TIMEOUT
                reasons.append("task_timeout")
            elif result.get("outcome") == "UNAVAILABLE":
                if result.get("model_status") != "UNAVAILABLE":
                    classification = INVALID_PROVIDER_GAP
                    reasons.append("available_model_reported_unavailable")
                elif result.get("reason") != "sealed model-tier status":
                    classification = INVALID_PROVENANCE
                    reasons.append("unavailable_reason_mismatch")
            elif result.get("outcome") not in {"PASS", "FAIL"}:
                classification = INVALID_INCOMPLETE
                reasons.append("unsupported_or_incomplete_outcome")
            elif result.get("process_exit") is None or result.get("oracle_exit") is None:
                classification = INVALID_INCOMPLETE
                reasons.append("execution_or_oracle_incomplete")
            if classification == REUSABLE:
                trace_reason = _trace_reason(
                    result, trace_by_id, repositories, expected_trace_seals
                )
                if trace_reason:
                    classification = INVALID_PROVENANCE
                    reasons.append(trace_reason)
        latency_status = (
            "NOT_APPLICABLE"
            if result.get("model_status") == "UNAVAILABLE"
            else "LEGACY_RUNNER_LATENCY"
        )
        cells.append(
            {
                "cell_id": cell_id,
                "classification": classification,
                "reasons": reasons,
                "functional_result_reusable": classification == REUSABLE,
                "latency_status": latency_status,
                "task_id": result.get("task_id"),
                "task_class": result.get("task_class"),
                "model_tier": result.get("model_tier"),
                "model_id": result.get("model_id"),
                "arm": result.get("arm"),
                "source_outcome": result.get("outcome"),
                "source_trace_id": result.get("trace_id"),
                "source_result_sha256": digest(result),
            }
        )
    counts = Counter(item["classification"] for item in cells)
    manifest_reference = (
        str(manifest_path.relative_to(root))
        if manifest_path.is_relative_to(root)
        else str(manifest_path.resolve())
    )
    report = {
        "schema": 1,
        "classification": "EVALUATION_CHECKPOINT_COMPATIBILITY_AUDIT",
        "source_checkpoint": str(source_path.resolve()),
        "source_checkpoint_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "source_trace_log_sha256": (
            hashlib.sha256(trace_path.read_bytes()).hexdigest() if trace_path.is_file() else None
        ),
        "source_runner_revision": source.get("source_revision"),
        "target_runner_revision": manifest["target_runner_revision"],
        "validated_by_runner_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "compatibility_manifest": manifest_reference,
        "compatibility_manifest_seal": manifest["seal"]["canonical_payload"],
        "trace_integrity": trace_integrity,
        "source_cells": len(results),
        "counts": dict(sorted(counts.items())),
        "bridge_required_before_migration": True,
        "latency_merge_permitted": False,
        "cells": cells,
    }
    return {
        **report,
        "seal": {"algorithm": "sha256", "canonical_payload": digest(report)},
    }
