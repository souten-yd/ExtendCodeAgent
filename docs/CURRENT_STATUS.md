# ExtendCodeAgent — Current Status

Status date: 2026-08-17

## Program state

Overall: **A-I COMPLETE — PHASE 0 COMPLETE — E0-E5 AND V0a COMPLETE — B0 COMPLETE — B1 SKIPPED — B2 COMPLETE — C0-C1 COMPLETE — C2 NEXT**

C1 completed at implementation revision `aa446d1` without a model call. The host-neutral
orchestration layer projects the bounded C0 collector into `TaskSignals`, deterministically emits
`TaskIntent` and a minimum initial L0-L5 `IntelligencePlan`, and retains only a transient
`PlanOutcome`. It is strictly shadow-only: no capability executes, no context is delivered, no model
route or verification changes, and no user-visible intervention occurs. Production rules receive no
evaluation task ID/class/oracle input and the architecture gate rejects EvaluationPIPlan/task-ID
coupling.

The sealed C1 evaluation reuses all 13 manual-reviewed expected plans (9 tuning, 4 repository-held-
out) without changing the task suite, oracle, corpus or thresholds. Intent accuracy, capability
precision/recall and exact capability/depth match are 1.0 on both splits; under- and over-selection
are 0.0. This is plan-selection evidence, not capability-efficacy or task-success evidence. Across
1,300 deterministic decisions p95 was 27 us and maximum 412 us, with zero repository I/O and zero LLM
calls. Actual injected context is zero; shadow planned context budgets average 3,582.769 tokens and
max at the existing 8,192-token configured bound. Evidence:
`docs/evidence/final/c1-shadow-planner-result-v1.json`.

C2's conditional entry is now satisfied by the previously measured bounded-evidence defects: 20 B0b
cells had sufficient PI facts but incorrect final schema, `pi_symbol`/`pi_context` dominate injected
data, and C1 proves that minimum task/capability/depth plans can be chosen deterministically. C2 must
address only those measured protocol gaps. `local-low` remains `UNAVAILABLE / NOT_CONFIGURED`; under
the local-only execution exception C2 may evaluate only `local-practical` and makes no local-low or
cross-tier claim.

C0 completed at implementation revision `0a8a846` without an LLM call. The new host-neutral runtime
contract has an exhaustive 12-capability descriptor, explicit supported/degraded/unavailable states,
and a bounded `TaskSignalCollector` consuming task, session, exact ProjectRef workspace/root,
mutation, model and advisory-delivery signals. Existing immutable `RuntimeObservation` remains the
single tool/verification evidence path and now carries optional runtime session/call identity with
backward-compatible loading. OpenCode 1.18.18 normalizes its task/model/session/advisory types inside
the TypeScript adapter and passes a real TypeScript-to-Python sidecar conformance check. Automatic
context delivery and ECA-owned model requests are `UNAVAILABLE`, not PASS; mutation observation and
verification are explicitly degraded. Full gates pass 213 Python + 14 adapter fast tests, 96 Python
+ 14 adapter integration tests, and both builds. Evidence:
`docs/evidence/final/c0-runtime-contract-result-v1.json`.

B2 completed at exact main `87ced9f`. Its zero-model preflight passed all five stack/restart checks and
both degraded-sidecar orders. The Qwen Bridge then accounted for five stacks with 16 newly executed
step requests and four compatible reused native requests; all five task/oracle results passed, both
combined orders recorded four runtime observations, and no duplicate call ID or exact-workspace
lingering sidecar occurred. Full prompt context had p95 17,958 and maximum 17,990 tokens. The exact
tuple is classified `degraded`, not `compatible`, because OMO's standalone tool inventory already
duplicates `glob/grep/skill/task` and both combined orders preserve that same limitation. C6 remains
`NOT_TESTED_TEAM_MODE_OFF`; no recommended-stack, general-model or P4 comparative claim is made. See
`docs/evidence/final/b2-omo-coexistence-result-v1.json`. C0 then completed as recorded above.

B2's first exact-main Qwen Bridge completed the native and ECA controls before stopping on the ECA
control. Native passed with four model requests; the ECA coding oracle also passed, but the required
agent-flow runtime observation was absent. The later OMO attempt was operator-interrupted before a
durable cell checkpoint and is retained as an uncounted incomplete request attempt, not as a zero-call
or completed result. A focused repair now awaits runtime ingest in the OpenCode post-tool hook and
handles OpenCode 1.18.18's missing tool-output title. The runner stops after any failed control,
checkpoints operator interruption, and may migrate only the already-passing native/no-plugin result
when every sealed input remains equal. Because the adapter repair changes runtime-evidence semantics,
it is deliberately outside the existing lifecycle-only B0 compatibility exception.

The repaired exact-main rerun at `ace1e94` correctly migrated only native and executed four fresh ECA
model requests, but again stopped on zero runtime observations with the task oracle passing. The
model-free diagnosis found the evaluation configuration—not the task oracle or agent behavior—was
inconsistent: B2 launched ECA in `advisory`, while automatic runtime ingestion is permitted only in
`shadow` or `active`. The next bounded runner repair sets ECA-containing B2 stacks to explicit
`active`, matching the existing `active-scoped(local-practical)` claim; core rollout semantics remain
unchanged and no combined stack is run before this control passes.

The active `b0a-quality-target-v2` progression target is the ControlDeck-managed `local-practical`
Qwen route only.
Its `native`/`off` baseline denominator is 54 cells, followed by an adaptive local screen bounded by
the existing sealed 714-cell exhaustive maximum.
Sonnet/Codex are `NOT_RUN_USER_POLICY / SHARED_QUOTA_EXHAUSTED`, `host-default` is
`NOT_RUN_USER_POLICY`, and `local-low` is `UNAVAILABLE / NOT_CONFIGURED`. No new call or probe and no
claim is permitted for those tiers while the local-only exception is active.

B0a adaptive screening completed at exact merged head `e793103`: 30 new Qwen calls plus 22 reused
results accounted for the full 714-cell contract together with 684 machine-classified avoided calls
(95.7983%). This is observational / agent-selection-weighted screening and evaluation-scheduler call
avoidance—not causal proof for all capabilities and not a production ECA call-reduction metric.
`NOT_TESTED_NO_ACTIVE_USE` is not negative efficacy evidence. The six current candidates (graph,
twin, semantic, impact, test-selection and test-obsolescence) remain intact; no capability was
promoted or demoted. See `docs/evidence/final/b0a-adaptive-screening-result-v1.json`.

The B0b causal-correction entry gate completed at `88d2e17`: 58/58 cells are accounted by 22 new Qwen
calls, 13 compatible reused results and 23 adaptive skips (39.6552% avoided); all 34 forced cells are
exact-trace compliant with no provider/API gap. Requirement tracing and symbol/reference tasks show
intrinsic positive signals. Twin, Semantic, Blueprint and Strategy add positive corrective signals.
The six observational candidates remain preserved, so B0b receives the eight-capability union
`blueprint, graph, impact, semantic, strategy, test_obsolescence, test_selection, twin`. Graph/
Impact/Context/Runtime/Convergence/Traceability gap labels and Test Selection no-signal are corrective
screening diagnostics, not demotions. `research` and corrective test-obsolescence coverage remain
`NO_TASK_COVERAGE`. See `docs/evidence/final/b0a-causal-correction-result-v1.json`.

Auto selection remains a separate axis: eight tasks were measurable, mean precision was 0.666667,
mean recall 0.534821, and 20 `EXPECTED_BUT_NOT_USED` states were recorded. In particular,
`cd-requirement-001` is `PI_SELECTION_GAP` because auto failed while forced passed. B0b confirmation
then completed all 57/57 exact-main local-practical cells: 21 PASS, 36 FAIL, 48/48 forced-use
compliant, with no provider/process/timeout/unavailable outcome. Forced PI versus off and each
covered ON/ablation comparison had zero PASS delta. Graph, Semantic, Twin and Test Selection are
`NO_CONFIRMED_CAUSAL_EFFECT`; Blueprint, Impact, Strategy and Test Obsolescence remain
`NO_HELD_OUT_TASK_COVERAGE`, not no effect. No capability was promoted or demoted.

B0b auto selection measured precision 0.650794, recall 0.530952 and 22
`EXPECTED_BUT_NOT_USED` states. Required-test-set precision/recall was 1.0 across 21 cells, but all
PI/off/ablation variants passed, so the accuracy is not attributable to PI. Full request prompt
context had p95 68,512, p99 86,351 and maximum 93,189 tokens; 128k is a bounded lower-context
candidate, while the configured 262,144 remains unchanged pending an equivalence Bridge. See
`docs/evidence/final/b0b-confirmation-result-v1.json` and
`docs/evidence/final/baseline-gap-report.md`.

The prior three-route checkpoint remains immutable history: Qwen 54/54, Sonnet 54/54, Codex 37/54,
145/162 overall, with 17 Codex cells blocked by quota. It is not the current local-first denominator
and its mixed legacy/current latency is not imported blindly. Its Qwen 54/54 subset must pass the
existing compatibility audit, Bridge Proof and checkpoint migration contracts; only proven residual
cells rerun.

PRs A-I are merged and the implementation baseline is complete. Planning PRs
[#20](https://github.com/souten-yd/ExtendCodeAgent/pull/20) and
[#21](https://github.com/souten-yd/ExtendCodeAgent/pull/21) are also merged. All planning documents
have since been consolidated into a single canonical execution plan,
`docs/PI_MASTER_EXECUTION_PLAN.md`, which replaced eight parallel stage-numbering schemes with one
backlog.

This is not a production-capable designation. B0 is complete, but it did not confirm a held-out PI
causal effect for the covered local-practical tasks. Conditional B1 has no product lifecycle/config/
provider entry condition after closeout and is explicitly skipped. B2 OMO coexistence is active; the
selection/projection gaps remain inputs to C1/C3 and X0 rather than being hidden as successful PI.

## Canonical read order

1. `docs/PI_MASTER_EXECUTION_PLAN.md` — the single execution plan
2. `docs/handoff/NEXT_TASK.md` — the active stage
3. this file — program state and evidence ledger
4. the design detail registered in master plan section 2, for the active stage only

Legacy stage identifiers (`RV-x`, `TA-x`, `AL-x`, `CV-x`, `TP-x`, `VI-Xx`, `RA-x`, `EM-0`, `MA-0`) are
mapped in master plan section 9 and must not be used to schedule work.

## Accepted architectural baseline

- OpenCode remains the agent runtime; ExtendCodeAgent is a host-independent Project Intelligence layer.
- OpenCode-specific APIs remain behind replaceable adapters.
- KasaneCore is a behavioral/reference source, not a directory-copy dependency.
- Reuse/adaptation is preferred over parallel reimplementation.
- Project Graph/Digital Twin/Impact are the first functional foundation.
- Major capabilities are independently configurable and support off/shadow/advisory/active rollout.
- Low-performance local LLMs, practical local coding models, OpenCode host/default models, and frontier models are all first-class targets.
- Model calls use role-based routing and provider-independent adapters; exact model names are configuration, not domain constants.
- Routing supports local-first/frontier-first/host-only/local-only and adaptive/cost/latency/quality policies with explainable escalation/fallback.
- Weak local models receive smaller structured evidence and deterministic candidate sets rather than large repository dumps.
- Privacy policy can forbid remote model/source-code use and remote escalation.
- Deterministic analysis is preferred before model reasoning at every model tier.
- Local tests/E2E/benchmarks are primary evidence; GitHub CI is exceptional.
- Real OpenCode and real-LLM A/B evaluation is required at milestone gates, not on every edit.

## Implementation sequence

| PR | Scope | Status |
|---|---|---|
| Planning PR | architecture, migration audit, implementation/validation/model-routing plan | complete |
| PR-A | foundation contracts, config/capability policy, model-router contracts, local harness | complete |
| PR-B | graph revision/store/source snapshot | complete |
| PR-C | structural/Python semantic/path/impact | complete |
| PR-D | OpenCode adapter + MCP advisory integration | complete |
| PR-E | context/test intelligence/runtime ingest | complete |
| PR-F | Blueprint + task-level Convergence | complete |
| PR-G | live model routing + Strategy | complete |
| PR-H | JS/TS/framework/deep graph expansion | complete; deeper graphs deferred by measurement |
| PR-I | Research/evidence + project-level convergence | complete |

## Capability gating state

Complete inventory as enforced by `tests/architecture/test_capability_gating.py`. Ablatable means the
capability can be set to `off` independently and the corresponding work then does not run.

| Capability | Implementation | Rollout authority | Ablatable |
|---|---|---|---|
| `graph` | implemented | own | yes |
| `twin` | implemented | own | yes |
| `semantic` | implemented | own | yes |
| `impact` | implemented | own | yes |
| `test_selection` | implemented | own | yes |
| `test_obsolescence` | implemented | own | yes |
| `context` | implemented | own | yes |
| `runtime` | implemented | own | yes |
| `blueprint` | implemented | own | yes |
| `convergence` | implemented | own | yes |
| `research` | implemented | own | yes |
| `traceability` | implemented | own | yes |
| `strategy` | implemented | own | yes |
| `call_graph` | implemented | governed by `semantic` | no — ablate `semantic` |
| `cfg` | not_implemented | forced `off` | n/a |
| `data_flow` | not_implemented | forced `off` | n/a |
| `state_event` | not_implemented | forced `off` | n/a |
| `side_effects` | not_implemented | forced `off` | n/a |
| `api_schema_db` | not_implemented | forced `off` | n/a |
| `ui_graph` | not_implemented | forced `off` | n/a |
| `memory` | not_implemented | forced `off` | n/a |

13 capabilities are independently configurable; the other 8 must stay `off` and a non-`off` value is a
`ConfigError`. `pi_status` reports `implementation`, `mode`, `depth`, inferred-relation confidence
floor and `governed_by` for all 21. Rollout authority and D0–D4 cost depth are independent; folded
`call_graph` uses `semantic`'s depth. Rationale
for the `call_graph` folding and the `ConfigError` policy: `docs/handoff/DECISIONS.md` (2026-08-16).

## Immediate next action

Phase 1, B2 OMO coexistence baseline. Revalidate the recorded OpenCode/OMO/ECA tuple, keep Team Mode
off, execute both meaningful plugin load orders, and measure startup/tool/session/basic coding and
verification compatibility under the existing C0-C6 taxonomy. This is compatibility, not the P4
comparative score. Model-bearing checks use only the existing port-8090 Qwen route. See
`docs/handoff/NEXT_TASK.md`.

The first B0a bootstrap checkpoint attempted all nine pinned repositories: seven established a Twin,
while KasaneCore and PEDS exceeded the bounded 300-second initial-Twin limit and are
`EXCLUDED_BOOTSTRAP_GAP`. Only Express and ExtendCodeAgent met their provisional cold-index budgets;
the other five completed Twins exceeded their size-class budget. PI-disabled route checks reached
port-8090 Qwen, host-default, GitHub Copilot Sonnet and GitHub Copilot Codex without provider errors;
local-low remains `UNAVAILABLE`. OMO 4.19.4 + ECA model-free namespace/tool visibility recheck passed.
This is a partial B0a checkpoint, not screening or confirmation evidence.

The current runner defines a 54-cell local-practical `native`/`off` baseline and retains a 714-cell
local-practical screen as the hard maximum. The latter contains 294 paired active/ablation cells plus
capability-specific D0-D4 arms only for semantic, impact, test selection and context. Adaptive
execution first uses active tool traces, deterministic depth equivalence, compatible evidence reuse
and sequential repetition/depth stopping; every omitted cell retains a machine-readable non-effect-
neutral reason. Screening fails closed unless the
exact-head 54/54 report binds the current local-first target seal. The old 306- and 162-cell protocols
remain diagnostic history only.

At clean implementation commit `6cbacaf`, model-free adaptive analysis selected 102 candidate cells
from the 714 hard maximum. Before the first sequential decision it expects 50 results: 23 compatible
reused cells and 27 new calls; the maximum new-call fallback is 79. It classified 534 cells
`NOT_TESTED_NO_ACTIVE_USE` and 78 `SKIPPED_DEPTH_OUTPUT_EQUIVALENT`. One old active-refactor cell was
invalidated because its trace accessed the shared runner `.venv`. The persistent OpenCode Bridge
used one additional Qwen call and failed its adoption conditions: attach changed PASS to FAIL and
took 68,016ms versus the 55,003ms per-cell control. Per-cell OpenCode therefore remains selected.
See `docs/evidence/final/b0a-adaptive-screening-execution-v1.json`. These are scheduler/Bridge
results, not a completed screening table or capability promotion.

A corrected-head comprehensive baseline reached 229/306 before the host-default provider began
returning `Rate limit exceeded`. OpenCode exhausted its retries immediately but the runner waited for
each task timeout and recorded four cells as `TIMEOUT` with projection attribution. This is a runner
classification defect, not model quality. PR #66 at merged head `91b82e3` enables error logging, stops after final
provider retry exhaustion, records stable `provider_failure` categories, and emits
`UNAVAILABLE`/`PROVIDER_GAP`. A real ControlDeck-installed OpenCode route reproduced the rate limit
and completed this classification in 9,103ms rather than the 300,000ms task timeout. The 229-cell
checkpoint remains immutable. The former whole-checkpoint discard decision is superseded by a
sealed compatibility audit: a development-tree diagnostic classified 217 cells as functional reuse
candidates, four as provider gaps and eight as timeouts. No cell migrates until a clean merged runner
reproduces the audit and a 10–20-cell multi-provider Bridge Proof matches the affected classes.
Migrated latency remains separate. The compatibility audit, Bridge proof and migration have since
completed; this paragraph records why the immutable 229-cell source required that process. See
`docs/evidence/final/b0a-provider-gap-runner-repair.json`.

The first 12-cell Bridge run at merged head `7bfca0e` produced eight semantic matches: both
local-practical symbol/impact cells and all six Copilot Sonnet/Codex cells matched. The
local-practical test-selection cell changed from FAIL to PASS, so that model/task class must replay.
All three host-default cells remained `RATE_LIMIT` and are bridge-unavailable, not semantic failures.
This run also exposed that a provider shard continued after its first gap; the runner now pauses that
queue after one triggering attempt while allowing other model queues to continue.

The latest activation at `c95bdfb` observed ready Twin revisions, canonical evidence and
`pi_status`/`pi_symbol` through local-practical, Copilot Sonnet and Copilot Codex. Local-practical and
Sonnet also passed the task oracle; Codex's PI activation passed while its task oracle failed.
host-default remained rate-limited and is the only missing route, so this is
`PARTIAL_PROVIDER_GAP`, not a complete activation PASS. The historical 27-cell pilot separately
audits as 27/27 `REUSABLE` with trace integrity PASS and can be promoted without rerunning it.

A review found that the long schedules had no fail-closed activation precondition. A separately
sealed four-model gate now requires observed `pi_status`, task-bearing PI tool use, active
capability/depth state, Twin revision, canonical evidence and positive PI time before comprehensive
execution. Activation is followed by an interleaved 9-cell port-8090 `native/off/active` pilot
tranche over three representative tasks; only a passing signal continues to 27 total cells. No
objective active gain, missing PI use, provider/timeout failure or active
median above 2x the slower control requires repair and the same pilot again. It also found a blocking
OpenCode reachability gap for `blueprint`, `convergence`, `traceability` and `strategy`; that B1
adapter gap is now repaired as described below. Comprehensive evaluation remains stopped until the
repaired exact-head activation and effect pilot pass; PI effect remains NOT TESTED.

PRs #49-#51 repaired configuration propagation, staged task-interleaved execution and duplicate
plugin/MCP routing. At exact merged head `6064e311c3f98fe37ab87c6c1e71603ef08db7b2`, activation
passed all four required routes. The first sealed 9-cell tranche then produced native/off/active
PASS counts of 0/0/1; active won only the test-selection task, had no observation failure and its
124,194ms median was 1.051x the slower control. This is a positive pilot signal, not comprehensive
effect evidence.

The same-head confirmation stopped after 12/27 checkpointed cells when repetition-2 active symbol
timed out at 300,157ms. This triggers `REPAIR_AND_RETEST`; neither 27-cell confirmation nor 306/714
evaluation may continue. B1 now first separates `RETRIEVAL_MISSING`, `PROJECTION_SCHEMA_ERROR` and
`AGENT_REASONING_ERROR`, and traces cold Twin build, snapshot load, adjacency/index build, query,
JSON serialization and post-tool model reasoning. The measured repair order is compact task
projection, obligation-aware/structural test coverage, revision-scoped query indexes, then missing
OpenCode runtime routes. The sealed tasks and exact oracles remain unchanged.

PRs #52/#53 merged segmented timing and exact-failure attribution. A single exact-head active-symbol
smoke at `1116d6b` proved report/trace agreement: wall 57,990ms, PI tools 161ms, cold Twin 474.730ms,
snapshot load 149.969ms, query 6.191ms, serialization 0.043ms and post-PI agent/model residual
23,066ms; adjacency was unused. The FAIL was classified `RETRIEVAL_MISSING`. This one-cell smoke is
instrumentation evidence only and does not explain the earlier timeout or authorize broader runs.

B1 compact projection is now implemented for the existing `pi_symbol`, `pi_impact` and `pi_tests`
routes without adding tools. OpenCode defaults to compact while direct application callers retain
the detailed view. A clean-workspace deterministic query returns the exact symbol definition,
public export, production source caller and two existing tests for `select_tests`; compact impact
separates focused tests from the wider candidate set and keeps `coverage_complete=false` plus an
explicit unresolved boundary. This is projection evidence only pending the sealed pilot rerun.

The next bounded structural-obligation slice upgrades the Python analyzer to `python_ast.v2`. It
retains repeated call occurrences, derives direct `structurally_covers` relations when a test uses a
module-level `Path` source scope, and stores deterministic test-intent tokens. Compact selection uses
those facts conservatively. On the clean ECA task workspace, `_edge_meets_confidence` now projects
the exact 3 production methods, 4 source uses and 2 focused tests; required-verification selection
returns exactly the unit, integration and architecture files with all three bounded obligations
covered. This is task-grounded repair evidence, not general TestIntent completeness.

A revision-scoped sidecar cache now reuses the immutable `GraphSnapshot`, exact-name symbol index and
`GraphAnalysisService` adjacency indexes, while checking the cheap current revision and invalidating
after every Twin open/refresh. On the clean ECA task workspace after one cold symbol query, cached
snapshot loads measured 0.045/0.018/0.016ms for impact/tests/symbol, adjacency rebuild stayed 0ms and
query execution measured 1.697/0.739/0.244ms. These are one-process query-path measurements, not
large-repository performance acceptance.

The four previously unreachable capabilities now have two bounded OpenCode routes rather than four
extra tools. `pi_plan` derives focused and impact-aware alternatives from graph facts, invokes
deterministic Strategy scoring, and projects the selected result into Blueprint elements; persistence
is explicit and defaults off. `pi_verify` maps requirements to current Twin facts and evaluates both
Traceability and Convergence without upgrading materialized facts to verified evidence. Plugin and
MCP routes are covered by real sidecar calls, and active-mode propagation now includes all four
capabilities. Evaluation output records the capabilities actually reported by each composite tool.
The activation contract maps `eca-refactor-001` to `pi_plan` and `cd-cross-boundary-001` to
`pi_verify`; screening refuses a no-effect classification when those required calls/capability traces
are absent. The sealed task suite and exact oracles are unchanged.

At merged route head `b67f9514937d62a1f235baf95f2e2581183dabc3`, fresh activation passed Qwen,
host-default and both GitHub Copilot frontier routes with no capability gap. The following sealed
9-cell pilot completed without timeout/provider/PI-observation failures, but PASS remained 0/0/0 and
correctly returned `REPAIR_AND_RETEST`. Active median was 113,474ms versus the slower control's
114,317ms (0.993x), so this run shows neither time penalty nor functional gain.

Raw trace inspection found the active agent explicitly requested `view=detail` for symbol and impact,
so none of the repaired compact projections was exercised. The detailed impact response was also
large enough for OpenCode to truncate. Test selection received four source-directory strings rather
than canonical refs and returned `full_suite`; the agent then found only two of three required tests.
The next bounded repair removes the detail choice from OpenCode while retaining core compatibility,
and makes compact test selection accept a task objective plus optional refs. On the exact pilot
workspace, current compact projection returns every sealed symbol and impact fact, while objective
selection returns the exact unit/integration/architecture triplet. This deterministic proof precedes
another real-model pilot and is not itself effect evidence.

After PR #59 and the compact-evidence collector repair in PR #60, exact-head activation passed all
four required routes. A bounded active-only Qwen diagnostic then produced one PASS in three tasks:
test selection passed exactly, while symbol and impact each had PI required-fact recall 1.0 but failed
the final answer. Symbol dropped one known test; impact converted a path into prose and added
unrequested objects. This is the first post-repair functional success but has no controls and is not
pilot-gate evidence. The remaining repair clarifies that requested answer keys are an exact schema
for every arm and that matching active compact fields must be preserved verbatim before the full
sealed 9-cell comparison is rerun.

PR #61 merged the exact-schema clarification. At exact head `170649043f50`, four-model activation
passed and the sealed 9-cell Qwen pilot produced native/off/active PASS counts of 0/0/2. Active PI
required-fact recall was 1.0 for all three tasks; impact and test selection passed exactly, while
symbol retained every fact but converted a one-item list to a scalar. Median wall times were
91,611/100,609/70,107ms. The pilot still fail-closed because `pi_tests` exposes task-ready repository
paths rather than canonical URIs and the collector did not classify those paths as selected evidence.
That attribution defect must be repaired and the same 9 cells rerun before confirmation expands.

PR #62 repaired repository-path attribution. At exact head `d36d9104c822`, activation and the fresh
9-cell pilot passed the initial gate with the same 0/0/2 PASS split, active required-fact recall 1.0,
and no observation failures. Confirmation was stopped at 14/27 after off impact repetition 2 reached
its sealed 420-second timeout. ControlDeck llama.cpp logs show the first Qwen response continuously
generated 27,998 tokens at about 67 tokens/second; PI was not involved. The replacement matrix now
caps local-practical output at 8,192 tokens for every arm, is resealed, and requires a fresh run.
OpenCode runtime validation additionally requires the model context limit; the final sealed provider
pair is context 262,144 and output 8,192, matching the ControlDeck llama.cpp server. The intermediate
output-only activation failed before any model or PI call and is not effect evidence.

At merged exact head `7e58751b05ec`, the completed provider limits passed all four activation
routes and the fresh 27-cell confirmation gate returned `PROCEED_TO_COMPREHENSIVE`. Exact PASS was
native/off/active 0/0/6: impact 3/3 active, symbol 1/3, tests 2/3. Every active symbol/impact PI fact
recall was 1.0; tests was 0.333/1.0/1.0. There were no PI/off observation failures or timeouts.
Active median wall time was 72,100ms versus 105,688/109,601ms controls. This confirms functional
advantage; symbol schema projection and objective-sensitive test retrieval remain measured variance.

The bootstrap blocker has a bounded B1 repair at exact head
`fcd61dff6c66324fed970ecfb1d9b19cae2aa8f7`. A matching current-edge identity index and schema-5
migration reduce exact-pin three-run cold medians to 15,825ms for KasaneCore and 6,368ms for PEDS;
both now pass their size-class budgets and are eligible for held-out work. This performance result
does not establish PI quality. The pre-activation baseline stopped at 137/306 cells on old exact
head `86e8061`; those cells are diagnostic model-variance history only and cannot be reused by the
corrected activation/pilot protocol.

E3 sealed 13 tasks across three task repositories and nine required classes at
`23bf76039ea1e95a29c31c09823f2501bd3658dea305a4e38868eb9e1e6f6632`. The ControlDeck-managed
OpenCode 1.18.16 native proof executed every task: 4 PASS, 9 FAIL, no timeout or unavailability
(30.77%). A clean pinned PEDS full suite measured 756 seconds. OMO 4.19.4 and ECA loaded together
model-free with all nine `pi_*` tools visible; the required local-low model arm remains UNAVAILABLE
because no permitted non-Ollama weak-local endpoint is registered. GitHub reference candidates are
recorded separately and do not alter the v1 split.

E4 sealed 12 promoted Layer A review cases and a 5,083-cell full schedule. The unified runner validates
every versioned input, emits every integrated metric key, archives incomplete workspaces, checkpoints
each cell atomically and resumes without duplicating results. Exact-head route proof exercised native,
advisory, port-8090 Qwen3.6 27B, GitHub Copilot Sonnet and GitHub Copilot Codex through the
ControlDeck-managed OpenCode executable. This is runner/route evidence, not a B0 quality result.

E5 added a compact hash-chained append-only trace with idempotent append, fail-closed replay,
explicit planned-versus-observed capability-state provenance, and no prompts/transcripts/secrets.
Exact-head evidence emitted 115 unique traces over all 23 arms. All local-low cells remain correctly
`UNAVAILABLE`; a real ControlDeck-managed OpenCode advisory cell recorded `pi_status`-observed state
and failed its task oracle. This closes attribution infrastructure only, not the product thesis.

No recorded evidence yet supports the product thesis. The only real-model result,
`docs/evidence/pr-g/model-evaluation.json`, is 6 scenarios at 1 repetition with `tool_calls = 0` in
every arm — a context-injection A/B rather than agent task completion. It is evidence that model
routing works, not that Project Intelligence improves outcomes. See master plan section 5; B0 replaces
it against the sealed E3 task suite.

The ControlDeck-managed OpenCode used by E3/E4 is `1.18.16`; earlier npm-stable evidence used
`1.18.18`, so B0 must report the executable actually used. The old PR-G frontier route failed 0/18,
but E4 confirmed both replacement GitHub Copilot routes are currently callable. This only removes the
route-unavailability observation; quality still requires repeated B0 distributions. No permitted
local-low endpoint is currently registered.

PR-C provides
deterministic structural/Python AST facts, analyzer-owned Python alias resolution, persisted
dependency-aware refresh, bounded path/impact traversal, weakest-link confidence, uncertainty,
explanations, and test-candidate projection. Curated FP/FN review and real-repository repeated-query
measurements are recorded under `docs/evidence/pr-c/`; PR #6 merged as `ef6db532`.

PR-A intentionally has no real OpenCode or real-LLM claim. Live host integration remains PR-D;
live model routing remains PR-G. PR-D now adds a stable OpenCode 1.18.18 TypeScript plugin, six
bounded tools, an authenticated versioned local sidecar, a shared MCP server, coalesced background
events, restart/reconnect handling, and a measured filesystem-watcher fallback isolated to the
adapter. Real model-free OpenCode evidence is recorded under `docs/evidence/pr-d/`; native/off/
shadow/advisory behavior was exercised without transmitting source to a model. PR #8 merged as
`1cc7fd26` after exact local/remote head and mergeability verification.

The local PR-A gates passed on Python 3.12.3: Ruff lint/format,
strict mypy, 25 unit/architecture tests, sdist/wheel build, and wheel-archive import smoke.

PR-B adds file-level Graph facts, immutable Twin revisions, atomic/restart-safe SQLite persistence,
historical snapshots, workspace isolation, expected-head conflicts, bounded source fingerprints,
file-level refresh/invalidation, retention and integrity-checked export/import. Semantic/Impact and
host/model integration remain deliberately absent. The recorded real-repository benchmark shows
correct incremental behavior but only a 1.9% latency advantage on a 50-file repository.

PR-C's current real-repository sample indexed 64 files into 423 nodes and 2,194 edges in
623.969 ms. A dependency-aware two-file incremental refresh took 282.761 ms. One hundred repeated
impact queries had p50 0.0649 ms; the separate lexical `rg` candidate baseline had p50 2.2538 ms.
These are latency measurements, not a claim that graph impact and lexical search have equal quality.

PR-E adds immutable runtime observations, revision-aware freshness, deterministic graph-based test
selection, evidence-based Test Obsolescence states, and bounded revision-aware context packages.
Exact-head evidence under `docs/evidence/pr-e/` records 100-item/2,131-token standard context versus
8-item/148-token weak context, two graph-linked test candidates without fallback, restart-persistent
real OpenCode tool evidence, and truthful `observed` status when stable host metadata lacks an exit
code. Live routing remains PR-G scope.

PR #10 merged as `fbdfcbd3864a3c46b76cc9ff10d77a57639258a6`. PR-F must preserve immutable
planned revisions and compare small `TargetSnapshot`, `ActualSnapshot`, and
`VerificationEvidence` projections without treating planned content as existing project facts.

The implemented PR-F slice now does so: immutable payloads are separate from lifecycle metadata,
planned and Actual namespaces are guarded, all eight task states and seven bounded decisions are
deterministic, stale/unavailable evidence cannot complete, and SQLite restart/workspace isolation
is covered. The standalone 200-element benchmark under `docs/evidence/pr-f/` measured evaluation
p50 0.2348 ms and restart 1.8938 ms. Exact-head local gates passed; publication remains.

PR #12 merged as `157fd19b56db6c61e61b5f02ab81e3bf985d79fd`. Live adapters and model-backed
Strategy remain PR-G scope and must extend the existing PR-A ModelRouter.

PR #14 merged as `3386cfa429caf5b476e8abc5d52d87a8ab99c719`. PR-G extends that router with deterministic adaptive signals, live OpenAI-compatible/OpenCode
adapters, complete-session model metrics, bounded reasoning/output controls, and fail-closed
provider errors. Strategy metrics are deterministic across all required axes; model synthesis only
proposes alternatives and explanation. The six-scenario evidence under `docs/evidence/pr-g/`
records local-low/local-medium/host comparisons. Host active scored 6/6 with zero tool calls in
14.509 seconds versus native 6/6 with 40 calls in 78.016 seconds. The configured frontier path was
unavailable with `APIError`; it is not counted as passed and remains a final release blocker.
Post-merge main passed all-fast (85 Python and 9 adapter tests) and both package builds.

The reproducible PR-D smoke measured alternating three-run startup medians of 1,046 ms native and
1,070 ms plugin-enabled (+24 ms), then observed tool and external edit refreshes at 151 ms, MCP
connection/reconnection, three durable revisions, and no off-mode revision change. The raw
comparison includes a 1,609 ms native outlier; this is functional smoke evidence, not a stable
distribution.

## Evidence policy

A work package is not complete merely because source files exist or mocked tests pass. Record exact local commands/results and distinguish:

- deterministic unit/component/integration evidence;
- real repository benchmark evidence;
- real OpenCode integration evidence;
- real LLM/model-routing evidence;
- unavailable checks.

Planning documents are design evidence only. They do not count as implementation, build, test, real-host, or real-model evidence.

Do not mark unavailable evidence as passed.
