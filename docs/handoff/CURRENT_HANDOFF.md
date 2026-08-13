# Current Handoff

Updated: 2026-08-13 (Asia/Tokyo)

Current branch: `agent/pr-e-context-test-runtime`
Current PR: pending creation
Base commit: `01efc16b40c5233fc21e725beae158dc87520b8e`
Latest commit: `47d47cd` (Python re-export test-selection correction)
Current milestone: PR-E Context + Test Intelligence + Runtime Ingest
Current task: publish validated PR-E and merge after remote-head verification
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
- commit exact-head evidence and handoff, publish PR-E, verify the remote head, and merge.

Not started:
- PR-E publication/merge and merged-state closeout.

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
Files currently being edited: compact evidence, final status/handoff, and formatter-only test layout.

Exact tests executed: base `tools/local/all-fast`; base `tools/local/build`; focused PR-E pytest;
post-domain `tools/local/all-fast`; focused store/application pytest; post-integration
`tools/local/all-fast`; `tools/local/test-integration`.
Exact results: final Ruff/format/mypy PASS; Python `64 passed in 0.41s`; adapter `9 passed in
4.26s`; integration `12 passed in 1.21s`; build PASS. Model-free and real-local-model OpenCode
smokes PASS when run serially.
Benchmark results: exact `47d47cd` cold graph/symbol 2,739.11 ms; standard context p50 29.81 ms at
100 items/2,131 tokens; weak context p50 34.15 ms at 8 items/148 tokens; test selection p50 31.33 ms
with two candidates/no fallback; DB 5,152,768 bytes; max RSS 43,984 KiB.
OpenCode version: 1.18.18.
Model/provider: real local `ollama/qwen3.6-27b-q5_k_m:latest` for adapter runtime-event evidence;
8,887 input/33 output tokens, 64,528 ms, cost 0.
Routing profile: not applicable; live routing is out of scope.
Known failures: an initial concurrent execution of both OpenCode smokes caused one shared-database
lock; both passed when rerun serially. The earlier session-shell hook expectation was corrected.
Known limitations: actual stable `bash` metadata lacked exit status and remains `observed`; the
resolver correction does not claim dynamic-import completeness; context projects Graph nodes only.
Uncommitted work: formatting, compact evidence, final status, and handoff sync.
Temporary work: none.

Next exact action: commit evidence/handoff, push the branch, create PR-E, inspect remote diff/head,
merge, then create the small merged-state closeout.
Next files: `docs/evidence/pr-e/`, CURRENT_STATUS and handoff.
Next commands: `git diff --check`; commit; push; `gh pr create`; verify; merge.
Rollback path: revert PR-E commits or delete this branch; merged PR-D remains unaffected.
