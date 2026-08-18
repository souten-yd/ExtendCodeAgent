# C2 Evidence Delivery Decision

Status: stage-local architecture decision for the active C2 work. This is not a parallel roadmap; stage order remains owned by `docs/PI_MASTER_EXECUTION_PLAN.md`.

## Problem statement

B0b showed two different failure classes that must not be conflated:

- Project Intelligence may fail to contain the required truth.
- Project Intelligence may contain the required truth, yet the model can still ignore, misread, over-generalize, or project it into the wrong output schema.

The second class is currently material: B0b recorded 20 `PROJECTION_SCHEMA_ERROR` cells where required PI facts were present, plus 16 `AGENT_REASONING_ERROR` cells. At the same time, request context was much larger than the C1 minimum plans and `pi_symbol`/`pi_context` dominated serialized PI output.

Context compression is therefore treated as both an efficiency mechanism and a possible reliability mechanism. Reducing irrelevant, duplicated, weakly related, or verbose evidence can reduce attention dilution, position effects, conflicting cues, copying mistakes, schema overload, and unnecessary model/tool loops. This is a hypothesis to measure, not permission to prune required truth. Compression that loses critical evidence is a regression even when it is faster.

## Decision

C2 implements a deterministic-first **Evidence-to-Answer Pipeline** inside existing context/orchestration/trace components. It must optimize for minimum sufficient context, not minimum context.

The pipeline is:

```text
TaskSignals
  -> C1 TaskIntent / IntelligencePlan
  -> Project Truth candidate union
  -> EvidenceAtom + Task Obligation projection
  -> protected mandatory evidence
  -> deterministic coverage optimizer
  -> role-budgeted Evidence Envelope
  -> Sufficiency Gate
       -> targeted expansion only for explicit Evidence Gaps
  -> AnswerIR / ChangeIR
  -> primary task/coding model only for genuinely unresolved reasoning/code work
  -> Evidence Utilization / Projection Gate
  -> deterministic rendering / verification
```

The host's primary coding model remains the main code-generation/design/reasoning engine. ECA should not add extra model work for search, narrowing, ranking, copying or schema construction unless an evaluated auxiliary-model component proves that its quality gain is worth its operational cost.

## Failure taxonomy and attribution

Every C2 evaluation should attribute failure as far through the pipeline as observable:

1. `TRUTH_MISSING` — required fact is absent from Project Truth/candidate union.
2. `SELECTION_MISSING` — fact exists but was not selected into the evidence set.
3. `DELIVERY_MISSING` — selected fact was not delivered within the model-visible envelope.
4. `UTILIZATION_MISS` — fact was delivered but required output did not cite/use it.
5. `PROJECTION_SCHEMA_MISS` — fact was used or available but deterministic/model projection is wrong.
6. `REASONING_MISS` — evidence was available, selected, delivered and used but unresolved reasoning is wrong.
7. `VERIFICATION_MISS` — an incorrect result escaped the completion/verification gate.

This attribution is more important than a single aggregate PI score because it determines whether to improve Graph/Truth, evidence selection, delivery, model reasoning, or verification.

## EvidenceAtom and obligations

C2 should project existing Graph/Twin/Impact/Test/Runtime/Traceability facts into bounded `EvidenceAtom`-like records rather than add a second truth store. Each atom should carry only fields required by a consumer, such as:

- stable evidence ID / canonical ref;
- workspace/revision identity;
- provenance and freshness;
- role (`required`, `supporting`, `uncertain`, `contradictory`, `historical`);
- relation/fact kind;
- confidence;
- estimated serialization/token cost where observable;
- obligations covered;
- dependencies required for interpretation;
- contradiction/staleness markers.

Task obligations are derived deterministically from the C1 plan and existing verification/impact contracts. A ranker never creates obligations and never upgrades evidence to Project Truth.

## Never rank away required truth

Evidence selection has two classes:

- **Protected evidence**: required by a task obligation, dependency closure, mandatory requirement, explicit uncertainty/contradiction, or verification gap. It bypasses ranking and cannot be pruned merely for token cost.
- **Optional/supporting evidence**: eligible for deterministic cost/coverage optimization and, later, ranking/reranking.

A fixed Top-K policy is forbidden for protected evidence.

## Deterministic coverage optimizer

Treat context construction as a constrained evidence-coverage problem rather than a pure relevance-ranking problem.

Runtime selection should use a cheap deterministic heuristic over existing facts, preferring evidence that covers currently uncovered obligations at lower serialization cost while preserving structural importance, provenance, freshness, confidence, runtime confirmation, verification relevance and diversity.

Offline/evaluation tooling may compute a stronger reference solution (for example weighted set cover / integer optimization) to estimate how close the runtime heuristic is to a minimum sufficient evidence set. The expensive reference solver is not a production dependency.

Ranker score is subordinate to structural/verification requirements. Semantic similarity must never override an explicit dependency, required verification obligation, contradiction, or runtime-confirmed relation.

## Role budgets and redundancy

Do not allocate all tokens through a single relevance queue. The Evidence Envelope should reserve budget by evidence role when applicable:

- mandatory facts / exact IDs / direct relations;
- impact/dependency closure;
- verification obligations/tests;
- requirement/runtime evidence;
- uncertainty/contradiction;
- supporting redundancy;
- optional ranked evidence;
- small expansion reserve.

Useful redundancy is permitted when independent evidence (for example static + runtime) materially improves reliability. Context compression should remove accidental duplication, not independent confirmation.

## Sufficiency Gate and targeted expansion

The model is not asked whether context is sufficient. C2 adds a deterministic gate using existing plan/evidence signals. Example machine states include:

- `SUFFICIENT`;
- `MISSING_SYMBOL`;
- `REFERENCE_INCOMPLETE`;
- `IMPACT_INCOMPLETE`;
- `REQUIREMENT_UNMAPPED`;
- `VERIFICATION_UNCOVERED`;
- `RUNTIME_UNOBSERVED`;
- `CONTRADICTORY_EVIDENCE`;
- `STALE_EVIDENCE`;
- `INTENT_UNCERTAIN`.

Only the capability/scope responsible for the unresolved state expands. Do not globally raise every capability depth. C1's context budgets are initial budgets, not hard caps; difficult tasks may expand while easy tasks stay small.

A false `SUFFICIENT` decision is a high-severity C2 failure and must be measured explicitly as `false_sufficient_rate`.

## AnswerIR / ChangeIR and deterministic projection

When PI already knows an exact path, symbol, canonical ref, selected test, requirement mapping, enum, boolean, or other structured field, the primary task model should not be required to regenerate or copy it from a large payload.

C2 should introduce the smallest typed intermediate representation needed by measured tasks:

- `AnswerIR` for exact-answer/projection tasks;
- `ChangeIR` only where coding tasks need explicit target files/symbols, must-preserve constraints, required tests/obligations and unresolved design decisions.

Resolved fields are bound directly to evidence IDs and rendered deterministically. The primary task model receives only unresolved reasoning/code slots plus the evidence needed for those slots. Do not turn this into a new planning framework or parallel truth store.

## Evidence Utilization / Projection Gate

For structured tasks, completion must be checked against required output obligations and evidence IDs before it is accepted.

Record, where measurable:

- evidence availability recall;
- evidence selection recall;
- evidence delivery recall;
- evidence utilization recall;
- projection fidelity;
- task/oracle success.

If a required field/evidence obligation is missing from the result, perform a bounded repair using only the missing obligation and its relevant evidence. Do not reread or resend the whole repository/context by default. A bounded repair may invoke the primary task/coding model again when genuine reasoning or code synthesis is needed; that is normal task work, not an auxiliary-model dependency.

This gate directly targets the observed case where correct PI facts are present but the model misses or misprojects them.

## Context Shadow Reservoir

Evidence not selected into the current model envelope remains addressable by ID and lightweight metadata; it is not deleted from Project Truth. If validation exposes a new Evidence Gap, promote only the relevant reservoir evidence or expand its neighborhood. `not in context` must never mean `forgotten by ECA`.

## Ranker / reranker policy

Ranker/reranker is optional and begins in shadow mode after the deterministic bounded baseline exists.

Preferred order:

1. deterministic structural/obligation filter;
2. cheap lexical/embedding ranking only if it adds measurable value;
3. small cross-encoder reranker for optional evidence only;
4. an LLM ranker only for a narrowly defined unresolved ambiguity where cheaper methods fail and measured quality improvement justifies its operational footprint.

A reranker may order or allocate optional budget but may not remove protected truth or create Project Truth.

Before adoption, evaluate at least critical-evidence recall, required-evidence/obligation coverage, critical miss rate, task success, projection fidelity, context size, wall time and resource cost. For a learned/LLM reranker also record setup/startup time, model/API availability, RAM/VRAM residency or peak use where observable, and whether it competes with the primary coding model for accelerator memory. A reranker that saves context but lowers correctness or creates disproportionate operational cost is rejected.

## Model-use policy: primary coding model vs auxiliary PI model

There are two different model roles and they must not be conflated.

### Primary task/coding model

The OpenCode task model (for example the configured Qwen coding model) performs code generation, design, repair and genuinely model-required reasoning. It is expected to be used normally and may be called as often as the task or sealed evaluation contract requires. C2 should make those calls **better supplied and less distracted**, not artificially suppress them. Avoid duplicate/redundant work when deterministic evidence or compatible prior results already resolve the same question, but do not sacrifice useful coding/reasoning quality merely to minimize the number of primary-model calls.

### Auxiliary PI model

An auxiliary PI model is an additional inference dependency introduced by ECA for classification, ranking/reranking, summarization, schema projection, judging/validation, planning, or similar support functions. These models are undesirable by default because they can require extra API/provider setup, model downloads/startup, RAM/VRAM residency, accelerator contention with the primary coding model, latency and operational maintenance.

Default: **no auxiliary PI model** when deterministic methods can satisfy the same contract.

A fast/small auxiliary model can still be appropriate when its measured operational footprint is small enough and it materially improves quality or enables a better accuracy/context/latency tradeoff. The decision is empirical, not ideological.

Adoption rule for an auxiliary PI model:

- establish a deterministic/non-LLM baseline first;
- freeze task/oracle/corpus and the adoption rule before comparison;
- compare deterministic vs auxiliary-model-assisted variants on tuning + held-out evidence appropriate to the claim;
- require no unacceptable regression in critical evidence recall, false-sufficient rate, privacy, correctness or required verification;
- require either a predeclared material improvement in task success/projection/reasoning quality that justifies the extra cost, or quality non-inferiority with a separately meaningful system-level benefit;
- record model/provider, calls, context/tokens, setup/startup, wall time, RAM/VRAM/resource impact where observable, and whether the auxiliary model can coexist with the primary coding model without harmful contention;
- if it does not win, keep it disabled; if it wins only for a bounded task class, enable it only there.

Large LLM reranking of every task is specifically disfavored because it can erase the latency/context/resource advantage C2 is intended to create. The host's primary Qwen coding model is not subject to this auxiliary-component adoption gate.

## Evaluation and adoption

Compare at minimum these treatment classes on the same sealed tasks/revisions where compatible:

- full/current PI delivery;
- deterministic bounded evidence;
- deterministic coverage-optimized evidence;
- coverage + shadow/advisory ranker/reranker when available.

Use correctness-first Pareto/non-inferiority reasoning rather than a single arbitrary weighted score. A candidate is attractive only when task correctness and critical-evidence coverage are not worse while at least one meaningful cost dimension improves, or when a deliberate cost increase produces a predeclared material correctness improvement.

Primary quality metrics:

- task/oracle success;
- critical evidence recall and critical miss rate;
- mandatory obligation coverage;
- false-sufficient rate;
- evidence availability/selection/delivery/utilization recall;
- projection fidelity;
- stale/conflicting evidence retention.

Secondary efficiency metrics:

- request/evidence context tokens and serialized size;
- compression ratio;
- primary-model calls and auxiliary-model calls separately;
- tool calls;
- prefill/cache/prefix reuse when observable;
- model/deterministic wall time;
- auxiliary model startup/API availability and RAM/VRAM/resource cost where observable.

For offline ranker studies also record recall@K/MRR/nDCG only as diagnostic metrics; they never outrank critical-evidence recall or task correctness.

## C2 implementation order

Keep these as work packages inside C2, not new roadmap stages:

1. **C2-A attribution telemetry** — trace `available -> selected -> delivered -> used -> projected -> verified` where observable.
2. **C2-B EvidenceAtom + obligation projection** — reuse existing truth/contracts; no new store.
3. **C2-C AnswerIR / deterministic exact projection** — first target the measured 20 projection/schema failures.
4. **C2-D Sufficiency + Utilization Gate** — explicit Evidence Gap states and bounded repair.
5. **C2-E deterministic coverage optimizer + role budgets** — preserve protected evidence and useful diversity.
6. **C2-F progressive targeted expansion + shadow reservoir** — expand only the missing capability/scope.
7. **C2-G context Bridge** — measure bounded starting budgets and expansion behavior; do not preclaim 2k/4k/8k sufficiency.
8. **C2-H shadow ranker/reranker** — optional evidence only; no production behavior change.
9. **C2-I adoption + causal rerun** — compare current/full, bounded, optimized and any winning ranker variant; seal the result before C3.

The order is intentional: observed projection/utilization failure is repaired before introducing a new learned ranking dependency.

## Expected effect by current gap

- `PROJECTION_SCHEMA_ERROR`: directly targeted by C2-C/D and expected to be the highest-potential improvement area.
- evidence present but ignored: directly targeted by smaller role-focused envelopes, evidence IDs and C2-D utilization checks.
- oversized `pi_symbol`/`pi_context`: directly targeted by C2-E/F/G.
- auto capability under-selection: not solved by C2 alone; C1 is the plan source and C3 is the first production-like automatic application.
- cross-boundary facts missing from Project Truth: not solved by compression/ranking; if failures remain after C2/C3 delivery repair, X0 supplies the smallest measured runtime/static bridge.
- required-test-set tasks already solved equally with PI off: C2 may improve cost/reliability but cannot manufacture a causal accuracy gain; V2/V3 must prove harder verification-specific value.
- held-out capability coverage gaps: remain coverage gaps; do not relabel them as no effect.
- weak-local superiority: remains unproven until an allowed weak-local model exists; no substitute model may be silently introduced.

## Safe continuation after C2

Do not reorder the master backlog. After C2 evidence is merged:

1. enter C3 only with the C1 planner and C2 delivery protocol that survived evaluation; compare `native / manual-best / static-depth / auto` and keep automatic application advisory until held-out evidence passes;
2. run a bounded post-C2/C3 causal confirmation on the previously failing/diagnostic task classes before interpreting B0's no-effect result as final product evidence;
3. if cross-boundary failures persist with correct delivery, proceed with the already-authorized X0 smallest runtime bridge rather than widening all graphs;
4. continue V0-V4, with V2 required verification and V3 evidence reuse as primary differentiation work; do not skip their ablation/false-verified gates;
5. A0/A1 may activate only accepted low-risk classes with stale/uncertain fallback;
6. R0 remains the production-capable baseline gate;
7. P0/P3/P4 remain post-baseline strategic work unless their existing entry conditions explicitly promote them.

Every later stage continues the same model-role separation: use the host's primary coding model normally for genuine coding/reasoning work, while auxiliary PI models remain optional evidence-gated dependencies. Project Evidence Memory, parallel/worktree intelligence and comparative OMO integration must reuse the same evidence identity/provenance rather than creating another context or memory system.
