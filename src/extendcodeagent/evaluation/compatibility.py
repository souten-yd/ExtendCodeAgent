"""Strict checkpoint compatibility audit for evaluation-only result migration."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import UTC, datetime
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


def create_bridge_plan(root: Path, audit_path: Path, manifest_path: Path) -> dict[str, Any]:
    """Select one reusable source cell for every required model/task pair."""
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    verify_seal(audit, "checkpoint audit")
    verify_seal(manifest, "compatibility manifest")
    if audit.get("compatibility_manifest_seal") != manifest["seal"]["canonical_payload"]:
        raise CompatibilityError("audit and compatibility manifest seals differ")
    policy = manifest["bridge_sample_policy"]
    required_models = list(policy["required_model_tiers"])
    required_tasks = dict(policy["required_tasks"])
    reusable = [item for item in audit.get("cells", []) if item.get("classification") == REUSABLE]
    selected: list[dict[str, Any]] = []
    missing: list[str] = []
    for model_tier in required_models:
        for task_id, task_class in required_tasks.items():
            candidates = [
                item
                for item in reusable
                if item.get("model_tier") == model_tier
                and item.get("task_id") == task_id
                and item.get("task_class") == task_class
            ]
            candidates.sort(
                key=lambda item: (
                    item.get("arm") != "native",
                    str(item.get("cell_id", "")),
                )
            )
            if not candidates:
                missing.append(f"{model_tier}:{task_id}")
                continue
            selected.append(
                {
                    key: candidates[0][key]
                    for key in (
                        "cell_id",
                        "model_tier",
                        "model_id",
                        "task_id",
                        "task_class",
                        "arm",
                        "source_outcome",
                        "source_result_sha256",
                    )
                }
            )
    if missing:
        raise CompatibilityError(f"bridge coverage has no reusable source cells: {missing}")
    if not policy["minimum_cells"] <= len(selected) <= policy["maximum_cells"]:
        raise CompatibilityError("bridge cell count is outside sealed policy")
    current_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    report = {
        "schema": 1,
        "classification": "EVALUATION_CHECKPOINT_BRIDGE_PLAN",
        "bridge_runner_revision": current_revision,
        "audit": str(audit_path.resolve()),
        "audit_seal": audit["seal"]["canonical_payload"],
        "compatibility_manifest": (
            str(manifest_path.relative_to(root))
            if manifest_path.is_relative_to(root)
            else str(manifest_path.resolve())
        ),
        "compatibility_manifest_seal": manifest["seal"]["canonical_payload"],
        "source_checkpoint": audit["source_checkpoint"],
        "source_checkpoint_sha256": audit["source_checkpoint_sha256"],
        "policy": policy,
        "cells": selected,
    }
    return {**report, "seal": {"algorithm": "sha256", "canonical_payload": digest(report)}}


def prove_bridge(
    bridge_plan_path: Path, bridge_run_path: Path, source_checkpoint_path: Path
) -> dict[str, Any]:
    """Compare rerun semantics with immutable source cells and seal the proof."""
    bridge_plan = json.loads(bridge_plan_path.read_text(encoding="utf-8"))
    bridge_run = json.loads(bridge_run_path.read_text(encoding="utf-8"))
    source = json.loads(source_checkpoint_path.read_text(encoding="utf-8"))
    verify_seal(bridge_plan, "bridge plan")
    verify_seal(bridge_run, "bridge run")
    if bridge_run.get("bridge_plan_seal") != bridge_plan["seal"]["canonical_payload"]:
        raise CompatibilityError("bridge run does not match bridge plan")
    if hashlib.sha256(source_checkpoint_path.read_bytes()).hexdigest() != bridge_plan.get(
        "source_checkpoint_sha256"
    ):
        raise CompatibilityError("bridge source checkpoint hash mismatch")
    old_by_id = {item["cell_id"]: item for item in source.get("results", [])}
    new_by_id = {item["cell_id"]: item for item in bridge_run.get("results", [])}
    comparisons: list[dict[str, Any]] = []
    replay_classes: set[str] = set()
    unavailable_classes: set[str] = set()
    fields = (
        "outcome",
        "process_exit",
        "oracle_exit",
        "model_id",
        "pi_tools",
        "pi_capabilities_used",
        "observed_capability_modes",
        "observed_capability_depths",
        "observed_pi_readiness",
    )
    attribution_fields = ("schema_valid", "final_exact_pass")
    for planned in bridge_plan["cells"]:
        cell_id = planned["cell_id"]
        class_key = f"{planned['model_tier']}:{planned['task_class']}"
        old = old_by_id.get(cell_id)
        new = new_by_id.get(cell_id)
        mismatches: list[str] = []
        if old is None:
            raise CompatibilityError(f"bridge source result is missing: {cell_id}")
        elif digest(old) != planned["source_result_sha256"]:
            raise CompatibilityError(f"bridge source result hash mismatch: {cell_id}")
        if new is None:
            comparison_status = "INCOMPLETE"
            unavailable_classes.add(class_key)
        elif new.get("outcome") not in {"PASS", "FAIL"}:
            comparison_status = "UNAVAILABLE"
            unavailable_classes.add(class_key)
            mismatches.append("bridge_provider_or_execution_gap")
        else:
            comparison_status = "MATCH"
        if old is not None and new is not None and comparison_status == "MATCH":
            mismatches.extend(field for field in fields if old.get(field) != new.get(field))
            old_attr = old.get("outcome_attribution", {})
            new_attr = new.get("outcome_attribution", {})
            mismatches.extend(
                f"outcome_attribution.{field}"
                for field in attribution_fields
                if old_attr.get(field) != new_attr.get(field)
            )
        if comparison_status == "MATCH" and mismatches:
            comparison_status = "MISMATCH"
            replay_classes.add(class_key)
        comparisons.append(
            {
                "cell_id": cell_id,
                "model_tier": planned["model_tier"],
                "task_class": planned["task_class"],
                "status": comparison_status,
                "mismatches": sorted(set(mismatches)),
            }
        )
    status = (
        "PASS"
        if not replay_classes and not unavailable_classes
        else "PARTIAL"
        if comparisons
        else "FAIL"
    )
    matched_classes = sorted(
        {
            f"{item['model_tier']}:{item['task_class']}"
            for item in comparisons
            if item["status"] == "MATCH"
        }
    )
    required_models = set(bridge_plan["policy"]["required_model_tiers"])
    unavailable_models = {item.split(":", 1)[0] for item in unavailable_classes}
    matched_models = {item.split(":", 1)[0] for item in matched_classes}
    migration_models = sorted((required_models & matched_models) - unavailable_models)
    report = {
        "schema": 1,
        "classification": "EVALUATION_CHECKPOINT_BRIDGE_PROOF",
        "status": status,
        "migration_permitted": status == "PASS",
        "partial_migration_permitted": bool(matched_classes),
        "latency_merge_permitted": False,
        "bridge_plan": str(bridge_plan_path.resolve()),
        "bridge_plan_seal": bridge_plan["seal"]["canonical_payload"],
        "bridge_run": str(bridge_run_path.resolve()),
        "bridge_run_seal": bridge_run["seal"]["canonical_payload"],
        "source_checkpoint_sha256": bridge_plan["source_checkpoint_sha256"],
        "matched_cells": sum(item["status"] == "MATCH" for item in comparisons),
        "total_cells": len(comparisons),
        "replay_required_classes": sorted(replay_classes),
        "unavailable_classes": sorted(unavailable_classes),
        "migration_permitted_classes": matched_classes,
        "migration_permitted_model_tiers": migration_models,
        "bridge_unavailable_model_tiers": sorted(unavailable_models),
        "comparisons": comparisons,
    }
    return {**report, "seal": {"algorithm": "sha256", "canonical_payload": digest(report)}}


def migrate_checkpoint(
    root: Path,
    source_path: Path,
    audit_path: Path,
    bridge_proof_path: Path,
    trace_output_path: Path,
) -> dict[str, Any]:
    """Copy only bridge-authorized functional cells into a current-run checkpoint."""
    source = json.loads(source_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    proof = json.loads(bridge_proof_path.read_text(encoding="utf-8"))
    verify_seal(audit, "checkpoint audit")
    verify_seal(proof, "bridge proof")
    bridge_plan_path = Path(str(proof.get("bridge_plan", "")))
    if not bridge_plan_path.is_file():
        raise CompatibilityError("migration bridge plan is missing")
    bridge_plan = json.loads(bridge_plan_path.read_text(encoding="utf-8"))
    verify_seal(bridge_plan, "bridge plan")
    if proof.get("bridge_plan_seal") != bridge_plan["seal"]["canonical_payload"]:
        raise CompatibilityError("migration proof and bridge plan seals differ")
    if bridge_plan.get("audit_seal") != audit["seal"]["canonical_payload"]:
        raise CompatibilityError("migration audit and bridge plan seals differ")
    if bridge_plan.get("compatibility_manifest_seal") != audit.get("compatibility_manifest_seal"):
        raise CompatibilityError("migration compatibility manifest seals differ")
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if source_hash != audit.get("source_checkpoint_sha256"):
        raise CompatibilityError("migration source does not match checkpoint audit")
    if source_hash != proof.get("source_checkpoint_sha256"):
        raise CompatibilityError("migration source does not match bridge proof")
    if audit.get("trace_integrity") != "PASS":
        raise CompatibilityError("migration requires valid source trace integrity")
    if proof.get("partial_migration_permitted") is not True:
        raise CompatibilityError("bridge proof permits no migration")
    current_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    reusable_by_id = {
        item["cell_id"]: item
        for item in audit.get("cells", [])
        if item.get("classification") == REUSABLE
    }
    permitted_models = set(proof.get("migration_permitted_model_tiers", []))
    replay_classes = set(proof.get("replay_required_classes", []))
    migrated: list[dict[str, Any]] = []
    migrated_ids: set[str] = set()
    for result in source.get("results", []):
        cell_id = result.get("cell_id")
        audited = reusable_by_id.get(cell_id)
        if audited is None:
            continue
        class_key = f"{result.get('model_tier')}:{result.get('task_class')}"
        sealed_unavailable = (
            result.get("model_status") == "UNAVAILABLE"
            and result.get("outcome") == "UNAVAILABLE"
            and result.get("reason") == "sealed model-tier status"
        )
        if not sealed_unavailable and (
            result.get("model_tier") not in permitted_models or class_key in replay_classes
        ):
            continue
        migrated.append(
            {
                **result,
                "result_origin": "migrated_checkpoint",
                "original_runner_revision": audit["source_runner_revision"],
                "validated_by_runner_revision": current_revision,
                "compatibility_manifest": audit["compatibility_manifest"],
                "compatibility_proof": str(bridge_proof_path.resolve()),
                "compatibility_proof_seal": proof["seal"]["canonical_payload"],
                "original_result_sha256": audited["source_result_sha256"],
                "latency_status": ("NOT_APPLICABLE" if sealed_unavailable else "LEGACY_RUNNER"),
            }
        )
        migrated_ids.add(str(cell_id))
    source_trace_path = Path(str(source["trace_log"]))
    if hashlib.sha256(source_trace_path.read_bytes()).hexdigest() != audit.get(
        "source_trace_log_sha256"
    ):
        raise CompatibilityError("migration source trace hash mismatch")
    source_traces = EvaluationTraceLog(source_trace_path).replay()
    migrated_trace_ids = {item.get("trace_id") for item in migrated}
    selected_traces = [item for item in source_traces if item.trace_id in migrated_trace_ids]
    if len(selected_traces) != len(migrated):
        raise CompatibilityError("migration trace coverage is incomplete")
    if trace_output_path.exists():
        raise CompatibilityError("migration trace output already exists")
    trace_output_path.parent.mkdir(parents=True, exist_ok=True)
    migrated_trace_log = EvaluationTraceLog(trace_output_path)
    for trace in selected_traces:
        migrated_trace_log.append(trace)
    body = {
        **{key: value for key, value in source.items() if key not in {"results", "outcomes"}},
        "source_revision": current_revision,
        "captured_at": datetime.now(UTC).isoformat(),
        "trace_log": str(trace_output_path.resolve()),
        "executed_cells": len(migrated),
        "outcomes": dict(sorted(Counter(item["outcome"] for item in migrated).items())),
        "results": migrated,
        "result_origin": "migrated_checkpoint",
        "original_runner_revision": audit["source_runner_revision"],
        "validated_by_runner_revision": current_revision,
        "compatibility_manifest": audit["compatibility_manifest"],
        "compatibility_audit": str(audit_path.resolve()),
        "compatibility_audit_seal": audit["seal"]["canonical_payload"],
        "compatibility_proof": str(bridge_proof_path.resolve()),
        "compatibility_proof_seal": proof["seal"]["canonical_payload"],
        "latency_status": "LEGACY_RUNNER_SEPARATE",
        "latency_merge_permitted": False,
        "activation_evidence": None,
        "pilot_evidence": None,
        "migration_summary": {
            "migrated_cells": len(migrated),
            "source_reusable_cells": len(reusable_by_id),
            "remaining_schedule_cells": int(
                source.get("schedule", {}).get("counts", {}).get("cells", audit["source_cells"])
            )
            - len(migrated_ids),
            "replay_required_classes": sorted(replay_classes),
            "bridge_unavailable_model_tiers": proof.get("bridge_unavailable_model_tiers", []),
        },
    }
    return {**body, "seal": {"algorithm": "sha256", "canonical_payload": digest(body)}}
