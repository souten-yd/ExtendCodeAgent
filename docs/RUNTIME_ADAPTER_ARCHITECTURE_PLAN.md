# ExtendCodeAgent Runtime Adapter Architecture Plan

> **Consolidated 2026-08-16.** Canonical architecture reference. Sequencing (section 11) is superseded by `docs/PI_MASTER_EXECUTION_PLAN.md`.

Status: accepted architecture proposal for the productization phase
Date: 2026-08-16

## 1. Decision

ExtendCodeAgent MUST treat OpenCode as the **primary reference runtime and first native adapter**, not as the architectural core of Project Intelligence.

The durable product boundary is:

```text
Agent runtime / harness
        |
        v
Agent Runtime Adapter
        |
        v
host-neutral observations, capabilities and delivery ports
        |
        v
ExtendCodeAgent Project Intelligence
```

The Project Intelligence core, task-aware orchestration, context selection, impact analysis, verification, runtime evidence, model routing, Strategy and Convergence must remain usable without importing OpenCode-specific types.

This decision does **not** require building a new agent harness. ExtendCodeAgent should not duplicate the agent loop, shell, patching, permissions, session management, TUI, provider integration or MCP client behavior already supplied by capable runtimes.

OpenCode remains the primary runtime for current productization and release validation.

## 2. Why this boundary matters

There are two materially different product architectures:

### Rejected: OpenCode as the product core

```text
ExtendCodeAgent
  -> OpenCode-specific session/tool/event contracts everywhere
  -> Project Intelligence tightly coupled to OpenCode lifecycle
```

This reduces short-term adapter work but creates long-term lock-in. A future Codex CLI, Claude Code, Pi or independent harness integration would require changes throughout Project Intelligence and task orchestration.

### Accepted: OpenCode as the first runtime adapter

```text
                  ExtendCodeAgent
        +--------------------------------+
        | host-neutral Project Intelligence|
        +----------------+---------------+
                         |
                Agent Runtime Contract
                         |
          +--------------+---------------+
          |              |               |
      OpenCode        MCP-only       future native
       adapter         fallback        adapters
                                         |
                                Codex / Claude / Pi / ...
```

The current OpenCode integration remains valuable because it is the reference implementation and the first environment in which transparent PI is productized.

## 3. Critical constraint: do not build a second harness

This plan explicitly rejects turning ExtendCodeAgent into an AtomicBot-style independent harness unless future evidence demonstrates a requirement that cannot be satisfied through adapters.

Do not add generic replacements for:

- agent control loop;
- shell execution;
- file patch/edit execution;
- permission prompts;
- session history;
- TUI;
- provider authentication;
- ordinary MCP client/server lifecycle already supplied by runtimes;
- generic browser automation;
- generic tool registry unrelated to Project Intelligence.

Those components are expensive to maintain and are not the source of ExtendCodeAgent's differentiated value.

The differentiated value remains:

- Project Model / Graph / Digital Twin;
- Context Intelligence;
- Impact Intelligence;
- Test and Verification Intelligence;
- Runtime Evidence;
- Task-aware Intelligence selection;
- model routing around structured project evidence;
- Strategy / Convergence when justified;
- Research when explicitly useful;
- measured evaluation and evidence quality.

## 4. Three integration tiers

Do not require every runtime to support the same depth of integration.

### Tier 1 — Generic MCP / explicit tools

A runtime that can consume MCP or equivalent tools can use bounded PI queries even without a native runtime adapter.

Expected minimum surface:

- status/health;
- symbol lookup;
- references;
- path;
- impact;
- test selection;
- bounded context;
- optional Research/Strategy operations already exposed by the application.

This is the compatibility floor, not the transparent automation target.

### Tier 2 — Native runtime adapter

A native adapter additionally normalizes runtime observations and may expose PI through the runtime's preferred plugin/tool mechanism.

Possible capabilities include:

- task/session observation;
- file mutation observation;
- tool execution observation;
- model/provider observation;
- verification/result observation;
- tool exposure;
- context delivery;
- session lifecycle and health;
- runtime restart/reconnect signals.

### Tier 3 — Transparent integration

A runtime adapter that provides enough trusted signals can support the transparent Task-aware PI controller.

The user asks normal coding questions. The adapter supplies host-neutral signals, the controller selects the minimum useful PI, and runtime-specific delivery is performed through the adapter.

Not every runtime must reach Tier 3.

## 5. Runtime capability negotiation

Different agent harnesses expose different hooks. The core must not assume OpenCode's exact event model.

Define a compact immutable capability descriptor. Reuse existing capability/config contracts where possible rather than creating duplicate concepts.

Conceptual contract:

```text
RuntimeCapabilities
  observe_task
  observe_session
  observe_file_mutation
  observe_tool_execution
  observe_model_route
  observe_verification
  deliver_context
  expose_tools
  request_model
  session_lifecycle
  reconnect
  mcp
```

The exact representation should be a small host-neutral DTO/Protocol, not a framework object.

Capabilities are positive declarations. Unsupported capabilities must be explicitly false/unavailable rather than inferred from runtime name.

The Task-aware controller uses capability negotiation as a hard constraint:

```text
requested IntelligencePlan
        |
        v
RuntimeCapabilities
        |
   +----+----+
   |         |
supported  unsupported
   |         |
   v         v
execute   downgrade/fallback
```

Examples:

- runtime supports context delivery -> bounded active context is possible;
- runtime exposes tools but no context injection -> advisory tools only;
- runtime has only MCP -> explicit MCP compatibility mode;
- runtime cannot observe verification -> never claim runtime-confirmed completion from that host;
- runtime cannot observe file mutation -> use a bounded filesystem fallback only in the adapter if measurement justifies it.

## 6. Host-neutral runtime observations

Formalize only observations that Project Intelligence or transparent orchestration actually consumes.

Candidate small contracts:

### TaskObservation

- opaque runtime/session identifier;
- task text/objective when exposed;
- parent/follow-up relationship if exposed;
- referenced files/symbols when observable;
- timestamp/provenance.

### SessionObservation

- runtime session identifier;
- lifecycle state;
- workspace/project reference;
- runtime version/capabilities;
- optional model profile information.

### MutationObservation

- project/workspace;
- changed path(s);
- mutation source category;
- timestamp;
- runtime/source revision when available.

### ToolExecutionObservation

- tool category/name;
- affected paths/refs when safely derivable;
- explicit success/failure only when the runtime provides authoritative status;
- timestamp/provenance;
- no unbounded raw output persistence.

### ModelObservation

- logical model role/profile;
- provider/runtime source;
- token/tool/latency metrics when exposed;
- no provider-specific DTO leakage into Core.

### VerificationObservation

- test/build/lint/typecheck/runtime evidence category;
- current revision identity;
- explicit pass/fail/observed/unavailable status;
- freshness and provenance.

Do not invent values that a runtime does not expose.

## 7. Runtime delivery ports

Observation and action/delivery are separate.

Do not create a single giant `AgentRuntime` interface with dozens of mandatory methods.

Prefer small optional ports/protocols such as:

```text
RuntimeCapabilityProvider
TaskObservationSource
MutationObservationSource
ToolObservationSource
VerificationObservationSource
ContextDeliveryPort
ToolExposurePort
RuntimeHealthPort
```

This allows MCP-only and partially integrated runtimes to implement only the capabilities they actually support.

## 8. OpenCode reference adapter

`adapters/opencode/` remains the reference native adapter.

It may import OpenCode and MCP SDK types. Host-neutral packages may not.

Its responsibilities are:

1. detect/declare OpenCode runtime capabilities;
2. normalize stable OpenCode events/session/tool/model information into host-neutral observations;
3. deliver bounded PI context/tools using supported OpenCode interfaces;
4. own OpenCode-specific watcher/lifecycle/reconnect workarounds;
5. report degraded/unavailable capabilities truthfully;
6. preserve native OpenCode fallback.

It must **not** contain Task-aware business rules such as prompt keyword -> PI capability mappings.

OpenCode-specific watcher behavior, tool metadata quirks and version compatibility remain adapter concerns.

## 9. MCP is a compatibility layer, not a full runtime adapter

MCP is intentionally retained as a durable cross-runtime access surface.

However, MCP alone does not necessarily expose:

- task start/follow-up semantics;
- file mutation lifecycle;
- model route changes;
- tool execution lifecycle;
- verification completion;
- context injection timing;
- session restart/reconnect semantics.

Therefore:

```text
MCP-only compatibility != transparent runtime integration
```

Do not claim Tier 3 transparent PI merely because PI tools are reachable through MCP.

## 10. Relationship to Transparent Task-aware PI

The existing transparent PI architecture remains host-neutral:

```text
Runtime Adapter
  -> TaskSignals / observations
  -> deterministic TaskIntentClassifier
  -> IntelligencePlanner
  -> IntelligencePlan
  -> existing PI capabilities
  -> runtime delivery port
```

Before TA-0 implementation, formalize only the minimum Runtime Contract required by TaskSignalCollector and PlanOutcome telemetry.

Do not delay RV-0 for speculative multi-harness implementation. RV-0 still measures the existing OpenCode reference runtime first.

## 11. Productization sequence integration

This plan modifies the execution sequence as follows.

### RV-0 — OpenCode reference baseline

No change in priority.

- current OpenCode integration;
- local-low/local-practical/host/frontier model matrix;
- lifecycle/adapter gaps;
- benchmark task set;
- baseline gap report.

### RA-0 — Minimal Runtime Contract formalization

Run after RV-0 blocking adapter/provider fixes and **before TA-0 production behavior is implemented**.

Scope:

- inventory exactly which OpenCode data TA-0/TA-1 need;
- reuse existing ProjectRef, Provenance, RuntimeObservation and other contracts where possible;
- add only missing host-neutral runtime capability/observation/delivery contracts;
- architecture tests prohibit OpenCode types/imports outside adapters;
- no second harness implementation;
- no user-visible behavior change.

Exit criteria:

- TaskSignalCollector can consume host-neutral inputs;
- OpenCode adapter maps its relevant signals without Core OpenCode imports;
- missing OpenCode features are represented as unsupported/degraded capabilities;
- existing OpenCode/MCP behavior still passes.

### TA-0 through TA-FINAL

Continue the existing transparent PI rollout using the Runtime Contract.

OpenCode remains the only required Tier-3 runtime for this release baseline.

### RA-1 — OpenCode adapter conformance

This may run during/after TA-FINAL.

Create a reusable conformance suite for native adapters:

- capability declaration truthfulness;
- observation normalization;
- stale/missing status preservation;
- context/tool delivery bounds;
- lifecycle/fallback behavior;
- privacy enforcement;
- no runtime-specific types escaping the adapter.

The OpenCode adapter must pass first.

### RA-2 — MCP compatibility conformance

Prove that the host-neutral PI application remains usable in an MCP-only environment without depending on OpenCode plugin events.

This is not a claim of transparent automation.

### RA-3 — Second-harness proof

Run only after the OpenCode production-capable baseline or as a tightly bounded post-baseline architecture proof.

Select **one** second runtime based on current accessibility, API stability and user value. Candidate families include Codex CLI, Claude Code or Pi, but do not hard-code a choice in the core plan.

The purpose is architectural validation, not broad platform expansion.

Success requires:

- no Project Model/Impact/Context/Verification/Task-controller rewrite;
- only the runtime adapter and genuinely missing generic contract pieces change;
- core architecture tests remain host-neutral;
- at least Tier-1 compatibility and, if hooks permit, a small Tier-2 native observation smoke;
- documented capability matrix versus OpenCode.

If adding the second runtime requires large core changes, treat that as evidence that the Runtime Contract is wrong and revise the generic boundary rather than adding runtime-specific exceptions to Core.

## 12. Do not implement many adapters at once

The following is explicitly deferred:

```text
adapters/codex + adapters/claude + adapters/pi + adapters/other
```

all in one milestone.

Reasons:

- API/runtime surfaces change independently;
- it multiplies validation matrices;
- it can hide whether the generic boundary is actually stable;
- current product value depends on finishing OpenCode productization first.

One second-harness proof is enough to test the abstraction.

## 13. Cross-runtime evaluation

When RA-3 is executed, compare behaviors rather than attempting exact feature parity.

Record:

- runtime/version;
- supported RuntimeCapabilities;
- integration tier reached;
- installation/config effort;
- PI tools available;
- TaskObservation quality;
- mutation/runtime/verification signals available;
- transparent PI level possible;
- fallback behavior;
- task correctness;
- latency/token/tool overhead if comparable.

Do not average unrelated runtime metrics into one product score.

## 14. Critical architectural tests

Add/maintain tests that fail if:

- `src/extendcodeagent/core` imports OpenCode SDK/packages;
- Project Graph/Twin/Impact/Test/Context import runtime adapter types;
- Task-aware business rules live in `adapters/opencode`;
- an adapter declares a capability but silently cannot provide it;
- unavailable runtime status is promoted to verified evidence;
- MCP-only mode is labeled as fully transparent when required observations are absent.

Where practical, add fake runtime adapters to exercise conformance without live runtimes.

## 15. Failure and fallback semantics

Runtime integration failure must degrade safely.

Preferred order:

```text
transparent active
 -> advisory PI
 -> explicit PI/MCP tools
 -> native runtime
```

The adapter must expose the downgrade reason.

A runtime capability failure must never cause:

- false completion;
- fabricated verification;
- privacy override;
- source-code transmission when policy forbids it;
- OpenCode/native runtime unavailability when PI can be bypassed.

## 16. Versioning

The Runtime Contract should be versioned independently of OpenCode adapter versions.

Do not tie Core protocol versions to OpenCode package versions.

Adapters may have compatibility tables such as:

```text
runtime adapter version -> tested harness versions -> supported capabilities
```

but Core should consume capability declarations and host-neutral contract versions.

## 17. Installation strategy

Current productization still optimizes OpenCode installation first.

Future installation should allow:

```text
ExtendCodeAgent core/sidecar
  + chosen runtime adapter(s)
```

without installing dependencies for every supported harness.

Avoid making Claude/Codex/Pi SDK dependencies mandatory for OpenCode-only users.

## 18. Priority policy

Priority order remains:

1. RV-0 and measured OpenCode baseline;
2. blocking OpenCode/frontier/lifecycle fixes;
3. RA-0 minimal Runtime Contract;
4. TA-0 -> TA-FINAL transparent PI on OpenCode;
5. confidence/verification/Runtime Bridge/deep analysis only when evidence requires them;
6. RA-1 OpenCode conformance and RA-2 MCP compatibility proof;
7. RA-3 one second-harness proof;
8. additional harness adapters only when there is demonstrated user value.

Cross-runtime work must not postpone high-value OpenCode correctness or productization fixes.

## 19. Acceptance criteria for architectural independence

The architecture may be described as runtime-independent only when all of the following are true:

- OpenCode-specific imports remain isolated to the adapter;
- runtime capabilities are represented by host-neutral contracts;
- Task-aware controller consumes host-neutral signals;
- PI application can run through MCP-only or fake-runtime paths without OpenCode imports;
- OpenCode passes adapter conformance;
- a second runtime proof uses the same core without substantial core redesign.

Before RA-3, use the more precise wording:

> ExtendCodeAgent is designed as a host-neutral Intelligence Layer with OpenCode as its primary reference runtime.

Do not claim multi-harness production support before it is actually tested.

## 20. Non-goals

Unless separately justified by evidence, this plan does not authorize:

- a new independent coding-agent harness;
- replacing OpenCode;
- patching OpenCode core;
- implementing multiple runtime adapters before OpenCode release validation;
- adding runtime-specific conditionals throughout Core;
- forcing every harness to expose identical capabilities;
- making MCP the sole integration mechanism;
- making cross-runtime support more important than verified coding-task outcomes.

## 21. Codex implementation rule

For each runtime-boundary change Codex must record:

1. measured or architectural need;
2. existing contract/code that can be reused;
3. exact host-specific data crossing the boundary;
4. new generic contract only if necessary;
5. architecture/conformance tests;
6. OpenCode regression tests;
7. capability/fallback semantics;
8. documentation/handoff update.

Do not create abstraction layers with no consumer. RA-0 is justified because TA-0/TA-1 immediately consume the contract; RA-3 supplies the second implementation proof later.

## 22. Final principle

OpenCode is currently the best-supported execution environment for ExtendCodeAgent, but Project Intelligence must outlive any one harness.

The goal is not to support the maximum number of agent runtimes. The goal is to preserve one high-value, well-tested Intelligence Core and attach it to runtimes through the smallest honest adapter required by each environment.
