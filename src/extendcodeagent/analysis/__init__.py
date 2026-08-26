"""Bounded graph path, impact, and canonical-reference resolution."""

from .contracts import (
    GraphPath,
    ImpactItem,
    ImpactQuery,
    ImpactReport,
    PathQuery,
    PathResult,
)
from .resolver import (
    CanonicalReferenceResolver,
    CompositeCanonicalReferenceResolver,
    IdentityReferenceResolver,
    JavaScriptTypeScriptCanonicalReferenceResolver,
    PythonCanonicalReferenceResolver,
    SourceFileReferenceResolver,
)
from .service import GraphAnalysisService

__all__ = [
    "CanonicalReferenceResolver",
    "CompositeCanonicalReferenceResolver",
    "GraphAnalysisService",
    "GraphPath",
    "IdentityReferenceResolver",
    "SourceFileReferenceResolver",
    "ImpactItem",
    "ImpactQuery",
    "ImpactReport",
    "JavaScriptTypeScriptCanonicalReferenceResolver",
    "PathQuery",
    "PathResult",
    "PythonCanonicalReferenceResolver",
]
