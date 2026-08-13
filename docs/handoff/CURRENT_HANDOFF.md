# Current Handoff

Updated: 2026-08-13 (Asia/Tokyo)

Current branch: `agent/pr-e-context-test-runtime`
Current PR: not created
Base commit: `01efc16b40c5233fc21e725beae158dc87520b8e`
Latest commit: `01efc16` (PR-D closeout merge)
Current milestone: PR-E Context + Test Intelligence + Runtime Ingest
Current task: capture behavior-first contracts and tests before production implementation
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
  mode remains inert and creates no database.

In progress:
- review/commit durable application integration, then add versioned sidecar operations and the
  stable OpenCode tool-result normalization adapter.

Not started:
- sidecar/plugin integration, real OpenCode PR-E evidence, benchmarks, A/B, publication.

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

Files changed: PR-E domain packages/tests, observation schema/store, application integration,
architecture boundary, and handoff.
Files currently being edited: durable application slice handoff before commit.

Exact tests executed: base `tools/local/all-fast`; base `tools/local/build`; focused PR-E pytest;
post-domain `tools/local/all-fast`; focused store/application pytest; post-integration
`tools/local/all-fast`; `tools/local/test-integration`.
Exact results: pure-domain focused `12 passed`; store/application focused `8 passed`; Ruff/mypy
PASS; Python `63 passed in 0.43s`; adapter `6 passed in 4.27s`; Python integration `11 passed in
0.60s`; repeated adapter `6 passed in 4.27s`; base build PASS.
Benchmark results: none yet for PR-E.
OpenCode version: 1.18.18 (carried from verified PR-D install; not yet exercised for PR-E).
Model/provider: none.
Routing profile: not applicable; live routing is out of scope.
Known failures: none yet.
Known limitations: sidecar/OpenCode cannot yet submit/query PR-E operations; context currently
projects Graph nodes only and Test Obsolescence has no persisted report cache (it is recomputed).
Uncommitted work: coherent durable observation/application slice and this handoff update.
Temporary work: none.

Next exact action: commit the durable integration slice, then add sidecar request tests for runtime
ingest/evidence/context and adapter conformance tests for stable tool-result normalization.
Next files: `src/extendcodeagent/adapters/local_sidecar.py`, `tests/integration/test_local_sidecar.py`,
then `adapters/opencode/src/` and adapter tests.
Next commands: `git diff --check`; commit; add failing sidecar tests; implement strict parsing;
inspect stable hook metadata and normalize unknown outcomes as observed, never passed.
Rollback path: revert PR-E commits or delete this branch; merged PR-D remains unaffected.
