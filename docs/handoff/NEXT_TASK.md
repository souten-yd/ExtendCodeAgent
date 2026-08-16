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

**Phase 0 — E5: minimal PI trace as evaluation infrastructure.**

Entry conditions satisfied: E3 has sealed Layer B; E4 has sealed Layer A labels and one resumable
runner for the fixed arm/repository/task/model/repetition matrix.

Scope:

- define a compact append-only trace from plan to selected evidence IDs, Twin/source revisions,
  actual capability modes/depths, model route, verification outcome, fallback and timings;
- store no raw model transcripts or secrets;
- reserve `used_features` for the `VerificationFeature` policy V0 introduces, without implementing
  those later capabilities early;
- emit one trace for every runner arm and demonstrate attributable ablation on one task class;
- make the PI portion replayable from versioned inputs and trace IDs.

Exit evidence: every runner result carries a compact trace reference; one task class demonstrates
that changing one capability arm changes the recorded capability set without changing the sealed
task/oracle identity. See master plan section 8.

Evaluation environment mandated by the user:

- launch/use OpenCode through ControlDeck's existing path where available; do not add ControlDeck
  behavior to the host-neutral ECA core;
- use the existing Llama-compatible Qwen3.6 27B service on port 8090 for `local-practical`; wait for
  wake-up and never start Ollama or a substitute server;
- use Sonnet and Codex through OpenCode's registered GitHub Copilot provider as the two mandatory
  frontier model arms; discover and seal their exact installed identifiers before the first run.

## Why B0 (baseline validation) is not the current task

The sealed task suite, unified evaluation runner/labels and attributable PI trace are not complete. A
baseline measured in that state cannot support the required attribution and keep/demote decisions.
E3–E5 must complete first. See master plan sections 6 and 8.

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
- **E5** minimal PI trace as evaluation infrastructure — current, with a `used_features` shape
  reserved for the `VerificationFeature` policy V0 introduces.

Then **B0** baseline release validation and gap report.

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
git switch -c agent/e3-layer-b-task-suite
```

Update `CURRENT_HANDOFF.md` after each stage.
