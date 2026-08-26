# Independent Audit — PR #102 Context Virtualization and Semantic Working Set

Audit date: 2026-08-26
Auditor: independent review, code-first
Target: PR #102 `agent/context-virtualization-semantic-working-set` (Draft, docs only, +1745/-0, 3 files)
Base reviewed: `main` at `7bab478`, plus unmerged `agent/weak-local-evidence-protocol` (`4e51af4`)

**Verdict: `NARROW_AND_RETEST`.**

The design's *rulings* are mostly right. Its *premises about the current codebase are not*, and two
production defects found during this audit meant the C2 measurement instrument was measuring the wrong
project entirely. The architecture cannot be adopted, rejected or even sized until it is re-measured
against a Twin that contains the project. This audit fixed both defects (§6) so that retest is possible.

---

## 1. Method

Design prose was not accepted as evidence. Every claim was checked against production code, the test
suite, and executed measurement:

- read every domain contract and service under `src/extendcodeagent/`;
- ran the full suite (329 tests, green) plus `ruff` and `mypy`;
- executed `tools/local/c2_evidence_protocol.py` against this repository before and after fixes;
- measured Twin composition, delivered payload size and estimator fidelity directly.

---

## 2. What is actually implemented, versus what the design assumes

| Design claim | Verified state | Verdict |
|---|---|---|
| "`context` is a small PR-E implementation that filters only by confidence" | `build_context` is; but `build_weak_local_evidence` (451 lines, unmerged branch) already implements scopes, evidence IDs, provenance interning, gap emission and progressive expansion | **understated** |
| "Reuse and extend the existing C2 [Evidence Gap] taxonomy" | No such taxonomy exists in production. Production emits 4 strings: `objective_anchor_missing:*`, `candidate_or_token_bound_reached`, `candidate_search_bound_reached`, `no_task_relevant_evidence` — all *mechanism-saturation* states, none semantic | **no existing basis** |
| "Extend the existing Python `GraphAnalyzer`" for semantic contracts | The analyzer emits `name`, `qualname`, `start_line`, `end_line`, `intent_tokens`, `scope`, `bound_name`, `occurrences`. No parameters, annotations, return types, visibility, raises or effects. Of the 16 contract fields in §6.1, **5 are derivable today** | **near-greenfield, not an extension** |
| "Twin correctly owns source revision identity, refresh selection and invalidation" | True for revision mechanics, but the scope it indexes was wrong — see §3 | **partially false** |
| Analysis budgets bound the work | `AnalysisBudgets` has 8 fields; **7 have no consumer anywhere** (`max_files`, `max_file_bytes`, `max_graph_nodes`, `max_graph_edges`, `incremental_batch_ms`, `background_workers`, `memory_budget_mb`). Only `max_depth` is read | **dead config** |
| `ProjectIntelligenceApplication` "may not accumulate C2 algorithms" | It already had: a second test-selection heuristic (`_focused_test_paths`, `_objective_test_paths`, `_structural_test_paths`, `_intent_architecture_test_paths`, `_direct_use_count`, `_test_obligation`) competing with `testing/service.py::select_tests` | **already violated** |

### 2.1 The design largely restates an already-merged decision

`docs/handoff/C2_EVIDENCE_DELIVERY_DECISION.md` (on `main`, 271 lines) already owns: EvidenceAtom and
its field list, protected-evidence rules, the deterministic coverage optimizer, role budgets, the
Sufficiency Gate with its `MISSING_SYMBOL … INTENT_UNCERTAIN` states, AnswerIR/ChangeIR, the Evidence
Utilization/Projection Gate, the Context Shadow Reservoir, the ranker policy and a C2-A..C2-I
implementation order. `docs/handoff/NEXT_TASK.md` repeats the work packages.

PR #102 renumbers C2-A..C2-I as C2-1..C2-9 and restates those concepts in different words. Roughly
**60% of the 950-line design is duplication of merged decisions**, which is itself the duplication
failure the document warns against. Genuinely new material is listed in §4.

### 2.2 Governance

Master Plan §8 defines C2 as *"Weak-local evidence protocol (conditional)"*, scoped to *"stable PI
envelope, deterministic candidate reduction, bounded ID/enum/schema decisions, progressive expansion…
Implemented inside existing context/routing code, not as a new package."* PR #102 expands a
**conditional** stage into nine sub-stages spanning contract extraction, an HTML analyzer, task state,
project memory and a quantization boundary. It states it "is not a second roadmap" while functioning
as one.

Additionally: the design never mentions `CapabilityName`, `CapabilityPolicy`, ablation or the `D0..D4`
depth axis — **zero occurrences across all three files**. AGENTS.md and Master Plan invariant 6 require
that a mechanism that cannot be switched off cannot be shown to be worth its cost. Every mechanism
proposed (Semantic Contract, ABI fingerprint, Working Set, Sufficiency Gate, Memory, TaskExecutionState)
is un-ablatable as specified. Six of them map onto capability names that already exist and are forced
`off`: `side_effects`, `state_event`, `api_schema_db`, `ui_graph`, `memory`, `data_flow`.

---

## 3. Two production defects found during audit (both fixed — §6)

### 3.1 P0 — the Twin of this repository contained none of this repository

`SourceSnapshotter` walked `sorted(root.rglob("*"))` with a hard-coded `IGNORED_NAMES` set and a
10,000-file cap. `.evaluation/` is in `.gitignore` but **not** in `IGNORED_NAMES`, sorts before `src/`,
and holds 207,037 of 207,308 scannable files. The cap was reached at index 10,000; the first `src/`
file sits at index 207,147.

Measured before the fix:

```
Twin nodes: 75,712   edges: 429,958
by top directory: .evaluation 75,709 | .claude 2 | . 1
src/ nodes: 0        tests/ nodes: 0      tools/ nodes: 0
```

Every `pi_symbol`, `pi_impact`, `pi_tests` and `pi_context` answer about this project was derived from
unrelated evaluation corpora. The truncation was reported only as an `INFO` diagnostic, so it degraded
silently. This invalidates every dogfooding measurement taken on `main` or the C2 branch, including the
sealed artifact `tools/local/c2_evidence_protocol.py` writes to `docs/evidence/final/`.

It is not in `KNOWN_ISSUES.md`. **The scoping bug, not the architecture, is why C2's evidence looked
bad.** Note the boundary: the evaluation runner copies corpora into separate workspaces, so B0b's
93,189-token figure is *not* attributed to this defect — but every self-measurement is.

### 3.2 P0 — the token budget was not measuring the delivered payload

`ContextRequest.token_budget` was enforced against an estimate computed from three short strings
(`canonical_ref + summary + why_included`) / 4, while the consumer receives revision, provenance,
confidence and status as well.

```
claimed used_tokens: 1,830   actual delivered: ~9,384 tokens   → 5.1x under-count
```

A 32k/64k target cannot be stated, tested or enforced against an estimator that is wrong by 5x. This
also means every historical "PI envelope tokens" figure produced through this path is an under-report.

---

## 4. Concept classification

Per the design's own required disposition (`REUSE` / `EXTEND` / `PROJECT` / `CONSOLIDATE` / `NEW`).

| Concept in PR #102 | Existing owner | Disposition | Note |
|---|---|---|---|
| Semantic Working Set | `context/` + `WeakLocalEvidencePackage` | **CONSOLIDATE** | A rename of what the C2 branch already builds. Do not add a second envelope type. |
| EvidenceAtom | `WeakLocalEvidenceItem` + `C2_EVIDENCE_DELIVERY_DECISION.md` | **EXTEND** | Add `role`, `obligation_ids`, `depends_on_evidence_ids` to the existing item. Not new. |
| Evidence Gap taxonomy | none in code; taxonomy already merged in the decision doc | **REUSE** the merged names | Production's 4 saturation strings are a different axis; keep both, do not conflate. |
| Sufficiency Gate | `WeakLocalEvidencePackage.deterministic_resolution` | **EXTEND** | The field exists; the semantic states do not. |
| Semantic Contract Projection | `graph/analyzers/*` | **EXTEND**, but ~11 of 16 fields are greenfield | Belongs to `side_effects` / `state_event` / `api_schema_db` capabilities. Must be gated. |
| Semantic ABI / contract fingerprint | none | **NEW** — and **defer** | See §5.1. |
| ChangeCapsule | `ChangeIR` in the merged decision doc | **CONSOLIDATE** | Two names for one object. Keep `ChangeIR`. |
| Context Compiler pipeline | `context/service.py` | **EXTEND** | The 7-module split in §13.1 is premature; see §5.4. |
| Context Debt | `evaluation/trace.py` + `c2-effect-metrics-v1.json` | **PROJECT** | A metric over existing attribution, not a subsystem. |
| Evidence Scope ladder | `context.EvidenceScope` **and** `orchestration.ContextScope` | **CONSOLIDATE** | Two overlapping scope enums already exist. C2 must not add a third. |
| TaskExecutionState | `orchestration.PlanOutcome` + `convergence.*` + `blueprint.*` | **REUSE first**, defer | See §5.3. |
| Project Memory | `CapabilityName.MEMORY` (declared, `not_implemented`) + SQLite bitemporal store | **EXTEND when justified** | Storage already supports it: `valid_from`/`valid_to`, workspace scoping. |
| Shadow reservoir | `C2_EVIDENCE_DELIVERY_DECISION.md` §Context Shadow Reservoir | **REUSE** | Already decided. |
| HTML/CSS analyzer | `CapabilityName.UI_GRAPH` (declared, `not_implemented`) | **DEFER**, correctly | The design's own gating on measured root cause is right. |
| Quantization/resource boundary | `large-project-bounded-context-target-v1.json` | **REUSE** | Already specified in more detail than the design restates. |

**Net: 1 justified `NEW` (deferred), 3 `CONSOLIDATE`, 5 `EXTEND`, 4 `REUSE`, 2 `DEFER`.**
No concept in PR #102 requires a new truth store, a new database or a new planner. On that central
question the design is correct, and its non-duplication rules (§3.2) should be adopted verbatim.

---

## 5. Critical evaluation of the specific risks raised

### 5.1 Semantic Contract / ABI false negatives — **highest risk; defer**

The fingerprint is defined over "declared inputs, declared output, declared/observed effect classes,
API/schema bindings, uncertainty markers". Today the analyzers supply **none of those**. A fingerprint
computed now would hash a near-constant `unknown` vector, so it would report "boundary unchanged" for
almost every real boundary change — a false stop that silently truncates the Impact closure and
therefore the required verification set.

The design's mitigation ("a missing fact becoming known is a fingerprint change") does not help: the
dangerous case is a fact that stays unknown across a change that alters it. The failure is silent and
lands on correctness, the one thing declared a hard gate.

**Ruling:** the fingerprint may not gate Impact or context propagation until contract-field coverage
per entity is measured and a false-stop rate is published on a labelled corpus. Shadow-only, and
`accepted false_stop_rate = 0` for public boundaries. This is C2-7 in the design, correctly last —
but it should be moved out of C2 entirely.

### 5.2 Memory staleness — the invalidation story is sound, the retrieval story is not

§9.2's binding requirements (project, revision or dependency closure, provenance, producer version,
freshness policy, invalidation reason) are correct and the SQLite owner already implements bitemporal
`valid_from`/`valid_to` with workspace scoping, so persistence is genuinely cheap to add.

The gap is that **structural memory (§9.1 class 1) has no invalidation key that is cheaper than
recomputation**. If it is regenerated from Graph/Twin, it is a cache, not memory, and should be named
one. Decision memory (class 2) is the only class with real long-horizon value and it is exactly the
class whose invalidation cannot be derived mechanically — a design decision does not become stale when
a file changes. The design does not resolve this and should not persist class 2 until a human-review
or supersession protocol exists.

### 5.3 Task Engine — not justified by any current evidence

`orchestration.PlanOutcome` already records plan, capabilities, evidence IDs, expansion count and
fallback reason. `convergence` already models target/actual/verification with a 7-state element model
and a 7-value decision enum. `blueprint` already models planned elements with dependencies and
acceptance criteria. No measurement in the repository shows session history being needed to recover
execution progress — C1 ran with **zero** repository I/O and no model calls.

**Ruling:** `TaskExecutionState` has no measured consumer. Correctly deferred to C2-9; it should be
deleted from the C2 scope and re-proposed with evidence.

### 5.4 Context Compiler responsibility separation — right principle, wrong granularity

§13.1's seven-module split (`evidence`, `coverage`, `sufficiency`, `compiler`, `projection`, …) would
turn a 451-line service into seven files before there is behaviour to separate. The document itself
says "split only when production code exists" — that caveat should be promoted to the rule. Two splits
are justified *now* because they fix real defects, and both were performed in §6: serialization+cost
into one owner, and test-path projections into the testing domain.

### 5.5 32k / 64k feasibility — unproven, and until this audit unmeasurable

- The estimator was 5.1x low (§3.2), so no historical envelope figure supports any target.
- The Twin held the wrong project (§3.1), so no selection quality figure is meaningful.
- `_infer_scope` is degenerate on this corpus: all three C2 tasks classify as `verification` because
  the heuristic keys on the substrings `test`/`evidence`/`requirement`, which appear in nearly every
  objective in a PI repository. Scope inference is effectively constant.
- Before the fix, one-step progressive expansion returned **identical** candidate counts, selection
  counts and unresolved gaps. The advertised targeted page-in resolved nothing.

After the §6 fixes, on this repository: candidates 256(saturated) → 25–70, `candidate_search_truncated`
False for the symbol task, unresolved gaps 5–6 → 0, and estimator fidelity 5.1x → 1.01x. The residual
`oracle_projection_equal: false` now reflects **genuine** test over-selection rather than a wrong graph
— which is the first time C2 has had a valid signal to work against.

**The 32k p95 / 64k max targets should stay declared engineering targets. They are not yet supported
by any valid measurement**, and the design's own §18 wording ("describe as an engineering target, not
a proven product guarantee") is correct and should be kept.

### 5.6 `application.py` maintainability

At audit start: 1,752 lines, importing nearly every domain, and hosting a second test-selection
heuristic that `testing/service.py` was supposed to own. Prose rules ("keep the facade thin") had
already failed to hold the line. §6 reduced it to 1,533 lines and replaced the prose rule with an
executable one.

`tools/local/evaluation_runner.py` (2,811 lines) and `adaptive_screening_runner.py` (1,801) remain
larger maintainability risks than any production module. The design's §13.5 "refactor opportunistically,
not speculatively" is the right call and needs no change.

### 5.7 Programme-level concern the design does not address

The last 40 commits on `main` touched `docs/` 111 times against `src/` 17 times, and documentation
(14,999 lines) now exceeds production source (13,004 lines). Meanwhile B0b recorded Graph, Twin,
Semantic and Test Selection as `NO_CONFIRMED_CAUSAL_EFFECT`. PR #102 proposes to build a Semantic
Working Set on top of exactly those four capabilities and adds 1,745 further lines of design with no
production code. This is the pattern the audit was asked to challenge, and it should be challenged.

---

## 6. Changes made during this audit

Applied on `agent/weak-local-evidence-protocol`. Full suite green (329 tests), `ruff` and `mypy` clean.

| Change | Kind | Effect |
|---|---|---|
| `twin/source_snapshot.py`: scope resolved by `git ls-files --exclude-standard`, filesystem walk only for non-Git roots; `file_limit` raised to `ERROR` | P0 fix | Twin nodes 75,712 → 1,925; `src/` 0 → 886 nodes |
| `context/serialization.py` (new): owns the emitted payload **and** `estimate_payload_tokens` over it | P0 fix + CONSOLIDATE | Estimator fidelity 5.1x → 1.01x; adds `delivered_evidence_tokens` |
| `testing/selection.py` (new): the six test-path heuristics moved out of the facade | CONSOLIDATE | `application.py` 1,752 → 1,533 lines |
| `tests/architecture/test_application_facade.py` (new) | enforcement | Line budget + relocated-helper ban; the §13.2 rule becomes a test |
| `tests/integration/test_twin_lifecycle.py`: two regression tests | enforcement | Pins gitignored-corpus exclusion and `ERROR` truncation |
| `tests/unit/test_context_intelligence.py`: cost-fidelity test | enforcement | Pins estimate == delivered payload |

No behaviour was added, no capability was promoted, no evaluation threshold was changed.

---

## 7. Verdict and the smallest slice that may merge next

### 7.1 On PR #102: `NARROW_AND_RETEST`

Do not merge as drafted. Merge a reduced document that:

1. **keeps** §3.2 non-duplication rules, §12 quantization boundary, §15 evaluation contract, §17
   rejected alternatives, §18 definition of done — these are the document's real contribution;
2. **deletes** §6.4 EvidenceAtom, §6.5 Evidence Gap, §6.6 ChangeCapsule, §10.2 shadow reservoir and
   §14's renumbering, replacing each with a pointer to `C2_EVIDENCE_DELIVERY_DECISION.md`;
3. **moves** §6.2 Semantic ABI, §8 TaskExecutionState, §9 Project Memory and §7.3 HTML out of C2 into
   a deferred set with explicit entry evidence;
4. **adds** the missing capability-gating section: which `CapabilityName` owns each mechanism, at which
   depth, and how each is ablated;
5. **corrects** the four factual claims in §2 of this audit.

Expected size after narrowing: ~250 lines, not 950.

### 7.2 The smallest implementation slice that may merge next

**Slice C2-0 — restore a valid measurement basis.** Nothing else in C2 is interpretable until this
lands.

1. The two P0 fixes and their regression tests (§6) — already implemented, ready to review.
2. Wire `AnalysisBudgets.max_files` / `max_file_bytes` into `SourceSnapshotter`, or delete the five
   fields that have no consumer. Dead budget config must not survive a stage that is about budgets.
3. Re-run `tools/local/c2_evidence_protocol.py` on the repaired Twin and seal the result as the C2
   baseline, replacing any artifact produced against the starved Twin.
4. Report `delivered_evidence_tokens` alongside `estimated_evidence_tokens` in every C2 measurement.

**Exit:** a sealed preflight artifact whose `oracle_projection_equal` failures are attributable to PI
selection precision rather than to project scope, and an estimator whose error against the delivered
payload is under 10%.

**Only then C2-1** (attribution telemetry, per the already-merged C2-A). Do not begin contract
extraction, ABI fingerprinting, memory or task state in the same PR.

### 7.3 The smaller architecture that delivers ~80%

Most of the bounded-context value is available from four things the repository already owns:

1. a correctly scoped Twin (now fixed);
2. an honest cost model (now fixed);
3. `select_tests` + `derive_required_verification_set` as the protected-evidence source — obligations
   already exist and already carry criticality and provider IDs;
4. AnswerIR/deterministic projection for the 20 measured `PROJECTION_SCHEMA_ERROR` cells.

Item 4 targets the *only* failure class with measured evidence behind it. Semantic contracts, ABI
fingerprints, working-set compilers, memory and a task engine are all downstream of failures that have
not yet been observed on a valid Twin. Build item 4, re-measure, and let the next mechanism be chosen
by the attribution data rather than by the roadmap.

---

## 8. Open questions for the author

1. Which measurement, taken on a correctly scoped Twin, shows that confidence-ordered packing loses a
   mandatory relation? Without it, the Coverage Optimizer is unmotivated.
2. What is the accepted false-stop rate for the contract fingerprint, and on which labelled corpus is
   it measured?
3. Which `CapabilityName` and depth owns each proposed mechanism, and how is each ablated?
4. Is `EvidenceScope` or `orchestration.ContextScope` the single scope ladder? Two exist today.
5. What invalidates a decision-memory entry, given that no file change makes a design decision stale?
