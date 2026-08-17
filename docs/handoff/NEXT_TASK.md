# Next Task

Updated: 2026-08-17 (Asia/Tokyo)

## Canonical plan

`docs/PI_MASTER_EXECUTION_PLAN.md` is the single execution plan. It owns product scope, the capability
inventory, the evaluation framework, the stage backlog, and the release gates.

Read order:

1. `docs/PI_MASTER_EXECUTION_PLAN.md`
2. this file
3. `docs/CURRENT_STATUS.md`
4. the design detail listed in that plan's section 2 for the **active stage only**

Do not schedule work from the legacy identifiers (`RV-x`, `TA-x`, `AL-x`, `CV-x`, `TP-x`, `VI-Xx`,
`RA-x`, `EM-0`, `MA-0`). Their mapping is in section 9 of the master plan.

## Current stage

**Phase 1 — B2 OMO coexistence baseline.**

B0 is complete. The exact-main B0b confirmation accounted for 57/57 local-practical cells with 48/48
forced-use compliance, 21 PASS, 36 FAIL and no provider/process/timeout/unavailable outcome. No
covered capability showed a held-out causal PASS delta; four candidates remain
`NO_HELD_OUT_TASK_COVERAGE`. Conditional B1 is `SKIP_NO_ENTRY_CONDITION`: B0 found no remaining ECA
product lifecycle/config/version/provider blocker, and the evaluation-runner worktree-retention defect
is repaired and gated in the B0b closeout. Evidence:
`docs/evidence/final/b0b-confirmation-result-v1.json` and
`docs/evidence/final/baseline-gap-report.md`.

B2 entry is satisfied because B0 is stable and the prior model-free smoke recorded OMO 4.19.4 as
installable with OpenCode 1.18.16. B2 revalidates the exact current OpenCode 1.18.18 tuple. Follow
`docs/OMO_COEXISTENCE_AND_COMPATIBILITY_PLAN.md` §9 only for the active design detail.

Scope:

- record the exact OpenCode / OMO / ExtendCodeAgent version tuple and keep OMO Team Mode off;
- test startup, tool visibility and invocation, session behavior, one basic coding flow and one
  verification flow with both meaningful plugin load orders;
- classify every observation under the existing C0-C6 conflict taxonomy and apply the existing §11
  stop rules; prefer ECA namespace/idempotence fixes and do not patch OpenCode or OMO;
- prove cell/session/workspace isolation and clean shutdown; do not infer coexistence from DOM/tool
  registration alone;
- use only ControlDeck-managed Qwen3.6 27B at `127.0.0.1:8090` for any model-bearing check. Do not
  call or probe Copilot, host-default or unavailable local-low;
- keep claims bounded to compatibility and `active-scoped(local-practical)`. P4 still owns the
  OpenCode / +OMO / +ECA / +OMO+ECA comparative benchmark.

Exit: a reproducible version tuple classified `compatible`, `degraded` or `incompatible`, with every
conflict and load-order result recorded; test/build/evidence/handoff updated; PR reviewed and merged.
Do not widen B2 into C-series planner work or P4 scoring.

Current interruption point: the first exact-main model Bridge passed native, then passed the ECA task
oracle but failed its mandatory runtime-observation control. Repair and merge the awaited post-tool
runtime ingest plus missing-title normalization before resuming model work. Reuse only the sealed
native/no-plugin result after exact input/task/oracle/route verification; rerun ECA and all later
stacks. Do not add the semantic runtime-hook change to the lifecycle-only B0 compatibility manifest.

The B0a execution notes below are retained as immutable history and are not current scheduling
instructions.

The pre-run contract is sealed in `docs/evaluation/b0a-screening-plan-v1.json`. Use
`tools/local/b0a-bootstrap` to acquire exact pins and emit the initial per-repository baseline; do
not run an arm for a repository classified `EXCLUDED_BOOTSTRAP_GAP`.

The original bootstrap evidence excludes KasaneCore and PEDS after 300-second Twin timeouts. Retain
that historical result in old-head schedules/reports. The B1 evidence below supersedes their current
eligibility for repaired-head screening and confirmation. See
`docs/evidence/final/b0a-bootstrap-environment-v1.json`.

The active execution contract is sealed in `docs/evaluation/b0a-quality-target-v2.json`. It changes
only model selection and claim scope: port-8090 `local-practical` Qwen is the sole execution route;
Sonnet/Codex and host-default receive no calls or probes; local-low remains unavailable. Promote the
existing Qwen 54/54 through the existing compatibility audit, Bridge Proof and checkpoint migration
when task/oracle/model limits/ECA semantics match, and rerun only proven residual cells. A sealed
exact-head 54/54 report opens the adaptive B0a screen. The sealed 714 cells remain the hard maximum;
deterministic active-use relevance, depth-output equivalence, compatible reuse and sequential
stopping determine expected/max calls before execution under Master Plan Invariant 11.

The implementation-commit preflight is sealed in
`docs/evidence/final/b0a-adaptive-screening-execution-v1.json`: 102 candidate maximum, 23 compatible
reused cells, 27 expected new calls before the first decision and 79 maximum new calls. Persistent
OpenCode failed oracle-equivalence/speedup adoption and must not be used. After merge, regenerate the
model-free plan at exact main, then run the per-cell adaptive frontier with `--resume`.

The deeper chronology below is retained as immutable history. Its 306-, 162-, and 145-cell
instructions are superseded by quality-target v2 and are not current execution instructions.

The runner has two comprehensive resumable schedules: `b0a-baseline` has 162 cells across the three
quality targets (ControlDeck-managed Qwen, GitHub Copilot Sonnet, and GitHub Copilot Codex)
and `b0a-screening` retains 714 local-practical cells as its exhaustive fallback, including
capability-specific depth arms only for the four recorded depth claims. The local-only adaptive
runner schedules only unresolved exercised cells. Neither may run until the separately sealed three-model
`b0a-activation` gate and staged Qwen `b0a-pilot` pass at the same exact head. The pilot requires a
positive interleaved 9-cell tranche before extending to 27 total, with an objective active PASS gain,
observed task-specific PI and bounded latency; otherwise the next
action is repair and retest, not the full matrix. The first valid 9-cell tranche at `6064e311`
showed active gain +1, but confirmation stopped at 12/27 on a 300,157ms active-symbol timeout.
Therefore the old partial confirmation must not continue. Failure attribution, the six-part PI/model
timing trace, compact task projection, obligation-aware structural coverage, revision-scoped query
indexes, and the missing OpenCode routes are now implemented. `pi_plan` covers Blueprint/Strategy on
`eca-refactor-001`; `pi_verify` covers Traceability/Convergence on `cd-cross-boundary-001`, with
fail-closed route observation in screening. PR #58 merged that slice and same-head activation passed,
but the fresh pilot produced 0/0/0 PASS because Qwen explicitly selected detailed graph views and
never exercised compact projection. PRs #59/#60 now enforce compact views and preserve compact
canonical evidence; exact-head activation passes. One active-only repetition reached PI fact recall
1.0 for all tasks and PASSed test selection, but symbol/impact still changed the final schema. PR #61
merged the exact-schema repair; its exact-head controlled rerun is initial positive evidence:
native/off/active were 0/0/2, with active PI fact recall 1.0 on all tasks. Do not start the remaining
18 confirmation cells yet. Merge the repository-path evidence attribution repair, rerun activation
and the same sealed 9 cells at the new exact head, and require `CONTINUE_TO_CONFIRMATION` before
running repetitions 2-3.

That initial gate passed after PR #62, but confirmation encountered a 420-second Qwen runaway in an
off-control at 14/27. Merge the sealed 8,192-token local-practical output bound, then use fresh
activation and pilot paths; do not resume the superseded-seal report. Only a clean 27-cell
`PROCEED_TO_COMPREHENSIVE` result permitted the then-current comprehensive schedules; the baseline
denominator was subsequently corrected to 162 by the sealed three-route quality target.
Use the completed limit pair (context 262,144/output 8,192), not the intermediate output-only
configuration. After merge, prove it with real OpenCode activation before starting the fresh pilot.

The final new-seal activation and 27-cell pilot now pass. Version and merge the confirmed-effect
evidence, then start the 162-cell baseline with the exact activation/pilot reports;
only after baseline completion start the 714-cell PI screening. Preserve task-level symbol/test
variance and the six-part timing fields in compact evidence.

The compatibility-migrated/resumed target currently has 145/162 valid cells: Qwen and Sonnet are
complete, while GitHub Copilot Codex is 37/54. Its remaining 17 cells are paused because the Copilot
provider reports monthly quota exhaustion. Requeue the 16 misclassified quota responses into
provider attempts, retain the interrupted cell as pending, and resume only after a separate Codex
availability probe succeeds. Do not substitute `host-default`; it is outside the quality target.

That baseline reached 229/306 at `7e58751` before host-default began returning rate limits. Four
provider-gap cells were misreported as task timeouts because OpenCode wrote the retry failure only to
its error log and remained alive until the task deadline. PR #66 at merged head `91b82e3` repairs early provider-gap
detection and classification. Do not directly resume or modify the 229-cell report. Audit it against
the sealed compatibility manifest, run the required multi-provider Bridge Sample, migrate only
validated functional results with provenance, rerun latest activation, and execute only remaining
cells. Legacy runner latency stays separate. The 714-cell screen is now mechanically gated on a
sealed, exact-head 162/162 baseline report.

The conditional B1 storage blocker is repaired at exact implementation head
`fcd61dff6c66324fed970ecfb1d9b19cae2aa8f7`: KasaneCore and PEDS now pass three-run cold-index
budgets. That earlier restart-from-zero instruction is superseded by the sealed compatibility audit,
Bridge proof and checkpoint migration. Continue only the current 162-cell target checkpoint; do not
combine unaudited old-protocol cells with corrected-head evidence.

The pre-activation baseline stopped after 137/306 cells at old exact head `86e8061`. Preserve it as
diagnostic model-variance history only. Its former restart-from-zero instruction is superseded by the
audited migration and current three-route checkpoint.

Evaluation environment mandated by the user:

- launch/use OpenCode through ControlDeck's existing path where available; do not add ControlDeck
  behavior to the host-neutral ECA core;
- use the existing Llama-compatible Qwen3.6 27B service on port 8090 for `local-practical`; wait for
  wake-up and never start Ollama or a substitute server;
- retain the sealed Sonnet and Codex identifiers as historical configuration; do not call or probe
  them while the local-only execution exception is active.

## E5 closeout

E5 exact-head evidence produced 115 unique traces over all 23 arms. The required local-low route was
UNAVAILABLE for every cell, which proves trace coverage but no quality outcome. A real
ControlDeck-managed OpenCode advisory cell recorded `pi_status`-observed capability state and failed
the objective task oracle. The append-only trace rejects conflicting IDs and tampering and stores no
prompt or transcript. See `docs/evidence/final/e5-trace-proof.json`.

## Phase 0 stage state

- **E0** plan consolidation — done;
- **E1** capability gating conformance — done (see `CURRENT_HANDOFF.md` and `DECISIONS.md`);
- **E2** capability depth contract — done (including the inferred-relation confidence threshold,
  completing the E1 `call_graph` folding decision);
- **V0a** verification contract slice — done, shadow-only, with no second truth store;
- **E3** Layer B task suite and outcome ground truth — done: 13 sealed tasks, native 4/13 PASS, clean
  756-second PEDS slow suite, and truthful OMO/local-low evidence;
- **E4** unified evaluation runner plus versioned Layer A label set — done: sealed 12-case labels,
  fixed 5,083-cell schedule, exact route proof, checkpoint/resume and metric-key projection;
- **E5** minimal PI trace as evaluation infrastructure — done, including explicit
  planned-versus-observed state provenance and reserved `used_features` shape.

**B0a** environment/integration freeze and observational adaptive screening is complete. The
**B0b entry gate** is current; held-out confirmation starts only after causal correction merges.

## Ablation arms available after E1

13 capabilities can be switched off independently: `graph`, `twin`, `semantic`, `impact`,
`test_selection`, `test_obsolescence`, `context`, `runtime`, `blueprint`, `convergence`, `research`,
`traceability`, `strategy`. `call_graph` has no arm of its own — it is governed by `semantic`. The
seven unimplemented capabilities have no arm and cannot be configured on.

## Standing rules

- OpenCode is the only current production-target runtime. ControlDeck-launched OpenCode is ordinary
  OpenCode; add no ControlDeck-specific code.
- A capability is not adopted because it is implemented or unit-tested. It must be proven with the
  required OpenCode/agent/model arms.
- Never mark unavailable evidence as passed.
- Feature adoption states: `experimental -> shadow -> advisory -> active-scoped -> active-default`,
  or `deferred/rejected`.

## Resume

```bash
cd /home/souten/ExtendCodeAgent
git switch main
git pull --ff-only origin main
git status --short
tools/local/all-fast
tools/local/test-integration
tools/local/build
git switch -c agent/b0b-local-confirmation
```

Update `CURRENT_HANDOFF.md` after each stage.
