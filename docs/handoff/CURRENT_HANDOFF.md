# Current Handoff

Updated: 2026-08-13 (Asia/Tokyo)

Current branch: `agent/pr-g-routing-strategy`
Current PR: not created
Base commit: `7b1fb759365cc8dc6e57ad1da9a2870307ac60c8`
Latest commit: `7b1fb75` (PR-F closeout merge)
Milestone: PR-G live Model Routing + Strategy
Current task: implement the adaptive routing/live adapter/Strategy contracts fixed by red tests
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

In progress:
- implement the minimum contracts/adapters/Strategy service behind the committed tests.

Not started:
- live OpenAI-compatible and OpenCode host adapters;
- adaptive router extension and Strategy Core;
- fake/privacy gates, real model A/B, evidence, publication.

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

Files changed: handoff plus behavior-first routing/live-adapter/Strategy tests.
Files currently being edited: model-routing contracts/router/adapters and new Strategy package.
Exact tests executed: base gates; focused PR-G red pytest.
Exact results: PASS; Python 75 passed in 0.60s, adapter 9 passed, Ruff/format/mypy and builds PASS.
Benchmark results: not started.
OpenCode version: 1.18.18.
Model/provider: none yet in PR-G.
Routing profile: to be exercised across configured modes; existing fake tests cover baseline modes.
Known failures: focused PR-G tests fail collection for expected missing target contracts/modules.
Known limitations: current router treats adaptive as local-first and has no live adapters or metrics;
Strategy Core does not exist yet.
Uncommitted work: behavior-first tests and red-gate handoff update.
Temporary work: none.

Next exact action: implement AdaptiveSignals/router ordering, transport-injected live adapters, and
deterministic Strategy contracts/service; run focused tests before real endpoints.
Next files: existing model-routing package and new `src/extendcodeagent/strategy/`.
Next commands: implement; run Ruff/mypy/focused pytest; then real adapter conformance.
Rollback path: discard/revert only this branch; merged PR-F remains intact on main.
