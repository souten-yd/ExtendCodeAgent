"""Bounded context intelligence."""

from .contracts import (
    ContextItem,
    ContextPackage,
    ContextProfile,
    ContextRequest,
    EvidenceScope,
    WeakLocalEvidenceItem,
    WeakLocalEvidencePackage,
    WeakLocalEvidenceRequest,
)
from .service import build_context, build_weak_local_evidence, stable_evidence_envelope

__all__ = [
    "ContextItem",
    "ContextPackage",
    "ContextProfile",
    "ContextRequest",
    "EvidenceScope",
    "WeakLocalEvidenceItem",
    "WeakLocalEvidencePackage",
    "WeakLocalEvidenceRequest",
    "build_context",
    "build_weak_local_evidence",
    "stable_evidence_envelope",
]
