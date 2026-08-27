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
from .envelope import build_answer_envelope
from .locate import files_for, files_naming
from .obligations import DEFAULT_MAX_OBLIGATIONS, obligation_refs
from .serialization import (
    context_item_json,
    context_package_json,
    estimate_payload_tokens,
    weak_local_evidence_json,
)
from .service import (
    attach_excerpts,
    attach_exemplar,
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
    "attach_exemplar",
    "DEFAULT_MAX_OBLIGATIONS",
    "build_answer_envelope",
    "files_for",
    "files_naming",
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
