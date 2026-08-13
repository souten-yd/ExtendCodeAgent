# Current Handoff

Updated: 2026-08-13 (Asia/Tokyo)

Current branch: `agent/pr-b-graph-twin-store`
Current PR: not created
Base commit: `40602d3ad8f147c9166e32919f7005da1c11279e`
Latest commit: `40602d3ad8f147c9166e32919f7005da1c11279e`
Current milestone: PR-B Graph / Digital Twin Foundation
Current task: behavior-first Graph contracts, immutable revisions, SQLite store, source snapshot, full/file-level incremental refresh, persistence and benchmark
Task status: investigation in progress; implementation not started

Goal: Adapt KasaneCore's proven revision/store/source lifecycle into the existing host-neutral PR-A foundation without importing semantic, impact, OpenCode/MCP, runtime, or model behavior.

Scope:
- GraphNode/GraphEdge/GraphEvidence/GraphRevision/GraphDelta/GraphSnapshot contracts;
- atomic SQLite revision store, current pointer, historical reads, isolation/conflict handling;
- bounded source snapshots and Git/non-Git fingerprints including untracked state;
- full build and file-level changed/deleted refresh;
- restart/retention/export-import foundation and local real-repository benchmark.

Out of scope:
- semantic/call graph, path/impact, OpenCode/MCP, runtime/test/context, Blueprint/Convergence,
  live model routing, research, and Atlas/Nexus application infrastructure.

Completed:
- fetched and fast-forward checked `origin/main` (already current);
- reviewed the PR-A planning baseline and relevant KasaneCore contracts/rollout tests;
- checked current official OpenCode plugin and MCP surfaces;
- created this PR-A branch and handoff framework.
- implemented the first host-neutral foundation slice: contracts/diagnostics, config resolver,
  capability policy, model-routing contracts/router/fakes, local scripts, and focused tests.
- passed lint/format, strict typecheck, 25 focused unit/architecture tests, package build, and
  generated-wheel archive smoke.
- published and squash-merged PR #2; post-merge `main` fast gates passed again.

In progress:
- extracting behavioral requirements from the four named KasaneCore sources/tests and defining the
  minimum PR-B contract/store boundary.

Not started:
- target tests, implementation, focused validation, benchmark, PR publication and merge.

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

Files currently being edited: PR-B behavioral test design and handoff documentation.

Tests executed at PR-B start:
- `tools/local/all-fast`
- `tools/local/build`
Exact results:
- Ruff lint: `All checks passed!`
- Ruff format: `17 files already formatted`
- mypy 1.17.1 strict: `Success: no issues found in 17 source files`
- pytest 8.4.1: `25 passed in 0.04s`
- sdist/wheel build: success
Benchmarks executed: none; PR-A has no graph/runtime or live-model performance path to benchmark.
Exact results: not applicable; unit suite runtime was 0.04 seconds.
OpenCode version tested: unavailable; `opencode` is not installed locally. Real integration is deferred to PR-D.
ExtendCodeAgent config tested: defaults plus user/project/runtime/session/command overrides; JSONC,
strict validation, immutability, capability off/shadow/advisory/active bounds, endpoint/role config.
LLM/provider tested: deterministic fake local/host/remote adapters only; no real LLM is required for PR-A.
Model routing profile: manual/local-first/frontier-first/cost/latency/quality/adaptive/host-only/local-only contracts; focused tests exercised local-only, host-only, fallback/retry, capability filters, and remote-code policy.
Known failures: none in required local gates.
Known limitations: no Graph/Twin, OpenCode/MCP, or live provider implementation exists in PR-A by design.
Uncommitted work: PR-B start handoff update only.
Temporary files: none.
Experimental code: none.

Next exact action: finish the targeted SQLite schema/apply/snapshot and module refresh inspection, then write target behavioral tests before implementation.
Next files: `../KasaneCore/agent/project_twin/store.py` relevant schema/apply/snapshot slices and `module.py` refresh slices; then `tests/unit/test_graph_contracts.py` and PR-B component tests.
Next commands: targeted `sed` of those slices; `git status --short`; focused pytest after tests exist.
Rollback path: remove/revert only PR-B branch commits; PR-A on `main` remains authoritative.
