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

**Phase 2 — C2 Weak-local evidence protocol (conditional entry satisfied).**

C1 is complete at implementation revision `aa446d1` with sealed deterministic evidence in
`docs/evidence/final/c1-shadow-planner-result-v1.json`. All 13 existing manual-reviewed plans were
reused: 9 tuning and 4 repository-held-out. Intent and capability selection precision/recall are 1.0
on both splits, under/over-selection is 0.0, p95 decision latency is 27 us, and no repository I/O,
model call, capability execution, context delivery or behavior change occurred. This proves only
shadow plan selection on the sealed tasks; it does not establish task-success or capability efficacy.

C2 entry is satisfied narrowly by existing B0/C1 evidence: 20 B0b cells had sufficient required PI
facts but an incorrect final schema, `pi_symbol` and `pi_context` dominate serialized injected data,
and C1 can now choose bounded task/capability/depth plans deterministically. Follow Master Plan §8 C2
and `docs/COMPETITIVE_ANALYSIS_AND_FEATURE_GAP_ROADMAP.md` §9.1 as the active design detail:

- define a stable PI envelope separated from task/revision evidence using existing context, trace and
  routing components rather than a new store or planner framework;
- reduce candidates deterministically before any model call and begin with minimum capability/depth/
  context selected by the C1 plan;
- make ID/enum/exact-schema decisions bounded, compress dominant symbol/context/runtime output, and
  expand only on an explicit unresolved evidence gap;
- preserve the sealed task suite, oracle, corpus, effect threshold and B0 evidence; audit compatible
  reuse before generating any new Qwen cell;
- measure request context, PI-attributed output size/tokens where observable, output/reasoning bounds,
  cache/prefix reuse, outcome and wall time on repeated `local-practical` runs;
- keep `local-low` as `UNAVAILABLE / NOT_CONFIGURED` with no claim. Do not call/probe Copilot,
  host-default or local-low, and do not substitute another provider;
- do not pull C3 advisory automatic application, V-series verification mechanisms or P0 evidence
  memory forward.

Exit under the one local-only execution exception: deterministic protocol tests, repeated
local-practical native/off/bounded-evidence evidence showing whether quality/reliability/efficiency
improves, explicit local-low unavailability, full test/build/evidence/handoff, PR review and merge.
Negative or no-effect results remain valid and must not be hidden by loosening the oracle.

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

**B0a/B0b**, conditional B1 disposition, B2, C0 and C1 are complete. **C2** is the current stage.

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
git switch -c agent/task-aware-shadow
```

Update `CURRENT_HANDOFF.md` after each stage.
