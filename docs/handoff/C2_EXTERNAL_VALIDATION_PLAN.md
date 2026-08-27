# C2 External Validation Plan

Status: **active work order for C2, after the 2026-08-26 corrective slice.**

This is a handoff. It assumes no memory of the session that produced it. Read
`C2_PLAN_REVISION_AND_ADOPTION_DECISIONS.md` for why the stage was re-sequenced, and
`C2_TRUTH_SCOPE_AND_COST_FIDELITY_CORRECTIVE_DESIGN.md` for the two defects that made earlier
measurement meaningless. This document says what to do next and in what order.

Branch: `agent/weak-local-evidence-protocol`.

---

## 1. What is proven, and what is not

**Proven, on three tasks.** Critical-evidence recall on the sealed tuning tasks
`eca-symbol-001`, `eca-impact-001`, `eca-tests-001` went from 0.24 to **1.00**, with delivered
envelopes of 3,105–4,385 tokens inside the 8k target. Raw recall matched normalized recall, so the
projection gap is closed. Measured by `tools/local/c2_evidence_recall.py`, no model calls.

**Not proven, and this is the point of this plan.**

- All 13 sealed tasks are from **this program's own repositories** — `eca-*` (ExtendCodeAgent),
  `cd-*` (ControlDeck), `kasane-*` (KasaneCore). **No public project is in the corpus.** The 1.00
  above is measured on the codebase PI was designed against, which is the weakest evidence position
  available.
- Recall is a **delivery** metric. It says PI handed over the required facts. It does not say the
  model used them, nor that the task succeeded, nor that PI beat a model with plain search.
- B0b recorded zero PASS delta between forced-PI and off arms. Until that is re-measured on a corpus
  weighted toward tasks PI can actually help with, "PI is useful" remains unsupported.

**Do not treat recall 1.00 as product evidence.** It is an instrument reading on three cells.

---

## 2. Why external validation comes before more mechanism

The corrective slice showed the binding constraints were selection recall and projection encoding,
and both were closed by consolidating capabilities ECA already had — no semantic contract, ABI
fingerprint, working-set compiler, project memory or task engine was needed. The remaining C2 items
(stable-prefix consolidation, compliance measurement, compression curve) are optimisations of a
delivery path whose **usefulness has never been demonstrated against a baseline**.

Spending on optimisation before demonstrating effect is how B0b's null result was produced: a corpus
that could not detect the effect, measured with an instrument that was reading the wrong project.

So: prove effect on external code first. If step 3 below shows no effect on the task classes where PI
should help, then §4's items are not worth building, and that is a finding rather than a failure.

---

## 3. Task classes, stratified by whether PI can plausibly help

Enumerating every coding task is less useful than separating the ones PI could move from the ones it
cannot. Mixing them is what makes an effect undetectable.

**High PI value — facts a model cannot cheaply find by reading the file in front of it**

| class | what PI supplies | covered today |
|---|---|---|
| change impact / blast radius | reverse dependency closure | `eca-impact-001` |
| which tests must run | obligation providers, intent match | `eca-tests-001`, `kasane-tests-001` |
| caller and re-export location | equivalence across re-exports | `eca-symbol-001`, `cd-symbol-001` |
| requirement to implementation trace | traceability | `cd-requirement-001`, `kasane-requirement-001` |
| cross-boundary flow (UI → API → backend) | cross-language relations | `cd-cross-boundary-001`, `kasane-cross-boundary-001` |
| safe deletion | who still references this | **not covered** |
| API/schema change and its consumers | consumer closure | **not covered** |
| dependency or version upgrade across call sites | call-site enumeration | **not covered** |

**Low PI value — a model with plain search already has what it needs**

single-file edits, formatting, writing a new isolated function, adding a field to a local struct,
docstrings. `eca-negative-001` exists as the negative control and should stay one.

**Unknown, worth measuring separately**

multi-file refactor (`eca-refactor-001`), bug fix from a stack trace (`cd-bug-001`), performance
regression, security fix, test authoring as opposed to test selection, reviewing a diff.

**Rule for the corpus: report high-value and low-value classes separately, never pooled.** A pooled
average is exactly what hid the signal in B0b.

---

## 4. Work order

Each step gates the next. Do not skip ahead to §4.4 because it is more interesting.

### 4.1 Generalise the recall instrument

`tools/local/c2_evidence_recall.py` currently hardcodes three `eca-*` task ids and their target refs.
Make it take a corpus descriptor: a repository path, a pinned commit, and a list of
`(objective, target_refs, required_facts)` cases. Keep the existing sealed-suite path working so the
three-task baseline stays comparable.

Exit: the same 1.00 reproduces on the sealed tasks through the generalised entry point.

### 4.2 Pin one public repository and generate oracles from merged pull requests

This is the cheap way to get labelled tasks at volume, and it is why external validation is
affordable at all.

A merged PR is a natural oracle:

```
merged PR / commit
  → files changed          = impact ground truth
  → tests changed with it  = test-selection ground truth
  → PR body / linked issue = requirement-trace ground truth
  → the regression test it adds = bug-fix ground truth
```

Two constraints that must not be violated:

1. **Build the Twin at the commit's parent.** Evaluating against a Twin that already contains the
   change is circular. Check out the parent, index, then ask.
2. **A PR is what someone did, not what was necessary.** It over- and under-shoots. Treat
   files-changed as an *upper* bound on required impact and tests-changed as a *lower* bound on
   required tests, and report both rather than a single accuracy number.

Follow the promotion checks already written in `docs/evaluation/github-corpus-candidates-v1.json`
§`selection_policy.required_checks_before_promotion` — pin an immutable SHA, confirm analyzer language
support, reproduce setup in an isolated checkout, classify network/credential dependencies, measure
full-suite wall time, and reserve a held-out split before any tuning.

**Corpus admission criterion, learned the hard way.** The first attempt used `psf/requests`, which
has 96 files and 8 test files. A search baseline listed every candidate it found — 60 of 60 — for
about 700 tokens and scored 0.96 without ever being budget-constrained. **A selection mechanism cannot
be shown to help where nothing has to be selected.** Before a corpus is admitted, the search arm must
be budget-constrained on most cases; `tools/local/c2_baseline_compare.py` now reports
`discriminating_cases` and returns `NOT_DISCRIMINATING` when it is zero.

In practice that means thousands of files, not hundreds — which is the product's premise anyway. Start
with **one** repository large enough to discriminate. Breadth is worthless until one works end to end.

Exit: a sealed corpus file with at least 30 cases across the high-value classes, held-out split
reserved.

### 4.2b RESULT — on a repository large enough to decide, plain search wins

`django/django` pinned at `05a5244b`, 7,085 files, Twin of 49,775 nodes and 220,934 edges across 609
test files. Thirty test-selection cases from its own later commits. **All thirty budget-constrained**,
so the comparison is meaningful — unlike `psf/requests`, where none were.

```
PI envelope   recall 0.428     105 items    7,842 tokens    74.8 tokens per item
plain search  recall 0.964     562 paths    7,840 tokens    14.0 tokens per path
delta        -0.537      PI ahead 0 of 30, tied 13, search ahead 17
```

**PI does not win a single case.** Three limits compound, and each is measured rather than inferred:

1. **Candidate cap.** `_PROTOCOL_MAX_CANDIDATES = 256` against a Twin of 49,775 nodes. Every case
   reports `candidate_search_bound_reached`: PI selects from **0.5% of the graph** while the search arm
   ranks 3,872 candidates.
2. **Representation cost.** An evidence item carries id, ref, path, kind, summary, reason, confidence,
   provenance_id and status — 74.8 tokens. For a question whose answer is a path, eight of nine fields
   are overhead, and the baseline pays 14.0. That is a 5.3x handicap PI's selection would have to
   overcome before it can win anything.
3. **Selection does not compensate.** Even where PI's items land, 0 of 30 cases come out ahead.

This is a **scale** finding, and it is the regime the product is aimed at. At 96 files nothing
discriminated; at 7,085 files PI is decisively behind plain search on this task class.

What it does not show: only `test_selection` was measured, on one repository, with one oracle type,
at the delivery layer. Impact, requirement trace, cross-boundary and safe-deletion classes are
untested, and task outcome is not measured at all. It also does not show PI's fields are worthless —
confidence, provenance and status buy trust, which recall does not score.

What it does show, and what §4.4 must respect: **on path-shaped questions over a large repository, the
current envelope is a net loss against grep at equal cost.** Optimising its prefix or its compression
curve cannot repair a 5.3x representation handicap over a 0.5% candidate pool. If PI is to earn its
place it must deliver what search cannot produce — relations, obligations, staleness, contradiction —
and be measured on classes where those are the answer.

### 4.2c Why context is large, classified against measurement

The Django result above measured **localization** — which file holds the answer — and that is the one
class where plain search is optimal by construction. Reporting it as a verdict on PI targeted the
wrong surface. Classifying the actual causes changes what is worth building.

| # | cause | measured | does search suffice? | countermeasure |
|---|---|---|---|---|
| 1 | where to look | grep recall 0.96 at 7,840 tokens | **yes** | PI should not compete here |
| 2 | the code being edited | median symbol 7 lines in a 367-line file — **52x waste** | no | **precise extraction; unbuilt** |
| 3 | blast radius | `impact.affected_symbols: 0` for a `file://` target | partly | accept file refs; measure on symbol refs |
| 4 | what to verify | `coverage_complete: False`, `fallback: full_suite` | no | depends on 3 |
| 5 | session accumulation | PI is 21% of the prompt; 79% is the agent loop | — | fewer round trips, which needs 2 and 3 |
| 6 | output starvation | zero answer at 512 and 1,024 output tokens | — | reserve headroom first (done) |

**Cause 2 is the largest measured waste and is entirely unbuilt.** Django's Twin holds 20,704
function and method nodes carrying `start_line` and `end_line`; the envelope emits a `summary` — the
symbol's name — and never the body. An agent that cannot be handed the symbol reads the file, and the
median file is fifty-two times the median symbol.

**Cause 3 is broken for how developers work.** Impact answers "I changed this symbol"; a developer
changes a file. With a `file://` target, `affected_symbols`, `focused_tests` and `candidate_tests` are
all empty, so the Django comparison ran with PI's main impact mechanism contributing nothing.

Consequence for §4.3: measure PI on causes 2 and 3, not on cause 1. A recall metric over path lists
also rewards shotgunning — grep delivered 562 paths to hit 1.5 required facts, precision 0.0029
against PI's 0.0076 — so precision and F1 must be reported alongside recall, and neither arm is
usable at those precisions.

### 4.3 Paired effect measurement: PI envelope versus plain search

The first measurement in this programme that can say "PI is useful".

Same task, same model, same output budget, two arms:

- **PI arm** — the bounded envelope from `pi_context view=envelope`.
- **Baseline arm** — no PI; the model gets the objective and may use its own search/read tools.

Report per class from §3, never pooled. The primary comparison is task/oracle success; secondary are
total context tokens, tool calls and wall time.

Model route: the sealed arm is the `local-practical` port-8090 Qwen route
(`docs/evaluation/b0a-quality-target-v2.json`). The ControlDeck gateway at
`http://127.0.0.1:8765/api/v1/llm/v1` is a **different route**; anything measured through it is
diagnostic and must not be recorded in `docs/evidence/final/` without a route/provenance decision.

Reserve at least 2,048 output tokens. Measured on Qwen3.8-27B, a real envelope produced **zero answer
characters** at 512 and at 1,024 because the reasoning model spends the budget thinking first; see
`C2_PLAN_REVISION_AND_ADOPTION_DECISIONS.md` §4b.7.

Exit: a sealed paired result per class. **If the high-value classes show no effect, stop and report
that.** It is a legitimate outcome and it invalidates §4.4.

### 4.4 Only if §4.3 shows effect

- **Stable protocol block.** The task-invariant head must exceed ~520 tokens and be emitted before any
  task-varying content, or none of it is cached. ECA's is ~330 tokens and sits after the objective on
  both routes, so it is currently worth nothing. Consolidating the gap taxonomy, scope ladder,
  AnswerIR schema and citation contract into one 2–4k-character block would earn its place on clarity
  grounds and then be ~78% free after the first call. See §4b.5 and §4b.8.
- **Protocol compliance.** Does the model cite evidence ids, treat omission as non-negative, and
  expand only for a named gap? A sufficiency gate the model ignores is not a gate.
- **Compression curve.** 8k/16k/24k/32k/48k/64k on total context including output headroom.

---

## 4d. Narrow first, widen on failure — and where that rule stops

Adopted after measurement: Impact's recommended tests reach precision 0.068 at depth 1, peak at 0.112
at depth 2, and by depth 6 buy recall 0.47 at precision 0.104. The full closure is the worst case paid
on every request — for `django/db/models/sql/query.py` it is 24,428 symbols while the change needed
one test. The ladder therefore starts at the narrowest rung the objective justifies and widens when a
caller asks, because the narrow answer did not hold.

**This rule governs the edit loop, not the completion gate.** "I changed something, ran the nearby
tests, and they pass" does not mean the change is safe: a break outside the narrow scope is undetected
precisely because those tests were never run. Treating a narrow pass as completion is the
`false_sufficient` failure named in `C2_EVIDENCE_DELIVERY_DECISION.md`, and it is why AGENTS.md keeps
the full suite available for release, high-uncertainty and calibration runs.

Two questions, two mechanisms:

| question | mechanism | may start narrow? |
|---|---|---|
| did my change work? | scope ladder, widen on failure | **yes** |
| is this change safe to complete? | required verification set | **no** — coverage is required, not sampled |

An implementation that answers the second with the first has not saved context; it has moved a risk
somewhere it will not be seen.

## 5. Standing constraints

- Every C2 mechanism declares its `CapabilityName`, its `D0..D4` depth and its ablation arm before
  implementation. Master Plan invariant 6.
- The full-suite fallback stays. The one recall miss found during the corrective slice was a test that
  guards its target through a value flowing across four modules with no call edge between them; intent
  matching recovered it, but that class of coupling is not generally reachable statically.
- `data_flow`, `side_effects`, `state_event`, `api_schema_db`, `ui_graph`, `memory` are declared and
  forced `off`. One observed instance is not a mandate to implement any of them.
- Report high-value and low-value task classes separately, always.
- Recall is a lower bound: it counts facts named in the oracle's answer, not facts needed to reason.
