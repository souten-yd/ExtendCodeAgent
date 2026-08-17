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

## 2026-08-13 — PR-D stable OpenCode boundary

Decision: target stable OpenCode and `@opencode-ai/plugin` 1.18.18 in PR-D. Keep the documented V2
beta plugin surface as a future adapter rather than mixing stable and beta hook/config shapes.

Current stable evidence checked 2026-08-13:
- <https://opencode.ai/docs/plugins/> — `.opencode/plugins/`, `Plugin` context, event hooks, tools;
- <https://opencode.ai/docs/custom-tools/> — stable tool helper and execution context;
- <https://opencode.ai/docs/mcp-servers/> — named `mcp` entries, local command, `enabled`;
- <https://opencode.ai/docs/cli/> and <https://opencode.ai/docs/config/>;
- <https://opencode.ai/v2/docs/build/plugins> and V2 MCP docs, explicitly treated as beta/incompatible.

The stable TypeScript adapter may import OpenCode packages. Host-neutral Python packages may not.
Plugin hooks enqueue events into a bounded local interface; they do not run graph analysis inline.
Plugin tools and MCP tools share one Python query/application service.

GitHub Actions are still unnecessary. Plugin typecheck/build, Python tests, MCP protocol tests, and
real OpenCode smoke/reconnect evidence will run locally.

## 2026-08-13 — PR-D watcher fallback after real-host measurement

Real stable OpenCode 1.18.18 testing on Linux initialized its inotify backend and watched the
fixture directories, but the documented `file.watcher.updated` stream exposed `.git/index.lock`
events and did not expose ordinary tracked source rewrites. Consuming the Git lock events caused a
self-sustaining loop because Twin fingerprinting invokes Git.

Decision: reject the same managed/dependency/cache/build paths as the source snapshot before event
enqueue, and ADAPT a small Chokidar 4.0.3 fallback inside `adapters/opencode`. Native and fallback
file events use the same coalescing queue. The watcher starts only after the central sidecar reports
a non-off mode and closes with the plugin. Do not move filesystem watching into the host-neutral
core and do not patch OpenCode.

Alternatives rejected:
- Trust the native watcher despite missing real source events: fails external-edit acceptance.
- Poll the entire repository: adds avoidable scan latency and delayed refresh.
- Implement recursive platform watchers in-house: less maintainable than a bounded existing library.

Measured result: the reproducible smoke observed both an OpenCode session-tool format edit and an
external edit as distinct immutable revisions, stabilized without a loop, preserved three revisions
through restart, and left the revision count unchanged in off mode. Alternating three-run startup
medians were 1,046 ms native and 1,070 ms plugin-enabled (+24 ms); one native sample was a 1,609 ms
outlier, so these values are retained as smoke evidence rather than treated as a stable distribution.

## 2026-08-13 — PR-E runtime, test, and context migration boundary

Classification after inspecting the PR-E plan, migration audit, KasaneCore runtime reconciliation/
collectors, context/query tests, and current ExtendCodeAgent call paths:

- ADAPT revision-matched verification, explicit unavailable/failed/observed results, collector
  failure normalization, bounded context, inclusion reasons, and stale/contradicted labeling.
- CONSOLIDATE observation identity, source/Twin revision, canonical refs, confidence, provenance,
  and evidence with existing host-neutral contracts and immutable Graph snapshots.
- NEW a dedicated Test Obsolescence engine with healthy/suspect/stale/obsolete/missing/redundant
  states; file age alone is not evidence and no state authorizes automatic deletion.
- DO NOT PORT KasaneCore Pydantic/Atlas DTOs, execution runners, PlanPool adapters, or application
  context packaging.

PR-E uses deterministic algorithms and the existing CapabilityPolicy. Model summarization/routing,
Blueprint/Convergence, and JS/TS semantic expansion remain later independent milestones.

## 2026-08-13 — Stable tool-result truthfulness after real-host measurement

Stable OpenCode 1.18.18 `tool.execute.after` exposes tool/title/output/metadata but does not
guarantee an exit status. A model-free session-shell API edit did not emit this hook at all. A real
local Ollama Qwen 3.6 27B agent invocation did emit a `bash` hook, but its actual metadata contained
no explicit exit status.

Decision: the adapter records `passed`/`failed` only from explicit supported status or numeric exit
metadata. Unknown outcomes are `observed`, output text is not persisted, and session-shell API calls
are not claimed as runtime-hook evidence. This prevents a completed tool call from becoming false
verification. Automatic ingest is limited to shadow/active; advisory remains explicit-query only.

The temporary Ollama provider configuration follows current stable OpenCode provider documentation:
<https://opencode.ai/docs/providers/>. Live model routing remains PR-G; this PR-E use is only a
bounded adapter conformance check.

## 2026-08-13 — PR-E test-selection recall correction from real-repository evidence

The first PR-E benchmark selected the concrete implementation ref
`py://src.extendcodeagent.runtime.service#reconcile_observations`, while tests called the public
package re-export `py://extendcodeagent.runtime#reconcile_observations`. The generic Impact engine
therefore found no candidate and correctly fell back to the full suite. This disproved the planning
assumption that PR-C's existing concrete/name-only bridge covered installed-package source roots and
re-exports.

Decision: ADAPT only the Python-owned `CanonicalReferenceResolver`. Strip the conventional `src.`
prefix and derive package aliases only from Graph `imports` edges that target the exact concrete
definition. Do not hard-code Python aliases into Impact, equate every identical short name, or widen
PR-E into new semantic languages/edge extraction.

Alternatives rejected:
- accept full-suite fallback: safe, but fails useful real-repository test-selection recall;
- equate all same-named concrete functions: increases false positives across unrelated modules;
- redesign the analyzer/import graph in PR-E: exceeds the measured gap and PR scope.

Measured result before commit: the focused collision fixture passed and the real-repository
candidate count changed from zero/full-suite fallback to two graph-linked candidates/no fallback.
Exact-head latency and candidate refs are recorded with the PR-E evidence after commit.

## 2026-08-13 — PR-F immutable payloads and schema-independent convergence projection

KasaneCore confirms useful lifecycle/evaluator behavior, but its Blueprint module mixes immutable
content with generator/planner DTOs and its Convergence evaluator imports Blueprint implementation
models. Direct porting would violate the target's host-neutral and schema-independent boundaries.

Decision: ADAPT the behavior onto two small domains. Blueprint revision payloads are immutable rows;
review/approve/active/superseded status and the active pointer are operational metadata. Planned
elements require `bp://` or `planned://`, while expected Actual refs remain separate. Convergence
consumes only immutable `TargetSnapshot`, `ActualSnapshot`, and `VerificationEvidence` projections.
The persisted report carries only the dependency projection needed for deterministic downstream
decisions, not a Blueprint implementation model.

The existing shared SQLite store owns durability and workspace isolation. The existing
`ProjectIntelligenceApplication` owns projection and central CapabilityPolicy checks. No OpenCode
adapter, model call, Atlas planner, or new feature-specific environment switch is introduced.

Measured test evidence before commit: focused domain/store tests passed (10 tests), then the full
local fast gate passed Ruff/format/strict mypy, 75 Python tests, and 9 adapter tests. The application
test also proves creating a planned target does not change the Actual Graph node count.

## 2026-08-13 — PR-G bounded model execution after real-model measurement

Decision: extend the existing `PolicyModelRouter`; add live adapters only behind `ModelAdapter`;
keep Strategy scoring deterministic and allow the LLM to propose scope/explanations only. Strategy
now exposes all planned axes (scope, impact, test burden, migration complexity, compatibility,
rollbackability, performance, maintainability, cost, uncertainty). Equal scores return no selected
alternative and require a decision instead of selecting by identifier.

The first 27B evaluation exceeded ten minutes because an OpenAI-compatible request had no output
bound. A 128-token bound alone caused Qwen thinking to consume the entire allowance and emit empty
answers. Current Ollama documentation confirms `max_tokens` and `reasoning_effort=none` on the
OpenAI-compatible endpoint. The adapter therefore uses provider-neutral request fields for both;
the evaluation run completed 36 local cases in about 23 seconds. Alternatives rejected were an
unbounded timeout-only request and silently raising the bound, both of which violate the weak-model
bounded-payload requirement.

Real OpenCode 1.18.18 also disproved the assumption that `tools: {}` disables tools: off mode still
used 34 complete-session tool parts in the diagnostic run. Stable tool configuration supports a
wildcard, so the host adapter now sends `tools: {"*": false}` unless native tools are explicitly
enabled, and it aggregates all session messages before cleanup. A focused live check then measured
zero active tool calls versus two native calls. The exact six-scenario run measured native 40 tool
calls/78.016 s versus active zero calls/14.509 s, with both scoring 6/6.

Do not make active the default from this sample. Local-low varied between repeated runs, and
local-medium advisory already scored 6/6 with fewer prompt tokens. The central default remains off;
advisory is the safe opt-in until final multi-repository distributions justify automation.
Frontier returned OpenCode `APIError` for every attempt, so it is recorded as unavailable and cannot
satisfy the final release gate.

## 2026-08-13 — PR-H language analyzer boundary

Classification after inspecting the existing GraphAnalyzer/Twin/application callers, Python
analyzer tests, bounded PR-H plan/audit slices, and KasaneCore JavaScript/TypeScript/Vue analyzer
fixtures:

- REUSE the host-neutral `GraphAnalyzer`, immutable Graph facts, Twin refresh/invalidation, generic
  path/impact, confidence/provenance, and centralized configuration;
- ADAPT the useful KasaneCore behaviors: collision-free file-qualified refs, imports, definitions,
  components, deterministic invalidation, capability versions, and truthful degradation;
- NEW a tree-sitter-backed JavaScript/TypeScript analyzer and one small composite analyzer because
  the current application composes only Python;
- DO NOT PORT KasaneCore's regex-only parser, parallel `SemanticGraph`/registry DTOs, LSP wrapper,
  or always-on behavioral/CFG/DFG/UI inference.

Each language analyzer is selected only through centralized immutable configuration; feature code
does not read environment variables. Tree-sitter is preferred to regex because syntax errors are
observable and resolved facts can be distinguished from inferred dynamic calls. Framework
relations remain separate plugin-style analyzers. Deeper graphs remain on-demand and require a
measured scenario gap before implementation.

The first real ControlDeck benchmark process segfaulted before producing measurements. Retaining
each owning tree-sitter `Tree`, then replacing cross-file `Node` state with serializable descriptors,
still reproduced the crash on one isolated ControlDeck TSX file under py-tree-sitter 0.26.0. The
official grammar wheels expose mixed ABI 15 (JavaScript) and ABI 14 (TypeScript/TSX), both within
the binding's declared 13–15 range, but the same isolated analyzer passed repeatedly on
py-tree-sitter 0.25.2. Decision: pin 0.25.2, retain one parser per grammar, stream Node traversal,
and retain only pure-Python descriptors across files. Treat every failed run only as a safety
defect signal, never as benchmark evidence. Real-repository measurement may resume only after
focused tests and three repetitions of the same ControlDeck cold/incremental path no longer crash.

The safe run then disproved the assumption that incremental refresh is always the faster strategy:
on the same existing baseline, an App.tsx dependency closure covered 60 of 133 JS/TS modules and
took 4,931 ms, while explicit full refresh took 1,187 ms. Alternatives considered were persisting a
new symbol index in PR-H, always rebuilding JS/TS, or choosing from existing graph facts. Decision:
REUSE the Twin lifecycle and select full refresh when affected paths cover at least 40% of current
module facts. This is language-neutral, deterministic, observable through
`auto_full_refresh_selected`, and preserves narrow incremental behavior. Three measured automatic
runs took 1,193 / 1,192 / 1,187 ms with identical 1,255 nodes and 3,888 edges. A persisted index is
deferred because the measured full strategy already removes the regression without new storage.

The ControlDeck ground-truth run found 92 Playwright inline tests but the initial graph represented
none. This is a JS/TS declaration gap, not evidence for deep CFG/DFG, so inline callbacks were
ADAPTED into stable test definitions and existing call/Impact behavior. The result represented all
92 tests and found static evidence for 39; the other 53 depend on browser/API/dynamic behavior and
remain unlinked rather than fabricated. Cold build was 5,789 ms, automatic refresh 1,389 ms, and 20
impact queries averaged 0.0282 ms. Decision: do not add always-on CFG/DFG/state/event/UI graphs in
PR-H. They add maintenance and certainty risk without closing the measured browser/runtime gap.
Keep framework/deep analyzers independently configurable and on-demand for a future concrete UI or
security benchmark; this follows the PR-H measurement stop gate rather than treating the plan as a
mandatory implementation list.

## 2026-08-14 — PR-I research and traceability boundary

After inspecting the existing shared evidence/provenance contracts, CapabilityPolicy, SQLite,
Runtime, Blueprint/Convergence projections, sidecar/MCP callers, bounded PR-I plan/audit text, and
KasaneCore research/requirement behavior:

- REUSE `ProjectRef`, `SourceRevision`, `EvidenceRef`, `EvidenceStatus`, `Provenance`, immutable
  dataclasses, centralized `RESEARCH`/`TRACEABILITY` modes, SQLite ownership, and the existing
  target/actual/verification Convergence evaluator;
- ADAPT bounded request/depth budgets, source candidates, claim-level evidence, explicit coverage
  gaps/retrieval deficits, and KasaneCore's rule that explicit requirement IDs are authoritative;
- CONSOLIDATE project convergence by projecting requirements into the existing `TargetSnapshot`
  vocabulary instead of creating a second completion engine;
- NEW small `SearchPort`, `FetchPort`, `ExtractPort`, `EvidenceRepository`, and `SynthesisPort`
  protocols so OpenCode web/MCP or local implementations can call the same core;
- DO NOT PORT Nexus jobs/events/heartbeats/UI, SearXNG, downloader/library/application databases,
  Atlas Pydantic schemas, prompt rendering, keyword-only verification, or raw provider result shapes.

External research evidence is always external provenance and cannot verify a Project Graph fact or
requirement implementation by itself. Keyword/candidate matching may produce an observed link or a
coverage gap, never `verified`. Completion continues to require current project/runtime evidence.

## 2026-08-16 — Planning consolidation into a single execution plan

Context: the repository contained 26 planning documents (~10,650 lines) with three conflicting
"canonical read order" lists, eight parallel stage-numbering schemes (`RV-x`, `COMP-0/RA-x/TA-x/WL-0/
VI-0/RB-0/DA-0/EM-0/MA-0/RV-X`, `AL-x`, `CV-x`, `TP-x`, `VI-Xx`, plus two unnumbered ordered lists),
two incompatible evaluation corpora, one declared-but-unapplied absorption (`VI-0` absorbing `RV-3`),
and a release-gate list whose blocking items included an externally unavailable provider path.

Decision: `docs/PI_MASTER_EXECUTION_PLAN.md` becomes the single canonical execution plan. It owns
product scope, the capability inventory, the evaluation framework, one stage backlog and the release
gates. Every other planning document keeps its design detail and is registered there with an explicit
disposition. Legacy stage identifiers are mapped and retired from scheduling.

Consequences:

- Verification work that was split across five documents (`RV-3`/`VI-0`, `AL-2`, `CV-*`, `TP-0..TP-3`,
  `VI-X0..VI-X7`, failure-driven sequence) becomes one V-series with each object defined exactly once.
- A new Phase 0 precedes baseline validation. Ten of twenty-one declared capabilities are not gated by
  `CapabilityPolicy` — including `strategy` and `test_obsolescence`, which have real implementations —
  so per-capability ablation is currently impossible and no keep/demote decision could be supported.
  Phase 0 adds gating conformance (E1), the capability depth contract (E2), a unified evaluation runner
  with a Layer B task suite (E3), a versioned Layer A label set and unified runner (E4), and a
  minimal attributable PI trace (E5).
- The minimal PI trace is promoted into Phase 0 as evaluation infrastructure. Durable Project
  Evidence Memory becomes the first post-baseline stage, `P0`.
- The frontier model path becomes a conditional release gate with a documented exception rule. A
  provider outage outside the repository can no longer block the baseline indefinitely; the exception
  records the error category, the native reproduction, the withdrawn claims and the re-test trigger.
  It is never recorded as a pass.
- Both corpora are retained with distinct roles: the realistic-task corpus (ExtendCodeAgent,
  KasaneCore, ControlDeck) for agent outcomes and scale, and the pinned external corpus for
  deterministic quality ground truth. Held-out material stays outside tuning.
- Future strategy changes edit the master plan. A new design document requires a section 2 registration
  and a stage owner in the same commit.

GitHub Actions: not added. This change is documentation only.

## 2026-08-16 — E1 capability gating conformance

Context: `CapabilityName` declares 21 capabilities, but `CapabilityPolicy` was consulted only in
`service/application.py` and covered 11 of them. `strategy` and `test_obsolescence` had real
implementations that no configuration could switch off, `call_graph` was emitted unconditionally by
the analyzers, and seven names were pure declarations with nothing behind them. Per-capability
ablation — the precondition for every keep/demote decision in the evaluation framework — was
therefore impossible for 10 of 21 capabilities.

### Decision 1 — `call_graph` is folded into `semantic`, not gated independently

`call_graph` is recorded in `CAPABILITY_FOLDED_INTO` as governed by `semantic`. Its rollout mode is
always `semantic`'s, and configuring `project_intelligence.capabilities.call_graph` to anything other
than `off` is a `ConfigError` pointing at `semantic`.

Reason: `may_call` is emitted by `graph/analyzers/python.py` and
`graph/analyzers/javascript_typescript.py` inside the same AST/tree-sitter walk that emits `calls`,
`references` and `imports`; the two differ only by whether `_resolve_call` resolved the target.

Rejected alternative — an independent `call_graph` gate. It was rejected because it requires one of
two unacceptable mechanisms:

- passing `CapabilityPolicy` into the analyzers, which are pure revision-keyed functions today.
  Analyzer output would then depend on rollout mode, so the same source revision would produce
  different Twin revisions under different configuration. That breaks revision identity and the
  Evidence Dependency Closure that compositional evidence reuse is built on; or
- post-filtering `may_call` edges out of a stored snapshot, which leaves the stored graph and the
  served graph disagreeing and silently changes `impact` confidence without any record.

An independent arm would also not isolate a distinct capability: ablating `call_graph` while
`semantic` stays on removes only the *inferred* half of one edge family, which is a confidence-
threshold question (`min_confidence`, already a query parameter) rather than a capability question.
The depth axis in stage E2 is the correct place for that trade-off.

Consequence: `ablation(call_graph)` is not an available arm. Ablating `semantic` covers it. This is
recorded in the master plan section 6 so no later stage schedules a `call_graph` arm.

### Decision 2 — configuring an unimplemented capability is a `ConfigError`, not a diagnostic

`cfg`, `data_flow`, `state_event`, `side_effects`, `api_schema_db`, `ui_graph` and `memory` are listed
in `NOT_IMPLEMENTED_CAPABILITIES`. `CapabilityPolicy` forces them to `off` regardless of
configuration, and the resolver rejects any non-`off` value for them at resolve time.

Reason: a warning-level diagnostic was rejected because `ResolvedConfig` has no diagnostic channel —
adding one would mean either logging from host-neutral core (which nothing else does) or growing the
resolved-config contract for a case that should not occur. More importantly, the failure mode a
diagnostic permits is exactly the one Phase 0 exists to remove: an evaluation arm configured with
`ui_graph: active` would record results under a label describing a capability that never ran, and the
resulting keep/demote decision would be unfalsifiable. Invariant 1 (evidence policy) and invariant 4
(truthful degradation) both require the loud failure. Configuration is resolved once at startup, so
failing closed costs one clear error at the earliest possible point.

The shipped default sets every capability to `off`, so no existing configuration is affected.

### Mechanism

No new gating mechanism was introduced. `CapabilityUnavailable` and `require_explicit_use` moved to
`core/policy.py` so `service/application.py` (`_require_explicit`, `_explicit_snapshot`),
`strategy/service.py` and `testing/service.py` share one gate. `build_strategy` and
`evaluate_test_health` take a required keyword-only `policy`. `test_obsolescence` is gated separately
from `test_selection`: with it off, `pi_tests` still selects tests and returns `health: []`.

`pi_status` now reports `name`, `implementation`, `mode` and `governed_by` for all 21 capabilities,
typed as `PiStatus`/`CapabilityStatus` in the OpenCode adapter.

`tests/architecture/test_capability_gating.py` asserts by AST scan that every `CapabilityName` member
is policy-gated, folded into a gated capability, or declared unimplemented, and pins the 21/7/1/13
inventory counts so a new capability cannot be added silently.

GitHub Actions: not added. Validation stays local.

## 2026-08-16 — Plan review corrections and evaluation scope

Context: a full read-through of the consolidated plan found three residual inconsistencies that E0 was
supposed to eliminate, and four scope gaps that would have surfaced as unusable results at B0.

### Corrections

1. **Project Evidence Memory was scheduled at both P0 and P1.** §3 row 6 and this file said P1; §8 and
   the §9 legacy mapping said P0. Resolved to **P0**, matching §8/§9.
2. **`D0` denoted two different things** — capability depth level 0 (§7.1 arm G, E2, V2) and the
   Phase 5 runtime-bridge stage. In a document whose purpose was retiring ambiguous identifiers this is
   a defect. Phase 5 stages are renamed **X0** and **X1**; `D0..D4` now means depth only, and §8
   Phase 5 states the rule explicitly.
3. **B0 scheduled an ablation sweep over "the 14 implemented capabilities".** After E1 folded
   `call_graph` into `semantic` there are 14 implemented but only **13** ablatable. Corrected to 13
   with a pointer to §6. This was missed in the E1 documentation pass.

### Decision — a Layer B task suite is a stage, not part of the runner

Phase 0 gains a new stage **E3 (Layer B task suite and outcome ground truth)**; the former E3 and E4
become **E4** and **E5**.

Reason: Layer A had a versioned label set while Layer B — the layer the entire product claim rests on
— had no defined task set, no per-task oracle, and no sealed held-out split. B0 would have produced
outcome numbers that could not be compared between arms or between runs, and the fix would have
required repeating B0. Folding the suite into the runner stage was rejected because it lets the suite
be shaped by what the runner happens to make easy, which is the standard way an evaluation ends up
measuring the implementation instead of the claim. E3 seals the suite before the runner exists.

The renumbering cost is accepted because no stage past E1 has started. §9, §11, §12, the handoff
documents and `CURRENT_STATUS.md` were updated in the same commit.

The suite must include a negative-control task class expected not to benefit from PI, and at least one
task whose correct answer is "insufficient evidence", so the suite can detect PI-induced
overconfidence rather than only rewarding recall.

### Decision — Layer C budgets become numeric thresholds in the master plan

§7.4 gated promotion on "Layer C stays within budget" while §7.2 listed only metric names, and the
qualitative budgets lived in a document whose sequencing was superseded. That made the condition
unfalsifiable. §7.2 now carries a numeric table by repository size class, plus an advisory context
overhead ratio. The numbers are provisional and calibrated at B0; changing one requires a decision
entry with the measurement. A budget breach blocks promotion even when Layer A and Layer B improve —
the response is lower depth or a scoped rollout, never a raised budget.

Recorded honestly: the PR-B measurement (182.145 ms incremental vs 185.638 ms cold on 50 files) means
the S-class incremental budget is **not currently met** by the fingerprint path.

### Decision — repository content is untrusted input (new invariant 8)

The plan treated privacy as outbound-only (`RemoteCodePolicy`). Nothing addressed the inbound
direction, even though every capability reads repository text and delivers it into an agent context —
a direct injection channel. New invariant 8 requires PI output to be structured data rather than
prose, forbids repository content from changing rollout mode, depth, capability selection, privacy
policy or verification verdicts, and requires the E3 suite to contain injection-shaped strings so B0
measures propagation instead of assuming absence. Propagation is a release blocker.

### Decision — Verification Intelligence is the primary differentiation hypothesis

The competitive analysis scored Project Graph and Impact Analysis only against agent harnesses, where
they look like a 5-vs-1 advantage. That is the wrong comparison set: static code intelligence
(Sourcegraph, CodeQL, IDE indexers, LSP) has built code graphs for years with wider language coverage
and greater scale. A **CI column** is added to §3.3, and rows 22–23 are scored at parity or behind.

Consequently §2 no longer lists five co-equal moat areas — which made the strategy unfalsifiable,
since any result could be credited to some other pillar. Verification Intelligence is the single
defended area; the other four are supporting. Master plan §1 is restated to match, and now also states
the Python/JS-TS language boundary explicitly.

### Decision — program-level stop and pivot criteria (new §10.2)

Invariant 10 was a per-capability stop rule only. Nothing said what happens if B0 disproves the
premise, so the default outcome was indefinite continuation. §10.2 adds two pivots (verification-only,
weak-local-only) and a three-condition stop requiring a confirming repeat run. A stop is written up as
a negative result to the same evidence standard as a positive one. Provider unavailability, a single
tier regressing, language coverage and OpenCode drift explicitly do not trigger it.

### Recorded — no existing evidence supports the product thesis

`docs/evidence/pr-g/model-evaluation.json` is 6 scenarios, 1 repetition, `tool_calls = 0` in every arm.
Zero tool calls means no agentic work occurred; it is a context-injection A/B, and 1/6 → 6/6 is close
to tautological when the needed facts are placed in the prompt. Under invariant 1 it is real evidence
that the model-routing path functions, and nothing more. §5 now states this, and no claim may cite it
as outcome evidence.

GitHub Actions: not added. This change is documentation only.

## 2026-08-16 — External review follow-ups and stale-document cleanup

Context: an external review of the consolidated plan raised six points. Its first and highest-priority
finding — that E1 and the plan corrections had not reached `main` — was correct when written and is
now resolved: `main` is `86a6a37`, whose tree is byte-identical to the verified branch. The stacked
PRs #34 and #35 had merged into their intermediate base branches instead of `main`, because GitHub
retargets a stacked PR only when its base branch is **deleted**. PR #36 merged the full content
forward. The remaining five points are accepted and applied here.

### Accepted — Existing Project Bootstrap becomes a B0 entry condition

`TEST_PORTFOLIO_INTELLIGENCE_AND_BROAD_EVALUATION_PLAN.md` treats existing-project bootstrap as a
first-class lifecycle, but no stage asserted it, so the ability to bring an unseen repository to a
usable baseline was never going to be evaluated. Added as a **B0 entry condition** rather than a new
stage, because it is a precondition for trustworthy arm results, not a work package: a repository whose
baseline silently failed would attribute a bootstrap failure to a capability. Per repository B0 now
records workspace/project identity, initial Twin revision, test-runner discovery, test inventory,
baseline evidence classified `observed`/`inferred`/`unknown`, and explicit degradation of unsupported
analysis. Imported baselines are never `verified`.

### Accepted — E3 must include a cross-boundary GUI/runtime causal task class

The E3 task classes covered symbol, impact, test selection, refactor, bug localization, traceability
and negative controls, but nothing crossing a UI/runtime boundary — despite `AGENTS.md` requiring GUI
verification to prove user-visible outcomes, and despite stage X0's entry condition being "repeated
measured failures at a real user-visible boundary". That condition was unsatisfiable and unrefutable
without such a task.

Added as a mandatory class, framed explicitly as a **measurement of how far current PI follows the
chain**, with a low score an expected and reportable outcome. `ui_graph` stays `not_implemented`;
nothing here authorizes building it. This keeps "GUI matters" and "do not build a large UI graph before
measuring" simultaneously true, and it produces the evidence that decides X0 and V5.

### Accepted — the V-series needs internal ablation handles (`VerificationFeature`)

E1 made the 13 top-level capabilities ablatable, but V2–V5 each add several independent mechanisms
beneath a single capability. Without handles, "Environment Matrix helped, Certificate did not" is
unanswerable, and the exact problem E1 solved recurs one level down: mechanisms that can be built but
never demoted.

V0 now also defines `VerificationFeature` (`required_set`, `evidence_reuse`, `failure_reevaluation`,
`oracle_assessment`, `test_intent`, `observability`, `environment_selection`, `certificate`), each with
its own depth on the same `D0..D4` axis. Deliberately **not** new `CapabilityName` members — the
top-level inventory stays at 21 with its counts pinned by the E1 architecture test, and the feature
policy nests under the capability that owns it. E5's trace shape is widened now to accept
`used_features` so the format does not change mid-programme. V0's exit gains a feature-policy test of
the same shape as the E1 one.

This is invariant 6 applied one level down: a mechanism that cannot be switched off cannot be shown to
be worth its cost, and therefore stays by default.

### Accepted — OMO coexistence smoke moves to B0/R0; full benchmark stays P4

`OpenCode + OMO + ExtendCodeAgent` is a realistic user configuration. A tool-ID namespace collision or
a duplicated observation there is a defect that ships regardless of how the P4 comparison turns out,
and deferring all OMO contact to P4 means discovering it after release. §10.1 gains blocking item 17
(plugin load with both present, `pi_*` and OMO tool visibility, no namespace collision, no duplicate
execution, sidecar failure isolation, clean shutdown), with `UNAVAILABLE` recorded rather than passed
if OMO is not installable at the pinned OpenCode version. The full A/B, Team Mode, hook order, context
overhead, model-routing conflict and worktree behavior stay at P4.

### Accepted — "moat" is downgraded to "primary differentiation hypothesis"

The review caught a contradiction introduced by the previous pass: §5 states that no evidence supports
the product thesis, while §1 and competitive analysis §2 asserted Verification Intelligence **is** the
moat. Both cannot hold. Since the §3 scores are explicitly planning heuristics, the honest form is a
hypothesis, promoted to "moat" only when B0 measures it against native OpenCode and against the tooling
a developer would otherwise use. Wording aligned in master plan §1, competitive analysis §2 and §3.3.

### Clarified — invariant 8 does not forbid explanations

"PI output is data, never instruction" risked being implemented as "return no prose", which would break
a product requirement: an impact result without a reason is not usable evidence. Invariant 8 now
distinguishes three kinds of text — repository-origin (quoted, untrusted, attributed), PI-generated
explanation (analysis with provenance, required), and control instruction (trusted configuration and
deterministic analysis only) — and forbids promotion from the first row into the others.

### Cleanup

- **Deleted** `docs/handoff/CODEX_OMO_COMPATIBILITY_INSTRUCTION.md`. It declared a fourth read order
  and directed agents to "follow the current RV/RA/TA/VI/WL/EM roadmap" — the legacy identifiers §9
  forbids for scheduling. It survived E0 because it sits under `handoff/` rather than `docs/`. Its OMO
  substance is retained in the registered `OMO_COEXISTENCE_AND_COMPATIBILITY_PLAN.md`.
- Read-order sections removed from `CODEX_IMPLEMENTATION_GUIDE.md` §2 and
  `CODEX_PRODUCTIZATION_EXECUTION_GUIDE.md` §1 per maintenance rule 5; their working rules are kept.
- `CODEX_PRODUCTIZATION_EXECUTION_GUIDE.md` §4 retitled from "First task" to B0 detail. Its content
  (environment capture list, integration checklist) is what B0 executes and is kept in full.
- All 36 merged remote branches deleted; only `main` remains.

**Not deleted:** every planning document registered in §2, including `KASANECORE_MIGRATION_AUDIT.md`.
§2 assigns each a live disposition as design detail; deleting them would discard the detail the
consolidation deliberately preserved. Superseded *sequencing* inside them is already marked by banners.

GitHub Actions: not added. This change is documentation only.

## 2026-08-16 — Feasibility, OMO restoration and hypothesis ordering

Context: a review of the plan against the stated product intent — OpenCode plus KasaneCore-derived
Project Intelligence plus OMO, used together — found that the intended production configuration was
absent from the backlog, that the baseline was not executable as specified, and that the designated
differentiation was scheduled after everything it is supposed to differentiate from.

### Restored — `OMO-C0` as stage B2

The E0 consolidation recorded `OMO_COEXISTENCE_AND_COMPATIBILITY_PLAN.md` as "executed only at stage
P4". That document's §9 defines `OMO-C0 Coexistence Baseline` as required **before any claim that
OMO + ECA is a recommended stack**, so the consolidation dropped a scheduled gate rather than mapping
it. Since `OpenCode + OMO + ExtendCodeAgent` is an intended production configuration, deferring all
coexistence work to a post-release benchmark means the recommended-stack claim could never be
supported at release.

`OMO-C0` returns as stage **B2** (conditional, after B0): version tuple, Team Mode off, startup/tool/
session/coding/verification compatibility, both plugin load orders, conflicts classified against the
C0–C6 taxonomy, resolved under the §11 stop rules. `OMO-C1` becomes the P3 entry condition. §2's
disposition now names the live parts of that document instead of retiring it wholesale. B2 asks "does
the stack work"; P4 still asks "is the stack better".

### Decision — B0 splits into B0a screening and B0b confirmation (new §7.5)

The arm set multiplied out is 23 arms x 14 tier-repetitions x tasks = 322 runs per task; 20 tasks is
6,440 agent runs, roughly 320 hours of continuous execution at three minutes each, before B0's
environment freeze, bootstrap conformance, integration revalidation, OMO smoke and GUI measurement.
The repetition minimums say how many times to repeat a cell but never which cells to skip, so the
specification had no way to terminate.

§7.5 adds a screening/confirmation design. Screening runs each ablation at one assigned tier over a
fixed tuning subset and can neither promote nor demote; confirmation runs full tiers, repetitions and
held-out only for what screened through, and §7.4 decisions may cite confirmation only. The subset,
threshold and tier assignment are fixed before the first run so the sample cannot be tuned toward a
result; a screened-out capability is recorded `no screened effect` rather than `rejected`, because
screening is under-powered by construction; anything within noise of the threshold goes to
confirmation anyway; and `native`/`off` always run at full power because every other number is read
against them.

This is a sampling design. Evidence standards are unchanged.

### Decision — a V0 slice moves into Phase 0 as `V0a`

§1 designates Verification Intelligence the primary differentiation hypothesis, but the V-series sat
in Phase 3 — after Phase 0, B0 and Phase 2. Everything implemented so far is Project Truth, which §1
concedes is at parity with mature code intelligence. The baseline would therefore have measured only
the conceded part, and §10.2's verification-only pivot would have had nothing to pivot to.

`V0a` (shadow, evaluation-only) defines `SemanticChangeSet`, `VerificationObligation` and
required-verification-set derivation, and nothing else; reuse, failure taxonomy, oracle assessment and
certificates stay in V0/V2–V5. V0 becomes the remainder and must extend those objects rather than
redefine them.

Named `V0a` rather than inserted as an E-stage on purpose: the E-series was renumbered once already
this week, and a second renumber would cost more than one irregular identifier. The name also states
what it is — a slice of V0, not new evaluation infrastructure.

### Accepted — E3 gains an `OMO + ECA @ local-low` arm

The intended production configuration is also the worst case for context budget: both extensions
inject into one window and `local-low` has the least room. `pr-g` shows ECA alone taking `local-low`
input from 236 to 840 tokens — an overhead ratio near 2.6 against the §7.2 weak-local budget of 0.5.
Those were trivial scenarios and real tasks will differ, but the direction is the concern and OMO can
only compress the window further. Conflict class C2 is measured here or nowhere before release.

### Accepted — E2 binds the inferred-relation confidence threshold to depth

E1 folded `call_graph` into `semantic` on the reasoning that `may_call` stays in the graph and is
controlled at use time by confidence and depth rather than at production time by a gate. That control
point did not exist. E2 now defines a minimum inferred-relation confidence per depth, so `D1` excludes
`may_call` at 0.35 while `D3` admits it. Without it the folding decision was half implemented.

### Accepted — slow-suite repository pinned; target project profile stated

Selective verification only pays when running everything is expensive. On a thirty-second suite,
"run it all" is faster, simpler and more certain, and correctly beats this product. The pinned corpus
(flask, httpx, express, vite) is fast-testing, so the plan would have measured the differentiation
hypothesis under the conditions where it cannot win. §7.3 adds a required repository whose full suite
exceeds ten minutes and records full-suite wall time for every corpus entry; §1 states the target
profile and says plainly that outside it, native OpenCode plus a fast test command is the better
answer.

### Recorded — execution capacity, review cost, unbuilt differentiator, KasaneCore reuse

Four risk rows added to §12. The KasaneCore row matters for estimation: the audit records 80-90%
algorithmic reuse but only 25-40% direct source reuse, and `src/` contains no KasaneCore-derived
module — all 7,835 lines were written fresh against KasaneCore's design lessons. Remaining work must
be estimated at scratch-implementation rates, not as inherited.

GitHub Actions: not added. This change is documentation only.

## 2026-08-16 — E2 capability depth contract

Decision: execution depth is a second centralized axis (`D0..D4`) with global profiles and
per-capability min/max/preferred/auto bounds. It is resolved independently of rollout authority;
`auto` is deterministic balanced behavior until C3 adds task-aware selection. Folded `call_graph`
inherits `semantic`'s depth as well as its rollout owner.

The confidence floor associated with depth applies only to inferred relations. The existing caller
`min_confidence` remains a floor for every fact; depth adds a separate
`min_inferred_confidence`. This prevents shallow depth from discarding lower-confidence declared
facts while still making the E1 `call_graph` decision real: D1 excludes confidence-0.35 `may_call`
and D3 admits it. Filtering occurs at query/use time, so stored Twin revisions do not depend on
configuration.

Every public PI response records the answering capability depth. `pi_status` has no single answering
capability and therefore reports top-level `depth: null` plus the resolved depth and inferred floor
for every capability entry. The shipped balanced/D2 default has a 0.3 inferred floor, below the
minimum 0.35 currently emitted by analyzers, so default query behavior is unchanged.

Validation: `tools/local/all-fast` PASS (171 Python, 9 adapter),
`tools/local/test-integration` PASS (16 Python, 9 adapter), and `tools/local/build` PASS (Python
sdist/wheel and TypeScript build). GitHub Actions were not added.

## 2026-08-16 — V0a immutable verification projections

Decision: V0a is a pure, host-neutral projection over existing Twin/Graph/Impact truth. It introduces
no verification database or adapter behavior. `SemanticChangeSet` compares base and candidate Twin
snapshots and retains entity/relation provenance. A changed file whose symbol shell is unchanged is
represented as an inferred symbol change at confidence 0.5; unknown body impact is not silently
treated as unchanged.

`VerificationObligation` remains `uncovered` until executed evidence exists. The initial required set
accepts graph-linked tests only for local/test-intent/consumer obligations and leaves side-effect and
uncertainty obligations visibly uncovered. V0a does not reuse old runtime evidence; V3 owns reuse.
Selection quality is measurable as exact provider IDs plus TP/FP/FN, precision and recall.

Architecture tests reject storage/SQLite/OpenCode/filesystem dependencies in this slice. Final gates:
all-fast PASS (178 Python, 9 adapter), integration PASS (17 Python, 9 adapter), build PASS.

## 2026-08-16 — User-mandated evaluation model routes

The evaluation environment uses OpenCode launched through ControlDeck's existing path where
available; this does not make ControlDeck a separate ECA runtime. `local-practical` uses the existing
Llama-compatible Qwen3.6 27B service on port 8090 and waits for wake-up. Ollama or substitute model
servers must not be started. Frontier evaluation uses two mandatory OpenCode arms, Sonnet and Codex,
both through the registered GitHub Copilot provider. E3 seals exact installed identifiers; domain code
must not hard-code them.

## 2026-08-16 — E3 sealed Layer B suite and corpus-candidate boundary

Decision: E3 v1 contains 13 objective tasks over pinned ExtendCodeAgent, ControlDeck and held-out
KasaneCore revisions. PEDS is pinned only for the measured slow-suite condition. OpenCode, Hermes
Agent and Atomic Agents are recorded as next-version candidates, while the Rust Codex repository is
reference-only until Rust analysis exists and is measured. Popularity is contextual evidence, not a
promotion criterion, and the candidate registry cannot mutate the sealed v1 split.

The native proof uses ControlDeck-managed OpenCode 1.18.16 in pure mode with `opencode/big-pickle`.
Its 4 PASS / 9 FAIL result is retained without manual upgrades: exact output-type, path-granularity
and terminal-symbol misses are objective failures. The 30.77% rate satisfies the non-triviality
condition without tuning against the held-out outcomes.

The slow-suite pin is PEDS `c607943367da648f1598f957ece314b29d2fc683`. A clean lockfile setup
passed the normal gate in 435 seconds and Playwright in 321 seconds, totaling 756 seconds. KasaneCore
was rejected for unreproducible generated-asset dependencies; a newer PEDS pin was rejected because
its remote revision was not green. Contaminated shared dependencies are never accepted as pin
evidence.

OMO 4.19.4 plus ECA model-free coexistence passed in an ephemeral profile. The absent permitted
weak-local endpoint keeps the required local-low model arm UNAVAILABLE. Installer isolation and
generic raw tool-ID overlap are recorded for later B2 assessment rather than being hidden or called
compatible.

## 2026-08-16 — E4 unified matrix, promoted labels and resumability

Decision: the canonical evaluation entry point is `tools/local/evaluation-runner`. Its matrix binds
the exact Layer A and Layer B seals, pinned quality corpus, integrated metric contract, ControlDeck
OpenCode executable, port-8090 local-practical route and both GitHub Copilot frontier IDs. Local-low
UNAVAILABLE cells remain in the schedule so absence cannot improve apparent completion.

The full Cartesian schedule has 5,083 cells and is deliberately not executed as an E4 proof. The
master plan requires screening before confirmation; E4 proves the route and runner, while B0 owns
repeated outcome distributions. Bounded `--arm`, `--model-tier`, `--task` and `--max-cells` slices are
diagnostic only. Atomic per-cell checkpoints plus `--resume` are mandatory; incomplete workspaces are
archived rather than reused or deleted.

The Layer A label set promotes 12 existing manually reviewed PR-C/PR-H cases, adding no new unsized
human review. Historical per-PR scripts remain reproducibility artifacts but are retired as current
entry points. Missing integrated metrics are emitted as `NOT_TESTED`, never zero or pass.

## 2026-08-16 — E5 trace integrity and observation provenance

Decision: E5 uses a compact evaluation-only record and append-only hash-chained JSONL rather than
promoting the later P0 Project Evidence Memory. Append is idempotent for an identical trace ID and
fails closed for conflicting content; replay validates sequence, prior hash, record hash and unique
IDs. Prompts, transcripts, messages and secret-shaped fields are forbidden.

The trace distinguishes `planned_matrix` capability state from `observed_pi_status`. A scheduled arm
whose model route is unavailable still needs a trace for matrix coverage and attribution, but its
configuration is not runtime evidence. Tool-returned evidence identifiers, Twin revisions and PI
timings are recorded only when observed. Empty lists/nulls remain truthful rather than being filled
from expectation.

The 115-cell local-low run demonstrates trace coverage and semantic-ablation attribution only; all
cells are `UNAVAILABLE`. The real host advisory cell demonstrates observed capability-state capture
but failed its objective oracle. Neither result supports a Project Intelligence benefit claim; B0
owns repeated outcome distributions.

## 2026-08-16 — B0a screening contract and bootstrap exclusion rule

Decision: B0a has its own sealed pre-run contract referencing, not modifying, the E4 matrix and E3
suite seals. The seven existing tuning tasks are screened as paired active/ablation cells. A
capability proceeds when active gains at least two objective PASS outcomes (minimum absolute delta
2/21) or an ablation introduces a critical completion/unsafe-claim
failure absent from active. This threshold selects B0b candidates only and cannot promote, demote or
reject a capability.

All 13 ablations use local-practical for the wide screen. This keeps the screen schedulable and tests
the bounded-evidence claim against the user-mandated port-8090 Qwen route; it does not remove mandatory
Sonnet/Codex GitHub Copilot arms from the full native/off baselines or later confirmation.

Every repository from the task suite and quality corpus must first reach an exact pinned initial Twin.
Pin/Twin failures exclude it as a bootstrap gap. Test-runner or inventory absence is instead recorded
as `unavailable`, and imported correctness remains `unknown`; neither is silently converted to PASS.

## 2026-08-16 — B0a bootstrap timeout and repair boundary

Decision: initial Twin construction is isolated per repository with a 300-second checkpoint timeout
for this B0a environment. A timeout is `EXCLUDED_BOOTSTRAP_GAP`, not an unavailable model result and
not a zero-quality capability score. Included repositories may enter B0a screening; KasaneCore-held-out
confirmation cannot start while its bootstrap gap remains.

The observed SQLite edge-supersession scaling path is not patched inside this evidence checkpoint.
B0a must first preserve exact repository results and classify the gap. If it blocks B0 completion,
the conditional B1 repair stage owns the minimal indexed-store correction and exact remeasurement.
One cold run is diagnostic; budget calibration still requires the master-plan repetition count.

## 2026-08-16 — B0a depth attribution and executable schedule boundary

Decision: B0a has separate executable scopes for the full-tier `native`/`off` baseline and the
local-practical screen. Both consume the sealed B0a contract and bootstrap eligibility at runtime;
an excluded repository cannot be reintroduced by a command-line selection.

Depth screening changes one claimed capability at a time. The four depth-dependent claims
(`semantic`, `impact`, `test_selection`, `context`) each receive D0-D4 arms while every other
capability stays at D2. A global all-capability depth change is not acceptable B0a attribution.
Depth cells do not enter the active-versus-ablation effect threshold; they are retained for the
separate depth-dependent claim analysis.

## 2026-08-16 — B1 current-edge index is a blocking repair

Decision: the missing current-edge identity index is confirmed as the B0 bootstrap blocker and is
repaired before B0a screening. The repair adds only the index used by the existing supersession
UPDATE and a schema-4-to-5 migration; it does not alter graph facts, capability behavior or task
oracles. This keeps the ongoing native/off baseline attributable to its sealed head while ensuring
PI-enabled screening does not measure avoidable quadratic storage work.

Three fresh exact-pin runs, rather than the first successful diagnostic, are the acceptance evidence.
KasaneCore and PEDS now pass their size-class cold-index budgets and may enter held-out confirmation.
The original timeout record remains immutable and is superseded, not rewritten.

## 2026-08-16 — B0a requires observed PI activation before comprehensive evaluation

Decision: a separately sealed exact-head activation gate precedes the long native/off baseline and
active/ablation screen. Each permitted available model route must actually call `pi_status` and a
task-bearing PI tool and expose observed modes/depths, ready Twin revision, canonical evidence and
positive PI time. Visibility of tool names or planned capability state is insufficient.

The first 137 baseline cells remain diagnostic history because they used the old protocol and pure
OpenCode `native` never exercised PI. They are not resumed into the final comparison. Corrected
baseline and screening evidence must start from zero at the same implementation head as the passing
activation report.

The activation contract also fails closed on capability reachability. `blueprint`, `convergence`,
`traceability` and `strategy` are implemented in core but currently have no OpenCode tool/task path;
running their ablations would measure non-execution and could falsely report no effect. This is a B1
adapter/productization gap to repair before the 714-cell screen, not a reason to weaken the screen.

Activation alone is not a reason to spend the full matrix. The port-8090 pilot first interleaves one
repetition of `native`, installed-but-off and active over three representative tasks (9 cells). Only
a passing initial signal continues to the three-repetition confirmation (27 total). Active
must show an objective PASS gain over the better control, every PI-enabled/disabled observation must
match its contract, provider errors/timeouts are forbidden, and active median wall time must stay
within 2x of the slower control. Any failure produces `REPAIR_AND_RETEST`; the pilot is rerun at the
repaired exact head before comprehensive evaluation.

Evaluation cells expose one canonical `pi_*` namespace through the OpenCode plugin and one sidecar.
The same tools are not simultaneously registered through MCP: the first staged off cell selected the
duplicate qualified MCP name and hit an OpenCode result-shape error instead of observing disabled
state. MCP conformance remains covered by its dedicated lifecycle tests rather than a duplicate live
route inside causal cells.

Evaluation agent shells must not inherit the runner's editable environment. The runner removes its
`.venv/bin`, `VIRTUAL_ENV` and root `PYTHONPATH` before launching OpenCode and requires pip to have an
isolated virtualenv. The ECA sidecar still receives its explicit interpreter. This prevents a model
task from changing later cells by retargeting the shared runner installation.

Resume is exact-head only. The runner rejects a checkpoint whose source revision, sealed schedule,
activation/pilot evidence or trace path differs, and rejects non-resume execution into an existing
report/trace. Old-protocol cells cannot be combined with corrected evaluation by operator mistake.

## 2026-08-16 — B1 effect repair is projection-first and measurement-gated

Decision: the initial 9-cell active gain permits diagnosis but the 300,157ms confirmation timeout
forbids continuing the 27/306/714 schedules. Preserve the sealed tasks and exact oracles. Before
changing graph depth, classify failures as retrieval missing, projection/schema error or agent
reasoning error, with required-fact recall, schema validity and final exact pass retained separately.

Every PI cell must split cold Twin build, snapshot load, adjacency/index build, query execution,
JSON serialization and post-PI agent/model residual from the first PI result after subtracting later
tool execution. Optimize the observed boundary rather
than attributing total wall time to PI. The implementation priority is compact task-shaped projection,
obligation-aware structural test coverage, revision-scoped query indexes/cache, missing OpenCode
routes, then a fresh sealed 9-cell pilot. CFG/DFG expansion and comprehensive evaluation do not
precede this repair.

## 2026-08-16 — Missing capabilities use two composite, fail-closed OpenCode routes

Decision: expose `pi_plan` for Blueprint plus Strategy and `pi_verify` for Traceability plus
Convergence. Do not add one tool per internal capability. Each result names the capabilities actually
used so evaluation can attribute composite execution independently of the public tool name.

`pi_plan` uses graph-derived bounded alternatives and deterministic Strategy scoring. It returns a
Blueprint-shaped draft by default and persists only when explicitly requested. `pi_verify` evaluates
requirements against current Twin facts but accepts no fabricated evidence; an existing fact that
still requires verification remains materialized and unresolved.

The existing sealed task/oracle truth is unchanged. The activation contract instead assigns
`eca-refactor-001` to `pi_plan` and `cd-cross-boundary-001` to `pi_verify`. Relevant active and
ablation cells must attempt those tools, and the screen reports `NOT_TESTED_ROUTE_GAP` rather than
`no_screened_effect` when active capability use or required tool attempts are absent.

## 2026-08-16 — OpenCode exposes task projections, not a detail-view choice

Decision: retain `detail` for direct application compatibility, but remove it from the OpenCode
plugin/MCP schemas for symbol, impact and test selection. The real Qwen pilot explicitly chose
`detail` despite compact defaults, so defaults did not test the intended projection and one impact
payload was truncated. Public agent tools must make the safe task-shaped path the only path.

Test selection requires a natural-language objective and accepts canonical refs only as optional
additional evidence. It deterministically ranks existing test intent per unit, integration and
architecture obligation, returns one best path per required class, and leaves uncovered obligations
explicit. This is a bounded projection repair, not a claim of generic semantic TestIntent coverage.

Requested answer keys are interpreted as an exact schema in every evaluation arm because the sealed
oracle performs exact equality while the natural-language tasks previously allowed models to append
explanation objects. Active PI receives one additional causal rule: matching compact fields are known
facts to preserve, not suggestions to delete or enrich. This does not change task facts or weaken the
oracle; it removes a presentation ambiguity equally for controls and tests PI's intended projection.

Activation continues to require canonical URI evidence. Effect-pilot cells may additionally satisfy
selected-evidence observation with repository-relative paths emitted in compact path/test fields.
These are the task-ready evidence used by `pi_tests`; treating them as absent caused a false PI-use
failure even when the exact PI output and final answer matched. This exception is limited to the
pilot assessment and does not weaken the four-model activation contract.

The local-practical OpenCode provider is sealed to an 8,192-token output limit for every arm. A
confirmation off-control generated 27,998 tokens in its first response and hit the 420-second task
timeout before any tool event, so this is a model runaway boundary rather than PI latency. The cap is
arm-neutral, remains well above ordinary observed outputs, and changes the matrix seal; old runs are
diagnostic only and a fresh activation/pilot is mandatory.
OpenCode custom-model runtime validation requires both `limit.context` and `limit.output`; debug
config rendering alone is insufficient proof. The context value is sealed to 262,144 to match the
actual ControlDeck llama.cpp `--ctx-size`, and real `opencode run` is required before activation.

The sealed 27-cell gate is now the adoption boundary evidence for entering comprehensive evaluation:
active gained six exact PASS over controls, every active cell observed required PI, and no timeout
occurred. This authorizes—not completes—the current 162-cell baseline and 714-cell screening
schedules. The historical schedule at the time of the pilot contained 306 baseline cells.
Residual symbol/test variance remains visible in task-level metrics and is not treated as resolved.

## 2026-08-17 — Evaluation checkpoints migrate only through compatibility and Bridge proof

Decision: a runner-only repair no longer forces unconditional deletion of every prior cell, but
`--resume` across revisions remains forbidden. A sealed Compatibility Manifest proves unchanged
core/adapter/task/oracle/repository/model semantics. `audit-checkpoint` classifies every source cell;
only complete, trace-valid, provider-clean cells are functional reuse candidates. Their latency is
kept as `LEGACY_RUNNER_LATENCY` and is not mixed with current-run timing.

Migration remains blocked until a sealed 10–20-cell Bridge Sample covers local-practical,
host-default, Copilot Sonnet and Copilot Codex plus symbol/impact/test classes. A mismatch expands
`REPLAY_REQUIRED` to the related model/task class. Migration copies results with source hashes and
provenance; it never edits the source checkpoint. Provider pause/resume and availability probes are
evaluation-runner concerns, not ECA core behavior.

## 2026-08-17 — B0a quality evaluation has exactly three model routes

Decision: B0a quality outcomes cover only ControlDeck-managed `local-practical` Qwen and GitHub
Copilot Sonnet/Codex. `host-default` is an opaque OpenCode convenience alias and `local-low` is
unavailable; neither belongs in the quality denominator. The `native`/`off` baseline is therefore
3 models x 9 tasks x 2 arms x 3 repetitions = 162 cells.

Provider capacity remains orthogonal to quality. The GitHub Copilot monthly quota is shared: fresh
Sonnet and Codex probes can both be unavailable even though only Codex has unfinished baseline
cells. Affected executions move to provider attempts, each route pauses independently, and cells
remain pending until an availability probe succeeds. They cannot be converted into FAIL/PASS or
substituted with `host-default`.

Screening order is enforced rather than documented convention: `b0a-screening` requires a sealed,
exact-head `--baseline-report` containing all 162 scheduled cells and one valid trace per result.
Provider-gap quality results, incomplete cells, changed provenance or a stale head reject screening
before any workspace or model call is created.

## 2026-08-17 — Execute the existing Master Plan local-only

Decision: preserve the existing plan, stage order, entry/exit conditions, task suite, oracles,
thresholds, corpus, capability design and historical evidence. Change only model execution selection
through sealed `b0a-quality-target-v2.json`: ControlDeck-managed Qwen3.6 27B at port 8090 is mandatory;
Sonnet/Codex and host-default receive no new calls; local-low remains unavailable.

The B0a denominator is 54 cells and the exhaustive screen has a 714-cell hard maximum. Existing Qwen 54/54 is not
discarded or rerun by default: the existing compatibility audit, Bridge Proof and checkpoint migration
must prove task/oracle/model-limit/ECA-semantic compatibility, and only residual invalid cells replay.
Local evidence can promote at most `active-scoped(local-practical)` and cannot support a frontier,
host-default, local-low or general-model claim.

R0 closes first as a production-capable local-only baseline under the single Master Plan §10.4
exception. P0-P4 then follow their existing entry conditions and use the same Qwen route for any
model-bearing evaluation. Unavailable or policy-excluded tiers are never passes, and prior Copilot
results remain historical/supplementary evidence without deletion or reclassification.

## 2026-08-17 — ECA development and evaluation use Minimum Sufficient Reasoning

Decision: ECA product runtime, development and evaluation all follow Minimum Sufficient Reasoning.
The LLM is used only for the unresolved reasoning that remains after deterministic analysis and
compatible evidence reuse; correctness obligations still expand/escalate when evidence is missing,
stale, contradictory or unknown.

Reason: ECA's value hypothesis is that Project Intelligence reduces the problem scope, context,
verification scope and call count presented to an LLM. Keeping ECA's own evaluation as a fixed
exhaustive, over-broad model workload would contradict that product hypothesis and obscure an
important efficiency effect.

Consequence: exhaustive evaluation is the hard-maximum fallback. Deterministic preflight,
active-use relevance filtering, depth-output equivalence, sequential stopping and compatible result
reuse run first. Skips retain machine-readable states and never become PASS or `no_screened_effect`;
independent repetitions required by an evaluation contract remain valid evidence work.

## 2026-08-17 — Capability efficacy and Capability selection are independent evaluation axes

Decision: Capability efficacy and Capability selection are independent evaluation axes. Core
`RolloutMode.ACTIVE` continues to mean authority, not mandatory tool use. Evaluation uses a sealed
expected EvaluationPIPlan and separate `auto_pi`, `forced_pi`, `forced_off`, and
`forced_ablation:X` policies. Causal ON/OFF/ablation comparisons hold task, model, prompt and exact PI
request plan constant; required tool order/input is verified fail-closed from the trace.

Reason: the current B0a screen used the active agent's self-selected `pi_*` trace for relevance, which
mixes whether a capability helps with whether the agent selected it. In particular,
`NOT_TESTED_NO_ACTIVE_USE` describes an unexercised route and is not negative capability-efficacy
evidence. An expected capability omitted by auto-use is a `PI_SELECTION_GAP`, not a capability failure.

Consequence: the completed B0a result remains immutable observational / agent-selection-weighted
screening and scheduler call-avoidance evidence. Its six candidates remain; selection bias alone
cannot exclude other capabilities. Before B0b, a tens-of-calls corrective screen evaluates only
representative relevant task/capability pairs, marks absent task coverage explicitly, and escalates
only causal boundaries. C1/C3 compare their planner against the EvaluationPIPlan as expected-plan
ground truth; the plan itself is not a production planner.
