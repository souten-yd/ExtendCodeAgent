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

**Phase 0 — E3: Layer B task suite and outcome ground truth.**

Entry conditions satisfied: E1/E2 are merged and V0a is complete on
`agent/v0a-verification-contract-slice`. Evaluation arms can now be identified by capability set and
depth, and required-verification quality has a deterministic precision/recall projection.

Scope:

- deliver versioned and sealed `docs/evaluation/task-suite-v1.json` with stable task IDs, pinned
  repository revisions, natural-language instructions, task classes, machine-checkable success
  oracles, allowed mutation scopes, timeouts and tuning/held-out membership;
- cover symbol/reference lookup, impact, test selection, cross-file refactor, failing-test bug
  localization, requirement tracing, a negative control, an unsafe/insufficient-evidence answer, and
  a real cross-boundary GUI/runtime causal flow;
- pin and justify minimum suite/per-class counts plus a slow-suite repository whose full suite exceeds
  ten minutes;
- execute every task once natively to prove its oracle is reachable and the suite is non-trivial;
- include `OpenCode + OMO + ECA @ local-low` on the required subset, recording `UNAVAILABLE` rather
  than pass if the pinned combination cannot run.

Exit evidence: versioned/sealed manifest; native oracle evidence for every task; native suite success
rate neither 0% nor 100%; recorded tuning/held-out split. See master plan section 8.

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
- **E3** Layer B task suite and outcome ground truth — current (what B0 actually measures), including a
  mandatory cross-boundary GUI/runtime causal task class, an `OMO + ECA @ local-low` arm, and a
  pinned slow-suite repository;
- **E4** unified evaluation runner plus versioned Layer A label set;
- **E5** minimal PI trace as evaluation infrastructure, with a `used_features` shape reserved for the
  `VerificationFeature` policy V0 introduces.

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
