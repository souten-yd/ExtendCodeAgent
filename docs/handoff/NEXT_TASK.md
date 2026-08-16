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

**Phase 0 — V0a: verification contract slice (shadow, evaluation-only).**

Entry condition satisfied: E2 (capability depth contract) is complete on
`agent/e2-capability-depth-contract`. Rollout authority and execution depth are independent, every PI
response records its depth, and inferred relations are bounded at use time by the selected depth.

Scope:

- define `SemanticChangeSet` and `VerificationObligation` once as projections over the existing
  Twin/Graph/Impact/Test/Runtime model;
- derive a required verification set from a semantic change;
- keep the slice shadow-only and evaluation-only: no applied behavior change;
- do not add evidence reuse, failure taxonomy, oracle assessment or certificates in this stage;
- keep the result measurable for precision/recall against the executed suite on the pinned corpus.

Exit evidence: contracts defined once; architecture test proving no second truth store; required-set
quality measurable on the pinned corpus. See master plan section 8.

## Why B0 (baseline validation) is not the current task

The verification contract slice, sealed task suite, unified evaluation runner/labels and attributable
PI trace are not complete. A baseline measured in that state cannot support the required attribution
and keep/demote decisions. V0a and E3–E5 must complete first. See master plan sections 6 and 8.

## Phase 0 stage state

- **E0** plan consolidation — done;
- **E1** capability gating conformance — done (see `CURRENT_HANDOFF.md` and `DECISIONS.md`);
- **E2** capability depth contract — done (including the inferred-relation confidence threshold,
  completing the E1 `call_graph` folding decision);
- **V0a** verification contract slice — current, shadow-only, pulled forward from V0 so the
  differentiation hypothesis is measured at B0 instead of Phase 3;
- **E3** Layer B task suite and outcome ground truth (what B0 actually measures), including a
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
git switch -c agent/v0a-verification-contract-slice
```

Update `CURRENT_HANDOFF.md` after each stage.
