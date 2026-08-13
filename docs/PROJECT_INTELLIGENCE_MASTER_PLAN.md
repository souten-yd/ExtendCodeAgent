# ExtendCodeAgent — Project Intelligence Master Plan

Status: initial strategic master plan
Date: 2026-08-13
Target host: OpenCode
Source inspiration / migration candidate: `souten-yd/KasaneCore` Atlas Project Intelligence

## 1. Mission

Extend OpenCode without forking or deeply modifying OpenCode core by adding a portable Project Intelligence layer that gives coding agents a persistent, revision-aware understanding of a project and closes the loop between requirements, strategy, implementation, tests, runtime evidence, and completion.

OpenCode remains the agent runtime. ExtendCodeAgent supplies project understanding and decision intelligence.

The extension must work across a wide model spectrum: weak/low-context local LLMs, practical local coding models, OpenCode's configured host model, and frontier reasoning/coding models. Project Intelligence must therefore move as much work as practical into deterministic analysis and provide a configurable model-routing layer rather than assuming one model tier.

```text
OpenCode
  ├─ models / providers
  ├─ sessions / agents / subagents
  ├─ read / edit / bash / LSP / web
  ├─ MCP client
  └─ plugin runtime
          |
          v
ExtendCodeAgent OpenCode Adapter (thin)
          |
          v
Project Intelligence Core (host-independent)
  ├─ Project Graph
  ├─ Digital Twin
  ├─ Impact Intelligence
  ├─ Test Intelligence
  ├─ Runtime Intelligence
  ├─ Context Intelligence
  ├─ Research Intelligence
  ├─ Architecture Blueprint
  ├─ Strategy Planner
  ├─ Execution Planning support
  ├─ Convergence / Replanning
  ├─ Requirement / Evidence Traceability
  └─ Model Routing / Capability Policy
```

The project MUST NOT become an OpenCode fork. Any OpenCode-specific API use belongs behind a thin adapter package.

## 2. Architectural principles

1. **Host independence** — Core packages do not import OpenCode APIs.
2. **Ports and adapters** — OpenCode, MCP, CLI, Git, LSP, test runners, research, memory, storage, and LLM providers integrate through explicit ports.
3. **Revision-aware truth** — every Project Graph/Twin result identifies the source/worktree revision from which it was derived.
4. **Actual versus planned separation** — planned Blueprint objects never masquerade as existing code facts.
5. **Evidence over inference** — static inference, runtime observation, tests, external research, and user decisions retain distinct provenance and confidence.
6. **Incremental by default** — file/tool events invalidate the smallest safely-computable graph region rather than rebuilding the repository blindly.
7. **OpenCode-native UX** — use OpenCode plugin hooks, tools, commands, agents, MCP, sessions, and SDK instead of duplicating them.
8. **Compatibility isolation** — OpenCode API changes are absorbed in `adapters/opencode/*`; core schemas remain stable.
9. **Truthful degradation** — unavailable analysis is `unavailable/degraded`, never silently treated as passed or verified.
10. **Measured rollout** — off -> shadow -> advisory -> active gates, with parity/regression measurement and rollback.
11. **Model-tier independence** — no core capability requires a frontier model; weak local models receive smaller structured tasks and deterministic evidence.
12. **Explainable routing** — model/provider escalation and fallback are policy-driven, configurable, observable, and privacy-aware.

## 3. OpenCode integration strategy

OpenCode currently provides strong extension primitives. The stable plugin surface exposes file, watcher, LSP, session, todo, command, and tool before/after events. OpenCode V2 additionally exposes a beta plugin API with transforms for agents/tools/commands/skills/references, request-time session hooks, tool hooks, and a V2 client-like context. V2 is explicitly beta, so ExtendCodeAgent must not bind its domain model directly to V2 draft shapes.

Recommended layers:

```text
packages/
  core-contracts/          # language-neutral domain contracts
  graph-core/              # nodes, edges, revisions, provenance, queries
  twin-core/               # lifecycle, incremental invalidation, reconciliation
  impact-core/             # path / impact / risk / test selection
  test-intelligence/       # health, staleness, obsolete/missing/redundant tests
  runtime-intelligence/    # test/trace/coverage/runtime observations
  context-intelligence/    # bounded task/phase context packages
  blueprint-core/          # target architecture model and revisions
  strategy-core/           # alternatives, tradeoffs, migration/rollback strategy
  convergence-core/        # actual-vs-target matching, progress, recovery decisions
  research-core/           # research plans, evidence, claim/source quality
  traceability-core/       # requirement -> evidence chain
  model-routing/           # provider-independent logical roles and policies
  storage-sqlite/          # initial durable storage adapter
  analyzers-python/
  analyzers-js-ts/
  analyzers-frameworks/
  adapters-opencode-v1/
  adapters-opencode-v2/
  adapters-llm/
  mcp-server/
  cli/
```

If a monorepo is premature, these may initially be directories in one package, but dependency direction must remain equivalent.

## 4. Capability portfolio and priority

Scoring: 100 = highest strategic value for extending OpenCode. Priority also considers dependency centrality and expected user benefit.

| Capability | Add value | Priority | Why |
|---|---:|---|---|
| Digital Twin | 100 | S+ | Persistent revision-aware project truth; foundation for stale-context detection and incremental analysis. |
| Project Graph | 98 | S+ | Replaces repeated grep/read reconstruction with queryable structural/semantic relations. |
| Impact Analysis | 98 | S+ | Direct user benefit: determines what a change can break and why. |
| Convergence | 98 | S+ | Separates "agent says done" from evidence-backed completion against target state. |
| Semantic / resolved Call Graph | 96 | S | Makes graph materially more accurate than name/grep matching. |
| Strategy Planner | 96 | S | Compares implementation/migration alternatives using actual project facts and external evidence. |
| Static/runtime reconciliation | 96 | S | Corrects static uncertainty with real observations over time. |
| Incremental refresh | 95 | S | Required for usable latency/scale and revision freshness. |
| Test selection | 95 | S | Runs the tests justified by impact instead of arbitrary/full-suite choices. |
| Test obsolescence detection | 94 | S | Detects green-but-stale tests, missing assertions/paths, and outdated evidence. |
| Architecture Blueprint | 94 | S | Durable approved target state, separate from transient execution plans. |
| Revision-aware context | 93 | S | Prevents agents from acting on context derived from an older workspace revision. |
| Side-effect/resource graph | 93 | S | Captures DB/file/network/process/UI effects that call graphs miss. |
| Automatic replanning | 93 | S | Converts divergence into bounded repair/downstream replan/strategy revision. |
| API/DB/schema graph | 92 | A+ | High-value end-to-end backend and client impact paths. |
| Data-flow graph | 90 | A+ | Valuable for correctness/security/data lineage; should be scoped/on-demand first. |
| Context Intelligence | 90 | A+ | Converts graph facts into bounded high-value context without replacing OpenCode context management. |
| Evidence traceability | 90 | A+ | Provides auditable proof of completion. |
| Test coverage/evidence graph | 90 | A+ | Basis of stale-test detection and confidence. |
| Runtime Intelligence | 89 | A+ | Converts tool/test execution into durable project evidence. |
| Dependency-aware plan compiler | 89 | A+ | Orders execution using real dependencies while retaining OpenCode planning UX. |
| Model routing / tier adaptation | 89 | A+ | Makes the same intelligence usable with weak local models and frontier models without hard-coding providers. |
| State/event/recovery graph | 88 | A | Critical for workflow/job/session/retry-heavy systems. |
| Requirement traceability | 87 | A | Preserves intent through planning, code, tests, and evidence. |
| Risk Intelligence | 86 | A | Combines impact, uncertainty, history, and runtime evidence. |
| CFG | 85 | A | Useful for difficult correctness/debug/security cases; expensive if always-on. |
| Research Intelligence | 84 | A | OpenCode already has web primitives; value is adaptive planning, evidence and source quality. |
| UI/rendering graph | 83 | A | Useful for full-stack impact tracing; second wave after backend graph quality. |
| Historical incident linkage | 75 | B+ | Valuable after durable graph/evidence identity exists. |
| Execution Planner replacement | 75 | B | Do not replace OpenCode Plan/Todo; provide structured envelopes and constraints instead. |
| Memory/knowledge replacement | 75 | B | Integrate with a generic memory port; do not clone host memory systems. |

## 5. Project Graph target

A common revisioned graph should support multiple analysis domains without exposing one micro-API per graph type.

### Structural

Nodes: repository, directory, file, package, module, class, function, method, variable, constant, type, config, dependency, test, fixture.

Edges: contains, defines, imports, exports, references, depends_on.

### Semantic and call

Resolve definitions, aliases, re-exports, inheritance, overrides, interface/protocol implementation, decorators, dependency injection and call targets. Dynamic ambiguity must be represented as `may_call` with provenance/confidence rather than promoted to certain fact.

### Control/data flow

Support CFG blocks/branches/loops/exceptions/returns and intraprocedural DFG first. Add interprocedural flow and API-to-persistence lineage later. Analysis may be on-demand for impacted code rather than global.

### State/event/recovery

Model workflows, sessions, jobs, retry, timeout, rollback, event production/consumption and causal transitions.

### Resource / side-effect

Model concrete DB tables/queries/transactions, file operations, network endpoints, process commands, configuration reads, and UI/render effects.

### API/schema/persistence

Enable route -> handler -> service -> repository/query -> table -> response schema -> client consumer paths.

### UI/rendering

Incrementally support control -> event -> handler -> state -> API -> response -> render, including common React/Vue/Svelte patterns through adapters.

### Runtime and evidence

Keep runtime observations separate from static facts, but make them queryable together through reconciliation.

## 6. Digital Twin target

The Twin is the lifecycle and truth layer over Project Graph.

Required readiness states:

`absent`, `building`, `ready`, `stale`, `degraded`, `corrupt`, `disabled`.

Required responsibilities:

- stable project/workspace identity;
- source revision + working-tree fingerprint;
- immutable Twin revisions;
- full build and incremental refresh;
- analyzer-version tracking;
- invalidation by changed file/symbol/dependency;
- runtime observation ingest;
- static/runtime reconciliation;
- path/impact/test/context queries;
- persistence/export/import/compaction;
- diagnostics and confidence/provenance.

OpenCode file/watch/LSP/tool events should feed an event queue. Plugin hooks must remain fast: they enqueue invalidation/evidence work; they do not run repository-scale graph analysis synchronously.

## 7. Impact and Test Intelligence

`impact` must return direct/transitive effects, affected behavior, resources, requirements, recommended tests, uncertainty and explanation paths.

Test Intelligence extends KasaneCore's related-test and test-selection concepts into a first-class health model:

```text
healthy
suspect
stale
obsolete
missing
redundant
```

Per-test evidence should include covered refs/paths, source revision, last execution/result, coverage/trace evidence, assertion signals, relevant implementation changes, and confidence. A green test with evidence from an incompatible/stale project revision cannot be considered fresh evidence.

## 8. Blueprint, Strategy, Execution and Convergence

Keep four responsibilities distinct:

- **Blueprint**: approved target state and contracts.
- **Strategy Planner**: alternative approaches and tradeoffs; selects migration/implementation strategy.
- **Execution Planning support**: translates a strategy into dependency-aware constraints/items for OpenCode Plan/Todo rather than replacing OpenCode planning.
- **Convergence**: compares one target revision with one actual Twin revision and decides what remains.

Strategy alternatives should be scored using project impact, test burden, compatibility, migration complexity, rollbackability, performance, maintainability, uncertainty, runtime evidence and optional external research.

Model use in Strategy is tier-aware. Weak local models should receive smaller bounded decisions and deterministic metrics; frontier models may perform broader synthesis. The deterministic evidence and scoring inputs remain the same across model tiers so evaluation is comparable.

Convergence states should include absent/partial/materialized/observed/verified/divergent/blocked/stale and return bounded decisions such as continue, complete, repair current scope, replan downstream, revise blueprint, request decision, or halt unsafe.

## 9. Research Intelligence

Do not duplicate OpenCode's basic web tools. Add a research orchestration/evidence layer with provider-independent Search/Fetch/Evidence ports. Search/fetch and synthesis model routing are separate concerns. Research may use local synthesis, host models, or frontier models according to configuration and privacy policy.

## 10. Model routing target

Define logical model roles rather than hard-coded names:

```text
fast_classifier
small_structured
summarizer
code_reasoner
strategy_reasoner
research_synthesizer
verification_reviewer
fallback
```

Roles map to configured endpoints such as OpenCode host models, OpenAI-compatible local endpoints, or remote/frontier providers. Required routing modes include manual, local-first, frontier-first, cost-optimized, latency-optimized, quality-optimized, adaptive, host-only, and local-only.

Routing must consider endpoint capabilities, context limits, privacy rules, task complexity, uncertainty, cost/latency budgets, and user policy. Escalation/fallback decisions must be observable and explainable. No silent remote escalation is allowed when policy forbids it.

Weak local-model mode emphasizes deterministic graph queries, small structured context, explicit schemas, and single-purpose calls. Frontier mode may use richer synthesis but cannot bypass deterministic evidence/verification rules.

## 11. Implementation and validation governance

The detailed implementation order, local-only validation strategy, real OpenCode/LLM A/B matrix, configuration model, CI restrictions, PR boundaries, and Codex token-efficiency rules are defined in `docs/IMPLEMENTATION_EXECUTION_LOCAL_VALIDATION_PLAN.md` and `docs/CODEX_IMPLEMENTATION_GUIDE.md`.

The baseline policy is local-first validation. GitHub CI is exceptional. Real LLM evaluations are milestone-gated and include weak local, practical local, OpenCode host/default, and frontier profiles when available.
