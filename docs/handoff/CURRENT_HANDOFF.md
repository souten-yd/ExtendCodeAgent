# Current Handoff

Updated: 2026-08-13 (Asia/Tokyo)

Current branch: `agent/pr-f-blueprint-convergence`
Current PR: not created
Base commit: `f14cfb088f7f51539f3685350d0ec503ec29d7c1`
Latest commit: `f14cfb0` (PR-E closeout merge)
Milestone: PR-F Blueprint + task-level Convergence
Current task: implement the host-neutral contracts/services required by the committed red tests
Status: in progress

Completed:
- PR-E implementation PR #10 merged as `fbdfcbd`; closeout PR #11 merged as `f14cfb0`;
- exact closeout main passed `tools/local/all-fast` (Python 64, adapter 9, Ruff/format/mypy) and
  `tools/local/build`;
- created this branch from that exact clean main head;
- read only the PR-F execution-plan and Blueprint/Convergence migration-audit sections;
- located the directly relevant KasaneCore Blueprint/Convergence source and tests.
- classified the slice and added behavior-first unit/integration tests for immutable lifecycle,
  planned/actual separation, all eight states, all seven decisions, truthful evidence, restart, and
  workspace isolation;
- confirmed the initial focused red gate fails only because the new target modules do not yet exist.

In progress:
- implement the minimum host-neutral Blueprint and Convergence domains behind those tests.

Not started:
- host-neutral Blueprint/Convergence contracts and services;
- durable store/application integration;
- focused/final gates, benchmark, evidence, publication.

Architecture classification:
- ADAPT immutable Blueprint revision/lifecycle and convergence evaluator/policy semantics;
- CONSOLIDATE ProjectRef/TwinRevisionRef/evidence with existing contracts;
- REPLACE raw/injected loaders with small explicit snapshot/evidence ports;
- DO NOT PORT Atlas planners/generators/application DTOs or model dependencies.

Scope:
- immutable Blueprint revisions and proposed/reviewed/approved/active/superseded lifecycle;
- mutable active pointer only, validation before activation, durable restart;
- schema-independent TargetSnapshot/ActualSnapshot/VerificationEvidence projection;
- task-level progress states and deterministic decisions;
- optional/simple-task bypass and centralized CapabilityPolicy.

Out of scope:
- live model routing and Strategy (PR-G);
- JS/TS semantic/deep graph (PR-H);
- Research/Traceability and project-level Convergence (PR-I);
- OpenCode/model integration changes.

Files changed: handoff plus behavior-first Blueprint/Convergence unit and integration tests.
Files currently being edited: new host-neutral `blueprint/` and `convergence/` packages.
Exact tests executed: base `tools/local/all-fast`; base `tools/local/build`; focused PR-F red pytest.
Exact results: PASS; Python 64 passed in 0.45s, adapter 9 passed, Ruff/format/mypy PASS, Python and
TypeScript builds PASS.
Benchmark results: not started.
OpenCode version: not applicable to PR-F; last verified 1.18.18 in PR-E.
Model/provider: none; PR-F deterministic domain work does not use a model.
Routing profile: not applicable.
Known failures: focused PR-F tests currently fail collection with expected missing
`extendcodeagent.blueprint` and `extendcodeagent.convergence` modules.
Known limitations: PR-F is task-level only; project-level convergence remains PR-I.
Uncommitted work: behavior-first tests and this test-gate handoff update.
Temporary work: none.

Next exact action: implement immutable contracts, in-memory lifecycle service, pure convergence
evaluator/policy, then run unit tests before SQLite integration.
Next files: `src/extendcodeagent/blueprint/`, `src/extendcodeagent/convergence/`.
Next commands: implement; run focused unit pytest; then add durable repository adapters.
Rollback path: discard/revert only this branch; merged PR-E remains intact on main.
