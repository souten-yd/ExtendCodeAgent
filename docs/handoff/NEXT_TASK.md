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

**Phase 0 — E2: capability depth contract.**

Entry condition satisfied: E1 (capability gating conformance) is complete on
`agent/e1-capability-gating-conformance`. Every `CapabilityName` is now policy-gated, folded into a
gated capability, or declared `not_implemented`, so per-capability ablation is possible for the 13
configurable capabilities.

Scope:

- add the depth axis (`D0..D4`) to the central config with min/max/preferred/auto, orthogonal to
  `RolloutMode` — never encode cost in the rollout mode (master plan invariant 6);
- no adaptive depth selection yet; that is stage C3;
- record the depth used in every PI response;
- surface depth in `pi_status` alongside the capability inventory E1 added;
- no behavior change at default depth.

Exit evidence: config/architecture tests, depth visible in `pi_status`, `tools/local/all-fast`,
`tools/local/test-integration`, `tools/local/build`.

## Why B0 (baseline validation) is not the current task

The depth axis is unimplemented, the evaluation harness is a set of per-PR scripts, and there is no
attributable PI trace. A baseline measured in that state cannot support any keep/demote decision and
would have to be repeated. E2–E5 must complete first. See master plan sections 6 and 8.

## Phase 0 stage state

- **E0** plan consolidation — done;
- **E1** capability gating conformance — done (see `CURRENT_HANDOFF.md` and `DECISIONS.md`);
- **E2** capability depth contract — current;
- **E3** Layer B task suite and outcome ground truth (what B0 actually measures), including a
  mandatory cross-boundary GUI/runtime causal task class;
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
git switch -c agent/e2-capability-depth-contract
```

Update `CURRENT_HANDOFF.md` after each stage.
