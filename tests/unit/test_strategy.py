from __future__ import annotations

from collections.abc import Callable

import pytest

from extendcodeagent.core.config.schema import CapabilityName
from extendcodeagent.core.model_routing import FakeModelAdapter
from extendcodeagent.core.policy import CapabilityPolicy, CapabilityUnavailable
from extendcodeagent.strategy import (
    ModelStrategySynthesis,
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


def test_strategy_scores_project_facts_deterministically_and_llm_only_proposes_text(
    policy: CapabilityPolicy,
) -> None:
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
            migration_complexity_by_file={"a.py": 1, "b.py": 4, "c.py": 3},
            compatibility_risk_by_file={"b.py": 0.8},
            rollbackability_by_file={"a.py": 1.0, "b.py": 0.2, "c.py": 0.4},
            performance_risk_by_file={"b.py": 0.7},
            maintainability_benefit_by_file={"a.py": 0.5, "b.py": 0.2},
            cost_by_file={"a.py": 1.0, "b.py": 8.0, "c.py": 5.0},
            uncertainty_by_file={"c.py": 0.6},
        ),
        synthesis,
        policy=policy,
    )
    assert result.selected_id == "narrow"
    assert result.alternatives[0].score > result.alternatives[1].score
    assert result.alternatives[0].scope_size == 1
    assert result.alternatives[0].rollbackability == 1.0
    assert result.alternatives[0].metric_provenance == "project_intelligence"
    assert set(synthesis.payloads[0]) == {"goal", "constraints", "candidate_files"}


def test_strategy_has_no_generic_fallback_when_synthesis_is_unavailable(
    policy: CapabilityPolicy,
) -> None:
    with pytest.raises(StrategyError, match="no alternatives"):
        build_strategy(
            StrategyRequest("plan", ()), StrategySignals(), FakeSynthesis(()), policy=policy
        )


def test_strategy_does_not_select_an_arbitrary_id_when_scores_tie(
    policy: CapabilityPolicy,
) -> None:
    result = build_strategy(
        StrategyRequest("choose", ()),
        StrategySignals(),
        FakeSynthesis(
            (
                ProposedAlternative("a", ("same.py",), "first", "revert"),
                ProposedAlternative("z", ("same.py",), "second", "revert"),
            )
        ),
        policy=policy,
    )
    assert result.selected_id is None
    assert result.reasons[-1] == "tie_requires_decision"


def test_strategy_is_unavailable_when_the_capability_is_off(
    policy_factory: Callable[..., CapabilityPolicy],
) -> None:
    off = policy_factory("advisory", overrides={CapabilityName.STRATEGY: "off"})
    synthesis = FakeSynthesis((ProposedAlternative("a", ("x.py",), "only", "revert"),))
    with pytest.raises(CapabilityUnavailable, match="strategy"):
        build_strategy(StrategyRequest("plan", ()), StrategySignals(), synthesis, policy=off)
    assert synthesis.payloads == []


def test_model_synthesis_accepts_only_explicit_structured_alternatives() -> None:
    adapter = FakeModelAdapter(
        '{"alternatives":[{"id":"narrow","changed_files":["a.py"],'
        '"explanation":"small","rollback_plan":"revert"}]}'
    )
    synthesis = ModelStrategySynthesis(adapter)
    proposals = synthesis.propose({"goal": "fix", "constraints": (), "candidate_files": ("a.py",)})
    assert proposals[0].alternative_id == "narrow"
    assert adapter.calls[0].requires_structured_output is True
    assert adapter.calls[0].contains_source_code is False


def test_model_synthesis_rejects_invalid_payload_without_fallback() -> None:
    synthesis = ModelStrategySynthesis(FakeModelAdapter("not-json"))
    with pytest.raises(StrategyError, match="invalid strategy synthesis"):
        synthesis.propose({"goal": "fix", "constraints": (), "candidate_files": ()})
