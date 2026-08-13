# Next Task

Start PR-F Blueprint + task-level Convergence only after the PR-E closeout is merged.

1. Fast-forward `main`, pass `tools/local/all-fast` and `tools/local/build`, then create
   `agent/pr-f-blueprint-convergence` from the exact updated head.
2. Read only the PR-F section of `IMPLEMENTATION_EXECUTION_LOCAL_VALIDATION_PLAN.md`, Blueprint and
   Convergence sections of `KASANECORE_MIGRATION_AUDIT.md`, and directly relevant KasaneCore
   Blueprint/Convergence source and tests.
3. Classify before implementation: ADAPT immutable Blueprint revision/lifecycle and convergence
   evaluator/policy semantics; CONSOLIDATE refs/evidence with existing core and PR-E runtime
   contracts; REPLACE injected loaders with explicit small ports; DO NOT PORT Atlas planners,
   generators, application DTOs, or model dependencies.
4. Add behavior-first tests proving create/revise immutability, reviewed/approved/active/superseded
   transitions, validation before activation, mutable active pointer only, and durable restart.
5. Keep planned and actual namespaces separate. Planned files/symbols must never enter ProjectGraph
   as existing facts merely because a Blueprint names them.
6. Project Blueprint content into a small immutable `TargetSnapshot`; Convergence must consume
   `TargetSnapshot`, `ActualSnapshot`, and `VerificationEvidence`, not Blueprint implementation
   models.
7. Implement task states `absent`, `partial`, `materialized`, `observed`, `verified`, `divergent`,
   `blocked`, and `stale`, plus deterministic decisions `continue`, `complete`, `repair_current`,
   `replan_downstream`, `revise_target`, `request_decision`, and `halt`.
8. Prove unavailable/missing evidence cannot produce `verified` or `complete`; stale revision
   evidence must remain stale. Simple tasks must be able to bypass durable Blueprint.
9. Use the centralized CapabilityPolicy for off/shadow/advisory/active. Do not add independent env
   switches inside feature code.
10. Run focused lifecycle/evaluator/store tests, all-fast, build, restart/integration cases, and a
    bounded deterministic benchmark. PR-F has no OpenCode/model acceptance gate; do not widen it.
11. Publish/merge PR-F and a separate merged-state closeout before PR-G.

Resume:

```bash
cd /home/souten/ExtendCodeAgent
git switch main
git pull --ff-only origin main
git status --short
tools/local/all-fast
tools/local/build
git switch -c agent/pr-f-blueprint-convergence
```

Keep live model routing/Strategy (PR-G), JS/TS semantic/deep graphs (PR-H), and
Research/Traceability/project-level Convergence (PR-I) outside PR-F.
