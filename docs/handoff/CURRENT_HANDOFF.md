# Current Handoff

Updated: 2026-08-16 (Asia/Tokyo)

Current branch: `agent/competitive-feature-gap-roadmap`
Base: `main` at `d64c75d2707c93a25485d2582b506b176e0a95f5`
Milestone: A-I implementation complete; evidence-driven Productization active
Current task: merge the competitive/ControlDeck-first planning update, then start RV-0

## Current source of truth

The strategy has been refined after comparing OpenCode + ExtendCodeAgent with Atomic Agent, Claude
Code, Codex, Cline and OMO.

New canonical overlays:

1. `docs/COMPETITIVE_ANALYSIS_AND_FEATURE_GAP_ROADMAP.md`
2. `docs/CONTROLDECK_OPENCODE_VALIDATION_AND_ADOPTION_PLAN.md`
3. `docs/handoff/NEXT_TASK.md`

Existing architecture/productization plans remain valid unless the overlays explicitly consolidate
feature order.

## Product decision

- Architecture remains host-neutral.
- **OpenCode is the only current production-target runtime.**
- **ControlDeck's existing OpenCode feature is the primary end-to-end validation host.**
- Other harnesses are research/reference sources and future adapter targets, not current production
  dependencies.
- OMO may be used later for targeted OpenCode orchestration comparisons but is not a release dependency.
- A second independent harness is deferred until after an OpenCode production-capable baseline.

This focus must not leak OpenCode/ControlDeck types into Project Intelligence core contracts.

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

## Mandatory adoption evidence

A feature is not adopted because it is implemented or unit-tested. It must be exercised with the
harness/agent/LLM combinations necessary to prove the claimed effect.

Primary comparison:

```text
ControlDeck -> OpenCode native
ControlDeck -> OpenCode + ExtendCodeAgent off
ControlDeck -> OpenCode + ExtendCodeAgent shadow
ControlDeck -> OpenCode + ExtendCodeAgent advisory
ControlDeck -> OpenCode + ExtendCodeAgent active (only where permitted)
```

Use local-low, local-practical, host/default and functioning frontier tiers as relevant to the claim.
Repeat stochastic local-model runs. Record exact ControlDeck/ExtendCodeAgent/OpenCode/model/project
versions for accepted evidence.

For orchestration-specific questions only, later compare OpenCode+OMO against
OpenCode+OMO+ExtendCodeAgent on identical tasks.

## Anti-overfit rule

ControlDeck is the primary repository and host, but generic PI cannot reach `active-default` solely
from tuning-set success on ControlDeck.

- reserve held-out ControlDeck tasks/prompts;
- run real ControlDeck Python/TypeScript/workflow/OpenCode tasks first;
- before generic active-default, confirm a small accepted subset on at least one suitable held-out
  repository using the same OpenCode runtime;
- do not add a second harness merely to prove generalization.

ControlDeck may run on managed/imported project copies. PI workspace identity, source relation, Git SHA
and fingerprint must be explicit. Evidence from different copies must not be silently merged.

## Updated execution sequence

1. COMP-0 planning update (this branch).
2. RV-0 ControlDeck-first OpenCode baseline and gap report.
3. RV-1 blocking ControlDeck/OpenCode/provider/lifecycle repair if measured.
4. RA-0 minimum OpenCode runtime contract used by PI.
5. TA-0 shadow Task-aware planner.
6. WL-0 weak-local evidence protocol if RV/TA evidence justifies it.
7. TA-1 advisory automatic capability/context selection.
8. VI-0 consolidated confidence/Test Intelligence/Convergence quality work.
9. TA-2 bounded active.
10. TA-3 progressive expansion.
11. conditional Runtime Bridge and bounded deep analysis.
12. RV-FINAL OpenCode production baseline with ControlDeck primary plus held-out repo confirmation.
13. EM-0 Project Evidence Memory/PI Trace if not pulled earlier by measured need.
14. optional OpenCode/OMO complementarity benchmark.
15. RA-3 one second-harness portability proof.
16. MA-0 PI-aware parallel/worktree intelligence after stable runtime identity signals are proven.

No later feature is accepted merely because it appears on this roadmap. Each advancement follows the
adoption gates in the ControlDeck validation plan.

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

- ControlDeck exact commit and OpenCode integration mode;
- ExtendCodeAgent exact commit;
- current OpenCode version;
- model/provider tiers and availability;
- managed project/workspace identity and repository SHA/fingerprint;
- hardware/runtime environment;
- native OpenCode baseline before PI optimization.

Then build versioned ControlDeck tuning and held-out tasks, execute paired mode/model comparisons, and
produce `docs/evidence/final/baseline-gap-report.md` before production feature changes.

Rollback path: switch to synchronized `main`; this planning branch changes documentation only.
