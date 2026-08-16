# Failure-Driven PI Re-evaluation Plan

> **Consolidated 2026-08-16.** Design detail for failure triage. Its implementation sequence is superseded; see stages V0 and V4 of `docs/PI_MASTER_EXECUTION_PLAN.md`.

Status: canonical refinement
Date: 2026-08-16
Scope: Test/Verification Portfolio Intelligence, failure triage, adaptive PI expansion, Test Intent, Oracle quality, Test Obsolescence, Convergence

## 1. Decision

ExtendCodeAgent MUST treat an unexpected verification failure as **new revision-aware evidence** that may invalidate assumptions in the current Project Intelligence model.

The default interpretation is neither:

```text
FAIL -> production implementation is wrong
```

nor:

```text
FAIL -> the test is stale/obsolete
```

Instead:

```text
verification failure
  -> ingest FailureEvidence
  -> check Test Intent against current Requirement / Blueprint / accepted behavior
  -> check Oracle quality against the actual Verification Obligation
  -> check fixture/mock/helper freshness
  -> check harness/environment/runtime validity
  -> localize the failed obligation/boundary
  -> expand only relevant PI scope/depth when unresolved
  -> classify the root cause with evidence
  -> recompute the Change Package and Required Verification Set
  -> rerun only newly required evidence
```

The target semantic is:

> During the `VERIFYING` stage, FAIL means the candidate revision does not yet satisfy the accepted verification model. PI must then determine whether the mismatch comes from production implementation, Test Intent/specification drift, test implementation, Oracle defect, stale fixture/mock, environment/runtime, nondeterminism, harness/tooling, or a PI model miss.

This document refines and must remain consistent with:

- `TEST_PORTFOLIO_INTELLIGENCE_AND_BROAD_EVALUATION_PLAN.md`;
- `VERIFICATION_OBLIGATION_AND_TEST_EXECUTION_PLAN.md`;
- `COMPOSITIONAL_VERIFICATION_AND_EVIDENCE_REUSE_PLAN.md`;
- `ADAPTIVE_CAPABILITY_LEVELS_AND_TARGETED_VERIFICATION_PLAN.md`;
- `TRANSPARENT_PI_ORCHESTRATION_PLAN.md`.

## 2. Pre-change goal: eliminate expected specification-driven failures

Before implementation, PI should analyze the requested change and include known production/test/evidence effects in one Change Package.

```text
Requirement / task change
  -> Semantic Change Plan
  -> Impact Closure
  -> production-code impact
  -> Test Intent impact
  -> reusable-evidence impact
  -> Change Package
```

Candidate pre-change classifications:

- `KEEP`;
- `UPDATE`;
- `OBSOLETE_CANDIDATE`;
- `REPLACE_CANDIDATE`;
- `CREATE_REQUIRED`;
- `REUSE_EVIDENCE`;
- `INVALIDATE_EVIDENCE`;
- `UNKNOWN_REVIEW_REQUIRED`.

The goal is to avoid this wasteful sequence:

```text
implement new behavior
 -> run old-specification test
 -> fail
 -> investigate
 -> discover the test was expected to change with the specification
```

When Test Intent impact is sufficiently known before implementation, update/replace/remove the affected test as part of the same planned change.

## 3. Test Intent is a first-class diagnostic object

A test file/function is an implementation artifact. `TestIntent` describes **what the test is supposed to prove**.

Candidate `TestIntent` fields:

- stable intent id;
- source Requirement / Blueprint / regression / behavior reference;
- covered Verification Obligation ids;
- expected behavior/outcome;
- relevant input partitions / preconditions;
- evidence layer: unit/component/integration/contract/e2e/runtime/gui/etc.;
- accepted environment/runtime assumptions;
- provenance;
- confidence/uncertainty;
- lifecycle state: current/update-required/spec-conflict/obsolete-candidate/etc.

A failed test MUST NOT be marked obsolete simply because it failed. `OBSOLETE_CANDIDATE` requires independent specification evidence, for example:

- an explicit superseding Requirement;
- an accepted Blueprint/decision change;
- an accepted Semantic Change whose new obligation conflicts with the old Test Intent;
- evidence that the old behavior is removed/unreachable and no unique regression/calibration value remains.

If the requirement relationship is ambiguous, keep the test as `SPEC_CONFLICT_CANDIDATE` or `REVIEW_REQUIRED`.

## 4. Oracle Quality is a first-class diagnostic object

A test may execute the correct path but still have a defective Oracle/assertion.

The Oracle must answer the Verification Obligation at the correct observation layer.

Example:

```text
Obligation:
  pressing Start causes the actual game/process/session to reach Running

Weak Oracle:
  assert HTTP response == 200

Relevant Oracle:
  backend accepted launch
  AND target process/session is observed Running
  AND user-visible state becomes Running where required
```

Candidate Oracle-quality checks:

- assertion observes the claimed obligation rather than an implementation detail;
- expected value comes from an independent requirement/contract rather than the same possibly broken implementation;
- assertion is discriminating rather than vacuous/always-pass;
- positive/negative/failure branch matches Test Intent;
- mocked evidence is not presented as real runtime evidence;
- GUI/cross-boundary tests observe required final outcome, not only click/callback/API-success;
- required timing/state/resource conditions are actually observable.

A production implementation may be correct while the test fails because the Oracle is wrong. That is `TEST_ORACLE_DEFECT`, not `IMPLEMENTATION_MISMATCH`.

## 5. Failure taxonomy

Use a bounded, explainable taxonomy.

### `IMPLEMENTATION_MISMATCH`

Production implementation violates a still-current Verification Obligation.

### `TEST_IMPLEMENTATION_MISMATCH`

The test code/update/generation is incorrect while the Test Intent remains valid.

### `TEST_INTENT_STALE_OR_OBSOLETE`

The test encodes behavior that is no longer part of the accepted specification. Requires independent evidence; failure alone is insufficient.

### `TEST_ORACLE_DEFECT`

The assertion does not correctly measure the intended obligation.

### `FIXTURE_MOCK_STALE`

Fixture/mock/helper no longer represents the accepted production boundary/state.

### `ENVIRONMENT_RUNTIME`

Browser, external service, DB, dependency/runtime, hardware/process or other environment prerequisite prevents valid observation.

### `NONDETERMINISTIC`

Race/timing/flaky behavior remains unresolved under nominally equivalent conditions.

### `PI_MODEL_MISS`

Earlier PI omitted or misclassified a dependency, Impact relation, Test Intent mapping, Evidence Dependency Closure, boundary condition, invalidation condition or Requirement relationship.

### `EVIDENCE_REUSE_MISS`

Compositional Verification reused evidence that should have been invalidated or whose boundary assumptions were incompatible.

### `HARNESS_TOOL_FAILURE`

Runner/collection/setup/command/adapter/tooling failed before a meaningful behavior observation was obtained.

### `SPECIFICATION_UNRESOLVED`

Available specification sources are contradictory or insufficient to determine whether production or test intent is correct.

## 6. Result-state semantics

Do not collapse everything into PASS/FAIL.

At minimum preserve:

- `PASS` — required observation satisfied;
- `FAIL` — meaningful observation contradicts a current obligation;
- `ERROR` — harness/setup failed before a valid observation;
- `UNAVAILABLE` — required runtime/provider/environment unavailable;
- `FLAKY` — repeated equivalent runs disagree;
- `STALE` — test/evidence does not apply to current revision/assumptions;
- `CONFLICTED` — credible evidence disagrees;
- `INCONCLUSIVE` — current evidence is insufficient for safe classification.

Convergence MUST NOT treat `ERROR`, `UNAVAILABLE`, `STALE`, `CONFLICTED` or `INCONCLUSIVE` as either behavioral pass or production-code failure.

## 7. FailureEvidence

Normalize unexpected results into a revision-aware `FailureEvidence` projection or equivalent.

Candidate fields:

- project/workspace identity;
- candidate Twin/source revision;
- Verification Obligation ids;
- Test Intent id;
- test/evidence-provider id;
- expected observation;
- actual observation;
- failed Evidence Segment/boundary when localizable;
- result state;
- runner/tool/command;
- fixture/mock/config fingerprints;
- runtime/environment profile;
- timing/retry metadata;
- changed refs and current Impact context;
- PI mode/depth;
- classification + confidence + reasons;
- provenance.

Do not persist raw private model chain-of-thought.

## 8. Failure localization before broad expansion

Do not immediately re-analyze the whole repository.

Example GUI causal flow:

```text
V1 Start interaction
 -> V2 launch command
 -> V3 backend acceptance
 -> V4 game/process starts
 -> V5 Running state is observable
```

If fresh evidence gives:

```text
V1 PASS
V2 PASS
V3 FAIL
```

start at the V2/V3 boundary:

- payload/schema/serializer/parser;
- backend handler;
- relevant config/feature flags;
- fixture/mock of the boundary;
- changed dependencies/resources;
- runtime observation of backend acceptance.

Expand farther only when the localized evidence cannot resolve the contradiction.

## 9. Re-evaluation order

For a meaningful FAIL, use this default order.

1. **Test Intent / specification consistency** — does the test still represent an accepted obligation?
2. **Oracle quality** — does the assertion actually measure that obligation?
3. **Fixture/mock/helper freshness** — are test doubles/current boundary assumptions valid?
4. **Harness/environment/runtime validity** — did the test reach a meaningful observation?
5. **Impact / Evidence Dependency Closure** — did PI miss a changed dependency or invalidation?
6. **Static/runtime reconciliation** — do Graph/Twin assumptions conflict with observations?
7. **Production implementation** — if the above remain valid, classify as implementation mismatch.

This ordering is diagnostic guidance, not permission to change a valid Test Intent/Oracle merely to make the test green.

## 10. Failure-driven progressive PI expansion

Raise only relevant PI capability depth when the current evidence is insufficient.

Example:

```text
D2 verification
 -> unexpected FAIL
 -> missing relation/evidence hypothesis
 -> Impact D2 -> D3
 -> Test Intelligence D2 -> D3
 -> Runtime D1 -> D2
 -> recompute
```

Do not automatically raise Research, CFG, DFG/Taint, Strategy, Blueprint or every capability to D4. Expansion needs an explicit missing-information reason.

If localized D3 remains insufficient and the task/risk justifies it, use bounded D4 for the affected capability only.

## 11. Obsolescence safeguard

Explicitly prohibit the anti-pattern:

```text
test fails
 -> agent calls it obsolete
 -> deletes/weakens test
 -> task appears green
```

Rules:

1. Failure alone never proves obsolescence.
2. Obsolescence requires independent specification/Test Intent evidence.
3. Before removal, preserve unique obligation coverage, evidence diversity, historical regression value, fault-detection value and calibration role.
4. Initial automatic obsolescence handling remains advisory unless an empirically calibrated relation/task scope is promoted to active.
5. Ambiguity yields `SPEC_CONFLICT_CANDIDATE`/`REVIEW_REQUIRED`, not deletion.

## 12. Pre-change prevention remains preferred

Failure-driven re-evaluation is a fallback, not the preferred path.

Before implementation, PI should already identify:

```text
Requirement change
 -> affected production refs
 -> affected Test Intents/tests
 -> affected reusable evidence
 -> updates/removals/new obligations
```

Re-evaluation mainly covers:

- incomplete existing-project bootstrap knowledge;
- uncertain Requirement/Test Intent mappings;
- hidden/dynamic dependency misses;
- implementation diverging from plan;
- defective generated/updated tests;
- Oracle defects;
- runtime-discovered behavior;
- environment/nondeterminism;
- evidence-reuse misses.

## 13. Interaction with Compositional Verification

If a fresh segment test fails or calibration contradicts reused evidence:

1. ingest FailureEvidence;
2. re-check Test Intent and Oracle first;
3. re-evaluate boundary pre/postconditions;
4. expand Evidence Dependency Closure around the failed segment;
5. invalidate reused segments when required;
6. move the Verification Frontier until a safe boundary exists;
7. execute only newly invalidated/residual verification unless policy requires broader/full validation.

A discovered composition miss must be recorded as PI/evidence-reuse calibration evidence.

## 14. Interaction with GUI/runtime verification

For a Start flow, distinguish at least:

- UI action not emitted;
- wrong command constructed;
- backend rejects accepted-intent command;
- backend accepts but process does not start;
- process starts but session/runtime state is wrong;
- runtime state is correct but UI does not update;
- runtime failure occurs but UI falsely reports success;
- browser/test harness failed and produced no valid user-flow observation.

Re-evaluate the failed causal segment. Do not regenerate a monolithic E2E test or rerun every GUI test by default.

Test Intent expresses the expected user-visible behavior. Oracle Quality determines whether the chosen browser/runtime assertions actually prove it.

## 15. Implementation stages and expected failures

Distinguish:

- `IMPLEMENTING` — partial work; known incomplete obligations may fail;
- `MATERIALIZED` — planned production/test changes exist;
- `VERIFYING` — candidate is expected to satisfy the accepted model;
- `VERIFIED` — task-scope obligations have acceptable fresh/composed evidence.

Failure-driven root-cause classification is strongest in `VERIFYING`. Expected intermediate failures during `IMPLEMENTING` should not trigger expensive PI expansion unless they expose an unplanned dependency.

## 16. Recompute after diagnosis

After repair/update:

```text
new candidate revision
 -> recompute SemanticChangeSet
 -> update Impact Closure
 -> update Test Intent/test/evidence states
 -> invalidate affected evidence
 -> recompute Verification Obligations
 -> recompute Required Verification Set
 -> reuse still-valid evidence where allowed
 -> rerun only newly required verification
```

Do not automatically rerun the original full set when PI can justify a smaller evidence-complete set.

## 17. PI self-improvement feedback

`PI_MODEL_MISS` and `EVIDENCE_REUSE_MISS` are first-class product evidence.

Record where practical:

- missing relation/dependency/boundary type;
- wrong Test Intent mapping;
- wrong Oracle-coverage mapping;
- false unaffected classification;
- invalid evidence reuse;
- confidence band/depth that allowed the miss;
- repository/framework/task class;
- whether broader/full/calibration verification exposed it;
- correction that would have prevented it.

Use repeated misses to adjust Graph relations, invalidation rules, Test Intent mappings, Oracle-quality rules, confidence thresholds, runtime bridges and capability-depth recommendations.

Do not globally widen every task after one isolated miss.

## 18. Evaluation

Evaluate this policy on the existing five-project corpus plus GUI/runtime real-world cases.

Compare:

1. immediate `FAIL -> edit production code` behavior;
2. failure re-evaluation without depth expansion;
3. failure-driven localized PI expansion;
4. localized expansion with Test Intent/Oracle checks ablated;
5. broader/full reference verification where practical.

Correctness metrics:

- root-cause classification precision/recall;
- false `IMPLEMENTATION_MISMATCH` rate;
- false obsolete/stale classification rate;
- Test Oracle defect detection rate;
- PI Model Miss detection rate;
- escaped regression / false VERIFIED rate;
- evidence-reuse miss detection.

Efficiency metrics:

- re-analysis scope;
- additional test count;
- verification wall time;
- heavy E2E/full-suite executions avoided;
- unnecessary production-code edits avoided;
- unnecessary test rewrites/deletions avoided;
- time from failure to correct root-cause classification.

## 19. Acceptance gates

Failure-driven re-evaluation may become an active/default behavior only when repeated evidence shows:

1. FAIL is not automatically blamed on production code;
2. FAIL is not sufficient to obsolete/delete/weaken a test;
3. Test Intent and Oracle Quality are explicit first-class diagnostic checks;
4. meaningful behavior FAIL is distinguished from ERROR/UNAVAILABLE/FLAKY/INCONCLUSIVE;
5. localized PI expansion finds hidden impact without routinely escalating to repository-wide analysis;
6. PI/evidence-reuse misses are captured as calibration evidence;
7. GUI/runtime failures are localized by causal segment and final outcome;
8. after repair, verification is recomputed rather than blindly rerunning the old full set;
9. no critical false VERIFIED regression versus broader/full reference validation;
10. Test Intent/Oracle checks measurably reduce unnecessary code edits or wrong test deletion on held-out tasks.

## 20. Implementation sequence

1. Formalize `TestIntent` projection and mappings to Requirement/Blueprint/Verification Obligation.
2. Formalize Oracle-quality representation/checks for current test/evidence providers.
3. Define `FailureEvidence` and result-state taxonomy.
4. Add deterministic failure-localization and bounded root-cause classifier.
5. Integrate Test Intent/Oracle/fixture/environment checks into the re-evaluation order.
6. Add capability-specific progressive depth expansion.
7. Integrate re-evaluation with Evidence Dependency Closure and Verification Frontier.
8. Feed `PI_MODEL_MISS` / `EVIDENCE_REUSE_MISS` into evaluation/calibration evidence.
9. Add GUI causal-segment failure scenarios.
10. Evaluate across the pinned five-repository corpus and held-out rotation before active-default promotion.

## 21. Governing principle

> Prevent expected specification-driven failures before implementation when PI can do so. When an unexpected failure still occurs, treat it as new Project Truth evidence, check Test Intent and Oracle before blaming production code, expand only the unresolved PI neighborhood, and repair the smallest proven cause.
