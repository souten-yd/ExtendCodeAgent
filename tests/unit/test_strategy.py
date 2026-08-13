from __future__ import annotations

import pytest

from extendcodeagent.strategy import (
    ProposedAlternative,
    StrategyError,
    StrategyRequest,
    StrategySignals,
    build_strategy,
)


class FakeSynthesis:
    def __init__(self, alternatives: tuple[ProposedAlternative, ...]) -> None:
        self.alternatives = alternatives
        self.payloads: list[dict[str, object]] = []

    def propose(self, payload: dict[str, object]) -> tuple[ProposedAlternative, ...]:
        self.payloads.append(payload)
        return self.alternatives


def test_strategy_scores_project_facts_deterministically_and_llm_only_proposes_text() -> None:
    synthesis = FakeSynthesis(
        (
            ProposedAlternative("narrow", ("a.py",), "small change", "revert one commit"),
            ProposedAlternative(
                "wide", ("a.py", "b.py", "c.py"), "broad redesign", "restore branch"
            ),
        )
    )
    result = build_strategy(
        StrategyRequest("fix safely", ("preserve API",)),
        StrategySignals(
            impact_by_file={"a.py": 1, "b.py": 8, "c.py": 5},
            tests_by_file={"a.py": 1, "b.py": 4, "c.py": 3},
            compatibility_risk_by_file={"b.py": 0.8},
            uncertainty_by_file={"c.py": 0.6},
        ),
        synthesis,
    )
    assert result.selected_id == "narrow"
    assert result.alternatives[0].score > result.alternatives[1].score
    assert result.alternatives[0].metric_provenance == "project_intelligence"
    assert set(synthesis.payloads[0]) == {"goal", "constraints", "candidate_files"}


def test_strategy_has_no_generic_fallback_when_synthesis_is_unavailable() -> None:
    with pytest.raises(StrategyError, match="no alternatives"):
        build_strategy(StrategyRequest("plan", ()), StrategySignals(), FakeSynthesis(()))
