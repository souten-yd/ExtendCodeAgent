# Known Issues

## B0b did not confirm a covered held-out PI causal effect

- The exact-main local-practical confirmation completed 57/57 cells with 48/48 forced-use compliance
  and no provider/runtime gap, but every intrinsic and covered capability comparison had zero PASS
  delta. Graph, Semantic, Twin and Test Selection are `NO_CONFIRMED_CAUSAL_EFFECT` on the sealed
  held-out tasks. This blocks a positive PI effectiveness claim; it is not hidden by the earlier
  screening signals.
- Blueprint, Impact, Strategy and Test Obsolescence are `NO_HELD_OUT_TASK_COVERAGE`, not no effect.
  Do not invent tasks, weaken oracles or permanently exclude them because of selection/coverage.
- Cross-boundary and requirement tasks failed in forced PI as well as controls. Failure attribution is
  16 `AGENT_REASONING_ERROR` and 20 `PROJECTION_SCHEMA_ERROR`, with no provider/process failure. The
  smallest projection/relation repair belongs to later existing stages; repeated cross-boundary
  failure satisfies X0 entry.
- Auto selection remains weak: precision 0.650794, recall 0.530952, under-selection 0.469048 and 22
  `EXPECTED_BUT_NOT_USED` states. C1/C3 must measure and address it independently of efficacy.
- Required-test-set precision/recall is 1.0 across 21 test-selection cells, but all off/ablation arms
  also pass. Do not claim an attributable Verification Intelligence effect from equal accuracy.
- Full prompt context reached 93,189 tokens; 64k/96k are not safe current defaults. Keep 262,144 until
  a bounded 128k-or-higher context Bridge proves oracle/truncation equivalence on broader tasks.

## B0a screening classifications are not promotion or general-model evidence

- B0a completed with six local-practical B0b candidates, two `no screened effect` capabilities and
  five `NOT_TESTED_NO_ACTIVE_USE` capabilities. The latter state is an auto/active selection
  observation, not zero effect or any other negative capability-efficacy evidence.
- The 95.7983% avoided-call ratio measures the adaptive evaluation scheduler, not production ECA call
  reduction. A causal-correction gate now holds the PI plan constant and measures auto selection
  separately before B0b.
- The 22 compatible reused results include five historical timeouts; this is retained outcome
  history, while the 30 newly executed cells had no timeout. B0b confirmation must use the unchanged
  held-out split and full repetitions before any promotion/demotion decision.
- All current claims remain bounded to `active-scoped(local-practical)`. B0a provides no evidence for
  frontier, host-default, local-low, or general-model effectiveness.

## First causal-correction attempt did not reach the model

- At exact main `692de70`, the 24 initial cells all exited in about 15 seconds with zero model tokens.
  A relative raw-root was passed into `git worktree add`; Git resolved the target under each task
  template, while OpenCode and the oracle used the repository-relative path. Every result is a
  pre-model runner failure and is excluded from causal/quality evidence.
- Keep the raw report as diagnostic history. After the absolute-root repair merges, create a new
  exact-head plan/output rather than resuming or rewriting the failed checkpoint.

## Expected disabled responses need treatment-aware classification

- The `79ffe3c` forced-off cell called the exact five-tool plan. `pi_status` succeeded and each
  disabled capability route returned `capability_unavailable`, as designed. The generic tool-error
  classifier labeled those expected treatment responses `PI_TOOL_API_GAP`, which would make every
  forced-off intrinsic comparison invalid.
- Preserve the eight completed model captures and stop the run. Accept only a capability-unavailable
  response expected by `forced_off` or the named `forced_ablation:X`; any other tool/input/route error
  remains fail-closed. Re-finalize compatible captures deterministically on the repaired runner, with
  source/current revision and original result hash provenance, rather than spending eight new calls.
- The first reclassification attempt correctly stopped on a trace-ID conflict because rerunning the
  deterministic oracle changed only timing. Keep the immutable source trace and do not append a
  second envelope for an already traced migrated cell; no new model call occurred in this attempt.
- `forced_ablation:graph` on `b947a24` exposed `%3A` workspace-root encoding and is diagnostic only,
  not capability evidence. Preserve its capture/checkpoint; after the path-safe workspace repair,
  compatibility migration must reject that noncompliant capture and execute a fresh isolated cell.
  **Closed for execution at `88d2e17`:** the path-safe rerun was `PASS / FORCED_USE_COMPLIANT`; the
  original diagnostic remains preserved and is not causal evidence.

## B0a corrective gaps carried into B0b

- Graph, Impact, Context, Runtime, Convergence and Traceability did not produce a corrected causal
  signal under their representative sealed tasks; Test Selection produced three ON/OFF PASS pairs.
  These are screening diagnostics, not demotions, and do not remove the six observational candidates.
- Research and Test Obsolescence lacked a suitable corrective task/oracle. They are
  `NO_TASK_COVERAGE`, not no effect. B0b must use only coverage already present in its sealed held-out
  contract and must not invent or weaken an oracle.
- Auto selection under-selected expected capabilities: mean recall 0.534821 and 20
  `EXPECTED_BUT_NOT_USED` states across eight measured tasks. C1/C3 retain this as a planner gap;
  forced efficacy evidence must not be reinterpreted as automatic-selection success.

## Shared GitHub Copilot monthly quota defers 17 historical Codex cells

- Exact-head activation proved this is the GitHub Copilot provider's shared monthly quota: both
  `github-copilot/claude-sonnet-5` and `github-copilot/gpt-5.3-codex` now return
  `You have exceeded your monthly quota`. Qwen still passes. Each affected Copilot route is paused
  independently as `QUOTA_EXHAUSTED`.
- Current valid target progress is 145/162: Qwen 54/54, Sonnet 54/54, Codex 37/54. Sixteen quota
  responses must be requeued and one interrupted Codex cell remains pending. They must not enter
  PASS/FAIL or latency aggregates.
- These cells no longer block local-only progression. Sonnet/Codex are
  `NOT_RUN_USER_POLICY / SHARED_QUOTA_EXHAUSTED`; no new call or availability probe is permitted while
  the exception is active. Previously completed Sonnet/Codex results remain immutable supplementary
  history and are not reclassified.

## Checkpoint migration is proof-gated, not direct resume

- The 229-cell `7e58751` report is immutable and cannot be passed directly to `--resume` on a newer
  runner. It is also no longer discarded wholesale merely because provider supervision changed.
- The sealed compatibility audit yielded 217 reuse candidates, four provider gaps and eight
  timeouts. The multi-provider Bridge Proof and migration have completed. Under the current
  three-route target, 100 cells are retained as migrated evidence and 45 were executed by the current
  runner; 17 Codex cells remain pending.
- Functional outcome and legacy latency are separate. Even a migrated functional result remains
  `LEGACY_RUNNER_LATENCY` until an explicit latency bridge permits aggregation.
- Historical Bridge evidence remains useful for provenance, but `host-default` and `local-low` are
  no longer B0a quality targets. Local-practical test-selection was replay-required; matched Qwen,
  Sonnet, and Codex classes supported the migrated checkpoint before the target-scope correction.

## B0a host-default provider rate limit and superseded checkpoint

- The `7e58751` baseline stopped at 229/306 after four host-default cells encountered an immediate
  provider rate limit. OpenCode stayed alive after exhausting retries, so the old runner recorded
  task `TIMEOUT` and projection attribution instead of provider unavailability.
- PR #66 at merged head `91b82e3` repairs the harness and has real-route fail-fast evidence, but it does not restore
  provider capacity. The affected checkpoint remains diagnostic and must not enter quality/latency
  aggregates or be resumed across the runner-head change.
- This host-default condition is historical and outside the current quality target. Its cells remain
  excluded; it is not a resume condition for the three-route baseline. Port 8090 and Ollama are
  unrelated and must not be changed for this historical gap.

## E3 evaluation limitations

- The ControlDeck-managed OpenCode selected for E3 is 1.18.16, while earlier npm-stable evidence used
  1.18.18. E4/B0 must report the executable and version actually used rather than treating these as
  interchangeable.
- No permitted non-Ollama weak-local endpoint is registered. `OpenCode + OMO + ECA @ local-low` is
  therefore UNAVAILABLE; model-free coexistence PASS is not model-task evidence.
- OMO 4.19.4 and ECA expose unique ECA `pi_*` names, but generic raw IDs such as `glob`, `grep`,
  `skill`, and `task` overlap. B2 must assess semantic dispatch/conflict behavior.
- OMO's installer wrote `~/.omo/omo.jsonc` despite an isolated XDG configuration. The newly created
  file was moved into the temporary evidence root and the previously absent directory was restored;
  future automation must not assume XDG isolation is complete.
- GitHub candidate popularity and activity observations drift. OpenCode, Hermes Agent, Atomic Agents,
  and Codex require a fresh immutable pin and clean dependency/test audit before any corpus promotion.
- A supplemental repository-wide Ruff scan reports one pre-existing E501 long line in
  `tools/local/benchmark_pr_b.py`. Normal all-fast/integration/build gates pass; E4 already owns
  retiring that per-PR benchmark into the unified runner.

## E4 evaluation limitations

- E4 route proof uses one repetition per representative cell. It proves wiring and objective scoring,
  not comparative quality; B0 owns minimum-repetition distributions and screening/confirmation.
- The sealed full schedule is 5,083 cells, of which 1,495 are visible local-low UNAVAILABLE cells.
  Running all cells without screening would violate the execution-capacity design.
- Integrated metric keys whose implementing verification stage does not yet exist are emitted as
  `NOT_TESTED`. They must not be numerically aggregated or interpreted as zero.
- Historical `benchmark_pr_b/c/h/i` and `pr_g_evaluate` remain executable only to reproduce their
  original evidence. They contain obsolete route assumptions and are not current entry points.

## PR-A environment

- The local machine has Python 3.12.3 but no Python 3.11 executable, so the declared 3.11 lower
  bound was checked through syntax/tool configuration rather than a second interpreter run.
- The `opencode` command is not installed locally. PR-A therefore makes no real OpenCode claim;
  real plugin/MCP evaluation remains a PR-D acceptance gate.
- PR-A has fake model evidence only. Live local/host/frontier routing remains a PR-G gate.
- `timeout_seconds` is validated configuration but the synchronous fake adapter does not simulate
  wall-clock timeout enforcement; live adapters must implement that contract in PR-G.

## PR-B measured limitation

- On the 50-source-file ExtendCodeAgent repository, file-level refresh took 182.145 ms versus
  185.638 ms cold build. The fact update is incremental, but workspace fingerprint scanning
  dominates. Before claiming scale benefit, benchmark a Git-status fast path and automatic
  full-rebuild selection for small repositories.
- Snapshot import validates integrity and restores current facts, but deliberately creates a new
  local revision instead of importing foreign revision identity. Cross-store lineage preservation
  remains future work.

## PR-C current limitations

- Dependency-aware semantic refresh repairs unchanged importers of a removed/renamed symbol, but it
  currently parses every Python AST to build the symbol index before emitting only affected facts.
  The 64-file sample improved from 623.969 ms cold to 282.761 ms incremental; larger-repository
  scaling and a persisted symbol index remain future measurements.
- Dynamic receiver calls are deliberately emitted as inferred `may_call` edges at confidence 0.35.
  This avoids false certainty but can produce name-collision false positives through alias bridging;
  the PR-C FP/FN report must quantify representative cases.

## PR-D current limitations

- Stable OpenCode 1.18.18 emits `.git/index.lock` watcher events while the Twin computes its Git
  fingerprint. Unfiltered handling caused a self-sustaining refresh loop. The plugin now discards
  `.git`, `.extendcodeagent`, dependency, cache, and build paths before enqueue; the final real-host
  smoke must retain explicit no-loop evidence.
- Stable OpenCode's native event stream did not expose ordinary tracked edits in the tested Linux
  environment. The adapter-only Chokidar fallback passed both OpenCode-tool and external-edit
  evidence, but future stable OpenCode releases should be retested so the extra watcher can be
  removed when the native contract is reliable.
- The three-run temporary-repository startup comparison had a +24 ms median delta and one 1,609 ms
  native outlier. It is not statistically conclusive; retain broader native/extension comparisons
  for final release validation.

## PR-E current limitations

- Stable OpenCode 1.18.18 does not route the model-free session-shell endpoint through
  `tool.execute.after`. Real runtime-hook evidence therefore requires an actual agent tool call.
- The real local Qwen agent `bash` hook omitted explicit exit metadata, so its successful command is
  truthfully stored as `observed`, not `passed`.
- The first real-repository test-selection sample found no graph-linked candidate for
  `reconcile_observations` and correctly selected full-suite fallback. A bounded diagnosis confirmed
  a Python `src.`/package re-export alias gap; the language-owned resolver now uses exact import
  evidence and a collision fixture. This repairs the measured sample without claiming general
  dynamic-import or alias completeness.
- OpenCode smoke processes share the host OpenCode database and must run serially; a concurrent
  evidence attempt produced `database is locked`. Serial model-free and model-backed reruns passed.

## PR-G current limitations

- The configured `llama/llama-3.3-70b-instruct` frontier path returned OpenCode `APIError` for all
  18 mode/scenario attempts. Provider failures now fail closed, but no real frontier quality result
  exists; the final release gate remains unmet until a usable frontier credential/path is available.
- Qwen3 0.6B varied across repeated six-case runs. Bounded Project Intelligence consistently beat
  off, but advisory versus active was not stable enough to justify an active default. The central
  default remains off and active must stay explicit until multi-repository distributions exist.
- OpenCode's host token report separates cache reads from new input. Evidence records both; adding
  them as if billed identically would be misleading. Host big-pickle was free in the measured setup
  (`cost: 0`) but that does not generalize to other providers.
- Stable session prompt does not expose a per-request output-token bound. The OpenAI-compatible path
  is bounded; the host path relies on focused prompts and a transport timeout. Final validation
  should reassess this against the then-current stable OpenCode API.

## PR-H measurement incident

- py-tree-sitter 0.26.0 segfaulted even after cross-file `Node` state was replaced with serializable
  descriptors; the same isolated ControlDeck TSX analysis passed repeatedly on 0.25.2. The analyzer
  pins 0.25.2, reuses one `Parser` per grammar, streams traversal, and retains only descriptors
  across files. This remains open until three repetitions of the real-repository cold/incremental
  path and full local gates pass; a recurrence requires replacing the Python binding path.

## PR-I current limitations

- PR-I defines and exercises provider-neutral Search/Fetch/Extract/Synthesis ports and exposes the
  shared bounded plan through MCP, but does not claim a new standalone web provider. OpenCode/web or
  MCP retrieval adapters supply those ports; live cross-provider research quality belongs in final
  Release Validation.
- External evidence is deliberately never promoted to verified project fact. A claim needing both
  external truth and implementation verification must carry separate external and current project
  evidence; this may leave more explicit coverage gaps but prevents false completion.

## E5 trace limitations

- The required local-low route is not registered under the permitted environment, so the all-arm
  E5 demonstration has 115 `UNAVAILABLE` outcomes. Its capability states are scheduled matrix values,
  not observed runtime values, and it provides no quality comparison.
- The real advisory trace observed capability state through `pi_status`, but its `pi_symbol` output
  exposed neither a selected evidence ID nor a Twin revision ID. Those trace fields correctly remain
  empty/null.
- E5 is a serial evaluation log without cross-process locking and is not durable cross-session
  Project Evidence Memory. The sealed runner is serial; broader durability/replay belongs to P0.

## B0a bootstrap performance observation

- Resolved for the two blocking repositories by `fcd61dff6c66324fed970ecfb1d9b19cae2aa8f7`:
  schema 5 adds the matching current-edge identity index. Three fresh runs put KasaneCore at a
  15,825ms median and PEDS at 6,368ms, both within budget. The original timeout evidence remains a
  valid observation of the pre-repair implementation.
- The first pinned KasaneCore initial Twin spent multiple minutes applying edges in
  `SqliteGraphStore._close_current`. The schema indexes current nodes by canonical reference but has
  no equivalent current-edge ID index, so the per-edge supersession update is a suspected scaling
  defect. This is observed diagnosis, not yet a confirmed repair; B0a records bounded timeout/build
  evidence and B1 owns a product fix if the completed gap report confirms it is blocking.
- Exact bounded measurement excluded KasaneCore and PEDS after 300 seconds. ControlDeck completed in
  204,116ms against a 20,000ms M budget; Vite completed in 184,488ms against a 180,000ms L budget;
  React Hook Form, Flask and HTTPX also missed their size budgets. Express and ExtendCodeAgent passed.
  Only one cold run per repository exists, so required three-run medians remain NOT TESTED.

## B0a PI activation and capability reachability

- The exact-head `0a1a9f4` activation run proved real PI tool execution on all four required model
  routes but failed the configuration-integrity gate: `blueprint`, `strategy` and `convergence`
  appeared off. This is a confirmed runner/adapter propagation defect, not model variance. The
  generated project config was scoped only to MCP while OpenCode used plugin tools, and MCP also
  forced advisory. Comprehensive evaluation and the pilot remain blocked until repair and rerun.
- PR #49 resolved that configuration defect, and activation passed at `ebe2a197`. The first pilot
  exposed a protocol-efficiency defect instead: arm-major ordering completed eight native cells
  before any active comparison, including one 256,319ms response. Those cells are not effect
  evidence. Pilot execution must be interleaved and pass its 9-cell initial tranche before spending
  the remaining confirmation cells.
- After PR #50, the first interleaved off cell selected a duplicate qualified MCP `pi_status` and hit
  an OpenCode tool-result shape error. Native and active completed; active PI observation passed.
  This is not an effect result. Causal cells must expose one plugin namespace/sidecar, while MCP is
  validated separately, before the 9-cell tranche is rerun from zero.
- PR #51 removed that duplicate causal route. At `6064e311`, the initial 9-cell tranche showed a
  real but narrow active gain (0/0/1 PASS); only test selection passed. Confirmation then hit a
  300,157ms active-symbol TIMEOUT at cell 12/27 and was stopped. This is a B1 repair condition, not
  evidence that Project Truth is ineffective.
- `pi_symbol`/`pi_references` and impact/path previously repeated snapshot scans/materialization or
  `GraphAnalysisService` adjacency construction. Segmented timing confirmed this boundary and the
  revision-scoped cache now removes repeated materialization/reindex in one sidecar. Large-repository
  cold materialization, fallback substring scans and cross-process cache behavior remain unmeasured;
  the earlier 300,157ms timeout still cannot be assigned to PI query work from one small-repo smoke.
- Exact-answer misses are not treated as one failure class. Required fact recall, schema validity
  and final exact pass distinguish retrieval gaps from task-schema projection and downstream agent
  reasoning. The exact oracle is not weakened.
- Compact projection fixes the symbol entity-context shape on the clean ECA task workspace. Python
  analyzer v2 also closes the two measured impact/test gaps: it distinguishes three callers from
  four call occurrences and links directly used Path/AST source scopes to architecture tests. The
  two pilot task projections now match their required fact sets. This does not prove generic
  TestIntent/coverage recall; broad or helper-mediated structural inspection, dynamic discovery and
  non-Python frameworks remain bounded uncertainty until held-out/full-suite calibration.

- The old 306-cell baseline began without an observed-PI activation precondition. It stopped at 137
  cells; pure `native` results measure OpenCode/model behavior, not PI effect, and will not be reused
  as corrected-protocol evidence.
- One old refactor cell ran an editable install and retargeted the shared runner `.venv` to its
  temporary workspace; the preserved 24-cell screening checkpoint reproduced that contamination.
  The root editable install was restored. Corrected runs remove the runner venv and `PYTHONPATH`
  from the agent shell environment, require an isolated virtualenv for pip, and now deny OpenCode
  `external_directory` access for every arm while the ECA sidecar keeps its explicit interpreter.
  Adaptive migration invalidates any old cell whose trace accessed the shared venv; it does not
  silently reuse that result.
- Core PI is known to be callable in earlier single-cell route proofs, but comprehensive readiness is
  blocked until the four-model exact-head activation gate and staged port-8090 effect pilot pass: a
  9-cell initial tranche first, then 27 total only after a positive initial signal.
- The pilot is intentionally small and cannot promote a capability. It only prevents spending the
  comprehensive schedules when active PI has no objective gain, was not actually used, or has
  abnormal latency; any such result requires repair and the same pilot again.
- The prior OpenCode route gap for `blueprint`, `convergence`, `traceability` and `strategy` is
  repaired with `pi_plan`/`pi_verify` plus covered screening tasks. This is deterministic route
  evidence only: real model use and effect remain NOT TESTED until the fresh activation and pilot.
- `pi_plan` currently generates two bounded graph-derived alternatives rather than using a model to
  invent arbitrary designs. `pi_verify` currently reports Twin materialization and gaps but accepts
  no external verification-evidence payload. Those boundaries are intentional for the screening
  route and must not be described as full planning or certificate support.
- The first post-route 9-cell pilot at `b67f951` had no functional gain because OpenCode still
  exposed `view=detail`, and Qwen explicitly chose it in symbol/impact. This bypassed compact facts
  and produced a truncated impact payload. The repair removes that public choice while preserving
  direct application detail compatibility; effect remains NOT TESTED until the same pilot is rerun.
- Objective-aware test projection is deterministic token/obligation ranking, not calibrated generic
  TestIntent. It is exact on the sealed ECA pilot workspace but held-out precision/recall remains
  unmeasured. Any missing obligation continues to require native fallback.
- The first `b128ade` activation attempt stopped after one cell because evaluation evidence parsing
  did not recognize canonical URIs in compact `symbols`/`*_refs` arrays. PR #60 repaired the
  collector and the fresh `130f0a2` four-model activation passed.
- At `130f0a2`, active compact PI supplied every required fact for all three pilot tasks and test
  selection passed, but Qwen still deleted one symbol path and enriched the impact schema. Exact
  answer/field-preservation instructions are pending merge and real controlled rerun; 1/3 active-only
  is not evidence of advantage over native/off.
- The first controlled post-projection pilot at `1706490` showed functional advantage (0/0/2 exact
  PASS) but fail-closed attribution rejected the passing tests cell because repository-relative
  `selected_tests` were not recognized as selected evidence. The collector repair is tested but must
  merge and the same 9 cells must rerun before the initial gate can pass.
- At `d36d910`, the repaired initial 9-cell gate passed, but confirmation was stopped at 14/27 after
  an off-control Qwen first response generated 27,998 tokens and hit its 420-second timeout. This is
  not PI latency. The new 8,192-token arm-neutral output bound changes the matrix/plan seals, so all
  prior pilot cells are diagnostic and cannot be resumed into the repaired protocol.
- PR #63's output-only model limit passed debug rendering but failed real OpenCode runtime validation
  because `limit.context` was absent. The final pair is context 262,144/output 8,192. A fresh real
  activation remains required; the 488ms configuration failure observed no model or PI activity.
- The final 27-cell pilot confirms aggregate PI effect, but symbol is only 1/3 exact PASS despite PI
  fact recall 1.0 in all repetitions, showing remaining scalar/list projection variance. Tests are
  2/3; one repetition's PI fact recall fell to 0.333 because objective projection selected only one
  required class. These are measured residual gaps, not blockers to comprehensive measurement.
