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

### Decision — the moat is Verification Intelligence; Project Truth is substrate

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
