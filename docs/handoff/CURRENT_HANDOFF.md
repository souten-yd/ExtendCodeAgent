# Current Handoff

Updated: 2026-08-13 (Asia/Tokyo)

Current branch: `agent/pr-g-routing-strategy`
Current PR: not created
Base commit: `7b1fb759365cc8dc6e57ad1da9a2870307ac60c8`
Latest commit: `b4548c7` (PR-G behavior-first tests)
Milestone: PR-G live Model Routing + Strategy
Current task: commit passing adaptive routing/live adapter/Strategy core slice
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

In progress:
- commit the passing core slice, then exercise real local/host transports and add metrics harness.

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
Exact tests executed: base gates; focused red; focused Ruff/mypy/pytest.
Exact results: PASS; Python 75 passed in 0.60s, adapter 9 passed, Ruff/format/mypy and builds PASS.
Benchmark results: not started.
OpenCode version: 1.18.18.
Model/provider: none yet in PR-G.
Routing profile: to be exercised across configured modes; existing fake tests cover baseline modes.
Known failures: initial red collection failure resolved by implementation.
Known limitations: current router treats adaptive as local-first and has no live adapters or metrics;
Strategy Core does not exist yet.
Uncommitted work: passing adaptive/live-adapter/Strategy implementation and handoff update.
Temporary work: none.

Next exact action: commit this slice; add execution wall-time/tier accounting and a reproducible real
adapter/model evaluation harness; exercise Ollama local and OpenCode host paths serially.
Next files: model-routing response metrics, `tools/local/`, `docs/evidence/pr-g/`.
Next commands: commit; implement harness; run local/host conformance; record unavailable tiers.
Rollback path: discard/revert only this branch; merged PR-F remains intact on main.
