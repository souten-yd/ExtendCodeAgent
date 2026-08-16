# Adaptive Capability Levels and Targeted Verification Plan

> **Consolidated 2026-08-16.** Design detail for the capability depth axis. `AL-0..AL-4` are superseded; see stages E2, E3, V2 and C3 of `docs/PI_MASTER_EXECUTION_PLAN.md`.

Status: canonical enhancement policy
Date: 2026-08-16
Scope: configurable Project Intelligence depth, evidence-driven tuning, targeted verification/test selection

## 1. Goal

ExtendCodeAgent should strengthen Project Intelligence without forcing every strengthened capability to execute at maximum depth on every task.

The project therefore separates two independent control axes:

1. **Rollout mode / authority** — whether a capability may affect agent behavior: `off`, `shadow`, `advisory`, `active`.
2. **Capability depth / cost** — how much analysis, context, verification, memory, research, or graph expansion the capability may perform.

A capability can be active but shallow, advisory but deep, or shadow with expensive experimental analysis. Do not encode execution cost into rollout mode.

The objective is not to maximize intelligence use. It is to maximize verified task value per unit of latency, tokens, CPU, memory, tool calls and model cost while preserving correctness.

## 2. Capability depth model

Use one common ordinal depth contract for capabilities that have meaningful cost/depth tradeoffs:

- `D0` — **native/minimal**: no extra expensive PI work beyond already-ready cheap facts; used for no-benefit tasks or explicit budget limits.
- `D1` — **light**: direct facts, direct impact, smallest context, direct test candidates, no deep/transitive analysis.
- `D2` — **balanced**: normal recommended depth; bounded transitive impact, standard context, graph-selected tests and existing runtime evidence.
- `D3` — **thorough**: broader transitive relations, richer evidence, subsystem verification, optional framework/runtime bridge, higher context budget.
- `D4` — **exhaustive/on-demand**: deep bounded DFG/Taint/CFG, broad verification/full-suite fallback, architecture/research expansion, expensive analysis justified by risk or explicit user request.

Do not require every capability to implement every depth. Each capability declares supported depths and maps them to concrete parameters.

Examples:

- Context: item/token budget, transitive depth, evidence kinds.
- Impact: traversal depth, relation classes, confidence threshold, historical/runtime expansion.
- Test Intelligence: direct tests vs impacted tests vs subsystem/integration/full-suite verification.
- Runtime Intelligence: existing observations vs active smoke/trace collection.
- Research: none/micro/standard/deep.
- Project Evidence Memory: no retrieval/direct facts/related incidents/history expansion.
- Graph: existing semantic facts vs framework/resource/state relations vs bounded deep analysis.

## 3. Configuration hierarchy

Keep configuration centralized. Avoid feature-local environment flags.

Resolution order:

```text
hard safety/privacy/capability bounds
  > user explicit per-capability override
  > project profile
  > model profile
  > task-aware recommended depth
  > global default
```

Suggested configuration shape:

```yaml
intelligence:
  mode: advisory
  profile: auto
  budget:
    max_wall_ms: 5000
    max_context_tokens: 6000
    max_model_calls: 2
  capabilities:
    impact:
      min_depth: D1
      max_depth: D3
      preferred: auto
    context:
      min_depth: D1
      max_depth: D3
      preferred: auto
    verification:
      min_depth: D1
      max_depth: D4
      preferred: auto
    research:
      min_depth: D0
      max_depth: D2
      preferred: D0
```

`auto` chooses a task-specific depth inside the configured bounds; it never silently rewrites persistent user configuration.

## 4. User profiles

Provide simple global presets while allowing per-capability overrides:

- `eco` — prioritize latency/CPU/token cost; generally D0-D1.
- `balanced` — default daily-use profile; generally D1-D2.
- `quality` — broader impact/context/verification; generally D2-D3.
- `max` — user-requested deep analysis; permits D4 where supported.
- `auto` — task-aware selection within user/project min/max bounds using evaluation-backed recommendations.

The recommended default should initially be `balanced` or `auto` with conservative D2 ceilings until release evidence supports deeper defaults.

## 5. Evaluation-driven level recommendation

Each meaningful capability/depth pair must be measurable against lower-depth and native baselines.

Record at least:

- verified task success;
- completion correctness;
- unsupported claims;
- test/impact/context precision and recall where applicable;
- wall time;
- tool/file-read counts;
- context/input/output tokens;
- model calls/escalations;
- CPU/RAM/DB growth;
- failures/timeouts.

For each capability and task/model/repository class, estimate:

```text
marginal_value = verified_quality_gain over lower depth
marginal_cost  = additional latency/tokens/CPU/tooling
```

Do not collapse these into one opaque universal score. Store reviewer-readable evidence and derive a recommendation such as:

- `promote`: higher depth produces repeatable meaningful gain at acceptable cost;
- `retain`: gain/cost tradeoff supports current depth;
- `demote`: higher depth adds cost with no stable gain;
- `scope`: higher depth helps only specific task/model/repository classes;
- `reject`: regression or cost outweighs value.

## 6. Adaptive depth selection

The Task-aware controller may select a depth per capability using explainable signals:

- task class/stage;
- change scope;
- impact size;
- relation confidence/uncertainty;
- source/Twin freshness;
- model capability profile;
- prior failed attempt class;
- available runtime/test evidence;
- public API/schema/security significance;
- configured latency/token/CPU budget;
- historical evaluation recommendation for the task/model class.

Start shallow and expand progressively. A weak-model failure does not automatically justify D4; first improve candidate reduction/evidence structure and verify that missing information is the root cause.

Suggested flow:

```text
D1 cheap evidence
  -> sufficient confidence/success? stop
  -> missing relation/evidence? D2
  -> high risk or unresolved verification? D3
  -> explicit deep/security/release requirement or proven missing deep relation? D4
```

## 7. No silent permanent self-tuning

Evaluation may update committed/released recommendation profiles, but runtime behavior must not permanently rewrite project/user defaults merely because one task succeeded or failed.

Two mechanisms are allowed:

1. **Adaptive per-task selection** inside configured bounds.
2. **Evidence-backed recommendation update** during release/productization, reviewed and versioned like code/config.

An optional future user-facing action may offer `Apply recommended levels`, but this must be explicit and reversible.

## 8. Capability contribution / ablation

A strengthened capability should not remain expensive merely because total system performance is good.

For representative tasks compare:

```text
native
current depth
higher depth
higher depth with one capability ablated
```

Where practical, record whether the extra capability/depth changed:

- selected context/evidence;
- agent actions;
- verification decision;
- correctness;
- cost.

If an expensive level contributes no repeatable value, lower the recommended depth or scope it to the task classes where it helps.

## 9. Targeted verification and test selection

Project Intelligence MUST NOT imply running the entire test suite after every change.

The normal verification policy is **targeted first, progressive expansion second, full suite only when justified**.

Define verification depth separately but map it onto the common D0-D4 contract:

### D0 — no execution / analysis-only

Use for locate/explain/research tasks where no code changed and no runtime claim needs verification.

### D1 — direct verification

- tests directly linked to changed symbols/files;
- focused lint/typecheck for changed scope when tooling supports it;
- direct unit tests.

### D2 — impacted verification

- graph-selected direct + transitive affected tests;
- affected package/module tests;
- relevant lint/typecheck/build targets;
- existing fresh runtime evidence.

This should be the normal coding-task default if test-selection recall is empirically acceptable.

### D3 — subsystem / integration verification

Use for higher-risk changes:

- public API/schema changes;
- cross-layer UI/API/backend changes;
- state/event/resource changes;
- low-confidence impact graph;
- stale or contradictory test evidence;
- previous targeted verification failure.

Run affected integration/smoke/subsystem suites, not necessarily the entire repository.

### D4 — full verification

Use full suite/full build/release-level checks when one or more of the following holds:

- release/final acceptance gate;
- impact/test-selection confidence below accepted threshold;
- critical/high-risk/security change;
- repository-wide refactor/migration;
- selected tests expose unexpected broad coupling;
- repeated targeted verification cannot establish confidence;
- periodic audit/calibration run;
- explicit user request.

## 10. Why targeted tests can be faster

Yes: a core ECA benefit is to use Project Graph + Impact + Test Intelligence to reduce verification work.

Conceptually:

```text
changed refs
  -> Impact graph
  -> affected behavior/resources
  -> test/evidence relations
  -> minimal verification candidates
  -> run selected tests
  -> ingest results as revision-aware evidence
```

This can reduce wall time dramatically in repositories where the full suite is large and the changed blast radius is small.

However, speed is only a valid improvement if selected-test **recall remains high enough**. A fast test selector that omits the failing regression is worse than a full suite.

Therefore measure:

- selected-test recall against known affected tests;
- selected-test precision;
- full-suite fallback rate;
- escaped-regression rate discovered by periodic/full validation;
- targeted vs full wall time;
- verification correctness.

## 11. Calibration by periodic full-suite sampling

Targeted verification needs an oracle/audit path. Do not stop running full suites forever.

Use full-suite runs for:

- release/final gates;
- periodic calibration samples;
- selected high-risk tasks;
- held-out benchmark tasks;
- suspected selector misses.

Compare targeted selections against full-suite outcomes and feed misses back into Graph/Test Intelligence quality work. Do not automatically widen every future task because one miss occurred; classify the missing relation and fix the selector/graph if justified.

## 12. Verification escalation policy

Suggested deterministic escalation:

```text
D1 direct tests
  -> fail: diagnose/fix and rerun relevant scope
  -> pass + high confidence + low risk: accept targeted evidence
  -> pass + uncertainty/stale evidence/public contract: D2/D3
  -> unexpected coupling or insufficient evidence: broaden
  -> release/high-risk/unresolved: D4 full
```

Completion/Convergence must record which verification depth was used. `verified` at D1 is not semantically identical to release-level D4 verification; expose verification scope/provenance rather than hiding it behind one boolean.

## 13. Interaction with Convergence

Convergence should use both **evidence quality** and **verification scope**.

Examples:

- small internal change + high-confidence impact + fresh D2 tests -> may be fully verified for task scope;
- public API migration + only D1 unit tests -> materialized/observed but not sufficient for final verification;
- stale selected tests -> cannot satisfy completion regardless of test pass;
- D4 full-suite pass does not override an explicit missing requirement/runtime evidence gap.

## 14. Interaction with OMO

OMO may perform multi-agent/background execution, but ECA owns PI verification selection.

Avoid two independent systems both deciding to run broad test suites. When observable, normalize OMO/OpenCode task/worktree/test events into ECA evidence; ECA may recommend verification scope, while the runtime executes it.

For OMO Team Mode, test selection must remain workspace/worktree scoped and cross-worktree invalidation must not let one agent's pass verify another agent's newer revision.

## 15. Initial implementation sequence

Do not implement every strengthened feature at D4 immediately.

### AL-0 — contracts/config only

- add capability depth contract and centralized min/max/preferred/auto config;
- no behavioral change;
- architecture/config tests.

### AL-1 — evaluation telemetry/recommendations

- record selected depth/reason/cost/outcome;
- add depth A/B and ablation evidence schema;
- produce recommendation reports without auto-changing behavior.

### AL-2 — targeted verification depth

- formalize D1-D4 verification selection;
- use existing graph-linked test selection first;
- add progressive fallback/escalation;
- record verification scope in evidence/Convergence.

### AL-3 — Task-aware adaptive depth

- Task-aware planner selects per-capability depth inside configured bounds;
- start in shadow/advisory;
- evaluate native/manual/static-depth/auto-depth.

### AL-4 — strengthened capabilities

Implement Risk Intelligence, Verification 2.0, Project Evidence Memory, PI Trace/Replay, API/resource/state relations, weak-local protocol and OMO cross-agent consistency **one capability at a time**, each with supported depth mappings and contribution evidence.

Do not promote a higher depth unless it passes its measured adoption gate.

## 16. Acceptance rules

A configurable/adaptive depth system is acceptable when:

1. rollout mode and execution depth are independent;
2. users can set global profile plus per-capability min/max/preferred/auto;
3. `auto` never exceeds privacy/capability/user bounds;
4. higher levels are evidence-gated, not assumed superior;
5. no-benefit higher levels can be demoted without removing the capability;
6. selected depth/reason is inspectable;
7. runtime does not silently rewrite persistent user configuration;
8. targeted tests are the normal path for bounded changes once recall is accepted;
9. full-suite fallback remains available and mandatory for defined high-risk/release cases;
10. Convergence records verification scope and freshness;
11. periodic full-suite sampling calibrates selected-test misses;
12. weak-local, practical-local, host and frontier model tiers are evaluated separately;
13. OMO compatibility tests include verification/depth interaction when OMO is enabled;
14. native OpenCode remains a working fallback.

## 17. Decision principle

**More Project Intelligence is not automatically better.**

The desired product is an evidence-driven adaptive system that can retain a powerful capability while using it lightly for normal work, deeply only when justified, and lowering its recommended level again when real evaluations show that extra processing does not improve verified outcomes.
