# ExtendCodeAgent Productization and Model Evaluation Plan

Status: proposed execution baseline after PR-I
Date: 2026-08-14

## 1. Purpose

The A-I implementation sequence is substantially complete. The next phase is not a general feature-expansion phase. It is a productization and evidence phase whose goal is to prove that ExtendCodeAgent improves real OpenCode work across weak local models, practical local models, the OpenCode host/default model path, and a frontier model path while preserving correctness, privacy, bounded overhead, and graceful fallback.

This phase MUST optimize for real usability and measurable agent performance. Low-priority features MUST remain frozen unless evaluation demonstrates a concrete failure that they are the smallest reasonable way to fix.

The product definition for this phase is:

> ExtendCodeAgent is a bounded Project Intelligence layer that gives OpenCode the minimum high-value project facts needed to complete coding tasks with fewer reads/tool calls/tokens, better impact and verification decisions, and no loss of correctness.

The phase is successful only if this claim is supported by repeated real-host/model evidence.

## 2. Zero-based priorities

### P0 — required for a usable baseline

1. Release validation across real repositories, modes, and model tiers.
2. Frontier model path repair and successful live evaluation.
3. Repeatable weak-local and practical-local model evaluation.
4. OpenCode integration hardening: startup, reconnect, sidecar lifecycle, MCP fallback, configuration, diagnostics, and feature disable/fallback behavior.
5. Context Intelligence optimization by task and model capability.
6. Verification Intelligence quality: test selection, stale evidence, runtime evidence, and completion correctness.
7. Task-aware capability selection sufficient to avoid enabling expensive intelligence indiscriminately.
8. Evidence/Confidence calibration for the relations that directly affect impact, test selection, and context.
9. Performance/refresh policy tuning using measured repository behavior.

### P1 — implement only if P0 evaluation demonstrates need

1. Runtime bridge across frontend/browser/API/backend boundaries.
2. Framework-specific analyzers for React/Vue/etc. behind a generic projection interface.
3. On-demand DFG/Taint analysis for security/data-origin/debug tasks.
4. On-demand CFG for complex control-flow/debug tasks.
5. Additional state/event extraction for workflow-heavy repositories.

### Frozen unless evidence changes the priority

- repository-wide always-on CFG;
- repository-wide always-on DFG;
- persistent full UI/render graphs;
- universal Blueprint generation;
- universal Strategy generation;
- automatic Research for normal coding tasks;
- deeper graph types whose measured recall/quality benefit is not established;
- GitHub CI merely to duplicate local validation.

## 3. Current evidence and what it does not prove

Existing evidence already demonstrates important value:

- Project Graph/Twin/Impact is functional and query latency is low after indexing.
- OpenCode 1.18.18 plugin/MCP/sidecar integration has real-host smoke evidence.
- weak model context can be reduced from a large standard package to a much smaller bounded package.
- local-medium model evaluation succeeded on the existing six controlled scenarios.
- the recorded weak local model run improved materially when bounded Project Intelligence facts were active.
- host/default active evaluation completed the six scenarios with dramatically fewer tool calls/tokens and lower wall time than the recorded native run.
- JS/TS/TSX analysis works on a real ControlDeck repository and the refresh policy already switches to full refresh when incremental closure is too broad.

These results DO NOT yet prove:

- stable quality across repeated weak-local runs;
- frontier quality, because the configured frontier path was unavailable;
- production readiness across multiple repositories and task classes;
- that `active` should be the default for every model/task;
- calibrated confidence values;
- high recall across browser/API/runtime boundaries;
- that additional deep graphs are worth their storage/latency/complexity cost.

Do not overstate previous evidence.

## 4. Productization principles

### 4.1 Evaluation drives implementation

For each failure:

1. reproduce it;
2. classify whether the failure is model, context, graph, runtime evidence, adapter, configuration, or orchestration related;
3. attempt the smallest existing capability/configuration fix first;
4. extend/consolidate existing code before creating a new subsystem;
5. add a new analyzer/capability only when evidence shows the current system cannot solve the class of failure cleanly.

Every substantive productization change MUST link to a measured failure or usability problem.

### 4.2 Deterministic evidence remains primary

LLM output does not become verified project truth. Graph, source revision, runtime observation, test/build evidence, and explicit verification remain authoritative according to current contracts.

### 4.3 The default path must remain bounded

An ordinary coding task must not trigger every available intelligence capability. Expensive or deep analysis is opt-in or automatically selected only when justified by task class, uncertainty, risk, or a failed cheaper analysis.

### 4.4 Native fallback is a feature

Any ExtendCodeAgent failure must preserve a clear path to native OpenCode behavior. `off` MUST remain genuinely inert. `shadow` MUST not change agent behavior. `advisory` MUST not silently become active. Active automation MUST fail closed to advisory/native when its evidence is unavailable or stale.

## 5. Required task-aware controller

Do not build a large autonomous planner. Implement the smallest controller needed to select existing capabilities and context profiles.

### Inputs

- task text/type;
- repository language/framework indicators;
- change scope if known;
- Project Model readiness/freshness;
- available runtime/test evidence;
- model capability profile;
- privacy constraints;
- uncertainty/risk signals;
- previous failed attempts in the current task.

### Output

A bounded `IntelligencePlan` describing:

- capabilities to use;
- context profile/budget;
- graph/query depth limits;
- whether runtime evidence is needed;
- whether Strategy/Convergence is justified;
- whether escalation is allowed;
- reasons for every non-default capability.

### Minimum task classes

- locate/explain;
- rename/refactor;
- bug fix;
- test/verification;
- UI/browser bug;
- API/backend change;
- security/data-flow investigation;
- architecture/migration;
- external research.

### Expected selections

- locate/explain: semantic/context only;
- rename/refactor: semantic + impact + tests;
- bug fix: semantic + impact + verification + runtime evidence if present;
- UI/browser bug: JS/TS + framework/runtime bridge only when required;
- security: impact + on-demand DFG/Taint if evidence shows need;
- architecture: impact + Strategy + Convergence;
- research: Research port explicitly.

Controller logic MUST be deterministic or rule-based initially. Do not add an LLM classifier unless deterministic classification proves inadequate in evaluation.

## 6. Model evaluation matrix

### 6.1 Model tiers

Evaluate logical profiles, not hard-coded product names. Record exact model/provider/version in evidence.

Required tiers:

1. `local-low`: a deliberately weak/small local model.
2. `local-practical`: the practical local coding/reasoning model available on the machine.
3. `host-default`: current OpenCode host/default path.
4. `frontier`: at least one functioning current frontier model path.

Existing examples may be reused when available, but names MUST stay configuration data.

### 6.2 Modes

At minimum compare:

- native OpenCode with extension absent/disabled;
- `off`;
- `advisory`;
- `active`.

Use `shadow` in adapter/overhead tests where its semantics are relevant.

### 6.3 Repositories

Use at least:

- ExtendCodeAgent or another small/medium Python repository;
- KasaneCore or another realistically large Python-heavy repository;
- ControlDeck or another real JS/TS/TSX repository;
- one mixed project if available.

Record exact commit SHA for every run.

### 6.4 Task set

Create a versioned benchmark task set. Do not only ask synthetic graph questions. Include real coding-agent tasks with objective verification.

Required classes:

1. implementation-location discovery;
2. impact analysis before change;
3. test selection after bounded change;
4. multi-file defect diagnosis;
5. stale/obsolete test risk detection;
6. small refactor;
7. API change with consumer impact;
8. UI/browser-related diagnosis;
9. architecture/strategy decision;
10. verification/completion decision.

Add security/data-flow and research scenarios only if those capabilities are under evaluation.

### 6.5 Repetition

Weak/local model results MUST be repeated. A single lucky run is not acceptance evidence.

Recommended minimum:

- local-low: 5 runs per critical scenario/mode;
- local-practical: 3 runs;
- host-default: 3 runs for representative scenarios;
- frontier: 3 runs after connectivity is fixed.

If cost is material for frontier runs, use a representative stratified subset but do not claim full-matrix coverage.

### 6.6 Metrics

Record:

- task success;
- objective test/build/result correctness;
- unsupported/fabricated claims;
- unnecessary file reads;
- tool calls;
- newly supplied input tokens;
- cached input tokens when available;
- output/reasoning tokens when available;
- wall time;
- retries/timeouts/provider failures;
- frontier/local escalation count;
- context items/tokens;
- impact recall/precision on curated cases;
- selected-test recall/precision;
- unnecessary edits;
- stale-context incidents;
- verification/completion correctness;
- peak memory;
- DB+WAL size;
- cold index time;
- refresh time;
- OpenCode startup overhead;
- sidecar/MCP reconnect behavior.

Do not optimize a single metric at the cost of correctness.

## 7. Frontier model repair gate

Frontier is currently a release blocker because prior attempts returned provider/API errors.

Before changing core logic:

1. reproduce using current OpenCode and current provider configuration;
2. confirm authentication and model availability independently of ExtendCodeAgent;
3. run a minimal OpenCode-native prompt against that model;
4. record exact provider/model/error category without secrets;
5. compare native provider payload requirements with the existing host adapter;
6. fix adapter/config only if the failure is ExtendCodeAgent-specific;
7. retain fail-closed behavior for provider errors;
8. run the frontier evaluation subset only after a minimal native and adapter smoke both pass.

A provider credential/service outage is `UNAVAILABLE`, not a code failure and not a pass.

## 8. Local LLM optimization

### 8.1 Preserve bounded contexts

The main advantage for weak models is the transformation of a repository problem into a small structured evidence problem. Continue optimizing this before attempting larger models or more reasoning.

For each local model profile measure:

- context tokens vs success;
- item count vs success;
- inclusion precision: how many supplied facts were actually useful;
- missing-fact failures;
- model/tool call count;
- latency.

### 8.2 Adaptive context budget

Context budget should depend on:

- model context/capability;
- task class;
- impact size;
- confidence/uncertainty;
- available evidence;
- previous failure.

Prefer progressive expansion:

1. minimal relevant symbols/path/tests;
2. add direct surrounding context;
3. add transitive impact/evidence;
4. escalate model only if needed and allowed.

Do not start by sending the maximum context.

### 8.3 Reasoning/output control

Keep provider-specific output/reasoning controls inside adapters. Maintain explicit timeouts and token/output bounds. Record any model whose "thinking" behavior consumes the complete output budget or materially hurts latency.

## 9. OpenCode-specific optimization

### 9.1 Adapter compatibility

Re-verify the current stable OpenCode version at release validation. Do not assume 1.18.18 behavior indefinitely.

Keep all OpenCode API/event shapes in the TypeScript adapter. Core contracts must not change merely because the host API changes.

### 9.2 Startup and lifecycle

Measure and optimize:

- plugin import/load time;
- sidecar startup/discovery;
- connection/auth handshake;
- MCP setup;
- first useful query latency;
- shutdown/restart cleanup;
- stale process/port recovery.

The user should not need manual lifecycle management for normal use. If current behavior requires multiple manual commands, record it as a productization defect and simplify the existing bootstrap path.

### 9.3 Event pressure

Validate editor/tool/watch events under rapid multi-file edits. Keep coalescing and feedback-loop protection. Measure revision churn, redundant refreshes, and time-to-stable revision.

### 9.4 Tool exposure

OpenCode should see only useful, bounded tools. Avoid dozens of overlapping tools. Prefer a small stable surface plus an optional diagnostic/deep-analysis entry point.

### 9.5 Native-tool competition

Measure whether Project Intelligence reduces unnecessary `grep/read/LSP/bash` use without preventing necessary source inspection. Active mode MUST NOT prohibit the model from checking source when confidence/evidence is insufficient.

## 10. Runtime bridge gate

The current static JS/TS evidence leaves known browser/API/runtime gaps. Do not immediately build a large UI graph.

First create benchmark cases where the current Project Model fails to connect a real user-visible path. Classify the missing boundary:

- browser event -> frontend handler;
- frontend fetch/client -> API route;
- route -> backend handler;
- dependency injection/runtime registration;
- test/browser observation -> project symbols.

Implement only the smallest bridge that improves measured recall without unacceptable FP growth.

Preferred architecture:

- framework/runtime adapters emit generic relations/evidence;
- generic Project Graph/Impact code stays framework-neutral;
- runtime-confirmed facts carry provenance and freshness;
- inferred bridge facts remain lower-confidence;
- feature is independently configurable and may remain advisory/on-demand.

If benchmark recall is already sufficient for product tasks, defer this feature.

## 11. Confidence calibration

Existing numeric confidence values must not be treated as probabilities until calibrated.

For high-value relation classes gather ground truth:

- definition/reference;
- resolved call;
- `may_call`;
- import/dependency;
- test relation;
- impact projection;
- runtime-confirmed relation.

Report at least precision and recall by relation/confidence band.

Use the results to:

- adjust thresholds;
- distinguish ordinal confidence from calibrated probability in APIs/docs;
- tune context/test selection cutoffs;
- identify relation types that should never drive active automation alone.

Do not build complex statistical calibration before enough samples exist. The first goal is empirical threshold validation.

## 12. Refresh/cache policy

Generalize the measured PR-H behavior instead of assuming incremental refresh is always better.

Select among:

- no refresh/cache hit;
- targeted file refresh;
- dependency-closure refresh;
- full refresh;
- deferred/on-demand deep analysis.

Inputs may include:

- repository size;
- number/share of changed modules;
- dependency closure coverage;
- language analyzer cost history;
- previous full/incremental timings;
- current system load.

Start with explainable heuristics. Store small local timing history if useful. Do not add an ML predictor.

## 13. Verification/product acceptance

A task is not considered improved merely because the LLM answer is shorter/faster.

For coding tasks use objective verification whenever possible:

- relevant tests;
- full-suite fallback where required;
- lint/typecheck/build;
- API/UI smoke;
- expected diff/behavior assertions;
- no unintended modifications.

For analysis tasks use curated ground truth or independent source review.

For completion decisions explicitly test stale, missing, conflicting, and external-only evidence to ensure they cannot produce false completion.

## 14. User-facing configuration and usability

Before declaring production-capable, verify that a user can:

- install/bootstrap with documented commands;
- enable/disable the plugin;
- choose off/shadow/advisory/active globally and by capability;
- configure local/OpenCode/frontier model roles without modifying source;
- enforce remote-code/privacy policy;
- inspect `pi.status`/health diagnostics;
- identify stale/degraded/unavailable Project Intelligence;
- recover from sidecar/provider failure;
- return to native OpenCode behavior cleanly.

Prefer extending the existing central config over adding feature-local flags.

## 15. Required execution PR sequence

This phase should use small evidence-driven PRs rather than another broad A-I expansion.

### RV-0 — Baseline Release Validation and gap report

No speculative feature work.

- re-run local/build/integration/OpenCode gates on current main;
- repair frontier connectivity/config if possible;
- execute representative native/off/advisory/active matrix;
- repeat local-low/local-practical runs;
- produce `docs/evidence/final/baseline-gap-report.md` and compact machine-readable results;
- rank observed failures by frequency, severity, and expected user value.

Exit: measured gap list and a decision on which following PRs are actually required.

### RV-1 — OpenCode productization/hardening

Only if RV-0 reveals lifecycle/config/adapter friction or version drift.

Possible scope:

- bootstrap/lifecycle simplification;
- health/diagnostic improvements;
- version compatibility adapter fixes;
- reconnect/event-coalescing fixes;
- MCP-only fallback hardening.

### RV-2 — Task-aware capability/context controller

Required unless RV-0 proves manual/static profiles are already sufficient.

- deterministic task classification;
- bounded IntelligencePlan;
- progressive context expansion;
- explicit reasons/telemetry;
- no LLM classifier by default.

### RV-3 — Verification/confidence quality

Required for active automation confidence.

- ground-truth expansion;
- precision/recall and threshold report;
- test-selection/completion correctness improvements;
- confidence semantics cleanup where needed.

### RV-4 — Runtime bridge

Conditional on demonstrated frontend/runtime recall gap that affects benchmark task success.

Do not implement if it does not materially improve task/impact/test recall.

### RV-5 — On-demand deep analysis

Conditional only.

Prioritize DFG/Taint before CFG when the measured task requires data origin/security reasoning. Implement bounded symbol/neighborhood analysis and cache only when useful. Do not persist project-wide deep graphs by default.

### RV-FINAL — Final release validation

Repeat the relevant matrix after fixes. No new feature scope.

Only then consider `PRODUCTION-CAPABLE BASELINE COMPLETE`.

## 16. Stop criteria for low-value work

Stop or defer a proposed feature when any of the following is true:

- it does not improve a measured real task;
- it duplicates information already available from semantic/runtime evidence;
- it increases default startup/refresh latency disproportionately;
- it substantially increases graph/database size without query benefit;
- its precision is too low for active use and advisory value is marginal;
- only a frontier model benefits while local/host paths regress;
- it requires OpenCode core patches;
- it creates a second implementation of an existing core capability;
- it mainly increases architectural elegance rather than user-visible capability.

## 17. Release gates

The production-capable baseline requires all of the following, or an explicit scoped exception documented as non-blocking:

1. clean local lint/typecheck/unit/integration/build;
2. current stable OpenCode plugin load and core tool smoke;
3. MCP connection/reconnect/fallback smoke;
4. off mode inertness;
5. advisory/active behavior consistent with capability policy;
6. repeated local-low evaluation recorded;
7. repeated practical-local evaluation recorded;
8. host-default comparison recorded;
9. functioning frontier model path and evaluation, unless explicitly re-scoped by project decision;
10. no privacy-policy leak in deny/metadata/selected-context tests;
11. context/token budget evidence;
12. impact/test quality evidence;
13. completion/stale-evidence correctness;
14. repository-scale startup/index/refresh/memory/DB evidence;
15. installation/configuration/recovery instructions verified on a clean local setup or equivalent isolated environment;
16. known limitations documented honestly;
17. handoff documents updated so another agent can reproduce every critical gate.

## 18. GitHub CI policy

Keep GitHub CI minimal/absent. All normal validation must remain reproducible locally. Add CI only for a demonstrably GitHub-specific or unavailable-platform gate and record the rationale in `docs/handoff/DECISIONS.md` before adding it.

Do not put real model evaluation, provider secrets, or costly frontier runs in mandatory GitHub CI.

## 19. Evidence layout

Use compact committed evidence:

```text
docs/evidence/final/
  environment.md
  baseline-gap-report.md
  model-matrix.json
  task-results.json
  opencode-integration.json
  graph-quality.json
  performance.json
  release-gates.md
```

Large raw transcripts/logs remain local. Record enough command/model/config/revision metadata to reproduce results without committing secrets.

## 20. Final decision rule

The goal is not feature parity with Atlas and not the maximum possible graph depth.

The goal is to make OpenCode measurably better on real coding work. The default release should contain only capabilities that either:

- improve correctness/verification;
- reduce model/tool/token/time cost without quality loss;
- enable weak local models to solve tasks they otherwise fail;
- provide essential impact/runtime/project evidence;
- make the integration reliable and configurable enough for daily use.

Everything else stays optional, on-demand, or deferred until evidence justifies investment.
