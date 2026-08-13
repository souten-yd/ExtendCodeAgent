# Current Handoff

Updated: 2026-08-13 (Asia/Tokyo)

Current branch: `agent/pr-e-context-test-runtime`
Current PR: not created
Base commit: `01efc16b40c5233fc21e725beae158dc87520b8e`
Latest commit: `c689b7e` (real PR-E host and benchmark harness)
Current milestone: PR-E Context + Test Intelligence + Runtime Ingest
Current task: correct measured Python re-export selection recall, then capture exact-head evidence
Task status: in progress

Goal: add revision-aware runtime observations, deterministic test selection and obsolescence, and
bounded context packages without introducing Blueprint, live model routing, or new semantic graphs.

Scope:
- immutable host-neutral runtime/verification observations and truthful freshness reconciliation;
- deterministic graph-based test selection with explicit confidence/full-suite fallback;
- evidence-based test-health states without automatic deletion;
- bounded revision/provenance-aware context packages with smaller weak-model profiles;
- adapter-only normalization of OpenCode tool results after core behavior is proven.

Out of scope:
- Blueprint and Convergence (PR-F);
- live model routing and Strategy (PR-G);
- JS/TS semantic/deep graphs (PR-H);
- Research, requirement traceability, and project convergence (PR-I).

Completed:
- PR-D implementation PR #8 merged as `1cc7fd26`; closeout PR #9 merged as `01efc16b`;
- post-closeout main all-fast and package/TypeScript build passed;
- created this branch from exact `01efc16b`;
- read the PR-E execution-plan section and runtime/test/context migration-audit slices;
- inspected KasaneCore runtime reconciliation/collectors plus context/query behavioral tests and
  current ExtendCodeAgent Impact/application/config call paths;
- added immutable host-neutral runtime observations for all seven planned kinds, revision-aware
  reconciliation, truthful unavailable/failure rollup, and collector-unavailable construction;
- added confidence-aware deterministic test selection plus all six evidence-based test-health
  states with an invariant that no result recommends deletion;
- added bounded revision/provenance/confidence-aware context packages and a materially smaller weak
  profile;
- expanded architecture-boundary coverage to the new `runtime`, `testing`, and `context` packages.
- added durable runtime observation storage with idempotency, payload-collision rejection, restart
  persistence, workspace isolation, and canonical-ref reverse lookup;
- integrated context, runtime ingest/evidence, confidence fallback, and test health into the one
  existing Project Intelligence application/store;
- verified a matching-revision green test becomes stale after an active source refresh, while off
  mode remains inert and creates no database;
- exposed strict sidecar operations for context, runtime ingest, and runtime evidence;
- added stable plugin/MCP `pi_context` and `pi_runtime_evidence` tools plus adapter-only tool-result
  normalization that never infers passed from output presence, never stores output text, and avoids
  recursive evidence for `pi_*` tools;
- measured stable real-host behavior: model-free session shell emitted no tool hook, while a real
  local Qwen 3.6 27B agent `bash` call emitted and persisted one `observed` result with no explicit
  exit metadata; restart retained it and off mode added none;
- ran an initial real-repository benchmark: standard context 100 items/2,131 tokens versus weak 8
  items/148 tokens; the selected symbol had no test candidate and safely fell back to full suite.
- diagnosed the fallback as a Python `src.`/public-package re-export mismatch, added an
  import-evidence-constrained language-owned resolver bridge and collision fixture, and recovered
  two candidates with no fallback in a worktree benchmark.

In progress:
- commit the bounded resolver correction, rerun all real-host/benchmark gates on exact head, and
  record compact PR-E evidence.

Not started:
- exact-head evidence commit, final gates, publication.

Important architecture decisions:
- ADAPT KasaneCore revision matching, truthful unavailable semantics, and bounded context behavior.
- CONSOLIDATE observations with existing ProjectRef/TwinRevisionRef/CanonicalRef/Provenance rather
  than porting Pydantic/Atlas DTOs.
- NEW a dedicated Test Obsolescence engine; KasaneCore has signals but no sufficient independent
  engine for this target.
- DO NOT PORT Atlas runners, PlanPool/context application DTOs, or model-dependent context logic.

Important invariants:
- a passed observation verifies only its matching source/Twin revision;
- unavailable never becomes passed, and collector failure becomes unavailable;
- low-confidence selection can fall back to the full suite;
- obsolescence is evidence/revision/impact based, never file-age-only, and never deletes tests;
- context is bounded, explains inclusion, and preserves revision/provenance/confidence.

Files changed: PR-E domains/store/application, sidecar, stable plugin/MCP tools, adapter tests,
architecture boundary, local harnesses, Python resolver, and handoff.
Files currently being edited: Python resolver collision test, benchmark gate, and decision/handoff.

Exact tests executed: base `tools/local/all-fast`; base `tools/local/build`; focused PR-E pytest;
post-domain `tools/local/all-fast`; focused store/application pytest; post-integration
`tools/local/all-fast`; `tools/local/test-integration`.
Exact results: pure-domain focused `12 passed`; store/application focused `8 passed`; Ruff/mypy
PASS; Python `63 passed in 0.43s`; adapter `6 passed in 4.27s`; Python integration `11 passed in
0.60s`; sidecar/adapter all-fast Python `63 passed in 0.43s`, adapter `9 passed in 4.27s`;
integration `12 passed in 1.18s`, repeated adapter `9 passed in 4.27s`; base build PASS.
Benchmark results: initial worktree sample cold graph/symbol 2,164 ms; standard context p50 28.56 ms
at 100 items/2,131 tokens; weak context p50 28.55 ms at 8 items/148 tokens; test selection p50 30.90
ms with full-suite fallback; DB 5,111,808 bytes; max RSS 45,172 KiB. Exact-head rerun required.
OpenCode version: 1.18.18 (carried from verified PR-D install; not yet exercised for PR-E).
Model/provider: none.
Routing profile: not applicable; live routing is out of scope.
Known failures: the first runtime smoke incorrectly expected session-shell to emit a stable tool
hook and timed out after 20 seconds; corrected after real-host diagnosis.
Known limitations: actual stable `bash` metadata lacked exit status and remains `observed`; the
resolver correction does not claim dynamic-import completeness; context projects Graph nodes only.
Uncommitted work: bounded resolver correction, benchmark candidate gate, and measured-decision docs.
Temporary work: none.

Next exact action: commit the resolver correction, rerun model-free/model-backed OpenCode smoke and
the PR-E benchmark on exact head, then record compact evidence and final gates.
Next files: `tools/local/`, `docs/evidence/pr-e/`, CURRENT_STATUS and handoff.
Next commands: `git diff --check`; commit; `tools/local/opencode-smoke`;
`EXTENDCODEAGENT_SMOKE_MODEL=ollama/qwen3.6-27b-q5_k_m:latest tools/local/opencode-runtime-smoke`;
`tools/local/pr-e-benchmark`; record exact outputs; run all-fast/integration/build.
Rollback path: revert PR-E commits or delete this branch; merged PR-D remains unaffected.
