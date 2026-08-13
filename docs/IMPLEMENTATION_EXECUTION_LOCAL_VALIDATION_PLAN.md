# ExtendCodeAgent — Implementation, Local Validation, and Model Routing Plan

Status: canonical implementation execution plan
Date: 2026-08-13
Target host: OpenCode
Primary implementation agent: Codex
Validation policy: local-first; GitHub CI is exceptional, not default

## 1. Purpose

This document converts the strategic architecture and KasaneCore migration audit into an executable implementation, build, validation, real-LLM evaluation, and PR plan.

The objective is not to reproduce Atlas inside OpenCode. ExtendCodeAgent must add a compact, host-independent Project Intelligence layer that measurably improves project understanding, planning, implementation, test selection, verification, and completion while preserving OpenCode as the agent runtime.

The implementation must support both low-performance local LLMs and frontier models. Model/provider selection, context budgets, fallback paths, feature activation, and evaluation profiles must therefore be configurable and replaceable without changing the Project Intelligence core.

## 2. Non-negotiable constraints

1. Do not fork OpenCode or patch OpenCode core unless a documented blocker proves no supported extension mechanism can satisfy the requirement.
2. OpenCode-specific APIs, including beta/V2 APIs, remain behind replaceable adapters.
3. Every major capability supports independent enable/disable control.
4. Expensive analysis supports explicit scope, depth, latency, CPU, memory, and token budgets.
5. `off` mode preserves normal OpenCode behavior as closely as possible.
6. Project Intelligence failure degrades to advisory/unavailable behavior and must not make OpenCode unusable.
7. Plugin hooks enqueue work and return quickly; they do not perform repository-scale analysis synchronously.
8. Reuse OpenCode, LSP, Git, test frameworks, MCP, and existing libraries instead of duplicating them.
9. Reuse or adapt proven KasaneCore behavior before writing competing implementations.
10. New implementation is allowed when no suitable existing code can be generalized safely or when a rewrite measurably reduces coupling/complexity.
11. Avoid speculative abstractions and one-interface-per-method architecture.
12. Prefer concise, composable code and shared internal primitives over duplicated feature-specific implementations.
13. Local unit/integration/E2E/benchmark evidence is mandatory before a feature becomes active by default.
14. GitHub Actions is not the primary validation platform. Use it only for an essential clean-remote or cross-platform check that is not reasonably reproducible locally.
15. PRs must be independently reviewable/revertible and should deliver coherent behavior, not only scaffolding.
16. Real-LLM evaluation is required at milestone gates, but deterministic tests remain the primary correctness mechanism.
17. No feature may assume a frontier model. The system must remain useful with a weak local model by shifting work toward deterministic analysis and smaller structured tasks.
18. No feature may assume a local model. Frontier-only users must be able to use OpenCode's configured providers without running a separate LLM stack.

## 3. Critical and skeptical assessment

### 3.1 Project Graph can become an expensive second compiler

Risk: whole-repository semantic/CFG/DFG analysis can consume excessive CPU, memory, startup time, and storage; dynamic-language resolution can create false confidence.

Mitigation:
- structural graph first;
- reuse parser/LSP output;
- semantic resolution incrementally;
- CFG/DFG on-demand or impact-scoped initially;
- provenance/confidence on inferred relations;
- unsupported capabilities remain explicitly unavailable;
- benchmark against native OpenCode exploration.

Acceptance rule: a graph capability must improve at least one of answer correctness, repeat-query latency, tool-call count, token usage, or impact/test-selection quality without unacceptable regression in the others.

### 3.2 Digital Twin may duplicate Git/filesystem truth

Git/filesystem remain canonical. Twin is a rebuildable indexed projection. Every Twin revision records source/worktree fingerprint and analyzer versions. Stale detection and rebuild-from-source are mandatory. Retention is bounded.

### 3.3 Too many modules can create architecture astronautics

Boundaries are logical first. Begin with a small number of physical packages and split only where dependency direction, runtime deployment, or independent testing requires it. Use coarse ports such as HostEvents, SourceProvider, Analyzer, Storage, LLM, Research, Memory, and Verification.

### 3.4 Python sidecar plus TypeScript plugin creates operational complexity

Hybrid Python/TS is a migration strategy, not an immutable architecture. The protocol must be language-neutral and versioned. Measure startup, IPC latency, memory, and install complexity. If reuse benefits do not justify Python operational cost, rewrite only proven minimal cores while retaining KasaneCore tests/fixtures as behavioral specifications.

### 3.5 Strategy planning can become token-consuming ceremony

Strategy mode defaults to `auto`/off for small tasks. It should activate only by explicit request or risk/scope thresholds. Deterministic project signals provide metrics; LLMs generate/synthesize alternatives. Record token/time overhead and compare with native OpenCode Plan behavior.

### 3.6 Blueprint/Convergence may over-formalize simple changes

Support lightweight task targets for small work and durable Blueprint revisions only for architecture/migration/multi-step work. Convergence must work at both task and project scope.

### 3.7 Test obsolescence may be noisy

Do not infer staleness from age alone. Use changed implementation paths, coverage/trace mismatch, assertion relevance, source/evidence revision mismatch, and historical execution. Distinguish `suspect` from `stale` and `obsolete`; expose reasons/confidence; never auto-delete tests.

### 3.8 Deep Research can duplicate host capabilities

Do not port Nexus infrastructure wholesale. Define ResearchPort/evidence contracts and reuse host/MCP/search providers. Adaptive retrieval is optional and task-triggered.

### 3.9 Context Intelligence can increase rather than reduce tokens

Context packages have explicit budgets, deduplication, inclusion reasons, and confidence. Benchmark prompt/completion tokens, tool calls, wall time, and outcome quality. Auto-injection stays disabled until it demonstrates value.

### 3.10 Real-LLM evaluation is non-deterministic and expensive

Use a small fixed real-LLM scenario suite at milestone gates. Record provider/model/version/config. Compare native OpenCode, extension-off, shadow, advisory, and active modes. Do not run expensive frontier evaluations on every edit.

### 3.11 Weak local models may fail when given large unstructured context

This is a core design concern, not an edge case. Weak models should receive smaller structured facts, deterministic candidate lists, explicit schemas, and short decision tasks. The system should move complexity from the model into Project Graph, Impact, Test Selection, and deterministic policy code where practical.

### 3.12 Frontier models may make some intelligence features appear unnecessary

A strong model can often reconstruct relationships using grep/read/LSP. Therefore every automatic intelligence feature must prove value through lower repeated exploration cost, better stale-context handling, improved test selection, persistent evidence, or completion correctness. Do not enable features solely because they are architecturally elegant.

## 4. Runtime architecture

Initial target:

```text
OpenCode
  |
  +-- Thin TypeScript Host Plugin
  |      - event capture
  |      - config/status
  |      - commands/tools
  |      - fast enqueue
  |      - host model/provider bridge when available
  |
  +-- MCP client/fallback
         |
         v
ExtendCodeAgent Core Service
  - graph/twin
  - impact/test/context/runtime
  - blueprint/strategy/convergence
  - analyzer/storage adapters
  - model routing abstraction
  - optional research/memory ports
```

Core never imports OpenCode types.

## 5. Minimal initial repository structure

Create directories only when used.

```text
src/
  core/
    contracts/
    config/
    diagnostics/
    model_routing/
  graph/
  twin/
  impact/
  test_intelligence/
  runtime/
  context/
  blueprint/
  strategy/
  convergence/
  research/
  adapters/
    opencode/
    git/
    lsp/
    test_runners/
    llm/
  storage/
  mcp/
  cli/
plugin/
  opencode/
tests/
  unit/
  integration/
  fixtures/
  e2e/
  llm_eval/
tools/
  local/
docs/
```

## 6. Configuration architecture

Precedence:

```text
built-in defaults
< user config
< project config
< environment/runtime profile
< session/command override
```

Suggested project file:

```text
.extendcodeagent/config.jsonc
```

All resolved configuration is materialized into one immutable runtime configuration object. Do not scatter environment reads and feature checks throughout business logic.

### 6.1 Global mode

```jsonc
{
  "enabled": true,
  "mode": "off" // off | shadow | advisory | active
}
```

- `off`: no automatic analysis/injection.
- `shadow`: compute/measure without changing OpenCode decisions or prompts.
- `advisory`: explicit tools/suggestions/context available.
- `active`: configured automatic hooks may affect context/test/replanning recommendations.

Development default: `off` or `shadow`.

### 6.2 Feature flags

Independent flags are required for:

```text
graph
twin
semantic
call_graph
cfg
data_flow
state_event
side_effects
api_schema_db
ui_graph
runtime
impact
test_selection
test_obsolescence
context
blueprint
strategy
convergence
research
traceability
memory
```

Resolve these into a `CapabilityPolicy` during composition rather than checking raw config everywhere.

### 6.3 Analysis budgets

Support:

```text
max_files
max_file_bytes
max_graph_nodes
max_graph_edges
max_depth
incremental_batch_ms
background_workers
cpu_budget
memory_budget_mb
deep_analysis = never | on_demand | auto | always
```

CFG/DFG/research default to `on_demand` or `auto`, not `always`.

### 6.4 Context budgets

Support:

```text
context.max_tokens
context.max_items
context.min_confidence
context.include_runtime
context.include_tests
context.include_uncertainty
context.auto_inject = false | planning | generation | both
```

Weak-model profiles should use smaller defaults.

## 7. Flexible model/provider routing

### 7.1 Design goal

The Project Intelligence core must never depend on one model vendor or one performance tier. A `ModelRouter` chooses a logical model role, not a hard-coded model name.

Logical roles:

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

Each role maps to one or more configured provider/model endpoints.

### 7.2 Provider classes

Support at least these categories through adapters:

```text
host_model        # OpenCode's configured provider/session model
local_openai_api  # llama.cpp, vLLM, Ollama-compatible/OpenAI-compatible endpoint
local_custom      # optional direct local adapter
remote_api        # frontier provider exposed through supported API/host
mcp_model_service # optional external model broker
```

Do not embed provider SDKs into domain logic.

### 7.3 Routing modes

```text
manual
local_first
frontier_first
cost_optimized
latency_optimized
quality_optimized
adaptive
host_only
local_only
```

`adaptive` must be policy-based and explainable. It should not silently escalate to a paid/remote model unless user policy allows it.

### 7.4 Example configuration

```jsonc
{
  "models": {
    "routing_mode": "adaptive",
    "allow_remote_escalation": true,
    "allow_local_fallback": true,
    "roles": {
      "fast_classifier": ["local-small", "host-default"],
      "small_structured": ["local-medium", "host-default"],
      "summarizer": ["local-medium", "host-default"],
      "code_reasoner": ["host-default", "frontier-code"],
      "strategy_reasoner": ["frontier-reasoning", "host-default"],
      "research_synthesizer": ["frontier-reasoning", "local-medium"],
      "verification_reviewer": ["host-default", "frontier-reasoning"]
    },
    "endpoints": {
      "local-small": {
        "type": "openai-compatible",
        "base_url": "http://127.0.0.1:8080/v1",
        "model": "local-small",
        "max_context": 8192,
        "expected_tier": "low"
      },
      "local-medium": {
        "type": "openai-compatible",
        "base_url": "http://127.0.0.1:8081/v1",
        "model": "local-medium",
        "max_context": 32768,
        "expected_tier": "medium"
      },
      "host-default": {
        "type": "opencode-host",
        "expected_tier": "unknown"
      },
      "frontier-reasoning": {
        "type": "host-or-remote",
        "expected_tier": "frontier"
      }
    }
  }
}
```

Exact model identifiers are user configuration, not source constants.

### 7.5 Capability declaration

Every endpoint may declare or probe:

```text
context_length
structured_output_support
tool_call_support
reasoning_strength_estimate
code_strength_estimate
latency_class
cost_class
privacy_class
local_or_remote
```

Routing uses these capabilities plus task requirements.

### 7.6 Task complexity classification

Prefer deterministic complexity signals where possible:

```text
number of impacted files/symbols
cross-language/framework count
presence of architecture migration
runtime/evidence conflict
uncertainty level
required external research
context size
convergence severity
security/data-flow relevance
```

A weak model can classify only after deterministic features are assembled into a small schema.

### 7.7 Escalation policy

Example:

```text
local small
  -> structured extraction / classification / short summary
local medium
  -> bounded code explanation / candidate ranking
host/default model
  -> normal coding-plan reasoning
frontier
  -> high-risk strategy, ambiguous convergence, complex cross-system reasoning
```

Escalation reasons must be recorded, e.g. `context_exceeds_model`, `low_confidence`, `cross_domain_strategy`, `verification_conflict`.

### 7.8 De-escalation and token control

Do not use frontier models for deterministic tasks. Before model calls:
- query graph/storage directly;
- filter/rank evidence;
- compress to structured fields;
- ask the smallest sufficient question;
- cache stable model-independent artifacts;
- optionally cache model outputs keyed by input hash/model/config for evaluation only.

### 7.9 Weak-model prompt profile

Weak models receive:
- smaller context;
- explicit JSON schema;
- one task per call;
- reduced number of alternatives;
- deterministic candidate choices where possible;
- no requirement to infer repository structure from raw files when graph facts exist.

### 7.10 Frontier-model prompt profile

Frontier models may receive richer evidence and can perform multi-objective strategy/review, but still receive bounded, provenance-rich inputs. Do not abandon deterministic checks because a stronger model is available.

### 7.11 Privacy controls

Configuration must support:

```text
remote_code_policy = deny | metadata_only | selected_context | allow
research_remote_policy = deny | allow
redaction_rules
path allow/deny patterns
secret scanning before remote context
```

Local-first users must be able to prevent project source from leaving the machine.

## 8. Feature-specific runtime policy

### Graph/Twin
No LLM required for baseline structural build. Semantic resolution should prefer parser/LSP. LLM-assisted inference, if introduced, is optional and tagged as inferred.

### Impact/Test selection
Deterministic graph algorithms first. LLM may summarize impact or resolve ambiguous candidate ranking, but must not be required for core results.

### Test obsolescence
Deterministic evidence score first; optional model reviewer for ambiguous `suspect` cases.

### Context Intelligence
Deterministic retrieval/ranking first. Local summarizer may compress low-priority facts. Frontier model is not required.

### Blueprint
Schema/lifecycle deterministic. Model may propose Blueprint content. Weak-model mode builds smaller sections iteratively.

### Strategy
Local mode may produce 1-2 bounded alternatives; frontier mode may compare richer alternatives. Deterministic metrics remain identical.

### Convergence
Element matching and evidence rules deterministic. Model only handles ambiguous semantic matching or explanation when configured.

### Research
Search/fetch/evidence collection independent from reasoning model. Synthesis can be routed separately.

## 9. Local development and validation policy

### 9.1 Local-first rule

All PR acceptance begins locally. GitHub Actions should normally be absent or manually invoked only for exceptional checks.

Required local script family:

```text
tools/local/bootstrap.*
tools/local/lint.*
tools/local/test-unit.*
tools/local/test-integration.*
tools/local/test-e2e.*
tools/local/benchmark.*
tools/local/llm-eval.*
tools/local/all-fast.*
tools/local/all-release.*
```

Cross-platform wrappers may share one Python/Node implementation to avoid duplication.

### 9.2 Local environment capture

Every benchmark/E2E report records:
- OS/kernel;
- CPU/RAM;
- Python/Node/Bun/OpenCode versions;
- package lock hashes;
- model/provider identifiers;
- relevant config profile;
- git commit;
- fixture/repository revision.

### 9.3 Test pyramid

1. Pure unit tests — contracts, graph algorithms, config, routing, policies.
2. Component tests — SQLite/store, source snapshot, analyzers, invalidation.
3. Integration tests — Graph+Twin+Impact+Context, runtime ingest, test selection.
4. Host adapter contract tests — simulated OpenCode events/client.
5. Local OpenCode E2E — real plugin loaded into real OpenCode.
6. Real-repository benchmark — several fixed repositories.
7. Real-LLM A/B evaluation — milestone-gated only.

### 9.4 No-network baseline

Core unit/integration tests must run with network disabled. Network/LLM/research tests are separately labeled and never required for basic correctness.

## 10. Real repository evaluation

Use at least three fixture classes:

```text
small:  < 100 source files
medium: hundreds to low thousands
large:  representative real project
```

Include at least Python and JS/TS projects before claiming general usefulness.

Measure:
- initial index time;
- incremental refresh time;
- graph DB size;
- peak memory;
- query latency;
- path/impact precision on curated cases;
- test-selection recall/precision where ground truth is available;
- stale-context detection;
- restart persistence.

Do not optimize synthetic microbenchmarks at the expense of real tasks.

## 11. Real OpenCode connection evaluation

### Stage A — adapter smoke

Load plugin in a real local OpenCode installation. Verify:
- config discovery;
- status command;
- no errors in `off` mode;
- file/session/tool events observed;
- event queue does not block UI/agent execution;
- sidecar/MCP reconnect behavior.

### Stage B — shadow

Enable graph/twin in shadow. Edit files through OpenCode and externally. Confirm:
- incremental invalidation;
- correct Twin revision changes;
- no prompt/behavior modification;
- low hook latency;
- restart recovery.

### Stage C — advisory

Expose explicit tools:

```text
pi.status
pi.symbol
pi.references
pi.path
pi.impact
pi.tests
pi.context
```

Ask real OpenCode agents to use them on fixed tasks. Compare with native grep/read/LSP exploration.

### Stage D — active

Only after shadow/advisory evidence. Enable bounded automatic context/test suggestions. Verify disabling each capability immediately restores baseline behavior.

## 12. Real LLM evaluation matrix

At each major milestone, run a small matrix rather than every model combination.

Minimum profiles:

1. `local-low`: intentionally weak/low-context local model.
2. `local-medium`: practical local coding model.
3. `host-default`: normal OpenCode configured model.
4. `frontier`: strong reasoning/coding model when available.

Scenarios:
- find implementation path for a feature;
- assess impact of a symbol/API change;
- select tests for a change;
- diagnose a multi-file bug;
- plan a medium architectural modification;
- detect stale evidence/test risk;
- resume after repository changed externally;
- Blueprint/Convergence task after milestone supports it.

Compare modes:

```text
OpenCode native
ExtendCodeAgent off
shadow
advisory
active
```

Metrics:
- task success;
- factual/code accuracy;
- files unnecessarily modified;
- tests selected and missed;
- tool calls;
- prompt/completion tokens if available;
- wall time;
- model calls by tier;
- remote/frontier escalations;
- context size;
- user-visible errors;
- rollback/recovery success.

Weak local models are considered a first-class success criterion. A feature that only improves frontier models but severely harms local models should not default to active globally.

## 13. Model-routing evaluation

Create deterministic routing tests with fake model endpoints. Verify:
- local-only never calls remote;
- host-only never starts/uses local model adapter;
- remote escalation respects policy;
- context-length failure reroutes correctly;
- unavailable model falls back according to config;
- no fallback when policy forbids it;
- routing explanation is observable;
- per-role timeout/retry limits work;
- cost/token budgets cap escalation.

Then run local live routing with at least one OpenAI-compatible local endpoint and one OpenCode-hosted/default model.

## 14. Implementation waves and PR boundaries

### PR-A — Foundation contracts/config/local harness

Deliver:
- repository/package bootstrap;
- host-neutral contracts;
- configuration loader and capability policy;
- model routing interfaces/config only, with fake adapters;
- diagnostics/logging;
- local test runners;
- architecture-boundary tests.

Acceptance:
- local bootstrap reproducible;
- unit suite passes offline;
- no OpenCode runtime dependency in core;
- feature flags and profile precedence tested.

### PR-B — Graph revision/store/source snapshot

Prefer adapting KasaneCore behavior.

Deliver:
- node/edge/evidence/provenance contracts;
- SQLite revision store;
- source snapshot/git/worktree fingerprint;
- full rebuild;
- incremental file invalidation;
- bounded retention/export.

Acceptance:
- restart-safe;
- stale detection;
- deterministic identities;
- medium fixture benchmark recorded locally.

### PR-C — Structural/Python semantic + path/impact

Deliver:
- structural analyzer;
- Python AST semantic relations;
- optional LSP enrichment port;
- path tracing;
- direct/transitive impact;
- uncertainty/explanation;
- test candidate projection.

Acceptance:
- curated ground-truth cases;
- no graph false-certainty regressions;
- benchmark against native grep/LSP for repeated impact tasks.

### PR-D — OpenCode adapter + MCP advisory integration

Deliver:
- real plugin skeleton;
- version-isolated adapter;
- event queue/coalescing;
- config/status;
- MCP tools;
- `off`, `shadow`, `advisory` modes;
- sidecar lifecycle/reconnect.

Acceptance:
- real local OpenCode smoke/shadow/advisory passes;
- disabling plugin/features restores native behavior;
- event-hook latency budget met.

### PR-E — Context + Test Intelligence + runtime ingest

Deliver:
- bounded context package;
- runtime/test observation normalization;
- graph-based test selection;
- first evidence-based obsolescence scoring;
- tool-result ingest adapter.

Acceptance:
- real test-project scenarios;
- stale evidence never treated fresh;
- weak local model receives smaller structured context;
- local A/B evaluation recorded.

### PR-F — Blueprint + task-level Convergence

Deliver:
- immutable target revisions;
- review/activate/supersede;
- actual-vs-target matching;
- task-level progress states/decisions;
- optional mode only.

Acceptance:
- simple tasks can bypass durable Blueprint;
- unavailable evidence never becomes verified;
- recovery decisions deterministic where possible.

### PR-G — Strategy + model routing live adapters

Deliver:
- deterministic strategy metrics;
- role-based ModelRouter;
- OpenCode host-model adapter;
- OpenAI-compatible local model adapter;
- configurable local/frontier routing/escalation;
- strategy generation/synthesis;
- privacy/remote-code policy.

Acceptance:
- fake-routing tests;
- local low/medium and frontier/host model evaluation;
- token/time/model-tier report;
- local-only privacy policy proven.

### PR-H — JS/TS/framework graph expansion + deeper analysis

Deliver only after core proves value:
- JS/TS semantic adapter;
- framework API/schema/resource relations;
- on-demand CFG/DFG/state/event/UI expansions.

Each analyzer must be independently configurable.

### PR-I — Research/evidence and project-level convergence

Only after core workflows stabilize. Reuse host/MCP search, do not copy Nexus infrastructure wholesale.

## 15. Merge policy

For each implementation PR:

1. branch from current `main`;
2. inspect existing implementation before coding;
3. record intended reuse/modification/removal/new code;
4. implement smallest coherent slice;
5. run local checks;
6. run relevant real-repo benchmark if behavior/performance changes;
7. run real OpenCode/LLM evaluation only at defined milestone PRs;
8. update current-status/evidence docs in the same PR;
9. review diff for duplication and unnecessary abstractions;
10. merge only when local acceptance evidence is recorded.

Prefer squash or normal merge according to repository policy, but preserve clear PR-level milestones.

Do not leave a long-lived mega-PR containing the entire implementation.

## 16. GitHub CI policy

Default: no automatic full CI.

Allowed only when justified by one of:
- clean checkout/package reproducibility cannot be trusted locally;
- Windows/Linux/macOS behavior must be compared and local machines are unavailable;
- GitHub-specific integration itself is under test;
- release artifact integrity needs remote reproducibility.

Even then:
- keep workflows manually triggered or narrow where possible;
- avoid expensive matrix/model/network jobs;
- never put real-LLM evaluation in mandatory GitHub CI;
- do not upload source/model-sensitive artifacts unnecessarily;
- local evidence remains primary.

## 17. Codex token-efficiency rules

Codex must optimize implementation workflow as well as code.

Before coding:
1. read the relevant master plan/current-status/migration section only;
2. search symbols/files before opening large files;
3. inspect existing implementations and direct callers;
4. identify reusable logic and tests;
5. state a concise implementation slice internally/in task notes.

During coding:
- modify existing code when appropriate instead of parallel replacement;
- avoid broad refactors unrelated to acceptance criteria;
- centralize repeated transforms/contracts;
- do not generate large comments that restate code;
- do not create generic frameworks before two concrete uses exist;
- use deterministic code instead of LLM calls when feasible;
- keep schemas compact and versioned;
- prefer focused tests over huge duplicated fixtures;
- reuse fixture builders.

During validation:
- run focused tests first;
- expand to affected integration suite after focused pass;
- run expensive real-repo/LLM tests only when the changed layer warrants them;
- store concise machine-readable reports plus short human summary rather than full verbose logs in Git.

## 18. Performance budgets

Initial budgets are provisional and must be tuned from measurements.

Plugin/event path:
- enqueue/event processing should normally remain below tens of milliseconds;
- repository analysis never blocks the hook.

Queries:
- cached status/symbol lookups should feel interactive;
- common impact/path queries target sub-second to low-single-second latency on medium repos;
- deep analysis may be slower but must show status/cancellation.

Incremental refresh:
- proportional to affected scope, not total repository, whenever analyzers support it.

Storage:
- bounded revision retention and compaction;
- no unbounded runtime evidence accumulation.

Context:
- weak local profile defaults materially smaller than frontier profile;
- auto-injected context must have a hard cap.

## 19. Cancellation, timeout, recovery

All expensive jobs need:
- cancellation token/job ID;
- timeout;
- checkpoint/retry semantics where useful;
- idempotency key for event replay;
- coalescing of repeated file events;
- safe restart;
- explicit degraded diagnostics.

Model calls need per-role timeout/retry policies. Retries must not silently escalate provider tier unless policy allows it.

## 20. Observability

Local diagnostics should expose:
- feature state/mode;
- Twin/source revision;
- stale/degraded reason;
- queue depth/jobs;
- analyzer capability/version;
- graph/storage size;
- last refresh duration;
- model routing decision/reason;
- model tier/provider used;
- token/context usage where available;
- remote escalation count;
- last benchmark/evaluation profile.

Avoid telemetry that requires a cloud backend. Local JSON/SQLite/log output is sufficient initially.

## 21. Security and safety boundaries

- source mutation remains OpenCode/tool authority, not Project Intelligence authority;
- Project Intelligence can recommend, not bypass host permission;
- external research does not become verified code truth;
- runtime/test evidence retains provenance;
- remote model use respects project privacy policy;
- secrets must be filtered before optional remote model context;
- sidecar binds localhost by default and should use a narrow authenticated/session token when an HTTP transport is used;
- no arbitrary command execution through the intelligence service unless explicitly mediated by the host/test-runner adapter.

## 22. Documentation and evidence records

Maintain:

```text
docs/CURRENT_STATUS.md
docs/DECISIONS.md
docs/evidence/
  local-benchmarks/
  opencode-e2e/
  llm-eval/
```

Do not commit huge raw logs. Record command, environment, exact result summary, artifact hash/path, limitations, and failures truthfully.

## 23. Definition of done for first production-capable release

The first production-capable release is not complete until:

- OpenCode core remains unmodified;
- off/shadow/advisory/active modes work;
- every major capability can be independently disabled;
- config precedence and profiles are tested;
- Graph/Twin revisions and stale detection are durable;
- impact/path/test selection provide explainable results;
- local OpenCode integration survives restart and external file changes;
- at least one weak local model and one frontier/host model are validated;
- local-only/no-remote mode is proven;
- routing/fallback/escalation policy is tested;
- prompt/tool/token/time metrics show no unacceptable regression;
- deterministic tests pass locally from a clean bootstrap;
- real-repository benchmarks are recorded;
- failures degrade safely;
- no mandatory GitHub CI is required for normal development;
- implementation docs and current status match observed evidence.

## 24. Immediate next action

After this planning PR is merged, Codex should begin PR-A only. Do not start by copying large KasaneCore directories.

PR-A must establish the host-neutral contracts, configuration/capability policy, model-routing contracts, local validation harness, and dependency-boundary tests. Only after those boundaries pass should PR-B port/adapt the KasaneCore Graph/Twin persistence and snapshot behavior.
