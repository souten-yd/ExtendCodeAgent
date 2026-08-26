# C2 Plan Revision and Adoption Decisions

Status: **stage-local plan revision for C2, derived from measurement taken 2026-08-26.**

`docs/PI_MASTER_EXECUTION_PLAN.md` remains the canonical backlog and is not reordered by this
document. `docs/handoff/C2_EVIDENCE_DELIVERY_DECISION.md` remains the C2 evidence-delivery contract;
this document changes the **order and the exit criterion** of its work packages on measured grounds,
and rules on the mechanisms proposed in PR #102.

Inputs: `docs/audit/C2_CONTEXT_VIRTUALIZATION_INDEPENDENT_AUDIT.md`,
`docs/handoff/C2_TRUTH_SCOPE_AND_COST_FIDELITY_CORRECTIVE_DESIGN.md`,
and the new deterministic instrument `tools/local/c2_evidence_recall.py`.

---

## 1. The measurement that changes the plan

Once the Twin contained the project and the estimator matched the payload, C2's central assumption
became testable without a model. The sealed task oracle already states the facts a correct answer must
contain, so critical-evidence recall is computable at every budget on the compression curve.

Measured on `eca-symbol-001`, `eca-impact-001`, `eca-tests-001` at HEAD, zero model calls:

| Budget | delivered tokens | selected | normalized recall (mean) |
|---|---|---|---|
| 1,024 | ~1,250 | 12 | 0.18 |
| 2,048 | ~2,350 | 25 | 0.18 |
| 4,096 | ~2,800 | 32 | 0.24 |
| 8,192 | ~2,800 | 32 | 0.24 |
| 16,384 | ~2,800 | 32 | 0.24 |
| 32,768 | ~2,800 | 32 | 0.24 |

```
best normalized recall (mean over tasks) : 0.244
best raw recall        (mean over tasks) : 0.056
recall at 32,768 vs at 4,096             : unchanged
maximum unused budget                    : 30,417 tokens of 32,768
```

Three conclusions follow, and each contradicts a premise the C2 plan was built on.

**1.1 Context size is not the binding constraint.** At the 32k profile the envelope spends about 7%
of its budget and leaves 30,417 tokens unused. It stops because `_PROTOCOL_MAX_ITEMS = 32` binds long
before the token budget does — 46 candidates are excluded with 5,640 tokens still free at 8k. A
mechanism that cannot spend 8k cannot be tuned for 32k or 64k. **Compression is optimising a
constraint that is not active.**

**1.2 Selection recall is the binding constraint.** 0.244 of the facts a correct answer needs are
recoverable from the delivered envelope. `eca-tests-001` scores 0.00 — the required verification tests
are absent entirely, although `derive_required_verification_set` exists and could name them.

**1.3 The envelope encodes facts in the wrong shape.** Raw recall is 0.056 against normalized 0.244:
the envelope emits `py://src.extendcodeagent.testing.service#select_tests` while the answer requires
`src/extendcodeagent/testing/service.py`. The Graph holds both. PI makes the model perform a
deterministic translation it could perform itself — which is exactly the 20 measured
`PROJECTION_SCHEMA_ERROR` cells, now reproduced without a model.

### 1.4 Consequence for B0b's null result

B0b found Graph, Twin, Semantic and Test Selection `NO_CONFIRMED_CAUSAL_EFFECT`. That is consistent
with these numbers rather than surprising against them: a channel delivering a quarter of the required
facts, in the wrong encoding, should not move task success. **The null result is more likely a
delivery defect than a capability verdict**, which is a materially better position than the programme
believed it was in — but only if the plan targets delivery next.

---

## 2. Revised goal decomposition

The 32k/64k target was treated as one problem. It is three, and they are strictly ordered:

| | Question | Current | Binding? |
|---|---|---|---|
| **S — Sufficiency** | does the envelope contain what the answer needs? | 0.244 | **yes** |
| **E — Encoding** | is it in the shape the answer needs? | 0.056 raw | **yes** |
| **C — Compression** | does it fit the profile? | 2.8k of 32k used | no |

C cannot become binding until S approaches 1.0, because raising S will raise delivered tokens. The
entire value of the compression work is therefore **contingent on first solving S and E**, and every
compression mechanism proposed for C2 should be re-sequenced behind them.

**Revised C2 exit criterion.** Replace "showing task-success or cost improvement" — which B0b already
showed is not detectable on this corpus — with a criterion the instrument can decide:

> C2 exits when normalized critical-evidence recall is >= 0.90 and raw recall >= 0.90 on the sealed
> tuning tasks, with the delivered envelope inside the 8k initial evidence target, and held-out
> tasks non-inferior. Task-success comparison remains a gate, not the primary signal.

This is falsifiable, deterministic, costs no model budget, and can be run on every commit.

---

## 3. Adoption decisions

Each mechanism is ruled on value, cost and the evidence that supports it. `ADOPT` means it enters the
C2 work order; `NARROW` means adopt with a stated bound; `DEFER` means it needs entry evidence;
`REJECT` means it leaves C2 scope.

### 3.1 ADOPT — Critical-Evidence-Recall@Budget as C2's primary instrument

Implemented as `tools/local/c2_evidence_recall.py`.

The highest value-to-cost item in this review. It converts C2's central question into a deterministic
measurement with no model calls and **no new labelling** — the sealed oracle already carries the
required facts. It separates "PI delivered the truth" from "the model used the truth", which is the
attribution the merged decision document asks for and never had an instrument for. It also produces
the compression curve directly.

*Value: very high. Cost: one 250-line tool, already built. Risk: the oracle's answer fields are a
proxy for required evidence, not a complete labelling — treat recall as a lower bound.*

### 3.2 ADOPT and promote to first — deterministic exact projection (AnswerIR)

Raw recall 0.056 versus normalized 0.244 quantifies the burden precisely: **77% of the facts PI does
deliver arrive in an encoding the answer cannot use directly.** This is the only C2 failure class with
independent measured evidence behind it (20 B0b `PROJECTION_SCHEMA_ERROR` cells) and it is cheap: the
ref→path→qualname expansion already exists in the Graph and is computed in twelve lines by the recall
harness.

Promote `C2-C` ahead of `C2-A`. Attribution telemetry is valuable, but there is no point instrumenting
a channel whose top defect is already identified and mechanically fixable.

*Value: very high. Cost: low. Evidence: direct.*

### 3.3 ADOPT — make the budget actually bind

`_PROTOCOL_MAX_ITEMS = 32` and `_PROTOCOL_MAX_TOKENS = 8_192` are fixed constants that override the
caller's request, so the envelope cannot use a larger profile even when correctness requires it. This
is a two-line change and it is a **product behaviour change**, so it does not belong in the corrective
slice: it lands as the first C2-1 item, with a before/after recall curve as its evidence.

Note the asymmetry: raising the item cap alone will raise recall only if the ranking is right. Run the
curve first; if recall at 64 items is no better than at 32, the defect is ranking, not the cap, and
the coverage optimiser (§3.4) is the answer instead.

*Value: high. Cost: trivial. Must be measured, not assumed.*

### 3.4 NARROW — Semantic Working Set / Coverage Optimiser

Adopt, bounded to one justification: **raise S**. Not "minimum sufficient context", not a compiler
pipeline, not the seven-module split in PR #102 §13.1. The optimiser is admitted only after §3.3
shows the cap is not the whole story, and it is accepted only if it moves normalized recall.

Concretely, obligations already exist — `derive_required_verification_set` produces
`VerificationObligation`s with criticality and provider IDs. `eca-tests-001` scoring 0.00 while the
required set is derivable is the clearest single opportunity in the codebase: **make obligation
providers protected evidence and they enter the envelope by construction.**

*Value: high, but contingent. Cost: moderate. Gate: normalized recall delta.*

### 3.5 DEFER — Semantic Contract extraction

Near-greenfield (5 of 16 fields derivable; the analyzers emit no parameters, annotations, return
types, visibility, raises or effects). Before spending that effort, §3.2–3.4 should be measured: if
recall reaches 0.9 without contract facts, contract extraction is not a C2 concern at all. Entry
evidence: a recall ceiling that contract facts demonstrably lift.

It also belongs to `side_effects` / `state_event` / `api_schema_db`, not to `context`, and must
declare its `CapabilityName`, `D0..D4` depth and ablation arm before implementation.

### 3.6 REJECT for C2 — Semantic ABI / contract fingerprint

A fingerprint over "declared inputs, declared output, effect classes, schema bindings" computed on
analyzers that emit none of those hashes a near-constant `unknown` vector. It would report "boundary
unchanged" for real boundary changes, silently truncating the Impact closure and the required
verification set — a false negative landing directly on the one thing declared a hard gate.

Re-propose only with: a published contract-field coverage rate per entity, a labelled corpus, and
`false_stop_rate = 0` on public boundaries in shadow. Not a C2 mechanism.

### 3.7 REJECT for C2 — TaskExecutionState / durable task engine

No measured consumer exists. `PlanOutcome` + `convergence` + `blueprint` already cover plan, progress
and target-versus-actual, and C1 ran with zero repository I/O. Re-propose with a measurement showing
session history is required to recover execution progress.

### 3.8 DEFER — Project Memory

The audit's finding stands: structural memory regenerated from Graph/Twin is a cache and should be
named one; decision memory is the only class with long-horizon value and is exactly the class whose
invalidation cannot be derived from a file change. `CapabilityName.MEMORY` already exists and is
forced `off`; the SQLite owner is already bitemporal. Nothing needs building until an invalidation
protocol for reviewed decisions exists.

### 3.9 ADOPT as secondary — Context Debt

Keep it as a diagnostic, as PR #102 proposes, and do **not** promote it. Context Debt measures waste;
waste is not the active constraint while 93% of the budget is unspent. It becomes useful the moment S
approaches 1.0 and delivered tokens start to grow — schedule it to arrive with the compression work,
not before.

### 3.10 ADOPT as an experiment arm — "deliver only what local search cannot find"

**The most substantive new idea in this review, and it is a criticism of the product's premise.**

B0b's PI-off arms passed equally often as PI-on arms. One explanation deserves testing: much of what
PI delivers — a symbol's definition path, its name, its file — is what a coding agent finds with one
`grep`. PI's irreducible value is the part local search cannot produce: reverse dependencies,
transitive impact, verification obligations, staleness, contradiction, requirement mapping.

The experiment is cheap. Classify each delivered evidence item as *locally discoverable* (findable by
searching the objective's literal terms) or *graph-only* (requires traversal). Then measure recall and
task outcome for a graph-only envelope.

Two outcomes, both valuable:

- if a graph-only envelope preserves task outcome, context drops sharply **and** PI's effect is
  isolated for the first time — one experiment serves both programme goals;
- if it degrades outcome, the locally-discoverable payload is doing real work, which is itself the
  first positive causal evidence for the delivery channel.

*Value: very high — it addresses the programme's central unanswered question. Cost: low. Add as an
ablation arm, not as default behaviour.*

### 3.11 ADOPT — measure prefix-cache reuse for real

`stable_evidence_envelope()` and `stable_prefix_id` are exactly the right design: a task-invariant
prefix that a provider can cache. But the metric is the placeholder string
`"cache_observation": "model_response_metrics"`.

Progressive expansion's entire cost argument depends on this. If the stable prefix is not actually
cache-hit, then two bounded calls cost more prefill than one larger call, and the scope ladder is a
net loss disguised as a saving. Promote prefix-cache hit rate from placeholder to a required C2
measurement, or state plainly that expansion's economics are unverified.

### 3.12 ADOPT — structural enforcement of the facade boundary

The line budget added during the audit (1,600) is arbitrary and only works if someone lowers it.
A stronger invariant is already satisfied and should be pinned instead: **no module-level function in
`service/application.py` may traverse `snapshot.nodes` or `snapshot.edges`.** That is a precise
statement of "the facade serializes, the domain computes", and it cannot be satisfied by shuffling
lines. Keep the budget as a coarse backstop; add the structural rule as the real gate.

---

## 4. Revised C2 work order

Supersedes the ordering in `C2_EVIDENCE_DELIVERY_DECISION.md` §"C2 implementation order". The work
packages are unchanged; the sequence and the exit criterion are.

| # | Package | Why here | Gate |
|---|---|---|---|
| **C2-0** | Truth scope + cost fidelity | done; nothing below is interpretable without it | Twin covers the project; estimator within 10% |
| **C2-0b** | Recall instrument + baseline seal | makes every later gate decidable at zero model cost | sealed curve at HEAD |
| **C2-C′** | Deterministic exact projection (AnswerIR) | raw 0.056 vs normalized 0.244 — largest measured single defect | raw recall → normalized recall |
| **C2-1** | Budget actually binds (item cap) | envelope leaves 93% of a 32k profile unused | recall delta at 64 vs 32 items |
| **C2-E′** | Obligation providers as protected evidence | `eca-tests-001` is 0.00 while the required set is derivable | normalized recall on verification tasks |
| **C2-A** | Attribution telemetry | now instruments a channel whose top defects are fixed | attribution on residual failures |
| **C2-D** | Sufficiency gate | meaningful once recall is high enough to have a true `SUFFICIENT` | false-sufficient rate |
| **C2-X** | Graph-only ablation arm (§3.10) | isolates PI effect; can run alongside | outcome delta vs full envelope |
| **C2-G** | Compression curve + prefix-cache | first point at which compression is the active constraint | p50/p95 total context; cache hit rate |
| **C2-I** | Adoption + causal rerun | unchanged | sealed comparison |

Deferred out of C2: contract extraction, ABI fingerprint, task state, memory, HTML analyzer.

---

## 5. What this revision does not claim

- 0.244 is measured on **three tuning tasks in one Python repository**. It is a strong signal about the
  delivery channel and not a general recall figure. The instrument must be extended to all 13 sealed
  tasks and to the JS/TS corpus before any programme-level conclusion.
- Recall computed from oracle answer fields is a **lower bound** on required evidence: facts needed for
  reasoning but not present in the final answer are not counted.
- Nothing here promotes a capability, changes a threshold, or claims a 32k/64k capability. The targets
  in `large-project-bounded-context-target-v1.json` are unchanged and remain engineering targets.
- The graph-only experiment (§3.10) is proposed as an **arm**, not a default. If it wins, that is a
  finding; adopting it before measurement would repeat the mistake this revision is correcting.
