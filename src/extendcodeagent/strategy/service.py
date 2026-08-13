"""Deterministic Strategy scoring around optional model synthesis."""

from __future__ import annotations

from .contracts import (
    ProposedAlternative,
    StrategyAlternative,
    StrategyError,
    StrategyRequest,
    StrategyResult,
    StrategySignals,
    StrategySynthesisPort,
)


def build_strategy(
    request: StrategyRequest,
    signals: StrategySignals,
    synthesis: StrategySynthesisPort,
) -> StrategyResult:
    if not request.goal.strip():
        raise StrategyError("goal must not be empty")
    candidate_files = tuple(
        sorted(
            set(signals.impact_by_file)
            | set(signals.tests_by_file)
            | set(signals.compatibility_risk_by_file)
            | set(signals.uncertainty_by_file)
        )
    )
    proposals = synthesis.propose(
        {
            "goal": request.goal,
            "constraints": request.constraints,
            "candidate_files": candidate_files,
        }
    )
    if not proposals:
        raise StrategyError("no alternatives were proposed")
    identifiers = [item.alternative_id for item in proposals]
    if len(set(identifiers)) != len(identifiers):
        raise StrategyError("alternative ids must be unique")
    alternatives = tuple(_score(item, signals) for item in proposals)
    selected = max(alternatives, key=lambda item: (item.score, item.alternative_id))
    return StrategyResult(
        alternatives,
        selected.alternative_id,
        ("deterministic_project_metrics", "highest_score"),
    )


def _score(proposal: ProposedAlternative, signals: StrategySignals) -> StrategyAlternative:
    files = proposal.changed_files
    impact = sum(signals.impact_by_file.get(item, 0) for item in files)
    tests = sum(signals.tests_by_file.get(item, 0) for item in files)
    compatibility = max(
        (signals.compatibility_risk_by_file.get(item, 0.0) for item in files), default=0.0
    )
    uncertainty = max((signals.uncertainty_by_file.get(item, 0.0) for item in files), default=0.0)
    complexity = len(files)
    score = 100.0 - impact - tests * 2 - complexity * 2 - compatibility * 20 - uncertainty * 10
    return StrategyAlternative(
        proposal.alternative_id,
        files,
        proposal.explanation,
        proposal.rollback_plan,
        impact,
        tests,
        complexity,
        compatibility,
        uncertainty,
        round(score, 4),
    )
