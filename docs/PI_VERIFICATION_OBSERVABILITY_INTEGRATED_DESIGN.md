# PI Verification / Observability Integrated Design

> **Consolidated 2026-08-16.** Design detail for observability, environment and certificates. `VI-X0..VI-XFINAL` are superseded; see stages V0 and V5 and the deferred set of `docs/PI_MASTER_EXECUTION_PLAN.md`.

Status: canonical detailed design
Date: 2026-08-16
Scope: Project Intelligence-wide verification refinement using existing ECA capabilities

## 1. Decision

ExtendCodeAgent will strengthen verification by integrating the existing Project Intelligence capabilities rather than creating a separate test platform or a second project model.

The target is an **incremental, evidence-complete verification architecture** in which ECA can answer five questions for every meaningful change:

1. **What changed semantically?**
2. **What can that change affect?**
3. **What must be proven for the candidate revision to be acceptable?**
4. **Which current evidence still proves those obligations, and which evidence was invalidated?**
5. **What is the smallest additional observation/test work required to close the remaining evidence gaps?**

The canonical loop is:

```text
Requirement / Task / Blueprint
  -> Initial or current Digital Twin
  -> Semantic Change Plan / SemanticChangeSet
  -> Impact Closure
  -> Test Intent Impact + Evidence Invalidation
  -> Verification Obligations
  -> Observability Requirement / Gap analysis
  -> Environment Impact / Matrix selection
  -> Existing Evidence DAG + Evidence Diversity
  -> Verification Frontier / Residual Evidence Gaps
  -> Required Verification Set
  -> Cost-aware execution / targeted observation
  -> Runtime / GUI / Test / Build evidence
  -> Failure-driven PI re-evaluation when needed
  -> Compositional Verification
  -> Verification Certificate
  -> Convergence
  -> calibration / Project Evidence Memory
```

This design extends and must remain consistent with:

- `PROJECT_INTELLIGENCE_MASTER_PLAN.md`;
- `ADAPTIVE_CAPABILITY_LEVELS_AND_TARGETED_VERIFICATION_PLAN.md`;
- `VERIFICATION_OBLIGATION_AND_TEST_EXECUTION_PLAN.md`;
- `TEST_PORTFOLIO_INTELLIGENCE_AND_BROAD_EVALUATION_PLAN.md`;
- `COMPOSITIONAL_VERIFICATION_AND_EVIDENCE_REUSE_PLAN.md`;
- `FAILURE_DRIVEN_PI_REEVALUATION_PLAN.md`;
- `TRANSPARENT_PI_ORCHESTRATION_PLAN.md`;
- `PRODUCTIZATION_AND_MODEL_EVALUATION_PLAN.md`.

Where this document describes integration between those capabilities, this document is authoritative.

---

## 2. Architectural constraint: maximize reuse of existing PI

Do **not** implement each new idea as an isolated subsystem with its own truth store.

All verification intelligence must project from the same revision-aware Project Truth:

```text
Digital Twin revision
        |
        +--> Project Graph
        +--> Impact projection
        +--> Requirement / Blueprint projection
        +--> Test Intent / Test Portfolio projection
        +--> Runtime Evidence projection
        +--> Environment projection
        +--> Evidence DAG / Certificate projection
        +--> Convergence projection
```

### Ownership by existing PI capability

| Concern | Primary existing owner | Supporting PI |
|---|---|---|
| source/workspace identity | Digital Twin | Graph, Runtime |
| semantic dependency facts | Project Graph | Runtime reconciliation |
| changed/affected scope | Impact Intelligence | Twin, Graph |
| what a test means | Test Intelligence / TestIntent | Requirements, Blueprint |
| whether assertions prove intent | Test Intelligence / Oracle Quality | Runtime, Traceability |
| actual runtime/process/UI result | Runtime Intelligence | GUI Flow Graph |
| missing observation capability | Runtime Intelligence projection | Test Intelligence, Impact |
| environment dimension impact | Impact Intelligence projection | Test Intelligence, Runtime |
| evidence validity/invalidation | Twin + Evidence Dependency Closure | Impact, Runtime |
| evidence reuse/composition | Compositional Verification | Convergence |
| why a revision is accepted | Traceability + Convergence | all evidence producers |
| long-term project lessons | Project Evidence Memory | Trace / Certificate |
| model assistance | Model Routing | Context Intelligence |

No OpenCode-specific object may enter these core domain contracts. OpenCode remains an execution/runtime adapter.

---

## 3. Core objects and projections

### 3.1 `SemanticChangeSet`

Reuse the existing planned revision delta projection. It represents the actual semantic change rather than raw line count.

Minimum facts where available:

- source revision / candidate revision;
- changed refs and relation deltas;
- changed public API/schema/config/feature-flag behavior;
- resource/side-effect changes;
- test/TestIntent changes;
- requirement/Blueprint target changes;
- confidence/provenance;
- unresolved/unknown relations.

`unknown` is not equivalent to unchanged.

### 3.2 `TestIntent`

`TestIntent` remains the semantic identity of what a test is supposed to prove.

It must survive harmless test refactors and may be implemented by multiple concrete tests/evidence providers.

Suggested fields:

```text
intent_id
source_requirement_ids
source_blueprint_ids
regression_case_ids
verification_obligation_ids
expected_behavior
input_partitions
preconditions
observation_layer
accepted_environment_constraints
lifecycle_state
provenance
confidence
```

### 3.3 `OracleAssessment`

Do not treat Oracle quality as a single LLM score.

Represent deterministic/inspectable checks such as:

- claimed obligation;
- actual assertion/observation targets;
- observation layer;
- whether real or mocked evidence is used;
- whether expected values are independent of the implementation being tested;
- discriminating/vacuous assertion signals;
- required positive/negative branch coverage;
- missing final-outcome observation;
- confidence/provenance.

Suggested statuses:

- `ADEQUATE`;
- `PARTIAL`;
- `WRONG_LAYER`;
- `VACUOUS_SUSPECT`;
- `MOCK_ONLY_FOR_RUNTIME_OBLIGATION`;
- `CONFLICTED`;
- `UNKNOWN`.

### 3.4 `ObservabilityRequirement`

Represents what must be observable to prove one Verification Obligation.

Examples:

```text
obligation: Start causes game process to run
required observations:
- launch command accepted
- process identity exists
- process state == running
- optional session/UI state == running
```

Fields:

- obligation id;
- required observation kind;
- target ref/resource/state;
- minimum evidence layer;
- freshness requirement;
- environment constraint;
- accepted evidence providers;
- criticality;
- provenance.

### 3.5 `ObservabilityGap`

Created when an obligation is meaningful but no current evidence provider can actually observe the required truth.

Suggested reasons:

- `NO_PROVIDER`;
- `WRONG_LAYER_ONLY`;
- `MOCK_ONLY`;
- `NO_RUNTIME_SIGNAL`;
- `UNSTABLE_SIGNAL`;
- `ENVIRONMENT_UNAVAILABLE`;
- `PERMISSION_OR_HOST_LIMITATION`;
- `UNKNOWN_MAPPING`.

A gap is not automatically a request to add instrumentation. It first asks whether an existing host/runtime signal can be reused.

### 3.6 `EnvironmentProfile` and `EnvironmentImpact`

Avoid a universal environment matrix. Represent only dimensions that can affect an obligation/test.

Candidate dimensions:

- OS / architecture;
- browser / browser engine/version;
- runtime/interpreter version;
- dependency/toolchain fingerprint;
- GPU/display/HDR/resolution where relevant;
- locale/timezone;
- DB/backend/service profile;
- feature flags/config profile;
- network/offline profile;
- filesystem/platform behavior;
- hardware/process/runtime capability.

`EnvironmentImpact` records which changed facts can invalidate which dimensions.

### 3.7 `EvidenceDiversityRole`

Evidence providers that cover the same obligation may remain valuable because they exercise independent layers/failure modes.

Suggested roles:

- `LOCAL_UNIT`;
- `BOUNDARY_CONTRACT`;
- `INTEGRATION`;
- `RUNTIME_REALITY`;
- `GUI_USER_FLOW`;
- `NEGATIVE_FAILURE_PATH`;
- `PLATFORM_VARIANT`;
- `HISTORICAL_REGRESSION`;
- `MUTATION_FAULT_DETECTOR`;
- `CALIBRATION_E2E`;
- `RELEASE_GATE`.

Portfolio consolidation must preserve unique diversity roles unless policy explicitly accepts their removal.

### 3.8 `VerificationCertificate`

A certificate is an auditable **reason record**, not formal mathematical proof.

It should be immutable for one candidate Twin revision and task/convergence decision.

Candidate fields:

```text
certificate_id
project/workspace identity
candidate revision
requirement/task/blueprint refs
SemanticChangeSet id
Impact summary
required obligation ids
TestIntent ids
Oracle assessments
fresh evidence ids
reused evidence segment ids
invalidated evidence ids
Verification Frontier(s)
Observability gaps / resolved gaps
selected environment profiles
full/calibration verification performed?
remaining uncertainty/gaps
Convergence decision
PI mode/depth by capability
model-route metadata where relevant
created_at
```

It must never contain raw private chain-of-thought.

### 3.9 `RegressionKnowledge`

Project Evidence Memory may store verified historical regression knowledge derived from accepted bug-fix history or observed failures.

Candidate fields:

- affected refs/path;
- root cause class;
- user-visible symptom;
- TestIntent/evidence that detected it;
- requirement/obligation link;
- first fixed revision;
- invalidation policy;
- confidence/provenance.

Do not infer a regression lesson from commit text alone when evidence is weak.

### 3.10 `VerificationDebtSnapshot`

Do not produce one opaque debt number.

A revision-level snapshot may report counts/categories such as:

```text
GUI:
  uncovered: 3
  stale: 4
  calibration_due: 2
API:
  conflicted: 1
  reused_aging: 7
Runtime:
  observability_gap: 5
```

This is a diagnostic/portfolio planning projection, not a completion authority by itself.

---

## 4. Pre-implementation PI workflow

The preferred path remains prevention rather than failure recovery.

### 4.1 Change understanding

Before implementation:

```text
Task / Requirement / Blueprint
  -> Task-aware PI
  -> relevant current Twin
  -> Semantic Change Plan
  -> Impact Closure
```

Impact should include production, tests, requirements, runtime/resource effects and reusable evidence.

### 4.2 Test Intent impact

For every affected existing test/intention, classify:

- `KEEP`;
- `UPDATE`;
- `OBSOLETE_CANDIDATE`;
- `REPLACE_CANDIDATE`;
- `CREATE_REQUIRED`;
- `REVIEW_REQUIRED`.

Specification-driven stale tests should therefore be included in the planned Change Package before verification whenever confidence is sufficient.

### 4.3 Evidence invalidation

Use SemanticChangeSet + Evidence Dependency Closure to classify existing evidence:

- `REUSABLE`;
- `CONDITIONALLY_REUSABLE`;
- `INVALIDATED`;
- `CALIBRATION_DUE`;
- `UNKNOWN`.

### 4.4 Observability analysis

For each required obligation:

```text
Verification Obligation
  -> required observation
  -> existing provider?
       yes -> map evidence provider
       no  -> ObservabilityGap
```

Do not generate a test that can only assert a proxy if the actual obligation requires runtime reality.

### 4.5 Environment impact

Determine whether the change affects environment-sensitive dimensions.

Examples:

```text
pure Python algorithm change
 -> browser matrix not relevant

CSS/layout change
 -> selected browser/resolution profiles relevant

Linux process-launch change
 -> Linux runtime/process profile relevant

serialization contract change
 -> representative client/runtime versions may be relevant
```

### 4.6 Required Change Package

The plan should be able to present a bounded package such as:

```text
Production:
  MODIFY A, B
Tests:
  KEEP T1
  UPDATE T2
  CREATE T4 for missing V3 boundary
  OBSOLETE_CANDIDATE T3
Evidence:
  REUSE E10
  INVALIDATE E11
Observability:
  ADD/USE process-state observation for V5
Environment:
  verify Linux + Browser Chromium only
Calibration:
  full GUI E2E not required for task; remains scheduled
```

This minimizes post-implementation surprise.

---

## 5. Observability Gap Intelligence

### 5.1 Governing principle

A missing verification signal is not the same as a missing test.

Example:

```text
Requirement:
  clicking Start actually starts the game

Available test:
  HTTP request returns 200
```

This is not complete. The gap is the missing observation of the actual process/session/runtime state.

### 5.2 Resolution order

When a gap exists:

1. reuse an existing runtime/host observation already available;
2. reuse an existing test/evidence provider at the correct layer;
3. add a bounded adapter mapping to an existing signal;
4. add minimal project instrumentation only when justified;
5. if observation is impossible, keep the obligation `UNAVAILABLE/INCONCLUSIVE` rather than inventing a pass.

### 5.3 Host boundary

ECA owns:

- defining the observation requirement;
- mapping observation to obligation;
- evidence interpretation;
- freshness/provenance;
- gap diagnosis.

OpenCode/OMO/host tools own actual browser/process/shell/runtime execution where those tools already exist.

### 5.4 Avoid observability pollution

Do not add production logging/probes everywhere by default.

Instrumentation must be:

- target-scoped;
- removable or intentionally retained;
- privacy-aware;
- performance-bounded;
- justified by a concrete unresolved obligation.

---

## 6. Verification Certificate design

### 6.1 Why it is needed

Convergence currently answers whether evidence is sufficient. A certificate makes that decision reproducible and reviewable without reading agent conversation history.

### 6.2 Certificate construction

At the end of one verification cycle:

```text
Twin revision
+ SemanticChangeSet
+ Impact Closure
+ required obligations
+ Test Intent / Oracle mappings
+ fresh/reused evidence
+ environment coverage
+ unresolved uncertainty
=> VerificationCertificate
```

### 6.3 Certificate statuses

Suggested overall state:

- `VERIFIED_TASK_SCOPE`;
- `PARTIAL`;
- `BLOCKED`;
- `INCONCLUSIVE`;
- `DIVERGENT`;
- `STALE`.

Do not use a certificate as a permanent proof after its dependency closure becomes invalidated.

### 6.4 Certificate reuse

A later task may reference an older certificate only through the evidence segments whose validity still holds. Do not simply inherit an entire old certificate as current truth.

### 6.5 User/debug surface

Expose compact diagnostics such as:

```text
Verified: task scope
Fresh tests: 4
Reused evidence segments: 3
Environment profiles: linux-x64, chromium
Full E2E: skipped
Reason: downstream closure unchanged
Calibration due: yes within 20 revisions
Remaining gap: none
```

Detailed evidence ids/provenance remain queryable on demand.

---

## 7. Environment Matrix Intelligence

### 7.1 Avoid Cartesian explosion

Do not compute:

```text
all tests × all OS × all browsers × all runtimes × all configs
```

Instead compute:

```text
SemanticChangeSet
 -> impacted environment dimensions
 -> obligations sensitive to those dimensions
 -> representative required EnvironmentProfiles
 -> selected verification providers
```

### 7.2 Environment equivalence classes

Where evidence permits, group equivalent profiles.

Example:

```text
Chromium 140/141 same relevant feature behavior
 -> one equivalence class for this obligation
```

Never assume equivalence from version proximity alone. Use capability/behavior evidence or accepted policy.

### 7.3 Environment invalidation

Environment change can invalidate evidence even when source is unchanged:

- browser/runtime upgrade;
- GPU/driver change;
- dependency/toolchain update;
- DB engine/version change;
- OS behavior difference;
- changed feature flags;
- changed locale/timezone where behavior depends on them.

### 7.4 GUI focus

GUI/user-flow verification should prefer representative profiles derived from actual supported product targets rather than arbitrary browser lists.

For UI-only changes, verify relevant browser/render profiles. For backend-only changes, reuse frontend evidence when the boundary contract remains valid.

---

## 8. Nondeterminism Intelligence

### 8.1 Separate nondeterminism from ordinary failure

A test that disagrees across nominally identical runs should not immediately trigger production repair.

Use `NONDETERMINISTIC` / `FLAKY` evidence when:

- repeated equivalent runs disagree;
- timing/race ordering changes outcome;
- external service behavior is unstable;
- UI focus/animation/network scheduling dominates result.

### 8.2 Re-evaluation

Use Runtime Intelligence and Test Portfolio history to distinguish:

- deterministic implementation mismatch;
- flaky test harness;
- real race condition in production;
- external/environment instability.

### 8.3 Repetition policy

Do not repeat every test many times by default. Repeat only when:

- historical flaky evidence exists;
- a new inconsistent result appears;
- the obligation is timing/race sensitive;
- D3/D4 policy requests stronger nondeterminism evidence.

### 8.4 Portfolio consequence

A flaky test may remain valuable as a bug detector but should not provide the same reusable evidence strength as stable deterministic evidence.

---

## 9. Evidence diversity preservation

### 9.1 Redundancy is not simple overlap

Two tests can cover the same symbol/obligation but detect different failures.

Example:

```text
unit test        -> local algorithm
contract test    -> serialization boundary
runtime E2E      -> real process behavior
```

### 9.2 Consolidation rules

Before `MERGE/REMOVE/REPLACE`, check:

- unique Verification Obligation;
- unique EvidenceDiversityRole;
- unique input partition/failure branch;
- unique environment profile;
- unique historical regression detection;
- unique mutation/fault detection;
- unique calibration role;
- cost and maintenance burden.

### 9.3 Calibration E2E

Segmented evidence may make a full E2E unnecessary for every task, but the E2E can remain highly valuable as independent calibration evidence. Do not classify it redundant solely because local segments compose.

---

## 10. Regression Knowledge Mining

### 10.1 Goal

Use past confirmed project failures to improve future Verification Obligations without creating generic chat memory.

### 10.2 Candidate mining sources

- accepted bug-fix commits/PRs;
- tests added with confirmed regression fixes;
- FailureEvidence classified as real production defect;
- calibration misses;
- user-confirmed incident records.

### 10.3 Use during planning

When a changed ref/path intersects a known regression pattern:

```text
Impact Closure
 -> RegressionKnowledge match
 -> add/raise relevant obligation/test evidence
```

### 10.4 Critical safeguard

Commit-message similarity alone is not sufficient. Low-confidence historical mining remains advisory.

---

## 11. Statistical / stratified calibration sampling

### 11.1 Motivation

If targeted/compositional verification prevents frequent full-suite runs, ECA still needs a way to discover unknown dependencies between full calibrations.

### 11.2 Sampling candidates

Prefer stratified samples from tests that are:

- rarely selected;
- high graph centrality;
- cross-boundary;
- historically regression-sensitive;
- recently changed indirectly;
- associated with uncertain relations;
- from under-covered environment/layer classes.

Pure random sampling may be retained as a small unbiased component.

### 11.3 Role

Sampling is a **PI audit**, not primary task verification.

A sampled failure that the required set missed is classified as a potential Impact/Test/Evidence invalidation miss and feeds calibration.

### 11.4 Cost controls

Sampling rate is depth/profile/repository dependent and may be zero when the full suite is already cheap.

---

## 12. Performance Verification Obligations

### 12.1 Performance is not automatically a requirement

Only create a performance obligation when one of these is true:

- explicit requirement/SLO;
- accepted Blueprint/contract;
- benchmark-regression task;
- historically important project constraint;
- user-visible latency target;
- resource budget is part of task acceptance.

### 12.2 Evidence

Use distributions rather than one sample where noise is material:

- p50/p90/p95;
- warm/cold distinction;
- sample count;
- environment profile;
- baseline/candidate delta;
- accepted regression band.

### 12.3 Test execution time versus product performance

Do not confuse:

- **test execution duration**, used to optimize verification scheduling;
- **product performance evidence**, used to satisfy a performance obligation.

They are separate evidence types.

---

## 13. Verification Debt

### 13.1 Purpose

Expose accumulated uncertainty and stale verification without turning it into an arbitrary scalar.

### 13.2 Categories

By project area / requirement / API / GUI flow:

- uncovered obligations;
- partial obligations;
- stale Test Intents;
- weak/partial Oracles;
- stale evidence;
- conditionally reusable evidence;
- calibration due;
- Observability Gaps;
- unresolved nondeterminism;
- environment coverage gaps;
- conflicted evidence.

### 13.3 Use

Verification Debt may influence:

- Risk Intelligence;
- Task-aware depth recommendation;
- release planning;
- test portfolio cleanup priorities;
- calibration scheduling.

It MUST NOT automatically block unrelated low-risk tasks unless policy requires it.

---

## 14. PI-wide orchestration

### 14.1 Task-aware Intelligence

The controller selects only relevant capabilities.

Example UI wiring change:

```text
Impact D2
TestIntent D2
Oracle D2
Observability D2
Environment D1/D2
Runtime D1
Research D0
DFG/CFG D0
```

If process launch unexpectedly fails:

```text
Runtime D1 -> D2/D3
Impact D2 -> D3 around launcher boundary
Observability D2 -> D3
TestIntent stays D2 unless spec conflict appears
```

Do not raise unrelated capabilities merely because a test failed.

### 14.2 Context Intelligence

Weak/local models should receive compact structured objects:

- current obligation ids;
- affected refs;
- missing observation;
- candidate root causes;
- evidence ids;
- allowed actions/enums.

Do not dump the full Evidence DAG into weak-model context unless expansion is justified.

### 14.3 Model Routing

Deterministic analysis owns:

- graph traversal;
- revision identity;
- invalidation intersection;
- evidence freshness;
- environment dimension selection where rules suffice;
- obligation/evidence mappings where explicit.

LLMs may help with:

- ambiguous TestIntent extraction;
- Oracle semantic review;
- historical/regression synthesis;
- requirement ambiguity;
- test code synthesis;
- explanation.

LLM output remains inference until grounded by deterministic/runtime evidence.

### 14.4 Strategy / Blueprint

For architecture/migration tasks, Strategy can compare designs partly by future verification burden:

- observability availability;
- testability;
- environment matrix size;
- evidence reuse potential;
- failure localization quality;
- migration verification cost.

Do not optimize architecture purely for easy testing; correctness/maintainability remain primary.

### 14.5 Research Intelligence

Research is used only when external facts are needed, such as:

- browser/runtime behavior differences;
- dependency/toolchain compatibility;
- platform-specific testing semantics;
- external protocol/standard requirements.

Research claims never directly become verified project runtime evidence.

### 14.6 Risk Intelligence

Risk may incorporate categories rather than one opaque score:

- impact breadth;
- unresolved boundaries;
- Observability Gaps;
- Verification Debt;
- environment sensitivity;
- regression history;
- evidence freshness;
- nondeterminism.

Use these to justify deeper verification, not to fabricate certainty.

---

## 15. Full runtime flow

### 15.1 Existing project first use

```text
Bootstrap existing repo
 -> Initial Twin
 -> test/TestIntent inventory
 -> baseline evidence inventory
 -> observability inventory
 -> environment capability inventory
 -> readiness/confidence
```

Old historical PASS results are not automatically reusable.

### 15.2 Normal change

```text
Task
 -> pre-change PI plan
 -> Impact/TestIntent/Evidence invalidation
 -> Observability + Environment selection
 -> Change Package
 -> implementation
 -> candidate Twin revision
 -> Required Verification Set
 -> execute only needed evidence
 -> compose reusable evidence
 -> Verification Certificate
 -> Convergence
```

### 15.3 Failure path

```text
meaningful FAIL
 -> FailureEvidence
 -> TestIntent check
 -> Oracle check
 -> fixture/mock check
 -> harness/environment/runtime check
 -> local Impact/Evidence closure expansion
 -> runtime reconciliation
 -> implementation mismatch only if prior checks remain valid
 -> repair smallest proven cause
 -> recompute candidate Twin + Required Verification Set
```

### 15.4 Calibration path

```text
targeted/composed verification succeeds
 -> optional stratified audit
 -> periodic/full E2E/full suite calibration
 -> any miss becomes PI calibration evidence
 -> adjust relation/invalidation/depth recommendation if repeated
```

---

## 16. GUI / runtime-specific detailed design

GUI is a priority validation domain.

### 16.1 Flow model

```text
User intent
 -> control/action
 -> handler
 -> local state
 -> API/IPC/command
 -> backend handler
 -> service/process/resource effect
 -> runtime/session state
 -> UI/rendered/user-visible outcome
```

Each edge may have TestIntent/obligation/evidence mappings.

### 16.2 Start-button example

Obligations may include:

```text
V1 Start control accepts intended action
V2 correct LaunchGameCommand is produced
V3 backend accepts and interprets command
V4 target game/process actually starts
V5 runtime/session becomes Running
V6 UI truthfully shows Running
F1 launch rejection/failure produces truthful error state
```

Note the failure obligation is a separate branch.

If only V1/V2 wiring changes and PI proves V3..V6/F1 evidence closures remain valid, the Required Verification Set should verify the bridge to the nearest trusted frontier rather than rerun the full game-launch E2E.

### 16.3 Observability example

If V4 requires proof that a process actually started but no process/session observation exists:

```text
ObservabilityGap(NO_RUNTIME_SIGNAL)
```

ECA may request/use a host process observation. It must not accept `HTTP 200` as equivalent proof.

### 16.4 GUI environment example

A pure handler wiring change may require Chromium only if browser-specific behavior is not implicated. A rendering/HDR/fullscreen change may require selected display/browser/runtime profiles according to the Impact closure.

### 16.5 GUI failure diagnosis

Classify where possible:

- action not emitted;
- wrong command;
- backend rejection;
- process launch failure;
- runtime state mismatch;
- UI synchronization failure;
- false success reporting;
- browser/harness ERROR.

Do not regenerate or rerun every GUI test by default.

---

## 17. Depth mapping

Not every capability must implement every depth.

### D0 — native/minimal

- no extra integrated verification planning;
- host-native verification only.

### D1 — light

- direct TestIntent and obligation mapping;
- direct evidence invalidation;
- obvious Oracle mismatch;
- same-environment evidence reuse only;
- no broad environment matrix.

### D2 — balanced target

- bounded transitive Impact;
- Evidence Dependency Closure;
- Observability Requirement/Gap mapping;
- representative EnvironmentProfile selection;
- Evidence Diversity preservation;
- Verification Certificate;
- normal Compositional Verification.

### D3 — thorough

- cross-layer/API/IPC/process/UI runtime reconciliation;
- stronger Oracle review;
- environment-sensitive verification;
- regression knowledge;
- selected nondeterminism repetition;
- stratified audit sampling;
- selected performance obligations.

### D4 — exhaustive/on-demand

- explicit high-risk/release/security policies;
- broader/full E2E/full suite;
- bounded deep CFG/DFG/Taint where root cause requires it;
- broader environment validation;
- mutation/fault campaigns where justified.

Higher depth can invalidate more evidence. It must not mean blindly reusing more evidence or running more tests.

---

## 18. Failure and uncertainty semantics

Use distinct states:

- `PASS`;
- `FAIL`;
- `ERROR`;
- `UNAVAILABLE`;
- `FLAKY`;
- `STALE`;
- `CONFLICTED`;
- `INCONCLUSIVE`.

Additional gap states may include:

- `OBSERVABILITY_GAP`;
- `ENVIRONMENT_GAP`;
- `CALIBRATION_DUE`.

Only evidence that actually satisfies the obligation can contribute to `VERIFIED`.

---

## 19. Evaluation design

Use the existing pinned five-repository corpus and real GUI/runtime projects.

### 19.1 Required comparison arms

For representative tasks compare:

1. native/full verification reference;
2. impacted-test selection only;
3. obligation-based selection;
4. compositional verification;
5. integrated design with Observability/Environment/Certificate;
6. selected feature ablations.

### 19.2 Correctness metrics

- false `VERIFIED` rate;
- Verification Obligation coverage recall;
- TestIntent classification precision/recall;
- Oracle defect detection;
- Observability Gap precision/recall;
- environment-impact miss rate;
- evidence invalidation recall;
- evidence reuse miss rate;
- full-E2E/full-suite-only discovered failures;
- root-cause classification accuracy;
- regression escape rate.

### 19.3 Efficiency metrics

- verification wall time;
- heavy E2E executions avoided;
- selected tests / total tests;
- environment profiles executed / full matrix;
- browser/process/runtime minutes;
- PI analysis overhead;
- unnecessary generated tests avoided;
- unnecessary production/test edits avoided;
- time-to-VERIFIED;
- certificate construction overhead.

### 19.4 Portfolio metrics

- unique evidence diversity preserved after consolidation;
- stale/obsolete test recommendations accepted/rejected;
- calibration E2Es retained;
- Verification Debt by category;
- Observability Gaps resolved/remaining;
- regression knowledge contribution.

### 19.5 Anti-overfit

Keep the existing 4+1 rotating held-out policy. Freeze rules/thresholds before held-out evaluation.

No production heuristic may special-case Flask/HTTPX/Express/Vite/React Hook Form by repository name.

---

## 20. Critical objections and safeguards

### 20.1 More PI metadata can become more expensive than tests

If certificate/environment/closure analysis costs more than a cheap full suite, the repository profile may prefer the simpler full verification path.

### 20.2 Observability instrumentation can change behavior

Instrumentation may introduce timing/performance effects. Prefer existing signals and bounded probes. Record instrumentation provenance.

### 20.3 Environment selection can miss platform bugs

Use held-out/calibration/full matrix runs periodically. Unknown environment sensitivity remains uncertainty, not no-impact.

### 20.4 Oracle analysis can overfit to implementation

Expected behavior should derive from independent requirement/contract when possible. LLM-only Oracle grading remains advisory.

### 20.5 TestIntent extraction can be ambiguous

Use explicit source links, test names/docs, historical provenance and runtime behavior. Ambiguity yields `REVIEW_REQUIRED`, not automatic obsolescence.

### 20.6 Verification Certificate can create false authority

Certificates must expose gaps/freshness/reuse/provenance. They expire/invalidate with their underlying evidence.

### 20.7 Regression mining can preserve old mistakes

Only accepted/verified regression knowledge should influence active verification. Weak historical inference remains advisory.

### 20.8 Sampling cannot replace full calibration

Statistical audit is an early-warning mechanism, not proof that all unselected tests would pass.

### 20.9 Nondeterminism classification can hide real bugs

A flaky result must not simply be quarantined. Distinguish flaky harness from production race/timing defects through repeated/runtime evidence.

### 20.10 Test consolidation can destroy independent safety nets

Evidence Diversity is a required consolidation input. Do not optimize only for test count or wall time.

---

## 21. Implementation sequence

Implement by extending current contracts/components, not by creating a new platform.

### VI-X0 — contracts/projections only

1. reconcile existing `TestIntent`, `OracleAssessment`, `FailureEvidence`, `EvidenceSegment` contracts;
2. add `ObservabilityRequirement` / `ObservabilityGap`;
3. add `EnvironmentProfile` / `EnvironmentImpact`;
4. add `EvidenceDiversityRole`;
5. add `VerificationCertificate` projection/schema;
6. add `VerificationDebtSnapshot` projection;
7. no behavior change.

### VI-X1 — observability mapping

1. map existing runtime/test/build/browser/process observations to obligations;
2. detect wrong-layer/no-provider gaps;
3. remain advisory;
4. benchmark overhead and precision.

### VI-X2 — environment impact selection

1. discover environment dimensions from current project/runtime config;
2. map semantic changes to affected dimensions;
3. select bounded profiles;
4. compare against broader reference matrices.

### VI-X3 — certificate + convergence integration

1. construct certificates from existing evidence DAG;
2. expose compact diagnostic summary;
3. make Convergence reference certificate inputs rather than duplicate calculations;
4. invalidate certificate projections when underlying evidence changes.

### VI-X4 — evidence diversity + consolidation guard

1. classify evidence roles;
2. block unsafe redundancy removal;
3. measure accepted/rejected portfolio recommendations.

### VI-X5 — nondeterminism + calibration sampling

1. detect inconsistent repeated outcomes;
2. add bounded repetition policy;
3. add stratified audit sampling;
4. feed misses into PI calibration evidence.

### VI-X6 — regression knowledge + performance obligations

Only after baseline verification quality is stable:

1. mine accepted regression knowledge;
2. add contribution evidence;
3. add explicit performance obligations where requirements justify them.

### VI-X7 — Verification Debt diagnostics

1. aggregate category-level debt;
2. integrate with Risk/Task-aware depth recommendations;
3. do not create a universal scalar gate.

### VI-XFINAL — broad evaluation

Run the pinned five-repository + GUI/runtime evaluation with:

- native/full reference;
- current ECA baseline;
- integrated design;
- per-capability ablations;
- model tiers;
- held-out rotation;
- D1-D4 cost/quality comparisons.

Promote only capability/depth combinations with repeatable value.

---

## 22. Definition of Done

This integrated design is successful only when:

1. all new verification intelligence projects from the same revision-aware Twin/Graph truth;
2. TestIntent and Oracle quality are first-class and revision/specification aware;
3. missing observability is distinguished from missing tests;
4. runtime reality is not replaced by proxy assertions when the obligation requires runtime evidence;
5. environment selection avoids unnecessary Cartesian test matrices without increasing critical misses;
6. evidence invalidation remains conservative and explainable;
7. Compositional Verification reuses only still-valid evidence;
8. evidence diversity prevents unsafe test consolidation;
9. failure-driven PI re-evaluation remains localized before broad/deep expansion;
10. Verification Certificate explains why Convergence accepted/rejected the candidate revision;
11. certificates do not outlive invalidated underlying evidence;
12. nondeterminism is distinguished from deterministic behavior failure without hiding real races;
13. calibration sampling/full verification continues to audit PI misses;
14. regression knowledge is evidence-backed and invalidatable;
15. performance obligations are explicit requirement-driven evidence, not confused with test runtime;
16. Verification Debt is category-based and actionable rather than one opaque score;
17. D0-D4 can raise/lower each capability independently based on measured benefit;
18. weak-local models receive bounded structured evidence rather than large raw graphs;
19. OpenCode/OMO remain execution/orchestration runtimes rather than duplicated inside ECA;
20. broad multi-repository and GUI/runtime held-out evidence shows better verification efficiency without worse critical correctness or false `VERIFIED`.

## 23. Governing principle

> Use Project Intelligence not to run more tests, but to know exactly what changed, what must still be true, what evidence is still valid, what reality is not yet observable, which environments actually matter, and what smallest fresh evidence is required to justify completion.
