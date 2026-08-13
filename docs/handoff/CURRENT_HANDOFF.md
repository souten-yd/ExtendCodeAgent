# Current Handoff

Updated: 2026-08-13 (Asia/Tokyo)

Current branch: `agent/pr-f-blueprint-convergence`
Current PR: not created
Base commit: `f14cfb088f7f51539f3685350d0ec503ec29d7c1`
Latest commit: `1a657ba` (PR-F behavior-first tests)
Milestone: PR-F Blueprint + task-level Convergence
Current task: commit the passing Blueprint/Convergence domain, durability, and policy integration
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
- implemented immutable Blueprint contracts/lifecycle with explicit validation and simple-task
  bypass, plus SQLite restart/workspace isolation;
- implemented schema-independent task convergence with all eight states, all seven deterministic
  decisions, truthful unavailable/stale evidence, and generic dependency traversal;
- integrated both capabilities through the existing application and central CapabilityPolicy;
- proved planned targets do not become Actual Graph nodes and off mode creates no database;
- passed focused domain/store tests, Ruff/format/strict mypy, full Python 75 tests, and adapter 9
  tests.

In progress:
- record the architecture decision and commit the passing vertical slice.

Not started:
- bounded deterministic benchmark, exact-head integration/build evidence, publication.

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

Files changed: new `blueprint/` and `convergence/` domains, shared SQLite store, application
composition, architecture test, unit/integration tests, and handoff.
Files currently being edited: architecture decision and handoff before substantive commit.
Exact tests executed: base gates; focused red pytest; focused domain/store pytest; targeted
Ruff/mypy; post-integration `tools/local/all-fast`.
Exact results: focused 10 passed; final fast gate Ruff/format/mypy PASS, Python `75 passed in
0.95s`, adapter `9 passed` in 4.56s.
Benchmark results: not started.
OpenCode version: not applicable to PR-F; last verified 1.18.18 in PR-E.
Model/provider: none; PR-F deterministic domain work does not use a model.
Routing profile: not applicable.
Known failures: initial red gate failed only for missing target modules; resolved by implementation.
Known limitations: PR-F is task-level only; project-level convergence remains PR-I.
Uncommitted work: passing domain/store/application implementation and documentation update.
Temporary work: none.

Next exact action: commit this passing slice, add a bounded reproducible PR-F benchmark, record
compact evidence, then run integration/build/final gates.
Next files: `tools/local/pr_f_benchmark.py`, `docs/evidence/pr-f/`, handoff/status.
Next commands: commit; implement benchmark; run benchmark, integration, all-fast, build.
Rollback path: discard/revert only this branch; merged PR-E remains intact on main.
