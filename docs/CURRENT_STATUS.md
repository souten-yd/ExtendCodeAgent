# ExtendCodeAgent — Current Status

Status date: 2026-08-16

## Program state

Overall: **A-I COMPLETE — PHASE 0 COMPLETE — E0-E5 AND V0a COMPLETE — B0a IN PROGRESS**

PRs A-I are merged and the implementation baseline is complete. Planning PRs
[#20](https://github.com/souten-yd/ExtendCodeAgent/pull/20) and
[#21](https://github.com/souten-yd/ExtendCodeAgent/pull/21) are also merged. All planning documents
have since been consolidated into a single canonical execution plan,
`docs/PI_MASTER_EXECUTION_PLAN.md`, which replaced eight parallel stage-numbering schemes with one
backlog.

This is not a production-capable designation. Phase 0 now provides the verification contract slice,
sealed task suite, unified evaluation runner/labels and attributable PI trace. Baseline release
validation (stage B0, formerly RV-0) is next; it must first establish Existing Project Bootstrap
conformance and then run the schedulable B0a screening/B0b confirmation split.

## Canonical read order

1. `docs/PI_MASTER_EXECUTION_PLAN.md` — the single execution plan
2. `docs/handoff/NEXT_TASK.md` — the active stage
3. this file — program state and evidence ledger
4. the design detail registered in master plan section 2, for the active stage only

Legacy stage identifiers (`RV-x`, `TA-x`, `AL-x`, `CV-x`, `TP-x`, `VI-Xx`, `RA-x`, `EM-0`, `MA-0`) are
mapped in master plan section 9 and must not be used to schedule work.

## Accepted architectural baseline

- OpenCode remains the agent runtime; ExtendCodeAgent is a host-independent Project Intelligence layer.
- OpenCode-specific APIs remain behind replaceable adapters.
- KasaneCore is a behavioral/reference source, not a directory-copy dependency.
- Reuse/adaptation is preferred over parallel reimplementation.
- Project Graph/Digital Twin/Impact are the first functional foundation.
- Major capabilities are independently configurable and support off/shadow/advisory/active rollout.
- Low-performance local LLMs, practical local coding models, OpenCode host/default models, and frontier models are all first-class targets.
- Model calls use role-based routing and provider-independent adapters; exact model names are configuration, not domain constants.
- Routing supports local-first/frontier-first/host-only/local-only and adaptive/cost/latency/quality policies with explainable escalation/fallback.
- Weak local models receive smaller structured evidence and deterministic candidate sets rather than large repository dumps.
- Privacy policy can forbid remote model/source-code use and remote escalation.
- Deterministic analysis is preferred before model reasoning at every model tier.
- Local tests/E2E/benchmarks are primary evidence; GitHub CI is exceptional.
- Real OpenCode and real-LLM A/B evaluation is required at milestone gates, not on every edit.

## Implementation sequence

| PR | Scope | Status |
|---|---|---|
| Planning PR | architecture, migration audit, implementation/validation/model-routing plan | complete |
| PR-A | foundation contracts, config/capability policy, model-router contracts, local harness | complete |
| PR-B | graph revision/store/source snapshot | complete |
| PR-C | structural/Python semantic/path/impact | complete |
| PR-D | OpenCode adapter + MCP advisory integration | complete |
| PR-E | context/test intelligence/runtime ingest | complete |
| PR-F | Blueprint + task-level Convergence | complete |
| PR-G | live model routing + Strategy | complete |
| PR-H | JS/TS/framework/deep graph expansion | complete; deeper graphs deferred by measurement |
| PR-I | Research/evidence + project-level convergence | complete |

## Capability gating state

Complete inventory as enforced by `tests/architecture/test_capability_gating.py`. Ablatable means the
capability can be set to `off` independently and the corresponding work then does not run.

| Capability | Implementation | Rollout authority | Ablatable |
|---|---|---|---|
| `graph` | implemented | own | yes |
| `twin` | implemented | own | yes |
| `semantic` | implemented | own | yes |
| `impact` | implemented | own | yes |
| `test_selection` | implemented | own | yes |
| `test_obsolescence` | implemented | own | yes |
| `context` | implemented | own | yes |
| `runtime` | implemented | own | yes |
| `blueprint` | implemented | own | yes |
| `convergence` | implemented | own | yes |
| `research` | implemented | own | yes |
| `traceability` | implemented | own | yes |
| `strategy` | implemented | own | yes |
| `call_graph` | implemented | governed by `semantic` | no — ablate `semantic` |
| `cfg` | not_implemented | forced `off` | n/a |
| `data_flow` | not_implemented | forced `off` | n/a |
| `state_event` | not_implemented | forced `off` | n/a |
| `side_effects` | not_implemented | forced `off` | n/a |
| `api_schema_db` | not_implemented | forced `off` | n/a |
| `ui_graph` | not_implemented | forced `off` | n/a |
| `memory` | not_implemented | forced `off` | n/a |

13 capabilities are independently configurable; the other 8 must stay `off` and a non-`off` value is a
`ConfigError`. `pi_status` reports `implementation`, `mode`, `depth`, inferred-relation confidence
floor and `governed_by` for all 21. Rollout authority and D0–D4 cost depth are independent; folded
`call_graph` uses `semantic`'s depth. Rationale
for the `call_graph` folding and the `ConfigError` policy: `docs/handoff/DECISIONS.md` (2026-08-16).

## Immediate next action

Phase 1, stage B0a: freeze the evaluation environment, establish Existing Project Bootstrap
conformance per repository, rerun the integration gates, fix the screening subset/effect threshold/
model-tier assignments, and execute the baseline plus screening cells. See
`docs/handoff/NEXT_TASK.md`.

The first B0a bootstrap checkpoint attempted all nine pinned repositories: seven established a Twin,
while KasaneCore and PEDS exceeded the bounded 300-second initial-Twin limit and are
`EXCLUDED_BOOTSTRAP_GAP`. Only Express and ExtendCodeAgent met their provisional cold-index budgets;
the other five completed Twins exceeded their size-class budget. PI-disabled route checks reached
port-8090 Qwen, host-default, GitHub Copilot Sonnet and GitHub Copilot Codex without provider errors;
local-low remains `UNAVAILABLE`. OMO 4.19.4 + ECA model-free namespace/tool visibility recheck passed.
This is a partial B0a checkpoint, not screening or confirmation evidence.

The post-bootstrap runner defines a 306-cell full-tier `native`/`off` baseline and a 714-cell
local-practical screen. The latter contains 294 paired active/ablation cells plus capability-specific
D0-D4 arms only for semantic, impact, test selection and context. A synthetic test proves the
two-PASS screening-table threshold. The old protocol stopped after 137/306 baseline cells; those
cells measured OpenCode model variance and are diagnostic only, not PI effect.

A review found that the long schedules had no fail-closed activation precondition. A separately
sealed four-model gate now requires observed `pi_status`, task-bearing PI tool use, active
capability/depth state, Twin revision, canonical evidence and positive PI time before comprehensive
execution. Activation is followed by a 27-cell port-8090 `native/off/active` effect pilot over three
representative tasks. No objective active gain, missing PI use, provider/timeout failure or active
median above 2x the slower control requires repair and the same pilot again. It also records a
blocking OpenCode reachability gap: `blueprint`, `convergence`,
`traceability` and `strategy` have no current tool/task route, so a 13-capability ablation sweep would
misclassify non-execution as no effect. Comprehensive evaluation stays stopped until those B1 adapter
paths and covered tasks are repaired; PI effect remains NOT TESTED.

The bootstrap blocker has a bounded B1 repair at exact head
`fcd61dff6c66324fed970ecfb1d9b19cae2aa8f7`. A matching current-edge identity index and schema-5
migration reduce exact-pin three-run cold medians to 15,825ms for KasaneCore and 6,368ms for PEDS;
both now pass their size-class budgets and are eligible for held-out work. This performance result
does not establish PI quality. The pre-activation baseline stopped at 137/306 cells on old exact
head `86e8061`; those cells are diagnostic model-variance history only and cannot be reused by the
corrected activation/pilot protocol.

E3 sealed 13 tasks across three task repositories and nine required classes at
`23bf76039ea1e95a29c31c09823f2501bd3658dea305a4e38868eb9e1e6f6632`. The ControlDeck-managed
OpenCode 1.18.16 native proof executed every task: 4 PASS, 9 FAIL, no timeout or unavailability
(30.77%). A clean pinned PEDS full suite measured 756 seconds. OMO 4.19.4 and ECA loaded together
model-free with all nine `pi_*` tools visible; the required local-low model arm remains UNAVAILABLE
because no permitted non-Ollama weak-local endpoint is registered. GitHub reference candidates are
recorded separately and do not alter the v1 split.

E4 sealed 12 promoted Layer A review cases and a 5,083-cell full schedule. The unified runner validates
every versioned input, emits every integrated metric key, archives incomplete workspaces, checkpoints
each cell atomically and resumes without duplicating results. Exact-head route proof exercised native,
advisory, port-8090 Qwen3.6 27B, GitHub Copilot Sonnet and GitHub Copilot Codex through the
ControlDeck-managed OpenCode executable. This is runner/route evidence, not a B0 quality result.

E5 added a compact hash-chained append-only trace with idempotent append, fail-closed replay,
explicit planned-versus-observed capability-state provenance, and no prompts/transcripts/secrets.
Exact-head evidence emitted 115 unique traces over all 23 arms. All local-low cells remain correctly
`UNAVAILABLE`; a real ControlDeck-managed OpenCode advisory cell recorded `pi_status`-observed state
and failed its task oracle. This closes attribution infrastructure only, not the product thesis.

No recorded evidence yet supports the product thesis. The only real-model result,
`docs/evidence/pr-g/model-evaluation.json`, is 6 scenarios at 1 repetition with `tool_calls = 0` in
every arm — a context-injection A/B rather than agent task completion. It is evidence that model
routing works, not that Project Intelligence improves outcomes. See master plan section 5; B0 replaces
it against the sealed E3 task suite.

The ControlDeck-managed OpenCode used by E3/E4 is `1.18.16`; earlier npm-stable evidence used
`1.18.18`, so B0 must report the executable actually used. The old PR-G frontier route failed 0/18,
but E4 confirmed both replacement GitHub Copilot routes are currently callable. This only removes the
route-unavailability observation; quality still requires repeated B0 distributions. No permitted
local-low endpoint is currently registered.

PR-C provides
deterministic structural/Python AST facts, analyzer-owned Python alias resolution, persisted
dependency-aware refresh, bounded path/impact traversal, weakest-link confidence, uncertainty,
explanations, and test-candidate projection. Curated FP/FN review and real-repository repeated-query
measurements are recorded under `docs/evidence/pr-c/`; PR #6 merged as `ef6db532`.

PR-A intentionally has no real OpenCode or real-LLM claim. Live host integration remains PR-D;
live model routing remains PR-G. PR-D now adds a stable OpenCode 1.18.18 TypeScript plugin, six
bounded tools, an authenticated versioned local sidecar, a shared MCP server, coalesced background
events, restart/reconnect handling, and a measured filesystem-watcher fallback isolated to the
adapter. Real model-free OpenCode evidence is recorded under `docs/evidence/pr-d/`; native/off/
shadow/advisory behavior was exercised without transmitting source to a model. PR #8 merged as
`1cc7fd26` after exact local/remote head and mergeability verification.

The local PR-A gates passed on Python 3.12.3: Ruff lint/format,
strict mypy, 25 unit/architecture tests, sdist/wheel build, and wheel-archive import smoke.

PR-B adds file-level Graph facts, immutable Twin revisions, atomic/restart-safe SQLite persistence,
historical snapshots, workspace isolation, expected-head conflicts, bounded source fingerprints,
file-level refresh/invalidation, retention and integrity-checked export/import. Semantic/Impact and
host/model integration remain deliberately absent. The recorded real-repository benchmark shows
correct incremental behavior but only a 1.9% latency advantage on a 50-file repository.

PR-C's current real-repository sample indexed 64 files into 423 nodes and 2,194 edges in
623.969 ms. A dependency-aware two-file incremental refresh took 282.761 ms. One hundred repeated
impact queries had p50 0.0649 ms; the separate lexical `rg` candidate baseline had p50 2.2538 ms.
These are latency measurements, not a claim that graph impact and lexical search have equal quality.

PR-E adds immutable runtime observations, revision-aware freshness, deterministic graph-based test
selection, evidence-based Test Obsolescence states, and bounded revision-aware context packages.
Exact-head evidence under `docs/evidence/pr-e/` records 100-item/2,131-token standard context versus
8-item/148-token weak context, two graph-linked test candidates without fallback, restart-persistent
real OpenCode tool evidence, and truthful `observed` status when stable host metadata lacks an exit
code. Live routing remains PR-G scope.

PR #10 merged as `fbdfcbd3864a3c46b76cc9ff10d77a57639258a6`. PR-F must preserve immutable
planned revisions and compare small `TargetSnapshot`, `ActualSnapshot`, and
`VerificationEvidence` projections without treating planned content as existing project facts.

The implemented PR-F slice now does so: immutable payloads are separate from lifecycle metadata,
planned and Actual namespaces are guarded, all eight task states and seven bounded decisions are
deterministic, stale/unavailable evidence cannot complete, and SQLite restart/workspace isolation
is covered. The standalone 200-element benchmark under `docs/evidence/pr-f/` measured evaluation
p50 0.2348 ms and restart 1.8938 ms. Exact-head local gates passed; publication remains.

PR #12 merged as `157fd19b56db6c61e61b5f02ab81e3bf985d79fd`. Live adapters and model-backed
Strategy remain PR-G scope and must extend the existing PR-A ModelRouter.

PR #14 merged as `3386cfa429caf5b476e8abc5d52d87a8ab99c719`. PR-G extends that router with deterministic adaptive signals, live OpenAI-compatible/OpenCode
adapters, complete-session model metrics, bounded reasoning/output controls, and fail-closed
provider errors. Strategy metrics are deterministic across all required axes; model synthesis only
proposes alternatives and explanation. The six-scenario evidence under `docs/evidence/pr-g/`
records local-low/local-medium/host comparisons. Host active scored 6/6 with zero tool calls in
14.509 seconds versus native 6/6 with 40 calls in 78.016 seconds. The configured frontier path was
unavailable with `APIError`; it is not counted as passed and remains a final release blocker.
Post-merge main passed all-fast (85 Python and 9 adapter tests) and both package builds.

The reproducible PR-D smoke measured alternating three-run startup medians of 1,046 ms native and
1,070 ms plugin-enabled (+24 ms), then observed tool and external edit refreshes at 151 ms, MCP
connection/reconnection, three durable revisions, and no off-mode revision change. The raw
comparison includes a 1,609 ms native outlier; this is functional smoke evidence, not a stable
distribution.

## Evidence policy

A work package is not complete merely because source files exist or mocked tests pass. Record exact local commands/results and distinguish:

- deterministic unit/component/integration evidence;
- real repository benchmark evidence;
- real OpenCode integration evidence;
- real LLM/model-routing evidence;
- unavailable checks.

Planning documents are design evidence only. They do not count as implementation, build, test, real-host, or real-model evidence.

Do not mark unavailable evidence as passed.
