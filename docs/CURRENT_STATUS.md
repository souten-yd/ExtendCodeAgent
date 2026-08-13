# ExtendCodeAgent — Current Status

Status date: 2026-08-13

## Program state

Overall: **PR-D OPENCode/MCP IMPLEMENTED — PUBLICATION GATES IN PROGRESS**

The project now contains the strategic planning baseline plus a working Python host-neutral
foundation. PR-A provides shared immutable contracts, centralized JSON/JSONC configuration,
capability rollout policy, provider-neutral model-routing contracts and deterministic fake
adapters, local validation scripts, and architecture-boundary tests.

## Canonical read order

1. `docs/PROJECT_INTELLIGENCE_MASTER_PLAN.md`
2. `docs/KASANECORE_MIGRATION_AUDIT.md`
3. `docs/IMPLEMENTATION_EXECUTION_LOCAL_VALIDATION_PLAN.md`
4. `docs/CODEX_IMPLEMENTATION_GUIDE.md`
5. this file
6. active PR/task source and tests

## Accepted architectural baseline

- OpenCode remains the agent runtime; ExtendCodeAgent is a host-independent Project Intelligence layer.
- OpenCode-specific APIs remain behind replaceable adapters.
- KasaneCore is a behavioral/reference source, not a directory-copy dependency.
- Reuse/adaptation is preferred over parallel reimplementation.
- Project Graph/Digital Twin/Impact are the first functional foundation.
- Major capabilities are independently configurable and support off/shadow/advisory/active rollout.
- Low-performance local LLMs, practical local coding models, OpenCode host/default models, and frontier models are all first-class targets.
- Model calls use role-based routing and provider-independent adapters; exact model names are configuration, not domain constants.
- Routing supports local-first/frontier-first/host-only/local-only and adaptive/cost/latency/quality policies with explainable escalation/fallback.
- Weak local models receive smaller structured evidence and deterministic candidate sets rather than large repository dumps.
- Privacy policy can forbid remote model/source-code use and remote escalation.
- Deterministic analysis is preferred before model reasoning at every model tier.
- Local tests/E2E/benchmarks are primary evidence; GitHub CI is exceptional.
- Real OpenCode and real-LLM A/B evaluation is required at milestone gates, not on every edit.

## Implementation sequence

| PR | Scope | Status |
|---|---|---|
| Planning PR | architecture, migration audit, implementation/validation/model-routing plan | complete |
| PR-A | foundation contracts, config/capability policy, model-router contracts, local harness | complete |
| PR-B | graph revision/store/source snapshot | complete |
| PR-C | structural/Python semantic/path/impact | complete |
| PR-D | OpenCode adapter + MCP advisory integration | in progress |
| PR-E | context/test intelligence/runtime ingest | not started |
| PR-F | Blueprint + task-level Convergence | not started |
| PR-G | live model routing + Strategy | not started |
| PR-H | JS/TS/framework/deep graph expansion | not started |
| PR-I | Research/evidence + project-level convergence | not started |

## Immediate next action

Complete PR-D publication and merge after final exact-head gates. PR-C provides
deterministic structural/Python AST facts, analyzer-owned Python alias resolution, persisted
dependency-aware refresh, bounded path/impact traversal, weakest-link confidence, uncertainty,
explanations, and test-candidate projection. Curated FP/FN review and real-repository repeated-query
measurements are recorded under `docs/evidence/pr-c/`; PR #6 merged as `ef6db532`.

PR-A intentionally has no real OpenCode or real-LLM claim. Live host integration remains PR-D;
live model routing remains PR-G. PR-D now adds a stable OpenCode 1.18.18 TypeScript plugin, six
bounded tools, an authenticated versioned local sidecar, a shared MCP server, coalesced background
events, restart/reconnect handling, and a measured filesystem-watcher fallback isolated to the
adapter. Real model-free OpenCode evidence is recorded under `docs/evidence/pr-d/`; native/off/
shadow/advisory behavior was exercised without transmitting source to a model.

The local PR-A gates passed on Python 3.12.3: Ruff lint/format,
strict mypy, 25 unit/architecture tests, sdist/wheel build, and wheel-archive import smoke.

PR-B adds file-level Graph facts, immutable Twin revisions, atomic/restart-safe SQLite persistence,
historical snapshots, workspace isolation, expected-head conflicts, bounded source fingerprints,
file-level refresh/invalidation, retention and integrity-checked export/import. Semantic/Impact and
host/model integration remain deliberately absent. The recorded real-repository benchmark shows
correct incremental behavior but only a 1.9% latency advantage on a 50-file repository.

PR-C's current real-repository sample indexed 64 files into 423 nodes and 2,194 edges in
623.969 ms. A dependency-aware two-file incremental refresh took 282.761 ms. One hundred repeated
impact queries had p50 0.0649 ms; the separate lexical `rg` candidate baseline had p50 2.2538 ms.
These are latency measurements, not a claim that graph impact and lexical search have equal quality.

The reproducible PR-D smoke measured alternating three-run startup medians of 1,043 ms native and
1,069 ms plugin-enabled (+26 ms), then observed tool and external edit refreshes at 151 ms, MCP
connection/reconnection, three durable revisions, and no off-mode revision change. The raw plugin
samples include a 3,229 ms outlier; this is functional smoke evidence, not a stable distribution.

## Evidence policy

A work package is not complete merely because source files exist or mocked tests pass. Record exact local commands/results and distinguish:

- deterministic unit/component/integration evidence;
- real repository benchmark evidence;
- real OpenCode integration evidence;
- real LLM/model-routing evidence;
- unavailable checks.

Planning documents are design evidence only. They do not count as implementation, build, test, real-host, or real-model evidence.

Do not mark unavailable evidence as passed.
