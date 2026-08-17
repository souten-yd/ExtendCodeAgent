from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tools.local import omo_coexistence as runner


def test_b2_plan_seals_exact_five_stack_local_only_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    omo = tmp_path / "omo"
    omo.joinpath("dist").mkdir(parents=True)
    omo.joinpath("dist/index.js").write_text("export default {}", encoding="utf-8")
    omo.joinpath("package.json").write_text(
        json.dumps({"name": runner.OMO_PACKAGE, "version": runner.OMO_VERSION}),
        encoding="utf-8",
    )
    opencode = tmp_path / "opencode"
    opencode.write_text("binary", encoding="utf-8")
    monkeypatch.setattr(runner, "_require_clean", lambda: None)
    monkeypatch.setattr(runner, "_opencode", lambda: opencode)
    monkeypatch.setattr(runner, "_version", lambda _: "1.18.18")
    monkeypatch.setattr(runner, "_head", lambda: "a" * 40)
    monkeypatch.setattr(runner, "_omo_root", lambda _: omo)

    plan = runner.create_plan(tmp_path / "plan.json")

    runner._verify_seal(plan, "plan")
    assert plan["execution_scope"] == "local-only"
    assert plan["endpoint"] == "127.0.0.1:8090"
    assert plan["team_mode"] == "off"
    assert plan["eca_rollout_mode"] == "active"
    assert plan["maximum_agent_runs"] == 5
    assert plan["model_parallelism"] == 1
    assert plan["stacks"] == {
        "native": [],
        "eca": ["eca"],
        "omo": ["omo"],
        "omo_eca": ["omo", "eca"],
        "eca_omo": ["eca", "omo"],
    }


def test_stack_expectations_keep_namespaces_and_team_mode_fail_closed() -> None:
    tools = sorted(runner.EXPECTED_PI_TOOLS | runner.EXPECTED_OMO_TOOLS)
    agents = {f"{name} agent" for name in runner.EXPECTED_OMO_AGENT_PREFIXES}
    assert runner._stack_expectations("omo_eca", tools, agents) == []
    assert "missing_pi_tool" in runner._stack_expectations(
        "omo_eca", sorted(runner.EXPECTED_OMO_TOOLS), agents
    )
    assert "team_mode_not_off" in runner._stack_expectations(
        "omo_eca", [*tools, "team_create"], agents
    )


def test_conflict_observations_are_mechanically_classified() -> None:
    assert runner._classified_conflicts(
        [
            "duplicate_tool_id",
            "runtime_observation_count_not_one",
            "verification_oracle_failed",
            "duplicate_tool_execution",
            "resolved_model_route_mismatch",
            "session_not_recovered",
            "team_mode_not_off",
        ]
    ) == [
        {"conflict_class": f"C{index}", "observation": observation}
        for index, observation in enumerate(
            [
                "duplicate_tool_id",
                "runtime_observation_count_not_one",
                "verification_oracle_failed",
                "duplicate_tool_execution",
                "resolved_model_route_mismatch",
                "session_not_recovered",
                "team_mode_not_off",
            ]
        )
    ]


def test_isolated_environment_forbids_remote_credentials_and_disables_team(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = {
        "eca": {"plugin": str(tmp_path / "eca.js")},
        "omo": {"root": str(tmp_path / "omo")},
    }
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    monkeypatch.setenv("GH_TOKEN", "secret")

    env = runner._isolated_env(plan, "omo_eca", tmp_path / "profile", tmp_path / "workspace")

    assert "OPENAI_API_KEY" not in env
    assert "GH_TOKEN" not in env
    assert env["OMO_DISABLE_POSTHOG"] == "1"
    assert env["EXTENDCODEAGENT_MODE"] == "active"
    assert json.loads(env["OPENCODE_CONFIG_CONTENT"])["model"] == runner.MODEL_ROUTE
    omo_config = json.loads((tmp_path / "profile/config/opencode/oh-my-openagent.json").read_text())
    assert omo_config["team_mode"] == {"enabled": False}

    native_env = runner._isolated_env(plan, "native", tmp_path / "native", tmp_path / "workspace")
    assert native_env["EXTENDCODEAGENT_MODE"] == "off"


def test_token_metrics_count_cached_prompt_context_per_request() -> None:
    messages = [
        {
            "info": {
                "role": "assistant",
                "tokens": {
                    "input": 7,
                    "output": 3,
                    "reasoning": 0,
                    "cache": {"read": 11, "write": 2},
                },
            }
        },
        {
            "info": {
                "role": "assistant",
                "tokens": {
                    "input": 5,
                    "output": 1,
                    "reasoning": 0,
                    "cache": {"read": 23, "write": 0},
                },
            }
        },
    ]

    measured = runner._token_metrics(messages)

    assert measured["llm_calls_executed"] == 2
    assert measured["input_tokens"] == 12
    assert measured["cache_read_tokens"] == 34
    assert measured["cache_write_tokens"] == 2
    assert measured["context_request_tokens"] == [20, 28]
    assert measured["average_context_tokens"] == 24
    assert measured["p95_context_tokens"] == 28
    assert measured["max_context_tokens"] == 28


def _model_result(stack: str, result: str = "PASS") -> dict[str, Any]:
    return {
        "stack": stack,
        "plugins": list(runner.STACKS[stack]),
        "result": result,
        "errors": [],
        "oracle_exit": 0,
        "changed_files": ["calc.py"],
        "route": {"provider_id": runner.MODEL_PROVIDER, "model_id": runner.MODEL_ID},
        "llm_calls_executed": 1,
        "input_tokens": 10,
        "output_tokens": 2,
        "reasoning_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "context_request_tokens": [10],
        "max_context_tokens": 10,
    }


@pytest.mark.parametrize(
    ("failed_stack", "expected", "expected_runs", "complete"),
    [
        (None, "compatible", 5, True),
        ("omo_eca", "incompatible", 5, True),
        ("native", "NOT_EVALUATED_INCOMPLETE", 1, False),
    ],
)
def test_model_bridge_classifies_combined_regression_against_controls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failed_stack: str | None,
    expected: str,
    expected_runs: int,
    complete: bool,
) -> None:
    plan = runner._seal(
        {
            "source_revision": "a" * 40,
            "opencode": {"path": "/opencode", "version": "1.18.18"},
            "omo": {"root": "/omo", "plugin_sha256": "x"},
            "eca": {"plugin": "/eca", "plugin_sha256": "y"},
        }
    )
    preflight = runner._seal({"execution_plan": plan["seal"]["canonical_payload"], "pass": True})
    plan_path = tmp_path / "plan.json"
    preflight_path = tmp_path / "preflight.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    preflight_path.write_text(json.dumps(preflight), encoding="utf-8")
    monkeypatch.setattr(runner, "_require_clean", lambda: None)
    monkeypatch.setattr(runner, "_verify_plan", lambda _: None)
    monkeypatch.setattr(runner, "_user_omo_fingerprint", lambda: {"exists": False})
    monkeypatch.setattr(
        runner,
        "_provider_readiness",
        lambda: {"status": "PASS", "reason": None, "model_ids": ["llama"], "llm_calls": 0},
    )
    monkeypatch.setattr(
        runner,
        "_model_stack",
        lambda _plan, stack, _root: _model_result(
            stack, "FAIL" if stack == failed_stack else "PASS"
        ),
    )

    report = runner.run_model_bridge(
        plan_path,
        preflight_path,
        tmp_path / "result.json",
        tmp_path / "raw",
        resume=False,
    )

    assert report["compatibility"] == expected
    assert report["complete"] is complete
    assert report["agent_runs_executed"] == expected_runs
    assert report["llm_calls_executed"] == expected_runs
    if failed_stack == "native":
        assert report["execution_stop_reason"] == "CONTROL_FAILURE_REPAIR_REQUIRED:native"
        assert report["provider_gap_pending"] is False
    assert report["recommended_stack_claim"] is False
    runner._verify_seal(report, "result")


def test_model_bridge_stops_before_inference_when_local_provider_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = runner._seal(
        {
            "source_revision": "a" * 40,
            "opencode": {"path": "/opencode", "version": "1.18.18"},
            "omo": {"root": "/omo", "plugin_sha256": "x"},
            "eca": {"plugin": "/eca", "plugin_sha256": "y"},
        }
    )
    preflight = runner._seal({"execution_plan": plan["seal"]["canonical_payload"], "pass": True})
    plan_path = tmp_path / "plan.json"
    preflight_path = tmp_path / "preflight.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    preflight_path.write_text(json.dumps(preflight), encoding="utf-8")
    monkeypatch.setattr(runner, "_require_clean", lambda: None)
    monkeypatch.setattr(runner, "_verify_plan", lambda _: None)
    monkeypatch.setattr(runner, "_user_omo_fingerprint", lambda: {"exists": False})
    monkeypatch.setattr(
        runner,
        "_provider_readiness",
        lambda: {
            "status": "UNAVAILABLE",
            "reason": "ConnectionRefusedError",
            "model_ids": [],
            "llm_calls": 0,
        },
    )

    report = runner.run_model_bridge(
        plan_path,
        preflight_path,
        tmp_path / "result.json",
        tmp_path / "raw",
        resume=False,
    )

    assert report["complete"] is False
    assert report["provider_gap_pending"] is True
    assert report["agent_runs_executed"] == 0
    assert report["llm_calls_executed"] == 0
    assert report["pending_stacks"] == list(runner.STACKS)
    assert report["compatibility"] == "NOT_EVALUATED_INCOMPLETE"


def test_model_bridge_resume_reuses_completed_stack(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = runner._seal(
        {
            "source_revision": "a" * 40,
            "opencode": {"path": "/opencode", "version": "1.18.18"},
            "omo": {"root": "/omo", "plugin_sha256": "x"},
            "eca": {"plugin": "/eca", "plugin_sha256": "y"},
        }
    )
    preflight = runner._seal({"execution_plan": plan["seal"]["canonical_payload"], "pass": True})
    plan_path = tmp_path / "plan.json"
    preflight_path = tmp_path / "preflight.json"
    output = tmp_path / "result.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    preflight_path.write_text(json.dumps(preflight), encoding="utf-8")
    monkeypatch.setattr(runner, "_require_clean", lambda: None)
    monkeypatch.setattr(runner, "_verify_plan", lambda _: None)
    monkeypatch.setattr(runner, "_head", lambda: "a" * 40)
    monkeypatch.setattr(runner, "_user_omo_fingerprint", lambda: {"exists": False})
    statuses = iter(["PASS", "UNAVAILABLE"])
    monkeypatch.setattr(
        runner,
        "_provider_readiness",
        lambda: {
            "status": next(statuses),
            "reason": None,
            "model_ids": ["llama"],
            "llm_calls": 0,
        },
    )
    calls: list[str] = []

    def model_result(_plan: Any, stack: str, _root: Path) -> dict[str, Any]:
        calls.append(stack)
        return _model_result(stack)

    monkeypatch.setattr(runner, "_model_stack", model_result)

    partial = runner.run_model_bridge(
        plan_path, preflight_path, output, tmp_path / "raw", resume=False
    )
    assert partial["pending_stacks"] == ["eca", "omo", "omo_eca", "eca_omo"]
    assert calls == ["native"]

    monkeypatch.setattr(
        runner,
        "_provider_readiness",
        lambda: {"status": "PASS", "reason": None, "model_ids": ["llama"], "llm_calls": 0},
    )
    complete = runner.run_model_bridge(
        plan_path, preflight_path, output, tmp_path / "raw", resume=True
    )

    assert complete["complete"] is True
    assert complete["agent_runs_completed"] == 5
    assert calls == ["native", "eca", "omo", "omo_eca", "eca_omo"]


def test_model_bridge_resume_does_not_bypass_failed_control(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "_head", lambda: "a" * 40)
    plan = runner._seal({"source_revision": "a" * 40})
    preflight = runner._seal({"execution_plan": plan["seal"]["canonical_payload"], "pass": True})
    failed = _model_result("eca", "FAIL")
    previous = runner._model_report(plan, preflight, [_model_result("native"), failed], [], [])
    plan_path = tmp_path / "plan.json"
    preflight_path = tmp_path / "preflight.json"
    output = tmp_path / "result.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    preflight_path.write_text(json.dumps(preflight), encoding="utf-8")
    output.write_text(json.dumps(previous), encoding="utf-8")
    monkeypatch.setattr(runner, "_require_clean", lambda: None)
    monkeypatch.setattr(runner, "_verify_plan", lambda _: None)
    monkeypatch.setattr(
        runner,
        "_provider_readiness",
        lambda: pytest.fail("failed control must stop same-head resume before provider access"),
    )

    resumed = runner.run_model_bridge(
        plan_path, preflight_path, output, tmp_path / "raw", resume=True
    )

    assert resumed == previous
    assert resumed["execution_stop_reason"] == "CONTROL_FAILURE_REPAIR_REQUIRED:eca"
    assert resumed["provider_gap_pending"] is False


def test_operator_interruption_is_incomplete_but_not_a_provider_gap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runner, "_head", lambda: "a" * 40)
    plan = runner._seal({"source_revision": "a" * 40})
    preflight = runner._seal({"execution_plan": plan["seal"]["canonical_payload"], "pass": True})
    interrupted = _model_result("native", "OPERATOR_INTERRUPTED")

    report = runner._model_report(plan, preflight, [], [interrupted], [])

    assert report["complete"] is False
    assert report["execution_stop_reason"] == "OPERATOR_INTERRUPTED"
    assert report["provider_gap_pending"] is False


def test_native_result_reuse_requires_equal_sealed_inputs_and_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    comparable = {
        "execution_scope": "local-only",
        "model": "Qwen3.6 27B",
        "endpoint": "127.0.0.1:8090",
        "context": runner.MODEL_CONTEXT,
        "output_limit": runner.MODEL_OUTPUT,
        "team_mode": "off",
        "opencode": {"path": "/opencode", "version": "1.18.18"},
        "omo": {"package": "oh-my-openagent@4.19.4", "plugin_sha256": "x"},
        "stacks": {name: list(plugins) for name, plugins in runner.STACKS.items()},
        "task_fixture_fingerprint": runner._fixture_fingerprint(),
    }
    source_plan = runner._seal({**comparable, "source_revision": "a" * 40})
    source_result = _model_result("native")
    source_report = runner._seal(
        {
            "source_revision": "a" * 40,
            "execution_plan": source_plan["seal"]["canonical_payload"],
            "results": [source_result],
        }
    )
    plan_path = tmp_path / "source-plan.json"
    report_path = tmp_path / "source-report.json"
    plan_path.write_text(json.dumps(source_plan), encoding="utf-8")
    report_path.write_text(json.dumps(source_report), encoding="utf-8")
    monkeypatch.setattr(runner, "_head", lambda: "b" * 40)
    monkeypatch.setattr(
        runner, "_task_instruction_at_revision", lambda _revision: runner.MODEL_TASK_INSTRUCTION
    )

    reused = runner._native_reuse_result(
        {**comparable, "source_revision": "b" * 40}, plan_path, report_path
    )

    assert reused["result_origin"] == "COMPATIBILITY_MIGRATION"
    assert reused["llm_call_execution"] == "reused"
    assert reused["migration_basis"]["stack_has_eca_plugin"] is False
    assert reused["migration_basis"]["non_applicable_current_input_differences"] == [
        "eca_rollout_mode"
    ]
