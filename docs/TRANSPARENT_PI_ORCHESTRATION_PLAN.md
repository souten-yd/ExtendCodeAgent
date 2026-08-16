# Transparent Task-Aware Project Intelligence Plan

> **Consolidated 2026-08-16.** Design detail for the task-aware controller. Consumed by stages C1 and C3 of `docs/PI_MASTER_EXECUTION_PLAN.md`.

Status: proposed productization architecture after PR #20
Date: 2026-08-14

## Goal

Normal OpenCode use must not require PI-specific prompts or manual `pi_*` tool selection. The extension should observe the task, repository, evidence, model and privacy constraints, select only the minimum useful Project Intelligence, and fall back safely when evidence is insufficient.

```text
OpenCode task
  -> cheap deterministic task signals
  -> IntelligencePlan
  -> minimum existing PI capabilities/context
  -> model/tool flow
  -> verification + telemetry
  -> progressive expansion or native fallback when needed
```

This does **not** mean enabling every feature automatically. A good controller frequently decides that no extra intelligence is needed.

## Critical design objections

1. **Hidden automation can silently bias the model.** Active facts therefore require freshness/confidence gates, provenance remains visible to the system, uncertain facts stay labeled, native source inspection remains allowed, and stale/unavailable evidence cannot drive completion.
2. **Prompt-only task classification is brittle.** Use prompt/session text together with changed files, referenced symbols, repository language/framework, available test/runtime evidence, prior failures and current task stage.
3. **Invisible indexing can hurt UX.** No repository-scale synchronous work in host hooks; deep analysis remains on-demand; non-project tasks select native OpenCode.
4. **More context is not always better.** Use progressive context expansion and model-aware budgets. Do not solve weak-model failures by blindly increasing context.
5. **Fewer tool calls are not automatically better.** Correctness and verification are primary. Tool/token/time reductions count only when quality is preserved or improved.
6. **Controller benchmarks can overfit.** Keep tuning tasks and held-out tasks separate, use multiple real repositories, paraphrased prompts and follow-up turns, and avoid source-specific production rules.
7. **Frontier models may need less PI.** Model capability is an input; the controller minimizes evidence rather than maximizing PI usage.
8. **Transparency conflicts with debuggability.** Normal UX stays quiet, while `pi.status` plus a compact "last plan/reason" diagnostic remains available.

## Minimal architecture

Do not build another planner/agent framework. Add a thin host-neutral orchestration layer over existing components:

```text
TaskSignalCollector
 -> deterministic TaskIntentClassifier
 -> IntelligencePlanner
 -> IntelligencePlan
 -> existing CapabilityPolicy / Context / Graph / Impact / Test / Runtime / ModelRouter / Strategy / Convergence
 -> PlanOutcome telemetry
```

OpenCode-specific objects remain in the TypeScript adapter. The adapter normalizes task/session/model/tool signals; it must not contain business rules such as prompt-word-to-capability mappings.

Suggested compact contracts, after checking existing types for reuse:

- `TaskSignals`: objective, prior task stage, referenced/changed files, language/framework signals, model profile, PI freshness, evidence availability, privacy policy, previous failure classes.
- `TaskIntent`: primary/secondary intent, ordinal uncertainty, reasons.
- `IntelligencePlan`: level, capabilities, context budget/profile, query/depth limits, evidence needs, escalation permission, fallback rule, Strategy/Convergence decision, reasons.
- `PlanOutcome`: actual capabilities/evidence used, expansions/fallbacks, model route, verified result, cost/latency/token/tool metrics, failure class.

## Progressive Intelligence levels

- **L0 Native**: PI not useful, unsupported or unsafe/stale. Normal OpenCode only.
- **L1 Understand**: Project Model freshness + semantic/reference facts + bounded context. Locate/explain/navigation tasks.
- **L2 Change**: L1 + Impact + Test selection + Verification freshness. Refactor, bug fix, API/change tasks.
- **L3 Runtime-aware**: L2 + available runtime evidence and a small Runtime Bridge only when static evidence fails on a real boundary.
- **L4 Strategic**: L2/L3 + Strategy/Convergence for broad/risky architecture work. Blueprint remains optional.
- **L5 Deep/on-demand**: DFG/Taint, CFG, state/event analysis or Research only for measured task need. Never project-wide/always-on by default.

## Initial deterministic task map

| Task intent | Initial plan | Avoid by default |
|---|---|---|
| locate/explain | L1 semantic + context | Impact, Strategy, Research, deep graph |
| rename/refactor | L2 semantic + impact + tests | Blueprint, Research, deep graph |
| bug fix | L2; L3 only with runtime evidence/gap | Strategy unless scope grows |
| verification | affected scope + test/runtime evidence | Strategy/Research |
| API/backend change | L2 consumers/tests | UI deep graph |
| UI/browser bug | L2 JS/TS first; L3 only if static evidence is insufficient | repository-wide CFG/DFG |
| security/data-flow | L2 first; bounded DFG/Taint only after missing data-origin evidence | project-wide DFG |
| architecture/migration | L2 + Strategy + Convergence; optional Blueprint | automatic Research unless external facts needed |
| external research | explicit Research + bounded relevant project context | treating external claims as verified code truth |

Follow-up turns inherit prior intent/stage unless deterministic signals show a transition.

## Selection and expansion rules

1. Start with the minimum justified level.
2. Expand only when a required relation is unavailable, confidence/freshness is insufficient, verification fails, the task scope expands, a runtime boundary is directly implicated, or repeated failure is classified as `CONTEXT_MISSING`.
3. Do not expand to deep analysis merely because a weak model failed. First improve candidate reduction and structure.
4. Intelligence expansion and model escalation are separate decisions. The planner chooses evidence; the existing ModelRouter chooses an allowed model.
5. Global/capability/privacy configuration is a hard upper bound. Automation can never override it.
6. Low-confidence `may_call` cannot independently drive broad/destructive active decisions.

## User experience

Normal usage:

1. user asks a normal OpenCode task;
2. controller creates a cheap plan;
3. smallest justified context/evidence is supplied;
4. PI expands only if necessary;
5. verification and fallback remain automatic and bounded.

No PI-specific syntax should be required. PI internals should appear only when they materially explain uncertainty/failure or the user requests diagnostics.

Failure behavior:
- sidecar/controller/graph failure must not block OpenCode;
- degrade to advisory/native;
- missing evidence remains missing, never passed;
- record a concise local diagnostic.

## Controller evaluation

Compare three baselines:

1. **native**: no PI assistance;
2. **manual/advisory**: current explicit PI use or a curated best-known capability plan;
3. **auto**: transparent controller-selected PI.

This distinguishes "PI is useful" from "the controller chooses PI correctly".

For benchmark tasks maintain a small human-reviewed expected level/capability set where feasible. These labels are evaluation ground truth, not rules copied into production logic.

### Selection metrics

- intent classification accuracy;
- capability precision: useful/required selected capabilities divided by selected capabilities;
- capability recall: required capabilities selected before failure;
- under-selection rate;
- over-selection rate;
- unnecessary deep-analysis activation rate;
- expansion count/stage;
- native fallback rate/reason;
- user-visible PI intervention rate.

### Outcome metrics

- objective task success and tests/build/behavior correctness;
- unsupported claims;
- unnecessary reads/edits;
- tool calls and token categories;
- wall time and retries/timeouts;
- context items/tokens;
- Impact/Test precision/recall;
- completion correctness.

### System cost metrics

- controller decision latency;
- time-to-first-useful-context;
- refresh/revision churn per task;
- selected analysis CPU/time;
- DB growth attributable to selected analysis;
- plugin/sidecar overhead.

Evaluate local-low, local-practical, host/default and frontier separately; do not average tiers into one score.

## Counterfactual checks

For representative/high-value tasks compare:

```text
native
manual/advisory best-known PI
controller shadow plan (no effect)
controller auto
controller auto with one selected capability ablated
```

Use ablation when it is unclear whether a selected capability actually caused the improvement.

## Initial acceptance gates

These are provisional and may change only with recorded evidence.

- No critical verified task may regress because of auto PI.
- Auto must match or exceed the verified success of manual/advisory on the release task set.
- Stale/unavailable evidence must never produce false completion.
- Automatic repository-wide deep analysis activation remains 0% until separately accepted.
- Critical under-selection failures after progressive expansion/fallback must be 0 on the accepted release cases.
- Investigate if more than 20% of representative tasks activate a capability with no demonstrated contribution.
- Controller logic itself must remain cheap and perform no repository-scale synchronous I/O.
- No-benefit tasks must not suffer material median latency/token regression versus native/off.
- Local-low uses repeated distributions, not best runs; local-practical remains viable; frontier native and PI-assisted paths are tested when available.
- Remote escalation never occurs when privacy policy forbids it.
- Normal benchmark tasks require no PI-specific user prompt.
- PI failure preserves a working native OpenCode path.

## Rollout and PR sequence

Run the existing RV-0 release-validation baseline first. It establishes current gaps and fixes blocking OpenCode/frontier/provider issues before controller effects are introduced.

Then:

### TA-0 Shadow planner

Implement signals/classifier/IntelligencePlan/telemetry only. No change to context, model routing, tests or task behavior.

Exit: deterministic tests, bounded planner latency, plan-quality report, no OpenCode behavior change.

### TA-1 Advisory auto-selection

Use the plan to choose which existing PI queries/context are prepared. Measure useful-item rate, under/over-selection, outcome and cost.

### TA-2 Bounded active

Permit active bounded context only for low-risk, empirically accepted task/relation classes. Strategy, Research, runtime bridge and deep analysis remain separately gated.

### TA-3 Progressive expansion

Add evidence-driven expansion/fallback and carefully retest weak-local distributions.

### TA-4 Complex task automation

Only after evidence: architecture may auto-select Strategy/Convergence; UI/runtime may select Runtime Bridge; security may select bounded DFG/Taint; Research remains explicit or strongly justified.

### TA-FINAL

Compare transparent auto vs native and manual/advisory across the final repository/model/task matrix. Only then consider it a default candidate.

Recommended branches:

- `agent/task-aware-shadow`
- `agent/task-aware-advisory`
- `agent/task-aware-active`
- optional measured Runtime Bridge/evidence/deep-analysis PRs
- `agent/release-validation-final`

If RV-0 finds a blocker, fix it before TA-0 rather than hiding it in controller work.

## Runtime Bridge / deep-analysis gate

Runtime Bridge is implemented only if held-out UI/API tasks show that the controller correctly selects L3 but current evidence cannot solve the task.

DFG/Taint/CFG require all of:
1. repeated high-value task failure;
2. root cause is a missing data/control relation, not model/context/provider;
3. bounded deep analysis is the smallest fix;
4. benchmarked quality gain;
5. default project cost remains bounded because analysis is target-scoped/on-demand.

## Confidence requirement for automation

Transparent automation raises the cost of false confidence because a human is no longer manually selecting the PI tool. Before TA-2, collect empirical threshold evidence for relation classes that can affect Impact, Test selection, context inclusion and completion decisions. Until enough samples exist, confidence is ordinal and active thresholds stay conservative.

## Evidence layout

```text
docs/evidence/final/task-aware/
  task-set.json
  oracle-plans.json
  shadow-plans.json
  controller-matrix.json
  ablations.json
  selection-quality.json
  model-tier-results.json
  opencode-usability.json
  acceptance-gates.md
```

Do not commit raw model transcripts or secrets.

## Definition of done

Transparent task-aware PI is a default candidate only when:

- normal OpenCode tasks require no PI-specific prompt/tool knowledge;
- the base controller is host-neutral and deterministic;
- capability/privacy policies remain hard upper bounds;
- shadow/advisory/bounded-active rollout works;
- auto selection is evaluated against native and manual/advisory baselines;
- critical under-selection is eliminated by expansion/fallback;
- over-selection/default cost is bounded;
- local-low repeated results do not materially regress from accepted manual PI;
- local-practical, host/default and frontier are separately validated;
- PI failure/degradation restores a usable native path;
- no unproven deep capability becomes always-on;
- active relation classes have empirical evidence or conservative fallback;
- users can inspect status/last plan and disable automation;
- another agent can reproduce the release gates from committed evidence/handoff.

The controller succeeds not by maximizing PI use, but by making the best OpenCode behavior require the least user knowledge of PI while preserving correctness, evidence quality and bounded cost.
