# Current Handoff

Updated: 2026-08-16 (Asia/Tokyo)

Current branch: `agent/opencode-equivalence-evaluation`
Milestone: A-I implementation complete; evidence-driven Productization active
Current task: merge the OpenCode-equivalence planning correction, then start RV-0

## Current source of truth

Canonical strategic overlays:

1. `docs/COMPETITIVE_ANALYSIS_AND_FEATURE_GAP_ROADMAP.md`
2. `docs/OPENCODE_VALIDATION_AND_ADOPTION_PLAN.md`
3. `docs/handoff/NEXT_TASK.md`

Existing architecture/productization plans remain valid unless these overlays explicitly consolidate
execution order.

## Corrected runtime decision

- Architecture remains host-neutral.
- **OpenCode is the only current production-target runtime.**
- Current ControlDeck usage is treated as **ordinary OpenCode usage** for ExtendCodeAgent purposes.
- ControlDeck is not a separate harness, adapter target, runtime contract, or mandatory evaluation
  dimension today.
- ExtendCodeAgent integrates only with OpenCode through its normal adapter/plugin/MCP boundary.
- Do not add ControlDeck-specific APIs, adapters, lifecycle management, install/discovery protocols,
  configuration formats, UI contracts, or special PI behavior.
- ControlDeck may remain a convenient place to run OpenCode, and its repository is a useful real-world
  benchmark candidate, but neither is privileged in product acceptance.
- Other harnesses remain research/reference sources and future portability targets, not current
  production dependencies.
- OMO may be used for targeted OpenCode orchestration comparisons but is not a release dependency.

The key rule is:

> Evaluate OpenCode + ExtendCodeAgent. Do not invent a separate ControlDeck runtime condition until a
> future deep ControlDeck integration is measured to change relevant OpenCode semantics.

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

ControlDeck-launched and terminal-launched OpenCode count as the same condition unless a measured
semantic discrepancy is found.

Use local-low, local-practical, host/default and functioning frontier tiers as relevant. Repeat
stochastic local-model runs. Record exact OpenCode/ExtendCodeAgent/model/repository/workspace
identities and relevant hardware/runtime details.

## Anti-overfit and attribution

- use multiple real repositories rather than treating ControlDeck as the sole acceptance project;
- ControlDeck can remain one mixed Python/JS/TS real-world corpus;
- reserve held-out tasks/prompts and at least one held-out repository outside tuning;
- before generic `active-default`, confirm accepted behavior on held-out repository work;
- do not credit OpenCode/model/provider improvements as PI gains;
- classify failures as OpenCode runtime, model/provider, PI adapter, PI core, task selection,
  verification or performance.

Different repositories, worktrees and copied workspaces remain distinct Twin/workspace identities
unless explicitly related.

## Competitive decisions

Adopt into PI only when measured useful:

- stable-prefix-aware / bounded structured evidence for weak local models;
- deterministic candidate reduction and decision envelopes;
- Project Evidence Memory with provenance/revision/invalidation;
- compact append-only PI trace/replay;
- stronger Verification Intelligence and evidence-backed completion;
- runtime-observed worktree/subagent/task identity sufficient for future PI-aware parallel work.

Explicitly do not duplicate runtime-owned team orchestration, scheduler/background manager, browser,
shell/edit engine, sandbox/permissions, provider/model management, generic session recovery,
worktree/checkpoint engine, generic conversational memory or host UI.

## Updated execution sequence

1. Merge this OpenCode-equivalence planning correction.
2. RV-0 OpenCode baseline and measured multi-repository gap report.
3. RV-1 blocking OpenCode/ECA/model-provider repair if measured.
4. RA-0 minimum OpenCode runtime contract used by PI.
5. TA-0 shadow Task-aware planner.
6. WL-0 weak-local evidence protocol if evidence justifies it.
7. TA-1 advisory automatic capability/context selection.
8. VI-0 consolidated confidence/Test Intelligence/Convergence quality work.
9. TA-2 bounded active.
10. TA-3 progressive expansion.
11. conditional Runtime Bridge and bounded deep analysis.
12. RV-FINAL OpenCode production baseline across representative and held-out repositories.
13. EM-0 Project Evidence Memory/PI Trace if not pulled earlier by measured need.
14. optional OpenCode/OMO complementarity benchmark.
15. RA-3 one second-harness portability proof.
16. MA-0 PI-aware parallel/worktree intelligence after stable runtime identity signals are proven.

## Future ControlDeck deep integration

The user expects ControlDeck may integrate OpenCode more deeply later. That future possibility does
not change today's ExtendCodeAgent plan.

Only introduce a distinct `ControlDeck + OpenCode` evaluation condition after an implemented
ControlDeck change is shown to alter relevant session/tool/context/model/workspace/verification or
multi-agent semantics. Until then, treat it as OpenCode.

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
- current OpenCode version and integration mode;
- model/provider tiers and availability;
- repository/workspace identity and SHA/fingerprint;
- hardware/runtime environment;
- OpenCode-native baseline before PI optimization.

Then execute paired mode/model comparisons across representative and held-out tasks and produce
`docs/evidence/final/baseline-gap-report.md` before production feature changes.

Rollback path: switch to synchronized `main`; this branch changes documentation only.
