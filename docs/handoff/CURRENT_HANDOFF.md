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

In progress:
- review/commit the first pure-domain slice, then add durable observation ingest and integrate the
  existing application service without duplicating business logic.

Not started:
- observation persistence, application/sidecar/plugin integration, benchmarks, A/B, publication.

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

Files changed: new `runtime`, `testing`, and `context` packages; their behavior tests; architecture
boundary; PR-E handoff.
Files currently being edited: first vertical-slice handoff before commit.

Exact tests executed: base `tools/local/all-fast`; base `tools/local/build`; focused PR-E pytest;
post-slice `tools/local/all-fast`.
Exact results: focused `12 passed`; Ruff/mypy PASS; Python `61 passed in 0.48s`; adapter
`6 passed in 4.25s`; base Python sdist/wheel and TypeScript build PASS.
Benchmark results: none yet for PR-E.
OpenCode version: 1.18.18 (carried from verified PR-D install; not yet exercised for PR-E).
Model/provider: none.
Routing profile: not applicable; live routing is out of scope.
Known failures: none yet.
Known limitations: the pure services are not yet persisted or exposed through the application/
adapter, and context currently projects Graph nodes only.
Uncommitted work: coherent first PR-E pure-domain vertical slice and this handoff update.
Temporary work: none.

Next exact action: commit the pure-domain slice, then add behavior-first persistence and
application-integration tests before changing SQLite/application code.
Next files: `src/extendcodeagent/storage/sqlite.py`, `service/application.py`, new integration tests,
then adapter normalization only after the host-neutral path passes.
Next commands: `git diff --check`; commit; inspect store schema/migrations and sidecar request path;
add failing durable-ingest/application query tests; implement; run focused pytest and all-fast.
Rollback path: revert PR-E commits or delete this branch; merged PR-D remains unaffected.
