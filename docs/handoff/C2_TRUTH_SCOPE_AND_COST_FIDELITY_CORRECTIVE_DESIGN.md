# C2-0 — Truth Scope and Cost Fidelity Corrective Design

Status: **stage-local corrective design for C2, ahead of C2-A attribution telemetry.**

Canonical owners are unchanged. `docs/PI_MASTER_EXECUTION_PLAN.md` owns the backlog;
`docs/handoff/C2_EVIDENCE_DELIVERY_DECISION.md` owns the C2 evidence-delivery contract. This document
adds only the corrective slice that must precede them, and records the contracts that slice
establishes. It supersedes no merged decision.

Origin: `docs/audit/C2_CONTEXT_VIRTUALIZATION_INDEPENDENT_AUDIT.md` §3 and §6.
Applied at: `agent/weak-local-evidence-protocol`.

---

## 1. Goal

> Make C2's measurements mean what they claim, before any C2 mechanism is chosen on the strength of
> them.

C2 is a *measurement-gated* stage: its exit is "repeated distributions showing task-success or cost
improvement". Two production defects meant neither the numerator nor the denominator was valid. The
corrective goal is narrow and falsifiable:

1. the Digital Twin of a project contains that project, and never silently contains something else;
2. a token budget is enforced against the payload the consumer actually receives;
3. both properties are held by tests, not by prose.

Non-goals: no new capability, no new contract for contracts, no promotion, no threshold change.

---

## 2. Root causes

### 2.1 Truth scope — the Twin indexed the wrong project

`SourceSnapshotter` combined three decisions that are individually reasonable and jointly wrong:

- scope came from a recursive filesystem walk;
- exclusion came from a hard-coded `IGNORED_NAMES` set that must be kept in sync by hand;
- overflow was a bounded cap reported at `INFO` severity.

A walk cannot distinguish project source from build output, vendored checkouts or evaluation corpora.
The hand-maintained set omitted `.evaluation/`, which the repository's own `.gitignore` does list.
Lexicographic order put it first, and the cap did the rest.

Measured on this repository before repair:

| | value |
|---|---|
| scannable files | 207,308 |
| of which `.evaluation/` | 207,037 |
| index of first `src/` file | 207,147 |
| `max_files` | 10,000 |
| Twin nodes | 75,712 (75,709 from `.evaluation/`) |
| Twin nodes from `src/` | **0** |

The general failure, not specific to this repository: **any project with a large ignored directory
sorting before its source silently gets a Twin of that directory.** The cap's diagnostic was
informational, so nothing failed and nothing warned.

### 2.2 Cost fidelity — the budget measured a different object than the one delivered

`ContextItem.token_estimate` was `(len(canonical_ref) + len(summary) + len(why_included)) / 4`, while
the delivered item also carries `revision`, `provenance` (three fields), `confidence`, `status` and
`kind`. The estimate and the payload were produced by different modules, so nothing forced them to
agree, and they diverged by 5.1x.

The weak-local path had already avoided this by estimating over its own compact payload — but it built
that payload twice, once for the estimate and once for the consumer, so the two could drift apart at
the next edit.

---

## 3. Contracts established

### C-1 — Project scope is the project's own declared scope

> In a Git worktree, the set of files a Twin may index is exactly
> `git ls-files --cached --others --exclude-standard`. A recursive walk is a fallback for non-Git
> roots only, and remains subject to `IGNORED_NAMES`.

Rationale: the repository already declares what belongs to it. Reusing that declaration removes a
hand-maintained list, makes exclusion correct by construction for every consumer's project, and costs
one subprocess call. Every snapshot records which rule resolved its scope, as a `snapshot_scope`
diagnostic.

### C-2 — Truth truncation is an error, never a note

> Reaching `max_files` means the Twin covers a prefix of the walk order rather than the project.
> It is reported at `DiagnosticSeverity.ERROR`.

Rationale: a partial Twin does not degrade answers proportionally — it makes them answers about a
different codebase. Silent partial truth is the failure mode C2 exists to eliminate.

### C-3 — One owner for the delivered payload and its cost

> The module that emits a context payload owns the estimate of that payload's cost. An estimate is
> computed over the emitted shape, including the estimate field itself, to a fixed point.

Rationale: a budget enforced against a shape the consumer never receives is not a budget. Co-locating
them makes agreement structural. The self-reference (the estimate is a field of the payload it
measures) settles in at most three rounds and is asserted by test.

### C-4 — Domain behaviour has a domain owner, enforced by test

> The application facade may resolve policy, load a snapshot, invoke domain services, serialize and
> record timing. Domain heuristics live in their domain package. This is checked by
> `tests/architecture/test_application_facade.py`, not asserted in prose.

Rationale: the facade imports every domain, so it is the path of least resistance for new algorithms.
Behaviour that lands there is invisible to its domain's tests, unreachable by other consumers, and not
ablatable with its capability. The prose rule already existed and had already been violated.

---

## 4. Implementation

| Module | Change | Contract |
|---|---|---|
| `twin/source_snapshot.py` | `_candidate_paths()` resolves scope via `git ls-files -z --cached --others --exclude-standard`, falling back to the walk; `SOURCE_SNAPSHOT_VERSION` → `v2`; `file_limit` at `ERROR`; `snapshot_scope` diagnostic added | C-1, C-2 |
| `context/serialization.py` **(new)** | Owns `context_item_json`, `context_package_json`, `weak_local_evidence_json`, `canonical_bytes`, `estimate_payload_tokens`. Adds `delivered_evidence_tokens` to envelope metrics | C-3 |
| `context/service.py` | `_context_item` estimates over the emitted payload to a fixed point; weak-local path reuses the shared item shape and estimator instead of building its own | C-3 |
| `service/application.py` | `_context_json` / `_weak_local_evidence_json` removed and delegated to `context`; the six test-path heuristics removed and delegated to `testing` | C-3, C-4 |
| `testing/selection.py` **(new)** | `test_obligation`, `uncovered_obligations`, `focused_test_paths`, `objective_test_paths`, `structural_test_paths`, `intent_architecture_test_paths`, `direct_use_count` | C-4 |

`SOURCE_SNAPSHOT_VERSION` is bumped because the analyzer-version tuple participates in Twin refresh
selection: existing revisions built under `v1` must be treated as produced by a different scope rule.

### 4.1 Tests added

| Test | Pins |
|---|---|
| `test_git_ignored_corpus_never_starves_the_project_source_scope` | C-1 — a 40-file gitignored corpus under a `max_files=20` cap must not displace `src/` |
| `test_file_limit_truncation_is_reported_as_an_error` | C-2 |
| `test_context_item_cost_matches_the_delivered_payload` | C-3 |
| `test_application_stays_within_its_facade_line_budget` | C-4 — ratchet, currently 1,600 |
| `test_relocated_domain_helpers_are_not_redefined_in_the_facade` | C-4 |
| `test_context_payload_and_its_cost_estimate_share_one_owner` | C-3 |

---

## 5. Measured effect

Same repository, same command (`tools/local/c2_evidence_protocol.py`), before and after.

| Metric | Before | After |
|---|---|---|
| Twin nodes / edges | 75,712 / 429,958 | 1,925 / 13,207 |
| Twin nodes from `src/` | 0 | 886 |
| Legacy estimator error vs delivered payload | 5.1x under | 1.01x |
| Envelope candidate count (symbol task) | 256 (cap saturated) | 70 |
| `candidate_search_truncated` (symbol task) | True | False |
| Unresolved gaps (symbol task) | 5 | 0 for a targeted objective |
| `pi_symbol` definition for `select_tests` | corpus artifact | `src/extendcodeagent/testing/service.py` |
| `application.py` | 1,752 lines | 1,533 lines |
| Suite / lint / types | 323 green | 329 green, `ruff` and `mypy` clean |

`oracle_projection_equal` remains `false`, and this is the point: the residual mismatches are now
genuine test over-selection (for example `test_python_semantic.py` and `test_javascript_typescript_
semantic.py` selected for a `select_tests` locate task) rather than a Twin of the wrong project. C2
has a valid signal for the first time.

---

## 6. Remaining gaps, with corrective direction

Recorded so the next stage inherits them explicitly rather than rediscovering them.

### G-1 — `AnalysisBudgets` is 7/8 dead config *(open)*

`max_files`, `max_file_bytes`, `max_graph_nodes`, `max_graph_edges`, `incremental_batch_ms`,
`background_workers`, `memory_budget_mb` have no consumer; only `max_depth` is read. `SourceSnapshotter`
is constructed with its own defaults, so configuring `max_files` does nothing.

**Direction:** wire `max_files` / `max_file_bytes` through `TwinService` into `SourceSnapshotter`, and
delete the remaining five fields. A stage about budgets cannot ship inert budget configuration. A
config key that silently does nothing is worse than an absent one.

### G-2 — `_infer_scope` is degenerate *(open)*

All three C2 tasks classify as `EvidenceScope.VERIFICATION` because the heuristic matches the
substrings `test` / `verification` / `requirement` / `evidence`, which occur in nearly every objective
in a project-intelligence repository. Scope inference is effectively constant, so the scope ladder
never starts narrow.

**Direction:** derive scope from the C1 `IntelligencePlan.context_scope` — which is already computed
deterministically from `TaskIntent` and is already the designated task/plan source — instead of from
substring matching on raw objective text. This also resolves G-3.

### G-3 — two scope ladders exist *(open)*

`context.EvidenceScope` (`symbol`/`neighborhood`/`impact`/`verification`/`subsystem`) and
`orchestration.ContextScope` (`none`/`symbol`/`neighborhood`/`impact`/`runtime_boundary`/`strategic`/
`research`) overlap on three values and disagree on the rest.

**Direction:** `orchestration.ContextScope` is the plan-side vocabulary and stays. `EvidenceScope` is
the evidence-side ladder and stays. Exactly one total mapping between them is defined, in the context
domain, at the point where a plan is consumed — and no third ladder is introduced by C2. Do not
add the mapping before there is a consumer that wires plan → evidence request.

### G-4 — objective anchor terms are unfiltered *(open)*

Emitted gaps included `objective_anchor_missing:plus`, `:covers`, `:order.`, `:boundary.` — stop-word
filtering is incomplete and trailing punctuation is not stripped, so `_TERM_PATTERN` admits sentence
noise as evidence anchors.

**Direction:** strip trailing punctuation in `_objective_terms`, and treat the stop list as a symptom:
the durable fix is G-2, since a plan-derived scope supplies target refs rather than inferring anchors
from prose.

### G-5 — the analyzers carry no contract surface *(open, out of C2-0 scope)*

Node properties are `name`, `qualname`, `start_line`, `end_line`, `intent_tokens`, `scope`,
`bound_name`; edges are `contains`, `defines`, `imports`, `depends_on`, `calls`, `may_call`,
`references`, `inherits`, `decorated_by`. No parameters, annotations, return types, visibility, raised
exceptions or effects.

**Direction:** this is the real precondition for any Semantic Contract or ABI-fingerprint work, and it
belongs to the `side_effects` / `state_event` / `api_schema_db` capabilities that are already declared
and forced `off` — not to the `context` domain. Any such work must first declare its `CapabilityName`,
its `D0..D4` depth and its ablation arm.

### G-6 — capability gating is unspecified for every proposed C2 mechanism *(open)*

Master Plan invariant 6 and AGENTS.md require that a mechanism which cannot be switched off cannot be
shown to be worth its cost. No proposed C2 mechanism currently declares an owning `CapabilityName`,
a depth, or an ablation arm.

**Direction:** every C2 work package declares these three before implementation, and
`tests/architecture/test_capability_gating.py` is extended to hold the declaration. Six of the
mechanisms map onto capability names that already exist and are forced `off`: `side_effects`,
`state_event`, `api_schema_db`, `ui_graph`, `memory`, `data_flow`.

---

## 7. Definition of done for C2-0

1. A Twin built on any project contains that project's declared source scope, or fails loudly.
2. Truncation of Project Truth is an error-severity diagnostic and is visible in `pi_status`.
3. Every delivered context payload's cost estimate is within 10% of the payload actually emitted.
4. `delivered_evidence_tokens` accompanies `estimated_evidence_tokens` in every C2 measurement.
5. The C2 preflight artifact is re-sealed against the repaired Twin, and any artifact produced against
   the starved Twin is withdrawn rather than compared against.
6. Residual `oracle_projection_equal` failures are attributable to PI selection precision.
7. G-1 is closed — budget configuration either works or is removed.
8. The facade boundary is held by `tests/architecture/test_application_facade.py`, and its line budget
   ratchets downward only.

Until 1–6 hold, no C2 context-reduction number may be cited as evidence for the 32k/64k target, and
no C2 mechanism may be adopted or rejected on the strength of a measurement taken before this slice.
