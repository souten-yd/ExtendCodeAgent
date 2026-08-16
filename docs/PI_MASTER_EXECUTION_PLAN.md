# ExtendCodeAgent — PI Master Execution Plan

Status: **canonical single execution plan**. This document owns product scope, capability inventory,
evaluation design, stage sequencing, and release gates.
Date: 2026-08-16
Supersedes: the sequencing, backlog numbering, corpus definitions, metric lists and release-gate lists
of every document named in section 2. Those documents remain valid as design detail.

## 0. Why this document exists

Before this consolidation the repository contained 26 planning documents (~10,650 lines) with:

- three different "canonical read order" lists (`CURRENT_STATUS.md`, `handoff/CURRENT_HANDOFF.md`,
  `handoff/NEXT_TASK.md`);
- eight parallel stage-numbering schemes (`PR-A..PR-I`, `RV-0..RV-FINAL`, `COMP-0/RA-x/TA-x/WL-0/VI-0/
  RB-0/DA-0/EM-0/MA-0/RV-X`, `AL-0..AL-4`, `CV-0..CV-FINAL`, `TP-0..TP-7`, `VI-X0..VI-XFINAL`, plus two
  unnumbered ordered lists);
- two incompatible evaluation corpora;
- one already-declared but unapplied absorption (`VI-0` absorbing `RV-3`);
- a release-gate list whose blocking items include an externally unavailable provider path.

There is now exactly one backlog: section 8. Any future plan MUST edit this document rather than add a
parallel roadmap (section 13).

## 1. Product definition

> ExtendCodeAgent is a host-neutral Project Intelligence and Verification Runtime. It gives coding
> agents persistent revision-aware project truth, bounded evidence, impact/test/runtime reasoning,
> evidence-backed completion, and weak-local-model efficiency, while the agent runtime keeps ownership
> of the agent loop, execution, permissions and orchestration.

OpenCode is the current reference and production-target runtime. The core remains portable by
architecture; no second harness is a current production dependency.

The **primary** defended area is **Verification Intelligence**: deriving what must be verified from a
semantic change, reusing still-valid evidence under an explicit dependency closure, re-evaluating
failures without weakening tests, and backing completion with executed revision-matched evidence.
Project Truth, Task-aware Intelligence, Weak-local Efficiency and Cross-agent Consistency are
supporting areas that exist to make the primary one possible.

Project Truth is **not** the differentiator. Mature code-intelligence products (Sourcegraph, CodeQL,
IDE indexers, LSP servers) already build code graphs with wider language coverage and greater scale
than this project has; against them a Project Graph is parity at best. What they do not provide is
revision-aware evidence with invalidation, verification obligations as first-class objects, or bounded
agent-shaped delivery. See `COMPETITIVE_ANALYSIS_AND_FEATURE_GAP_ROADMAP.md` §2 and §3.3, which carry
the ranking and the code-intelligence comparison column.

Language scope is currently **Python and JavaScript/TypeScript only** (`KNOWN_ANALYZERS`). Every
Project Truth claim is bounded by that until another analyzer is measured, and the pinned corpus
(§7.3) reflects the same limit. This is a stated product boundary, not an oversight.

Everything else is delegated to the runtime (`COMPETITIVE_ANALYSIS_AND_FEATURE_GAP_ROADMAP.md` §11
non-goals remain binding).

## 2. Document consolidation map

| Document | Disposition |
|---|---|
| `PROJECT_INTELLIGENCE_MASTER_PLAN.md` | **Canonical domain reference.** Capability portfolio, graph/twin targets, architecture principles. Sequencing in §21 superseded. |
| `RUNTIME_ADAPTER_ARCHITECTURE_PLAN.md` | **Canonical architecture reference** for runtime boundary/observations. §11 sequence superseded. |
| `IMPLEMENTATION_EXECUTION_LOCAL_VALIDATION_PLAN.md` | **Canonical reference** for config schema, routing, performance budgets, merge/CI policy. §14 waves are history. |
| `PRODUCTIZATION_AND_MODEL_EVALUATION_PLAN.md` | Reference for productization principles/metrics. §15 `RV-0..RV-FINAL` sequence and §17 gates superseded by §8/§10 here. |
| `COMPETITIVE_ANALYSIS_AND_FEATURE_GAP_ROADMAP.md` | **Canonical adopt/delegate/reject decisions** (§4–§9, §11, §13). §10 sequence superseded. |
| `TRANSPARENT_PI_ORCHESTRATION_PLAN.md` | Canonical design detail for the task-aware controller (levels L0–L5, signals, selection metrics). Consumed by stage C1/C3. |
| `ADAPTIVE_CAPABILITY_LEVELS_AND_TARGETED_VERIFICATION_PLAN.md` | Canonical design detail for the depth axis (D0–D4, ablation policy). `AL-0..AL-4` superseded. |
| `VERIFICATION_OBLIGATION_AND_TEST_EXECUTION_PLAN.md` | Design detail for obligations / required verification set. Sequence superseded → V0/V2. |
| `COMPOSITIONAL_VERIFICATION_AND_EVIDENCE_REUSE_PLAN.md` | Design detail for evidence segments/reuse. `CV-0..CV-FINAL` superseded → V0/V3. |
| `FAILURE_DRIVEN_PI_REEVALUATION_PLAN.md` | Design detail for failure taxonomy/re-evaluation. Sequence superseded → V0/V4. |
| `PI_VERIFICATION_OBSERVABILITY_INTEGRATED_DESIGN.md` | Design detail for observability/environment/certificate. `VI-X0..VI-XFINAL` superseded → V0/V5 and Deferred set. |
| `TEST_PORTFOLIO_INTELLIGENCE_AND_BROAD_EVALUATION_PLAN.md` | Design detail for portfolio/bootstrap/GUI and the pinned external corpus. `TP-0..TP-7` superseded → E4/V-series/Deferred. |
| `OPENCODE_VALIDATION_AND_ADOPTION_PLAN.md` | Canonical evidence rule and ControlDeck ruling. Sequencing folded into §8. |
| `OMO_COEXISTENCE_AND_COMPATIBILITY_PLAN.md` | Conditional compatibility reference. Executed only at stage P4. |
| `KASANECORE_MIGRATION_AUDIT.md` | Historical migration reference. No active obligations. |
| `CODEX_IMPLEMENTATION_GUIDE.md`, `CODEX_PRODUCTIZATION_EXECUTION_GUIDE.md` | Agent working rules. Their read orders and first-task sections are replaced by §8 and `handoff/NEXT_TASK.md`. |
| `CURRENT_STATUS.md` | Program state and evidence ledger only. No sequencing. |
| `handoff/*` | Rolling state. `NEXT_TASK.md` points at this document. |

## 3. Resolved inconsistencies

| # | Conflict | Resolution |
|---|---|---|
| 1 | Three canonical read orders | One read order: this document → `handoff/NEXT_TASK.md` → `CURRENT_STATUS.md` → design detail for the active stage only. |
| 2 | Eight stage-numbering schemes | One backlog (§8). Legacy IDs are mapped in §9 and MUST NOT be used to schedule work. |
| 3 | `RV-3` vs `VI-0` (declared absorbed, never applied) | Both dissolved into the V-series (V1 calibration, V2 required set, V4 failure triage). |
| 4 | Two corpora: local repos (ECA/KasaneCore/ControlDeck) vs pinned external five | Both retained with distinct roles (§7.3). Neither alone is acceptance evidence. |
| 5 | Frontier provider path is a blocking release gate but is externally `UNAVAILABLE` (`0/18 APIError`) | Frontier becomes a **conditional** gate with an explicit re-scope rule (§10.3). A provider outage cannot indefinitely block the baseline. |
| 6 | PI Trace / Evidence Memory scheduled at P1, but depth telemetry (`AL-1`), ablation attribution and failure replay all depend on it | Split: a **minimal evaluation-only trace** moves to stage E5 (Phase 0); durable Project Evidence Memory becomes stage **P0**. |
| 7 | Capability depth axis is specified but the config schema has only `RolloutMode` | Depth contract moves into Phase 0 (stage E2) because every later evaluation claim is depth-conditional. |
| 8 | 10 of 21 declared capabilities are never gated in code (§6) | Stage E1 makes gating total before any ablation-based decision is recorded. |
| 9 | Verification work is split across five documents with overlapping objects (`SemanticChangeSet` appears in three) | One contract stage (V0) defines each object exactly once. |

## 4. Invariant policies

These apply to every stage and are not restated per stage.

1. **Evidence policy.** Source files and mocked tests are not completion. Distinguish deterministic
   unit/component evidence, real-repository benchmark evidence, real OpenCode evidence, real
   model-routing evidence, and `UNAVAILABLE`. Never mark unavailable evidence as passed. Planning
   documents are design evidence only.
2. **Mandatory feature-effect rule.** A capability is adopted only after evaluation with the
   OpenCode/agent/model combinations required to prove its claim. Mode comparison baseline:
   `native / off / shadow / advisory / active`.
3. **Anti-overfit.** Multiple repositories, reserved held-out tasks and at least one held-out
   repository outside tuning. ControlDeck-launched and terminal-launched OpenCode are the same
   condition until a semantic difference is measured.
4. **Truthful degradation.** `off` is inert, `shadow` changes nothing, `advisory` never silently
   becomes active, active fails closed to advisory/native on stale or unavailable evidence.
5. **Deterministic before model.** Deterministic analysis precedes model reasoning at every tier. LLM
   output never becomes verified project truth.
6. **Two independent axes.** Rollout mode (authority) and capability depth (cost) are configured
   separately. Never encode cost in the rollout mode.
7. **Privacy.** Local-only/no-remote-source policies are hard bounds that automation cannot override.
8. **Repository content is untrusted input.** Every capability here reads repository-derived text
   (identifiers, docstrings, comments, test names, commit messages, dependency metadata, research
   results) and delivers it into an agent's context. That is an injection channel: a file in the
   analyzed repository can contain text shaped like instructions. The bounds are:
   - PI output is **data, never instruction**. Every PI payload is structured (`canonical_ref`, `kind`,
     `confidence`, `provenance`, `revision`), and free text from the repository appears only inside
     clearly delimited value fields, never as top-level prose that could read as a directive.
   - PI never escalates its own authority from repository content. Rollout mode, depth, capability
     selection, privacy policy and verification verdicts are decided by configuration and
     deterministic analysis only. No repository text can change them.
   - A verification verdict is never derived from repository prose. `verified` requires executed
     evidence with a matching revision; a comment claiming a test passes is not evidence.
   - Provenance is mandatory and distinguishes `source`, `runtime`, `model` and `external`. External
     research evidence (§9.3 of the competitive analysis) can never become project truth by itself.
   - The threat is evaluated, not assumed away: the E3 task suite includes at least one repository
     containing benign injection-shaped strings, and B0 records whether any PI path propagated them as
     instructions. A propagation is a release blocker, not a known limitation.

   This invariant is about **inbound** trust. Invariant 7 covers the outbound direction; the two are
   separate and neither implies the other.
9. **CI policy.** Validation is local. GitHub CI stays minimal; no real-model evaluation or provider
   secrets in mandatory CI. Additions require a `handoff/DECISIONS.md` entry first.
10. **Stop rule.** Defer or drop any capability that does not improve a measured real task, duplicates
   existing evidence, disproportionately raises default latency/size, is too imprecise for active use,
   benefits only one model tier while others regress, requires OpenCode core patches, or creates a
   second implementation of an existing core capability.

## 5. Current program state

- `PR-A .. PR-I` implementation baseline complete; 62 Python modules under `src/extendcodeagent`,
  plus the stable OpenCode 1.18.18 adapter and MCP surface (`pi_status`, `pi_symbol`, `pi_references`,
  `pi_path`, `pi_impact`, `pi_tests`, `pi_context`, `pi_runtime_evidence`, `pi_research_plan`).
- No production-capable designation. Baseline validation has not started.
- **No existing evidence supports the product thesis.** The only real-model result on record,
  `docs/evidence/pr-g/model-evaluation.json`, is 6 scenarios at 1 repetition with `tool_calls = 0` in
  every arm. Zero tool calls means the agent never performed agentic work: this is a context-injection
  A/B, not task completion. `local-low` moving from 1/6 to 6/6 between `off` and `active` is close to
  tautological under that setup, since the needed facts were placed directly in the prompt. Under
  invariant 1 the result is real model-routing evidence that the routing path works, and nothing more.
  It is **not** evidence that Project Intelligence improves agent outcomes, and no claim may cite it as
  such. B0 replaces it against the sealed E3 task suite, with repetitions and real tool use.
- Known blockers and measurement limits are recorded in `handoff/KNOWN_ISSUES.md`; the material ones
  for sequencing are: frontier path `0/18 APIError`, `local-low` result instability, py-tree-sitter
  pinned to 0.25.2 after a 0.26.0 segfault, and OpenCode version drift risk beyond 1.18.18.

## 6. Capability inventory and gating status

Source of truth: `CapabilityName` in `src/extendcodeagent/core/config/schema.py` versus actual
`CapabilityPolicy` use. **Closed by stage E1 (2026-08-16).** Gating is no longer confined to
`service/application.py`; `strategy/service.py` and `testing/service.py` gate through the same
`CapabilityPolicy.require_explicit_use`, and the declarations below are enforced by
`tests/architecture/test_capability_gating.py`.

| Capability | Implementation | Policy-gated | Ablation arm |
|---|---|---|---|
| `graph` | yes | yes | yes |
| `twin` | yes | yes | yes |
| `semantic` | yes | yes | yes (covers `call_graph`) |
| `impact` | yes | yes | yes |
| `test_selection` | yes | yes | yes |
| `context` | yes | yes | yes |
| `runtime` | yes | yes | yes |
| `blueprint` | yes | yes | yes |
| `convergence` | yes | yes | yes |
| `research` | yes | yes | yes |
| `traceability` | yes | yes | yes |
| `strategy` | yes (`strategy/service.py`) | yes (E1) | yes |
| `test_obsolescence` | yes (`testing/service.py`) | yes (E1), independent of `test_selection` | yes |
| `call_graph` | yes (analyzer `may_call`, conf. 0.35) | folded into `semantic` (E1) | **no — use `semantic`** |
| `cfg` | no | `not_implemented` (E1) | no |
| `data_flow` | no | `not_implemented` (E1) | no |
| `state_event` | no | `not_implemented` (E1) | no |
| `side_effects` | no | `not_implemented` (E1) | no |
| `api_schema_db` | no | `not_implemented` (E1) | no |
| `ui_graph` | no | `not_implemented` (E1) | no |
| `memory` | no | `not_implemented` (E1) | no |

13 capabilities are independently configurable and ablatable. `call_graph` is governed by `semantic`
and the seven unimplemented names are forced to `off`; configuring any of the eight to a non-`off`
mode is a `ConfigError` rather than a silent no-op, so an evaluation arm can never record a result
under a capability that did not run. The `call_graph` folding rationale and the rejected independent
gate are in `handoff/DECISIONS.md` (2026-08-16).

Before E1 this table read 11 gated of 21, which made config-driven ablation impossible for 10
capabilities including two with real implementations. That is why Phase 0 precedes baseline
validation.

## 7. Evaluation framework

One framework serves baseline validation, per-stage adoption gates and final release validation.
Stages do not define private metric lists.

### 7.1 Arms

Mandatory per claim, minimum sufficient subset allowed with a written justification:

```text
A  native            OpenCode without ExtendCodeAgent
B  off               installed, globally off              (inertness / overhead)
C  shadow            plans and records, no behavior change (controller quality)
D  advisory          PI facts offered
E  active            PI facts applied where permitted
F  ablation(X)       best accepted configuration with capability X forced off
G  depth(d)          best accepted configuration at depth D0..D4
```

`F` and `G` are what make refinement decisions possible; they are unavailable until stages E1/E2.

### 7.2 Metric layers — never averaged into one score

- **Layer A — deterministic quality.** Impact precision/recall, resolved-call and reference precision,
  selected-test precision/recall, obligation coverage recall, evidence-invalidation recall,
  false-verified rate. Requires the versioned Layer A label set (stage E4).
- **Layer B — agent outcome.** Objective task success (tests/build/behavior), unsupported claims,
  unnecessary reads/edits, tool calls, new vs cached input tokens, output tokens, wall time, retries,
  escalations, completion correctness.
- **Layer C — system cost.** Cold index, refresh latency and revision churn, query latency, peak
  memory, DB+WAL size, OpenCode startup delta, controller decision latency, sidecar/MCP recovery.

#### Layer C budgets

"Within budget" in §7.4 means these thresholds. They are **provisional**, calibrated at B0 against the
frozen environment, and any change requires a `handoff/DECISIONS.md` entry with the measurement that
justified it. A promotion that breaches a budget is blocked even if Layer A and Layer B improve; the
correct response is a depth reduction or a scoped rollout, not a budget increase.

Repository size classes: **S** ≤ 100 source files, **M** ≤ 1,000, **L** ≤ 10,000 (the
`analysis.max_files` default).

| Metric | S | M | L | Measured as |
|---|---|---|---|---|
| Cold index (full build) | ≤ 2 s | ≤ 20 s | ≤ 180 s | median of 3 |
| Incremental refresh, single-file edit | ≤ 150 ms | ≤ 500 ms | ≤ 2 s | median of 5 |
| `pi_symbol` / `pi_references` (warm) | ≤ 100 ms | ≤ 250 ms | ≤ 500 ms | p95 |
| `pi_impact` / `pi_path` (warm) | ≤ 500 ms | ≤ 1 s | ≤ 3 s | p95 |
| `pi_context` build | ≤ 500 ms | ≤ 1 s | ≤ 2 s | p95 |
| Event enqueue → return (hook path) | ≤ 20 ms | ≤ 20 ms | ≤ 20 ms | p95, never blocking |
| OpenCode startup delta vs native | ≤ 150 ms | ≤ 150 ms | ≤ 300 ms | median of 5 |
| Peak RSS above `analysis.memory_budget_mb` | 0 | 0 | 0 | hard cap, 1024 MB default |
| DB + WAL after a full session | ≤ 50 MB | ≤ 250 MB | ≤ 1 GB | after compaction |
| Controller decision latency (C1/C3) | ≤ 50 ms | ≤ 50 ms | ≤ 100 ms | p95, deterministic path only |
| Sidecar/MCP reconnect | ≤ 5 s | ≤ 5 s | ≤ 5 s | median of 3 |

Token cost is reported per task as new vs cached input tokens and output tokens, per arm and tier
(Layer B), and additionally as the **advisory context overhead ratio** — PI-injected tokens divided by
the native prompt tokens for the same task. Budget: ≤ 0.5 at the weak-local profile and ≤ 1.5 at
frontier, since a weak local model that spends its window on evidence has none left for reasoning.

Two measured facts already constrain these numbers and must be revisited at B0: on a 50-file
repository, file-level refresh was 182.145 ms against a 185.638 ms cold build — workspace fingerprint
scanning dominated, so the S-class incremental budget is currently not met by the fingerprint path;
and the PR-D startup comparison of +24 ms median contained a 1,609 ms native outlier and is not
statistically conclusive. See `handoff/KNOWN_ISSUES.md`.

Model tiers (`local-low`, `local-practical`, `host-default`, `frontier`) are reported separately.
Repetition minimums: `local-low` 5 runs, `local-practical` 3, `host-default` 3, `frontier` 3 when
available. Report distributions, never a best run.

### 7.3 Corpora and their roles

| Role | Repositories | Used for |
|---|---|---|
| Realistic-task corpus | ExtendCodeAgent, KasaneCore, ControlDeck | agent-outcome tasks (Layer B), scale/performance (Layer C) |
| Pinned quality corpus (`docs/evaluation/test-portfolio-corpus-v1.json`) | flask, httpx, express, vite | Layer A ground truth, verification-quality stages |
| Held-out | react-hook-form + one reserved realistic repository | anti-overfit confirmation only; never used for tuning |

Corpus pins are immutable within a corpus version. Refreshing upstream creates a new version.
Third-party sources are cloned into ignored evaluation roots and never vendored.

### 7.4 Adoption / refinement decision rule

For each capability and each depth, using the arms above:

- **Promote** (`shadow → advisory → active-scoped → active-default`) only when Layer A or Layer B
  improves on repeated runs, Layer C stays within budget, and the held-out set reproduces the effect.
- **Keep scoped** when only one model tier or task class benefits.
- **Demote / defer** when `ablation(X)` shows no Layer A or Layer B degradation.
- **Reject** when ablation shows no degradation and Layer C cost is material.

Every promotion and demotion is recorded in `handoff/DECISIONS.md` with the evidence path.

## 8. Unified backlog

One stage per work package. Each stage lists entry, scope, exit evidence. Conditional stages are
skipped with a recorded reason, not silently dropped.

### Phase 0 — Make evaluation possible (no product behavior change)

**E0 — Plan consolidation**
Entry: none. Scope: this document, `NEXT_TASK.md`, `CURRENT_STATUS.md` read order, superseded banners,
decision entry. Exit: single canonical backlog; no code change.

**E1 — Capability gating conformance**
Scope: gate `strategy`, `test_obsolescence`, `call_graph` (or fold `call_graph` into `semantic` with a
recorded decision); declare the seven unimplemented capabilities `not_implemented` so config
references them truthfully; add an architecture test asserting every `CapabilityName` is either gated
by a real service or declared unimplemented; `pi_status` reports capability implementation state.
Exit: architecture test green; `off` inertness re-verified per capability.

**E2 — Capability depth contract**
Scope: depth axis (`D0..D4`) in the central config with min/max/preferred/auto, orthogonal to
`RolloutMode`; no adaptive selection yet; depth recorded in every PI response. Exit: config/architecture
tests; depth visible in `pi_status`; no behavior change at default depth.

**E3 — Layer B task suite and outcome ground truth**
Entry: E1 and E2 complete, so an arm can be described by `(capability set, depth)`.
Scope: define **what B0 actually measures**. Layer A has a versioned label set; Layer B has had no
equivalent, which would make baseline outcome numbers incomparable between runs and between arms.
Deliver a versioned `docs/evaluation/task-suite-v1.json` containing, per task: a stable task ID,
repository and pinned revision, the natural-language instruction given to the agent, the task class
(see below), the objective success oracle (command + expected result, never a human judgement call at
scoring time), an allowed-mutation scope, and a timeout.
Requirements:

- task classes must cover the capabilities that claim value: symbol/reference lookup, impact
  assessment, test selection, cross-file refactor, bug localization from a failing test,
  requirement-to-code tracing, and at least one task class expected to *not* benefit from PI as a
  negative control;
- every task's oracle is machine-checkable, so scoring does not drift between runs;
- tasks are split into tuning and held-out sets before any tuning, and the held-out split is sealed;
- minimum suite size and per-class counts are fixed in the manifest and justified, so later stages
  cannot quietly shrink the suite;
- a negative-control class and at least one task whose correct answer is "the change is unsafe /
  insufficient evidence" must be present, so the suite can detect PI-induced overconfidence.

Exit: `task-suite-v1.json` versioned and sealed; every task executed once natively to confirm the
oracle is reachable and non-trivial (native success rate is neither 0% nor 100% across the suite);
tuning/held-out split recorded.

**E4 — Unified evaluation runner and ground truth**
Scope: one runner executing `arm × repository × task × model tier × repetition` over the E3 suite and
emitting the metric keys of `docs/evaluation/pi-verification-integrated-metrics-v1.json`; retire the
per-PR scripts (`benchmark_pr_b/c/h/i`, `pr_g_evaluate`) into it; promote the `pr-c` FP/FN review and
the `pr-h` ground-truth report into a versioned label set for Layer A; bind the pinned corpus
manifest. Exit: one command reproduces a full matrix run into `docs/evidence/final/`; both label sets
(Layer A labels, Layer B task suite) versioned and referenced by the run output.

**E5 — Minimal PI trace (evaluation infrastructure)**
Scope: compact append-only record of plan → selected evidence IDs → revision IDs → model route →
verification outcome → fallback → timings. No raw model transcripts, no secrets. Enough to attribute
an outcome to a capability and to replay the PI portion. Exit: trace present for every runner arm;
ablation attribution demonstrated on one task class.

Phase 0 gate: `F` and `G` arms are executable, run against a sealed task suite, and produce
attributable results.

### Phase 1 — Baseline

**B0 — Baseline release validation and gap report** (was `RV-0`)
Scope: freeze and record environment (ECA commit, OpenCode version, provider/model tiers and
availability, repository/workspace identity and SHA, hardware); re-run local lint/typecheck/unit/
integration/build; revalidate adapter/plugin/MCP/edit/restart/reconnect/off/shadow/advisory paths;
reproduce provider failures with PI disabled first; establish native baselines before any PI
optimization; execute the arm matrix on the realistic corpus with repetition; run the first
`ablation(X)` sweep over the 13 independently ablatable capabilities (§6; `call_graph` has no arm of
its own and is covered by `semantic`); measure the competition-derived concerns
(weak-local prefix/tool-output efficiency, lifecycle observability, worktree/subagent capability
availability, completion correctness, cross-session evidence loss, host-native overlap).
Exit: `docs/evidence/final/baseline-gap-report.md` with every failure classified as OpenCode runtime,
model/provider, PI adapter, PI core, task selection, verification or performance; a ranked gap list;
and an explicit skip/keep decision for every later stage.

**B1 — Blocking host/productization repair** (conditional; was `RV-1`)
Entry: B0 records lifecycle, config, adapter, version-drift or provider friction attributable to
ExtendCodeAgent. Scope: bootstrap/lifecycle simplification, health diagnostics, version compatibility,
reconnect/event coalescing, MCP-only fallback hardening. Exit: repaired paths re-measured against B0.

### Phase 2 — Task-aware intelligence

**C0 — Minimal runtime contract** (was `RA-0`)
Scope: only the host-neutral observations a PI consumer actually uses (task/session identity, workspace
and worktree identity, mutation, tool execution, model, verification events, advisory delivery). No
field without a consumer and a conformance test. Exit: conformance test; missing host capabilities
degrade explicitly.

**C1 — Shadow task-aware planner** (was `TA-0`)
Scope: `TaskSignals` → deterministic `TaskIntent` → `IntelligencePlan` → `PlanOutcome`, shadow only, no
behavior change; levels L0–L5 per `TRANSPARENT_PI_ORCHESTRATION_PLAN.md`; no LLM classifier.
Exit: intent accuracy, capability precision/recall, under/over-selection rate measured against
human-reviewed expected plans on tuning and held-out tasks.

**C2 — Weak-local evidence protocol** (conditional; was `WL-0`)
Entry: B0/C1 show weak-local failures that bounded evidence can address. Scope: stable PI envelope
separated from task/revision evidence, deterministic candidate reduction, bounded ID/enum/schema
decisions, progressive expansion, compressed tool/runtime evidence, strict output budgets, cache-reuse
metrics where observable. Implemented inside existing context/routing code, not as a new package.
Exit: repeated `local-low` and `local-practical` distributions showing task-success or cost improvement.

**C3 — Advisory automatic selection and adaptive depth** (was `TA-1` + `AL-3`)
Scope: the planner selects capabilities *and* depth inside configured bounds; advisory only; progressive
expansion rules; reasons recorded in the trace. Exit: `native / manual-best / static-depth / auto` compared;
auto must not be worse than manual-best on Layer B while reducing Layer C.

### Phase 3 — Verification intelligence

This phase absorbs the former `RV-3`, `VI-0`, `AL-2`, `CV-*`, `TP-0..TP-3`, `VI-X0..VI-X7` and the
failure-driven sequence. Each object is defined once, in V0.

**V0 — Verification contracts** (design detail: four documents, one implementation)
Scope: `SemanticChangeSet`, `VerificationObligation`, `TestIntent`, `OracleAssessment`,
`EvidenceSegment` + dependency closure, `FailureEvidence` + result-state taxonomy. All are projections
over the existing Twin/Graph/Impact/Runtime/Traceability/Convergence model — no parallel truth store.
Exit: contracts, shadow computation, architecture tests proving no second store.

**V1 — Confidence calibration and ground truth**
Scope: precision/recall by relation class and confidence band (definition/reference, resolved call,
`may_call`, import, test relation, impact projection, runtime-confirmed); threshold validation, not
statistical modelling; separate ordinal confidence from calibrated probability in APIs and docs;
identify relation classes that may never drive active automation alone.
Exit: calibration report on the pinned corpus; thresholds updated with recorded rationale.

**V2 — Required verification set and verification depth** (was `AL-2` + obligation plan)
Scope: obligation-driven selection (`SemanticChangeSet → Impact closure → obligations → coverage graph
→ required set → cost-aware plan`), depths D0–D4, residual gap recomputation, periodic full-suite
calibration sampling, Convergence integration. Cost is a scheduling input, never a correctness selector.
Exit: selected-test precision/recall and escaped-regression rate vs full-suite reference across tiers.

**V3 — Evidence reuse and compositional verification** (was `CV-1`, `CV-2`)
Scope: invalidation-aware reuse of still-valid evidence segments, boundary contracts, verification
frontier, freshness/aging, residual-gap test suppression. Exit: false-verified rate must not rise;
heavy-run avoidance counted; diversity roles preserved.

**V4 — Failure-driven re-evaluation**
Scope: deterministic failure localization and bounded root-cause classification over the taxonomy
(implementation mismatch, test/intent/oracle/fixture defects, environment, nondeterminism,
`PI_MODEL_MISS`, `EVIDENCE_REUSE_MISS`, harness failure, unresolved specification); re-evaluation starts
at Test Intent and Oracle and expands only the unresolved PI neighborhood; obsolescence safeguard.
Exit: root-cause classification accuracy on injected-fault tasks; no obsolescence false positives on
held-out repositories.

**V5 — Observability, environment and certificate** (conditional)
Entry: V2/V4 record obligations that cannot be discharged because the required truth is unobservable,
or environment-dependent misses. Scope: `ObservabilityRequirement`/`ObservabilityGap` with
host-signal-first resolution, environment equivalence classes and impact-selected profiles,
`VerificationCertificate` as an auditable per-revision reason record. Missing observability is not
automatically a missing test; unresolvable obligations stay `unavailable`.
Exit: gap precision/recall, environment miss rate, certificate correctness on stale/missing/conflicting
evidence cases.

### Phase 4 — Active rollout

**A0 — Bounded active** (was `TA-2`)
Scope: only accepted low-risk task/relation classes; stale or uncertain evidence downgrades to
advisory/native; low-confidence `may_call` may never independently drive broad or destructive actions.
Exit: held-out confirmation before any `active-default`.

**A1 — Progressive expansion** (was `TA-3`)
Scope: expand only from recorded evidence gaps. Model escalation stays a separate policy decision.

### Phase 5 — Conditional deep capability

Stage identifiers in this phase are `X*`, not `D*`. `D0..D4` denotes **capability depth only**
(§7.1 arm G, stage E2), and must never be used as a stage identifier.

**X0 — Runtime bridge** (was `RB-0`/`RV-4`). Entry: repeated measured failures at a real user-visible
boundary (browser event → handler, client fetch → route, route → backend, DI/registration, observation →
symbol). Smallest bridge only; generic relations with runtime provenance; inferred bridge facts stay
low-confidence. Skip if recall is already sufficient.

**X1 — Bounded deep analysis** (was `DA-0`/`RV-5`). Entry: data-origin/security tasks fail measurably.
DFG/Taint before CFG, bounded to a symbol neighborhood, never repository-wide or always-on.

### Phase 6 — Release

**R0 — Production-capable baseline** (was `RV-FINAL`). No new feature scope. Re-run the matrix on
realistic + pinned + held-out corpora; verify §10 gates; document known limitations honestly.

### Phase 7 — Post-baseline strategic work

**P0 — Project Evidence Memory + durable PI trace/replay** (was `EM-0`). Promoted earlier only if B0
proves cross-session evidence loss is release-blocking. Reuses the E5 trace and existing SQLite/
revision/provenance contracts. Records require provenance, revision/workspace scope, confidence and an
invalidation policy. Not conversational memory.

**P1 — Adapter and MCP conformance** (was `RA-1`, `RA-2`).

**P2 — Second-harness proof** (was `RA-3`). Exactly one runtime, chosen at that time on API stability,
hook quality and user value. Must reuse the core without rewriting it.

**P3 — PI-aware parallel/worktree intelligence** (was `MA-0`). Detection and advisory only at first:
workspace-specific Twin identity, base/fork ancestry, cross-worktree affected-contract detection,
stale-context invalidation, merge-risk projection. Requires a configuration that actually provides
distinct agent/task/workspace identities; a sequential single-agent test cannot validate it.

**P4 — Comparative integration benchmark** (was `RV-X` + OMO plan). `OpenCode` vs `+OMO` vs `+ECA` vs
`+OMO+ECA` on identical tasks/revisions/models, using the conflict taxonomy C0–C6. Purpose is
complementarity and duplicate-overhead detection, not a score.

### Deferred set (design retained, no scheduled stage)

Test synthesis/generation and its quality gate; portfolio consolidation; GUI flow graph and GUI
compositional verification; mutation/fault-probe policy; regression knowledge mining; nondeterminism
intelligence; verification debt diagnostics; performance verification obligations; stratified
calibration sampling; repository-wide CFG/DFG/state/event/UI graphs; universal Blueprint/Strategy/
Research generation.

Each item re-enters the backlog only through §7.4 with a measured failure it is the smallest fix for.

## 9. Legacy identifier mapping

| Legacy | Now |
|---|---|
| `COMP-0` | E0 |
| `RV-0` | B0 (extended with the E-phase prerequisites) |
| `RV-1` | B1 |
| `RV-2` / `TA-0` | C1 |
| `RV-3` / `VI-0` | V1 + V2 + V4 |
| `RV-4` / `RB-0` | X0 |
| `RV-5` / `DA-0` | X1 |
| `RV-FINAL` | R0 |
| `RV-X` | P4 |
| `RA-0` / `RA-1` / `RA-2` / `RA-3` | C0 / P1 / P1 / P2 |
| `TA-1` | C3 |
| `TA-2` / `TA-3` | A0 / A1 |
| `WL-0` | C2 |
| `EM-0` | E5 (minimal, evaluation) + P0 (durable) |
| `MA-0` | P3 |
| `AL-0` / `AL-1` / `AL-2` / `AL-3` / `AL-4` | E2 / E4+E5 / V2 / C3 / per-capability stages |
| `CV-0` / `CV-1` / `CV-2` / `CV-3` / `CV-4` / `CV-FINAL` | V0 / V3 / V3 / Deferred / Deferred / R0 |
| `TP-0` / `TP-1` / `TP-2` / `TP-3` / `TP-4` / `TP-5` / `TP-6` / `TP-7` | V0 / V2 / Deferred / Deferred / Deferred / E4 / B0+R0 / P4 |
| `VI-X0` / `VI-X1` / `VI-X2` / `VI-X3` / `VI-X4..X7` / `VI-XFINAL` | V0 / V5 / V5 / V5 / Deferred / R0 |
| Verification-obligation plan steps 1–11 | V0 (1–3), V2 (4–9), R0 (10–11) |
| Failure-driven plan steps 1–10 | V0 (1–3), V4 (4–8), Deferred (9), R0 (10) |

## 10. Release gates for R0

### 10.1 Blocking

1. clean local lint, typecheck, unit, integration, build;
2. current stable OpenCode plugin load and core tool smoke, on the version recorded at B0;
3. MCP connection, reconnect and fallback smoke;
4. `off` inertness, verified per capability (depends on E1);
5. advisory and active behavior consistent with capability policy and depth bounds;
6. repeated `local-low` and `local-practical` evaluation recorded as distributions;
7. `host-default` comparison recorded;
8. no privacy-policy leak in deny, metadata and selected-context tests;
9. context and token budget evidence;
10. impact and selected-test quality evidence against the versioned label set;
11. completion correctness including stale, missing, conflicting and external-only evidence cases;
12. repository-scale startup, index, refresh, memory and DB evidence;
13. installation, configuration and recovery verified on a clean environment;
14. held-out repository confirmation for every `active-default` capability;
15. known limitations documented honestly;
16. handoff documents updated so another agent can reproduce every gate.

### 10.2 Program-level stop and pivot criteria

Invariant 10 is a per-capability stop rule. It cannot answer the question B0 might actually raise:
*what if the premise is wrong?* Without a stated answer, the default outcome is indefinite
continuation, which is the failure mode this plan exists to prevent. These criteria are evaluated at
B0 and re-evaluated at R0.

**Pivot to verification-only.** If B0 shows no Layer B improvement attributable to Project Truth
capabilities (`graph`, `twin`, `semantic`, `impact`, `context`) at any model tier on the held-out
split, but the verification capabilities do improve completion correctness, then Project Truth is
demoted to internal substrate: no Project Truth capability is promoted past `advisory`, the product
claim narrows to Verification Intelligence, and Phases 2 and 5 are cut to what the V-series needs.

**Pivot to weak-local-only.** If improvement appears only at `local-low` and `local-practical` and
disappears at `host-default`, the product is repositioned as a weak-local efficiency layer. Frontier
claims are withdrawn entirely rather than qualified, and §10.3's conditional gate becomes moot.

**Stop.** Halt productization and record the negative result if **all** of the following hold after
B0, with a repeat run confirming them:

1. no capability shows a Layer A or Layer B improvement that survives ablation on the held-out split
   at any model tier;
2. Layer C cost of the best configuration exceeds the §7.2 budgets at M scale;
3. no failure class in the B0 gap report is attributable to a fixable ExtendCodeAgent defect — that
   is, the shortfall is in the premise, not the implementation.

A stop is written up as a negative result in `docs/evidence/final/baseline-gap-report.md` with the
same evidence standard as a positive one. Under invariant 1 a negative result is a real result;
abandoning the program quietly, or continuing while unable to state what would change the decision,
are both prohibited.

**What does not trigger a stop:** provider unavailability (§10.3), a single weak model tier
regressing, missing language coverage, or OpenCode version drift. Those are scope or environment
problems with known handling in §12.

### 10.3 Conditional — frontier model path

A functioning frontier path is required **if one is available and permitted**. If the configured path
remains unavailable for reasons outside the repository (credentials, provider outage, export policy),
R0 may proceed with a recorded exception that states: the exact provider/model/error category without
secrets, the native-OpenCode reproduction proving the failure is not ExtendCodeAgent-specific, the
scope of claims withdrawn, and the re-test trigger. The exception is a documented limitation, never a
pass. No frontier-tier performance claim may be made under this exception.

## 11. Evidence layout

```text
docs/evidence/final/
  environment.md              # B0 frozen environment
  baseline-gap-report.md      # B0 ranked gaps and stage skip/keep decisions
  model-matrix.json           # arms × tiers × repetitions
  task-results.json           # Layer B
  graph-quality.json          # Layer A against the versioned label set
  ablation.json               # per-capability F-arm results
  opencode-integration.json
  performance.json            # Layer C
  release-gates.md            # §10 status
docs/evaluation/
  test-portfolio-corpus-v1.json
  pi-verification-integrated-metrics-v1.json
  labels-v1/                  # E4 Layer A ground truth promoted from pr-c and pr-h
  task-suite-v1.json          # E3 Layer B task suite, tuning/held-out split sealed
```

Per-PR evidence directories (`docs/evidence/pr-*`) are historical and are not rewritten.

## 12. Risk register

| Risk | Current state | Handling |
|---|---|---|
| Provider/frontier unavailability blocks release | `0/18 APIError` | §10.3 conditional gate |
| `local-low` result instability | observed across repeated runs | distributions only, never best-run; scoped rollout |
| py-tree-sitter segfault | 0.26.0 crashed; pinned 0.25.2 | three-repetition real-repository check inside B0; replace the binding path on recurrence |
| OpenCode version drift | validated on 1.18.18 only | re-verify at B0 and R0; adapter absorbs shape changes |
| Single-repository overfit | ControlDeck previously dominant | corpus roles in §7.3; held-out reserved |
| Plan re-proliferation | root cause of this consolidation | §13 |
| Evaluation harness drift | per-PR scripts | E4 retires them into one runner |

## 13. Maintenance rule

1. New strategy, scope or sequencing changes edit **this document**. Do not create another plan file.
2. A new design document is allowed only for detail that does not fit here, and it must be registered
   in §2 with a disposition and a stage owner on the same commit.
3. Stage promotion, demotion and skip decisions are appended to `handoff/DECISIONS.md` with the
   evidence path.
4. Revalidate the competitive snapshot at B0, before P2 and before P3, when OpenCode materially changes
   its plugin/event contract, and at least every 90 days while productization is active.
5. Delete or consolidate superseded steps rather than accumulating parallel plans.

## 14. Immediate next action

Phase 0, stages E0 and E1 are complete. Next is E2.

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

Do not start B0 before E1–E5 are complete. A baseline measured without total capability gating,
a depth contract, a unified runner and attributable traces cannot support any refinement decision,
and would have to be repeated.
