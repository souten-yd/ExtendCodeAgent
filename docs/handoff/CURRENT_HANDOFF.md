# Current Handoff

Updated: 2026-08-13 (Asia/Tokyo)

Current branch: `agent/pr-a-foundation`
Current PR: not created yet; publication is the next action
Base commit: `9623282d00ef98490d5c36ea16256f6fcde260af`
Latest commit: `9623282d00ef98490d5c36ea16256f6fcde260af`
Current milestone: PR-A Foundation
Current task: host-neutral contracts, centralized configuration/capability policy, model-routing contracts and fake adapters, local validation harness, architecture tests
Task status: implementation and local validation complete; commit/PR/merge pending

Goal: Establish the smallest working host-neutral foundation that later KasaneCore migrations and OpenCode adapters can depend on without leaking Atlas or OpenCode types into core.

Scope:
- repository/package bootstrap;
- shared host-neutral contracts and diagnostics;
- immutable centralized configuration resolution;
- feature capability policy with off/shadow/advisory/active modes;
- provider-neutral model router contracts and fake adapters;
- offline local test/build/lint/typecheck harness;
- architecture dependency boundary tests.

Out of scope:
- Graph/Twin persistence, indexing, semantic analysis, impact analysis, MCP server, OpenCode plugin implementation, real model provider calls, real OpenCode/LLM evaluation;
- bulk copying KasaneCore or importing Atlas/Nexus DTOs.

Completed:
- fetched and fast-forward checked `origin/main` (already current);
- reviewed the PR-A planning baseline and relevant KasaneCore contracts/rollout tests;
- checked current official OpenCode plugin and MCP surfaces;
- created this PR-A branch and handoff framework.
- implemented the first host-neutral foundation slice: contracts/diagnostics, config resolver,
  capability policy, model-routing contracts/router/fakes, local scripts, and focused tests.
- passed lint/format, strict typecheck, 25 focused unit/architecture tests, package build, and
  generated-wheel archive smoke.

In progress:
- committing, publishing, verifying the PR head, and merging PR-A.

Not started:
- PR-B Graph/Twin revision/store/source snapshot work.

Important architecture decisions:
- Use the planning baseline's recommended Python-first staged core for PR-A; no TypeScript OpenCode adapter is introduced in this slice.
- Adapt KasaneCore immutable contract and truthful diagnostic semantics, but replace Atlas identities/rollout environment parsing with host-neutral contracts and one centralized resolver.
- Treat OpenCode stable and V2 beta APIs as future adapter-only dependencies; neither may be imported by core.

Important invariants:
- Core must not import OpenCode, Atlas, Nexus, provider SDKs, or adapter packages.
- Unknown/invalid configuration fails explicitly; it never enables a capability accidentally.
- Global off and per-capability off are inert.
- Remote routing obeys the resolved privacy and escalation policy.
- Fake model adapters do not perform network access.

Files changed:
- package metadata/README/ignore rules;
- `src/extendcodeagent/core/*` foundation implementation;
- `tests/unit/*` and `tests/architecture/*`;
- `tools/local/*`;
- required handoff files.

Files currently being edited: PR-A foundation tests and validation documentation.

Tests executed:
- `tools/local/all-fast`
- wheel archive import smoke against `dist/extendcodeagent-0.1.0-py3-none-any.whl`
Exact results:
- Ruff lint: `All checks passed!`
- Ruff format: `17 files already formatted`
- mypy 1.17.1 strict: `Success: no issues found in 17 source files`
- pytest 8.4.1: `25 passed in 0.04s`
- wheel archive smoke: `PASS (version=0.1.0, default_enabled=False)`
Benchmarks executed: none; PR-A has no graph/runtime or live-model performance path to benchmark.
Exact results: not applicable; unit suite runtime was 0.04 seconds.
OpenCode version tested: unavailable; `opencode` is not installed locally. Real integration is deferred to PR-D.
ExtendCodeAgent config tested: defaults plus user/project/runtime/session/command overrides; JSONC,
strict validation, immutability, capability off/shadow/advisory/active bounds, endpoint/role config.
LLM/provider tested: deterministic fake local/host/remote adapters only; no real LLM is required for PR-A.
Model routing profile: manual/local-first/frontier-first/cost/latency/quality/adaptive/host-only/local-only contracts; focused tests exercised local-only, host-only, fallback/retry, capability filters, and remote-code policy.
Known failures: none in required local gates.
Known limitations: no Graph/Twin, OpenCode/MCP, or live provider implementation exists in PR-A by design.
Uncommitted work: all staged PR-A files pending the first commit.
Temporary files: none.
Experimental code: none.

Next exact action: commit the staged PR-A scope, push, open a draft PR, verify exact remote head/diff, then merge after local evidence review.
Next files to inspect after merge: `../KasaneCore/agent/project_twin/contracts.py`, `store.py`, `source_adapter.py`, `module.py`, plus store/source-refresh/durability tests.
Next commands to run: `git diff --cached --check`; `tools/local/all-fast`; `git commit`; `git push`.
Rollback path: before commits, remove only PR-A-created files; after commit, revert the PR-A commit. Do not reset unrelated work.
