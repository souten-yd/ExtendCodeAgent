# C2 Context Virtualization and Semantic Working Set Design

Status: **stage-local architecture decision for C2 and the later C3/V/R0 gates**.

This document is **not a second roadmap**. `docs/PI_MASTER_EXECUTION_PLAN.md` remains the canonical
backlog and stage owner. This document refines how the active C2 work must evolve the existing codebase
so that large projects can be handled with a bounded primary-model context without duplicating truth,
storage, planning, runtime or verification subsystems.

Base reviewed for this decision: `main` at `7bab478709d125722e57fd99dd95b784e0ce62c7`.

---

## 1. Product goal

The target product is no longer "a coding agent that can tolerate a very long context". The target is:

> **A host-neutral project-intelligence runtime that virtualizes project knowledge outside the LLM,
> compiles only the minimum semantically complete working set for the current task, and therefore lets
> higher-quality / lower-quantization local coding models work on large repositories with a preferred
> p95 total context around 32k tokens and a supported maximum profile of 64k tokens.**

The repository may be very large. The **single-call primary-model context must not scale linearly with
repository size**. The intended relationship is:

```text
Repository size
    ↓
Digital Twin / Project Truth / Evidence
    ↓
Task + semantic boundaries + obligations
    ↓
Semantic Working Set
    ↓
Context Compiler
    ↓
Primary model call (normally 8k–32k, supported <=64k total)
```

`docs/evaluation/large-project-bounded-context-target-v1.json` remains the machine-readable target:

- supported total primary-model profile: `<= 65,536` tokens including reserved output headroom;
- preferred p95 total: `<= 32,768`;
- preferred p50 total: `<= 16,384`;
- initial evidence envelope target: about `8,192` before targeted expansion;
- correctness and critical-evidence recall are hard gates and outrank compression.

If a task cannot fit in the supported profile without dropping required truth, ECA must **decompose the
task or mark the task class/revision as not yet 64k-capable**. It must never silently truncate critical
evidence to meet the target.

---

## 2. Why long context is currently needed

The root cause is not simply repository size. Long context is often compensating for missing or weak
project-side structure.

| Root cause | Long-context workaround | Project-side replacement |
|---|---|---|
| change location unknown | broad search/read loops | semantic localization + Graph/Twin |
| consumers/impact unknown | read callers/importers broadly | bounded Impact closure |
| callable/API behavior unknown | read implementation bodies | semantic contracts / boundary contracts |
| hidden effects/state unknown | inspect surrounding code and runtime logs | effect/state contract + runtime evidence |
| task progress/decisions forgotten | retain chat history | bounded Task State / plan outcome / decision evidence |
| requirements/design intent unknown | resend docs/history | revision-aware requirement/decision evidence |
| verification scope unknown | read/run large suites | Verification Obligations + Required Verification Set |
| UI/API/backend relation unknown | load frontend and backend broadly | smallest cross-boundary contract/path projection |
| previous evidence forgotten | repeat tools/models | revision-scoped evidence reuse / memory |
| exact answer fields copied incorrectly | give the model more context | AnswerIR / deterministic projection |

The current B0b evidence is consistent with this diagnosis: required facts were present in 20
`PROJECTION_SCHEMA_ERROR` cells while the final exact projection was still wrong, and full prompt
context reached 93,189 tokens. `pi_symbol` and `pi_context` dominated serialized PI payload size.
The first task is therefore **better knowledge representation and delivery**, not simply a smaller
Top-K.

---

## 3. Current implementation inventory and reuse ruling

### 3.1 Keep and extend: one truth substrate

The following existing owners are authoritative and must be reused.

| Existing owner | Current responsibility | Ruling for this design |
|---|---|---|
| `graph/contracts.py` | immutable nodes, edges, evidence, revision facts | **reuse** as structural/semantic fact substrate |
| `twin/lifecycle.py` | source snapshot -> immutable revisioned Graph | **reuse** as revision/invalidation owner |
| `analysis/*` | paths, references, Impact closure | **reuse** for semantic working-set expansion |
| `verification/*` | `SemanticChangeSet`, `VerificationObligation`, required set | **reuse** as obligation model; do not create another obligation type system |
| `runtime/*` | runtime observations and runtime signal collector | **reuse**; no second runtime evidence store |
| `traceability/*` | requirement-to-project evidence | **reuse** for requirement obligations/contracts |
| `orchestration/*` | `TaskSignals`, `TaskIntent`, `IntelligencePlan`, C1 shadow plan | **reuse** as task/capability/depth plan source |
| `blueprint/*` | immutable planned project elements | **reuse** for large/greenfield decomposition where justified |
| `convergence/*` | target/actual/verification comparison | **reuse** for completion/progress state instead of a parallel task-completion engine |
| `storage/sqlite.py` | shared durable revision store | **reuse/extend only when persistence is justified** |
| `evaluation/trace.py` | append-only evaluation attribution | **reuse** for evidence-delivery evaluation; do not make it Project Truth |
| `context/*` | bounded context request/package today | **refactor/expand** into the Context Compiler / Semantic Working Set owner |
| `service/application.py` | host-neutral public application facade | **keep facade, reduce domain logic growth** |

### 3.2 Explicit non-duplication rules

Do **not** add any of the following parallel systems:

- `ContractStore` separate from Graph/Twin;
- `RuntimeMemoryStore` separate from runtime observations;
- `RequirementGraph` separate from Traceability/Graph;
- `TaskPlannerV2` separate from Orchestration + Blueprint/Convergence;
- `VerificationObligationV2` separate from `verification/contracts.py`;
- a second SQLite database for context/memory;
- a repository-wide permanent CFG/DFG/UI graph merely to reduce context;
- an LLM-generated "project truth summary" used as authority.

New objects introduced by C2 must be **projections, indexes, envelopes or cacheable views over the
existing truth substrate**, not competing truth owners.

---

## 4. Current code gaps

### 4.1 `context` is too shallow for the target

The production `ContextRequest`/`ContextItem`/`ContextPackage` model is revision aware, but it has no
stable evidence identity, role, obligation coverage, dependency requirements, contradiction markers,
protected-truth semantics, or evidence-gap states.

`build_context()` currently:

1. takes a `GraphSnapshot`;
2. filters only by confidence;
3. sorts target refs first, then confidence;
4. estimates tokens from short strings;
5. packs items until token/max-item limits.

That is useful as a PR-E baseline but cannot implement minimum **semantically sufficient** context.
It may select high-confidence but task-irrelevant nodes and may omit a low-volume mandatory relation.

### 4.2 C1 plans are useful but not a durable task system

`TaskSignals` and `IntelligencePlan` already provide task objective, target/ref signals, capability
selection, context scope/budget, evidence needs and escalation conditions. These must remain the
entrypoint.

Do not introduce another generic task classifier. If durable task decomposition becomes necessary for
large/greenfield work, project the decomposition from existing Blueprint/Convergence concepts and add
only the missing execution-state projection.

### 4.3 Twin is structurally strong but semantically incomplete

Twin correctly owns source revision identity, analyzer versions, refresh selection and invalidation.
It currently carries mostly file/module/symbol/import/reference/call-style facts. For bounded context,
Twin needs richer **boundary facts** and **contract projections**, but those should still be emitted as
Graph facts by analyzers and versioned by the same Twin lifecycle.

### 4.4 `ProjectIntelligenceApplication` is already a large facade

`src/extendcodeagent/service/application.py` is the public application boundary and currently imports
nearly every domain. C2 must **not** place the working-set algorithm, contract extraction, coverage
optimizer, task-state persistence or memory invalidation logic directly into this facade.

The facade may:

- resolve policy/config;
- load the current Twin snapshot;
- invoke domain services;
- serialize bounded results;
- keep request-local timing/cache ownership.

Domain behavior belongs in `context`, `analysis`, `verification`, `twin`, `runtime`, etc.

---

## 5. Target architecture

```text
                         Agent Runtime / OpenCode
                                  │
                                  ▼
                         TaskSignals / Plan (C1)
                                  │
                                  ▼
                       Semantic Working Set Request
                                  │
             ┌────────────────────┼────────────────────┐
             ▼                    ▼                    ▼
       Project/Twin Truth   Verification Obligations   Task/Decision State
             │                    │                    │
             ├──── Contract / boundary projections ───┤
             │                    │                    │
             ▼                    ▼                    ▼
                         Evidence Candidate Union
                                  │
                                  ▼
                         EvidenceAtom projection
                                  │
                         protected truth first
                                  │
                                  ▼
                     Coverage / dependency optimizer
                                  │
                                  ▼
                         Semantic Working Set
                                  │
                         Sufficiency Gate
                           │             │
                     sufficient      evidence gap
                           │             │
                           │       targeted page-in only
                           │             │
                           └──────┬──────┘
                                  ▼
                            ChangeCapsule
                                  │
                                  ▼
                         Context Compiler
                                  │
                                  ▼
                    primary coding model 8k–32k target
                                  │
                                  ▼
                  AnswerIR / code change / Verification
                                  │
                                  ▼
                       revision-matched evidence
```

The project repository and Twin can be large. The model-visible working set is bounded and replaceable.

---

## 6. Core design concepts

### 6.1 Semantic Contract Projection

A semantic contract is not a new truth store. It is a deterministic projection over existing Graph
facts, source syntax and runtime/verification evidence.

Minimum useful contract fields depend on the entity kind but may include:

```text
identity / canonical_ref
entity kind
source_ref + Twin revision
visibility / exported-public boundary
inputs / parameter types when declared
outputs / return/schema type when declared
preconditions when mechanically derivable
postconditions when mechanically derivable
exceptions / error channel when statically observable
reads state / writes state
declared or observed external effects
calls / called-by boundary refs
API/event/schema bindings
requirements covered
verification obligations/providers
confidence + provenance
```

Rules:

- lack of a field is `unknown`, never invented;
- LLM inference may be advisory evidence but never declared Project Truth;
- runtime-observed effects remain `observed` unless stronger verification exists;
- exact static facts retain their language analyzer provenance.

### 6.2 Semantic ABI / Contract Fingerprint

For a public/boundary entity, compute a deterministic fingerprint over the **known contract surface**,
not the implementation body.

Purpose:

- distinguish implementation-only changes from boundary changes;
- stop impact/context propagation at a proven unchanged boundary;
- invalidate only dependent contract/evidence slices when a boundary changes.

The fingerprint must include a schema/version and the set of known/unknown contract components. A
missing fact becoming known is a fingerprint change. Do not use a hash to hide uncertainty.

Example conceptually:

```text
contract_fingerprint = hash(
  producer_version,
  canonical_ref,
  visibility,
  declared inputs,
  declared output,
  declared/observed effect classes,
  API/schema/event bindings,
  uncertainty markers
)
```

An unchanged fingerprint is evidence that the **modeled boundary** is unchanged. It is not proof that
all runtime behavior is unchanged.

### 6.3 Semantic Working Set

The Semantic Working Set is the current task's bounded, evidence-backed view of the project.

It is **not** persisted as truth. It is reproducible from:

- `TaskSignals` / `IntelligencePlan`;
- current Twin revision;
- target refs and contract boundaries;
- Impact closure;
- `VerificationObligation`s;
- runtime and requirement evidence;
- valid task/decision memory;
- configured context profile.

A working set contains only evidence that:

1. satisfies an active obligation;
2. is a dependency needed to interpret such evidence;
3. is uncertainty/contradiction that must be visible;
4. is optional support selected under the remaining budget.

### 6.4 EvidenceAtom

C2 should add one small projection contract in the existing `context` package. It should reference
existing truth; it must not duplicate it.

Required fields:

```text
evidence_id                 stable within truth/revision semantics
canonical_ref               when applicable
source_ref                  when applicable
revision                    exact Twin/source revision
provenance
fact/relation kind
role                        required/supporting/uncertain/contradictory/historical
confidence/freshness
obligation_ids              zero or more existing obligation IDs
depends_on_evidence_ids     minimum interpretation dependencies
estimated_token_cost
status
compact payload             consumer-oriented, not raw Graph serialization
```

Protected evidence is any atom required by an obligation, contradiction, uncertainty boundary,
revision/freshness check, or verification gap. Protected evidence cannot be ranked away for cost.

### 6.5 Evidence Gap

Use machine states rather than asking the model "do you have enough context?".

Reuse and extend the existing C2 taxonomy:

```text
MISSING_SYMBOL
REFERENCE_INCOMPLETE
IMPACT_INCOMPLETE
CONTRACT_INCOMPLETE
PUBLIC_BOUNDARY_UNCERTAIN
REQUIREMENT_UNMAPPED
VERIFICATION_UNCOVERED
RUNTIME_UNOBSERVED
CONTRADICTORY_EVIDENCE
STALE_EVIDENCE
INTENT_UNCERTAIN
WORKING_SET_OVERFLOW
```

Each gap names the responsible capability/scope and determines the next targeted expansion.

### 6.6 ChangeCapsule

A ChangeCapsule is the compiled handoff to the primary model for an edit/design step. It reuses the
working set and does not own truth.

Conceptual contents:

```text
task objective / current subtask
current revision
change targets
current semantic contracts
desired contract delta when known
must-preserve invariants
impact boundary / affected consumers
unresolved questions only
required verification obligations/providers
selected evidence IDs
small source excerpts only where implementation is required
```

Exact IDs, paths, tests, enum values and other already-known structured outputs should be bound through
AnswerIR/ChangeIR rather than copied from large prose by the model.

### 6.7 Context Compiler

Refactor the current `context` domain into a compiler-like pipeline while keeping backward
compatibility during migration.

```text
ContextRequest (legacy/simple API)
        │
        └── compatibility adapter

WorkingSetRequest
  -> CandidateProjector
  -> EvidenceAtomProjector
  -> ProtectedEvidenceResolver
  -> CoverageOptimizer
  -> SufficiencyChecker
  -> WorkingSetEnvelope
  -> ChangeCapsule / AnswerIR
  -> serializer for host/model
```

Do not create a single huge `ContextCompiler` class containing every concern. Keep small deterministic
services/functions with immutable contracts and compose them in the application service.

---

## 7. Contract extraction by language

### 7.1 Python first

Extend the existing Python `GraphAnalyzer`; do not build a second parser.

High-value facts, only when statically supported:

- function/method parameter names and declared annotations;
- return annotation;
- class inheritance and decorators already known by the analyzer;
- module/package export evidence when resolvable;
- raised exception types when direct syntax supports them;
- obvious state write classes (`self.x=`, module/global assignment) as inferred facts;
- obvious I/O/effect calls only through a bounded, explicit rule registry with low/medium confidence;
- Pydantic/dataclass/schema fields when mechanically recognizable;
- framework route/schema bindings only as separate analyzer facts with explicit version/provenance.

Do not infer arbitrary pre/postconditions with an LLM and persist them as truth.

### 7.2 JavaScript / TypeScript

Extend the existing tree-sitter JS/TS analyzer and reuse its canonical-ref rules.

Prioritize:

- exported functions/classes/types;
- parameter/return type syntax where present;
- imported/exported boundary bindings;
- event handler relation when syntax is explicit;
- fetch/client call target when statically literal/resolvable;
- route/schema bindings only through small framework-specific adapters that emit generic Graph facts.

### 7.3 HTML/CSS

HTML is currently outside `KNOWN_ANALYZERS`. Do **not** implement a full DOM/UI graph preemptively.

First evaluate the current ECA on static-web/full-stack tasks. If the dominant root cause is
`HTML_STRUCTURE_MISSING` or `SELECTOR_RELATION_MISSING`, add the smallest analyzer using the same
`GraphAnalyzer` protocol. Initial useful facts are:

- element IDs/classes;
- `<script src>` / stylesheet references;
- form action/method;
- link/href relations;
- `data-*` attributes when referenced by JS;
- static selector bindings.

The goal is cross-boundary contracts, not full persistent DOM state.

---

## 8. Task state and decomposition

Long context also acts as accidental task memory. ECA should move only the necessary task state out
of the conversation.

### 8.1 Do not build another planner first

Reuse:

- C1 `TaskSignals` / `TaskIntent` / `IntelligencePlan` for intent and minimum capability/depth;
- Blueprint for large planned structure;
- Convergence for target-vs-actual-vs-verification progress;
- Verification Obligations for required checks.

### 8.2 Add only the missing execution-state projection

If C2/C3/greenfield evaluation shows that session history is required merely to remember execution
progress, add a small revision-aware `TaskExecutionState` projection, not a new autonomous task engine.

Minimum fields:

```text
task_id / parent_task_id
project/workspace/revision
objective fingerprint
current step/state
input obligations
output obligations
target refs
must-preserve constraints
completed evidence IDs
open Evidence Gaps
required verification IDs
decision refs
freshness / invalidation reason
```

A Task DAG is justified only for tasks whose semantic working set would exceed the supported profile
or whose independent outputs have explicit contracts. Decomposition must have typed input/output
contracts so subtasks can be reasoned about independently.

---

## 9. Project memory

Memory has high potential for long-horizon context reduction but also high stale-truth risk.

### 9.1 Memory classes

Use one revision/invalidation model and keep the classes distinct:

1. **Structural memory** — derived project contracts/architecture facts; normally regenerated from
   Graph/Twin and not stored as free-text memory.
2. **Evolution/decision memory** — reviewed decisions, migration rationale, requirement mappings,
   known compatibility constraints.
3. **Task/episodic memory** — bounded execution state, failed approaches, remaining obligations.
4. **Verification evidence memory** — existing revision-scoped executed evidence and future reusable
   segments; owned by the V/P0 design, not a generic chat-memory subsystem.

### 9.2 Persistence rule

Persist only when there is a clear invalidation key and consumer. Every durable entry must bind to:

```text
project/workspace
source/Twin revision or dependency closure
provenance
producer/version
freshness policy
invalidation reason/state
```

Natural-language summaries without source/evidence identity are advisory at most.

### 9.3 Storage ruling

Prefer extending the shared SQLite owner/repositories when a durable object is accepted. Do not add a
vector database merely because semantic retrieval is convenient. Embeddings may later index optional
supporting memory, but never become the authority or freshness mechanism.

---

## 10. Context virtualization / semantic paging

Model context is treated as a volatile cache, not project storage.

### 10.1 Working-set tiers

Use adaptive budgets as profiles, not correctness caps:

| profile | typical purpose |
|---|---|
| ~8k | locate / narrow / mechanical or small change |
| ~16k | normal single-subsystem change |
| ~24k | multi-file impact/verification task |
| ~32k | preferred large-project primary-model p95 target |
| ~48k | complex cross-boundary/architecture task |
| <=64k total | supported single-call maximum profile |

If mandatory evidence does not fit, the compiler should first:

1. remove optional/supporting redundancy;
2. replace raw facts with contract projections;
3. bind exact structured fields through AnswerIR/ChangeIR;
4. split independent reasoning/edit obligations into contract-bounded subtasks;
5. page in only the unresolved dependency neighborhood.

It should **not** globally increase every capability depth or resend all prior tool output.

### 10.2 Shadow reservoir

Evidence outside the current envelope remains addressable by ID and lightweight metadata. A model or
validator can request expansion of a named gap/evidence neighborhood. `not delivered` never means
`forgotten by ECA`.

### 10.3 Context Debt

Add a diagnostic metric:

> **Context Debt = model-visible tokens that cannot be attributed to an active task obligation,
> evidence dependency, uncertainty/contradiction requirement, implementation excerpt, or required
> control metadata.**

Do not initially make an arbitrary Context Debt percentage a release gate. Measure it by task class,
then use it to find serialization/selection waste. A large reduction with equal quality is a valid
multi-objective PI effect.

---

## 11. Verification integration

Verification is part of the working-set definition, not an afterthought.

For a code change:

```text
SemanticChangeSet
  -> ImpactReport
  -> VerificationObligations / RequiredVerificationSet
  -> protected evidence in Working Set
  -> ChangeCapsule required checks
  -> execution owned by host/runtime
  -> revision-matched evidence
  -> Convergence/completion decision
```

The model must not have to rediscover which tests matter from raw repository context when ECA already
has a required set. Conversely, a required verification obligation that is unresolved must block
`SUFFICIENT` even if the code context fits 8k.

---

## 12. Quantization and model-resource strategy

ECA should not hardcode quantization formats. The product-level goal is to make context compact enough
that the operator can spend memory on **better model weights / less aggressive quantization / larger
model quality** instead of extremely long KV cache.

The runtime/model profile should expose, where available:

- supported context limit;
- reserved output headroom;
- model tier/capability;
- backend max parallel;
- observed or estimated KV/context memory;
- optional model-quality profile metadata supplied by the host.

ECA uses this to compile a safe working set and optionally produce resource/concurrency hints. The
runtime/backend owns model loading, quantization selection and scheduling.

A context reduction is not a product win if it requires an auxiliary model that consumes the freed
VRAM, causes primary-model eviction/reload or lowers final coding quality.

---

## 13. Refactoring and maintainability plan

### 13.1 Refactor `context` in place

Preserve the existing public PR-E contracts long enough for compatibility tests, but stop growing the
simple node-packing algorithm.

Recommended internal structure as C2 implementation grows:

```text
src/extendcodeagent/context/
  contracts.py          existing + bounded C2 projection contracts
  service.py            thin compatibility facade / composition entrypoint
  evidence.py           EvidenceAtom projection and protected-evidence rules
  coverage.py           deterministic obligation/dependency coverage optimizer
  sufficiency.py        Evidence Gap / Sufficiency checker
  compiler.py           Semantic Working Set -> model-visible envelope
  projection.py         AnswerIR/ChangeIR exact-field binding
```

This is a suggested decomposition threshold, not permission to create empty modules in advance. Split
only when production code exists and tests show a cohesive responsibility.

### 13.2 Keep `ProjectIntelligenceApplication` thin

Do not append large C2 algorithms to `service/application.py`.

When C2 introduces behavior, application methods should be approximately:

```text
load/reuse snapshot
build/obtain current plan
invoke context-domain compiler
serialize result
record timing/diagnostics
```

If repeated orchestration appears in multiple application methods, extract one domain/application
service rather than duplicate the sequence.

### 13.3 Reuse the existing analyzer protocol

Contract/boundary facts must extend `GraphAnalyzer` / `CompositeGraphAnalyzer` or a compatible
language-owned analyzer extension. Do not parse Python/JS/TS again in Context code.

### 13.4 Reuse the existing store

Do not create another database. If contract indexes, decision memory or task execution state becomes
accepted durable product state, add a focused repository/table behind the current storage owner and
preserve workspace/revision isolation.

### 13.5 Refactor touched large evaluation code opportunistically, not speculatively

`tools/local/evaluation_runner.py` is large and should not absorb C2 product algorithms. If C2 changes
require repeated evaluation-runner logic, split only the touched concerns (schedule/workspace/provider/
trace/result aggregation) with exact regression tests. Do not perform a risky whole-runner rewrite in
the same PR as Project Truth/context behavior changes.

### 13.6 Duplication check before every new type/function

Before adding a contract or algorithm, search at least:

```text
core/contracts.py
context/
orchestration/
verification/
convergence/
blueprint/
runtime/
traceability/
graph/
storage/
evaluation/
```

For each proposed type record one disposition:

- `REUSE` existing exact owner;
- `EXTEND` existing contract/service;
- `PROJECT` a consumer-specific immutable view;
- `CONSOLIDATE` duplicate existing behavior;
- `NEW` only when no existing owner can satisfy the contract cleanly.

Code review must reject unexplained `NEW` decisions.

---

## 14. Implementation sequence inside existing stages

This does not create new Master Plan stages.

### C2-1 — attribution first

Implement/finish the existing C2 attribution chain:

```text
available -> selected -> delivered -> used -> projected -> verified
```

Add long-context root-cause labels so future fixes are targeted rather than assumed.

### C2-2 — EvidenceAtom and obligation projection

Project Graph/Twin/Impact/Verification/Runtime/Traceability facts into bounded atoms. Reuse existing
`VerificationObligation` IDs and revision identities.

### C2-3 — semantic contract extraction in shadow

Add only high-confidence Python and current JS/TS contract facts needed by the evaluation tasks.
Measure precision/recall and context benefit before expanding language/framework scope.

### C2-4 — AnswerIR/ChangeIR and exact projection

Target the measured projection/schema failures first. Exact known fields are deterministically bound to
evidence IDs; the model handles unresolved reasoning/code only.

### C2-5 — sufficiency and evidence-gap gate

Prevent false completion, identify the exact missing capability/scope, and trigger bounded expansion.

### C2-6 — Semantic Working Set / Context Compiler

Replace confidence-only packing with protected obligation coverage + dependency closure + optional
budget optimization. Retain a compatibility path for current `ContextRequest` until consumers migrate.

### C2-7 — contract-boundary propagation and semantic ABI experiment

Measure whether unchanged modeled public contracts allow Impact/context expansion to stop safely. Keep
this shadow/advisory until false-negative risk is bounded.

### C2-8 — compression curve

On same-head compatible tasks run the required context curve:

```text
8k / 16k / 24k / 32k / 48k / 64k
```

Record actual total primary-model context including output headroom, not only PI envelope size.

### C2-9 — task state / memory only if still needed

If repeated context remains dominated by conversation/task-progress reconstruction, add the smallest
revision-aware TaskExecutionState/evolution memory projection using the existing persistence and
invalidation model. Do not pre-build a generic memory platform.

### C3 and later

C3 may automatically apply only the C1 planning and C2 working-set mechanisms that survive held-out
quality/effect evaluation. X0 cross-boundary work begins only when correct delivery still leaves a
truth gap. V-series and R0 prove verification/reuse and the final bounded-context claim.

---

## 15. Evaluation contract

### 15.1 Hard quality gates

No bounded-context mechanism is accepted if it causes an unacceptable regression in:

- task/oracle correctness;
- critical evidence recall;
- mandatory obligation coverage;
- projection fidelity;
- false-sufficient rate;
- stale/conflicting evidence retention;
- required verification coverage;
- workspace/revision identity.

### 15.2 Context goals

For large-project-capable claims:

- **required maximum supported single-call profile:** total `<=64k`;
- **preferred p95 target:** total `<=32k`;
- **preferred p50 target:** total `<=16k`;
- smaller is better only on the quality non-inferiority frontier.

If the existing full/current path exceeds these targets but the new compiler fits them with equal
quality, that is a **positive Project Intelligence effect even if final PASS rate is unchanged**.

### 15.3 Root-cause attribution

Every failed bounded-context cell should classify the earliest responsible stage where observable:

```text
TRUTH_MISSING
CONTRACT_MISSING
SELECTION_MISSING
DELIVERY_MISSING
UTILIZATION_MISS
PROJECTION_SCHEMA_MISS
REASONING_MISS
VERIFICATION_MISS
TASK_DECOMPOSITION_MISS
MEMORY_STALE
WORKING_SET_OVERFLOW
MODEL_CAPABILITY
RUNTIME_BOUNDARY
```

### 15.4 Required measurements

At minimum:

- task/oracle result;
- critical/mandatory evidence coverage;
- evidence availability/selection/delivery/utilization/projection recall;
- total primary-model context p50/p95/max;
- PI envelope tokens/serialized size;
- Context Debt tokens/ratio;
- expansion count and reason;
- number of distinct source excerpts/files delivered;
- model/tool calls;
- prefill/cache metrics when observable;
- wall time;
- peak RAM/VRAM/KV when observable;
- model reload/eviction/OOM count;
- task/workspace/revision identity errors;
- contract-fingerprint precision/false-stop incidents when that experiment is active.

---

## 16. Large-project and greenfield behavior

### Existing large project

Normal path:

```text
Task -> locate target -> contract/impact closure -> obligations -> bounded working set -> edit -> verify
```

Repository size alone must not expand context.

### Greenfield / near-empty project

There is little Project Truth initially. Reuse Blueprint/Strategy/Convergence for requirement and
architecture decomposition. As code appears, Twin/Graph/contracts become the substrate. Do not force
Graph/Impact features to pretend useful facts already exist.

### Long-horizon evolution

Persist only reviewed/verified decision/task/evidence state whose invalidation is defined. A new
session reconstructs the current Semantic Working Set from project state rather than replaying the
full previous conversation.

---

## 17. Rejected / deferred alternatives

### Reject: repository-wide always-on CFG/DFG/UI graph

Too expensive and not shown to solve the measured projection/context problem. Use on-demand analysis
only after a repeated root-cause signal.

### Reject: pure embedding/RAG as the primary context selector

Similarity does not guarantee obligation/dependency coverage or freshness. Embeddings may later rank
optional evidence only.

### Reject: LLM-generated project summaries as durable truth

They are difficult to invalidate precisely and can create a second, stale semantic reality.

### Reject: OOP/class boundaries as the only decomposition rule

Encapsulation is useful, but real systems cross functions, APIs, events, schemas, state and runtime
boundaries. Use semantic contracts and effects, not class membership alone.

### Defer: general autonomous Task DAG engine

Only add durable task decomposition when bounded-context evaluation shows it is needed beyond existing
Orchestration/Blueprint/Convergence.

### Defer: learned/LLM reranker

Deterministic coverage and contract projections must establish the baseline first. Optional evidence
ranking is a later measured optimization.

---

## 18. Definition of done for this architecture direction

This direction is considered proven only when all of the following are demonstrated on held-out and
large-project workloads:

1. Project size does not cause proportional primary-model context growth.
2. Current/full and bounded/compiler paths have comparable truth coverage and required verification.
3. The supported large-project path never exceeds 64k total primary-model context.
4. p95 around 32k is achieved for the declared task classes without quality regression.
5. A material portion of saved context comes from project-side contracts/working-set selection rather
   than merely truncating outputs.
6. At least one local model can use the saved memory budget for a higher-quality / less aggressive
   quantization profile without operational regression; model-loading policy remains runtime owned.
7. Task/session changes do not require replaying full conversation history to recover project truth,
   open obligations or revision identity.
8. Stale memory/contract/evidence is invalidated or clearly degraded.
9. No competing truth store or duplicate task/verification/runtime system has been introduced.
10. The winning implementation remains understandable: domain services are cohesive, application and
    adapter layers stay thin, and rejected mechanisms are removed or left off rather than accumulated.

Until these gates pass, describe 32k/64k as an engineering target, not a proven product guarantee.
