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
            | set(signals.migration_complexity_by_file)
            | set(signals.compatibility_risk_by_file)
            | set(signals.rollbackability_by_file)
            | set(signals.performance_risk_by_file)
            | set(signals.maintainability_benefit_by_file)
            | set(signals.cost_by_file)
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
    highest_score = max(item.score for item in alternatives)
    leaders = tuple(item for item in alternatives if item.score == highest_score)
    selected_id = leaders[0].alternative_id if len(leaders) == 1 else None
    reasons = (
        ("deterministic_project_metrics", "highest_score")
        if selected_id is not None
        else ("deterministic_project_metrics", "tie_requires_decision")
    )
    return StrategyResult(
        alternatives,
        selected_id,
        reasons,
    )


def _score(proposal: ProposedAlternative, signals: StrategySignals) -> StrategyAlternative:
    files = proposal.changed_files
    impact = sum(signals.impact_by_file.get(item, 0) for item in files)
    tests = sum(signals.tests_by_file.get(item, 0) for item in files)
    migration_complexity = sum(signals.migration_complexity_by_file.get(item, 1) for item in files)
    compatibility = max(
        (signals.compatibility_risk_by_file.get(item, 0.0) for item in files), default=0.0
    )
    uncertainty = max((signals.uncertainty_by_file.get(item, 0.0) for item in files), default=0.0)
    rollbackability = min(
        (signals.rollbackability_by_file.get(item, 1.0) for item in files), default=1.0
    )
    performance_risk = max(
        (signals.performance_risk_by_file.get(item, 0.0) for item in files), default=0.0
    )
    maintainability_benefit = sum(
        signals.maintainability_benefit_by_file.get(item, 0.0) for item in files
    )
    cost = sum(signals.cost_by_file.get(item, 1.0) for item in files)
    scope_size = len(files)
    score = (
        100.0
        - impact
        - tests * 2
        - migration_complexity * 2
        - compatibility * 20
        + rollbackability * 5
        - performance_risk * 10
        + maintainability_benefit * 5
        - cost
        - uncertainty * 10
    )
    return StrategyAlternative(
        proposal.alternative_id,
        files,
        proposal.explanation,
        proposal.rollback_plan,
        scope_size,
        impact,
        tests,
        migration_complexity,
        compatibility,
        rollbackability,
        performance_risk,
        maintainability_benefit,
        cost,
        uncertainty,
        round(score, 4),
    )
