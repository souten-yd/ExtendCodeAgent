"""Optional model synthesis adapter; deterministic scoring remains in Strategy Core."""

from __future__ import annotations

import json
from dataclasses import dataclass

from extendcodeagent.core.config.schema import ModelRole
from extendcodeagent.core.model_routing.contracts import ModelAdapter, ModelRequest

from .contracts import ProposedAlternative, StrategyError


@dataclass(frozen=True, slots=True)
class ModelStrategySynthesis:
    adapter: ModelAdapter

    def propose(self, payload: dict[str, object]) -> tuple[ProposedAlternative, ...]:
        prompt = json.dumps(
            {
                "instruction": (
                    "Propose concrete alternatives. Return JSON with alternatives; each needs "
                    "id, changed_files, explanation, rollback_plan. Do not score them."
                ),
                **payload,
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        response = self.adapter.complete(
            ModelRequest(
                ModelRole.STRATEGY_REASONER,
                prompt,
                context_tokens=max(1, len(prompt) // 4),
                contains_source_code=False,
                requires_structured_output=True,
            )
        )
        try:
            raw = json.loads(response.text)
            values = raw["alternatives"]
            if not isinstance(values, list):
                raise TypeError
            alternatives = tuple(
                ProposedAlternative(
                    str(item["id"]),
                    tuple(str(value) for value in item["changed_files"]),
                    str(item["explanation"]),
                    str(item["rollback_plan"]),
                )
                for item in values
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise StrategyError("invalid strategy synthesis response") from error
        if not alternatives or any(not item.alternative_id.strip() for item in alternatives):
            raise StrategyError("invalid strategy synthesis response")
        return alternatives
