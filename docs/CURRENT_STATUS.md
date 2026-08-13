# ExtendCodeAgent — Current Status

Status date: 2026-08-13

## Program state

Overall: **PLANNING BASELINE COMPLETE — IMPLEMENTATION NOT STARTED**

The project currently contains the strategic architecture, KasaneCore migration audit, implementation/local-validation/model-routing plan, and Codex implementation guide. No production Project Intelligence code has been implemented yet.

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
- Low-performance local LLMs and frontier models are both first-class targets.
- Model calls use role-based routing and provider-independent adapters.
- Deterministic analysis is preferred before model reasoning.
- Local tests/E2E/benchmarks are primary evidence; GitHub CI is exceptional.
- Real OpenCode and real-LLM A/B evaluation is required at milestone gates, not on every edit.
- Privacy policy can forbid remote model/source-code use.

## Implementation sequence

| PR | Scope | Status |
|---|---|---|
| Planning PR | architecture, migration audit, implementation/validation/model-routing plan | complete |
| PR-A | foundation contracts, config/capability policy, model-router contracts, local harness | not started |
| PR-B | graph revision/store/source snapshot | not started |
| PR-C | structural/Python semantic/path/impact | not started |
| PR-D | OpenCode adapter + MCP advisory integration | not started |
| PR-E | context/test intelligence/runtime ingest | not started |
| PR-F | Blueprint + task-level Convergence | not started |
| PR-G | live model routing + Strategy | not started |
| PR-H | JS/TS/framework/deep graph expansion | not started |
| PR-I | Research/evidence + project-level convergence | not started |

## Immediate next action

After the planning PR is merged, create PR-A from current `main`. Codex must first inspect the merged repository and KasaneCore reference implementations, then implement only the foundation slice defined in the execution plan.

## Evidence policy

A work package is not complete merely because source files exist or mocked tests pass. Record exact local commands/results and distinguish:

- deterministic unit/component/integration evidence;
- real repository benchmark evidence;
- real OpenCode integration evidence;
- real LLM/model-routing evidence;
- unavailable checks.

Do not mark unavailable evidence as passed.
