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
