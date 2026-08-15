# Compositional Verification and Evidence Reuse Plan

Status: canonical refinement
Date: 2026-08-16
Scope: Test/Verification Portfolio Intelligence, evidence reuse, GUI/runtime verification, Convergence

## 1. Decision

ExtendCodeAgent SHOULD avoid rerunning expensive end-to-end verification when Project Intelligence can prove that an already-verified downstream segment remains valid and only a changed upstream or boundary segment needs fresh evidence.

The core model is **Compositional Verification**:

```text
changed project truth
  -> invalidate affected evidence
  -> retain still-valid evidence segments
  -> locate a trusted verification frontier
  -> verify only uncovered/invalidated obligations and boundary connections
  -> compose fresh + reusable evidence
  -> Convergence
```

This is not permission to reuse an old PASS merely because the downstream source files were not edited.
Evidence reuse is allowed only when its validity conditions remain satisfied.

The governing principle is:

> Re-run the smallest evidence-complete portion whose truth may have changed; reuse the rest only when Project Intelligence can justify the composition.

This document refines:

- `VERIFICATION_OBLIGATION_AND_TEST_EXECUTION_PLAN.md`;
- `TEST_PORTFOLIO_INTELLIGENCE_AND_BROAD_EVALUATION_PLAN.md`;
- `ADAPTIVE_CAPABILITY_LEVELS_AND_TARGETED_VERIFICATION_PLAN.md`.

Where older language implies that an unchanged file or a previously passing test is sufficient for reuse, this document is authoritative.

## 2. Verification is a DAG, not always a linear chain

User flows often branch.

For a Start action, a simplified success flow may be:

```text
V1 Start control is actionable
 -> V2 launch intent/command is emitted correctly
 -> V3 backend accepts and interprets the request
 -> V4 target game/process actually starts
 -> V5 UI/session reaches the expected Running state
```

Failure handling is normally a separate branch rather than a successor of successful V5:

```text
V2/V3/V4 failure
 -> V6 truthful failure/error state is produced and surfaced
```

Do not model all verification obligations as `V1 -> V2 -> ... -> V6` merely for convenience.
Use a **Verification Evidence DAG** with explicit branches, joins, preconditions, postconditions and causal boundaries.

## 3. Evidence Segment

Introduce a host-neutral `EvidenceSegment` or equivalent projection representing a verified portion of a causal/behavioral path.

Candidate fields:

- `segment_id`;
- workspace/project identity;
- source/Twin revision where verified;
- covered Verification Obligation ids;
- start boundary / precondition contract;
- end boundary / postcondition contract;
- covered refs/relations/resources;
- evidence providers: tests/runtime/build/typecheck/GUI observation/etc.;
- static and runtime provenance;
- confidence/uncertainty;
- environment/runtime profile;
- config/feature-flag fingerprint;
- dependency/toolchain fingerprint where material;
- state/schema/resource assumptions;
- test harness/browser/platform profile where material;
- verified timestamp and revision distance/churn metadata;
- validity dependencies / invalidation keys;
- current status.

Suggested status values:

- `CURRENT`;
- `REUSABLE`;
- `CONDITIONALLY_REUSABLE`;
- `STALE`;
- `INVALIDATED`;
- `CONFLICTED`;
- `CALIBRATION_DUE`;
- `UNAVAILABLE`.

Do not serialize raw model reasoning as evidence.

## 4. Evidence Dependency Closure

Evidence validity depends on more than the files directly exercised by a test.

For each reusable segment, track a bounded **Evidence Dependency Closure** including the relations that could invalidate the verified behavior.

Depending on the flow, this may include:

- implementation symbols;
- callers/consumers;
- boundary serializers/parsers;
- public API/schema contracts;
- command/IPC payload schemas;
- configuration and feature flags;
- dependency versions or lockfile regions;
- DI/runtime registration;
- DB schema/migrations;
- shared/global state;
- process-launch configuration;
- environment variables;
- resource/file/network assumptions;
- platform/browser/runtime versions when relevant;
- fixture/mock implementations;
- test harness/helpers.

`file unchanged` MUST NOT be used as a synonym for `evidence still valid`.

## 5. Boundary Contract for Safe Composition

Given two evidence segments:

```text
A: V1 -> V3
B: V3 -> V5
```

ECA may infer composed coverage only when their boundary semantics are compatible.

At minimum validate:

1. A's postcondition implies or matches B's accepted precondition.
2. Boundary structural contract is unchanged or proven compatible.
3. Relevant behavioral assumptions are unchanged or explicitly covered.
4. Environment/config/runtime profiles are compatible.
5. B's Evidence Dependency Closure has not been invalidated.
6. No newer conflicting evidence exists.
7. Required freshness/criticality policy permits reuse.
8. Workspace/revision identity is not mixed incorrectly.

A type-compatible boundary alone is insufficient when timing, ordering, retry, side effects, state, authorization or other behavioral assumptions matter.

## 6. Verification Frontier / Evidence Frontier

For each change, compute the nearest boundary beyond which existing evidence remains trustworthy.

Example:

```text
changed V1 implementation
  -> V2 boundary unchanged and verified
  -> downstream V2..V5 evidence reusable
```

The **Verification Frontier** is V2. The fresh verification target is therefore the changed region up to V2, not the entire V1..V5 flow.

If V2's payload semantics changed, the frontier moves downstream until ECA finds a boundary whose contract and evidence remain valid.

If no safe frontier exists, targeted composition must stop and broader integration/E2E verification is required.

## 7. Example: Start button flow

Assume existing evidence establishes:

```text
E_downstream:
V3 backend accepts valid LaunchGameCommand
 -> V4 game process starts
 -> V5 UI/session eventually reaches Running
```

and separate failure evidence establishes:

```text
E_failure:
backend/process launch failure
 -> truthful error propagates to UI
```

A new change modifies only the Start screen/button wiring.

PI finds:

- V1 handler changed;
- V2 command creation may be affected;
- V3 backend contract unchanged;
- V3..V5 dependency closure unchanged;
- failure propagation code/config unchanged;
- runtime profile compatible;
- existing downstream evidence is still within accepted freshness policy.

Then ECA should first search for an existing test that verifies:

```text
V1 user action -> V2 correct command -> V3 accepted boundary
```

If such a current test exists, no new test is required.

If it does not exist, generate/update the smallest test that proves this missing bridge.

After PASS:

```text
fresh V1..V3 bridge evidence
+
reusable V3..V5 downstream evidence
+
reusable failure-branch evidence where its preconditions remain valid
=
composed task-scope verification
```

The old full GUI/game-launch E2E test remains valuable as calibration/release evidence even if it is not executed for every Start-screen edit.

## 8. Test generation suppression

Before generating a new test, Test Portfolio Intelligence MUST ask in order:

1. Is the obligation already covered by current reusable evidence?
2. Is only a boundary connection missing?
3. Does an existing test already cover that boundary at the required revision/confidence?
4. Can an existing test be extended/parameterized without losing intent?
5. Only then: is a new test needed?

This prevents test proliferation caused by generating a new full E2E test for every local change.

Preferred generation target is the **Residual Evidence Gap**, not the entire user flow.

## 9. Evidence reuse versus cached test results

Compositional Verification is not a generic test-result cache.

A test cache usually answers:

> Were these inputs/artifacts already tested?

ECA must answer:

> Does the previous evidence still prove the current verification obligation under the current Project/Twin/runtime assumptions?

Therefore reuse decisions must be revision/graph/contract/evidence aware rather than command-hash-only.

## 10. Freshness and aging

Even structurally valid evidence may become less trustworthy over time or after substantial surrounding churn.

Track signals such as:

- revision distance;
- dependency closure churn;
- config/runtime churn;
- dependency/toolchain upgrades;
- environment/platform changes;
- historical calibration misses;
- flaky evidence history;
- time since last real E2E/runtime observation.

Do not impose one universal TTL. Use evidence type, risk class and evaluation results.

A low-risk pure function unit segment may be reusable for many revisions if its closure is unchanged.
A hardware/process/browser integration segment may require more frequent calibration.

## 11. Critical objections and safeguards

### 11.1 Composition can create false confidence

Two individually passing segments do not automatically prove the composed path.
Boundary pre/postconditions and behavioral assumptions must match.
If compatibility cannot be established, mark the gap unresolved and execute a broader test.

### 11.2 Hidden dependencies can invalidate downstream evidence

Static Graph completeness is imperfect, especially for dynamic registration, globals, environment, plugins, reflection and process boundaries.
Propagate uncertainty. Unknown dependency does not mean unchanged dependency.
Use runtime evidence and periodic full-flow calibration to discover misses.

### 11.3 Upstream changes can alter input distribution without changing the boundary type

For example, V2 may still emit the same command schema but change optional values, ordering, timing or ranges.
Track behavioral/input partitions where possible and invalidate downstream evidence if new values fall outside previously verified assumptions.

### 11.4 Stateful systems can invalidate apparently unchanged segments

Database contents, caches, sessions, files, external services and global process state can change behavior without code changes.
Evidence needing state assumptions must record them or be treated conservatively.

### 11.5 GUI/browser tests are nondeterministic

Animation, async timing, browser versions, network, focus and rendering can produce flakiness.
Do not reuse flaky evidence at the same strength as stable evidence. Record environment and timing-sensitive assumptions.

### 11.6 Too much evidence bookkeeping can cost more than rerunning tests

If the full flow is cheap, or dependency-closure analysis is more expensive than execution, evaluation may recommend running the test instead of composing evidence.
ECA is not required to reuse evidence merely because reuse is possible.

### 11.7 Independent redundancy may be valuable

A full E2E test can catch integration failures that segmented tests miss. Do not delete it solely because segmented evidence usually composes.
Reclassify it as calibration/release/independent evidence when appropriate.

### 11.8 Security and release policy may require end-to-end execution

For high-risk/security/release gates, policy may prohibit evidence reuse for specific obligations or require a fresh end-to-end run regardless of available segments.
Policy outranks optimization.

## 12. Confidence propagation

Do not average segment confidence into an opaque optimistic score.

The composed result should preserve:

- per-segment confidence;
- boundary compatibility confidence;
- unresolved uncertainty;
- freshness;
- evidence type/diversity;
- criticality.

Use conservative/weakest-link semantics for decisions that can produce `VERIFIED`.
A high-confidence upstream segment cannot compensate for an uncertain critical boundary.

## 13. Relationship to capability depth

Depth controls how much effort is spent proving reuse safety.

- `D0`: native/no compositional planning.
- `D1`: reuse only direct, high-confidence, same-runtime evidence with simple closure.
- `D2`: normal semantic dependency closure + boundary contract + revision freshness; recommended target for ordinary work.
- `D3`: cross-layer/API/IPC/resource/runtime evidence reconciliation and richer GUI/runtime boundaries.
- `D4`: deep/high-risk analysis, broad fresh validation, or policy-required full E2E/full suite.

Depth MUST NOT mean "reuse more evidence". Higher depth can invalidate more evidence because it discovers previously unknown dependencies.

## 14. GUI/runtime specialization

GUI Test Intelligence should distinguish at least these evidence layers where applicable:

```text
UI interaction
 -> local handler/state
 -> command/API/IPC boundary
 -> backend/service acceptance
 -> process/resource side effect
 -> runtime/session state
 -> rendered/user-visible outcome
```

Tests may cover one or several layers.

For a changed UI-only segment, a lightweight browser/component/integration test may connect fresh UI behavior to a trusted API/command frontier.

For a changed launcher/process segment, the UI portion may remain reusable while process/runtime evidence is refreshed.

For changed state synchronization, process launch evidence may remain reusable while runtime->UI state propagation is retested.

For final release/calibration, execute representative full user-flow E2E tests that prove the segmentation/composition model has not hidden an integration dependency.

## 15. Existing-project bootstrap

On importing an existing project, ECA should not immediately assume its old test results are composable evidence.

Bootstrap should:

1. build initial Twin/Graph/test inventory;
2. discover candidate user flows and existing tests where possible;
3. map tests/evidence to obligations/segments conservatively;
4. run or observe selected baseline tests to establish fresh evidence;
5. initially classify unmapped/old evidence as unknown/stale rather than reusable;
6. increase reuse capability as calibration confirms relation quality.

This prevents an imported project's historical green state from being mistaken for trusted evidence.

## 16. Portfolio consolidation implications

Compositional verification changes how redundant tests are evaluated.

Example:

- Test A proves UI -> command.
- Test B proves command -> backend acceptance.
- Test C proves backend -> process -> Running.
- Test D proves full UI -> Running E2E.

D is not necessarily redundant even if A+B+C compose.
It may provide independent calibration evidence.

Portfolio Intelligence should classify roles such as:

- `PRIMARY_SEGMENT_EVIDENCE`;
- `BOUNDARY_EVIDENCE`;
- `INDEPENDENT_REDUNDANCY`;
- `CALIBRATION_E2E`;
- `RELEASE_GATE`;
- `REDUNDANT_CANDIDATE`.

Only remove/merge a test when its unique obligation, path, failure-detection and calibration value are all replaceable.

## 17. Runtime algorithm

Suggested bounded deterministic flow:

```text
1. derive SemanticChangeSet
2. compute Impact Closure
3. derive affected Verification Obligations
4. invalidate evidence whose dependency closure intersects relevant semantic changes
5. evaluate remaining evidence validity/freshness
6. construct Verification Evidence DAG
7. find safe Verification Frontier(s)
8. derive Residual Evidence Gaps
9. reuse/update existing tests first
10. generate new bridge/segment test only for uncovered gap
11. execute Required Verification Set with cost-aware scheduling
12. ingest fresh evidence
13. re-evaluate residual gaps and boundary compatibility
14. compose evidence DAG
15. Convergence decides task-scope completion
16. schedule/retain calibration E2E according to policy
```

Do not solve frontier selection with an expensive globally optimal algorithm unless measurements justify it. Prefer explainable bounded graph traversal.

## 18. Evaluation requirements

Use the existing five-project corpus plus GUI/runtime real-world cases.

Measure at least:

### Correctness

- false `VERIFIED` rate;
- evidence-reuse invalidation recall;
- boundary compatibility errors;
- full-E2E-only discovered failures;
- escaped regression rate;
- stale/conflicting evidence reuse rate.

### Efficiency

- heavy tests avoided per task;
- full E2E executions avoided;
- verification wall-time reduction;
- CPU/process/browser time reduction;
- evidence-analysis overhead;
- time-to-VERIFIED;
- new tests avoided because existing/composed evidence was sufficient.

### Portfolio quality

- unnecessary generated tests avoided;
- bridge/segment tests generated versus full-flow tests generated;
- calibration tests retained;
- consolidation recommendations accepted/rejected;
- unique obligation coverage retained after consolidation.

### Ablation

Compare representative tasks with:

1. full-suite/full-E2E every time;
2. ordinary impacted-test selection only;
3. verification-obligation selection without evidence reuse;
4. compositional verification/evidence reuse;
5. compositional verification with one validity signal ablated.

This separates the value of Impact selection from the incremental value of evidence composition.

## 19. Calibration policy

Evidence composition must be audited.

Use fresh end-to-end/full-suite runs for:

- release/final acceptance;
- defined high-risk changes;
- periodic sampling;
- held-out benchmark tasks;
- low-confidence or newly learned boundaries;
- after dependency/runtime/browser/toolchain upgrades;
- after a composition miss is discovered.

When calibration finds a failure that composed evidence missed:

1. classify the missing dependency/contract/state assumption;
2. record the miss;
3. invalidate affected reusable evidence if needed;
4. improve Graph/obligation/boundary validity rules;
5. reduce recommended reuse/depth for the relevant task/repository class until revalidated.

Do not respond to one miss by disabling all evidence reuse globally unless evidence supports that conclusion.

## 20. Acceptance gates

Compositional Verification may become normal/default behavior only when repeated evidence shows:

1. no increase in critical false `VERIFIED` versus full/reference verification;
2. invalidated downstream evidence is conservatively detected;
3. boundary conditions are inspectable and explainable;
4. GUI/runtime causal paths are not reduced to DOM-click assertions;
5. existing fresh evidence prevents unnecessary test generation;
6. expensive E2E/full suites are materially reduced for bounded changes;
7. evidence-analysis overhead does not erase the saved execution cost;
8. periodic full-flow calibration catches model misses and feeds them back into PI quality;
9. user/project policy can force fresh verification where required;
10. evidence reuse never crosses incompatible workspace/revision/runtime identities;
11. D0-D4 and off/shadow/advisory/active remain independent;
12. held-out repository and GUI/runtime scenarios confirm the behavior is not project-specific.

## 21. Implementation sequence

### CV-0 — contracts and shadow planning

- define EvidenceSegment / boundary contract / dependency-closure projection;
- define reuse statuses and invalidation reasons;
- construct evidence DAG and frontier in shadow mode;
- no test suppression yet.

### CV-1 — reuse existing current evidence

- reuse only high-confidence same-workspace/same-runtime evidence;
- expose why each test would run or be skipped;
- compare decisions against full/reference runs.

### CV-2 — residual-gap test suppression/generation

- generate/update tests only for uncovered boundary/segment obligations;
- measure avoided new tests and preserved correctness.

### CV-3 — GUI/runtime compositional verification

- add runtime/GUI boundary evidence needed by real user-flow failures;
- validate UI->API/IPC->backend->process->state->UI paths;
- retain calibration E2E.

### CV-4 — portfolio consolidation integration

- classify calibration/segment/redundant test roles;
- advisory merge/delete proposals only until broad evidence supports stronger automation.

### CV-FINAL — broad adoption gate

- five-repository corpus + held-out rotation;
- real GUI/runtime cases;
- model-tier and ECA/OMO coexistence checks where relevant;
- publish efficiency/correctness tradeoffs and recommended depths.

## 22. Definition of Done

This capability is successful when ECA can explain, for a change:

- which prior evidence became invalid and why;
- which evidence is still reusable and under what conditions;
- the nearest trustworthy verification frontier;
- which residual obligations actually require fresh tests;
- why a new test was or was not generated;
- how fresh and reused evidence compose to support Convergence;
- which expensive E2E/full tests were safely avoided;
- when and why a calibration/full-flow test is still required.

The optimization target is not "run fewer tests" by itself. It is **preserve evidence-complete correctness while avoiding verification work whose truth has demonstrably not changed**.
