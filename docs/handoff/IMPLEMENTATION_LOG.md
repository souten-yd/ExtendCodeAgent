# Implementation Log

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
