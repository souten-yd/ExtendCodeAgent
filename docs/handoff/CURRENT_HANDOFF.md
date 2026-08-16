# Current Handoff

Updated: 2026-08-16 (Asia/Tokyo)

Current branch: `agent/pi-master-execution-plan`
Milestone: A-I implementation complete; Phase 0 (evaluation enablement) active
Current task: merge the planning consolidation, then start stage E1

## Current source of truth

`docs/PI_MASTER_EXECUTION_PLAN.md` is the single canonical execution plan. It owns product scope, the
capability inventory, the evaluation framework, the stage backlog and the release gates.

1. `docs/PI_MASTER_EXECUTION_PLAN.md`
2. `docs/handoff/NEXT_TASK.md`
3. `docs/CURRENT_STATUS.md`

All other planning documents remain valid as design detail and are registered in section 2 of the
master plan with an explicit disposition. Legacy stage identifiers are mapped in section 9 and must not
be used to schedule work.

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

## Execution sequence

Owned by master plan section 8. Summary:

```text
Phase 0  E0 consolidation -> E1 gating conformance -> E2 depth contract
         -> E3 evaluation runner + labels -> E4 minimal PI trace
Phase 1  B0 baseline validation and gap report -> B1 blocking repair (conditional)
Phase 2  C0 runtime contract -> C1 shadow planner -> C2 weak-local (conditional)
         -> C3 advisory selection + adaptive depth
Phase 3  V0 verification contracts -> V1 calibration -> V2 required verification set
         -> V3 evidence reuse -> V4 failure-driven re-evaluation -> V5 observability (conditional)
Phase 4  A0 bounded active -> A1 progressive expansion
Phase 5  D0 runtime bridge (conditional) -> D1 bounded deep analysis (conditional)
Phase 6  R0 production-capable baseline
Phase 7  P0 evidence memory -> P1 conformance -> P2 second harness -> P3 parallel intelligence
         -> P4 comparative benchmark
```

B0 does not start before E1-E4 are complete.

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
git switch -c agent/e1-capability-gating-conformance
```

E1 gates `strategy`, `test_obsolescence` and `call_graph`, declares the seven unimplemented
capabilities truthfully, adds the architecture test that makes gating total, reports capability
implementation state through `pi_status`, and re-verifies `off` inertness per capability.

Rollback path: switch to synchronized `main`; this branch changes documentation only.
