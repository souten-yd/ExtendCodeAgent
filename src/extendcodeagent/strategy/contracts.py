"""Evidence-based Strategy contracts independent of model providers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol


class StrategyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class StrategyRequest:
    goal: str
    constraints: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StrategySignals:
    impact_by_file: Mapping[str, int] = field(default_factory=dict)
    tests_by_file: Mapping[str, int] = field(default_factory=dict)
    compatibility_risk_by_file: Mapping[str, float] = field(default_factory=dict)
    uncertainty_by_file: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "impact_by_file",
            "tests_by_file",
            "compatibility_risk_by_file",
            "uncertainty_by_file",
        ):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))


@dataclass(frozen=True, slots=True)
class ProposedAlternative:
    alternative_id: str
    changed_files: tuple[str, ...]
    explanation: str
    rollback_plan: str


@dataclass(frozen=True, slots=True)
class StrategyAlternative:
    alternative_id: str
    changed_files: tuple[str, ...]
    explanation: str
    rollback_plan: str
    impact_size: int
    test_burden: int
    migration_complexity: int
    compatibility_risk: float
    uncertainty: float
    score: float
    metric_provenance: str = "project_intelligence"


@dataclass(frozen=True, slots=True)
class StrategyResult:
    alternatives: tuple[StrategyAlternative, ...]
    selected_id: str
    reasons: tuple[str, ...]


class StrategySynthesisPort(Protocol):
    def propose(self, payload: dict[str, object]) -> tuple[ProposedAlternative, ...]: ...
