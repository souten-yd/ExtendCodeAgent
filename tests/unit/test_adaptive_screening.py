from __future__ import annotations

from extendcodeagent.evaluation.adaptive import (
    capability_task_relevance,
    depth_equivalence_classes,
    efficiency_summary,
    next_depth,
    reasoning_input_fingerprint,
    representative_depths,
    sequential_ablation_decision,
)


def test_relevance_uses_only_observed_non_status_active_tools() -> None:
    relevance = capability_task_relevance(
        [
            {
                "arm": "active",
                "task_id": "symbol",
                "pi_tools": ["pi_status", "pi_symbol"],
            },
            {
                "arm": "active",
                "task_id": "planned",
                "pi_tools": ["pi_status"],
                "pi_capabilities_used": ["strategy"],
            },
            {"arm": "active", "task_id": "negative", "pi_tools": ["pi_status"]},
            {"arm": "off", "task_id": "ignored", "pi_tools": ["pi_impact"]},
        ]
    )

    assert relevance["symbol"] == {
        "tools": ("pi_symbol",),
        "capabilities": ("graph", "semantic", "twin"),
    }
    assert "negative" not in relevance
    assert "ignored" not in relevance
    assert relevance["planned"] == {"tools": (), "capabilities": ("strategy",)}


def test_depth_preflight_folds_identical_d2_d3_d4_outputs() -> None:
    outputs = {
        "D0": {"depth": "D0", "items": ["one"], "timing": {"query": 1}},
        "D1": {"depth": "D1", "items": ["one", "two"]},
        "D2": {"depth": "D2", "items": ["one", "two", "three"]},
        "D3": {"depth": "D3", "items": ["one", "two", "three"]},
        "D4": {"depth": "D4", "items": ["one", "two", "three"]},
    }

    classes = depth_equivalence_classes(outputs)

    assert [item["depths"] for item in classes] == [["D0"], ["D1"], ["D2", "D3", "D4"]]
    assert representative_depths(classes) == ("D0", "D1", "D2")


def test_ablation_repetition_stops_positive_at_two_and_uses_three_only_at_boundary() -> None:
    pairs = [
        {
            "task_id": "task",
            "task_class": "symbol-lookup",
            "repetition": repetition,
            "active_outcome": "PASS",
            "ablation_outcome": "FAIL" if repetition <= 2 else None,
        }
        for repetition in range(1, 4)
    ]

    first = sequential_ablation_decision(pairs, threshold=2, current_repetition=1)
    second = sequential_ablation_decision(pairs, threshold=2, current_repetition=2)

    assert first["decision"] == "CONTINUE_TO_REPETITION"
    assert second["decision"] == "PROCEED_TO_B0B_EARLY"
    assert second["needs_next_repetition"] is False


def test_unexercised_pairs_are_not_synthesized_as_no_effect() -> None:
    decision = sequential_ablation_decision([], threshold=2, current_repetition=1)

    assert decision["completed_pairs"] == 0
    assert decision["decision"] == "NOT_TESTED_NO_ACTIVE_USE"


def test_minimum_sufficient_depth_stops_after_first_pass() -> None:
    representatives = ("D0", "D1", "D2")

    assert next_depth(representatives, {})["next"] == "D0"
    assert next_depth(representatives, {"D0": "FAIL"})["next"] == "D1"
    assert next_depth(representatives, {"D0": "FAIL", "D1": "PASS"}) == {
        "decision": "MINIMUM_SUFFICIENT",
        "depth": "D1",
        "next": None,
    }


def test_reasoning_fingerprint_is_order_independent_and_requires_provenance() -> None:
    values = {
        "project_workspace": "project/workspace",
        "revision": "abc",
        "task_intent": "find symbol",
        "capability_depth": {"semantic": "D1"},
        "selected_evidence_ids": ["evidence-1"],
        "relevant_environment": {"model": "local-practical"},
    }

    assert reasoning_input_fingerprint(values) == reasoning_input_fingerprint(
        dict(reversed(list(values.items())))
    )


def test_efficiency_summary_counts_avoided_calls_without_calling_them_passes() -> None:
    summary = efficiency_summary(
        requested_calls=4,
        results=[{"outcome": "PASS", "input_tokens": 10, "output_tokens": 2, "wall_ms": 5}],
        skips=[
            {"reason": "NOT_TESTED_NO_ACTIVE_USE", "avoids_llm_call": True},
            {"reason": "SKIPPED_DEPTH_OUTPUT_EQUIVALENT", "avoids_llm_call": True},
            {"reason": "PENDING", "avoids_llm_call": False},
        ],
        deterministic_pi_wall_ms=3,
        total_wall_ms=8,
        reused_evidence_count=0,
        invalidated_evidence_count=0,
        minimum_sufficient_depths={},
    )

    assert summary["llm_calls_executed"] == 1
    assert summary["llm_calls_avoided"] == 2
    assert summary["avoided_call_ratio"] == 0.5


def test_efficiency_summary_does_not_count_reused_model_evidence_as_a_new_call() -> None:
    summary = efficiency_summary(
        requested_calls=2,
        results=[
            {"llm_call_execution": "reused", "input_tokens": 20, "wall_ms": 9},
            {
                "llm_call_execution": "executed",
                "input_tokens": 5,
                "context_request_count": 1,
                "context_token_sum": 17,
                "max_context_tokens": 17,
                "wall_ms": 2,
            },
        ],
        skips=[{"reason": "REUSED_COMPATIBLE_EVIDENCE", "avoids_llm_call": True}],
        deterministic_pi_wall_ms=0,
        total_wall_ms=2,
        reused_evidence_count=1,
        invalidated_evidence_count=0,
        minimum_sufficient_depths={},
    )

    assert summary["llm_calls_executed"] == 1
    assert summary["llm_calls_avoided"] == 1
    assert summary["average_context_tokens"] == 17
    assert summary["max_context_tokens"] == 17
    assert summary["context_results_unavailable"] == 0
