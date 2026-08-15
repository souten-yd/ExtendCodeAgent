# Next Task

Updated: 2026-08-16 (Asia/Tokyo)

The immediate product target is **OpenCode**, with the OpenCode feature already integrated into
ControlDeck as the primary end-to-end validation host. ExtendCodeAgent remains architecturally
host-neutral, but no second harness is a current production dependency.

Canonical execution documents:

1. `docs/PRODUCTIZATION_AND_MODEL_EVALUATION_PLAN.md`
2. `docs/COMPETITIVE_ANALYSIS_AND_FEATURE_GAP_ROADMAP.md`
3. `docs/CONTROLDECK_OPENCODE_VALIDATION_AND_ADOPTION_PLAN.md`
4. `docs/TRANSPARENT_PI_ORCHESTRATION_PLAN.md`
5. `docs/RUNTIME_ADAPTER_ARCHITECTURE_PLAN.md`
6. `docs/CODEX_PRODUCTIZATION_EXECUTION_GUIDE.md`
7. `docs/handoff/CURRENT_HANDOFF.md`

The competitive and ControlDeck validation plans are strategic overlays. Where older feature-order
language conflicts, use their consolidated sequence while preserving existing architecture invariants.

## Product target

OpenCode is the primary reference runtime and the only production-target runtime during the current
phase. ControlDeck is the first user-facing integration and acceptance environment.

ExtendCodeAgent is positioned as:

> a host-neutral Project Intelligence and Verification Runtime with OpenCode as its primary reference
> runtime and ControlDeck as its first end-to-end product host.

Its differentiated value is:

1. Project Truth — revision-aware Graph/Twin/provenance/freshness;
2. Verification Intelligence — Impact/Test/Runtime/Traceability/Convergence;
3. Task-aware Intelligence — minimum useful PI and progressive expansion;
4. Weak-Local Efficiency — bounded structured evidence and cache-friendly delivery;
5. Cross-agent Consistency — Project Truth across runtime-owned worktrees/tasks when those signals are
   available.

Do not implement a second generic agent harness, team runtime, scheduler, browser, shell/edit engine,
sandbox, worktree/checkpoint engine, generic conversational memory or TUI.

## Mandatory evidence rule

A capability is not adopted because source code exists or unit tests pass. Every new or materially
changed capability MUST be evaluated using the harness/agent/LLM combinations needed to prove its
claimed benefit.

The primary comparison path is ControlDeck -> OpenCode:

- native OpenCode / ExtendCodeAgent absent or disabled;
- `off`;
- `shadow`;
- `advisory`;
- `active` when permitted.

Model tiers are selected according to the feature:

- local-low;
- local-practical;
- host/default when applicable;
- frontier when functioning/allowed.

Repeated runs are mandatory for stochastic local models. A feature that benefits only one model tier
may be retained only with an explicit model-scoped rollout.

For orchestration-specific tests only, OpenCode+OMO and OpenCode+OMO+ExtendCodeAgent may be compared
after the normal OpenCode baseline is stable. OMO is not a release dependency.

## Anti-overfit rule

ControlDeck is the primary repository and integration target, but ControlDeck-only success is
insufficient for `active-default` generic PI.

- Keep a held-out ControlDeck task set outside tuning.
- Run the first implementation/evaluation on real ControlDeck Python/TS/workflow/OpenCode tasks.
- Before generic `active-default`, repeat a small accepted subset on at least one suitable held-out
  repository using the same OpenCode runtime.
- Do not add another harness merely to prove generalization.

ControlDeck headless runs may operate on managed/imported project copies. Record exact workspace
identity, source/managed-copy relation, Git SHA and fingerprint. Never mix Twin/runtime evidence from
different copies because content appears similar.

## Competitive decisions

Adopt when measured useful:

- Atomic-style stable-prefix-aware PI delivery;
- deterministic candidate reduction and bounded decision envelopes for weak models;
- Project Evidence Memory with revision/provenance/invalidation;
- compact PI trace/replay without raw private reasoning transcripts;
- stronger evidence-backed verification/completion;
- runtime-observed worktree/subagent/task identity for future PI-aware parallel development.

Delegate rather than reimplement:

- generic multi-agent/team orchestration;
- background execution/scheduling;
- browser/desktop automation;
- shell/edit/patch;
- sandbox/permissions;
- provider/model management;
- generic session recovery;
- worktree/checkpoint engines;
- host UI.

## Immediate sequence

1. Merge COMP-0 strategy documentation.
2. Create `agent/release-validation-baseline` from synchronized `main`.
3. Run local lint/typecheck/unit/integration/build before production changes.
4. Record ControlDeck commit, ExtendCodeAgent commit, OpenCode version, model/provider profiles,
   managed project/workspace identities and hardware/environment under `docs/evidence/final/`.
5. Establish **ControlDeck -> OpenCode native** baseline before PI optimization.
6. Revalidate plugin/MCP/edit/external-edit/restart/reconnect/off/shadow/advisory paths inside the
   ControlDeck-hosted workflow where applicable.
7. Reproduce frontier/provider failures with PI disabled first. Fix ControlDeck/OpenCode/provider
   lifecycle/config issues before PI core changes.
8. Build versioned ControlDeck real-task and held-out task sets. Compare required runtime/mode/model
   combinations with objective tests/build/behavior evidence.
9. Produce the RV-0 gap report. Attribute every failure to host, runtime, model/provider, PI adapter,
   PI core, task selection, verification or performance before changing code.
10. Run RA-0 only for OpenCode signals actually consumed by TA/verification. Keep OpenCode SDK/types in
    the adapter.
11. Implement TA-0 shadow planning; no task behavior change.
12. Evaluate TA-0 task/capability selection on ControlDeck held-out prompts.
13. Run WL-0 only if measured weak-local failures justify stable-prefix/structured-evidence changes.
14. Implement TA-1 advisory selection using existing PI services.
15. Run VI-0, consolidating confidence calibration, Test Intelligence and Convergence/completion
    correctness. Add Verification Intelligence 2.0 features only for measured failures.
16. Implement TA-2 bounded active only for accepted task/relation/model scopes.
17. Implement TA-3 progressive expansion after repeated model-tier evidence.
18. Implement Runtime Bridge or bounded DFG/Taint/CFG only after repeated ControlDeck tasks prove a
    specific missing relation is the smallest fix.
19. Run RV-FINAL with ControlDeck primary plus held-out repository confirmation. No new feature scope.
20. Implement Project Evidence Memory/PI Trace as P1 after the baseline unless cross-session evidence
    loss is shown to be a release blocker.
21. Run optional OpenCode+OMO complementarity tests only for relevant orchestration claims.
22. Run RA-3 second-harness proof only after the OpenCode production baseline. It proves portability;
    it does not start broad adapter expansion.
23. Run PI-aware parallel/worktree work only after a stable OpenCode/compatible runtime signal path is
    demonstrated. Start advisory/detection-only, not automatic team control.

## Feature adoption states

Use explicit rollout states:

`experimental -> shadow -> advisory -> active-scoped -> active-default`

or `deferred/rejected` when evidence does not justify cost.

A capability advances only when real ControlDeck-hosted OpenCode evidence exists, the necessary
model/agent combinations were tested, critical correctness did not regress, benefit is attributable to
the capability, overhead is bounded, fallback/privacy semantics remain correct, and held-out tasks do
not show critical overfit.

## Resume

```bash
cd /home/souten/ExtendCodeAgent
git switch main
git pull --ff-only origin main
git status --short
tools/local/all-fast
tools/local/test-integration
tools/local/build
git switch -c agent/release-validation-baseline
```

Update `CURRENT_HANDOFF.md` after each major ControlDeck/OpenCode/model/controller evaluation so work
can resume without conversation history.
