"""Semantic-change and verification-obligation projections."""

from .contracts import (
    ChangeOperation,
    Criticality,
    ObligationStatus,
    ObligationType,
    RequiredSetQuality,
    RequiredVerificationProvider,
    RequiredVerificationSet,
    SemanticChangeSet,
    SemanticEntityChange,
    SemanticRelationChange,
    VerificationObligation,
)
from .service import (
    derive_required_verification_set,
    derive_semantic_change_set,
    evaluate_required_set_quality,
)

__all__ = [
    "ChangeOperation",
    "Criticality",
    "ObligationStatus",
    "ObligationType",
    "RequiredSetQuality",
    "RequiredVerificationProvider",
    "RequiredVerificationSet",
    "SemanticChangeSet",
    "SemanticEntityChange",
    "SemanticRelationChange",
    "VerificationObligation",
    "derive_required_verification_set",
    "derive_semantic_change_set",
    "evaluate_required_set_quality",
]
