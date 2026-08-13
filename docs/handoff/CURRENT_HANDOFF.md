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
  current ExtendCodeAgent Impact/application/config call paths.

In progress:
- host-neutral contract shape and behavior-first tests for freshness, truthful unavailable state,
  test-selection fallback, obsolescence states, and bounded context.

Not started:
- production PR-E modules, persistence/adapter integration, benchmarks, A/B, publication.

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

Files changed: PR-E task-start handoff only.
Files currently being edited: behavior tests and new host-neutral PR-E contracts/services next.

Exact tests executed: base `tools/local/all-fast`; base `tools/local/build`.
Exact results: base Ruff/mypy PASS; Python `49 passed in 0.28s`; adapter `6 passed in 4.26s`;
Python sdist/wheel and TypeScript build PASS.
Benchmark results: none yet for PR-E.
OpenCode version: 1.18.18 (carried from verified PR-D install; not yet exercised for PR-E).
Model/provider: none.
Routing profile: not applicable; live routing is out of scope.
Known failures: none yet.
Known limitations: no PR-E behavior is implemented or claimed at this checkpoint.
Uncommitted work: task-start handoff.
Temporary work: none.

Next exact action: add behavior-first unit/integration tests and minimal host-neutral contracts for
RuntimeObservation, freshness reconciliation, selection fallback, obsolescence, and context budgets.
Next files: `tests/unit/`, `tests/integration/`, then `src/extendcodeagent/runtime/`,
`src/extendcodeagent/testing/`, and `src/extendcodeagent/context/` as justified by tests.
Next commands: inspect current contracts/GraphSnapshot/ImpactService; add failing tests; run focused
pytest; implement the smallest coherent vertical slice; rerun focused tests and all-fast.
Rollback path: revert PR-E commits or delete this branch; merged PR-D remains unaffected.
