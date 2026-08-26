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


def weak_local_evidence_item_json(item: Any) -> dict[str, Any]:
    return {
        "id": item.evidence_id,
        "ref": item.canonical_ref.value,
        "kind": item.kind,
        "summary": item.summary,
        "reason": item.reason,
        "confidence": item.confidence,
        "provenance_id": item.provenance_id,
        "status": item.status,
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
