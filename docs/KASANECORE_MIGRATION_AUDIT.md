# KasaneCore -> ExtendCodeAgent / OpenCode Migration Audit

Status: architecture and migration audit
Date: 2026-08-13
Source repository: `souten-yd/KasaneCore` `main`
Target repository: `souten-yd/ExtendCodeAgent`
Target host: OpenCode

## 1. Executive assessment

KasaneCore contains a substantial, tested implementation of Project Intelligence. Its recovery status records `PIR-0..PIR-15 ACCEPTANCE COMPLETE`, including production composition, source/Twin refresh, semantic and behavioral graphs, verification ingest, context/impact/test selection, Blueprint, Convergence, planning/generation/verification integration, Greenfield E2E, scale/cutover, benchmark and retirement evidence.

However, **KasaneCore must not be copied wholesale into ExtendCodeAgent**.

The codebase has two simultaneous characteristics:

1. the Project Intelligence architecture intentionally established useful facade/module boundaries and many components are technically reusable;
2. implementation contracts still encode Atlas/KasaneCore assumptions: Python/Pydantic models, Atlas project/phase terminology, PlanPool IDs, Atlas verification and canonical event semantics, `ca_data`, internal source adapters, Nexus, HybridMemoryStore, Skill registry, Safe Apply and Atlas rollout models.

The correct migration is therefore:

```text
KasaneCore implementation
      |
      +-- extract stable algorithms/data concepts
      +-- remove Atlas authority semantics
      +-- replace cross-module DTO dependencies
      +-- define host-neutral ports
      +-- retain provenance/revision/evidence rules
      v
ExtendCodeAgent Domain Core
      |
      +-- OpenCode stable adapter
      +-- OpenCode V2 adapter
      +-- MCP facade
      +-- CLI / optional HTTP
```

Overall reuse recommendation:

- **Conceptual/algorithmic reuse: high (80-90%)** for graph revisioning, impact/path logic, Blueprint lifecycle, Convergence state/policy concepts, test-selection concepts, truthful evidence principles.
- **Direct source reuse without modification: low-medium (25-40%)** because domain contracts and composition roots are still coupled to KasaneCore conventions.
- **Adapter/integration reuse: low (10-25%)** for Atlas-specific planner/generator/verification/Nexus/API/UI wiring.
- **Tests as behavioral specification: very high value (80%+)**; migrate/adapt tests before or alongside algorithms to prevent semantic regression.

## 2. Evidence reviewed

Primary code/design surfaces reviewed in the audit include:

- `docs/atlas_project_intelligence_architecture.md`
- `docs/atlas_project_intelligence_master_goal.md`
- `docs/atlas_project_intelligence_current_status.md`
- `docs/atlas_project_intelligence_recovery_current_status.md`
- `docs/atlas_project_intelligence_existing_capability_map.md`
- `agent/project_intelligence/facade.py`
- `agent/project_intelligence/coordinator.py`
- `agent/project_intelligence/production_factory.py`
- `agent/project_intelligence/contracts.py`
- `agent/project_twin/module.py`
- `agent/project_twin/facade.py`
- `agent/project_twin/contracts.py`
- `agent/project_twin/store.py`
- `agent/project_twin/analysis.py`
- `agent/project_twin/static_graph.py`
- `agent/project_twin/behavioral_graph.py`
- `agent/project_twin/context_broker.py`
- `agent/project_twin/context_adapters.py`
- `agent/project_twin/memory_adapter.py`
- `agent/architecture_blueprint/module.py`
- `agent/project_convergence/module.py`
- `agent/deep_planner.py`
- `app/nexus/research_agent.py`

OpenCode surfaces were checked against current stable plugin documentation and the OpenCode V2 plugin/MCP documentation. V2 is currently marked beta and its entrypoints/hooks/shapes may change, which materially affects adapter design.

## 3. Completion level by subsystem

Ratings describe KasaneCore implementation maturity **as a migration source**, not whether it is perfect for every language/framework.

| Subsystem | KasaneCore maturity | Migration readiness | Assessment |
|---|---:|---:|---|
| Revisioned Twin/store lifecycle | 9/10 | 8/10 | Strong foundation. Generalize identity/storage interfaces. |
| Structural graph | 8/10 | 8/10 | Reusable algorithms; broaden language/plugin architecture. |
| Semantic/call graph | 7/10 | 6/10 | Useful implementation but language/framework completeness remains bounded. |
| Behavioral/CFG/state/resource graph | 7/10 | 6/10 | Significant code exists; validate precision on non-Kasane repos. |
| Path/impact analysis | 9/10 | 9/10 | One of the best direct migration candidates after DTO cleanup. |
| Incremental refresh/invalidation | 8/10 | 7/10 | Good basis; OpenCode events require queue/coalescing/debounce redesign. |
| Context broker/packaging | 8/10 | 6/10 | Concepts strong; Atlas phase/PlanPool vocabulary must be removed. |
| Runtime normalization/reconciliation | 8/10 | 6/10 | Keep evidence model; replace Atlas runners with RuntimeObservation ports. |
| Related-test/test selection | 8/10 | 8/10 | High-value reuse; extend into first-class test health/staleness. |
| Test obsolescence | 4/10 | 5/10 | Building blocks exist, but dedicated health engine should be new. |
| Architecture Blueprint | 8/10 | 7/10 | Lifecycle and immutable revisions useful; contract model needs host-neutral redesign. |
| Convergence | 8/10 | 7/10 | Evaluator/policy concepts useful; loader interfaces and evidence contracts should be redesigned. |
| Deep/strategy planning | 5/10 | 4/10 | Existing DeepPlanner is heavily Atlas/Nexus/LLM-schema coupled and uses heuristic fallback defaults. Rebuild as Strategy Core. |
| Deep Research/Nexus | 8/10 as Kasane feature | 4/10 direct | Rich pipeline but deeply tied to `app.nexus` DB/jobs/search/downloader/report stack. Extract research domain concepts, not module wholesale. |
| Memory integration | 7/10 | 6/10 | Verified-promotion policy is excellent; HybridMemoryStore binding becomes a generic MemoryPort. |
| Skill integration | 7/10 | 5/10 | Keep safety/precedence concepts, integrate with OpenCode Skills through adapter. |
| Atlas planner/generator/verification bridges | 9/10 Atlas-specific | 2/10 | Do not migrate directly; replace with OpenCode adapters. |
| Atlas API/UI/rollout wiring | 9/10 Atlas-specific | 1/10 | Host-specific and should not enter core. |

## 4. The most reusable component: path and impact analysis

`agent/project_twin/analysis.py` is a strong direct candidate because the essential algorithm operates against a graph-store abstraction and returns explainable paths/impacts.

Useful behavior to preserve:

- directed path tracing with depth/path bounds;
- edge type, status and minimum-confidence filters;
- reverse-dependency impact traversal;
- forward expansion for implementation relations such as route -> handler;
- alias bridging for unresolved/name-only call relations;
- weakest-link/path confidence tracking;
- direct vs transitive impacts;
- affected requirements;
- side effects;
- recommended tests;
- historical risk/incidents;
- uncertainty;
- explanation paths.

### Required redesign

Do not carry KasaneCore `TwinNode`, `ImpactRequest`, `ImpactResult` Pydantic contracts directly into the host-neutral core. Introduce minimal internal protocols:

```text
GraphSnapshotPort
  get_revision(project)
  nodes(filter)
  outgoing(node)
  incoming(node)

ImpactQuery
  changed_refs
  max_depth
  confidence_policy
  include_history

ImpactReport
  revision
  direct
  transitive
  resources
  tests
  requirements
  uncertainty
  explanation_paths
```

The current `py://` / `pyname://` compatibility behavior should become an analyzer-specific alias resolver rather than hard-coded generic impact-engine knowledge. The generic impact engine should ask a `CanonicalReferenceResolver` for aliases/equivalents.

## 5. Digital Twin: reuse the lifecycle, redesign identity and composition

`DigitalTwinModuleImpl` is already a meaningful concrete implementation. It combines source snapshots, static/behavioral analyzers, durable SQLite graph revisions, invalidation, runtime ingest and context/query behavior. This is materially beyond a scaffold.

### Strong parts to preserve

- immutable revision model;
- optimistic expected revision handling;
- source revision + working-tree hash;
- parser/analyzer version tracking;
- full rebuild versus changed-path refresh;
- invalidation of old nodes/edges not regenerated in the changed scope;
- degraded result instead of fabricated success on store/revision errors;
- project/workspace isolation;
- source snapshot -> analyzer -> delta -> store flow.

### Coupling that must be removed

The current module imports `ProjectIdentity`, context/evidence DTOs and diagnostics from `agent.project_intelligence.contracts`. This means the lower-level Twin implementation still depends on the higher Project Intelligence DTO package. The target architecture should invert this.

New dependency direction:

```text
core-contracts
  ^
  |
graph-core <- twin-core <- context/impact/test modules
  ^
  |
project-intelligence orchestrator
```

`ProjectIdentity` should become a generic `ProjectRef`:

```text
ProjectRef
  project_id
  workspace_id
  root_uri
  repository_id?
  branch?
  source_revision?
  worktree_fingerprint?
```

OpenCode-specific `directory`, `worktree`, session IDs and project objects remain only in the adapter.

### Incremental event processing redesign

KasaneCore refresh calls are sufficiently synchronous for Atlas composition, but OpenCode plugin hooks should remain low-latency. Use:

```text
file.edited / watcher / LSP / tool result
          |
          v
OpenCodeAdapter event normalization
          |
          v
bounded async queue
  - debounce
  - coalesce same path
  - collapse superseded revisions
  - priority for user-requested queries
          |
          v
Twin refresh worker
```

A query may choose `freshness=required|best_effort|stale_ok`. `required` waits for the revision barrier; `best_effort` returns current revision with explicit stale diagnostics.

## 6. Project Intelligence coordinator: keep orchestration idea, replace Atlas DTO surface

KasaneCore `ProjectIntelligenceCoordinator` correctly depends on public Twin/Blueprint/Convergence facades rather than their stores. This is a good boundary.

But its public planning/generation DTOs contain Atlas concepts such as `plan_pool_id`, `plan_item_id`, Atlas rollout phases and package fields tailored to Atlas Patch Proposal/Planner consumers.

### Target replacement

```text
ProjectIntelligenceService
  prepare_project(ProjectRequest) -> ProjectState
  build_context(ContextRequest) -> ContextPackage
  record_change(ChangeObservation) -> ProjectionResult
  record_verification(VerificationObservation) -> ProjectionResult
  assess_progress(ProgressRequest) -> ProgressReport
```

`ContextRequest.phase` should use host-neutral intents such as:

- explore
- plan
- implement
- verify
- repair
- review
- research

The OpenCode adapter maps its agent/session state into those intents. There should be no PlanPool identifier in core contracts; an optional generic `execution_item_ref` is sufficient.

## 7. Production factory: do not port directly

`production_factory.py` is useful evidence that concrete Twin/Blueprint/Convergence components can be composed and preflighted, but it is not a reusable composition root for ExtendCodeAgent.

Kasane-specific assumptions include:

- `ca_data_dir`;
- fixed SQLite filenames;
- Atlas rollout environment model;
- disabled facades for legacy compatibility;
- event projection composition chosen specifically for Atlas.

Replace it with a target composition layer driven by configuration:

```text
createProjectIntelligence(config, ports)
  storage
  filesystem
  git
  analyzers
  runtime
  research
  memory
  clock
  telemetry
```

The OpenCode plugin can instantiate this service, but core tests must instantiate it with in-memory/fake ports without OpenCode.

## 8. Blueprint: good lifecycle, incorrect dependency layering for the target

`ArchitectureBlueprintModuleImpl` already enforces valuable semantics:

- immutable revision content;
- revise creates a child revision;
- activation moves an active pointer rather than mutating content;
- reviewed/approved/active/superseded lifecycle;
- validation before activation;
- planned target state never claims actual implementation status.

These should be retained.

### Required changes

The module imports diagnostics/errors from `agent.project_intelligence.contracts`. Move Blueprint-specific errors into `blueprint-core` or shared `core-contracts`.

`BlueprintPlannerAdapter` should become an optional generator port, not required Blueprint-domain behavior:

```text
BlueprintRepository
BlueprintValidator
BlueprintGeneratorPort (optional LLM/host adapter)
BlueprintService
```

A deterministic Blueprint model/lifecycle should be usable without an LLM.

Blueprint source links should reference generic `TwinRevisionRef` and `RequirementRef`, not Atlas requirement store internals.

## 9. Convergence: preserve evaluator/policy, replace injected loader functions with ports

The concrete `ConvergenceModuleImpl` is already reasonably isolated: it receives Blueprint, Actual snapshot and verification loaders and persists reports/decisions.

The key improvement is to make this isolation explicit in contracts instead of raw callable signatures:

```text
TargetSnapshotPort
ActualSnapshotPort
VerificationEvidencePort
ConvergenceRepository
```

Preserve the important truthful behavior: missing Blueprint/Actual data returns unavailable diagnostics rather than completion.

Do not import Blueprint implementation models directly into convergence internals. Define a small immutable `TargetSnapshot` projection consumed by Convergence. This avoids Blueprint schema changes forcing convergence rewrites.

## 10. Strategy Planner: redesign rather than port

KasaneCore `DeepPlanner` demonstrates the intended user experience — three architecture alternatives, selected option, benefits/drawbacks, risk, complexity, target files, reflection, implementation phases and verification strategy.

But direct portability is low because it imports:

- Atlas LLM output models/schemas;
- Atlas structured-output generator;
- Atlas requirement schema;
- Nexus context dictionary;
- repository context as pre-rendered text.

It also supplies broad fallback choices such as A/B/C with generic labels and defaults to option B when the LLM payload is invalid. Those fallbacks are useful for UX continuity but are not sufficient for an evidence-based Strategy Planner.

### New Strategy Core

```text
StrategyRequest
  goal
  constraints
  target_state?
  actual_revision
  candidate_scope?

StrategyAlternative
  id
  changes
  benefits
  drawbacks
  compatibility
  impact_summary
  test_burden
  migration_complexity
  rollback_plan
  performance_effect
  maintainability_effect
  research_evidence
  uncertainty
  score_breakdown

StrategyDecision
  selected
  rejected
  reasons
  unresolved_decisions
  evidence_refs
```

The LLM proposes/explains alternatives through `StrategySynthesisPort`; deterministic services calculate project-derived facts and enforce comparison completeness. No option should be selected merely because it is the fallback ID.

The Strategy Planner should consume structured Project Intelligence queries, not a huge rendered `repository_context` string.

## 11. Nexus / Deep Research: extract concepts, not the application package

`app/nexus/research_agent.py` is a rich implementation with queued/planning/search/source collection/download/extraction/library/evidence/answer/verify/report states, adaptive retrieval targets, quick/standard/deep/exhaustive budgets, source mix goals, replenishment and failure classification.

Direct migration is inappropriate because the research agent imports a large `app.nexus` stack:

- answer builder;
- citation mapper;
- config;
- downloader/artifacts;
- evidence persistence;
- jobs/events/heartbeats;
- news source collectors;
- research gaps;
- source collector and registry;
- planner;
- SQLite DB;
- SearXNG web scout and engine health.

### Extract these reusable domain concepts

- `ResearchRequest` and depth/budget policy;
- research lifecycle states;
- source candidate/evidence/claim records;
- retrieval target calculation;
- deficit/replenishment logic;
- source-quality/type policy;
- claim-level gap analysis;
- explicit insufficient/unavailable state;
- citation/provenance mapping.

### Replace infrastructure with ports

```text
SearchPort
FetchPort
DocumentExtractPort
EvidenceRepository
ResearchJobRepository
SourceQualityPolicy
Clock
LLMSynthesisPort
```

For OpenCode, the first Search/Fetch implementation may call OpenCode-native tools through the adapter where feasible, or run as an independent MCP/local service. Do not make the core depend on OpenCode web tool result shapes.

Research must remain separable from Project Intelligence because external evidence is not code truth. Links into the Project Graph are evidence relations only.

## 12. Memory: preserve verified-promotion policy, remove HybridMemoryStore dependency

`TwinMemoryAdapter` contains an important safety/quality rule: unverified model inference cannot become durable memory without evidence, while verification/runtime/user decisions/canonical projections may be promoted.

This policy should be retained almost verbatim as domain behavior.

Replace optional `HybridMemoryStore` with:

```text
MemoryPort
  recall(query)
  put_verified(item)
  supersede(ref)
```

OpenCode Skills, any future memory plugin, local SQLite memory, or external memory systems can implement the port. The Twin's durable evidence graph remains authoritative for project-specific verified facts.

## 13. Skills and other Atlas-adjacent capabilities

KasaneCore Project Twin also integrates Skill/Nexus/Memory adapters and Atlas canonical events. For ExtendCodeAgent these become separate integration classes:

| KasaneCore concept | Target abstraction | OpenCode mapping |
|---|---|---|
| SkillRegistry/Resolver | `SkillCatalogPort` | OpenCode Skills transform/list/read adapter |
| HybridMemoryStore | `MemoryPort` | optional OpenCode/memory plugin/local implementation |
| Nexus | `ResearchPort` | MCP or OpenCode-aware search/fetch adapter |
| Atlas canonical events | `ProjectEvent` | normalized file/change/verification/requirement events |
| PlanPool | `ExecutionPlanPort` or refs | OpenCode Plan/Todo/session adapter; never core authority |
| Safe Apply | `MutationObservation` | OpenCode edit/write/patch tool outcomes; core does not mutate by itself |
| Verification Gate | `VerificationObservation` | normalized test/build/lint/check outcomes |
| Atlas rollout | `FeatureRolloutPolicy` | plugin config + shadow/advisory/active modes |
| Atlas API/UI | presentation adapter | OpenCode tools/commands/TUI messages or external UI |
| Atlas requirements | `RequirementPort` | conversation/task/spec/document adapters |

## 14. OpenCode integration design

### 14.1 Stable adapter

Use the stable plugin API for currently documented events such as file edits/watcher updates, LSP updates, session changes and tool before/after. The adapter should:

- normalize host events;
- enqueue refresh/evidence work;
- register coarse PI tools;
- show diagnostics/status;
- avoid repository-scale analysis in hook callbacks.

### 14.2 V2 adapter

OpenCode V2 exposes a more powerful beta plugin context including agent/tool/command/skill/reference transforms, session request hooks and tool hooks. This is attractive for richer integration, but **must stay isolated** because the API is explicitly beta.

Maintain:

```text
OpenCodeAdapter interface
  opencode-v1 implementation
  opencode-v2 implementation
```

Run compatibility tests against supported OpenCode versions. If V2 shapes change, only the V2 package should require modification.

### 14.3 MCP facade

MCP is the portability surface for OpenCode and other agents. Expose coarse tools:

- `pi.status`
- `pi.context`
- `pi.symbol`
- `pi.references`
- `pi.path`
- `pi.impact`
- `pi.tests`
- `pi.test_health`
- `pi.runtime_evidence`
- `pi.blueprint`
- `pi.strategy`
- `pi.convergence`
- `pi.research`

The OpenCode plugin may use the same in-process service directly for low latency while MCP exposes it externally. Do not implement different semantics for the two surfaces.

## 15. Contract redesign

A high-priority migration task is removing accidental cross-domain DTO coupling.

### Shared core contracts should contain only

- `ProjectRef`, `WorkspaceRef`;
- `SourceRevision`, `TwinRevisionRef`;
- `CanonicalRef`;
- `Provenance`, `Confidence`, `Diagnostic`;
- `EvidenceRef` and evidence status;
- common paging/bounds/freshness policies.

### Domain contracts live with the domain

- Graph node/edge/query -> graph-core;
- Twin lifecycle -> twin-core;
- Blueprint revision -> blueprint-core;
- Convergence report -> convergence-core;
- Test health -> test-intelligence;
- Strategy -> strategy-core;
- Research -> research-core.

No lower-level graph/twin package may import a Project Intelligence orchestration DTO package.

## 16. Storage redesign

KasaneCore's SQLite approach is a good initial choice and should be retained as the default local backend, but persistence must be abstracted.

Requirements:

- schema/version migration independent of OpenCode version;
- atomic revision commit;
- project/workspace isolation;
- bounded indexes for reverse traversal;
- analyzer version recorded per revision/fact;
- export/import with integrity checks;
- retention/compaction policies;
- optional future server/remote implementation;
- no `ca_data` assumption.

Suggested default root: XDG-compatible cache/data directory with project-scoped database selection configurable by the OpenCode adapter.

## 17. Analyzer redesign

KasaneCore already proves the graph can combine structural and behavioral analyzers. Extend this into explicit capability adapters:

```text
AnalyzerDescriptor
  id
  version
  languages
  frameworks
  capabilities

AnalyzerRequest
  project
  source revision
  changed paths
  requested capabilities

AnalyzerResult
  nodes
  edges
  diagnostics
  provenance
  invalidation hints
```

Start with Python + JS/TS and framework adapters. LSP is an input provider, not the entire semantic graph implementation. A language analyzer may combine AST, LSP and framework-specific parsing.

Do not hardcode Python alias rules into generic graph traversal.

## 18. Runtime/Test redesign

Normalize tool outputs into generic observations:

```text
VerificationObservation
  kind: test|lint|build|typecheck|smoke|benchmark|runtime
  command/tool
  started/finished
  exit status
  affected/observed refs
  source revision
  evidence artifacts
  pass/fail/unavailable
```

OpenCode tool hooks must capture failures as well as successes where the host API allows. Because plugin event behavior can differ by OpenCode generation/version, write adapter-specific conformance tests for failed tool calls.

Test Intelligence then derives health from current code/graph revisions plus runtime evidence, rather than treating any historical green run as current proof.

## 19. Dedicated Test Obsolescence Engine (new work)

KasaneCore has related-test discovery, impact-based test recommendation, runtime/evidence integration and revision identity, but not a sufficiently independent test-health engine for the OpenCode target.

Implement a new engine with signals:

- impacted production refs changed after last meaningful test evidence;
- changed control/data/state path not covered by prior observation;
- test only reaches obsolete symbol/route;
- assertions no longer validate changed behavior;
- target file/symbol removed or renamed without test update;
- runtime coverage/trace drops materially;
- repeated implementation churn with static test body;
- duplicate/redundant tests covering identical evidence;
- test disabled/skipped/quarantined;
- flaky history separated from stale semantics.

Never auto-delete an obsolete/redundant test solely from heuristic inference. Return recommendations and evidence.

## 20. Migration classification by source area

### REUSE / ADAPT HEAVILY

- graph node/edge/revision concepts;
- SQLite revision/store patterns;
- source snapshot and analyzer versioning;
- path/impact algorithms;
- confidence/provenance/status concepts;
- Blueprint immutable revision/lifecycle;
- Convergence element states and bounded decisions;
- memory verified-promotion rule;
- truthful `unavailable != passed` rule;
- incremental invalidation principles;
- benchmark/rollout concepts.

### REIMPLEMENT BEHIND NEW CONTRACTS

- Project Intelligence coordinator;
- context packages;
- analyzer registry/interfaces;
- runtime observation adapters;
- test intelligence/obsolescence;
- strategy planner;
- Research core;
- requirement/evidence trace;
- OpenCode integration.

### DO NOT PORT INTO CORE

- Atlas API routers/UI;
- Atlas PlanPool storage/models;
- Atlas Patch Proposal/Safe Apply orchestration;
- Atlas-specific approval/retry/handoff services;
- `ca_data` composition root;
- Nexus DB/job/search infrastructure as-is;
- Atlas LLM output/schema utilities;
- Atlas rollout compatibility code whose sole purpose is legacy Atlas parity.

## 21. Detailed migration sequence

### Step 1 — behavioral specification capture

Before copying implementation, select KasaneCore tests for graph store, source refresh, semantic/behavioral graph, impact/path, runtime reconciliation, Blueprint and Convergence. Translate them into target behavior statements and fixtures. Preserve edge cases and truthful failure semantics.

### Step 2 — create host-neutral contracts

Implement core references, revisions, provenance, evidence, diagnostics and ports. Add architecture-boundary tests forbidding OpenCode imports outside adapters.

### Step 3 — port graph store and source snapshot

Port SQLite revision/store behavior and source snapshot logic behind filesystem/git ports. Verify Windows/Linux path normalization and worktree identities.

### Step 4 — port analyzers

Port structural/Python semantic behavior first. Separate language-specific canonical-ref/alias code. Add JS/TS next. Keep behavioral/deep analyses capability-gated.

### Step 5 — port impact/path

Move GraphAnalysis algorithms to generic graph snapshots. Benchmark against real repos before calling it production-ready.

### Step 6 — build OpenCode event adapter

Normalize file/watcher/LSP/tool/session events and introduce coalesced async refresh. Do not inject heavy synchronous work into hooks.

### Step 7 — context/test tools

Add `pi.context`, `pi.impact`, `pi.tests` and test-selection evidence. Compare against baseline OpenCode exploration for latency, tool calls, token use and missed dependencies.

### Step 8 — runtime and test health

Normalize verification runs, reconcile graph evidence and implement dedicated stale/obsolete/missing test detection.

### Step 9 — Blueprint and Convergence

Port lifecycle/evaluator semantics onto new target/actual snapshot contracts. Prove no planned element can be treated as actual/verified without evidence.

### Step 10 — Strategy Planner

Build new Strategy Core. Use ProjectGraph/Twin/Impact/Test/Runtime/Research facts to score alternatives. Integrate with OpenCode Plan through a planning envelope, not by replacing Plan Agent.

### Step 11 — Research

Extract Nexus research-domain algorithms behind ports; implement an initial OpenCode/MCP search/fetch adapter. Keep external evidence separate from code truth.

### Step 12 — shadow/advisory rollout

Run PI tools in shadow/advisory mode. Capture accuracy/performance/compatibility data before any context/request interception becomes active by default.

## 22. OpenCode update-following strategy

This project exists specifically to avoid core-fork maintenance.

Requirements:

- pin a tested OpenCode compatibility range;
- keep stable and V2 adapters separate;
- run CI against current supported releases plus a `latest/next` canary where feasible;
- treat V2 beta API breakage as adapter breakage, not core breakage;
- feature-detect optional hooks/capabilities;
- allow MCP-only operation if in-process plugin integration is temporarily incompatible;
- never store OpenCode SDK/plugin objects in persistent/domain state;
- maintain adapter conformance tests for file events, failed/successful tools, session identity, request augmentation and cleanup/reload.

## 23. Risks and mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| OpenCode V2 beta API churn | High | separate adapter, version gates, stable/MCP fallback |
| Heavy graph refresh blocks agent | High | queue/coalesce/background worker, revision barriers only when required |
| False graph certainty | High | provenance/confidence, may-relations, runtime reconciliation |
| KasaneCore tests overfit KasaneCore repo | High | benchmark on diverse real repositories/languages |
| Atlas semantics leak into core | High | boundary tests + contract review + no `atlas` names in exported core APIs |
| Python implementation limits OpenCode distribution | Medium-High | choose explicit sidecar/MCP boundary or port selected core to TS/Rust; do not mix runtime assumptions accidentally |
| SQLite growth | Medium | retention/compaction/index metrics/export-import |
| Test selection misses critical tests | High | conservative uncertainty policy, full-suite fallback at low confidence |
| Research contaminates code truth | High | external-evidence domain, explicit promotion rules |
| Strategy LLM invents scores | High | deterministic project-derived metrics + score provenance; LLM explains/proposes only |
| Historical evidence becomes stale | High | revision compatibility/freshness checks everywhere |

## 24. Language/runtime decision

KasaneCore is Python. OpenCode plugins are TypeScript/JavaScript/Bun oriented. There are three viable migration forms:

### Option A — Python sidecar + TypeScript OpenCode plugin

Pros: fastest reuse of KasaneCore algorithms, Pydantic/SQLite tests easiest to migrate.
Cons: Python deployment dependency, IPC lifecycle, packaging complexity.

### Option B — TypeScript rewrite of core

Pros: simplest OpenCode packaging, one runtime.
Cons: highest rewrite risk; difficult to prove parity quickly for graph/store/research algorithms.

### Option C — hybrid staged migration (recommended)

1. extract/clean KasaneCore algorithms into a Python host-neutral service;
2. expose stable local protocol/MCP;
3. implement thin TS OpenCode adapter;
4. benchmark and stabilize contracts;
5. selectively port latency-critical/core algorithms to TS/Rust only when evidence justifies it.

This preserves speed of delivery and avoids prematurely rewriting mature behavior.

## 25. Acceptance criteria before implementation is called complete

The migration is not complete merely because KasaneCore code runs from OpenCode.

Required evidence:

- no core import of OpenCode/Atlas/Nexus app packages;
- OpenCode stable and chosen V2 compatibility tests pass;
- MCP-only mode works independently;
- graph/twin revisions survive restart and concurrent worktree scenarios;
- incremental refresh is materially faster than full rebuild at realistic repo scale;
- impact paths are explainable and confidence-aware;
- test selection has safe fallback on uncertainty;
- stale-test fixtures are detected;
- Blueprint/Actual namespaces cannot be confused;
- Convergence cannot declare completion without required evidence;
- Strategy scoring reports source/provenance for non-LLM metrics;
- external research remains evidence, not verified project fact;
- plugin failure/degradation does not corrupt OpenCode tool/session authority;
- benchmarks record latency, token/tool-call changes, accuracy and storage growth.

## 26. Recommended immediate implementation backlog

1. Create `core-contracts` and architecture-boundary tests.
2. Decide Python sidecar protocol and lifecycle; start with local MCP/stdio or a versioned local RPC protocol.
3. Port graph revision/store and source snapshot tests.
4. Port generic path/impact engine.
5. Define `OpenCodeAdapter` interface and stable/V2 conformance fixtures.
6. Implement file-change queue/coalescing and `pi.status`.
7. Port structural + Python semantic analyzer.
8. Add `pi.symbol`, `pi.references`, `pi.path`, `pi.impact`.
9. Build benchmark harness before adding more graph types.
10. Add runtime observation and `pi.tests`.
11. Implement Test Obsolescence Engine.
12. Port Blueprint + Convergence on redesigned contracts.
13. Implement evidence-based Strategy Core.
14. Extract Research Core from Nexus concepts.
15. Expand JS/TS/framework/deep graph adapters based on measured need.

## 27. Bottom line

KasaneCore should be treated as a **high-value reference implementation and behavioral specification**, not as a library that can simply be imported by OpenCode.

The strongest migration candidates are Digital Twin revision/store behavior, path/impact analysis, graph facts/provenance, Blueprint lifecycle, Convergence policy concepts, and truthful evidence rules. The weakest direct candidates are Atlas planner/generator/verification bridges, DeepPlanner, Nexus application infrastructure, and Atlas rollout/API/UI composition.

The recommended architecture is a host-neutral Project Intelligence Core with a Python-first staged extraction, a thin TypeScript OpenCode adapter, and MCP as a durable cross-agent interface. This gives ExtendCodeAgent a path to reuse mature KasaneCore behavior while remaining maintainable as OpenCode evolves.

## References

- KasaneCore Project Intelligence architecture and recovery status on `main`.
- `agent/project_twin/analysis.py` — impact/path behavior.
- `agent/project_twin/module.py` — concrete durable Twin and incremental source refresh.
- `agent/project_intelligence/coordinator.py` — facade-only orchestration pattern and Atlas-specific context DTOs.
- `agent/project_intelligence/production_factory.py` — production composition and `ca_data`/rollout assumptions.
- `agent/architecture_blueprint/module.py` — immutable target revisions and lifecycle.
- `agent/project_convergence/module.py` — snapshot/evidence loader boundaries and truthful unavailable behavior.
- `agent/project_twin/memory_adapter.py` — evidence-gated durable memory promotion.
- `agent/deep_planner.py` — current Atlas/Nexus-coupled alternative-planning implementation.
- `app/nexus/research_agent.py` — adaptive research pipeline and infrastructure coupling.
- OpenCode stable plugins: `https://opencode.ai/docs/plugins/`
- OpenCode V2 plugins (beta): `https://opencode.ai/v2/docs/build/plugins`
- OpenCode V2 MCP: `https://opencode.ai/v2/docs/mcp-servers`
