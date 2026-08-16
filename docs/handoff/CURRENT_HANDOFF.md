# Current Handoff

Updated: 2026-08-16 (Asia/Tokyo)

Current branch: `agent/plan-cleanup-and-review-followups`
Milestone: A-I implementation complete; Phase 0 (evaluation enablement) active
Current task: E0/E1 and both plan passes are merged to `main` (`86a6a37`); next is stage E2

## Plan review pass (2026-08-16)

A full read-through corrected three residual inconsistencies (Evidence Memory at both P0 and P1;
`D0` meaning both a depth level and a Phase 5 stage, now `X0`/`X1`; B0's ablation sweep saying 14
instead of 13) and closed four scope gaps: a new stage **E3** defines the Layer B task suite before
the runner exists, §7.2 gains numeric Layer C budgets, invariant **8** treats repository content as
untrusted input, and §10.2 adds program-level stop and pivot criteria. The moat is restated as
Verification Intelligence with Project Truth as substrate, scored against a new code-intelligence
column in the competitive analysis. Full rationale in `DECISIONS.md`.

Phase 0 is now E0–E5; the former E3/E4 became E4/E5.

## External review follow-ups (2026-08-16)

An external review confirmed the plan direction and raised six points. Its top finding — E1 and the
corrections not being on `main` — was correct and is resolved: the stacked PRs #34/#35 had merged into
their intermediate bases rather than `main` (GitHub retargets a stacked PR only when its base branch is
deleted), and PR #36 merged the full content forward. The other five are applied:

- **Existing Project Bootstrap** is now a B0 entry condition, per evaluation repository.
- **E3 must include a cross-boundary GUI/runtime causal task**, framed as a measurement of how far
  current PI follows the chain. `ui_graph` stays `not_implemented`.
- **V0 defines `VerificationFeature`** so the V-series is ablatable from the inside, without adding
  `CapabilityName` members. E5's trace shape widened to accept `used_features`.
- **OMO coexistence smoke** becomes blocking gate 17 at B0/R0; the full benchmark stays P4.
- **"moat" downgraded to "primary differentiation hypothesis"**, resolving a contradiction with §5.

Invariant 8 was also clarified so it does not read as forbidding explanations.

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
         -> E3 Layer B task suite -> E4 evaluation runner + labels -> E5 minimal PI trace
Phase 1  B0 baseline validation and gap report -> B1 blocking repair (conditional)
Phase 2  C0 runtime contract -> C1 shadow planner -> C2 weak-local (conditional)
         -> C3 advisory selection + adaptive depth
Phase 3  V0 verification contracts -> V1 calibration -> V2 required verification set
         -> V3 evidence reuse -> V4 failure-driven re-evaluation -> V5 observability (conditional)
Phase 4  A0 bounded active -> A1 progressive expansion
Phase 5  X0 runtime bridge (conditional) -> X1 bounded deep analysis (conditional)
Phase 6  R0 production-capable baseline
Phase 7  P0 evidence memory -> P1 conformance -> P2 second harness -> P3 parallel intelligence
         -> P4 comparative benchmark
```

B0 does not start before E1-E5 are complete.

## Future ControlDeck deep integration

The user expects ControlDeck may integrate OpenCode more deeply later. That future possibility does
not change today's ExtendCodeAgent plan.

Only introduce a distinct `ControlDeck + OpenCode` evaluation condition after an implemented
ControlDeck change is shown to alter relevant session/tool/context/model/workspace/verification or
multi-agent semantics. Until then, treat it as OpenCode.

## Stage E1 — done on this branch

Delivered:

- `strategy` gated at `build_strategy`, `test_obsolescence` gated at `evaluate_test_health`, both
  through the shared `CapabilityPolicy.require_explicit_use` in `core/policy.py`. No new gate
  mechanism; `service/application.py` now delegates `_require_explicit` to the same helper.
- `test_obsolescence` is independent of `test_selection`: with it off, `pi_tests` still selects tests
  and returns `health: []`.
- `call_graph` folded into `semantic` (`CAPABILITY_FOLDED_INTO`). The rejected independent-gate option
  and its reasons are in `DECISIONS.md`.
- The seven unimplemented capabilities declared in `NOT_IMPLEMENTED_CAPABILITIES`, forced to `off`,
  and rejected with `ConfigError` if configured to a non-`off` mode.
- `tests/architecture/test_capability_gating.py`: AST scan asserting every `CapabilityName` is gated,
  folded into a gated capability, or declared unimplemented; inventory counts pinned at 21/7/1/13 so a
  new capability cannot be added silently.
- `pi_status` reports `implementation`, `mode` and `governed_by` for all 21 capabilities;
  `PiStatus`/`CapabilityStatus`/`RolloutMode` typed in `adapters/opencode/src/client.ts`.
- Per-capability `off` inertness parametrized over all 13 configurable capabilities, in addition to
  the existing global-`off` test.

Evidence: `tools/local/all-fast`, `tools/local/test-integration`, `tools/local/build` all exit 0.
Defaults unchanged — every capability still ships `off`.

## Immediate next work

```bash
cd /home/souten/ExtendCodeAgent
git switch main
git pull --ff-only origin main
git status --short
tools/local/all-fast
tools/local/test-integration
tools/local/build
git switch -c agent/e2-capability-depth-contract
```

E2 adds the depth axis (`D0..D4`) to the central config with min/max/preferred/auto, orthogonal to
`RolloutMode`, with no adaptive selection yet, depth recorded in every PI response and visible in
`pi_status`, and no behavior change at default depth.

Rollback path: switch to synchronized `main`. This branch changes host-neutral core gating, the
OpenCode adapter status types, tests and documentation; it adds no capability and changes no default.
