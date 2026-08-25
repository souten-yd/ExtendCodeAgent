# Context Virtualization / Semantic Working Set — External Audit Checklist

Purpose: independent architecture and implementation audit for the bounded-context direction defined in
`docs/handoff/C2_CONTEXT_VIRTUALIZATION_AND_SEMANTIC_WORKING_SET_DESIGN.md`.

Audit base when this document was created: `main` at
`7bab478709d125722e57fd99dd95b784e0ce62c7`.

The auditor should treat repository code and committed evidence as authoritative. Planning prose is a
claim to verify, not proof that the implementation exists.

---

## 1. Audit objective

Determine whether the proposed direction can realistically make large-project coding quality
non-inferior while constraining the primary-model context to:

- supported maximum total profile `<=64k` tokens;
- preferred p95 around `32k`;
- preferred p50 around `16k`;

without duplicating existing Project Intelligence systems or hiding cost in preprocessing, stale memory,
model calls, VRAM consumption or unverified summaries.

The audit must explicitly search for reasons the design should **not** be adopted or should be reduced.

---

## 2. Required repository inspection

At minimum inspect these production areas:

```text
src/extendcodeagent/core/
src/extendcodeagent/graph/
src/extendcodeagent/twin/
src/extendcodeagent/analysis/
src/extendcodeagent/context/
src/extendcodeagent/orchestration/
src/extendcodeagent/verification/
src/extendcodeagent/runtime/
src/extendcodeagent/testing/
src/extendcodeagent/traceability/
src/extendcodeagent/blueprint/
src/extendcodeagent/convergence/
src/extendcodeagent/strategy/
src/extendcodeagent/storage/
src/extendcodeagent/service/application.py
adapters/opencode/
```

Inspect relevant tests, especially architecture boundaries, context intelligence, orchestration, Twin,
verification, Python/JS/TS semantic analysis and application integration.

Inspect the current evidence and active C2 design:

```text
docs/PI_MASTER_EXECUTION_PLAN.md
docs/handoff/NEXT_TASK.md
docs/handoff/C2_EVIDENCE_DELIVERY_DECISION.md
docs/evaluation/large-project-bounded-context-target-v1.json
docs/evidence/final/baseline-gap-report.md
docs/evidence/final/c1-shadow-planner-result-v1.json
AGENTS.md
```

---

## 3. Current-code claims to verify

Verify each claim as `CONFIRMED`, `PARTIAL`, `FALSE`, or `STALE`.

1. `GraphNode` / `GraphEdge` already provide generic versioned fact/property/evidence carriers suitable
   for semantic contract facts without adding a separate Contract Store.
2. `TwinService` is the correct source-revision/analyzer-version/invalidation owner and can version
   additional analyzer-produced contract facts.
3. `VerificationObligation` / `RequiredVerificationSet` are sufficient as the existing obligation
   vocabulary and should be reused instead of adding Context-specific obligation DTOs.
4. `TaskSignals` / `TaskIntent` / `IntelligencePlan` are the correct task-aware entrypoint and creating a
   second generic task classifier would be duplication.
5. `RuntimeObservation` and the existing runtime store are sufficient as the only runtime evidence
   authority.
6. Traceability already owns requirement mappings and a separate requirement graph/store is not needed.
7. `ContextRequest` / `ContextItem` / `ContextPackage` and `build_context()` are currently too shallow
   for obligation-aware minimum sufficient context.
8. `ProjectIntelligenceApplication` is already large enough that new C2 domain algorithms should not be
   added directly to it.
9. Shared SQLite/repository infrastructure can accept any justified durable task/memory object without
   adding a second persistence technology.
10. The current implementation has no production `EvidenceAtom`, semantic contract fingerprint,
    Semantic Working Set, ChangeCapsule, durable TaskExecutionState or generic Project Memory system.

If any claim is false, explain the exact existing owner that should replace the proposed concept.

---

## 4. Duplication and ownership audit

For every proposed concept, find the closest existing owner and assess whether the proposal is:

- `REUSE`;
- `EXTEND`;
- `PROJECT` (consumer-specific immutable view);
- `CONSOLIDATE`;
- truly `NEW`.

Review at least:

```text
EvidenceAtom
SemanticContract projection
Semantic ABI / contract fingerprint
Semantic Working Set
Evidence Gap
ChangeCapsule
Context Compiler
TaskExecutionState
Task DAG
Project/Evolution Memory
Context Debt
```

A high-severity finding is any new object/store that duplicates revision, evidence, requirement,
runtime, task planning, verification or graph ownership.

---

## 5. Context-root-cause audit

Challenge the premise that long context is primarily a representation/retrieval problem.

Using existing evaluation traces/evidence where possible, estimate the contribution of:

1. source/tool exploration;
2. PI serialization bloat;
3. conversation/task-state retention;
4. exact output/schema copying;
5. runtime/cross-boundary missing truth;
6. repeated verification/test discovery;
7. agent reasoning quality independent of context;
8. provider/runtime protocol overhead;
9. cache/prefix behavior;
10. model output/reasoning tokens.

Identify which causes can be solved by project-side structure and which cannot.

The auditor should reject a design that claims 32k mainly by moving the same data into hidden model
calls or expensive preprocessing.

---

## 6. Semantic contract audit

Evaluate whether contract extraction is sufficiently valuable and safe.

Questions:

- Which Python facts are reliably extractable from the current AST analyzer without a second parse?
- Which JS/TS facts are reliably extractable from the existing tree-sitter analyzer?
- Can public/exported boundaries be identified with sufficient precision?
- How are unknown input/output/effect components represented?
- Could a contract fingerprint incorrectly stop Impact propagation after an unmodeled behavior change?
- How is a newly-known field reflected in fingerprint/version semantics?
- Should effect/state facts live as Graph nodes, edges, properties or evidence?
- What confidence/status is appropriate for statically inferred side effects?
- Is a dedicated `contract` node type actually necessary, or can existing symbol nodes + typed edges/
  properties carry the facts more maintainably?

Flag any proposal that turns an implementation summary into falsely verified behavior.

---

## 7. Twin / invalidation audit

Verify that every proposed persistent or cached projection has a clear invalidation rule.

Required checks:

- exact project/workspace identity;
- Twin/source revision binding;
- analyzer/producer version binding;
- dependency/contract closure invalidation;
- runtime evidence freshness;
- requirement/decision evidence freshness;
- task state invalidation on objective/revision changes;
- memory invalidation after dependency changes;
- behavior when the worktree is dirty or revision fingerprint is absent.

A stale memory or contract reused as current truth is a release-blocking design defect.

---

## 8. Task state / memory audit

Critically evaluate whether new durable task/memory support is actually required.

First attempt to solve long-horizon continuity using existing:

- `TaskSignals` / `IntelligencePlan`;
- Blueprint;
- Convergence;
- Verification Obligations;
- trace/evidence IDs;
- Git/revision history.

Recommend a new `TaskExecutionState` only if concrete state cannot be represented cleanly by those
owners.

For Project Memory, reject generic "chat memory" or free-text embedding stores as truth. Require an
invalidation key and consumer for every durable entry.

Assess whether structural memory should simply be recomputed from Twin rather than persisted again.

---

## 9. Context Compiler audit

Check whether the proposed pipeline separates responsibilities cleanly:

```text
candidate projection
EvidenceAtom projection
protected evidence
coverage optimizer
sufficiency check
targeted expansion
working-set envelope
AnswerIR/ChangeIR projection
serialization
```

Look for accidental monoliths and duplicated ranking/selection logic.

Specific questions:

- Can existing `build_context()` remain a backward-compatible simple profile while a richer compiler is
  introduced incrementally?
- Which parts belong in `context/` vs `analysis/` vs `verification/`?
- Does the compiler require repository parsing, which would duplicate analyzers?
- Does it preserve required contradictory/uncertain evidence?
- Does it expose a deterministic reason for every included item?
- Can every page-in/expansion be attributed to a named Evidence Gap?
- Is "working set overflow" handled by task decomposition before silent truncation?

---

## 10. Maintainability / refactoring audit

Inspect code-size and responsibility hotspots rather than judging by line count alone.

Priority targets:

### `src/extendcodeagent/service/application.py`

Determine whether it is still a facade or has accumulated domain algorithms. Recommend exact
extract/move boundaries. Do not propose a framework-heavy rewrite merely to reduce file size.

### `src/extendcodeagent/orchestration/service.py`

Check whether classification, plan specification and plan generation remain cohesive. Split only if
new C2/C3 concerns would create conflicting responsibilities.

### `src/extendcodeagent/context/service.py`

Assess migration path from simple packing to a composed compiler without breaking existing public/test
behavior.

### analyzers

Ensure semantic-contract extraction extends current parse/traversal rather than re-reading/re-parsing
files in a second pipeline.

### storage

Check for duplicate repository/table patterns and suggest reusable persistence helpers only when there
is real repeated code.

### evaluation runner

It is large. Determine whether new C2 evaluation work would further entangle schedule/workspace/
provider/trace/result responsibilities. Recommend a bounded split only for code actually touched by C2.

The audit should classify refactors as:

- `REQUIRED_BEFORE_FEATURE`;
- `DO_WITH_FEATURE`;
- `SAFE_LATER`;
- `NOT_WORTH_IT`.

---

## 11. 32k / 64k feasibility audit

Treat the context target as an empirical contract, not a slogan.

Verify that the measurement counts:

- system/control prompt contribution where observable;
- model-visible user/task text;
- PI evidence/context;
- cached/read/write prompt contribution under the provider's semantics;
- reserved output headroom.

Test/plan a compression curve:

```text
8k / 16k / 24k / 32k / 48k / 64k
```

For each class, compare against full/current or manual-best context using non-inferiority quality gates.

Recommend which task classes can reasonably target 16k, 32k, 64k or require decomposition.

A task is not 64k-capable if input fits but reserved output pushes total above 65,536.

---

## 12. Local-model / quantization audit

The project goal is to free KV/context memory so the operator can use a less aggressive quantization
or higher-quality model. ECA must not own model loading/quantization policy.

Audit whether resource reporting is sufficient to prove this system-level benefit:

- context/KV memory reduction;
- primary-model VRAM/RAM residency;
- no model eviction/reload;
- no auxiliary PI model consuming the saved budget;
- quality comparison at two or more realistic quantization/model profiles if available.

Do not attribute quality improvement to context virtualization unless the model/profile comparison is
controlled.

---

## 13. Security / trust audit

Project content is untrusted. Verify:

- repository-origin strings remain data, not control instructions;
- summaries/contracts preserve provenance;
- no LLM-generated fact silently becomes Project Truth;
- memory cannot escalate rollout/depth/privacy policy;
- external research cannot become verified project fact;
- exact revisions and workspace IDs prevent cross-worktree leakage;
- context paging by evidence ID cannot fetch data from another workspace.

---

## 14. Required negative findings

The audit is incomplete if it only confirms the plan. Explicitly report:

1. top five assumptions most likely to be wrong;
2. top five places the design may become over-engineered;
3. mechanisms that should be dropped or deferred;
4. places an existing ECA type/service already solves the proposed problem;
5. expected failure modes at 32k;
6. expected failure modes for greenfield development;
7. expected failure modes for UI/browser/API/backend changes;
8. expected stale-memory/invalidation failures;
9. likely maintenance hotspots after implementation;
10. the smallest alternative architecture that could achieve 80% of the benefit.

---

## 15. Auditor output format

Return:

### A. Executive verdict

One of:

- `ADOPT_AS_DESIGNED`;
- `ADOPT_WITH_CHANGES`;
- `NARROW_AND_RETEST`;
- `REJECT`.

### B. Verified current-state table

For each code/design claim: `CONFIRMED / PARTIAL / FALSE / STALE`, evidence path, rationale.

### C. Severity-ranked findings

Use `BLOCKER / HIGH / MEDIUM / LOW` and include exact file/type/function references.

### D. Duplication/consolidation table

For every proposed new concept: `REUSE / EXTEND / PROJECT / CONSOLIDATE / NEW`.

### E. Refactoring plan critique

Mark each proposed refactor `REQUIRED_BEFORE_FEATURE / DO_WITH_FEATURE / SAFE_LATER / NOT_WORTH_IT`.

### F. 32k/64k feasibility verdict

State which task classes are plausibly 32k-capable, 64k-capable, or need task decomposition, and what
proof is still missing.

### G. Revised architecture

If the proposed architecture is not optimal, provide a smaller or safer replacement and explain why.

### H. Test/evaluation gaps

List exact missing tests/evidence required before active adoption.

### I. Go/no-go recommendation

State the smallest next implementation slice that should be allowed to merge.
