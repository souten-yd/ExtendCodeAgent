"""Consumer-facing serialization and the cost model that must agree with it.

The token budget in a `ContextRequest` only means something if the estimate is taken over
the payload the consumer actually receives. Keeping the emitted shape and the estimator in
one module makes that agreement structural instead of a convention two packages have to
remember.
"""

from __future__ import annotations

import hashlib
import json
from math import ceil
from typing import Any

from .contracts import ContextItem, ContextPackage, WeakLocalEvidencePackage

_CHARS_PER_TOKEN = 4


def canonical_bytes(payload: object) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def estimate_payload_tokens(payload: object) -> int:
    """Estimate model-visible tokens from the canonical form of the emitted payload."""

    return max(1, ceil(len(canonical_bytes(payload)) / _CHARS_PER_TOKEN))


def context_item_json(item: ContextItem) -> dict[str, Any]:
    return {
        "canonical_ref": item.canonical_ref.value,
        "kind": item.kind,
        "summary": item.summary,
        "why_included": item.why_included,
        "confidence": item.confidence,
        "revision": item.revision.value,
        "provenance": {
            "source": item.provenance.source,
            "producer": item.provenance.producer,
            "producer_version": item.provenance.producer_version,
        },
        "token_estimate": item.token_estimate,
        "status": item.status,
    }


def context_package_json(package: ContextPackage) -> dict[str, Any]:
    return {
        "items": [context_item_json(item) for item in package.items],
        "used_tokens": package.used_tokens,
        "token_budget": package.token_budget,
        "truncated": package.truncated,
        "excluded_count": package.excluded_count,
    }


#: What each role has to carry. A test answers with a path, so a path is what it needs;
#: identity, confidence and provenance buy trust that a path list does not spend tokens on.
#: Measured across flask and httpx, the full shape cost 81 tokens per test item.
_ROLE_FIELDS = {
    "test": ("id", "path"),
    "supporting": ("id", "path", "kind", "summary"),
    "consumer": ("id", "path", "kind", "summary", "reason"),
}


def weak_local_evidence_item_json(item: Any) -> dict[str, Any]:
    full = _full_item_json(item)
    fields = _ROLE_FIELDS.get(str(item.role))
    if fields is None:
        return full
    return {key: value for key, value in full.items() if key in fields}


def _full_item_json(item: Any) -> dict[str, Any]:
    return {
        "id": item.evidence_id,
        "ref": item.canonical_ref.value,
        # The canonical ref is ECA's identity; `path` is what an answer has to name. Emitting
        # only the ref made the model translate `py://a.b.c#d` into `a/b/c.py` itself, which
        # is the measured PROJECTION_SCHEMA_ERROR class.
        "path": item.source_ref,
        "kind": item.kind,
        "summary": item.summary,
        "reason": item.reason,
        "confidence": item.confidence,
        "provenance_id": item.provenance_id,
        "status": item.status,
        "role": str(item.role),
        # A symbol's exact span is what lets a consumer read seven lines instead of the
        # three hundred and sixty-seven the file happens to contain.
        **({"lines": [item.start_line, item.end_line]} if item.start_line else {}),
        **({"source": item.excerpt} if item.excerpt else {}),
    }


def weak_local_evidence_json(
    package: WeakLocalEvidencePackage, stable_envelope: dict[str, object]
) -> dict[str, Any]:
    stable_payload = canonical_bytes(stable_envelope)
    stable_with_id = {
        **stable_envelope,
        "stable_prefix_id": hashlib.sha256(stable_payload).hexdigest()[:24],
    }
    task_evidence = {
        "revision_id": package.revision_id,
        "source_revision": package.source_revision.value if package.source_revision else None,
        "objective_fingerprint": package.objective_fingerprint,
        "scope": package.scope.value,
        "provenance": [
            {
                "id": identifier,
                "source": item.source,
                "producer": item.producer,
                "producer_version": item.producer_version,
            }
            for identifier, item in package.provenance
        ],
        "items": [weak_local_evidence_item_json(item) for item in package.items],
        # Grouped as well as listed: a consumer asking "which tests must run?" reads
        # `answer.test` instead of filtering the whole envelope for them.
        "answer": {
            role: [item.evidence_id for item in package.items if str(item.role) == role]
            for role in ("target", "consumer", "test")
            if any(str(item.role) == role for item in package.items)
        },
        "selected_evidence_ids": list(package.selected_evidence_ids),
        "prior_evidence_ids": list(package.prior_evidence_ids),
        "unresolved_evidence_gaps": list(package.unresolved_gaps),
        "request_next_scope": package.next_scope.value if package.next_scope else "none",
    }
    task_payload = canonical_bytes(task_evidence)
    return {
        "stable_envelope": stable_with_id,
        "task_evidence": task_evidence,
        "metrics": {
            "stable_prefix_canonical_bytes": len(stable_payload),
            "task_evidence_canonical_bytes": len(task_payload),
            "candidate_count": package.candidate_count,
            "selected_count": len(package.items),
            "excluded_count": package.excluded_count,
            "estimated_evidence_tokens": package.used_tokens,
            "delivered_evidence_tokens": estimate_payload_tokens(task_evidence),
            "token_budget": package.token_budget,
            "truncated": package.truncated,
            "candidate_search_truncated": package.candidate_search_truncated,
            "deterministic_resolution": package.deterministic_resolution,
            "cache_observation": "model_response_metrics",
        },
    }
