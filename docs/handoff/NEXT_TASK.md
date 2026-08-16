# Next Task

Updated: 2026-08-16 (Asia/Tokyo)

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

**Phase 1 — B0a: environment, integration and screening.**

Entry conditions satisfied: E1-E5 and V0a are complete. The sealed Layer A/Layer B inputs, fixed
matrix, resumable runner, verification projection and attributable append-only trace are available.

Scope:

- freeze ECA/OpenCode/provider/model/repository/workspace/hardware identities;
- establish Existing Project Bootstrap conformance for every evaluation repository before any arm
  runs; exclude and report bootstrap failures instead of attributing them to a capability;
- rerun lint, typecheck, unit, integration, build and adapter/plugin/MCP lifecycle paths;
- reproduce provider failures with PI disabled first and run the blocking OMO coexistence smoke;
- pass the exact-head PI activation gate on port-8090 Qwen, host-default and both GitHub Copilot
  frontier routes, including observed tool use/Twin/provenance; classify every capability route and
  repair any missing route before comprehensive execution;
- run the interleaved 9-cell port-8090 `native/off/active` pilot tranche; only a passing signal may
  continue to 27-cell confirmation, while no effect, missing PI use, provider/timeout failure or
  abnormal active latency requires repair and repeat;
- fix and version the B0a tuning subset, effect threshold and one assigned model tier per ablation;
- run full-tier/repetition `native` and `off` baselines, then the bounded screening pass;
- emit the screening table with `proceed` or `no screened effect`, without promotion/demotion.

Exit evidence: frozen environment and bootstrap records, classified integration results, and a
screening table naming which capabilities proceed to B0b. See master plan sections 7.5 and 8.

The pre-run contract is sealed in `docs/evaluation/b0a-screening-plan-v1.json`. Use
`tools/local/b0a-bootstrap` to acquire exact pins and emit the initial per-repository baseline; do
not run an arm for a repository classified `EXCLUDED_BOOTSTRAP_GAP`.

The original bootstrap evidence excludes KasaneCore and PEDS after 300-second Twin timeouts. Retain
that historical result in old-head schedules/reports. The B1 evidence below supersedes their current
eligibility for repaired-head screening and confirmation. See
`docs/evidence/final/b0a-bootstrap-environment-v1.json`.

The runner has two comprehensive resumable schedules: `b0a-baseline` has 306 cells across full tiers
and `b0a-screening` has 714 local-practical cells, including capability-specific depth arms only for
the four recorded depth claims. Neither may run until the separately sealed four-model
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
`PROCEED_TO_COMPREHENSIVE` result permits the 306/714 schedules.
Use the completed limit pair (context 262,144/output 8,192), not the intermediate output-only
configuration. After merge, prove it with real OpenCode activation before starting the fresh pilot.

The conditional B1 storage blocker is repaired at exact implementation head
`fcd61dff6c66324fed970ecfb1d9b19cae2aa8f7`: KasaneCore and PEDS now pass three-run cold-index
budgets. Keep that merged result, but restart the 306-cell baseline and PI-enabled screen from zero
only after the activation gate, effect pilot and missing runtime-route repairs pass at one merged
exact head. Do not resume or combine old-protocol cells with corrected-head evidence.

The pre-activation baseline stopped after 137/306 cells at old exact head `86e8061`. Preserve it as
diagnostic model-variance history only. After the activation/runtime-route repairs merge, rerun both
baseline and screening from zero at one corrected exact head and protocol.

Evaluation environment mandated by the user:

- launch/use OpenCode through ControlDeck's existing path where available; do not add ControlDeck
  behavior to the host-neutral ECA core;
- use the existing Llama-compatible Qwen3.6 27B service on port 8090 for `local-practical`; wait for
  wake-up and never start Ollama or a substitute server;
- use Sonnet and Codex through OpenCode's registered GitHub Copilot provider as the two mandatory
  frontier model arms; discover and seal their exact installed identifiers before the first run.

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

**B0a** environment/integration freeze and screening is current; B0b confirmation follows only for
capabilities that screen through.

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
git switch -c agent/b0a-baseline-screening
```

Update `CURRENT_HANDOFF.md` after each stage.
