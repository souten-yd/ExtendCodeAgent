# Current Handoff

Updated: 2026-08-17 (Asia/Tokyo)

Canonical branch: `agent/b2-omo-coexistence`; synchronized merged base is
`58b17970266ebccb1a0cc9c2a0169bfab523ba84` (PR #91)
Milestone: A-I implementation and Phase 0 evaluation enablement complete
Current task: merge the B2 runner, then execute its exact-main model-free preflight and five-stack
local-practical bridge

## Current authoritative checkpoint (2026-08-17)

- B0a progression now uses only ControlDeck-managed port-8090 Qwen. The exact-head baseline contract
  is 54 cells; the following screen retains 714 local-practical cells as its hard maximum.
- Sonnet/Codex are `NOT_RUN_USER_POLICY / SHARED_QUOTA_EXHAUSTED`, host-default is
  `NOT_RUN_USER_POLICY`, and local-low is `UNAVAILABLE / NOT_CONFIGURED`. No new call/probe or
  cross-tier claim is permitted while the local-only exception is active.
- The confirmed 27-cell Qwen pilot remains `PROCEED_TO_COMPREHENSIVE`: native/off/active PASS is
  0/0/6, every required PI observation is present and active median wall ratio is 0.658.
- The exact-head, trace-complete 54/54 local baseline is sealed. The preserved old screening
  checkpoint remains immutable at 24/714; adaptive migration reuses only compatible cells and does
  not delete or rewrite the old checkpoint/raw evidence.
- The existing Qwen 54/54 was promoted through compatibility audit, Bridge Proof and checkpoint
  migration. The exact-head model-free plan recorded active-use relevance, D0-D4 output equivalence,
  expected/max calls, empirical limits, workspace strategy and skip reasons before new inference.
  No other model was probed or substituted.
- Development-tree preflight reduced the 714 hard maximum to 102 adaptive candidates, with 534
  `NOT_TESTED_NO_ACTIVE_USE` and 78 depth-equivalent skips. One of 24 old results accessed the shared
  runner `.venv` and is invalid under the corrected isolation contract. Clean commit `6cbacaf`
  reproduced 23 reusable cells, 27 expected new calls before the first decision and 79 maximum new
  calls. The one-call persistent OpenCode Bridge was oracle-inconsistent and 23.7% slower, so retain
  per-cell `opencode run`. Evidence: `docs/evidence/final/b0a-adaptive-screening-execution-v1.json`.
  The exact-main model-free plan and adaptive frontier then completed as recorded below.
- Exact-main adaptive screening is complete. The 714-cell contract is fully accounted for by 30 new
  calls, 22 compatible reused results and 684 machine-classified avoided calls. There were no
  provider gaps, new timeouts or step-limit terminations. The observed call-avoidance ratio is
  95.7983%; the oracle and effect threshold were unchanged. This is observational / agent-selection-
  weighted scheduler evidence, not product-runtime call reduction or causal evidence for every
  capability.
- `graph`, `twin`, `semantic`, `impact`, `test_selection`, and `test_obsolescence` proceed as B0b
  candidates only. `blueprint` and `strategy` recorded no screened effect. `context`, `runtime`,
  `convergence`, `research`, and `traceability` remain `NOT_TESTED_NO_ACTIVE_USE`; they are not
  classified as no effect. No B0a result promotes or demotes a capability.
- Before B0b, merge a causal-correction gate. The sealed EvaluationPIPlan covers all 13 tasks and was
  constructed without observed Qwen selection. It separates `auto_pi` selection evidence from
  forced ON/OFF/ablation efficacy and requires exact trace request equality.
- The corrective plan uses six representative tasks for eleven covered capabilities, preserves the
  six existing candidates, and records Research/Test Obsolescence as `NO_TASK_COVERAGE`. Five auto
  task traces are reusable only as selection evidence; `cd-requirement-001` needs one new auto call.
  The initial plan is 24 calls and the hard maximum 58. The old 27-cell forced pilot remains
  replay-required because it lacks exact request-input provenance.
- The active-trace-dependent 108-cell B0b runner was never executed and is retired. A corrected B0b
  plan is generated only after corrective evidence merges. No corrective or B0b model call has run
  on the implementation branch.
- The first exact-main corrective attempt at `692de70` did not reach Qwen: all 24 initial processes
  exited before provider/model work because a relative raw-root made `git worktree add` create cell
  workspaces under each template while OpenCode looked under the repository root. The diagnostic
  report has zero tokens and is not causal/quality evidence. Preserve it; resolve workspace roots to
  absolute paths, merge the repair, regenerate an exact-head plan, and retry from a fresh output.
- The repaired `79ffe3c` run completed one auto and six forced-ON calls plus the first forced-off call.
  All six ON traces were compliant; forced ON PASSed requirement/refactor/symbol/tests and FAILed
  cross-boundary/impact. Auto requirement FAIL versus forced PASS establishes a selection-gap sample.
  Stop before further calls: off correctly attempted the identical PI plan, but expected
  `capability_unavailable` responses were generically classified as `PI_TOOL_API_GAP`. Preserve and
  compatibility-reclassify these eight captures after the classifier repair; do not rerun them.
- The first reclassification on `65dad4d` made no model call and stopped on immutable trace conflict:
  regenerated oracle timing differed for an existing trace ID. Preserve the source hash-chain and
  append only previously untraced new cells after the trace-reuse repair merges.
- Exact-main execution reached 8 compatible reused plus 6 new cells before the first graph ablation
  exposed `%3A` workspace-root encoding. The diagnostic cell is `PI_TOOL_API_GAP`, not efficacy
  evidence; resume only after the path-safe workspace and noncompliant-capture rejection repair.
- The repaired exact-main run completed at `88d2e17`: 58/58 accounted, 22 new calls, 13 compatible
  reused results, 23 adaptive skips, and 34/34 forced cells exact-trace compliant. The candidate union
  is `blueprint, graph, impact, semantic, strategy, test_obsolescence, test_selection, twin`.
  PR #89 merged `docs/evidence/final/b0a-causal-correction-result-v1.json` and the canonical status
  updates at `eab71fb`; B0b entry is satisfied.
- The B0b runner implementation fixes a 57-cell local-only schedule over the three candidate-covered
  held-out KasaneCore tasks and three required repetitions: 9 auto, 9 forced PI, 9 forced off and 30
  forced ablations. Graph/Twin/Semantic receive nine pairs each and Test Selection three. Blueprint,
  Impact, Strategy and Test Obsolescence are explicitly `NO_HELD_OUT_TASK_COVERAGE`; the unsafe task
  has no candidate coverage. The existing absolute two-PASS threshold remains unchanged, forced use
  is trace-verified fail-closed, auto selection is separate, and no promotion is emitted before the
  Layer C budget gate. PR #90 merged the runner at `f15064c` before the plan or first B0b call.
- B0b then completed 57/57 cells at exact source revision `f15064c`: 21 PASS, 36 FAIL, 48/48 forced
  cells compliant, with no timeout/unavailable/provider/process result. Raw report SHA256 is
  `edc821d2218281808257127a1a83c2347d70b51ae1aaaabdb800cb242d66cbc5`; trace SHA256 is
  `665cf672e3a4ddbf38429271f6869827a65a8cf79b961a67ccacb813f0077c63`.
- Intrinsic PI PASS delta was zero on all three tasks. Graph, Semantic, Twin and Test Selection had
  equal ON/ablation outcomes and no confirmed held-out causal effect. Blueprint, Impact, Strategy and
  Test Obsolescence remain `NO_HELD_OUT_TASK_COVERAGE`. No promotion/demotion was made.
- Auto selection precision was 0.650794 and recall 0.530952, with 22 expected-but-unused states.
  Test-selection required-set precision/recall was 1.0 across all 21 relevant cells, but every off/
  ablation control also passed, so the result is not attributable to PI.
- Full request prompt context (`input + cache-read + cache-write`) across 538 steps was p95 68,512,
  p99 86,351 and maximum 93,189. A 128k setting is a bounded candidate for this workload; retain the
  configured 262,144 until a context-equivalence Bridge. The raw report's per-cell context and PI-wall
  aggregates are preserved but superseded by corrected sealed-log derivations in the compact evidence.
- The run temporarily exhausted disk because completed evaluation worktrees were retained. Only
  recreatable generated worktrees were removed; captures, fragments, checkpoint and trace were
  retained. Resume reused all completed cells without another model call. The closeout runner now
  discards each exact generated workspace only after durable capture/finalization, including pending
  prepared cells after a provider gap.
- B0 gap decisions: B1 is `SKIP_NO_ENTRY_CONDITION`; B2 is `KEEP_NEXT`; C1/C3 and X0 retain measured
  selection/projection gaps; four no-coverage candidates are not converted to negative evidence.
- PR #91 merged the B0b closeout at exact main `58b1797`; exact-main all-fast (208 Python plus 9
  adapter), integration (79 Python plus 9 adapter) and build gates passed after merge. B2 is active.
- The B2 runner fixes five isolated stacks (`native`, `eca`, `omo`, `omo_eca`, `eca_omo`), Team Mode
  off, OpenCode 1.18.18, exact OMO 4.19.4 and port-8090 Qwen. It seals the tuple before execution,
  performs model-free namespace/lifecycle/session/restart/runtime-observation and degraded-sidecar
  checks first, and permits at most one serial coding/verification agent run per stack only after the
  preflight passes. No profile, workspace or session is shared.

The chronology below is retained as history. Its four-model/306-cell and three-model/162-cell
statements describe superseded protocols and are not current execution instructions.

## B0a contract checkpoint (2026-08-16)

- PR #48 merged the activation/effect guard as exact main head
  `0a1a9f4e4b289fdef7c8a4ac225000b537e4a37b`.
- The first four-model activation run at that head observed `pi_status`, `pi_symbol`, ready Twin,
  revision, canonical evidence and positive PI time on every route, with no provider error. It
  correctly stopped before the pilot because all routes reported `blueprint`, `strategy` and
  `convergence` off despite the sealed active configuration.
- PR #49 repaired that root cause and merged as
  `ebe2a197fddf019bd2e40bbd372349a5f835d482`. Its fresh activation run passed all four routes. The
  first pilot attempt was stopped after eight arm-major native cells, including one 256,319ms cell,
  before it had measured `off` or `active`; staged interleaving is the current bounded repair.

- Stopped the pre-activation baseline after 137/306 atomically checkpointed cells at exact old head
  `86e8061`. No runner/OpenCode process remains. These cells are diagnostic OpenCode model-variance
  history and will not be mixed with corrected-protocol results.
- Added sealed `docs/evaluation/b0a-activation-plan-v1.json`. Its four one-cell routes are port-8090
  Qwen, host-default, GitHub Copilot Sonnet and GitHub Copilot Codex, all in active mode through the
  ControlDeck-managed OpenCode executable.
- A passing route must observe `pi_status`, `pi_symbol`, all configurable modes/depths, ready Twin,
  Twin revision, canonical evidence and positive PI time. Task-oracle quality remains a separate
  field.
- The pilot now starts with one interleaved port-8090 Qwen repetition: `native/off/active` over
  symbol/impact/test-selection (9 cells). Only a passing signal continues to three repetitions/27
  total; it proceeds only on an objective active PASS gain, complete active/off observations, no
  provider/timeout failure and active median wall ratio at most 2x.
- PR #50 merged staged interleaving as `6ab0850a513b0ee22ea82c1599e151bdc572fcc8`; activation passed
  4/4 at that head. The first symbol triplet stopped the tranche because off selected a duplicate MCP
  tool and failed to observe disabled state, while active PI observation passed. Current repair keeps
  one plugin namespace/sidecar in evaluation and retains MCP as a separate lifecycle gate.
- PR #51 merged that single-route repair as `6064e311c3f98fe37ab87c6c1e71603ef08db7b2`.
  Same-head activation passed 4/4. The sealed initial 9 cells produced PASS 0/0/1 for
  native/off/active, with active median 124,194ms versus 118,153ms for the slower control (1.051x).
  Only active test selection passed; symbol and impact still failed exact output requirements.
- Confirmation was stopped after 12/27 checkpointed cells because repetition-2 active symbol timed
  out at 300,157ms. The report records one PASS, ten FAIL and one TIMEOUT. Do not resume it as final
  evidence: implement B1 effect/timing repairs and rerun the same sealed 9-cell tranche from zero.
- Current bounded slice adds exact-oracle-preserving `required_fact_recall`, `schema_valid`,
  `final_exact_pass` and retrieval/projection/reasoning attribution. It also splits PI time into cold
  Twin build, snapshot load, adjacency/index construction, query execution, JSON serialization and
  post-PI agent/model residual from the first PI result after subtracting later tool execution.
  PRs #52 and #53 published this slice independently before PI projection semantics change.
- Exact merged-head instrumentation smoke at `1116d6be7f5e29b7bcea6b5c1610785bcc061afd`
  recorded wall 57,990ms, PI tool 161ms, cold Twin 474.730ms, snapshot load 149.969ms, query
  6.191ms, serialization 0.043ms and post-PI residual 23,066ms. Symbol does not build adjacency, so
  that segment was 0ms. This proves the trace path only; it is one FAIL classified
  `RETRIEVAL_MISSING`, not effect/performance acceptance evidence.
- B1 compact views are added to the existing symbol/impact/tests routes; OpenCode plugin and MCP
  default them to `compact`, while `view=detail` preserves prior graph-rich responses. On the clean
  ECA task workspace, symbol compact returns the exact `select_tests` definition, export, production
  source caller and two test paths. Impact compact returns the exact three production methods and
  narrows focused tests to `tests/unit/test_graph_analysis.py`, while retaining all candidates and
  `coverage_complete=false`. Structural obligation coverage and source use counts were the next
  measured repair and are closed below.
- Python analyzer `v2` now preserves call occurrence multiplicity and emits `structurally_covers`
  only when a test directly uses a resolved module-level `Path` scope. Compact projection combines
  that relation with deterministic test-intent tokens; broad structural scans are retained as
  candidates but not called focused without intent overlap.
- Clean ECA task-workspace proof now matches both remaining pilot schemas: impact returns the exact
  three methods, direct-use count 4, and capability-depth plus unit graph tests; test selection
  returns exactly architecture projection, Twin integration and unit verification, with
  `architecture_boundary`, `integration_boundary`, and `unit_behavior` covered and no fallback.
  This bounded evidence does not claim a complete generic TestIntent/Coverage Graph.
- Revision-scoped sidecar caching now reuses one immutable snapshot, exact symbol-name index and
  `GraphAnalysisService` forward/reverse adjacency map. Every request checks current revision;
  Twin open/refresh and revision mismatch invalidate all query caches. Existing fallback substring
  symbol behavior remains when there is no exact indexed match.
- Clean ECA task-workspace measurement after one cold symbol query: cached snapshot load
  impact/tests/symbol = 0.045/0.018/0.016ms, adjacency rebuild = 0ms, query execution =
  1.697/0.739/0.244ms. Cold Twin was 506.273ms and is reported cumulatively, not rerun per query.
- Comprehensive B0a execution requires same-exact-head activation and pilot reports. The prior
  deterministic reachability gap is repaired with `pi_plan` for Blueprint/Strategy and `pi_verify`
  for Traceability/Convergence. Both routes are proven through MCP against the real sidecar;
  persistence is opt-in and materialized facts are not mislabeled verified. The runner records
  composite `capabilities_used`, fixes one covered task per route, and refuses a no-effect decision
  if required route observations are absent. PR #58 merged this as `b67f951`; same-head activation
  passed all four routes, but the fresh 9-cell pilot produced 0/0/0 PASS and stopped correctly.
- Raw traces show Qwen explicitly selected detailed symbol/impact views, bypassing compact output;
  the impact payload was truncated. It also passed directories to detailed test selection and hit
  full-suite fallback. PRs #59/#60 now make OpenCode compact-only, project tests from an objective,
  and collect compact canonical evidence; fresh four-model activation passes. PR #61 then clarified
  exact answer projection. Its controlled 9-cell rerun produced native/off/active 0/0/2 PASS and PI
  fact recall 1.0 on every active task. The gate stopped because repository-relative
  `selected_tests` were not classified as selected evidence. Next: merge that bounded attribution
  repair and rerun activation plus the same 9 cells before any 27/306/714 continuation.
  PR #62's repaired 9-cell gate passed 0/0/2, but confirmation stopped at 14/27 when off impact
  generated 27,998 tokens before its first response and timed out at 420 seconds. The matrix now
  applies an 8,192-token local-practical limit to every arm and is resealed. Merge it, then restart
  activation and pilot on fresh paths; never resume the superseded-seal report.
  PR #63's first activation exposed an OpenCode runtime-schema requirement: output limit alone is
  invalid without context. The final provider config seals context 262,144 and output 8,192, matching
  the ControlDeck server. Merge and prove this pair with a fresh real activation.
  PR #64 merged the completed pair. Fresh activation passed, and the 27-cell pilot completed
  `PROCEED_TO_COMPREHENSIVE` with native/off/active 0/0/6, no observation failures or timeouts, and
  active median 72,100ms. Next: merge confirmed evidence, then run fresh 306 baseline followed by
  714 screening; do not conceal symbol 1/3 or tests 2/3 task-level variance.

- Conditional B1 repair exact head `fcd61dff6c66324fed970ecfb1d9b19cae2aa8f7` adds the missing
  current-edge identity index. Three cold exact-pin runs changed KasaneCore/PEDS from >300-second
  timeout to medians of 15,825ms/6,368ms; both are now bootstrap-eligible and within budget.
- The historical native/off baseline at merged schedule head `86e8061` is stopped at 137 cells and
  is not resumable into corrected evidence. It remains only as diagnostic model-variance history.
- Evidence: `docs/evidence/final/b1-edge-index-repair.json`. No PI effect claim follows from this
  performance repair.

- Runner enforcement is now implemented at exact head
  `9bfc934fc46d5db9ffcb43e48a695e8e470c1f29`: the baseline is 306 cells and the screen is
  714 cells. Both consume the sealed plan and bootstrap eligibility rather than relying on operator
  convention.
- The screen contains 294 active/ablation comparison cells. Its remaining 420 cells are targeted
  D0-D4 arms for the four capabilities with depth-dependent claims; only one capability depth moves
  in each arm.
- A machine screening table enforces the two-PASS threshold and preserves incomplete/provider-gap
  states. Its synthetic test is not outcome evidence. Baseline, screening and PI effect remain
  NOT TESTED pending the post-merge real runs.
- Schedule proof: `docs/evidence/final/b0a-schedule-proof.json`.

- Added a separately sealed B0a plan without changing the E4 matrix seal. It fixes the seven-task
  tuning subset, paired active/ablation comparison, screening-only effect threshold, four
  depth-claim capabilities and one explicit model-tier assignment for each of 13 ablations.
- The wide screen assigns every capability to the permitted port-8090 local-practical route. Full
  `native`/`off` baselines retain every tier, including GitHub Copilot Sonnet and Codex; local-low
  absence remains visible as UNAVAILABLE.
- Added a local bootstrap harness that unions the task and quality manifests (nine repositories),
  acquires exact detached pins, creates an initial Twin, discovers test runners/inventory and records
  observed/inferred/unknown classifications plus unsupported capabilities.
- Exact-pin or Twin failure yields `EXCLUDED_BOOTSTRAP_GAP`; absent test runner/inventory is recorded
  `unavailable` rather than silently skipped. Imported code correctness always starts `unknown`.
- No B0a evaluation result cell has run. Merge the enforced schedules before beginning the long,
  resumable baseline and screening executions.
- The first merged-head bootstrap attempt exposed two real gaps before any arm ran: the harness did
  not checkpoint until all repositories finished, and KasaneCore's initial Twin spent minutes in
  SQLite edge supersession. The harness now checkpoints atomically per repository, resumes, and
  classifies a bounded Twin timeout; the store performance defect remains a B0 gap, not a silent fix.
- Exact harness head `575be408dc05d7263cb16b3912f783d060539385` then attempted all nine pins.
  Seven Twins completed; KasaneCore and PEDS timed out at 300 seconds and are excluded bootstrap gaps.
  Express and ExtendCodeAgent met cold-index budgets. ControlDeck (204,116ms), Flask (5,903ms), HTTPX
  (8,100ms), React Hook Form (28,723ms) and Vite (184,488ms) completed but missed their size budgets.
- PI-disabled one-cell route checks found port-8090 Qwen, host-default, Copilot Sonnet and Copilot
  Codex callable without provider errors. Codex failed the task oracle, which is retained as a task
  failure rather than route unavailability. Local-low remains UNAVAILABLE.
- OMO 4.19.4 plus ECA model-free recheck retained 37 tool IDs, all nine unique `pi_*` tools, 16 agents
  and connected ECA MCP. This is the B0a smoke only; it is not the two-order B2 compatibility result.
- Evidence: `docs/evidence/final/b0a-bootstrap-environment-v1.json`. Screening remains NOT TESTED;
  included tuning repositories may proceed, while held-out confirmation remains blocked by KasaneCore.

## E5 closeout (2026-08-16)

- Added a compact typed evaluation trace covering plan/cell/task/oracle identity, sealed inputs,
  capability modes/depths, reserved verification features, evidence/revision IDs, model route,
  outcome/fallback and timings without storing prompts, transcripts or secrets.
- Added a hash-chained JSONL log with idempotent append, full replay validation, conflict rejection,
  tamper detection and fsync before returning.
- Capability state now records `planned_matrix` or `observed_pi_status`; unavailable scheduled cells
  cannot be misrepresented as runtime observations.
- Exact implementation head `9c29aa32eb57c61a394a989b1319423bb4092359` emitted 115 unique
  traces over all 23 arms. The local-low route remained correctly UNAVAILABLE in all 115 cells.
- Active versus semantic-ablation traces retained identical task/oracle/input/repository identity and
  differed only in semantic mode. This proves attribution shape, not quality benefit.
- A real ControlDeck-managed OpenCode advisory cell used `pi_status` and `pi_symbol`, recorded
  observed capability state and 8,332 ms PI analysis time, and correctly failed the task oracle.
- Versioned evidence: `docs/evidence/final/e5-trace-proof.json`. Raw JSONL/runtime logs remain ignored.
- Next: B0a Existing Project Bootstrap conformance, environment/integration freeze and screening.

## E4 closeout (2026-08-16)

- Promoted 12 already-reviewed PR-C/PR-H cases into sealed Layer A labels at
  `70710dfe82680afd8ab0c2ad3a735b7f82648c65554dbf93d878e0550a986427`.
- Sealed the unified matrix at
  `13d3e854234efbc302ff7d6c0ab5f4f2dfd3eea9cc11d98c2760e03ca4b6f16e`: 5,083 full cells,
  including 1,495 visible local-low UNAVAILABLE cells rather than silently dropping them.
- Added one ControlDeck-OpenCode runner for plan/run/filter/checkpoint/resume. Every output binds the
  Layer A/Layer B seals, quality corpus and integrated metric contract; unmeasured metrics remain
  `NOT_TESTED`.
- Exact implementation head `7ec5f42756bdd3035ec821fafa7256efebdb8152` ran native and advisory
  host checks, port-8090 Qwen3.6 27B, Copilot Sonnet and Copilot Codex. All routes were callable; task
  PASS/FAIL is retained as objective outcome, not a route verdict.
- A symbol task exercised `pi_context`, `pi_status`, `pi_symbol` and `pi_tests`. Raw logs and cloned
  workspaces remain ignored. The route proof is not a B0 quality or promotion result.
- Historical per-PR benchmark scripts remain solely for reproducing their original evidence and are
  retired as current entry points. New evaluation work uses `tools/local/evaluation-runner`.
- Next: E5 compact append-only PI trace and one attributable ablation demonstration.

## E3 closeout (2026-08-16)

- Sealed `docs/evaluation/task-suite-v1.json` with 13 tasks, nine required task classes, immutable
  tuning/held-out repository roles, exact ControlDeck OpenCode/model routes, and objective oracles.
- Exact manifest seal: `23bf76039ea1e95a29c31c09823f2501bd3658dea305a4e38868eb9e1e6f6632`.
- Native pure OpenCode proof: 4 PASS / 9 FAIL / 0 TIMEOUT / 0 UNAVAILABLE, success rate 30.77%; all
  13 task oracles executed at the exact seal.
- Selected PEDS `c607943367da648f1598f957ece314b29d2fc683` as the slow suite after clean `uv sync
  --frozen` and `npm ci`: normal gate 435 seconds plus Playwright 321 seconds, total 756 seconds.
- Loaded OMO 4.19.4 and ECA together in an ephemeral profile on ControlDeck-managed OpenCode 1.18.16;
  ECA connected and all nine `pi_*` tools remained visible. The local-low task arm is UNAVAILABLE
  because no permitted non-Ollama weak-local endpoint exists.
- Registered OpenCode, Hermes Agent and Atomic Agents as next-corpus candidates; Codex remains a
  reference-only candidate until the analyzer supports and measures Rust. This registry does not
  modify the sealed E3 v1 split.
- Next: E4 unified runner and versioned Layer A labels. Mandatory frontier routes remain GitHub
  Copilot Sonnet and Codex; local-practical remains the existing port-8090 Qwen3.6 27B service.

## Plan review pass (2026-08-16)

A full read-through corrected three residual inconsistencies (Evidence Memory at both P0 and P1;
`D0` meaning both a depth level and a Phase 5 stage, now `X0`/`X1`; B0's ablation sweep saying 14
instead of 13) and closed four scope gaps: a new stage **E3** defines the Layer B task suite before
the runner exists, §7.2 gains numeric Layer C budgets, invariant **8** treats repository content as
untrusted input, and §10.2 adds program-level stop and pivot criteria. The moat is restated as
Verification Intelligence with Project Truth as substrate, scored against a new code-intelligence
column in the competitive analysis. Full rationale in `DECISIONS.md`.

Phase 0 is now E0–E5; the former E3/E4 became E4/E5.

## External review follow-ups (2026-08-16)

An external review confirmed the plan direction and raised six points. Its top finding — E1 and the
corrections not being on `main` — was correct and is resolved: the stacked PRs #34/#35 had merged into
their intermediate bases rather than `main` (GitHub retargets a stacked PR only when its base branch is
deleted), and PR #36 merged the full content forward. The other five are applied:

- **Existing Project Bootstrap** is now a B0 entry condition, per evaluation repository.
- **E3 must include a cross-boundary GUI/runtime causal task**, framed as a measurement of how far
  current PI follows the chain. `ui_graph` stays `not_implemented`.
- **V0 defines `VerificationFeature`** so the V-series is ablatable from the inside, without adding
  `CapabilityName` members. E5's trace shape widened to accept `used_features`.
- **OMO coexistence smoke** becomes blocking gate 17 at B0/R0; the full benchmark stays P4.
- **"moat" downgraded to "primary differentiation hypothesis"**, resolving a contradiction with §5.

Invariant 8 was also clarified so it does not read as forbidding explanations.

## Current source of truth

`docs/PI_MASTER_EXECUTION_PLAN.md` is the single canonical execution plan. It owns product scope, the
capability inventory, the evaluation framework, the stage backlog and the release gates.

1. `docs/PI_MASTER_EXECUTION_PLAN.md`
2. `docs/handoff/NEXT_TASK.md`
3. `docs/CURRENT_STATUS.md`

All other planning documents remain valid as design detail and are registered in section 2 of the
master plan with an explicit disposition. Legacy stage identifiers are mapped in section 9 and must not
be used to schedule work.

## Corrected runtime decision

- Architecture remains host-neutral.
- **OpenCode is the only current production-target runtime.**
- Current ControlDeck usage is treated as **ordinary OpenCode usage** for ExtendCodeAgent purposes.
- ControlDeck is not a separate harness, adapter target, runtime contract, or mandatory evaluation
  dimension today.
- ExtendCodeAgent integrates only with OpenCode through its normal adapter/plugin/MCP boundary.
- Do not add ControlDeck-specific APIs, adapters, lifecycle management, install/discovery protocols,
  configuration formats, UI contracts, or special PI behavior.
- ControlDeck may remain a convenient place to run OpenCode, and its repository is a useful real-world
  benchmark candidate, but neither is privileged in product acceptance.
- Other harnesses remain research/reference sources and future portability targets, not current
  production dependencies.
- OMO may be used for targeted OpenCode orchestration comparisons but is not a release dependency.

The key rule is:

> Evaluate OpenCode + ExtendCodeAgent. Do not invent a separate ControlDeck runtime condition until a
> future deep ControlDeck integration is measured to change relevant OpenCode semantics.

## Mandatory adoption evidence

A feature is not adopted because it is implemented or unit-tested. It must be exercised with the
OpenCode/agent/LLM combinations necessary to prove the claimed effect.

Primary mode comparison:

```text
OpenCode native
OpenCode + ExtendCodeAgent off
OpenCode + ExtendCodeAgent shadow
OpenCode + ExtendCodeAgent advisory
OpenCode + ExtendCodeAgent active (where permitted)
```

ControlDeck-launched and terminal-launched OpenCode count as the same condition unless a measured
semantic discrepancy is found.

Use local-low, local-practical, host/default and functioning frontier tiers as relevant. The current
environment fixes local-practical to the existing port-8090 Llama/Qwen3.6 27B service and frontier to
Sonnet plus Codex through GitHub Copilot in OpenCode. Wait for the 8090 model to wake; never start
Ollama or a substitute server. Repeat stochastic runs and record exact OpenCode/ExtendCodeAgent/model/
provider/repository/workspace identities plus relevant hardware/runtime details.

## Anti-overfit and attribution

- use multiple real repositories rather than treating ControlDeck as the sole acceptance project;
- ControlDeck can remain one mixed Python/JS/TS real-world corpus;
- reserve held-out tasks/prompts and at least one held-out repository outside tuning;
- before generic `active-default`, confirm accepted behavior on held-out repository work;
- do not credit OpenCode/model/provider improvements as PI gains;
- classify failures as OpenCode runtime, model/provider, PI adapter, PI core, task selection,
  verification or performance.

Different repositories, worktrees and copied workspaces remain distinct Twin/workspace identities
unless explicitly related.

## Competitive decisions

Adopt into PI only when measured useful:

- stable-prefix-aware / bounded structured evidence for weak local models;
- deterministic candidate reduction and decision envelopes;
- Project Evidence Memory with provenance/revision/invalidation;
- compact append-only PI trace/replay;
- stronger Verification Intelligence and evidence-backed completion;
- runtime-observed worktree/subagent/task identity sufficient for future PI-aware parallel work.

Explicitly do not duplicate runtime-owned team orchestration, scheduler/background manager, browser,
shell/edit engine, sandbox/permissions, provider/model management, generic session recovery,
worktree/checkpoint engine, generic conversational memory or host UI.

## Execution sequence

Owned by master plan section 8. Summary:

```text
Phase 0  E0 consolidation -> E1 gating conformance -> E2 depth contract
         -> V0a verification contract slice (shadow)
         -> E3 Layer B task suite -> E4 evaluation runner + labels -> E5 minimal PI trace
Phase 1  B0a screening -> B0b confirmation and gap report -> B1 blocking repair (conditional)
         -> B2 OMO coexistence baseline (conditional)
Phase 2  C0 runtime contract -> C1 shadow planner -> C2 weak-local (conditional)
         -> C3 advisory selection + adaptive depth
Phase 3  V0 verification contracts -> V1 calibration -> V2 required verification set
         -> V3 evidence reuse -> V4 failure-driven re-evaluation -> V5 observability (conditional)
Phase 4  A0 bounded active -> A1 progressive expansion
Phase 5  X0 runtime bridge (conditional) -> X1 bounded deep analysis (conditional)
Phase 6  R0 production-capable baseline
Phase 7  P0 evidence memory -> P1 conformance -> P2 second harness -> P3 parallel intelligence
         -> P4 comparative benchmark
```

B0a does not start before E1-E5 and V0a are complete.

## Future ControlDeck deep integration

The user expects ControlDeck may integrate OpenCode more deeply later. That future possibility does
not change today's ExtendCodeAgent plan.

Only introduce a distinct `ControlDeck + OpenCode` evaluation condition after an implemented
ControlDeck change is shown to alter relevant session/tool/context/model/workspace/verification or
multi-agent semantics. Until then, treat it as OpenCode.

## Stage E1 — done on this branch

Delivered:

- `strategy` gated at `build_strategy`, `test_obsolescence` gated at `evaluate_test_health`, both
  through the shared `CapabilityPolicy.require_explicit_use` in `core/policy.py`. No new gate
  mechanism; `service/application.py` now delegates `_require_explicit` to the same helper.
- `test_obsolescence` is independent of `test_selection`: with it off, `pi_tests` still selects tests
  and returns `health: []`.
- `call_graph` folded into `semantic` (`CAPABILITY_FOLDED_INTO`). The rejected independent-gate option
  and its reasons are in `DECISIONS.md`.
- The seven unimplemented capabilities declared in `NOT_IMPLEMENTED_CAPABILITIES`, forced to `off`,
  and rejected with `ConfigError` if configured to a non-`off` mode.
- `tests/architecture/test_capability_gating.py`: AST scan asserting every `CapabilityName` is gated,
  folded into a gated capability, or declared unimplemented; inventory counts pinned at 21/7/1/13 so a
  new capability cannot be added silently.
- `pi_status` reports `implementation`, `mode` and `governed_by` for all 21 capabilities;
  `PiStatus`/`CapabilityStatus`/`RolloutMode` typed in `adapters/opencode/src/client.ts`.
- Per-capability `off` inertness parametrized over all 13 configurable capabilities, in addition to
  the existing global-`off` test.

Evidence: `tools/local/all-fast`, `tools/local/test-integration`, `tools/local/build` all exit 0.
Defaults unchanged — every capability still ships `off`.

## Immediate next work

```bash
cd /home/souten/ExtendCodeAgent
git switch main
git pull --ff-only origin main
git status --short
tools/local/all-fast
tools/local/test-integration
tools/local/build
git switch -c agent/b2-omo-coexistence
```

After this closeout PR merges, start B2 from synchronized main. Read only
`docs/OMO_COEXISTENCE_AND_COMPATIBILITY_PLAN.md` §9 as the active design detail. Record the exact
OpenCode/OMO/ECA tuple, Team Mode off, both meaningful plugin load orders, startup/tool/session/basic
coding/verification behavior, clean shutdown and C0-C6 classifications. Use port-8090 Qwen only for
model-bearing checks. This is compatibility evidence; do not pull P4 comparative scoring forward.

Rollback path: switch to synchronized `main`. B0b closeout changes evaluation cleanup/metrics and
evidence only; it does not change capability defaults, task/oracle truth, thresholds or product
rollout authority.

## Stage V0a — complete on this branch

Delivered:

- Added immutable `SemanticChangeSet`, `SemanticEntityChange` and `SemanticRelationChange`
  projections over actual base/candidate Twin snapshots, with deterministic IDs and provenance.
- Added explicit `VerificationObligation` and `RequiredVerificationSet` projections. Test providers
  cover only graph-supported local/consumer obligations; runtime/uncertainty gaps remain explicit.
- Added a precision/recall projection against an executed expected-provider set for E3/E4/B0 use.
- When a file body changes but analyzer symbol shells do not, affected symbols become low-confidence
  inferred semantic changes; unknown is not treated as unchanged.
- Architecture evidence proves the slice has no storage, SQLite, OpenCode or filesystem dependency;
  no evidence reuse, failure taxonomy, oracle assessment or certificate was pulled forward.
- Exit gates PASS: `tools/local/all-fast` (178 Python, 9 adapter),
  `tools/local/test-integration` (17 Python, 9 adapter), and `tools/local/build` (Python sdist/wheel
  plus TypeScript build).

## Stage E2 — complete on this branch

Delivered:

- Added centralized `D0..D4` depth profiles and per-capability min/max/preferred/auto bounds,
  independent of `RolloutMode`; `auto` resolves deterministically to balanced until C3.
- Added resolved depth and inferred-relation confidence floors to `CapabilityPolicy`; folded
  `call_graph` inherits `semantic`'s depth.
- Recorded depth in public PI responses and every `pi_status` capability entry. Status itself uses
  `depth: null` because no single capability owns the inventory response.
- Applied the depth floor only to inferred relations at use time. D1 excludes confidence-0.35
  `may_call`; D3 admits it; caller-provided confidence can narrow results but cannot bypass the depth
  floor. Stored Twin revisions remain configuration-independent.
- Preserved default behavior: balanced resolves to D2 and its 0.3 inferred floor admits every
  currently emitted analyzer confidence (minimum 0.35).
- Exit gates PASS: `tools/local/all-fast` (171 Python, 9 adapter),
  `tools/local/test-integration` (16 Python, 9 adapter), and `tools/local/build` (Python sdist/wheel
  plus TypeScript build).

## Feasibility and OMO pass (2026-08-16)

A review against the stated product intent (OpenCode + KasaneCore-derived PI + OMO together) produced
seven changes, all documentation:

1. **`OMO-C0` restored as stage B2.** E0 had recorded the OMO plan as "P4 only" and thereby dropped a
   gate its own §9 requires before any recommended-stack claim.
2. **B0 split into B0a screening and B0b confirmation**, with a new §7.5 sampling design. The full
   matrix is 322 runs per task — roughly 320 hours at 20 tasks — and had no termination rule.
3. **`V0a` pulled into Phase 0.** The differentiation hypothesis was scheduled four phases after
   everything it differentiates from, leaving §10.2's verification-only pivot with no target.
4. **E3 gains an `OMO + ECA @ local-low` arm** — the intended production configuration and the worst
   case for context budget. `pr-g` already shows an overhead ratio near 2.6 against a 0.5 budget.
5. **E2 binds inferred-relation confidence to depth**, completing the E1 `call_graph` folding decision.
6. **Slow-suite repository pinned and target project profile stated.** The existing corpus is
   fast-testing, i.e. the condition where selective verification correctly loses.
7. **Four risk rows added**: execution capacity, unbudgeted human review, unbuilt differentiator, and
   KasaneCore reuse being conceptual rather than code.

Rationale for each is in `DECISIONS.md`.
