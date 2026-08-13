from typing import TYPE_CHECKING

from .contracts import (
    ActualElement,
    ActualSnapshot,
    ConvergenceDecision,
    ConvergenceRecommendation,
    ConvergenceReport,
    ElementConvergence,
    ElementState,
    TargetElement,
    TargetSnapshot,
    VerificationEvidence,
)
from .service import decide_convergence, evaluate_convergence

if TYPE_CHECKING:
    from .storage import SqliteConvergenceRepository


def __getattr__(name: str) -> object:
    if name == "SqliteConvergenceRepository":
        from .storage import SqliteConvergenceRepository

        return SqliteConvergenceRepository
    raise AttributeError(name)


__all__ = [
    "ActualElement",
    "ActualSnapshot",
    "ConvergenceDecision",
    "ConvergenceRecommendation",
    "ConvergenceReport",
    "ElementConvergence",
    "ElementState",
    "SqliteConvergenceRepository",
    "TargetElement",
    "TargetSnapshot",
    "VerificationEvidence",
    "decide_convergence",
    "evaluate_convergence",
]
