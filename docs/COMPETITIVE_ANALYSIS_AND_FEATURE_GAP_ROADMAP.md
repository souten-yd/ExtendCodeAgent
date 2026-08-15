# ExtendCodeAgent Competitive Analysis and Feature-Gap Roadmap

Status: canonical strategic overlay
Date: 2026-08-16
Scope: OpenCode + ExtendCodeAgent positioning against current coding-agent harnesses

## 1. Purpose

This document converts the current competitive review into an execution policy for ExtendCodeAgent.
It is not a parity checklist. It decides which external ideas should strengthen Project Intelligence,
which runtime features should be consumed through adapters, and which capabilities should remain
explicit non-goals so ExtendCodeAgent does not become a second generic agent harness.

This document refines, but does not replace, the following architecture decisions:

- `PROJECT_INTELLIGENCE_MASTER_PLAN.md` defines the Project Intelligence product domain.
- `PRODUCTIZATION_AND_MODEL_EVALUATION_PLAN.md` defines evidence-driven productization and release gates.
- `TRANSPARENT_PI_ORCHESTRATION_PLAN.md` defines minimum-intelligence task-aware automation.
- `RUNTIME_ADAPTER_ARCHITECTURE_PLAN.md` defines OpenCode as the reference runtime rather than the PI core.

When old feature-order language conflicts with this document, use the execution sequence in section 10
until the older document is intentionally consolidated.

## 2. Strategic conclusion

ExtendCodeAgent MUST NOT compete by recreating the broad harness features already supplied by
OpenCode, Claude Code, Codex, Cline, OMO, OpenHarness, Goose, or future runtimes.

The durable product position is:

> ExtendCodeAgent is a host-neutral Project Intelligence and Verification Runtime that gives coding
> agents persistent, revision-aware project truth; bounded evidence; impact/test/runtime reasoning;
> evidence-backed completion; weak-local-model efficiency; and cross-agent/worktree consistency.

The moat is therefore five connected areas:

1. **Project Truth** — Project Graph, Digital Twin, provenance, freshness, workspace/revision identity.
2. **Verification Intelligence** — Impact, Test Intelligence, Runtime Evidence, Traceability, Convergence.
3. **Task-aware Intelligence** — minimum useful PI, progressive expansion, explainable model/context routing.
4. **Weak-local Efficiency** — small structured evidence, cache-friendly stable envelopes, bounded decisions.
5. **Cross-agent Consistency** — keep multiple agent sessions/worktrees aligned with project truth without
   owning the team runtime itself.

## 3. Competitive snapshot and scoring method

Snapshot date: 2026-08-16. Scores are planning heuristics, not benchmark results.

Scale:

- 0 = effectively absent
- 1 = minimal
- 2 = limited
- 3 = useful
- 4 = strong
- 5 = category-leading or unusually complete

Systems:

- OC = OpenCode native
- OC+E = OpenCode + ExtendCodeAgent current implemented/planned product baseline
- Atomic = Atomic Agent
- Claude = Claude Code
- Codex = OpenAI Codex CLI/runtime
- Cline = Cline SDK/CLI/agent runtime
- OMO = OpenCode + Oh-My-OpenAgent

A score for OC+E does not convert unimplemented roadmap items into delivered features. Current source,
recorded evidence, and accepted plans remain authoritative.

### 3.1 Harness and model/runtime foundation

| # | Capability | OC | OC+E | Atomic | Claude | Codex | Cline | OMO |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | edit/patch quality | 4 | 4 | 4 | 5 | 5 | 4 | 5 |
| 2 | shell/process operation | 4 | 4 | 4 | 5 | 5 | 4 | 4 |
| 3 | Git integration | 3 | 3 | 2 | 4 | 4 | 3 | 4 |
| 4 | LSP/AST/semantic tooling | 4 | 5 | 1 | 3 | 3 | 4 | 5 |
| 5 | browser/web/desktop operation | 2 | 2 | 5 | 4 | 4 | 5 | 4 |
| 6 | MCP | 5 | 5 | 4 | 5 | 4 | 5 | 5 |
| 7 | provider breadth | 5 | 5 | 3 | 1 | 2 | 5 | 5 |
| 8 | local-model support | 5 | 5 | 5 | 1 | 3 | 4 | 4 |
| 9 | weak/small-model optimization | 2 | 5 | 5 | 0 | 2 | 3 | 3 |
| 10 | context/compaction control | 4 | 5 | 5 | 5 | 4 | 4 | 5 |

Category normalized score: OC 76, OC+E 86, Atomic 76, Claude 66, Codex 72, Cline 82, OMO 88.

### 3.2 Multi-agent, lifecycle, and long-running work

| # | Capability | OC | OC+E | Atomic | Claude | Codex | Cline | OMO |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 11 | subagents | 4 | 4 | 1 | 5 | 5 | 4 | 5 |
| 12 | parallel multi-agent execution | 3 | 3 | 1 | 5 | 5 | 4 | 5 |
| 13 | persistent agent teams | 1 | 1 | 0 | 5 | 4 | 5 | 5 |
| 14 | background tasks | 2 | 2 | 4 | 5 | 4 | 4 | 5 |
| 15 | scheduler/remote trigger | 1 | 1 | 5 | 3 | 4 | 5 | 2 |
| 16 | skills/rules | 4 | 4 | 4 | 5 | 5 | 4 | 5 |
| 17 | hooks/plugin extension | 5 | 5 | 2 | 5 | 5 | 5 | 5 |
| 18 | session recovery | 4 | 4 | 4 | 5 | 4 | 4 | 5 |
| 19 | checkpoint/worktree isolation | 3 | 3 | 1 | 5 | 4 | 5 | 3 |
| 20 | permission/sandbox policy | 4 | 4 | 4 | 5 | 5 | 4 | 4 |

Category normalized score: OC 62, OC+E 62, Atomic 52, Claude 96, Codex 90, Cline 88, OMO 88.

The low OC+E score in this category is mostly intentional. The correct response is not to implement a
second team manager, scheduler, shell, permission system, browser, or checkpoint engine. The response
is to normalize the useful observations and let PI reason over work performed by those runtimes.

### 3.3 Project Intelligence and differentiated value

| # | Capability | OC | OC+E | Atomic | Claude | Codex | Cline | OMO |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 21 | persistent memory | 2 | 2 | 5 | 5 | 4 | 3 | 3 |
| 22 | Project Graph / Digital Twin | 1 | 5 | 1 | 2 | 2 | 1 | 3 |
| 23 | Impact Analysis | 1 | 5 | 1 | 3 | 3 | 2 | 3 |
| 24 | Test Intelligence | 2 | 5 | 1 | 4 | 4 | 3 | 3 |
| 25 | Runtime Evidence | 3 | 4 | 4 | 4 | 4 | 3 | 4 |
| 26 | requirement -> code -> test traceability | 1 | 4 | 1 | 2 | 2 | 1 | 1 |
| 27 | Strategy / architecture intelligence | 3 | 5 | 2 | 5 | 4 | 3 | 4 |
| 28 | Convergence / evidence-backed done | 2 | 5 | 1 | 3 | 3 | 2 | 3 |
| 29 | research evidence/provenance | 3 | 5 | 2 | 4 | 4 | 3 | 4 |
| 30 | adaptive model/task routing | 2 | 4 | 2 | 3 | 3 | 3 | 5 |

Category normalized score: OC 40, OC+E 88, Atomic 40, Claude 70, Codex 66, Cline 48, OMO 66.

Using a strategic weighting of 30% foundation, 30% orchestration, 40% Project Intelligence gives the
following planning score: OC+E 79.6, OMO 79.2, Claude 76.6, Codex 75.0, Cline 70.2, OC 57.4,
Atomic 54.4. This is not a claim of benchmark superiority. It demonstrates that ExtendCodeAgent's
best position is specialization above capable runtimes rather than harness parity.

## 4. What to adopt from Atomic Agent

Atomic's strongest transferable ideas concern small local models and externalized state.

### ADOPT — stable-prefix-aware PI delivery

Keep invariant/static PI protocol text, schemas, capability descriptions, and stable tool contracts
separate from task/revision-specific evidence. Measure cache reuse where the runtime/provider exposes
it. Do not make model-provider-specific KV-cache APIs part of PI core.

### ADOPT — bounded structured decision envelopes

Weak models should choose from deterministic candidates, IDs, enums, evidence references, and bounded
schemas wherever possible. Apply the concept to IntelligencePlan, Strategy alternatives, verification
and Convergence decisions. Do not replace the host agent loop with GBNF tool calling.

### ADOPT — externalized state as a Project Intelligence invariant

Project truth must live in Twin/Graph/evidence stores rather than conversation history. Context is a
projection of state, never the primary database.

### ADOPT — append-only diagnostic trace and replay

Record compact PI plans, selected evidence IDs, revision IDs, route decisions, validation outcomes,
fallbacks and timings so failures can be replayed or compared without retaining raw private model
transcripts. This becomes an evaluation/debugging capability, not a second session-history system.

### ADOPT WITH MODIFICATION — memory

Implement **Project Evidence Memory**, not generic conversational memory. Candidate durable objects:
architecture decisions, accepted requirements, previous regression causes, human overrides, known
failure signatures, successful repair evidence, stale-test incidents, runtime incidents and verified
project-specific lessons. Every record requires provenance, revision/workspace scope, confidence and an
invalidation/freshness policy.

### DO NOT ADOPT

Do not own llama.cpp/model download/quantization/speculative decoding, generic browser operation,
scheduling, shell, clipboard, ordinary session persistence, or the generic agent loop.

## 5. What to adopt from Claude Code

### ADOPT VIA RUNTIME CONTRACT — subagent/team/worktree observations

Claude demonstrates that independent worktrees and coordinated agent sessions are becoming normal
runtime primitives. Extend RuntimeCapabilities only with observations PI actually consumes, such as:
workspace fork identity, parent task/session relation, agent task identity, changed paths, verification
outcome and merge/rebase/finalization events when the runtime exposes them.

### ADOPT — completion-quality hook integration

Where a host exposes task-completion or teammate-idle hooks, Convergence may supply an advisory or
blocking decision according to rollout policy. Core completion truth still comes from PI evidence;
host hooks are delivery mechanisms.

### ADOPT WITH MODIFICATION — persistent memory

Use host memory for agent preferences/instructions if available; use Project Evidence Memory for
revision-aware engineering facts. Do not mirror full subagent conversation memory in ExtendCodeAgent.

### DO NOT ADOPT

Do not implement a lead agent, shared team mailbox/task board, terminal agent monitor, worktree manager,
or generic hook runner. Those remain host capabilities.

## 6. What to adopt from Codex

### ADOPT VIA RUNTIME CONTRACT — hooks, multi-agent and runtime metrics

Codex's expanding hook/multi-agent/memory/runtime surfaces reinforce capability-negotiated adapters.
Add a capability only after a concrete PI consumer exists. Missing hooks must degrade explicitly.

### ADOPT — strict separation between PI policy and execution policy

Sandbox/approval/execution authority belongs to the host. ExtendCodeAgent may calculate risk,
impact, verification need or evidence confidence, but must not silently replace runtime permissions.

### DO NOT ADOPT

Do not replicate sandboxing, approvals, shell snapshots, generic memory, browser/computer-use,
provider authentication, or the host TUI.

## 7. What to adopt from Cline

### ADOPT VIA RUNTIME CONTRACT — checkpoint and persistent-team identity

Cline checkpoints show value in identifying concrete workspace states. PI should be able to associate
runtime checkpoints/worktree revisions with Twin revisions when a runtime exposes them. It should not
create a shadow Git repository merely to match Cline.

Persistent team task IDs/mailbox state are useful only as external task identity and provenance for PI.
The team state itself remains owned by Cline.

### ADOPT — hook failure semantics and lifecycle observability

Use explicit blocking/non-blocking, timeout, retry and fail-open/fail-closed semantics for adapter-side
PI delivery where appropriate. Preserve native fallback for non-critical PI failures.

### DO NOT ADOPT

Do not build a scheduler, team board/mailbox, checkpoint engine, agent hub, remote execution service or
editor UI.

## 8. What to adopt from OMO

OMO is the most important direct complement because it extends OpenCode in the orchestration layer.

### ADOPT AS COMPLEMENT, NOT DUPLICATE — background/team orchestration

OMO Team Mode/background agents should be treated as host/runtime behavior. If stable observable
signals are available, ExtendCodeAgent should make them PI-aware: workspace/revision identity,
cross-agent dependency impact, stale-context detection and verification convergence.

### ADOPT — session/model failure observability

Feed observable provider/model/session failures into task-aware fallback and evaluation telemetry.
Do not duplicate OMO/OpenCode's session recovery implementation.

### KEEP COMPLEMENTARY — LSP/AST

OMO/OpenCode LSP/AST tools improve execution-time navigation. ExtendCodeAgent's durable revisioned
semantic graph, impact paths and evidence history remain separate and complementary.

### DO NOT ADOPT

Do not clone OMO's agent personalities, background manager, Team Mode, tmux panes, hash-anchored edit
engine, generic session manager or hook collection. OMO itself is undergoing multi-harness
restructuring; do not bind PI architecture to its internal shapes.

## 9. New differentiated capabilities created by the comparison

### 9.1 Weak-Local Evidence Protocol

Promote weak-local support from a context-size optimization into a formal protocol:

- stable PI envelope separated from revision/task evidence;
- deterministic candidate reduction before model calls;
- bounded IDs/enums/schemas for decisions;
- progressive evidence expansion;
- compressed tool/runtime evidence;
- cache-hit/prefix reuse metrics when observable;
- strict output/reasoning budgets;
- local-low repeated distributions rather than best-run reporting.

### 9.2 Project Evidence Memory

Add durable, revision-aware project lessons/evidence without becoming chat memory. Records must be
queryable by task/project/symbol/revision, bounded, provenance-bearing and invalidatable.

### 9.3 PI Trace and Replay

Persist a compact append-only trace of IntelligencePlan -> evidence selection -> model route ->
verification -> Convergence/fallback. Support deterministic replay of the PI portion where inputs are
available. Never require raw model chain-of-thought or secrets.

### 9.4 Verification Intelligence 2.0

Expand the current Test/Runtime/Convergence strength only where measured task failures justify it.
Candidate additions:

- stale mock/fixture detection;
- flaky-history signals;
- changed behavior without current evidence;
- requirement-to-test evidence gaps;
- mutation-survivability signals when practical;
- minimal verification-set selection;
- completion gate that rejects stale/missing/conflicting evidence.

### 9.5 PI-aware Parallel Development

This is a strategic differentiator, not a replacement team runtime.

Conceptual flow:

```text
runtime team/subagents/worktrees
        -> runtime adapter observations
        -> workspace-specific Twin revisions
        -> cross-workspace Impact comparison
        -> stale dependency/context detection
        -> verification and merge-risk evidence
        -> runtime-specific advisory/replan delivery
```

Target examples include one agent changing an API while another worktree still implements against the
old contract, or one worktree invalidating a test assumption used by another. The feature should
surface semantic conflicts earlier than Git merge conflict detection.

## 10. Consolidated execution sequence

The previous broad RV/TA/RA plans remain valid, but execution is reordered and consolidated below to
avoid scope creep.

### COMP-0 — Competitive strategy baseline

This document and handoff synchronization only. No production code.

Exit: adopted/delegated/rejected decisions are explicit and canonical.

### RV-0 — Baseline Release Validation

Remains first production step. Extend its gap report to measure competition-derived concerns:

- weak-local context/prefix/tool-output efficiency;
- lifecycle/recovery observability;
- worktree/subagent capability availability;
- completion correctness;
- repeat-task/cross-session evidence loss;
- current host-native feature overlap so PI does not duplicate it.

No speculative feature implementation.

### RV-1 — blocking host/productization repair

Conditional. Fix current OpenCode/frontier/lifecycle/config incompatibilities before new intelligence.

### RA-0 — Minimal Runtime Contract

Run before active transparent automation. Consolidate any new host-neutral capability fields needed by
TA or later multi-agent evidence. Candidate optional capabilities include:

- observe_subagent/task relation;
- observe_workspace/worktree identity;
- observe_background-task lifecycle;
- observe_checkpoint/revision identity;
- observe_host completion/verification event;
- deliver advisory completion/replan feedback.

Do not add a field without a PI consumer and a conformance test.

### TA-0 — shadow Task-aware planner

Unchanged principle: signals/classification/IntelligencePlan/reasons/telemetry only, no behavior change.

### WL-0 — Weak-Local Evidence Protocol

Run after RV-0/TA-0 provides a measured baseline and before weak-local active-default claims.
Implement only the parts that improve repeated task success, latency, tokens or structured-output
reliability. This may be folded into TA/context/model-routing code rather than created as a new package.

### TA-1 — advisory automatic selection

Use existing PI services and the Weak-Local Evidence Protocol. No duplicate query/context subsystem.

### VI-0 — Verification Intelligence and Convergence quality

This **absorbs the intent of the old RV-3 verification/confidence step**. Ground-truth confidence,
Test Intelligence improvements and completion correctness are one coherent work package. Do not add
Test Intelligence 2.0 features without a measured false-completion, stale-test, coverage or verification
gap.

### TA-2 — bounded active

Only accepted low-risk task/relation classes. Stale/uncertain evidence downgrades to advisory/native.

### TA-3 — progressive expansion

Expand intelligence only from evidence gaps. Model escalation remains a separate policy decision.

### RB-0 — Runtime Bridge

Conditional on repeated UI/API/runtime boundary failures. Use generic relations with runtime provenance.

### DA-0 — bounded deep analysis

Conditional. DFG/Taint before CFG when data-origin/security failures prove the need. No default
repository-wide deep graph.

### RV-FINAL — OpenCode production-capable baseline

No new feature scope. Re-run task/model/repository matrices and compare native vs PI modes.

### EM-0 — Project Evidence Memory + PI Trace/Replay

Strategic P1 after the baseline, unless RV-0/VI-0 shows cross-session evidence loss is release-blocking.
Implement one bounded evidence store/trace path, reusing existing SQLite/revision/provenance contracts.
Do not create a separate generic memory platform.

### RA-1 / RA-2 — OpenCode and MCP conformance

Verify runtime capability declarations, observations, privacy, lifecycle and fallback truthfully.

### RA-3 — Second-Harness Proof

Select exactly one runtime using API stability, hook quality, accessibility and user value. Cline SDK is
a strong initial candidate because it exposes explicit SDK lifecycle/team/checkpoint/plugin surfaces;
Claude Code is a strong candidate when its required hook path is sufficiently stable; Codex remains a
candidate as its plugin/hook/multi-agent surfaces stabilize. OMO is a complement/integration target,
not the first proof while its multi-harness architecture remains in active restructuring.

The proof must reuse Project Model/Impact/Context/Verification/Task Controller without rewriting core.

### MA-0 — PI-aware Parallel/Worktree Intelligence

P1 strategic differentiation after runtime/workspace observations are proven. Start with detection and
advisory evidence, not automatic cross-agent control. Required first targets:

1. workspace-specific Twin identity;
2. base/fork revision ancestry;
3. cross-worktree affected-contract detection;
4. stale-context/evidence invalidation;
5. merge-risk and test-selection projection;
6. host-specific advisory/replan delivery only when supported.

### RV-X — comparative integration benchmark

After the OpenCode baseline, compare where practical:

- OpenCode native;
- OpenCode + OMO;
- OpenCode + ExtendCodeAgent;
- OpenCode + OMO + ExtendCodeAgent.

Use the same tasks, revisions, models and objective verification. The purpose is to prove complementarity
and detect duplicate overhead, not to optimize a marketing score.

## 11. Explicit non-goals / rejected parity work

Unless a future measured requirement overturns the decision, ExtendCodeAgent will not implement:

- a generic agent control loop;
- its own shell/patch/edit runtime;
- a generic permission/sandbox engine;
- generic browser automation;
- a scheduler/cron runtime;
- a persistent agent-team task board/mailbox/lead coordinator;
- a generic worktree manager;
- a Cline-style shadow-Git checkpoint engine;
- a host TUI/IDE replacement;
- provider authentication/model download/quantization/speculative decoding;
- generic conversational memory replacement;
- an OMO-style personality/agent pack;
- repository-wide always-on CFG/DFG/taint/UI graphs;
- OpenCode core patches merely to gain convenience.

A runtime feature may still become visible to PI through an adapter observation without becoming an
ExtendCodeAgent-owned subsystem.

## 12. Anti-staleness policy

Competitive analysis is volatile. Keep it useful without turning the repository into a news tracker.

Revalidate this snapshot at any of these gates:

1. RV-0 environment capture;
2. RV-FINAL;
3. before RA-3 chooses a second harness;
4. before MA-0 selects a host-specific integration;
5. when OpenCode changes the plugin/event contract materially;
6. when a compared runtime ships a major architecture change that affects an adopted/delegated decision;
7. at least every 90 days while active productization continues.

Rules:

- prefer official documentation/source repositories;
- record snapshot date and relevant version/experimental status;
- do not change architecture merely because a competitor added a feature;
- rerun task evidence before promoting a competitor-inspired feature;
- experimental competitor features count as architectural signals, not production guarantees;
- measured ExtendCodeAgent task outcomes override heuristic scores;
- consolidate or delete superseded roadmap steps instead of accumulating parallel plans.

Primary sources used for this snapshot:

- Atomic Agent engineering/source docs: `https://github.com/AtomicBot-ai/atomic-agent`
- Atomic architecture docs: `https://atomicagent.io/docs/concepts/architecture/`
- Claude Code parallel agents/teams/hooks: `https://code.claude.com/docs/en/agents`,
  `https://code.claude.com/docs/en/agent-teams`, `https://code.claude.com/docs/en/hooks`
- Codex source/config schema: `https://github.com/openai/codex`
- Cline teams/checkpoints/plugins/scheduling: `https://docs.cline.bot/cli/agent-teams`,
  `https://docs.cline.bot/core-workflows/checkpoints`, `https://docs.cline.bot/sdk/plugins`,
  `https://docs.cline.bot/cli/scheduling`
- Oh-My-OpenAgent features/roadmap: `https://github.com/code-yeongyu/oh-my-openagent`

## 13. Decision rule

A competitor-inspired capability enters implementation only if at least one is true:

- it raises verified task correctness or completion quality;
- it materially reduces model/tool/token/time cost without quality loss;
- it enables weak local models to complete tasks they otherwise fail;
- it fixes a measured project-truth, cross-workspace, impact, test or runtime-evidence gap;
- it is necessary to keep PI portable across an accepted runtime adapter.

If the capability is already better owned by the runtime, ExtendCodeAgent should integrate it, not
reimplement it.
