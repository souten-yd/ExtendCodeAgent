"""Compact append-only trace for evaluation attribution and replay."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any


class TraceIntegrityError(ValueError):
    """The trace is malformed, conflicting, or no longer append-only."""


def _mapping(value: Mapping[str, str]) -> Mapping[str, str]:
    return MappingProxyType(dict(sorted(value.items())))


def _required(value: str, label: str) -> None:
    if not value.strip():
        raise TraceIntegrityError(f"{label} must not be empty")


@dataclass(frozen=True, slots=True)
class EvaluationTrace:
    """One replayable attribution record, excluding prompts and transcripts."""

    trace_id: str
    plan_id: str
    cell_id: str
    task_id: str
    task_class: str
    oracle_id: str
    input_seals: Mapping[str, str]
    capability_modes: Mapping[str, str]
    capability_depths: Mapping[str, str]
    used_features: Mapping[str, str]
    selected_evidence_ids: tuple[str, ...]
    source_revision_id: str
    twin_revision_id: str | None
    model_tier: str
    model_id: str | None
    verification_outcome: str
    fallback: str | None
    timings_ms: Mapping[str, int | None] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for label in (
            "trace_id",
            "plan_id",
            "cell_id",
            "task_id",
            "task_class",
            "oracle_id",
            "source_revision_id",
            "model_tier",
            "verification_outcome",
        ):
            _required(str(getattr(self, label)), label)
        for name in ("input_seals", "capability_modes", "capability_depths", "used_features"):
            object.__setattr__(self, name, _mapping(getattr(self, name)))
        object.__setattr__(self, "selected_evidence_ids", tuple(self.selected_evidence_ids))
        object.__setattr__(
            self, "timings_ms", MappingProxyType(dict(sorted(self.timings_ms.items())))
        )

    def to_dict(self) -> dict[str, Any]:
        value = {
            "trace_id": self.trace_id,
            "plan_id": self.plan_id,
            "cell_id": self.cell_id,
            "task_id": self.task_id,
            "task_class": self.task_class,
            "oracle_id": self.oracle_id,
            "input_seals": dict(self.input_seals),
            "capability_modes": dict(self.capability_modes),
            "capability_depths": dict(self.capability_depths),
            "used_features": dict(self.used_features),
            "selected_evidence_ids": list(self.selected_evidence_ids),
            "source_revision_id": self.source_revision_id,
            "twin_revision_id": self.twin_revision_id,
            "model_tier": self.model_tier,
            "model_id": self.model_id,
            "verification_outcome": self.verification_outcome,
            "fallback": self.fallback,
            "timings_ms": dict(self.timings_ms),
        }
        _reject_sensitive_keys(value)
        return value


class EvaluationTraceLog:
    """Hash-chained JSONL with idempotent append and full replay verification."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def append(self, trace: EvaluationTrace) -> None:
        envelopes = self._envelopes()
        existing = {str(item["record"]["trace_id"]): item["record"] for item in envelopes}
        record = trace.to_dict()
        if trace.trace_id in existing:
            if existing[trace.trace_id] == record:
                return
            raise TraceIntegrityError(f"trace_id conflict: {trace.trace_id}")
        sequence = len(envelopes) + 1
        previous_hash = str(envelopes[-1]["record_hash"]) if envelopes else None
        unsigned = {"sequence": sequence, "previous_hash": previous_hash, "record": record}
        envelope = {**unsigned, "record_hash": _hash(unsigned)}
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(envelope, ensure_ascii=False, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def replay(self) -> tuple[EvaluationTrace, ...]:
        return tuple(EvaluationTrace(**item["record"]) for item in self._envelopes())

    def _envelopes(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        envelopes: list[dict[str, Any]] = []
        previous_hash: str | None = None
        seen: set[str] = set()
        for line_number, line in enumerate(
            self._path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            try:
                envelope = json.loads(line)
            except json.JSONDecodeError as error:
                raise TraceIntegrityError(f"invalid trace JSON at line {line_number}") from error
            if not isinstance(envelope, dict):
                raise TraceIntegrityError(f"trace line {line_number} is not an object")
            unsigned = {
                "sequence": envelope.get("sequence"),
                "previous_hash": envelope.get("previous_hash"),
                "record": envelope.get("record"),
            }
            if unsigned["sequence"] != line_number:
                raise TraceIntegrityError(f"trace sequence mismatch at line {line_number}")
            if unsigned["previous_hash"] != previous_hash:
                raise TraceIntegrityError(f"trace chain mismatch at line {line_number}")
            if envelope.get("record_hash") != _hash(unsigned):
                raise TraceIntegrityError(f"trace hash mismatch at line {line_number}")
            record = unsigned["record"]
            if not isinstance(record, dict):
                raise TraceIntegrityError(f"trace record missing at line {line_number}")
            _reject_sensitive_keys(record)
            trace_id = str(record.get("trace_id", ""))
            if not trace_id or trace_id in seen:
                raise TraceIntegrityError(f"duplicate or empty trace_id at line {line_number}")
            seen.add(trace_id)
            envelopes.append(envelope)
            previous_hash = str(envelope["record_hash"])
        return envelopes


def _hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _reject_sensitive_keys(value: object, path: str = "record") -> None:
    forbidden = {"prompt", "transcript", "messages", "api_key", "authorization", "secret"}
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).casefold()
            if lowered in forbidden or lowered.endswith("_secret"):
                raise TraceIntegrityError(f"sensitive trace field forbidden: {path}.{key}")
            _reject_sensitive_keys(item, f"{path}.{key}")
    elif isinstance(value, list | tuple):
        for index, item in enumerate(value):
            _reject_sensitive_keys(item, f"{path}[{index}]")
