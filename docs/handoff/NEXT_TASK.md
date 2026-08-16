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

**Phase 0 — E1: capability gating conformance.**

Entry condition satisfied: E0 (plan consolidation) is merged.

Scope:

- gate `strategy` and `test_obsolescence` through `CapabilityPolicy`;
- gate `call_graph`, or fold it into `semantic` with a recorded decision;
- declare `cfg`, `data_flow`, `state_event`, `side_effects`, `api_schema_db`, `ui_graph` and `memory`
  as `not_implemented` so configuration references them truthfully;
- add an architecture test asserting that every `CapabilityName` either gates a real service or is
  declared unimplemented;
- report capability implementation state through `pi_status`;
- re-verify `off` inertness per capability.

Exit evidence: architecture test green, `tools/local/all-fast`, `tools/local/test-integration`,
`tools/local/build`, and a `handoff/DECISIONS.md` entry for the `call_graph` disposition.

## Why B0 (baseline validation) is not the current task

Ten of twenty-one declared capabilities are not policy-gated, the depth axis is unimplemented, the
evaluation harness is a set of per-PR scripts, and there is no attributable PI trace. A baseline
measured in that state cannot support any keep/demote decision and would have to be repeated. E1–E4
must complete first. See master plan sections 6 and 8.

## Remaining Phase 0 stages

- **E2** capability depth contract (`D0..D4`, orthogonal to `RolloutMode`);
- **E3** unified evaluation runner plus versioned ground-truth label set;
- **E4** minimal PI trace as evaluation infrastructure.

Then **B0** baseline release validation and gap report.

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
git switch -c agent/e1-capability-gating-conformance
```

Update `CURRENT_HANDOFF.md` after each stage.
