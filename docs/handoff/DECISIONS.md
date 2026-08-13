# Architecture Decisions

## 2026-08-13 — PR-A runtime and boundary

Decision: Start with a Python host-neutral core and defer the TypeScript OpenCode adapter and MCP process boundary to their dedicated milestone.

Reason: KasaneCore's reusable algorithms and contracts are Python, while PR-A needs to establish domain boundaries rather than plugin behavior. This follows the planning baseline's staged hybrid recommendation and avoids introducing an unused adapter package.

Consequences:
- `src/extendcodeagent/core` must have no OpenCode, Atlas, Nexus, MCP, or provider-SDK import.
- OpenCode stable and V2 beta types will be isolated under future adapter packages.
- Architecture tests enforce this before later migration begins.

Classification:
- ADAPT: immutable DTOs, explicit diagnostics, safe disabled/shadow semantics from KasaneCore.
- REPLACE: Atlas `ProjectIdentity`, rollout environment variables, and Project Intelligence composition DTOs.
- NEW: layered central config resolver, capability policy, role-based model routing contracts and deterministic fake adapters.
- DO NOT PORT: Atlas/PlanPool/Safe Apply/Nexus application types and provider-specific model logic.

GitHub Actions: not added. PR-A validation is local and offline by design.

## 2026-08-13 — Current OpenCode integration boundary

The stable plugin documentation currently exposes JavaScript/TypeScript plugin functions,
project/global plugin discovery, custom tools, and file/watcher/LSP/session/tool events. The
V2 plugin API offers richer transforms and hooks but is explicitly beta. OpenCode also accepts
local or remote MCP servers and provides local MCP management commands.

Decision: PR-A imports none of these shapes. Future stable, V2, and MCP integrations map into
host-neutral core requests through adapter packages. V2 compatibility changes must not require
core changes.

Sources checked 2026-08-13:
- <https://opencode.ai/docs/plugins/>
- <https://opencode.ai/v2/docs/build/plugins>
- <https://opencode.ai/docs/cli/>

## 2026-08-13 — PR-B migration classification

- ADAPT: immutable revision lineage, optimistic expected-head rejection, transaction atomicity,
  idempotency, historical snapshots, invalidation, restart persistence, and bounded source scans.
- CONSOLIDATE: KasaneCore project and workspace identity into PR-A `ProjectRef`; source/analyzer
  metadata into `SourceRevision`, `Provenance`, and Graph-domain contracts.
- REPLACE: Atlas/Pydantic DTOs, `project_id`-only store keys, `ca_data` defaults, and synchronous
  module orchestration with small host-neutral dataclasses/services and `(project, workspace)` scope.
- NEW: non-Git deterministic fingerprint fallback, explicit retention/export-import foundation,
  and real-repository local benchmark reporting.
- DO NOT PORT: semantic/static analyzers, impact/path, runtime observations, Atlas events/context,
  OpenCode/MCP, or model routing into PR-B.

GitHub CI remains unnecessary: all PR-B behavior, restart, benchmark, and packaging gates are locally reproducible.

## 2026-08-13 — PR-B persistence shape and incremental measurement

Decision: Persist immutable Graph contract payloads with normalized revision validity and
canonical/source/target indexes. Do not copy KasaneCore's semantic/runtime columns before their
consumers exist. PR-C may normalize additional query fields only when path/impact measurements
justify them.

Real-repository measurement (50 source files) showed cold build 185.638 ms and file-level refresh
182.145 ms. The refresh updates only selected facts, but the bounded workspace fingerprint scan
dominates at this size, so the latency improvement is only 1.9%. Snapshot query was 0.302 ms,
DB+WAL 255,448 bytes, max RSS 28,472 KiB.

Consequence: do not claim incremental speed superiority yet. Preserve correct incremental fact
semantics, and evaluate a Git-status fingerprint fast path plus an automatic full-rebuild choice
for small repositories in the next performance slice. The current behavior remains deterministic
and bounded.

## 2026-08-13 — PR-C migration classification and analysis boundary

- ADAPT: deterministic Python AST definitions/imports/decorators/inheritance/calls, bounded path
  traversal, reverse dependency impact, forward implementation expansion, weakest-link confidence,
  uncertainty, explanations, and test-candidate projection.
- CONSOLIDATE: semantic and structural facts into the existing immutable PR-B Graph contracts and
  snapshots instead of introducing KasaneCore `SemanticNode`, `TwinNode`, or result DTO copies.
- REPLACE: KasaneCore's generic impact-engine knowledge of `py://` and `pyname://` with a Python
  `CanonicalReferenceResolver` supplied to generic analysis.
- NEW: curated human-reviewable FP/FN evidence and a repeated-query local benchmark against native
  repository search.
- DO NOT PORT: Atlas/Pydantic contracts, old monolithic static analyzer, clone fingerprints,
  HTML/JS relations, LSP integration without a host-neutral consumer, runtime evidence, OpenCode,
  or LLM behavior.

The analyzer stays deterministic and stdlib-only. Unresolved dynamic dispatch is represented as
an inferred `may_call` edge with low confidence; it must never be promoted to a verified call.
GitHub Actions remain unnecessary because this slice is reproducible through local fixtures,
integration tests, package build, and benchmark scripts.
