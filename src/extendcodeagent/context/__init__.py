"""Bounded context intelligence."""

from .contracts import (
    ContextItem,
    ContextPackage,
    ContextProfile,
    ContextRequest,
    EvidenceRole,
    EvidenceScope,
    RequiredRef,
    WeakLocalEvidenceItem,
    WeakLocalEvidencePackage,
    WeakLocalEvidenceRequest,
)
from .obligations import obligation_refs
from .serialization import (
    context_item_json,
    context_package_json,
    estimate_payload_tokens,
    weak_local_evidence_json,
)
from .service import (
    attach_excerpts,
    build_context,
    build_weak_local_evidence,
    infer_evidence_scope,
    stable_evidence_envelope,
)

__all__ = [
    "ContextItem",
    "ContextPackage",
    "ContextProfile",
    "ContextRequest",
    "EvidenceRole",
    "EvidenceScope",
    "RequiredRef",
    "WeakLocalEvidenceItem",
    "WeakLocalEvidencePackage",
    "WeakLocalEvidenceRequest",
    "attach_excerpts",
    "build_context",
    "build_weak_local_evidence",
    "context_item_json",
    "context_package_json",
    "estimate_payload_tokens",
    "infer_evidence_scope",
    "obligation_refs",
    "stable_evidence_envelope",
    "weak_local_evidence_json",
]
