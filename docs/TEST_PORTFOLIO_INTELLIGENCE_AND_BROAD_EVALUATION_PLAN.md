# Test Portfolio Intelligence and Broad Evaluation Plan

Status: canonical enhancement plan
Date: 2026-08-16
Scope: existing-project bootstrap, Test/Verification Portfolio Intelligence, GUI/runtime verification, broad multi-repository evaluation

## 1. Decision

ExtendCodeAgent will evolve Test Intelligence from primarily **test selection + freshness/obsolescence** into a broader **Test / Verification Portfolio Intelligence** capability.

The product goal is not merely to generate tests with an LLM. The differentiating loop is:

```text
Existing/New Project
  -> Project Bootstrap / Initial Twin
  -> Requirement / Blueprint / Existing Behavior
  -> Semantic ChangeSet
  -> Impact Closure
  -> Verification Obligations
  -> Existing Test / Evidence Coverage
  -> Coverage Gaps
  -> Test Design Specification
  -> Test Synthesis / Update when justified
  -> Test Quality Evaluation
  -> Required Verification Set
  -> Cost-aware Execution
  -> Runtime / GUI / Test Evidence
  -> Residual Verification Gaps
  -> Test Portfolio Health / Consolidation
  -> Convergence
```

Tests are revision-aware evidence providers for verification obligations, not isolated source files or raw coverage percentages.

This plan extends and must remain consistent with:

- `PROJECT_INTELLIGENCE_MASTER_PLAN.md`;
- `VERIFICATION_OBLIGATION_AND_TEST_EXECUTION_PLAN.md`;
- `ADAPTIVE_CAPABILITY_LEVELS_AND_TARGETED_VERIFICATION_PLAN.md`;
- `TRANSPARENT_PI_ORCHESTRATION_PLAN.md`;
- `PRODUCTIZATION_AND_MODEL_EVALUATION_PLAN.md`.

## 2. Existing-project bootstrap is a first-class lifecycle

ECA must work for both greenfield development and existing repositories.

A reused/existing project must first be imported as a **baseline project truth** before Test Intelligence can make strong claims.

### 2.1 Initial Project Bootstrap

On first use of an existing repository, build an `InitialProjectBaseline` containing at least:

- stable project/workspace identity;
- source commit/revision and working-tree fingerprint;
- language/framework/package/build/test-runner discovery;
- Project Graph structural and supported semantic relations;
- immutable initial Twin revision;
- public API/schema/config surfaces where detectable;
- test files, suites, fixtures, mocks, helpers and runner metadata;
- current test commands / build / typecheck / lint commands;
- baseline test/evidence inventory;
- existing requirement/ADR/Blueprint-like documents where recognizable;
- current runtime evidence only when actually observed;
- analyzer versions and unsupported/degraded analysis areas.

The initial import must distinguish **observed fact**, **static inference**, **historical evidence**, and **unknown**. Existing code is not assumed correct merely because it is the baseline.

### 2.2 Existing Test Baseline Audit

During or after bootstrap, evaluate the existing test portfolio before using it as trusted verification evidence.

Classify or annotate tests with evidence such as:

- covered refs/behaviors/requirements where inferable;
- unit/component/integration/e2e/contract/type/build category;
- fixture/mock dependencies;
- last known execution result if locally observed;
- execution-time distribution when measured;
- freshness relative to baseline revision;
- assertion strength/relevance signals;
- flaky/stale/obsolete/redundant suspicion;
- runtime-path relevance;
- unsupported/unknown coverage.

Do not require a complete expensive audit before ECA can be used. Bootstrap itself is depth-configurable; deeper portfolio analysis may run on demand or in background according to policy.

### 2.3 Baseline confidence

An imported repository may start with partial knowledge. Surface readiness such as:

- graph ready / degraded;
- test inventory complete / partial;
- runtime evidence absent / partial;
- GUI flow coverage unknown / mapped;
- portfolio confidence low / medium / empirically calibrated.

Unknown must not be converted to `no impact` or `verified`.

## 3. Product position and differentiation

Do not position this as "AI unit-test generation". Dedicated test products and coding assistants already generate tests, use repository/diff context, detect coverage gaps, and select impacted regression tests.

ECA should differentiate through the integration of **persistent Project Truth + verification obligations + revision-aware evidence + runtime/GUI causal evidence + convergence**.

Target product claim:

> ECA determines what a change must prove, finds which current evidence already proves it, designs or generates only missing verification, evaluates whether the tests provide meaningful independent evidence, executes the smallest evidence-complete portfolio, keeps that portfolio fresh across revisions, audits existing projects on first import, and identifies redundant/stale/obsolete tests without losing verification obligations.

Differentiated dimensions:

1. Requirement-aware.
2. Impact-aware.
3. Revision-aware.
4. Evidence-aware across test/runtime/build/typecheck/GUI observations.
5. Convergence-aware.
6. Portfolio-aware.
7. Existing-project-bootstrap-aware.
8. Cross-workspace-aware for future OMO/team/worktree use.
9. Self-calibrating through broader/full validation.
10. Weak-local-friendly through structured TestDesignSpecifications.
11. GUI/runtime-causal rather than DOM-only.

## 4. Test Intelligence capability stack

Treat strengthened Test Intelligence as independently configurable capabilities.

### 4.1 Test Requirement Intelligence

Derive `VerificationObligation` objects from explicit requirements, Blueprint targets, Semantic ChangeSet, Impact Closure, public contract/schema/config changes, resource/side-effect/state transitions, GUI user-visible outcomes, and relevant past regressions.

Never derive obligations solely from unsupported model assertions.

### 4.2 Test Design Intelligence

For uncovered obligations, define a bounded `TestDesignSpecification` before code generation.

Candidate fields:

- obligation ids;
- target refs / user-visible behavior;
- test layer: unit/component/integration/e2e/contract/type/build/runtime-smoke/GUI-flow;
- preconditions/fixtures;
- input partitions/boundaries;
- expected observations/assertions;
- negative/failure/retry cases;
- mock use or prohibition;
- real-resource/runtime requirement;
- existing framework/style/helpers;
- revision/freshness target;
- evidence confidence target;
- cost/depth budget.

PI decides **what must be proven**. The LLM/agent translates that specification into repository-native test code.

### 4.3 Test Synthesis / Update

Prefer:

1. reuse fresh existing evidence;
2. update an existing test whose intent remains valid;
3. parameterize/extend an existing test family;
4. create a new test only when it supplies unique required evidence.

Do not mass-generate tests merely to improve line/branch coverage.

### 4.4 Test Quality Intelligence

Evaluate multiple dimensions rather than a single opaque score:

- verification-obligation coverage;
- requirement/Blueprint coverage;
- impacted behavior/path coverage;
- assertion relevance/strength;
- positive/negative/boundary coverage;
- runtime/GUI-path relevance;
- mock/fixture freshness;
- revision freshness;
- historical regression detection;
- flaky history;
- mutation/fault detection where practical;
- unique evidence versus other tests;
- setup/execution cost;
- implementation-detail coupling.

### 4.5 Test Selection / Required Verification Set

`VERIFICATION_OBLIGATION_AND_TEST_EXECUTION_PLAN.md` remains authoritative: correctness defines the Required Verification Set; cost optimizes execution only afterward.

### 4.6 Test Freshness / Obsolescence

Retain and strengthen states such as `healthy`, `suspect`, `stale`, `obsolete`, `missing`, `redundant`, with explainable causes including implementation change, stale fixture/mock, removed requirement, unreachable behavior, revision mismatch, changed runtime/UI path, or non-discriminating assertions.

### 4.7 Test Portfolio Intelligence

Portfolio decisions:

- `KEEP`;
- `REDUNDANT_CANDIDATE`;
- `MERGE_CANDIDATE`;
- `REPLACE_CANDIDATE`;
- `STALE`;
- `OBSOLETE`;
- `QUARANTINE`;
- `MISSING`.

Before removal/merge, ensure the test contributes no required unique evidence through obligations, evidence layer, historical failure detection, mutation kills, runtime path, input partition, platform/environment, or independent integration evidence.

Initial consolidation rollout is advisory. Automatic deletion/merge is not default-active.

## 5. GUI / user-flow Test Intelligence

GUI correctness is a priority because UI tests that only prove rendering or successful clicking often miss real failures.

### 5.1 User-visible outcome, not click success

For a GUI action, verification must model the causal chain from user intent to final observable outcome.

Example:

```text
User clicks Start
  -> button enabled / event emitted
  -> frontend handler
  -> state/action/IPC/API command
  -> backend/service/runtime request
  -> process/game launch request
  -> process/session actually starts
  -> expected game/window/session state becomes observable
  -> UI reflects success or a truthful error
```

A test that only verifies `button.click()` or callback invocation does **not** satisfy the full "game starts" obligation.

### 5.2 GUI Flow Graph

Incrementally model generic relations when evidence justifies them:

- control -> event;
- event -> handler;
- handler -> state/action;
- action -> API/IPC/command;
- API/IPC -> backend handler;
- handler -> service/process/resource;
- runtime observation -> resulting state;
- resulting state -> UI render/notification.

Framework adapters may emit these relations, but core obligations remain framework-neutral.

### 5.3 GUI verification layers

For one user flow, evidence may include:

- component rendering and accessibility;
- event/handler invocation;
- state transition;
- API/IPC request and response;
- backend/service side effect;
- spawned process/session/resource;
- final DOM/window/session state;
- screenshot/visual evidence only where it proves a relevant visual obligation;
- failure/error UX.

Use the smallest evidence-complete layer set. Do not require browser E2E for every local UI change if lower layers prove the obligation, but do require E2E/runtime evidence for obligations that explicitly depend on cross-boundary behavior.

### 5.4 GUI test generation

Generate GUI tests from user-flow obligations, not selectors alone.

A generated GUI test should specify:

- precondition/application state;
- semantic target (role/name/test-id only as locator, not proof);
- action sequence;
- expected cross-boundary effects;
- final user-visible outcome;
- timeout/retry behavior;
- error-state expectation;
- cleanup/reset requirements.

Prefer stable semantic locators and observable state over brittle DOM structure.

### 5.5 Runtime-backed GUI verification

Where possible, correlate browser/UI evidence with runtime observations. For example, a Start-button test may require both a UI transition and evidence that the expected process/session actually exists. ECA should retain provenance so a mocked frontend success cannot masquerade as real runtime success.

## 6. Test generation quality gate

A synthesized/updated test is not accepted merely because it compiles and passes.

```text
TestDesignSpecification
  -> generate/update
  -> syntax/typecheck/build validity
  -> execute
  -> obligation/assertion mapping
  -> freshness/mock/fixture validation
  -> existing portfolio comparison
  -> targeted mutation/fault probe when justified
  -> flaky repetition when justified
  -> ACCEPT / MODIFY / REJECT
```

Reject or revise tests that do not cover their claimed obligation, only assert implementation detail, duplicate evidence without value, depend on stale fixtures/mocks, contain weak/always-pass assertions, are unjustifiably flaky, or remain green under faults they are supposed to detect.

## 7. Pre-implementation test design

When Requirements/Blueprint are available, support obligation and TestDesignSpecification creation before implementation. This reduces the risk that implementation and tests share the same model-generated misunderstanding.

Do not force test-first generation on every task.

## 8. Mutation / fault-probe policy

Mutation is depth-gated because it can be expensive:

- D0-D1: none by default;
- D2: selected high-value generated/changed tests when cheap;
- D3: changed behavior/critical obligations;
- D4: broader bounded campaign for explicit quality/security/release work.

## 9. Adaptive depth integration

Depth controls analysis/evidence depth, not a fixed test count:

- D0: native/no portfolio analysis;
- D1: direct obligations/tests/basic freshness;
- D2: normal Impact + obligation coverage + missing/redundant detection;
- D3: cross-boundary/runtime/GUI/history/flaky/mock/fixture analysis plus selected synthesis/consolidation proposals;
- D4: deep audit/mutation/broad portfolio consolidation/full calibration when justified.

## 10. Critical objections and safeguards

### Existing-project baseline is not verified truth

Imported code and tests may already contain defects. Bootstrap establishes **current observed state**, not correctness. Use `baseline` rather than `verified` semantics until evidence supports verification.

### Test generation already exists elsewhere

Do not claim differentiation from generation alone. Require the Project Truth -> Obligation -> Evidence Portfolio -> Convergence loop.

### Generated tests can encode the same bug as generated implementation

Prefer requirement/Blueprint-derived intent, pre-implementation specifications, independent evidence and bounded fault/mutation probes.

### More tests can reduce quality

Measure unique evidence and maintenance/execution cost.

### Consolidation can delete valuable redundancy

Do not merge/remove based only on symbol/line coverage. Preserve independent layers, runtime paths, history and distinct fault detection.

### GUI E2E tests can be slow and flaky

Do not solve GUI quality by running all browser tests after every change. Build user-flow obligations, select affected flows, use deterministic state/reset, record timings/flakiness, and escalate only when cross-boundary evidence is required.

### UI selectors are not behavior

A visible/clickable control is not sufficient evidence that the intended feature works. Final user-visible/runtime outcome matters.

### LLM quality grading is unreliable

Deterministic facts/runtime evidence remain authoritative; model judgments are advisory.

### Portfolio intelligence itself can be expensive

Measure contribution/cost by depth and allow low-depth/full-suite-simple policies when they are objectively better.

## 11. Broad five-repository external evaluation corpus

Do not accept the feature from one repository or one favorable scenario.

Create a versioned reproducible five-repository corpus covering languages, frameworks, test runners and verification layers.

### E1 — Pallets / Flask

- repository: `pallets/flask`
- pinned commit: `2a8a38b051fc248865730bf3511bf2e2ea325e81`
- Python web framework; pytest, typing, multi-environment verification.

### E2 — Encode / HTTPX

- repository: `encode/httpx`
- pinned commit: `b5addb64f0161ff6bfe94c124ef76f6a1fba5254`
- Python sync/async HTTP client; pytest, async/network-sensitive behavior.

### E3 — Express

- repository: `expressjs/express`
- pinned commit: `a3714473feb3d2908add734d340e7755fd85e0a3`
- JavaScript web framework; Mocha + Supertest; unit/acceptance behavior.

### E4 — Vite

- repository: `vitejs/vite`
- pinned commit: `dcf88bd2ad2b1a8845f9029587cc8c825e382d42`
- large TypeScript monorepo; Vitest unit + serve/build E2E-style suites + typecheck/build.

### E5 — React Hook Form

- repository: `react-hook-form/react-hook-form`
- pinned commit: `9b7af71b4d25da143fd2522c40d20466c7433f00`
- TypeScript/React; Jest/jsdom, type tests, Playwright E2E, build/API extraction.

These are selected for diversity, not for special-case production rules.

## 12. Held-out and anti-overfit policy

Use a 4 + 1 rotating held-out design:

- four repositories may be used for diagnosis/tuning;
- one is held out from threshold/rule/heuristic tuning;
- freeze candidate behavior before running held-out;
- rotate held-out across release cycles.

Initial cycle: tune/reference on Flask, HTTPX, Express, Vite; hold out React Hook Form.

ExtendCodeAgent/ControlDeck may remain developer smoke/real-world validation repositories but do not replace the external held-out corpus.

## 13. Corpus acquisition and isolation

Implement a local evaluation bootstrap later that reads a machine-readable manifest and:

1. clones/fetches into an ignored local corpus root;
2. checks out exact pinned commit detached;
3. records license/toolchain metadata;
4. installs each project's declared toolchain in isolated environments/caches where practical;
5. creates disposable task worktrees/copies;
6. records setup success/failure;
7. never commits third-party source into ECA;
8. never silently updates pins within a corpus version.

An upstream refresh creates a new explicit corpus version.

## 14. Evaluation task sources

### 14.1 Historical bug/change reconstruction

Mine real historical commits/PRs around pinned versions. Hide accepted future patch/test from the agent and use it as ground truth when valid.

Evaluate obligation generation, relevant test discovery, missing-test detection, test design intent, generation/update quality and regression selection.

### 14.2 Controlled fault/mutation tasks

Inject bounded faults into disposable copies: boundary errors, branch/boolean errors, removed validation, wrong API response, stale mock/fixture, dropped consumer handling, async/error-path regression, GUI event-to-runtime disconnect.

### 14.3 Test portfolio maintenance tasks

Evaluate duplicated intent, parameterization opportunities, stale/obsolete tests, stale mocks/fixtures, missing edge-case tests, and slow broad tests versus evidence-equivalent alternatives. Human review is required before labeling a test truly redundant/obsolete.

### 14.4 GUI/user-flow tasks

Use React Hook Form and suitable Vite/playground or other test fixtures for UI flows. Include cases where:

- click handler fires but backend/runtime outcome does not occur;
- UI shows success despite failed command;
- stale state prevents action;
- async completion is not awaited;
- error is swallowed;
- browser/UI path works but underlying process/resource does not;
- type/unit tests pass while user-visible flow fails.

For product-specific richer flows, ControlDeck/SteamShine may be additional non-corpus validation projects, but results must be distinguished from the external corpus.

## 15. Comparison conditions

Use staged causal comparison rather than a giant Cartesian product.

### Stage A — core Test Portfolio effect

Compare representative tasks:

A. OpenCode native / ECA disabled;
B. OpenCode + current ECA baseline;
C. ECA Test Portfolio advisory D1;
D. ECA D2;
E. ECA D3 only on task classes claiming deeper benefit.

Use ablations for obligation generation, test design, synthesis/update, quality gate, portfolio consolidation, GUI/runtime evidence and targeted selection.

### Stage B — OMO complementarity

After Stage A is stable:

F. OpenCode + OMO;
G. OpenCode + OMO + ECA.

Evaluate duplicate tests produced by parallel agents, workspace/revision evidence identity, final verification quality, and orchestration overhead. OMO is not a base release dependency.

## 16. Model coverage

Evaluate logical tiers separately:

- local-low: structured test-design subset, repeated runs;
- local-practical: broad representative coverage;
- host-default: broad representative coverage;
- frontier: representative quality subset when functioning.

Specifically compare weak/local models given raw repository context versus bounded TestDesignSpecification to measure whether PI improves intent/assertion reliability.

## 17. Required metrics

### Obligation / design correctness

- obligation precision/recall;
- missing/irrelevant obligation rates;
- TestDesignSpecification correctness;
- correct test-layer selection;
- negative/boundary-case recall;
- mock-versus-real-resource decision correctness;
- GUI final-outcome obligation recall.

### Generation/update quality

- compile/typecheck success;
- deterministic execution;
- claimed-obligation coverage;
- weak/assertionless/always-pass rate;
- implementation-detail coupling;
- mutation/fault detection on evaluated subset;
- duplicate evidence introduced;
- ACCEPT/MODIFY/REJECT rate.

### Portfolio quality

- missing/stale/mock/fixture detection precision/recall;
- redundant-candidate precision;
- consolidation correctness;
- unique evidence lost by proposals;
- test count/LOC reduction only with evidence completeness preserved;
- portfolio execution-time change.

### GUI/runtime quality

- user-flow obligation coverage;
- DOM-only false-positive rate;
- event-to-runtime causal-chain coverage;
- final user-visible outcome correctness;
- swallowed-error detection;
- flaky/retry rate;
- UI-to-backend/process correlation correctness.

### Verification correctness

- selected-test recall;
- false `VERIFIED` rate;
- full-suite-only discovered failures;
- residual-gap accuracy;
- Convergence correctness;
- regression escape rate.

### Efficiency

- wall time / time-to-first-actionable-failure / time-to-VERIFIED;
- test duration distributions and setup reuse;
- context/tokens/model/tool calls;
- CPU/RAM/storage;
- avoided full-suite runs with correctness preserved.

Correctness outranks speed/test-count reduction.

## 18. Evaluation repetition

Do not report one-shot wins.

- deterministic selectors/graph tasks: repeat enough to detect timing variance and verify stable outputs;
- local-low: at least 5 runs for critical stochastic generation/design scenarios;
- local-practical: at least 3;
- host-default: representative repeated runs;
- frontier: representative repeated subset subject to cost/availability;
- GUI flaky-sensitive cases: repeat and record failure distribution, not only a pass.

Report per-repository and per-task-class results before any aggregate. Do not hide a repository regression inside an average improvement.

## 19. Implementation sequence

### TP-0 — Bootstrap / portfolio contracts

- InitialProjectBaseline contract;
- test/evidence inventory projection;
- readiness/confidence states;
- no active behavioral change.

### TP-1 — Obligation and design intelligence

- strengthen VerificationObligation generation;
- add TestDesignSpecification;
- map existing tests/evidence to obligations;
- detect missing verification.

### TP-2 — Test quality and synthesis gate

- generated/update test quality gate;
- assertion/mock/fixture/freshness analysis;
- bounded test synthesis/update path;
- D1/D2 first.

### TP-3 — Portfolio intelligence

- redundancy/merge/replace/stale/obsolete candidates;
- advisory-only initially;
- evidence-preservation checks.

### TP-4 — GUI/runtime flow intelligence

- generic GUI Flow Graph projection;
- browser/UI -> API/IPC -> backend/runtime -> final-state obligations;
- targeted GUI/E2E generation and runtime correlation;
- prioritize real failure classes such as click-without-effect.

### TP-5 — Broad corpus harness

- machine-readable five-project manifest;
- clone/pin/setup bootstrap;
- task/fault corpus;
- evidence capture;
- held-out rotation.

### TP-6 — Comparative evaluation

- native/current/D1/D2/D3 + ablations;
- repeated model-tier evaluation;
- periodic broader/full calibration;
- publish per-repo results and depth recommendation.

### TP-7 — OMO complementarity

- only after core portfolio behavior is stable;
- evaluate parallel-agent duplicate tests and cross-worktree evidence.

## 20. Adoption gates

Do not promote Test Portfolio Intelligence because it generates more tests.

A level/capability advances only if repeated multi-repository evidence shows:

- no critical correctness regression;
- obligation/test-selection recall meets accepted thresholds;
- false VERIFIED does not increase;
- generated tests provide real claimed evidence;
- consolidation does not lose unique evidence;
- GUI tests verify final outcomes rather than click/render only;
- targeted verification saves meaningful time where claimed;
- repositories where full-suite/simple policy is better remain allowed to use it;
- held-out repository does not show critical overfit;
- local-low/practical/host/frontier claims match actually tested tiers;
- OMO compatibility remains separately evidenced when enabled.

## 21. Definition of done

The strengthened Test Portfolio system is a default candidate only when:

- existing projects can be bootstrapped into a revision-aware initial Twin/test baseline;
- existing tests are inventoried/evaluated without pretending baseline means correct;
- obligations determine missing verification before generation;
- generated/updated tests pass quality/evidence gates;
- GUI user-flow tests cover cross-boundary final outcomes where required;
- portfolio consolidation is explainable and preserves unique evidence;
- broad five-repository + rotating held-out evaluation is reproducible;
- results are repeated, per-repository and per-task-class;
- capability depth remains configurable and evaluation can recommend promote/demote/scope/reject;
- ECA remains a Project Intelligence/Verification layer rather than a new generic test runner or browser automation framework.
