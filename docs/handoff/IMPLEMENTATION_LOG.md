# Implementation Log

## 2026-08-17 — Local-only execution policy v2

- Preserved sealed `b0a-quality-target-v1.json`, the evaluation matrix, task suite, oracles,
  thresholds, corpus and prior Copilot evidence unchanged. Added minimal
  `b0a-quality-target-v2.json` selecting only port-8090 `local-practical` Qwen.
- The v2 denominator is 54 `native/off` cells. The existing 714-cell screen, ablations, D0-D4 arms,
  tasks and threshold remain unchanged. Existing Qwen 54/54 must be promoted through compatibility
  audit, Bridge Proof and checkpoint migration; only proven residual cells rerun.
- Sonnet/Codex and host-default are blocked by user policy at the runner boundary. No automatic
  provider probe is permitted. Every new evaluation report records the local-only model, endpoint,
  context and output limit.
- Local gates PASS: `tools/local/all-fast` (191 Python + 9 adapter),
  `tools/local/test-integration` (55 Python + 9 adapter), and `tools/local/build` (Python sdist/wheel
  plus TypeScript build).
- The migration CLI now rebinds compatible migrated results to the active v2 54-cell schedule,
  rejects any out-of-target result, recomputes pending/complete counts, preserves migration
  provenance, and seals the local-only execution metadata. Focused runner/compatibility tests pass
  33/33; `tools/local/all-fast` passes 191 Python + 9 adapter,
  `tools/local/test-integration` passes 56 Python + 9 adapter, and `tools/local/build` passes the
  Python sdist/wheel plus TypeScript build.
- Added and sealed `b0a-checkpoint-compatibility-v2.json` against source `c0d13d7` and target
  `8f12078`. Core, OpenCode adapter, task/oracle and immutable evaluation-contract fingerprints are
  identical; the Bridge requirement is exactly three `local-practical` task classes. The active
  runner compatibility binding now selects v2 while preserving v1 as historical evidence.
- The first completed local-only checkpoint exposed a completion-gate provenance defect: planned
  cells retained the matrix-local model name `llama` while runtime results correctly recorded the
  resolved route `eca-local-practical/llama`. Planning now records the resolved route. Migration
  also excludes historical non-target provider queues/attempts from the active local-only report
  while preserving them unchanged in the immutable source checkpoint and recording exclusion counts.
- Sealed `b0a-checkpoint-compatibility-v3.json` from completed-baseline head `650b293` to the
  runner-only repair `1057169`; diagnostic audit reports trace integrity PASS and 54/54 `REUSABLE`.

## 2026-08-17 — Canonical three-route contract reconciliation

- Registered the sealed B0a quality target in the canonical master plan and replaced the active
  four-route/full-tier language with Qwen plus Copilot Sonnet/Codex and a 162-cell baseline.
- Refreshed the current handoff to 145/162, 100 migrated plus 45 current-runner cells, the shared
  Copilot quota gap and the PR #76 baseline-completion gate. Historical 306-cell chronology remains
  explicitly labeled superseded rather than being rewritten as current evidence.
- Corrected stale checkpoint/Bridge/migration and host-default resume instructions in the rolling
  handoff and known-issues documents.

## 2026-08-17 — Baseline-completion gate and mixed-provenance repair

- Added a fail-closed `--baseline-report` gate for B0a screening. The report must be sealed, produced
  at the current exact head, contain exactly all 162 scheduled cells, contain no provider-gap quality
  result, and have one valid append-only trace per result before any screening workspace is created.
- Baseline checkpoints are now sealed even without migrated cells, and resume verifies any available
  checkpoint seal. Screening reports retain the exact baseline evidence binding across resume.
- Requeue now recomputes retained migrated/current-runner counts and reports mixed provenance
  explicitly. Legacy-runner timing is excluded from current timing aggregates unless a separate
  latency bridge permits merging.

## 2026-08-17 — Three-route B0a target and Copilot quota requeue

- Corrected the B0a quality scope to the user-mandated routes only: ControlDeck-managed Qwen,
  GitHub Copilot Sonnet, and GitHub Copilot Codex. The baseline is 162 cells, not the historical
  306-cell all-tier schedule; `host-default` and `local-low` are excluded from target progress.
- The resumed run produced 54/54 valid Qwen cells, 54/54 valid Sonnet cells, and 37/54 valid Codex
  cells. Codex then returned `You have exceeded your monthly quota` through the GitHub Copilot
  provider. Sixteen such results are requeued as `QUOTA_EXHAUSTED`; the interrupted seventeenth
  cell remains pending. Valid progress is 145/162.
- Added a sealed copy/requeue command so provider-gap attempts leave the quality result set without
  modifying the source checkpoint. Resume keeps only the affected Copilot Codex queue paused and
  retains complete provenance and a rebuilt trace chain.
- At merged head `8c06a0a`, fresh activation passed Qwen with ready Twin, `pi_status`, `pi_symbol`,
  revision and evidence. Both Copilot Sonnet and Codex returned the same monthly-quota error, proving
  the exhausted capacity is shared at provider/account level rather than specific to Codex. The
  145-cell checkpoint resumed without executing or misclassifying any paused-provider cell.

## 2026-08-17 — Partial activation and compatible pilot promotion

- Latest activation at `c95bdfb` passed PI route activation for local-practical, Copilot Sonnet and
  Copilot Codex with ready Twin/revision/evidence observations. host-default alone remained
  `RATE_LIMIT`; its single trigger attempt paused that queue.
- Added fail-closed `PARTIAL_PROVIDER_GAP`: missing activation models must exactly equal paused
  provider queues and every observed route must pass with no capability gap. This allows unaffected
  baseline queues to proceed but does not claim full activation/baseline completion.
- Audited the immutable 27-cell pilot: all 27 are `REUSABLE`, trace integrity is PASS and the original
  active/control gain remains 6. Added sealed `promote-pilot`; any invalid pilot cell rejects reuse,
  and its latency remains legacy/separate.

## 2026-08-17 — Class-scoped checkpoint migration

- Added `migrate-checkpoint`, which requires sealed audit and Bridge proof, verifies source report and
  trace hashes, creates a new selected trace chain and copies rather than edits source results.
- Bridge-mismatched classes and provider-unavailable model tiers are excluded. Sealed unavailable
  model cells can migrate as `NOT_APPLICABLE` latency because they contain no provider execution.
- Each copied cell records original/validating runner revisions, source result hash, compatibility
  manifest/proof and legacy latency status. The report preserves these fields across resume and
  rejects resume if its migration seal is invalid.
- The current partial proof permits an expected 190 candidates: 90 sealed local-low cells, 47
  local-practical cells excluding test-selection, and 53 Copilot Sonnet/Codex cells. All 21
  host-default candidates and six local-practical test-selection candidates remain pending/replay.

## 2026-08-17 — Provider queue pause and Bridge three-way classification

- The first merged-head Bridge run matched 8/12 cells. Local-practical symbol/impact and every
  Copilot Sonnet/Codex sample matched the legacy semantics. Local-practical test-selection changed
  from FAIL to PASS and therefore makes that class replay-required.
- host-default remained rate-limited for all three attempted cells. These are now represented as
  bridge-unavailable rather than semantic mismatches or PI failures.
- Added queue-local pause: one provider gap records a non-quality attempt, keeps that cell pending,
  pauses only that model-tier queue and continues other queues. A separate sealed availability probe
  is required to reopen the queue on resume.

## 2026-08-17 — Sealed Bridge Sample runner

- Added deterministic Bridge planning over the formally audited reuse candidates: one source cell
  for each required local-practical, host-default, Copilot Sonnet and Copilot Codex by symbol,
  impact and test-selection task, for 12 cells total.
- Added exact-head Bridge execution with model-tier sharding/resume and sealed semantic comparison.
  Outcome, oracle/process result, answer-schema validity, model route and PI/tool state must match;
  mismatches expand replay to the related model/task class. Wall time is explicitly excluded.
- The prior official audit was generated at merged runner `c8a295f` and confirmed 217 reusable
  candidates, four provider gaps, eight timeouts and a valid trace chain. Because this PR extends the
  sealed Bridge policy, the audit must be regenerated once more at this PR's clean merge head before
  executing the Bridge.

## 2026-08-17 — Checkpoint compatibility audit foundation

- Added sealed `b0a-checkpoint-compatibility-v1.json` for `7e58751` to current-main comparison.
  Git tree fingerprints prove ECA core, OpenCode adapter, task/oracle and evaluation/model contracts
  are unchanged; only runner provider supervision/tests and documentation/evidence differ.
- Added `audit-checkpoint` with source/report/trace/result hashes, full trace-chain verification,
  task/model/repository provenance, explicit invalid classes and legacy-latency separation.
- A development-tree diagnostic audit of the immutable 229-cell checkpoint classified 217
  `REUSABLE`, four `INVALID_PROVIDER_GAP` and eight `INVALID_TIMEOUT`. This is not migration proof
  until regenerated by the clean merged runner and followed by the required Bridge Sample.
- Added integration coverage for successful reuse candidates, provider gaps, timeouts, task seal,
  repository provenance/pins, model/core semantic changes and runner-only compatibility.

## 2026-08-17 — B0a provider-gap fail-fast repair

- Stopped the corrected-head baseline at 229/306 after OpenCode logs proved host-default was returning
  `Rate limit exceeded` immediately while the runner misreported the cells as task timeouts.
- Added `--print-logs --log-level ERROR`, final-retry detection, bounded process-group cleanup and
  stable provider categories. Provider gaps now emit `UNAVAILABLE` with `PROVIDER_GAP` attribution.
- A real ControlDeck-installed `opencode/big-pickle` cell returned `RATE_LIMIT` in 9,103ms instead of
  waiting for the 300,000ms task timeout. Runner integration passed 20 tests; lint and typecheck pass.
- The old 229-cell checkpoint is diagnostic only. Exact-head activation/pilot and the 306-cell
  baseline restart after this repair merges and the provider route recovers.

## 2026-08-16 — B1 current-edge index repair

- Confirmed the B0a bootstrap diagnosis: `_close_current` updates current edges by
  `(scope, edge_id, valid_to)` while SQLite had no matching index, causing repeated scans during
  large initial Twins.
- Added `edges_current_id`, bumped the store schema to 5 and proved an existing schema-4 catalog is
  migrated and the exact UPDATE uses the new index. No graph or revision semantics changed.
- Exact implementation head `fcd61dff6c66324fed970ecfb1d9b19cae2aa8f7` rebuilt both previously
  excluded exact pins three times from fresh databases. KasaneCore measured 15,825 / 14,924 /
  17,258ms (median 15,825ms, L budget 180,000ms); PEDS measured 6,368 / 6,393 / 6,364ms
  (median 6,368ms, M budget 20,000ms). Both are now bootstrap-eligible.
- Final gates pass with the repair source selected: `all-fast` (183 Python, 9 adapter), integration
  (31 Python, 9 adapter), and Python/TypeScript build.
- Evidence: `docs/evidence/final/b1-edge-index-repair.json`. This removes a bootstrap blocker; it is
  not PI quality or model-effect evidence.

## 2026-08-16 — B0a enforced baseline and screening schedules

- Bound B0a runner scopes to the sealed screening plan and exact bootstrap eligibility evidence.
  KasaneCore and PEDS cannot silently enter an arm after their initial-Twin timeout.
- Fixed the baseline at 306 cells over `native`/`off`, three repetitions and all five tiers. The 90
  local-low cells remain scheduled as UNAVAILABLE; Sonnet and Codex retain their GitHub Copilot IDs.
- Fixed the local-practical screen at 714 cells: active, 13 independently paired ablations, and 20
  targeted depth arms covering only semantic, impact, test selection and context.
- Added a machine screening table with a 294-cell paired comparison, exact two-PASS threshold,
  critical-failure override, incomplete/provider-gap classifications and no adoption decision.
- Exact implementation head `9bfc934fc46d5db9ffcb43e48a695e8e470c1f29`; the synthetic analyzer fixture is test evidence only.
  Baseline outcomes, screening outcomes and PI effect remain NOT TESTED.
- Schedule evidence: `docs/evidence/final/b0a-schedule-proof.json`.

## 2026-08-16 — B0a bootstrap and screening contract

- Added sealed `b0a-screening-plan-v1.json` referencing the unchanged E3/E4 seals and fixing the
  subset, paired effect threshold, per-capability tier assignment, depth claims and forbidden
  adoption decisions before any screen runs.
- Added `tools/local/b0a-bootstrap`, which unions nine repositories from both canonical manifests,
  acquires exact detached pins and emits initial Twin/test baseline records with explicit evidence
  classifications and bootstrap eligibility.
- Added an isolated exact-pin fixture proving acquisition, Twin creation, test discovery, inventory
  and unknown correctness. Focused Ruff, mypy and two integration tests pass.
- Final gates pass: `all-fast` (182 Python, 9 adapter), integration (29 Python, 9 adapter), and
  Python/TypeScript build.
- No repository bootstrap evidence or agent screening result is claimed in this contract checkpoint.
- The first post-merge nine-repository run was interrupted after KasaneCore spent several minutes in
  `SqliteGraphStore._close_current` and earlier completed repository results remained only in memory.
  Added per-repository child isolation, timeout classification, atomic checkpoint/report writes and
  resume. Dirty or wrong-origin corpus clones are archived rather than force-reset.
- Exact-head bootstrap attempted nine pins: seven included, KasaneCore/PEDS excluded on 300-second
  Twin timeout. Only Express and ExtendCodeAgent met cold-index budgets; five other completed Twins
  exceeded budget. Worktree fingerprints, test inventories and unsupported analysis remain explicit.
- PI-disabled route checks reached Qwen on port 8090, host-default, Copilot Sonnet and Copilot Codex;
  local-low remained UNAVAILABLE. The Codex cell completed the route but failed its task oracle.
- Reused the isolated exact-version OMO profile to recheck OpenCode 1.18.16 + OMO 4.19.4 + current
  ECA: health, 37 tools, nine `pi_*` IDs, 16 agents and ECA MCP connection passed model-free.
- Added compact evidence at `docs/evidence/final/b0a-bootstrap-environment-v1.json`; raw clones,
  SQLite state, traces and model logs remain ignored.

## 2026-08-16 — E5 minimal attributable PI trace

- Added immutable `EvaluationTrace` records and an append-only hash-chained JSONL log with
  idempotent append, replay verification, conflict rejection, tamper detection and fsync.
- Integrated one trace per unified-runner result, including sealed inputs, capability/depth state,
  reserved `used_features`, selected evidence/source/Twin IDs, exact model route, outcome/fallback
  and timings. Prompts, transcripts and secret-shaped fields are rejected.
- Corrected the first implementation so selected PI evidence/Twin IDs and `pi_status` modes/depths
  come from actual tool output where present. Added explicit `capability_state_source` to distinguish
  that observation from a scheduled matrix state when a provider is unavailable.
- Exact-head `9c29aa32eb57c61a394a989b1319423bb4092359` emitted 115 unique traces across
  all 23 arms for one task. Every local-low cell was correctly `UNAVAILABLE`; the active/semantic
  ablation pair differed only in semantic mode with identical sealed task/oracle identity.
- A real ControlDeck-managed OpenCode advisory run called `pi_status` and `pi_symbol`, recorded
  observed capability state, and returned objective `FAIL` because it selected one of two required
  tests. This is truthful trace/runtime evidence, not B0 quality evidence.
- Focused E5 tests (10), scoped Ruff and scoped mypy passed. Final gates passed: `all-fast` (182
  Python, 9 adapter), integration (27 Python, 9 adapter), and Python/TypeScript build.
- Versioned proof: `docs/evidence/final/e5-trace-proof.json`; raw workspaces and JSONL logs remain
  ignored.

## 2026-08-16 — E4 unified evaluation runner and Layer A labels

- Promoted 12 PR-C/PR-H reviewed cases into a machine-readable sealed Layer A label set; no new human
  review volume was introduced.
- Added and sealed the full 5,083-cell matrix across five base arms, 13 capability ablations, five
  depth arms, 13 E3 tasks, model-tier repetition minimums and explicit local-low unavailability.
- Added a single ControlDeck-managed OpenCode runner with sealed-input validation, plan/filter/run,
  objective E3 oracle scoring, all versioned metric keys, atomic checkpoints, resume and recoverable
  incomplete-workspace archival.
- Exact implementation head `7ec5f42` route proof passed at the runner level for native, advisory,
  port-8090 Qwen3.6 27B, GitHub Copilot Sonnet and GitHub Copilot Codex. Objective task results were
  3 PASS / 3 FAIL across six representative cells; no provider was unavailable.
- Confirmed a host advisory symbol task called `pi_context`, `pi_status`, `pi_symbol` and `pi_tests`.
  The one-run route proof is explicitly not a B0 comparison or promotion result.
- Focused runner tests cover seals, the exact full schedule count, frontier IDs, visible unavailable
  cells, bounded filters, every integrated metric key, atomic checkpointing and resume deduplication.

## 2026-08-16 — E3 Layer B task suite and outcome ground truth

- Added the sealed 13-task Layer B suite, validation/preparation/oracle harness, serial native proof
  runner, and focused integration tests.
- Fixed an ambiguity found by the first preliminary native run by requiring the exact answer status;
  archived those three pre-seal logs under ignored local evidence and reran every task after the
  final seal.
- Final seal `23bf76039ea1e95a29c31c09823f2501bd3658dea305a4e38868eb9e1e6f6632` validated; native
  ControlDeck-managed OpenCode proof passed its non-triviality gate at 4/13 task successes with no
  timeout or unavailability.
- Rejected KasaneCore as the slow suite because its pinned tests require untracked/generated assets.
  Rejected current PEDS origin/main because its remote pin was not green. A clean older remote-
  reachable PEDS pin passed 1600 Python tests plus 82 Playwright tests in 756 seconds total.
- OMO 4.19.4 plus ECA loaded model-free with nine ECA tools and connected MCP; local-low remains
  UNAVAILABLE. Restored the installer-created home configuration path after capturing the isolation
  limitation.
- Added a versioned GitHub candidate registry for OpenCode, Hermes Agent, Atomic Agents and Codex,
  keeping it explicitly outside the sealed E3 v1 split.
- Focused E3 tests, scoped Ruff, strict mypy and diff checks passed. Full gates passed: all-fast 178
  Python plus 9 adapter tests; integration 21 Python plus 9 adapter tests; Python and TypeScript
  builds. An extra repository-wide Ruff scan found one pre-existing long line in the E4-retirement
  target `tools/local/benchmark_pr_b.py`; E3 did not absorb that unrelated cleanup.

## 2026-08-16 — Stage V0a completed locally

- Added immutable, deterministic semantic-change and verification-obligation projections over the
  existing Twin/Graph/Impact model without a second truth store.
- Added required-provider selection that keeps unsupported runtime/uncertainty obligations uncovered
  and a TP/FP/FN precision/recall evaluation projection.
- Added unit, architecture and real-Twin integration evidence; a file-body change projects affected
  symbol uncertainty rather than treating an unchanged symbol shell as unchanged behavior.
- Final local gates: all-fast PASS (178 Python, 9 adapter); integration PASS (17 Python, 9 adapter);
  build PASS (Python sdist/wheel and TypeScript).

## 2026-08-16 — Stage E2 completed locally

- Added the centralized D0–D4 capability depth contract, deterministic profiles and per-capability
  min/max/preferred/auto bounds without coupling depth to rollout authority.
- Added depth to PI responses and `pi_status`, propagated `semantic` depth to folded `call_graph`, and
  bound inferred-relation consumption to a depth-specific confidence floor.
- Corrected the reviewed implementation so the depth floor applies only to inferred facts rather
  than all facts, and strengthened tests to prove D1 excludes confidence-0.35 `may_call` while D3
  admits it.
- Final local gates: all-fast PASS (171 Python, 9 adapter); integration PASS (16 Python, 9 adapter);
  build PASS (Python sdist/wheel and TypeScript).

## 2026-08-13 — PR-A started

- Synced `main` with `origin/main`; no update was required.
- Reviewed planning documents, KasaneCore shared contracts and rollout behavior, and current official OpenCode plugin/MCP documentation.
- Created `agent/pr-a-foundation` from `9623282d00ef98490d5c36ea16256f6fcde260af`.
- Created the required handoff framework before production implementation.

## 2026-08-13 — PR-A implementation and local gates

- Added a Python 3.11+ package with no runtime dependencies.
- Added host-neutral project/revision/provenance/confidence/evidence/diagnostic contracts.
- Added strict layered JSON/JSONC configuration resolution and immutable runtime config.
- Added independent feature rollout policy for all planned major capabilities.
- Added logical model roles, endpoint profiles, privacy/routing policies, fake adapters, bounded
  retries/fallback, and explainable decisions.
- Added architecture tests blocking OpenCode/Atlas/Nexus/provider imports in core.
- Added reproducible local bootstrap/lint/typecheck/unit/build scripts.
- Local evidence: Ruff passed; strict mypy passed; `25 passed in 0.04s`; sdist/wheel build and
  wheel-archive smoke passed.
- Published draft PR [#2](https://github.com/souten-yd/ExtendCodeAgent/pull/2); initial remote head
  `43ada0d4dd5ddf4d11a9100a17143b957ee2a0c8` was mergeable with no GitHub Actions checks configured.
- Verified final PR head `ce251a5c0273e4bbb5fcd126d0bbffd10defed64`, marked it ready, and
  squash-merged as `49db5bac7084fc3df444dc8b3c5f18cc7f79a0f8`.
- Fast local gates on merged `main`: Ruff and strict mypy passed; `25 passed in 0.04s`.

## 2026-08-13 — PR-B started

- Synced `main` at `40602d3ad8f147c9166e32919f7005da1c11279e`; local fast gates and package build passed.
- Created `agent/pr-b-graph-twin-store`.
- Inspected the four required KasaneCore sources and their store/source/refresh/durability tests.
- Kept PR-B scope explicitly limited to Graph/Twin persistence, source snapshot, and file-level refresh.
- Added immutable Graph contracts and bounded Git/non-Git source snapshots; focused tests passed.
- Added atomic SQLite revision persistence with workspace scope, idempotency, expected-head conflict,
  historical snapshots, reverse-edge index, retention hook and snapshot export foundation.
- Post-store local gate: Ruff and strict mypy passed; `36 passed in 0.09s`.
- Added full/reopen/incremental/deletion/conflict/restart/workspace Twin lifecycle integration;
  `5 passed in 0.21s`.
- Added integrity-checked snapshot export/import and bounded retention tests.
- Real repository benchmark recorded under `docs/evidence/pr-b/`; incremental fact behavior passed,
  while small-repo latency remained near full-build latency and is documented as a limitation.
- Published draft PR [#4](https://github.com/souten-yd/ExtendCodeAgent/pull/4); initial published head
  `ad2175bf5b2f893c025fc4f48db846f9516a238f` was mergeable with no GitHub Actions checks.
- Verified final PR head `33889aa89b9d0b4ba97032be581390b97cce3adf`, marked it ready,
  and squash-merged as `0618cd29da2e695f7babaccd931727e214f96217`.
- Post-merge main: Ruff and strict mypy passed; unit/architecture `38 passed in 0.17s`;
  integration `5 passed in 0.21s`.

## 2026-08-13 — PR-C started

- Created `agent/pr-c-semantic-impact` from exact `origin/main` at `faf307d`.
- Reviewed only the PR-C planning/migration slices and the directly relevant KasaneCore analyzers,
  analysis service, and behavioral tests.
- Kept OpenCode/MCP, runtime/context/test obsolescence, live models, and deep graphs out of scope.
- Chose behavior-first curated tests before adding production analysis code.
- Added deterministic structural/Python AST nodes and edges with explicit low-confidence `may_call`.
- Added analyzer-owned Python alias resolution plus generic bounded path/reverse-impact traversal.
- Added weakest-link confidence, direct/transitive classification, requirements, side effects,
  recommended tests, historical risk, uncertainty, and explanation paths.
- Integrated the analyzer as an optional Twin lifecycle dependency; file-only PR-B behavior remains
  available when no analyzer is supplied.
- Substantive commit `40587d7`; focused tests `13 passed`, all-fast `45 passed in 0.18s`.
- Added dependency-aware importer refresh and verified a removed target downgrades the unchanged
  caller from resolved `calls` to inferred `may_call` instead of retaining a stale edge.
- Added persisted end-to-end leaf/caller/test and ambiguous-call impact evidence.
- Final pre-publication gates: all-fast `45 passed in 0.14s`; integration `8 passed in 0.35s`;
  sdist/wheel build succeeded.
- Real-repository benchmark: 64 files, 423 nodes, 2,194 edges; cold 637.215 ms; dependency-aware
  incremental 280.653 ms; impact p50 0.0652 ms; lexical `rg` p50 2.2526 ms.
- Substantive commit `e3a65b7`; exact substantive-head gates: all-fast `45 passed in 0.18s`,
  integration `8 passed in 3.30s`, sdist/wheel build success. Repeated benchmark: cold 623.969 ms,
  incremental 282.761 ms, impact p50 0.0649 ms, lexical `rg` p50 2.2538 ms.
- Final evidence commit `699d0d3`; exact-head all-fast `45 passed in 0.17s`, integration
  `8 passed in 0.36s`, and sdist/wheel build succeeded.
- Published draft PR [#6](https://github.com/souten-yd/ExtendCodeAgent/pull/6); initial remote head
  `699d0d39c42763ad28ab8c0fe1aaa49d4aff941d` matched the locally verified head.
- Final remote head `d078b3c413cbdbbcd9d9a9ef78c00122eb5b3864` was MERGEABLE/CLEAN with no
  GitHub Actions checks. PR #6 was marked ready and squash-merged as `ef6db532`.
- Post-merge `main`: all-fast `45 passed in 0.16s`; integration `8 passed in 0.37s`.

## 2026-08-13 — PR-D started

- Merged PR-C docs closeout #7 as `4a73c6f1`, synced main, and created
  `agent/pr-d-opencode-mcp`.
- Base all-fast passed with `45 passed in 0.21s`; sdist/wheel build succeeded.
- Confirmed OpenCode was not installed, then checked current official stable plugin/MCP/config/CLI
  docs and V2 beta docs before choosing an adapter target.
- Current npm versions: OpenCode/plugin 1.18.18 and MCP SDK 1.30.0.
- Added the host-neutral application service plus authenticated local v1 sidecar, with off/shadow/
  advisory behavior tests and persisted restart behavior.
- Added the stable TypeScript OpenCode plugin, coalescing background event queue, six tools, and MCP
  stdio server sharing the same sidecar/service.
- Adapter typecheck passed; four adapter tests passed, including real MCP protocol call and sidecar
  stop/reconnect.
- Real OpenCode 1.18.18 loaded the plugin, exposed all six tools through its server, and reported the
  configured MCP connected.
- Real watcher testing exposed a `.git/index.lock`/Git-fingerprint feedback loop. Added adapter-side
  filtering matching source snapshot exclusions before events enter the queue.
- Real plugin loading also showed that helper functions must not be exported from the entry module;
  moved path normalization to a dedicated module and reverified loader success.
- Because stable native watcher events still omitted ordinary source changes, added a Chokidar
  fallback solely in the adapter and documented the measured design change.
- Reproducible real OpenCode smoke passed without a model: alternating three-run startup medians
  were 1,046 ms native and 1,070 ms plugin-enabled (+24 ms; raw native samples include a 1,609 ms
  outlier), tool/external refreshes were 151 ms each, MCP connected/reconnected, three revisions
  persisted, no refresh loop formed, and off mode caused no revision.
- Substantive head `736c2e9` gate: Python unit/architecture `49 passed in 0.33s`; adapter
  `6 passed in 4.26s`; Python integration `9 passed in 1.45s`; repeated adapter `6 passed in 4.26s`;
  Python package and TypeScript builds passed.
- Evidence head `fb46df8` passed final all-fast (`49 passed in 0.31s`; adapter `6 passed in 4.25s`)
  and Python/TypeScript builds. Draft PR [#8](https://github.com/souten-yd/ExtendCodeAgent/pull/8)
  was published with an exact matching remote head and reported `MERGEABLE/CLEAN`; no GitHub
  Actions checks are configured.
- Final remote head `86b7f511d789c7d191bcbbd0b378eb790d0d3a44` passed all-fast, matched
  local exactly, and was `MERGEABLE/CLEAN`. PR #8 was marked ready and squash-merged as
  `1cc7fd26a4e13aaca051edba2d92a91827a2e5b6`.
- Post-merge `main`: Ruff/mypy passed; Python unit/architecture `49 passed in 0.31s`; adapter
  `6 passed in 4.26s`; Python integration `9 passed in 0.43s`; repeated adapter `6 passed in 4.26s`.
- PR-D closeout documentation worktree: all-fast passed with Python `49 passed in 0.34s` and
  adapter `6 passed in 4.26s`.

## 2026-08-13 — PR-E started

- PR-D closeout PR #9 merged as `01efc16b`; post-closeout main all-fast passed with Python
  `49 passed in 0.28s` and adapter `6 passed in 4.26s`; package and TypeScript builds passed.
- Created `agent/pr-e-context-test-runtime` from exact `01efc16b`.
- Read the bounded PR-E plan/audit sections and inspected KasaneCore runtime reconciliation,
  collectors, context broker/query behavior, and direct tests before writing production code.
- Chose ADAPT for truthful revision-aware runtime/context behavior, CONSOLIDATE for existing target
  contracts, NEW for Test Obsolescence, and DO NOT PORT for Atlas runners/application DTOs.
- Added behavior-first pure-domain slices for immutable runtime observations/reconciliation,
  confidence-aware test selection, six-state test health, and bounded weak/standard context.
- Expanded architecture boundaries to the new host-neutral packages. Focused `12 passed`; all-fast
  passed with Python `61 passed in 0.48s` and adapter `6 passed in 4.25s`.
- Added SQLite runtime observations with idempotent restart-safe storage, collision rejection,
  workspace isolation, and ref lookup; integrated runtime/context/test health into the existing
  application/store rather than adding a parallel coordinator.
- Verified fresh green to stale after source refresh and off-mode inertness. Focused `8 passed`;
  all-fast Python `63 passed in 0.43s`, adapter `6 passed in 4.27s`; integration `11 passed in
  0.60s`, repeated adapter `6 passed in 4.27s`.
- Added strict sidecar context/runtime operations, two stable plugin/MCP query tools, and adapter-only
  tool observation normalization. Unknown stable-host outcomes remain observed, explicit exit
  metadata controls pass/fail, output text is not persisted, and `pi_*` calls do not recurse.
- Sidecar/adapter gate: all-fast Python `63 passed in 0.43s`, adapter `9 passed in 4.27s`;
  integration `12 passed in 1.18s`, repeated adapter `9 passed in 4.27s`.
- First extended real-host run disproved the assumption that model-free session shell emits stable
  tool hooks: it produced zero observations. A real local Ollama Qwen 3.6 27B agent `bash` call did
  emit one hook, persisted/reconnected correctly, and truthfully normalized to `observed` because
  actual metadata had no exit status; off added no evidence. Eight `pi_*` tools were discovered.
- Initial real-repo PR-E benchmark: cold graph/symbol 2,164 ms; standard context 100 items/2,131
  tokens, weak context 8 items/148 tokens; both p50 about 28.6 ms. Test selection p50 30.90 ms and
  safely fell back to full suite for the selected uncovered/unaligned target.
- Diagnosed that fallback as a concrete `src.` implementation versus public package re-export gap,
  not missing tests. Added an import-evidence-constrained Python resolver bridge and a name-collision
  fixture; the focused graph analysis suite passed and the worktree benchmark recovered two
  candidates with no fallback. Kept the correction out of generic Impact and out of other languages.
- Exact `47d47cd` PR-E evidence: benchmark found two test candidates/no fallback; standard context
  was 100 items/2,131 tokens and weak context 8 items/148 tokens. Serial model-free and real-Qwen
  OpenCode 1.18.18 smokes passed; the real tool observation persisted as truthful `observed`.
- Final gates: Ruff/format/mypy passed, Python 64 tests passed, adapter 9 tests passed, integration
  12 tests passed, and Python package plus TypeScript build passed.
- PR #10 remote head `571bd86` matched the published branch and was mergeable with no GitHub CI;
  it squash-merged to `main` as `fbdfcbd3864a3c46b76cc9ff10d77a57639258a6`.
- PR-F behavior-first contracts were committed red, then implemented as immutable Blueprint
  payload/lifecycle plus schema-independent task Convergence, shared SQLite durability, application
  projection, and centralized policy guards. Full fast gate passed 75 Python and 9 adapter tests.
- Standalone exact-head PR-F 200-element benchmark: lifecycle 16.1298 ms, convergence p50 0.2348
  ms/p95 0.3639 ms, restart 1.8938 ms, DB 241,664 bytes, max RSS 23,548 KiB, decision `complete`.
  A concurrent gate run was slower from host contention and was not used as the reference value.
- PR-F final gates: Ruff/format/mypy PASS, Python 75 passed, adapter 9 passed, integration Python 13
  passed plus adapter 9 passed, and Python package/TypeScript build PASS.
- PR #12 remote head `44d123b` matched and was mergeable with no GitHub CI; it squash-merged to
  `main` as `157fd19b56db6c61e61b5f02ab81e3bf985d79fd`.
- PR-G extended the existing router with adaptive signals and execution metrics, added live
  OpenAI-compatible/OpenCode host adapters, and added deterministic Strategy scoring plus strict
  model synthesis. Real conformance passed on Qwen3 0.6B, Qwen 3.6 27B, and OpenCode big-pickle;
  the trivial host prompt consumed 8,250 input tokens, so it is not a weak-model bounded path.
- Real evaluation forced three corrections: cap OpenAI-compatible output and disable Qwen thinking
  for focused structured questions; use OpenCode `tools: {"*": false}` rather than an empty map;
  and aggregate every assistant message including cache/tool/cost before deleting the session.
- Exact implementation-head six-case results: local-low off/advisory/active 1/4/6 successes;
  local-medium 1/6/6; host native/off/advisory/active 6/2/4/6. Host native used 40 tool calls and
  78.016 s versus active zero calls and 14.509 s. No run mutated the worktree.
- Frontier `llama/llama-3.3-70b-instruct` returned OpenCode `APIError` for all 18 attempts. Adapter
  failure detection was corrected and reverified; frontier remains unavailable, not passed.
- Final PR-G local gates passed: Ruff/format/strict mypy, 85 Python tests, 9 adapter tests, Python
  sdist/wheel and TypeScript builds, 13 Python integration tests, and repeated 9 adapter tests.
- PR #14 was published from exact local/remote head `f772017fc4848cee7f6e4535ce2cbf9e06b55104`;
  no GitHub Actions checks are configured. Mergeability was still calculating at first query.
- PR #14 final remote head `1189c966a71d410a42ab3f51ed35d18b4c2f5af9` matched local and was
  `MERGEABLE/CLEAN`; it squash-merged as `3386cfa429caf5b476e8abc5d52d87a8ab99c719`.
- Post-merge main all-fast passed with Python 85 tests in 0.64s and adapter 9 tests; Python
  sdist/wheel and TypeScript builds passed.
- PR-G closeout PR #15 merged as `fe61a16e8f7f07e760d99ca449bc09c90166a6c5`; created
  `agent/pr-h-js-ts-deep-graph` from exact clean main and began bounded search-first inspection.
- PR-H classified current contracts/Twin/Impact as REUSE, KasaneCore JS/TS fixtures as ADAPT,
  tree-sitter analyzer/composite as NEW, and regex/parallel graph/always-on deep graphs as DO NOT
  PORT. Initial focused collection fails only on missing target analyzer exports, as intended.
- Added independently configured tree-sitter JS/TS/TSX analysis, small multi-language composition,
  and a language-owned JS ref resolver. Focused 12 tests and all-fast (90 Python, 9 adapter) pass;
  persisted incremental refresh reanalyzes an importing TS test and removes its stale resolved call.
- The first ControlDeck measurement exposed py-tree-sitter 0.26.0 native crashes. Pinning 0.25.2,
  streaming Node traversal, reusing parsers, and retaining only pure descriptors passed the same
  cold/incremental path in three independent processes; full fast and build gates passed afterward.
- Equal-baseline measurement disproved unconditional incremental preference: App.tsx affected 60
  of 133 JS/TS modules and took 4,931 ms incrementally versus 1,187 ms full. The existing Twin now
  deterministically selects full at 40% module coverage; three automatic runs were about 1.19s.
- ControlDeck ground truth found 92 Playwright inline tests versus zero initial test nodes. Added
  callback declarations behavior-first; graph recall became 92/92, with 39 tests carrying static
  evidence and the remaining dynamic/browser cases left truthful and unlinked.
- Final PR-H benchmark: 454 source files, 1,347 nodes, 5,597 edges, cold 5,789 ms, auto refresh
  1,389 ms, DB+WAL 17,438,936 bytes, max RSS 76,512 KiB, impact mean 0.0282 ms. Measurement did not
  justify always-on CFG/DFG/state/event/UI graphs; they remain independently configurable on-demand
  future analyzers rather than being added without a task benefit.
- PR #16 was created after final all-fast/build/integration/benchmark/diff gates; no GitHub Actions
  checks are configured and mergeability was still calculating at the initial query.
- PR #16 exact remote head `46306bf225035f2c40798a81992ac9f525eed5c0` was repeatedly
  `MERGEABLE/CLEAN` and squash-merged as `fdeeb4e694fa7f416bb3ac7e92f49952d31e1767`.
  Post-merge main passed all-fast (91 Python, 9 adapter) and both package builds.
- PR-I extracted bounded research/evidence/claim/gap/deficit behavior behind provider-neutral ports,
  added immutable evidence durability to shared SQLite, and projected explicit requirement IDs
  through the existing Convergence engine. External evidence remains observed and cannot complete.
- Added centrally policy-gated application behavior and MCP `pi_research_plan`; all-fast passed with
  99 Python and 9 adapter tests.
- PR-I benchmark on ExtendCodeAgent: 200-requirement Convergence mean 0.5424 ms/p50 0.5290 ms,
  1,000 research plans mean 0.0020 ms, 200 evidence inserts 196.650 ms, restart PASS, DB+WAL
  17,771,744 bytes, max RSS 59,644 KiB.
- PR #18 was created after final all-fast/build/integration/benchmark/diff/boundary gates; no GitHub
  Actions checks are configured and mergeability was calculating at the first query.
- PR #18 exact remote head `dab1969e2c6bd3fa93957af70d5c5dfe9428a8ce` was repeatedly CLEAN
  and squash-merged as `c2f2dc77700eb38291816d758e43aa27cd2ff06c`. Post-merge main passed
  all-fast (99 Python, 9 adapter) and both builds.

## 2026-08-14 — Productization phase activated

- PR #20 merged as `731f587d600d5a563a26231d801e248f5f176c32`, defining the
  evidence-driven productization and multi-model evaluation phase.
- PR #21 merged as `a87d2fc6453c2f0d7bb9d1ccb8e48e16e2b7f1a7`, defining the staged
  transparent task-aware Project Intelligence rollout.
- Synchronized `main` to exact `a87d2fc6453c2f0d7bb9d1ccb8e48e16e2b7f1a7`.
- Verified the pre-RV-0 baseline: all-fast PASS (99 Python, 9 adapter), integration PASS
  (16 Python, 9 adapter), and Python/TypeScript build PASS.
- Rechecked installed and npm-stable OpenCode as `1.18.18`.
- Preserved two pre-existing untracked release-validation helpers without including them in this
  docs-only closeout.
- Recorded A-I implementation complete, Productization active, Transparent Task-aware PI planned,
  and RV-0 next. The known frontier `0/18` OpenCode `APIError` and local-low stochasticity remain
  open evidence items, not implementation-complete claims.
- 2026-08-16: Stopped the old-head B0a baseline at 137/306 checkpointed cells after confirming
  `native` is pure OpenCode rather than PI-enabled. No process remained and no partial cell entered
  the report.
- Added a sealed four-model `b0a-activation` schedule and fail-closed same-head prerequisite for
  comprehensive B0a runs. Activation requires real PI tool calls, observed capability state, Twin and
  canonical-evidence provenance, and PI timing; task-oracle outcome stays independent.
- Added a 27-cell port-8090 effect pilot (`native/off/active` x three representative tasks x three
  repetitions). It emits `PROCEED_TO_COMPREHENSIVE` only for an objective active gain with observed
  PI, off inertness, no provider/timeout failure and bounded median latency; otherwise it emits
  `REPAIR_AND_RETEST`.
- Found and repaired evaluation-environment contamination from an old refactor cell whose editable
  install pointed the shared `.venv` at a temporary workspace. Agent subprocesses now exclude the
  runner venv and root `PYTHONPATH` and set pip to require an isolated virtualenv; the sidecar retains
  its explicit ECA interpreter.
- Hardened resume so source revision, sealed schedule, activation evidence, pilot evidence and trace
  path must match exactly; non-resume runs refuse existing output/trace paths. This mechanically
  prevents the old 137 cells from entering corrected evidence.
- Audited capability reachability before spending the 714-cell screen. Four of thirteen ablatable
  capabilities (`blueprint`, `convergence`, `traceability`, `strategy`) currently lack OpenCode
  runtime/task routes, so the activation contract blocks comprehensive execution pending bounded B1
  adapter repair.
- PR #48 merged the activation guard as `0a1a9f4e4b289fdef7c8a4ac225000b537e4a37b` after all-fast
  (183 Python, 9 adapter), integration (36 Python, 9 adapter), build and schedule-count gates passed.
- Ran the four-cell activation gate at that exact head through port-8090 Qwen, host-default, Copilot
  Sonnet and Copilot Codex. Every cell called `pi_status` and `pi_symbol`, returned a ready Twin,
  revision, canonical evidence and positive PI time, and had no provider error. The aggregate
  correctly failed because three configured capabilities were observed off; no pilot cell ran.
- Traced the common failure to split OpenCode integration configuration: the MCP child received the
  generated project config but the plugin process did not, and the MCP entry point hard-coded
  advisory. Began a bounded repair to propagate one config/mode to both routes before rerunning.
- PR #49 merged that propagation repair as `ebe2a197fddf019bd2e40bbd372349a5f835d482`. Its fresh
  four-model activation run passed every observed PI requirement; task oracles remained separately
  FAIL and therefore made no effect claim.
- Stopped the first pilot attempt after eight completed native cells because arm-major ordering had
  not reached `off` or `active`, while one completed native test-selection cell took 256,319ms. The
  eight cells remain diagnostic only. Began a staged task-interleaved repair: 9 cells first, then 27
  total only if the initial effect and latency gate passes.
- PR #50 merged staged interleaving as `6ab0850a513b0ee22ea82c1599e151bdc572fcc8`; its exact-head
  activation passed all four required routes.
- Stopped the staged pilot after the first native/off/active symbol triplet. Active observed its
  required PI successfully, but off selected the duplicate `extendcodeagent_pi_status` MCP route and
  OpenCode raised a tool-result shape error, leaving disabled state unobserved. Began a bounded
  single-route repair: plugin tools/one sidecar in causal cells, MCP in dedicated lifecycle tests.
- PR #51 merged the single canonical plugin/sidecar route as
  `6064e311c3f98fe37ab87c6c1e71603ef08db7b2`. Its exact-head activation passed 4/4. The first sealed
  9-cell tranche produced native/off/active PASS 0/0/1; active test selection passed, active median
  was 124,194ms and the ratio to the slower control was 1.051.
- Continued same-head confirmation only because the initial gate permitted it, then stopped at
  12/27 after repetition-2 active symbol timed out at 300,157ms. The checkpoint contains one PASS,
  ten FAIL and one TIMEOUT and is diagnostic repair input, not comprehensive evidence.
- Began bounded B1 attribution/timing instrumentation without changing task oracles. Sidecar results
  expose cold Twin build, snapshot load, adjacency/index build, query and JSON serialization time;
  the evaluation trace adds post-PI agent/model residual from the first PI result after subtracting
  later tool execution.
  Exact failures additionally record
  required-fact recall, schema validity, final exact pass and retrieval/projection/reasoning class.
- Attribution/timing slice gates pass: `all-fast` (183 Python, 9 adapter), integration (39 Python,
  9 adapter), strict mypy, focused trace/sidecar tests and Python/TypeScript build.
- Post-merge exact-head smoke found that the initial residual counted only from the final PI tool and
  exposed binary-float noise in summed serialization time. Corrected it to cover the interval from
  the first PI result through cell completion while subtracting every later tool interval, and round
  accumulated millisecond segments to three decimals.
- PRs #52/#53 merged the instrumentation and correction as `e901329`/`1116d6b`. A fresh exact-head
  active-symbol smoke through ControlDeck-managed OpenCode recorded wall 57,990ms, PI tool 161ms,
  cold Twin 474.730ms, snapshot 149.969ms, adjacency 0ms, query 6.191ms, serialization 0.043ms and
  post-PI residual 23,066ms. Report and hash-chain trace agree. Outcome was one
  `RETRIEVAL_MISSING` FAIL, so this is measurement-path evidence only. Versioned summary:
  `docs/evidence/final/b1-pi-timing-smoke.json`.
- Added `compact`/`detail` views to existing `pi_symbol`, `pi_impact` and `pi_tests`; no new tool was
  introduced. OpenCode plugin/MCP default to compact, direct application compatibility stays detail.
  Compact symbol projects definition/export/direct production source/tests and explicitly reports
  unresolved structural coverage. Compact impact separates focused lexical/source-aligned tests from
  the complete candidate list and reports unresolved dynamic/structural/repeated-use boundaries.
- Clean ECA task-workspace proof returned exact `select_tests` definition, export, application caller
  and both expected tests. `_edge_meets_confidence` returned the exact three production methods and
  focused unit graph test; direct use count remains 3 graph callers versus four source occurrences,
  and the architecture test remains absent. Both are deliberately unresolved inputs to the next
  structural-obligation slice rather than hidden as complete.
- Compact projection gates pass: `all-fast` (185 Python, 9 adapter), integration (39 Python,
  9 adapter), strict mypy, clean-workspace projection smoke and Python/TypeScript build.
- Upgraded Python graph facts to `python_ast.v2`: repeated `calls`/`may_call` edges retain an
  `occurrences` count; module-level source `Path` bindings are resolved and linked from test
  functions that directly use them as `structurally_covers`; test nodes retain bounded AST intent
  tokens. Incremental facts remain source-owned and revisioned in the existing Twin.
- Compact impact counts occurrence facts across canonical aliases and requires intent overlap before
  promoting broad architecture coverage into focused tests. Compact test selection reports bounded
  unit/integration/architecture obligations, explicit gaps and fallback requirement.
- Clean ECA task-workspace proof exactly produced impact methods 3/use count 4/focused tests 2 and
  required-verification selected tests 3 with `coverage_complete=true`. This closes the two measured
  projection gaps only; generic TestIntent, dynamic coverage and held-out recall remain unproven.
- Structural-obligation gates pass: `all-fast` (187 Python, 9 adapter), integration (39 Python,
  9 adapter), strict mypy, clean-workspace exact projection proof and Python/TypeScript build.
- Added revision-scoped in-process query caches for immutable snapshots, exact symbol buckets and
  `GraphAnalysisService` adjacency indexes. Current revision is checked before reuse; Twin open,
  refresh, close or revision mismatch invalidates the caches. `pi_references` now consumes the shared
  reverse index rather than scanning all edges per call.
- Clean ECA task-workspace query measurement after cold symbol: cached snapshot load
  0.045/0.018/0.016ms and query 1.697/0.739/0.244ms for impact/tests/symbol; cached adjacency rebuild
  is 0ms. The 506.273ms cold Twin is cumulative trace context, not repeated work.
- Revision-cache gates pass: `all-fast` (188 Python, 9 adapter), integration (39 Python, 9 adapter),
  strict mypy, refresh-invalidation test, clean-workspace segmented query measurement and
  Python/TypeScript build.
- Added two composite OpenCode routes for the four remaining configurable capabilities. `pi_plan`
  invokes Strategy scoring over Project Truth and projects a non-durable-by-default Blueprint;
  `pi_verify` invokes Traceability plus Convergence and preserves the distinction between
  materialized facts and verified evidence.
- Fixed command-mode propagation so `blueprint`, `convergence`, `traceability` and `strategy` are
  active in the real sidecar, then proved both tools through the MCP lifecycle test. Results expose
  `capabilities_used`, and the evaluation runner records those observations in hash-chained trace
  `used_features`.
- Sealed covered-task routing without changing task/oracle truth: `eca-refactor-001` exercises
  `pi_plan`; `cd-cross-boundary-001` exercises `pi_verify`. Screening now returns
  `NOT_TESTED_ROUTE_GAP` rather than `no_screened_effect` if a required composite call or active
  capability observation is missing.
- Missing-route gates pass: `all-fast` (190 Python, 9 adapter), integration (39 Python, 9 adapter),
  strict mypy, real sidecar/MCP calls and Python/TypeScript build.
- PR #58 merged the composite routes as `b67f9514937d62a1f235baf95f2e2581183dabc3`.
  Fresh same-head activation passed all four model routes with no capability gap. The sealed 9-cell
  pilot then produced native/off/active PASS 0/0/0 and correctly stopped with
  `REPAIR_AND_RETEST:no_objective_pass_effect`; active median was 0.993x the slower control and all
  PI/off observations passed without provider error or timeout.
- Raw active traces proved the agent explicitly selected `detail` for symbol and impact, bypassing
  the compact repair; the detailed impact payload was truncated by OpenCode. `pi_tests` received
  directory strings, returned `full_suite`, and the agent omitted the unit verification test.
- Began a bounded last-mile repair: plugin/MCP symbol and impact are compact-only; tests require a
  natural-language objective and accept optional refs. Deterministic intent ranking selects one best
  unit, integration and architecture obligation. Direct queries on the pilot workspace now return
  the exact sealed symbol, impact and three-test fact sets.
- Compact-enforcement gates pass: `all-fast` (191 Python, 9 adapter), integration (39 Python,
  9 adapter), strict mypy, exact pilot-workspace projection proof and Python/TypeScript build.
- PR #59 merged compact enforcement as `b128adedc632644fb0c58fbe915126ef9b9d83ea`.
  The first new-head activation cell correctly used compact symbol facts, but the runner only
  recognized object fields named `canonical_ref`; it did not recognize compact `symbols`/`*_refs`
  arrays and failed `canonical_evidence_not_observed`. Stopped after the first cell because the same
  deterministic collector defect would invalidate all four models.
- Extended evidence collection to treat URI values in `symbols` and `*_refs` arrays as canonical
  evidence, with an integration assertion. This changes attribution only, not task/oracle truth.
- PR #60 merged compact evidence collection as `130f0a28b947ed2f39409a34b58aa9e823c31e99`.
  Fresh exact-head activation passed Qwen, host-default, Copilot Sonnet and Copilot Codex.
- Stopped an active-only diagnostic after one Qwen repetition over all three pilot tasks. Compact PI
  required-fact recall was 1.0 in every task; tests PASS, symbol dropped one returned path, and impact
  added prose/objects. This 1/3 result has no controls and is diagnostic only.
- Clarified orchestration without changing tasks/oracles: every answer task treats requested keys as
  an exact schema with no extra keys; active cells preserve matching compact values without removing
  paths or expanding them into explanation objects. Added a direct instruction-contract test.
- Validation at the pre-PR working tree passed `tools/local/all-fast` (191 Python plus 9 adapter),
  `tools/local/test-integration` (40 Python plus 9 adapter), `git diff --check`, and unified
  evaluation validation.
- PR #61 merged exact answer projection as `170649043f502c41ebca119ff495b2e9809eda6d`.
  Fresh four-model activation passed. The same sealed 9-cell pilot produced native/off/active exact
  PASS counts 0/0/2 and active PI required-fact recall 1.0 on all three tasks. Median wall times were
  91,611/100,609/70,107ms.
- The gate correctly stopped before 27 cells because the tests cell had no canonical URI evidence.
  Raw inspection proved `pi_tests` returned the exact three repository paths and Qwen copied them
  into its passing answer. Added repository-path evidence collection and a pilot-only acceptance
  rule while retaining the activation gate's canonical URI requirement.
- Post-repair validation passed `tools/local/all-fast` (191 Python plus 9 adapter),
  `tools/local/test-integration` (41 Python plus 9 adapter), `git diff --check`, and unified
  evaluation validation.
- PR #62 merged path evidence attribution as `d36d9104c8228acbaadab69d650749aed96b3b55`.
  Fresh activation and the initial 9-cell pilot passed with native/off/active 0/0/2, active fact
  recall 1.0, and no PI observation failures.
- Stopped confirmation at 14/27 after off impact repetition 2 timed out at 420,088ms. ControlDeck
  llama.cpp logs showed 27,998 continuously decoded tokens at about 67 tokens/second before cancel;
  the cell had not completed its first response and PI was disabled.
- Added an arm-neutral local-practical output limit of 8,192 tokens to the matrix and generated
  OpenCode provider config. Resealed matrix, screening and activation plans. Validation passed
  `tools/local/all-fast` (191 Python plus 9 adapter), `tools/local/test-integration` (42 Python plus
  9 adapter), unified evaluation validation and B0a bootstrap validation.
- The first post-PR #63 activation failed local-practical in 488ms before OpenCode initialization.
  Direct reproduction exposed `Missing key ... limit.context`; `debug config` had rendered the
  incomplete object without enforcing the run-time schema. Added sealed context 262,144 alongside
  output 8,192 and regenerated dependent seals. This failed activation is not pilot evidence.
- A direct real `opencode run --pure` against the ControlDeck port-8090 model with the completed
  limits exited 0, returned the requested `hi`, emitted 69 output tokens and no stderr.
- PR #64 merged the completed local limits as `7e58751b05ec310412c3406c8b9ae1142fdd1c6c`.
  Fresh four-model activation passed. The new-seal 27-cell pilot completed without timeout and
  returned `PROCEED_TO_COMPREHENSIVE`: native/off/active exact PASS 0/0/6, active median 72,100ms
  versus 105,688/109,601ms controls, with no observation failures.
- Active task results were symbol 1/3, impact 3/3 and tests 2/3. PI required-fact recall was 1.0 for
  every symbol/impact cell and 0.333/1.0/1.0 for tests. This separates remaining final projection
  and objective retrieval variance from the confirmed aggregate effect.

## 2026-08-17 — B0a adaptive screening and Minimum Sufficient Reasoning

- Added Master Plan Invariant 11 and the corresponding mandatory AGENTS rule: deterministic PI,
  bounded context and compatible evidence precede model reasoning; expansion requires an unresolved
  evidence gap and skipped work never becomes PASS or no effect.
- Kept the sealed 714-cell task/oracle/corpus/effect contract as the hard maximum and added a sealed
  adaptive policy plus deterministic scheduler. Active non-status PI traces select relevance,
  D0-D4 preflight folds task-output-equivalent depths, repetitions advance 1 -> 2 -> 3 only while a
  threshold boundary remains, and positive screening signals stop for B0b confirmation.
- Added a serial-model/CPU-worker pipeline with task templates, measured worktree/reflink selection,
  durable agent captures before oracle work, reasoning fingerprints, compatibility migration and
  formal call/context/token/time/reuse metrics. Persistent OpenCode has a separate isolated Bridge
  command and remains disabled unless repeated oracle-equivalent speedup is measured.
- The preserved old 24-cell checkpoint exposed one refactor cell that explicitly activated and
  retargeted the shared repository `.venv`. Restored the root editable install, added an all-arm
  external-directory deny, and made adaptive compatibility reject that cell rather than reuse it.
- Pre-commit gates passed: `tools/local/all-fast` (199 Python, 9 adapter),
  `tools/local/test-integration` (60 Python, 9 adapter), `tools/local/build`, and
  `git diff --check`.
- Clean commit `6cbacaf` exact-head analysis produced 102 candidate cells, 23 reusable cells, 27
  expected new calls before the first decision, 79 maximum new calls, 534 no-active-use skips and
  78 depth-equivalent skips. Successful-run p99 plus 10% margin set step/output limits to 24/4,668;
  git worktree won at 10.118ms median and reflink was unavailable.
- The one-call persistent OpenCode Bridge retained the same oracle contract but changed the observed
  outcome from PASS to FAIL and was slower (68,016ms attach versus 55,003ms per-cell, plus 2,710ms
  server startup). Persistent mode is not adopted. Evidence is sealed in
  `docs/evidence/final/b0a-adaptive-screening-execution-v1.json`.
- PR review found that a local provider gap could stop one batch but still permit later depth work
  and could classify the unavailable attempt as a completed cell. Provider attempts are now stored
  separately, the cell remains pending, and the entire adaptive frontier stops without another
  model call. Final integration count is 61 Python plus 9 adapter tests.
- PR #82 merged the adaptive implementation as exact main `e793103`. Exact-head deterministic
  planning recorded 714 hard-maximum cells, 102 adaptive candidates, 50 expected total results at
  the first decision (23 reusable plus 27 expected new), and 79 maximum new calls.
- The exact-main frontier completed with 30 new Qwen calls and 22 compatible reused results. All 714
  contract cells are accounted for; 684 calls were avoided with machine-readable reasons, for a
  95.7983% avoided-call ratio. No new timeout, provider gap, or step-limit termination occurred.
- Screening sent `graph`, `twin`, `semantic`, `impact`, `test_selection`, and `test_obsolescence` to
  B0b as candidates only. `blueprint` and `strategy` recorded no screened effect, while five other
  capabilities remained `NOT_TESTED_NO_ACTIVE_USE`. No promotion or demotion was taken, and the
  task suite, oracle, corpus, capability set and effect threshold were unchanged.
- New-call outcomes were 6 PASS and 24 FAIL. The run consumed 1,246,135 input and 105,016 output
  tokens over 3,663,284ms model wall time; total wall time was 3,667,392ms. Maximum observed steps
  and output were 20 and 4,607, below the evidence-derived 24/4,668 screening limits.
- B0a closeout gates passed: `tools/local/all-fast` (199 Python plus 9 adapter),
  `tools/local/test-integration` (61 Python plus 9 adapter), `tools/local/build`, evidence seal
  verification and `git diff --check`.

## 2026-08-17 — B0b local-only held-out confirmation runner

- Added `b0b-confirmation` to the unified schedule without changing the sealed matrix/task suite.
  The B0a result supplies exactly six candidates; the quality-target v2 exception supplies only
  local-practical Qwen; the sealed held-out split supplies four KasaneCore tasks and three runs.
- The resulting hard maximum is 108 calls: 36 mandatory native/off/active baselines and 72
  conditional ablations. Expected calls are conservatively 108 before active traces exist. After
  those baselines, only a capability-task pair exercised in all three PASSing active repetitions
  generates its complete three-repetition ablation; all skips keep machine-readable non-outcomes.
- Confirmation does not use screening's sequential positive stop or derived step cutoff. It keeps
  task timeouts and the sealed 8,192 model output limit so call economy cannot weaken correctness.
- The existing answer oracle now emits compact required-verification-set true/false positive and
  false negative counts plus precision/recall for held-out test-selection results; it stores no
  answer text and does not change oracle acceptance. B0b also aggregates cross-boundary exact
  follow-through and unsafe-claim completion correctness over active repetitions.
- Reused the sealed workspace Bridge result selecting git worktree; no compatible prior held-out
  confirmation evidence exists. Model execution remains serial while preparation and finalization
  use the existing CPU pipeline. Provider gaps remain attempts, leave the cell pending and stop the
  run without creating a quality result.
- Validation passes `tools/local/all-fast` (199 Python plus 9 adapter),
  `tools/local/test-integration` (66 Python plus 9 adapter), `tools/local/build`, five focused B0b
  scheduling/execution tests and `git diff --check`. No B0b model call ran before merge.

This implementation was never pushed or executed. It is superseded and removed by the causal-axis
correction below because its active-trace relevance would have mixed efficacy with agent selection.

## 2026-08-17 — Separate causal capability efficacy from auto selection

- Added a sealed EvaluationPIPlan covering all 13 unchanged tasks. Its inputs are task instruction,
  task class, oracle and capability responsibility; prior Qwen tool choice and outcome are excluded.
- Added evaluation-only `auto_pi`, `forced_pi`, `forced_off` and `forced_ablation:X` policies without
  changing core ACTIVE authority. Forced conditions receive the same task/model/prompt and exact
  tool request plan. Ordered tool inputs are retained from OpenCode logs and validated fail-closed;
  compliance/API gaps cannot enter causal scoring.
- Auto-use now reports expected/observed capabilities, precision/recall, under/over-selection and
  explicit per-capability states. `EXPECTED_BUT_NOT_USED` becomes `PI_SELECTION_GAP`.
- Added the B0b entry-gate runner with 24 initial and 58 maximum new local-practical calls. It reuses
  five current B0a task traces only for selection, requests one missing auto task, begins causal
  coverage at repetition 1, and spends repetitions 2/3 only on boundaries. Existing six candidates
  are preserved; Research and Test Obsolescence are `NO_TASK_COVERAGE` in this corrective gate.
- Audited nine forced pilot cells: required tool names were present, but exact inputs were not
  retained, so they are `REPLAY_REQUIRED_INPUT_PROVENANCE_MISSING`, not causal reuse.
- Validation passes `tools/local/all-fast` (207 Python plus 9 adapter),
  `tools/local/test-integration` (64 Python plus 9 adapter), `tools/local/build`, unified evaluation
  seal validation, focused causal simulation, model-free 24/58 schedule accounting and
  `git diff --check`. No corrective or B0b model call ran before implementation merge.

## 2026-08-17 — Corrective workspace path pre-model repair

- The first exact-main corrective attempt produced 24 process FAIL results but zero tokens and no PI
  trace. `WorkspaceTemplates` retained a relative root, and Git interpreted each worktree target
  relative to its template repository. OpenCode therefore received a path that did not exist from the
  ECA repository cwd. This is runner infrastructure evidence, not Qwen/capability evidence.
- Resolve the template/workspace root once at construction. Also count an LLM call as executed only
  after token evidence (or an explicit provider attempt), and record pre-model results separately so
  infrastructure failures cannot inflate model-call metrics.
- Repair validation passes `tools/local/all-fast` (207 Python plus 9 adapter),
  `tools/local/test-integration` (65 Python plus 9 adapter), `tools/local/build`, focused relative-root
  and causal accounting tests, and `git diff --check`.

## 2026-08-17 — Treatment-aware disabled response and capture reuse repair

- The repaired exact-main run produced eight real Qwen captures: one auto, six forced ON and one
  forced off. Forced ON request fingerprints all matched. The off route also matched its five-tool
  request fingerprint, but its expected `capability_unavailable` tool states were indistinguishable
  from an actual API failure because metrics retained only `tool_state_error`.
- Preserve the concrete tool error reason. For `forced_off`, capability-unavailable responses are
  expected treatment observations; for `forced_ablation:X`, only unavailability of X is expected.
  Missing/reordered/changed/extra requests and every unrelated error remain fail-closed.
- Add explicit compatible-capture reclassification. It accepts a source revision only when no
  non-evaluation product/adapter semantic path changed, reruns deterministic oracle/log parsing, and
  attaches source/current revision plus source-result hash provenance. This prevents eight needless
  repeated model calls while keeping current-run/new-call metrics separate.
- Validation passes `tools/local/all-fast` (208 Python plus 9 adapter),
  `tools/local/test-integration` (67 Python plus 9 adapter), `tools/local/build`, expected-disabled/
  unexpected-error classification tests, capture-reuse accounting tests and `git diff --check`.

## 2026-08-17 — Compatible result reclassification preserves source trace

- The first exact-main capture-reclassification attempt stopped before a new model call because it
  tried to append a regenerated trace with the same ID but a fresh deterministic-oracle wall time.
  The hash-chain correctly rejected that conflict.
- Reuse the already verified immutable source trace for a migrated cell and append only traces for
  cell IDs absent from the source chain. Compliance classification is report evidence and does not
  require rewriting the source execution trace. New cells continue to append normally.
- Validation passes `tools/local/all-fast` (208 Python plus 9 adapter),
  `tools/local/test-integration` (68 Python plus 9 adapter), `tools/local/build`, immutable migrated-
  trace coverage and `git diff --check`.

## 2026-08-17 — Causal ablation workspace identifiers are path-safe

- The first `forced_ablation:graph` cell exposed an OpenCode worktree-path encoding gap: `:` became
  `%3A` for the PI sidecar root, so the cell is preserved as diagnostic `PI_TOOL_API_GAP` and is not
  efficacy evidence. The following in-flight cell was stopped before completion.
- Evaluation workspaces now use a deterministic filesystem-safe name plus source-ID digest while
  cell IDs, captures and evidence identities remain unchanged. Compatibility migration rejects a
  forced capture whose exact-use compliance failed, so the diagnostic capture is preserved but
  rerun after repair rather than promoted.
- Validation passes `tools/local/all-fast` (208 Python plus 9 adapter),
  `tools/local/test-integration` (69 Python plus 9 adapter), `tools/local/build`, focused path-safety
  coverage and `git diff --check`.

## 2026-08-17 — B0a causal capability correction complete

- Completed the sealed local-practical corrective contract at `88d2e17`: 58/58 accounted by 22 new
  Qwen calls, 13 compatible reused results and 23 adaptive skips. Repetitions were sequential
  (24 r1, 7 r2, 4 r3); positive and diagnostic decisions stopped early.
- All 34 forced PI/off/ablation cells matched the exact EvaluationPIPlan request order and inputs;
  no provider gap, API gap, timeout or unavailable result entered causal scoring. The repaired graph
  ablation passed; the earlier `%3A` capture/checkpoint remains preserved as diagnostic history.
- Intrinsic positive signals: requirement tracing and symbol/reference. Corrective positive
  capabilities: Twin, Semantic, Blueprint and Strategy. The original six observational candidates
  remain intact, producing the eight-capability B0b union. No promotion/demotion decision was made.
- Auto selection measured mean precision 0.666667 and recall 0.534821 across eight measurable tasks,
  with 20 `EXPECTED_BUT_NOT_USED` states; auto-fail/forced-pass requirement tracing is
  `PI_SELECTION_GAP`. Twenty-two evaluation sidecars were terminated after evidence capture without
  deleting workspaces or logs.
- Validation passes `tools/local/all-fast` (208 Python plus 9 adapter),
  `tools/local/test-integration` (70 Python plus 9 adapter), `tools/local/build`, plan/result/final
  evidence seal verification and `git diff --check`.

## 2026-08-17 — B0b local-only held-out confirmation complete

- Merged the bounded runner first at exact main `f15064c`, then sealed a 57-cell plan and executed one
  ControlDeck-managed Qwen inference at a time. The final checkpoint has 57/57 results, 21 PASS, 36
  FAIL, 48/48 forced-use compliance and zero provider/process/timeout/unavailable outcomes.
- Forced PI versus off and Graph/Semantic/Twin/Test Selection ON versus ablation all had zero PASS
  delta. Four other candidates remain `NO_HELD_OUT_TASK_COVERAGE`. No task, oracle, corpus, threshold,
  capability or rollout authority changed, and no promotion/demotion was emitted.
- The run exposed completed-worktree retention after durable capture, eventually filling the local
  disk. Removed only recreatable generated worktrees, preserved checkpoint/captures/fragments/logs,
  truncated one partial trace tail to its last valid newline, and resumed without repeating completed
  model work. The completed trace is unique/replayable for all 57 results.
- `WorkspaceTemplates.discard` and the CPU finalization pipeline now remove only the exact generated
  workspace after durable cell capture/finalization; prepared pending cells are also cleaned after a
  provider-gap stop. Unrelated templates/worktrees are never removed.
- Corrected efficiency instrumentation measures a request context as input plus cached prompt tokens,
  rather than per-cell cumulative input. The sealed logs contain 538 requests with p95 68,512, p99
  86,351 and maximum 93,189 prompt tokens. Deterministic PI wall time uses observed `pi_*` tool
  intervals only. The immutable raw report is preserved with explicit correction provenance.
- Added aggregated required-verification-set precision/recall by use policy and overall. All 21
  measured cells were exact (84 TP, 0 FP, 0 FN), but off and ablation passed equally, so it is not
  claimed as an attributable PI improvement.
- Final gate results are recorded in `docs/evidence/final/b0b-confirmation-result-v1.json`; B0 gap and
  stage decisions are in `docs/evidence/final/baseline-gap-report.md`. Closeout validation passes
  `tools/local/all-fast` (208 Python plus 9 adapter), `tools/local/test-integration` (79 Python plus 9
  adapter), `tools/local/build` and `git diff --check`.

## 2026-08-17 — B2 coexistence runner

- Added a sealed B2 runner for the existing OMO-C0 contract. It fixes five independent stacks:
  native OpenCode, ECA, OMO 4.19.4, OMO→ECA and ECA→OMO. Team Mode is explicitly off and every stack
  receives its own ephemeral HOME/XDG profile, workspace, server and session.
- Model-free preflight checks unique tool IDs, exact `pi_*`/OMO visibility, absence of `team_*`,
  deterministic shell verification, clean sidecar shutdown, session/tool recovery after restart, and
  OMO usability when the ECA sidecar is unavailable in both plugin orders. OpenCode 1.18.18's direct
  shell route does not exercise plugin tool hooks, so that state is recorded explicitly rather than
  treated as efficacy evidence; the agent Bridge instead requires a real ECA runtime observation.
- Only a passing sealed preflight can open the five-stack coding/verification Bridge. Every request is
  fixed to Qwen3.6 27B on `127.0.0.1:8090`; Copilot/host-default credentials are removed from child
  environments, external OMO MCPs and telemetry are disabled, inference stays serial, and exact
  route/tokens/tool-call uniqueness/oracle/changed-files are recorded. A non-inference `/v1/models`
  check precedes every stack; provider/request gaps stop the run immediately, while atomic per-stack
  checkpoints allow completed reasoning to be reused with `--resume`. Context metrics use full
  `input + cache-read + cache-write` request size and retain p50/p90/p95/p99/max distributions.
- Corrected the coexistence design header: B2 owns bounded compatibility; P4 still owns the four-way
  comparative benefit claim. No OMO/OpenCode patch or ECA orchestration copy is introduced.
- The first real model-free preflight used zero LLM calls and exposed an ECA lifecycle defect: abrupt
  OpenCode termination did not call plugin `dispose`, leaving the spawned Python sidecar alive. The
  sidecar now treats closure of its parent-owned stdin pipe as shutdown, with a real subprocess test.
  It also showed OMO's own `glob`/`grep`/`task`/`skill` override IDs duplicated in the tool inventory;
  the runner compares both combined orders to that OMO-only control and records an unchanged set as
  an inherited C0 limitation, not as an ECA-induced registration regression or a PASS.
- The repaired branch preflight at `d936372` passed with zero model calls (seal
  `5e13dd36354b8474b4c6692b46cd9f68eef66b2f0b8b4f8a94fafc1db905fbd1`): all five stack/restart
  checks and both degraded-sidecar orders passed, sessions recovered, the real user OMO profile was
  unchanged, and no exact-workspace sidecar remained. The inherited OMO-only C0 limitation remains
  explicit. Exact-main regeneration is still required after the runner PR merges.
- Sealed `b0a-compatible-product-transitions-v1.json` binds the exact before/after SHA-256 pair for
  the two lifecycle-only adapter files. This preserves completed B0 model outcomes without reusing
  their lifecycle latency/cleanup metrics; any later content change, new product path, task/oracle/
  route/PI-semantic change fails compatibility closed. The causal-runner integration contract covers
  the approved transition so unrelated product edits still require replay.

## 2026-08-17 — B2 agent-flow runtime observation repair in progress

- The exact-main Qwen Bridge completed native PASS with four step requests. The ECA task and oracle
  passed with four step requests, but the B2 control failed because runtime observation count was zero;
  the run stopped before combined-stack evidence was accepted. A subsequently interrupted OMO attempt
  predates interrupt checkpointing, so its exact call count is unknown and remains explicit.
- The OpenCode post-tool hook now awaits bounded sidecar ingest and the observation normalizer supplies
  a non-secret fallback title for OpenCode 1.18.18 output lacking `title`. Focused TypeScript and Python
  tests pass.
- The B2 runner records operator interruption durably, stops on any failed control, separates executed
  from reused calls/tokens, and allows only exact-input migration of a successful native/no-plugin
  result. The task instruction is extracted from the source revision rather than assumed.
- Adaptive/causal compatibility now also inspects dirty worktree semantics. The runtime-hook and
  normalizer changes invalidate affected old-head product compatibility; the sealed lifecycle-only
  exception is unchanged.
