# Implementation Log

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
