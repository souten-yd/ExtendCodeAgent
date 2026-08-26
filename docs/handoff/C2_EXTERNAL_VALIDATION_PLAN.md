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

Start with **one** Python repository of moderate size. Breadth is worthless until one repository works
end to end.

Exit: a sealed corpus file with at least 30 cases across the high-value classes, held-out split
reserved.

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
