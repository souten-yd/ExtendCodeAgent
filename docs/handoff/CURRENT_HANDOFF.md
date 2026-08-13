# Current Handoff

Updated: 2026-08-13 (Asia/Tokyo)

Current branch: `agent/pr-g-routing-strategy`
Current PR: not created
Base commit: `7b1fb759365cc8dc6e57ad1da9a2870307ac60c8`
Latest commit: `e575dc1` (adaptive routing and Strategy Core)
Milestone: PR-G live Model Routing + Strategy
Current task: build reproducible multi-scenario real-model A/B evaluation harness
Status: in progress

Completed:
- PR-F PR #12 merged as `157fd19`; closeout PR #13 merged as `7b1fb75`;
- exact closeout main passed all-fast (Python 75, adapter 9, Ruff/format/mypy) and build;
- created this branch from exact clean main;
- read the PR-G execution-plan and Strategy migration-audit slices;
- inspected the existing PR-A `PolicyModelRouter`, contracts, fakes, config, and routing tests;
- verified installed OpenCode 1.18.18 and current official provider/model guidance: stable V1 uses
  `provider` plus `@ai-sdk/openai-compatible`; session prompt selects `{providerID, modelID}`.
- added behavior-first tests for deterministic adaptive risk/privacy routing, OpenAI-compatible
  structured chat completions, stable OpenCode session/model payloads, evidence-derived Strategy
  scoring, bounded synthesis payload, and absence of generic fallback alternatives;
- confirmed the initial focused red gate fails only for the not-yet-implemented target contracts.
- extended the existing router with deterministic adaptive signals and explainable required tier;
- added transport-injected OpenAI-compatible and stable OpenCode host adapters with token parsing;
- added Strategy Core where synthesis proposes text/scope and deterministic project signals own all
  scoring/provenance; empty synthesis fails instead of fabricating fallback alternatives;
- focused Ruff/mypy and 15 routing/adapter/Strategy tests pass.
- added routed wall-time/escalation/locality metrics and strict model-backed Strategy synthesis;
- installed evaluation-only `qwen3:0.6b` (522 MB) in Ollama; repository unchanged by the model;
- real local-low conformance passed: Qwen3 0.6B returned correct JSON, 209 input/7 output tokens,
  2,205.4 ms;
- real local-medium conformance passed: Qwen 3.6 27B returned correct JSON, 26 input/262 output
  tokens, 13,068.0 ms;
- real OpenCode host conformance passed on 1.18.18 with `opencode/big-pickle`: exact `host-ok`,
  8,250 input/4 output tokens, 2,311.3 ms; large native system context is recorded as a limitation;
- focused routing/adapter/Strategy suite now passes 17 tests with Ruff/mypy PASS.

In progress:
- build same-repository/same-task native/off/advisory/active evaluation and compact evidence.

Not started:
- real local/host/frontier conformance, A/B metrics/evidence, final gates/publication.

Architecture classification:
- REUSE/EXTEND the existing `PolicyModelRouter` and ModelRequest/Response contracts;
- NEW transport adapters only behind existing ModelAdapter;
- NEW Strategy Core with deterministic metrics and optional synthesis port;
- DO NOT PORT KasaneCore DeepPlanner, Atlas/Nexus schemas, or fixed A/B/C fallbacks.

Scope:
- deterministic routing signals/selection/escalation/fallback accounting;
- OpenAI-compatible local path and current OpenCode host-model path;
- local-only and remote-code privacy enforcement;
- bounded weak-model structured requests;
- deterministic StrategyAlternative metrics/provenance plus LLM proposal/explanation;
- real local-low/local-medium/host/frontier evaluation where available.

Out of scope:
- JS/TS/deep graph (PR-H);
- Research/Traceability/project convergence (PR-I);
- replacing OpenCode Plan/runtime or adding GitHub CI.

Files changed: model-routing contracts/router/adapters, Strategy package, architecture and unit tests.
Files currently being edited: handoff before substantive implementation commit.
Exact tests executed: base gates; focused red; focused Ruff/mypy/pytest; three real model adapter
conformance calls.
Exact results: PASS; Python 75 passed in 0.60s, adapter 9 passed, Ruff/format/mypy and builds PASS.
Benchmark results: local-low 2,205.4 ms; local-medium 13,068.0 ms; host 2,311.3 ms. These are one
bounded conformance sample each, not quality distributions.
OpenCode version: 1.18.18.
Model/provider: Ollama Qwen3 0.6B; Ollama Qwen 3.6 27B Q5; OpenCode `opencode/big-pickle`.
Routing profile: to be exercised across configured modes; existing fake tests cover baseline modes.
Known failures: initial red collection failure resolved by implementation.
Known limitations: OpenCode host adds 8,250 input tokens to a trivial prompt; frontier tier not yet
confirmed; full scenario A/B not yet run.
Uncommitted work: routing metrics, strict live Strategy synthesis, tests, and handoff update.
Temporary work: none.

Next exact action: commit this slice; add a reproducible real-model evaluation harness with six
required scenarios and native/off/advisory/active modes; run tiers serially and record failures.
Next files: model-routing response metrics, `tools/local/`, `docs/evidence/pr-g/`.
Next commands: commit; implement harness; run local-low/local-medium/host/frontier evaluation.
Rollback path: discard/revert only this branch; merged PR-F remains intact on main.
