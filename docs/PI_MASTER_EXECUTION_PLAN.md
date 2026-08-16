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

The **primary differentiation hypothesis** is **Verification Intelligence**: deriving what must be
verified from a semantic change, reusing still-valid evidence under an explicit dependency closure,
re-evaluating failures without weakening tests, and backing completion with executed revision-matched
evidence. Project Truth, Task-aware Intelligence, Weak-local Efficiency and Cross-agent Consistency are
supporting areas that exist to make the primary one possible.

It is deliberately called a **hypothesis**, not a moat. §5 records that no evidence yet supports the
product thesis; asserting a moat in the same document would be the same overclaiming this plan exists
to prevent. It becomes a moat when B0 measures it against native OpenCode and against the existing
tooling a developer would otherwise use — not before. §10.2 states what happens if it does not.

Project Truth is **not** the differentiator. Mature code-intelligence products (Sourcegraph, CodeQL,
IDE indexers, LSP servers) already build code graphs with wider language coverage and greater scale
than this project has; against them a Project Graph is parity at best. What they do not provide is
revision-aware evidence with invalidation, verification obligations as first-class objects, or bounded
agent-shaped delivery. See `COMPETITIVE_ANALYSIS_AND_FEATURE_GAP_ROADMAP.md` §2 and §3.3, which carry
the ranking and the code-intelligence comparison column.

Language scope is currently **Python and JavaScript/TypeScript only** (`KNOWN_ANALYZERS`). Every
Project Truth claim is bounded by that until another analyzer is measured, and the pinned corpus
(§7.3) reflects the same limit. This is a stated product boundary, not an oversight.

**Target project profile.** The differentiation hypothesis is conditional on the cost of the
alternative. Where a full test suite runs in seconds, running it is faster, simpler and more certain
than any obligation-driven selection, and this product should lose. The claim is therefore scoped to
projects where at least one holds: the full suite is slow or expensive enough that running it on every
change is impractical; verification crosses process, service or UI boundaries that a unit suite does
not cover; or the agent operates across sessions and worktrees where prior evidence would otherwise be
lost. Outside that profile, ExtendCodeAgent should be honest that native OpenCode plus a fast test
command is the better answer. §7.3 pins a slow-suite repository so the profile is actually represented
in the evaluation.

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
| `OMO_COEXISTENCE_AND_COMPATIBILITY_PLAN.md` | **Canonical coexistence reference.** Its §4 conflict taxonomy, §9 `OMO-C0` gate and §11 stop rules are live: smoke subset at B0/R0 (§10.1 item 17), `OMO-C0` as stage **B2**, `OMO-C1` as the P3 entry condition, full comparison at P4. |
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

     This does **not** mean PI may not produce prose. Three kinds of text must stay distinguishable,
     and only the third carries authority:

     | Kind | Example | Trust |
     |---|---|---|
     | Repository-origin text | a docstring, a test name, a commit message | quoted value, untrusted, always attributed to its source |
     | PI-generated explanation | `"reason": "foo() is affected because bar() calls it"` | analysis with provenance — required, and must not be suppressed |
     | Control instruction | rollout mode, depth, capability selection, privacy policy | trusted configuration and deterministic analysis only |

     Explanations are a product requirement, not a risk: an impact result without a reason is not
     usable evidence. The rule forbids repository-origin text from being *promoted* into the second or
     third row, not the existence of the second row.
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

Mandatory per claim, minimum sufficient subset allowed with a written justification. §7.5 defines how
that subset is chosen, because the full product is not executable.

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
The current evaluation environment pins `local-practical` to Qwen3.6 27B through the already-running
Llama-compatible service on port 8090. Do not start Ollama or another substitute server; probe and
wait for model wake-up. The frontier tier has two mandatory model arms, Sonnet and Codex, both through
the GitHub Copilot provider registered in OpenCode. Their exact installed model identifiers are sealed
in E3 rather than guessed in core code. OpenCode may be launched through ControlDeck's existing launch
path, but remains ordinary OpenCode for ECA architecture and scoring.

Repetition minimums: `local-low` 5 runs, `local-practical` 3, `host-default` 3, and 3 each for the
Copilot Sonnet and Copilot Codex frontier arms when available. Report distributions, never a best run.

### 7.3 Corpora and their roles

| Role | Repositories | Full-suite time | Used for |
|---|---|---|---|
| Realistic-task corpus | ExtendCodeAgent, KasaneCore, ControlDeck | record at B0a | agent-outcome tasks (Layer B), scale/performance (Layer C) |
| Pinned quality corpus (`docs/evaluation/test-portfolio-corpus-v1.json`) | flask, httpx, express, vite | record at B0a | Layer A ground truth, verification-quality stages |
| **Slow-suite repository** (required, to be selected and pinned at E3) | one repository whose full suite exceeds **10 minutes** | > 10 min, measured | the condition under which selective verification can pay for itself |
| Held-out | react-hook-form + one reserved realistic repository | record at B0a | anti-overfit confirmation only; never used for tuning |

**Why the slow-suite row is mandatory.** Selective verification only has value when running everything
is expensive. On a suite that finishes in thirty seconds, "run the whole thing" is faster, simpler and
strictly more certain than any obligation-driven selection — and correctly beats this product. The
existing corpus (flask, httpx, express, vite) is fast-testing, so the current design would measure the
primary differentiation hypothesis under precisely the conditions where it cannot win, and then record
a fair negative. Full-suite wall time is therefore recorded for every corpus repository and reported
alongside every selective-verification result: a required-set precision number is uninterpretable
without knowing what the alternative cost.

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

### 7.5 Screening before confirmation — the matrix is not executable in full

The arm set multiplied out is not a schedule anyone can run:

```text
arms      5 base (A..E) + 13 ablation (F) + 5 depth (G)      = 23
tiers×reps  local-low ×5, local-practical ×3, host-default ×3,
            Copilot Sonnet ×3, Copilot Codex ×3               = 17
runs      23 × 17 × tasks                                    = 391 × tasks
```

At 20 tasks that is **7,820 agent runs**; at 40 tasks, 15,640. The one real measurement on record
(`pr-g`) took 15.8 s for a *trivial* local-medium scenario with no tool calls; a genuine agentic task
with reads, edits and test runs is minutes. At three minutes per run, 20 tasks is roughly **391 hours
of continuous execution**, before B0's environment freeze, bootstrap conformance, integration
revalidation, OMO smoke and GUI causal measurement are counted at all.

A plan that cannot be executed produces no evidence, which is the same outcome as having no plan.
Repetition minimums alone do not fix this: they say how many times to repeat a cell, never which cells
to skip. So the matrix is run in two passes.

**Screening.** Wide and shallow. Each `ablation(X)` runs at **one** model tier — the tier whose claim
the capability is supposed to serve — over a fixed subset of the tuning split, at default depth, with
the minimum repetitions for that tier. Depth arms run only for capabilities that make a depth-dependent
claim. Screening cannot promote anything and cannot demote anything; it only decides what is worth
confirming.

**Confirmation.** Narrow and deep. Only capabilities whose screening result crosses the effect
threshold proceed to the full tier set, full repetitions and the held-out split. Promotion and demotion
decisions under §7.4 may cite **confirmation results only**.

Rules that keep this honest:

- the screening subset, the effect threshold and the tier assignment per capability are fixed **before**
  the first run and recorded, so the subset cannot be tuned toward a desired outcome;
- a capability that screens out is recorded as `no screened effect`, not as `rejected` — screening is
  under-powered by construction and its negatives are weaker than its positives;
- any capability whose screening result is within noise of the threshold goes to confirmation, since
  the cost of a wrong skip exceeds the cost of an extra run;
- `native` (A) and `off` (B) always run at full tiers and repetitions: they are the baselines every
  other number is read against, and a cheap baseline corrupts everything above it.

This is a sampling design, not a reduction in evidence standards. Invariant 1 and §7.4 are unchanged;
what changes is that effort is spent where an effect might exist.

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
**Closed on `agent/e2-capability-depth-contract` (2026-08-16).**
Scope: depth axis (`D0..D4`) in the central config with min/max/preferred/auto, orthogonal to
`RolloutMode`; no adaptive selection yet; depth recorded in every PI response.

Also in scope: **bind the inferred-relation confidence threshold to depth.** E1 folded `call_graph`
into `semantic` on the reasoning that `may_call` stays in the graph and is controlled at *use* time by
confidence and depth rather than at *production* time by a gate. That control point does not exist
yet. E2 defines it: each depth carries a minimum confidence for inferred relations, so `D1` excludes
`may_call` at confidence 0.35 while `D3` admits it. Without this the folding decision is only half
implemented — the edges are produced unconditionally and nothing bounds their use.

Exit: config/architecture tests; depth visible in `pi_status`; inferred-relation threshold observable
per depth; no behavior change at default depth.

**V0a — Verification contract slice (shadow, evaluation-only)**
**Closed on `agent/v0a-verification-contract-slice` (2026-08-16).**
Entry: E2. Deliberately named `V0a`, not `E3` — it is a pulled-forward slice of stage V0, and the
E-series was renumbered once already; a second renumber would cost more than the naming irregularity.

Why it moves into Phase 0: §1 designates Verification Intelligence the primary differentiation
hypothesis, yet the entire V-series sits in Phase 3, behind Phase 0, B0 and Phase 2. Everything built
so far — 13 capabilities, all of Project Truth — is the part §1 concedes is at parity with mature code
intelligence. So the baseline would measure only the conceded part, and §10.2's verification-only pivot
would have nothing to pivot *to*. A programme cannot test its central hypothesis four phases after it
tests everything else.

Scope, minimal and shadow-only: `SemanticChangeSet` and `VerificationObligation` as projections over
the existing Twin/Graph/Impact/Test/Runtime model, plus derivation of a **required verification set**
from a change. No evidence reuse, no failure taxonomy, no oracle assessment, no certificate — those
stay in V0/V2–V5. No behavior change: computed in shadow, recorded in the E5 trace, never applied.

Exit: contracts defined once; architecture test proving no second truth store; required-set quality
(precision/recall against the executed suite) measurable on the pinned corpus, so B0b returns a first
number on the differentiation hypothesis rather than deferring it to Phase 3.

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
- **a cross-boundary GUI/runtime causal task class is mandatory.** At least one task must require
  tracing a user-visible flow across a boundary — button press → command → backend → process → visible
  state — on a real mixed UI/backend repository. This is a *measurement*, not a feature request: it
  is scored on how far current PI can follow the chain and where it loses the thread, and a low score
  is an expected, reportable outcome. `ui_graph` stays `not_implemented`; nothing here authorizes
  building it. The purpose is to produce the evidence that decides whether stage X0 (runtime bridge)
  and V5 (observability) are justified, and the plan already requires that such decisions come from
  measured failures at a real user-visible boundary rather than from assumption. Without this class,
  X0's entry condition can never be satisfied or refuted;
- every task's oracle is machine-checkable, so scoring does not drift between runs;
- tasks are split into tuning and held-out sets before any tuning, and the held-out split is sealed;
- minimum suite size and per-class counts are fixed in the manifest and justified, so later stages
  cannot quietly shrink the suite;
- a negative-control class and at least one task whose correct answer is "the change is unsafe /
  insufficient evidence" must be present, so the suite can detect PI-induced overconfidence;
- **`OpenCode + OMO + ExtendCodeAgent` at `local-low` is a required arm on a subset of the suite.**
  This is the intended production configuration and simultaneously the worst case for context budget:
  both extensions inject into the same window, and `local-low` has the least room. The only real
  measurement on record (`pr-g`) shows ECA alone taking `local-low` input tokens from 236 to 840 —
  an overhead ratio of about 2.6 against the §7.2 weak-local budget of 0.5. Those were trivial
  scenarios and the ratio will differ on real tasks, but the direction is the concern, and adding OMO
  can only compress the window further. Conflict class C2 of
  `OMO_COEXISTENCE_AND_COMPATIBILITY_PLAN.md` §4 is measured here or nowhere before release. Record
  `UNAVAILABLE` if OMO is not installable at the pinned OpenCode version.

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
an outcome to a capability and to replay the PI portion. The record includes the capability set and
the depth actually used, in a shape that later accepts the `VerificationFeature` entries V0 defines
(`used_features: {evidence_reuse: D2, oracle_assessment: D1, environment_selection: off}`), so
sub-capability ablation does not require a trace format change mid-programme.
Exit: trace present for every runner arm; ablation attribution demonstrated on one task class.

Phase 0 gate: `F` and `G` arms are executable under the §7.5 screening design, run against a sealed
task suite, and produce attributable results; and the V0a slice can report required-set quality, so
B0b measures the primary differentiation hypothesis rather than deferring it to Phase 3.

### Phase 1 — Baseline

**B0 — Baseline release validation and gap report** (was `RV-0`)
Entry — **Existing Project Bootstrap conformance**. Every capability here assumes a project the tool
has never seen before can be brought to a usable baseline; `TEST_PORTFOLIO_INTELLIGENCE_AND_BROAD_
EVALUATION_PLAN.md` treats existing-project bootstrap as a first-class lifecycle, but no stage
previously asserted it. Measuring PI on repositories whose baseline silently failed to build would
attribute a bootstrap failure to a capability. For **each** evaluation repository, record before any
arm runs:

- workspace and project identity established;
- initial Twin revision established, with node/edge counts and build time;
- test runner discovered, or explicitly `unavailable` with the reason;
- test inventory established, or explicitly `unavailable`;
- baseline evidence classified `observed` / `inferred` / `unknown` — never `verified` from import;
- every unsupported analysis explicitly degraded rather than silently skipped.

A repository that cannot reach this baseline is excluded from the arm matrix and reported as a
bootstrap gap, not as a capability result. The imported baseline is never treated as verified
correctness.

B0 runs in two passes, per §7.5. Running it as one pass is not schedulable.

**B0a — Environment, integration and screening**
Scope: freeze and record environment (ECA commit, OpenCode version, provider/model tiers and
availability, repository/workspace identity and SHA, hardware); re-run local lint/typecheck/unit/
integration/build; revalidate adapter/plugin/MCP/edit/restart/reconnect/off/shadow/advisory paths;
reproduce provider failures with PI disabled first; run the OMO coexistence smoke of §10.1 item 17 so
a namespace or duplicate-execution defect surfaces before R0 rather than at P4.

Before any long baseline or screening run, execute an exact-head **PI activation gate** through the
same ControlDeck-managed OpenCode executable. Every permitted available route (port-8090
local-practical, host-default, GitHub Copilot Sonnet and GitHub Copilot Codex) must call `pi_status`
and a task-bearing non-status PI tool, observe the configured capability modes/depths, a ready Twin
revision, provenance-bearing canonical evidence and positive PI execution time. The gate also checks
that every capability scheduled for ablation has at least one reachable OpenCode runtime route and a
covered screening task. Tool visibility, planned matrix state, or an unobserved prompt prefix alone
does not pass. A missing route is a blocking B1 adapter/productization gap; do not spend the full
matrix to infer `no screened effect` from a capability that could not run.

Activation proves execution, not benefit. Before the comprehensive schedules, run the sealed
**PI-effect pilot** on port-8090 local-practical: `native / off / active` over symbol, impact and test
selection tasks, three repetitions each (27 cells). Every active cell must use its task-specific PI
tools and every off cell must observe disabled inertness. Proceed only if active gains at least one
objective PASS over the better control, has no provider error/timeout or missing PI observation, and
its median wall time is at most 2x the slower control median. Otherwise classify
`REPAIR_AND_RETEST`, fix the measured PI/oracle/performance cause, and repeat this same pilot before
spending the comprehensive matrix.

After that gate passes, establish `native` and `off` baselines at **full** tiers and repetitions,
since every later number is read against them; then run the **screening** pass — each `ablation(X)` at
its one assigned tier over the fixed tuning subset, depth arms only where a depth-dependent claim
exists. Baseline or screening results produced before the activation contract, or at a different
exact head, are diagnostic history and cannot be mixed into the final comparison.
Fix before the first run and record: the screening subset, the effect threshold, and the tier assigned
to each of the 13 ablatable capabilities (§6; `call_graph` has no arm of its own and is covered by
`semantic`).
Exit: environment frozen; integration paths pass or are classified; a screening table naming which
capabilities proceed to B0b and which are recorded `no screened effect`. **No promotion or demotion
decision may be taken here.**

**B0b — Confirmation and gap report**
Entry: B0a screening table.
Scope: full tier set, full repetitions and the held-out split, for the capabilities that screened
through; measure the competition-derived concerns (weak-local prefix/tool-output efficiency, lifecycle
observability, worktree/subagent capability availability, completion correctness, cross-session
evidence loss, host-native overlap); record how far PI follows the E3 cross-boundary GUI/runtime task,
since that measurement is the entry condition for stages X0 and V5; record the required-verification-set
quality produced by the V0a slice, which is the first evidence bearing on the primary differentiation
hypothesis.
Exit: `docs/evidence/final/baseline-gap-report.md` with every failure classified as OpenCode runtime,
model/provider, PI adapter, PI core, task selection, verification or performance; a ranked gap list;
an explicit skip/keep decision for every later stage; and the §10.2 program-level criteria evaluated
against the result.

**B1 — Blocking host/productization repair** (conditional; was `RV-1`)
Entry: B0 records lifecycle, config, adapter, version-drift or provider friction attributable to
ExtendCodeAgent. Scope: bootstrap/lifecycle simplification, health diagnostics, version compatibility,
reconnect/event coalescing, MCP-only fallback hardening. Exit: repaired paths re-measured against B0.

**B2 — OMO coexistence baseline** (conditional; was `OMO-C0`)
Entry: B0 stable, and OMO installable at the recorded OpenCode version. Restored to the backlog — the
E0 consolidation recorded the OMO plan as "executed only at stage P4" and thereby dropped a stage its
own §9 defines as required **before any claim that OMO + ECA is a recommended stack**. Since
`OpenCode + OMO + ExtendCodeAgent` is an intended production configuration, that claim cannot wait for
a post-release benchmark.
Scope, per `OMO_COEXISTENCE_AND_COMPATIBILITY_PLAN.md` §9: recorded OpenCode / OMO / ECA version tuple;
Team Mode off; startup, tool, session, basic coding and verification compatibility; **both plugin load
orders** where meaningful; classification of every observed conflict against the C0–C6 taxonomy.
Exit: a version tuple marked `compatible`, `degraded` or `incompatible` with reproducible evidence, and
a recorded decision for each conflict following the §11 stop rules — ECA namespacing/idempotence first,
never patching OpenCode or OMO to force compatibility. `UNAVAILABLE` if OMO cannot be installed; the
recommended-stack claim is then withheld rather than assumed.
This is narrower than P4: B2 asks "does the stack work", P4 asks "is the stack better".

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
Entry: V0a, which already defined `SemanticChangeSet`, `VerificationObligation` and required-set
derivation in Phase 0. V0 is the **remainder**, and must extend those objects rather than redefine
them — the whole point of one contract stage is that each object exists once.
Scope: `TestIntent`, `OracleAssessment`, `EvidenceSegment` + dependency closure, `FailureEvidence` +
result-state taxonomy. All are projections over the existing Twin/Graph/Impact/Runtime/Traceability/
Convergence model — no parallel truth store.

**Also in scope: a verification feature policy, so the V-series is ablatable from the inside.** E1 made
the 13 top-level capabilities ablatable, but V2–V5 each add several independent mechanisms underneath a
single `impact` / `test_selection` / `runtime` capability. Without handles, "Environment Matrix helped
but Certificate did nothing" is unanswerable and the E1 problem recurs one level down — a set of
mechanisms that can be built but never demoted.

V0 therefore defines `VerificationFeature` with at least `required_set`, `evidence_reuse`,
`failure_reevaluation`, `oracle_assessment`, `test_intent`, `observability`, `environment_selection`
and `certificate`, each carrying its own depth on the same `D0..D4` axis as E2. These are **not** new
`CapabilityName` members: the top-level inventory stays at 21, its counts stay pinned by
`tests/architecture/test_capability_gating.py`, and the feature policy is nested under the capability
that owns it. Every feature and depth actually used is recorded in the E5 trace, which is what makes
`ablation(evidence_reuse)` and `ablation(certificate)` real arms rather than notional ones.

This is the same rule as invariant 6 applied one level down: a mechanism that cannot be switched off
cannot be shown to be worth its cost, and stays forever by default.

Exit: contracts, shadow computation, architecture tests proving no second store, and a feature-policy
test asserting every `VerificationFeature` is either gated or declared unimplemented — the E1 test
shape, reused.

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
| `OMO-C0` | B2 |
| `OMO-C1` | P3 entry condition |
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
16. handoff documents updated so another agent can reproduce every gate;
17. **OMO coexistence smoke**, if OMO is installable at the recorded OpenCode version: plugin load with
    both extensions present, `pi_*` tool visibility, OMO tool visibility, no tool-ID namespace
    collision, no duplicate execution of the same observation, ExtendCodeAgent sidecar failure isolated
    from OMO, clean shutdown of both. If OMO is not installable, record `UNAVAILABLE` with the reason
    rather than passing the gate.

    This is a **compatibility** check, not a comparison. `OpenCode + OMO + ExtendCodeAgent` is a
    realistic user configuration, and a namespace collision or duplicated execution there is a defect
    that ships to users regardless of how the P4 benchmark turns out. Deferring all OMO contact to P4 —
    after the release — would mean discovering it in production. The full A/B, Team Mode, hook order,
    context overhead, model-routing conflict and worktree behavior stay at P4 under the C0–C6 conflict
    taxonomy.

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
  b0a-activation-plan-v1.json  # exact-head PI use/readiness gate before comprehensive B0a runs
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
| **Execution capacity** | single maintainer; B0 at full matrix is ~320 h of continuous runs (§7.5) | screening/confirmation split; `no screened effect` is a valid recorded outcome; §10.2 permits stopping |
| **Unbudgeted human review** | C1 expected plans, V4 injected faults, E4 Layer A labels all need manual work that is not sized | each stage must state its review volume in its own entry before starting; a stage whose review cost is unknown does not start |
| **Differentiator is unbuilt** | 13 capabilities of conceded-parity Project Truth exist; the V-series is 0 lines | V0a pulls the minimum contract slice into Phase 0 so B0b returns a first number on the hypothesis |
| **KasaneCore reuse is conceptual, not code** | audit records 80–90% algorithmic reuse but 25–40% direct source reuse, and `src/` contains no KasaneCore-derived module | estimate remaining work from scratch-implementation rates, never from "already solved in KasaneCore" |

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

Phase 0, stages E0, E1, E2, V0a, E3, E4 and E5 are complete. Next is B0a.

```bash
cd /home/souten/ExtendCodeAgent
git switch main
git pull --ff-only origin main
git status --short
tools/local/all-fast
tools/local/test-integration
tools/local/build
git switch -c agent/b0a-baseline-screening
```

B0 entry is now open. Start with per-repository Existing Project Bootstrap conformance and the B0a
environment/integration freeze; do not collapse screening and confirmation into one unschedulable
pass or make promotion/demotion decisions from screening alone.
