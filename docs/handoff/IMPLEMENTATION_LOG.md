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
