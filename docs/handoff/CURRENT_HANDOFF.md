# Current Handoff

Updated: 2026-08-16 (Asia/Tokyo)

Current branch: `agent/platform-evaluation-boundary`
Milestone: A-I implementation complete; evidence-driven Productization active
Current task: merge the platform-boundary correction, then start RV-0

## Current source of truth

Canonical strategic overlays:

1. `docs/COMPETITIVE_ANALYSIS_AND_FEATURE_GAP_ROADMAP.md`
2. `docs/CONTROLDECK_OPENCODE_VALIDATION_AND_ADOPTION_PLAN.md`
3. `docs/handoff/NEXT_TASK.md`

Existing architecture/productization plans remain valid unless these overlays explicitly consolidate
execution order.

## Corrected product/platform decision

- Architecture remains host-neutral.
- **OpenCode is the only current production-target runtime.**
- **ControlDeck is the primary evaluation platform, not an ExtendCodeAgent integration target.**
- ExtendCodeAgent integrates with OpenCode only through its normal OpenCode adapter/plugin/MCP
  boundary.
- ControlDeck independently owns all ControlDeck-side intake/install/configuration/launch/UI/job
  integration needed to expose OpenCode or ExtendCodeAgent.
- ExtendCodeAgent MUST NOT add ControlDeck-specific APIs, adapters, lifecycle management, install
  protocols or configuration formats.
- Other harnesses remain research/reference sources and future portability targets, not current
  production dependencies.
- OMO may be used for targeted OpenCode orchestration comparisons but is not a release dependency.

The key distinction is:

> OpenCode is the runtime/product target; ControlDeck is one real-world platform used to evaluate it.

## Mandatory adoption evidence

A feature is not adopted because it is implemented or unit-tested. It must be exercised with the
OpenCode/agent/LLM combinations necessary to prove the claimed effect.

Primary mode comparison:

```text
OpenCode native
OpenCode + ExtendCodeAgent off
OpenCode + ExtendCodeAgent shadow
OpenCode + ExtendCodeAgent advisory
OpenCode + ExtendCodeAgent active (where permitted)
```

Use ControlDeck for realistic end-to-end runs, but treat its behavior as experiment-environment
behavior. Add direct OpenCode control runs whenever ControlDeck could materially influence the metric.

Use local-low, local-practical, host/default and functioning frontier tiers as relevant. Repeat
stochastic local-model runs. Record exact OpenCode/ExtendCodeAgent/model/project identities; record
ControlDeck version only as platform metadata when used.

## Anti-overfit and attribution

- reserve held-out ControlDeck tasks/prompts;
- use ControlDeck as the first rich real-task corpus;
- before generic `active-default`, confirm a small subset on a held-out repository with the same
  OpenCode runtime;
- use direct OpenCode controls for metrics sensitive to platform lifecycle/provider/project handling;
- do not credit ControlDeck/OpenCode/model improvements as PI gains;
- classify failures as evaluation-platform, OpenCode runtime, model/provider, PI adapter, PI core,
  task selection, verification or performance.

Copied/managed project workspaces remain separate Twin/workspace identities unless explicitly related.

## Competitive decisions

Adopt into PI only when measured useful:

- stable-prefix-aware / bounded structured evidence for weak local models;
- deterministic candidate reduction and decision envelopes;
- Project Evidence Memory with provenance/revision/invalidation;
- compact append-only PI trace/replay;
- stronger Verification Intelligence and evidence-backed completion;
- runtime-observed worktree/subagent/task identity sufficient for future PI-aware parallel work.

Explicitly do not duplicate runtime/platform-owned team orchestration, scheduler/background manager,
browser, shell/edit engine, sandbox/permissions, provider/model management, generic session recovery,
worktree/checkpoint engine, generic conversational memory, host UI or ControlDeck integration plumbing.

## Updated execution sequence

1. Merge this platform-boundary planning correction.
2. RV-0 OpenCode baseline using ControlDeck as the primary evaluation platform.
3. RV-1 blocking OpenCode/ECA/model-provider repair if measured. ControlDeck-only defects are not ECA
   production scope.
4. RA-0 minimum OpenCode runtime contract used by PI.
5. TA-0 shadow Task-aware planner.
6. WL-0 weak-local evidence protocol if evidence justifies it.
7. TA-1 advisory automatic capability/context selection.
8. VI-0 consolidated confidence/Test Intelligence/Convergence quality work.
9. TA-2 bounded active.
10. TA-3 progressive expansion.
11. conditional Runtime Bridge and bounded deep analysis.
12. RV-FINAL OpenCode production baseline, ControlDeck primary plus held-out repository confirmation.
13. EM-0 Project Evidence Memory/PI Trace if not pulled earlier by measured need.
14. optional OpenCode/OMO complementarity benchmark.
15. RA-3 one second-harness portability proof.
16. MA-0 PI-aware parallel/worktree intelligence after stable runtime identity signals are proven.

## Immediate next work after merge

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

RV-0 first records:

- ExtendCodeAgent exact commit;
- current OpenCode version and OpenCode integration mode;
- model/provider tiers and availability;
- repository/workspace identity and SHA/fingerprint;
- hardware/runtime environment;
- ControlDeck commit/version only when it is the evaluation platform;
- OpenCode-native baseline before PI optimization.

Then execute paired mode/model comparisons and produce `docs/evidence/final/baseline-gap-report.md`
before production feature changes.

Rollback path: switch to synchronized `main`; this branch changes documentation only.
