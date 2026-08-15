# Verification Obligation and Test Execution Plan

Status: canonical refinement of targeted verification policy
Date: 2026-08-16
Scope: ExtendCodeAgent Test Intelligence / Impact / Convergence / capability-depth interaction

## 1. Decision

ExtendCodeAgent MUST NOT select or omit tests primarily because they are fast, cheap, or because an
arbitrary progressive ladder has already produced several passing results.

The primary decision chain is:

```text
Semantic ChangeSet
  -> Impact Closure
  -> Verification Obligations
  -> Test / Evidence Coverage Graph
  -> Required Verification Set
  -> Cost-aware Execution Plan
  -> Runtime/Test Evidence
  -> Residual Verification Gaps
  -> targeted additional verification when gaps remain
  -> Convergence
```

The core rule is:

> **Impact and evidence decide WHAT must be verified. Execution cost decides HOW to verify the required set efficiently.**

A passing subset does not justify omitting another test if that omitted test is the only accepted
evidence for a still-required verification obligation.

This document refines `ADAPTIVE_CAPABILITY_LEVELS_AND_TARGETED_VERIFICATION_PLAN.md`. Where that plan's
`direct -> impacted -> subsystem -> full` shorthand could be interpreted as time-budget-driven staged
test sampling, this document is authoritative.

## 2. Why this fits Project Intelligence

ECA should reduce work in two different places:

1. **Minimize the semantic change** required to satisfy the task, using Graph/Twin/Impact/Strategy facts.
2. **Minimize the verification work** required to prove that semantic change is safe, using explicit
   impact and evidence coverage rather than a fixed full-suite policy.

The objective is not the smallest textual diff and not the fewest tests. It is:

> the smallest justified semantic change plus the smallest evidence-complete verification set.

A one-line public schema or authentication-policy change may have a much larger impact closure than a
multi-file mechanical rename. Diff size is therefore not a safe verification-scope proxy.

## 3. Semantic ChangeSet

After implementation, derive a revision-scoped `SemanticChangeSet` from the actual Twin/Graph delta,
not only Git line diff statistics.

Candidate fields:

- source revision / target revision;
- changed files and canonical refs;
- added / removed / changed symbols;
- changed public API/schema/config/feature-flag contracts;
- changed side effects/resources when available;
- changed call/dependency relations;
- behavior-relevant uncertainty;
- requirement/Blueprint elements claimed to be satisfied;
- provenance and confidence per change relation.

The change set may contain `unknown` or `uncertain` relations. Unknown impact is not zero impact.

## 4. Impact Closure

Run Impact Intelligence from the semantic change set and derive the bounded set of affected project
entities and behaviors.

The closure should distinguish at least:

- directly changed implementation;
- direct callers/consumers;
- transitive consumers where confidence supports inclusion;
- API/client boundaries;
- persistence/schema/config/resource effects when modeled;
- affected requirements/Blueprint targets;
- affected tests/fixtures/mocks;
- runtime-observed dependencies where available;
- unresolved or low-confidence edges.

Impact depth is controlled by the selected capability depth, but the verification planner must surface
when the selected depth leaves unresolved impact boundaries.

## 5. Verification Obligations

Convert the semantic change + impact closure into explicit verification obligations.

A verification obligation is a statement that must have current evidence before the change can reach
the requested Convergence state.

Examples:

```text
V1  Changed function preserves required local behavior.
V2  Public API request/response contract remains compatible.
V3  Database migration preserves expected persisted state.
V4  Frontend consumer still handles the response correctly.
V5  Requirement R-17 is satisfied by the new implementation.
V6  Failure/retry behavior remains valid.
```

Each obligation records:

- obligation id/type;
- originating changed/impacted refs;
- required evidence kind(s);
- minimum freshness;
- minimum relation confidence / uncertainty state;
- risk/criticality where available;
- accepted test/evidence providers;
- status: `uncovered`, `partially_covered`, `covered`, `conflicted`, `unavailable`.

Do not create obligations from a model's unsupported assertion. They must be derived from deterministic
project facts, explicit requirements/Blueprint, runtime evidence, or clearly labeled lower-confidence
inference.

## 6. Test / Evidence Coverage Graph

Tests are evidence providers, not the objective themselves.

Maintain/query relations such as:

```text
test -> covers symbol/path/behavior/requirement
runtime observation -> verifies behavior/resource
lint/typecheck/build -> verifies static/build obligation
manual/external evidence -> verifies explicit obligation with provenance
```

For every candidate test/evidence item retain:

- covered obligations/refs;
- source/project revision for which the relation is valid;
- last execution result and freshness;
- relation confidence/provenance;
- historical failure detection if known;
- flaky/stale/mock/fixture concerns;
- estimated execution cost;
- setup/fixture group when relevant.

A green result from an incompatible/stale revision does not satisfy a current obligation.

## 7. Required Verification Set

Select the smallest practical set of evidence providers that covers all currently required obligations
at the requested confidence/freshness level.

This resembles a constrained set-cover problem, but correctness dominates optimization.

Conceptually:

```text
minimize execution/verification cost
subject to:
  every required obligation is covered
  evidence is fresh enough
  confidence/freshness constraints are satisfied
  no unresolved critical evidence conflict remains
```

Do not optimize this as an exact NP-hard global problem if a bounded deterministic greedy algorithm is
sufficient. Prefer explainable selection.

Selection priority should be based on:

1. obligation coverage correctness;
2. evidence freshness/confidence;
3. unique coverage of critical obligations;
4. historical detection value where trustworthy;
5. then execution cost / setup reuse / parallelizability.

A faster test must never replace a slower one if the faster test does not cover the same required
obligation with acceptable evidence quality.

## 8. Execution Time as Evidence

Record test execution duration because it is useful, but treat it as execution-planning evidence, not
as the primary correctness selector.

Recommended stored metrics:

- last duration;
- p50 / p90 (p95 where enough samples exist);
- sample count;
- exponentially weighted recent estimate if useful;
- cold/warm classification where observable;
- parallelism/worker count;
- environment or machine profile when materially different;
- timeout/failure rate;
- setup/fixture group id when shared setup dominates cost.

Do not treat one duration sample as a stable estimate.

Uses of duration data:

- order required tests to fail fast where evidence value is equivalent;
- schedule required tests across workers to minimize wall time;
- choose between evidence-equivalent test providers;
- account for shared fixture/setup cost;
- detect test-performance regressions/hangs;
- measure the incremental cost of deeper capability/verification levels;
- support evaluation-driven recommendation of capability depth.

Non-use:

- do not drop a required test merely because it is slow;
- do not decide verification completeness from elapsed time budget alone.

## 9. Cost-aware Execution Plan

After the Required Verification Set is fixed, optimize how it runs.

Possible strategies:

- parallelize long independent tests;
- group tests sharing expensive fixtures/setup;
- run a high-value fast-failure test early when it can invalidate the change quickly;
- avoid duplicate build/typecheck/setup work;
- reuse already-current evidence when its revision/freshness contract permits;
- cap redundant evidence providers when obligations are already sufficiently covered.

The objective is lower wall time without reducing obligation coverage.

## 10. Residual Verification Gap Evaluation

After the required set executes, do not ask the vague question "are these tests enough?".

Recompute obligation status from the resulting evidence:

```text
V1 covered
V2 covered
V3 conflicted
V4 uncovered
```

Only the residual gaps drive additional verification.

Reasons for additional verification include:

- an obligation remains uncovered/partial;
- selected evidence failed or is unavailable;
- runtime behavior revealed a new impacted ref;
- a mock/fixture/test is stale;
- static and runtime evidence conflict;
- impact confidence drops at an important boundary;
- execution reveals an unexpected dependency;
- implementation changed again after the initial set was selected.

Then select evidence specifically for those residual obligations.

This is **evidence-driven progressive verification**, not "run a cheap batch, then another batch until
it feels sufficient".

## 11. Full-suite Role

A full suite remains important, but it has two distinct roles.

### Product/change verification

Run the full suite when evidence indicates targeted verification cannot establish sufficient coverage,
for example:

- unresolved broad impact;
- repository-wide/mechanical changes whose semantic closure is uncertain;
- public schema/protocol/security-critical changes where accepted policy requires full validation;
- unknown global/shared state;
- selector confidence below accepted threshold;
- release/final acceptance policy.

### PI calibration/audit

Periodically compare PI-selected verification with full-suite results even when targeted evidence was
considered complete.

If full suite finds a failure that the selected set missed, record it as a Test Intelligence / Impact
miss and use it to improve Graph relations, test coverage mapping, confidence thresholds, obligation
generation, and capability-depth recommendations.

Without periodic full-suite calibration, ECA could permanently hide dependencies it failed to model.

## 12. Interaction with Capability Depth

Capability depth controls how much intelligence is used, not a fixed number of tests.

- `D0`: no PI verification planning; native behavior.
- `D1`: bounded semantic change + direct/high-confidence impact and obligations.
- `D2`: normal balanced impact closure + test/evidence coverage; expected default for ordinary coding.
- `D3`: broader cross-boundary/resource/runtime reconciliation for risky/complex change.
- `D4`: exhaustive/on-demand deep relations/full validation when justified.

A D1 task can still require a slow test if it uniquely covers a required obligation. A D3 task may run
few tests if the broader analysis proves only a small evidence-complete set is needed.

Therefore `depth` MUST NOT be implemented as a simple numeric test-count or suite-size ladder.

## 13. Minimal Semantic Change Principle

ECA should attempt to reduce unnecessary edits before verification begins.

The goal is:

> **minimum justified semantic change**, not minimum lines changed.

Use Project Graph, Impact, Strategy/Blueprint constraints and existing architecture to discourage
unrelated refactors, speculative file edits, duplicated implementations, and broad API churn when a
local compatible change suffices.

Do not game this metric by choosing tiny but architecturally bad changes.

## 14. Convergence Semantics

Convergence must not reduce verification to `tests_passed=true`.

Persist/project at least:

- semantic change revision;
- required obligation ids;
- covered/uncovered/conflicted obligations;
- selected evidence/test ids;
- verification/evidence freshness;
- impact closure confidence/uncertainty;
- verification depth/capability depth;
- whether full-suite calibration was run;
- remaining gaps and reasons.

A small internal change with all obligations covered and current high-confidence impact may reach
`VERIFIED` using targeted tests. A public API migration with only local unit obligations covered must
not reach `VERIFIED` while consumer obligations remain uncovered.

## 15. Critical objections and safeguards

### Impact Graph can be wrong

Targeted verification is safe only to the degree that impact/test mappings are trustworthy. Use
conservative uncertainty propagation, high recall for critical selection, unresolved-boundary gaps,
periodic full-suite calibration, held-out ground truth, and empirically accepted active relation
classes.

### Minimizing verification can optimize away valuable redundancy

Some independent redundant tests detect different failure modes despite nominally covering the same
ref. Historical detection evidence and evidence type must distinguish these cases. Do not collapse
tests solely on symbol overlap.

### Test duration is environment-dependent

Store distributions/context and use duration only as a soft scheduling/cost signal.

### Minimal semantic change can become patch-local optimization

Strategy/architecture constraints outrank raw edit count. A slightly larger structurally sound change
may be preferred to a tiny workaround.

### Dynamic/runtime dependencies may escape static impact

Escalate depth/runtime evidence for boundaries with known uncertainty. Missing runtime relation must
be represented as uncertainty, not treated as no impact.

### Full suite may be cheap enough that selection is pointless

If historical full-suite wall time is sufficiently small and targeted selection provides no meaningful
benefit, evaluation should recommend full-suite or lower Test Intelligence depth for that repository
or task class. Optimization is evidence-driven, not ideological.

## 16. Evaluation Metrics

Correctness first:

- verification obligation coverage recall;
- selected-test recall for ground-truth impacted failures;
- false VERIFIED rate;
- full-suite-only discovered failures;
- stale/conflicting evidence acceptance rate;
- regression/task success.

Efficiency second:

- selected tests vs total tests;
- verification wall time;
- CPU/time consumed;
- shared setup reuse;
- avoided duplicate build/lint/typecheck work;
- time-to-first-actionable failure;
- time-to-VERIFIED.

Model quality:

- impact precision/recall;
- test/evidence mapping precision/recall;
- residual-gap accuracy;
- confidence calibration by relation type.

Never accept faster verification if false VERIFIED or critical recall regresses.

## 17. Evaluation-driven Depth Recommendation

Use repeated real-task evidence to recommend capability/Test Intelligence depth by task/repository/model
class.

Examples:

```text
Repo A, ordinary backend bug:
D2 = same correctness as D3, 70% lower verification time
=> recommend D2

Repo B, dynamic plugin architecture:
D2 misses consumer regressions, D3 catches them
=> recommend D3 for plugin/API change tasks

Repo C, full suite = 8s:
targeted selection saves only 1s and adds complexity
=> recommend simpler/full verification policy
```

The system may adapt depth within a task according to configured bounds, but it MUST NOT silently
rewrite persistent user policy merely because of one run.

## 18. Implementation Sequence

1. Define `SemanticChangeSet` projection from current Twin/Graph delta.
2. Define host-neutral `VerificationObligation` contracts.
3. Extend test/evidence relations to map providers -> obligations/refs.
4. Implement deterministic Required Verification Set selection.
5. Record duration distributions and setup-group metadata without making them correctness selectors.
6. Implement cost-aware scheduling/parallelization hints.
7. Recompute residual gaps after evidence ingestion.
8. Integrate obligation coverage into Convergence.
9. Add full-suite calibration/audit evidence and miss classification.
10. Evaluate D1-D4 across multiple repositories/task/model tiers.
11. Promote/demote default depth only from recorded repeated evidence.

Do not implement all graph types merely to support this plan. Add the smallest missing relation when
real verification misses prove it necessary.

## 19. Definition of Done

This policy is implemented successfully only when:

- tests are selected from semantic change + impact obligations, not runtime budget alone;
- every selected/omitted verification item has an explainable coverage reason;
- execution time optimizes scheduling/cost only after correctness coverage is established;
- passing a subset cannot satisfy an uncovered obligation;
- residual gaps specifically drive additional verification;
- full suite remains available for policy/release/fallback and periodic calibration;
- Convergence records verification scope/freshness/obligation coverage;
- capability depth changes analysis depth rather than blindly increasing test count;
- real multi-repository evidence shows targeted verification improves time without increasing false
  completion/regression;
- repositories where full-suite is already optimal are allowed to keep that simpler policy.
