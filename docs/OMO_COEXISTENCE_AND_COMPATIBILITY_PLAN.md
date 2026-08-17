# OpenCode + OMO + ExtendCodeAgent Coexistence and Compatibility Plan

> **Consolidated 2026-08-16; stage mapping corrected 2026-08-17.** B2 executes the bounded OMO-C0
> coexistence baseline. P4 retains the four-way comparative benchmark and benefit claim.

Status: canonical compatibility plan
Date: 2026-08-16
Runtime target: OpenCode
Optional orchestration plugin: Oh-My-OpenAgent (OMO)

## 1. Purpose

ExtendCodeAgent must remain useful with plain OpenCode, but OpenCode users may also install OMO for
agent orchestration, background work, additional hooks/tools, and Team Mode. This plan defines how to
prove that OMO and ExtendCodeAgent coexist without silent semantic conflicts.

OMO is an optional complement, not a dependency. ExtendCodeAgent must not require OMO, copy OMO's
orchestration features, or bind its core contracts to OMO internals.

The compatibility claim under test is:

> Adding ExtendCodeAgent to an otherwise working OpenCode + OMO environment preserves OMO behavior,
> preserves native OpenCode behavior outside the intended PI contribution, and adds measurable Project
> Intelligence value without duplicate execution, corrupted context, hidden tool loss, or false
> verification.

## 2. Current overlap surface

OpenCode supports multiple plugins and executes their hooks sequentially. OMO and ExtendCodeAgent can
therefore coexist structurally, but sequential mutation means plugin order can matter.

Current ExtendCodeAgent stable adapter surface:

- namespaced `pi_*` tools;
- `event` observations;
- `tool.execute.before` observation/timing;
- `tool.execute.after` runtime-evidence normalization;
- bounded filesystem watcher fallback;
- sidecar lifecycle and Project Intelligence queries.

Current OMO surface is materially broader:

- agent/tool/MCP/command registration;
- pre/post-tool guards and output transforms;
- message and system transforms;
- model-parameter/fallback changes;
- session lifecycle/recovery hooks;
- compaction preservation/continuation;
- background tasks;
- optional Team Mode and worktrees.

The primary compatibility risk is therefore hook interaction and transformed state, not current tool
name collision.

## 3. Compatibility principles

1. **Namespace ownership** — ExtendCodeAgent-owned user tools remain `pi_*`. Do not reuse OMO tool,
   agent, command, skill, MCP, or config names.
2. **Observation before mutation** — prefer observation-only hooks. A PI feature that mutates generic
   OpenCode message/tool/system state must justify the mutation with measured value.
3. **Idempotence** — future PI injection must be tagged/idempotent so repeated transforms cannot inject
   the same evidence twice.
4. **Order robustness** — supported features should work with either plugin ordering where OpenCode
   exposes ordering. If a feature cannot be order-independent, the required order must be explicit,
   tested, and treated as a compatibility limitation rather than hidden behavior.
5. **No orchestration ownership** — OMO owns OMO teams/background agents. ECA may observe task,
   session, workspace, mutation, and verification signals when available.
6. **Truth isolation** — OMO-generated summaries/messages are not verified project facts. ECA Graph,
   Twin, source revision, runtime evidence, and objective verification keep their existing truth rules.
7. **Fail-open for PI infrastructure** — non-critical ECA failure must leave an otherwise valid OMO /
   OpenCode session operational.
8. **No hidden fallback coupling** — OMO model fallback and ECA model routing are separate policies.
   ECA records resolved route information when observable but must not recursively trigger competing
   fallback loops.

## 4. Conflict taxonomy

### C0 — Namespace/registration conflict

Examples:
- duplicate tool names;
- duplicate agent/command/skill IDs;
- plugin registration replacing the other plugin;
- MCP name collision.

Acceptance: zero collisions for supported default configuration.

### C1 — Hook-order semantic conflict

Examples:
- OMO mutates tool args before ECA captures runtime evidence;
- OMO truncates/transforms a tool result before ECA observes it;
- future ECA context injection is duplicated or stripped by OMO transforms;
- compaction drops PI evidence or duplicates it after resume.

Acceptance: either order-independent behavior or an explicit, tested order constraint with equivalent
verified task correctness.

### C2 — Context/prompt conflict

Examples:
- both systems inject overlapping instructions;
- evidence consumes context without contributing to task success;
- OMO agent persona contradicts PI confidence/freshness semantics;
- weak models degrade from combined prompt volume.

Acceptance: no critical correctness regression; bounded context overhead; no duplicate PI blocks.

### C3 — Tool/policy conflict

Examples:
- OMO tool guards block `pi_*` tools;
- ECA active policy accidentally suppresses OMO tools;
- tool permissions differ between lead/member agents;
- one plugin causes a tool to execute twice.

Acceptance: intended tools remain visible and every tool call executes at most once.

### C4 — Model-routing conflict

Examples:
- OMO fallback and ECA escalation oscillate;
- resolved model identity is misattributed;
- privacy policy forbids a route that OMO selects.

Acceptance: no fallback loops; privacy upper bounds remain authoritative; recorded route is truthful.

### C5 — Session/compaction/recovery conflict

Examples:
- ECA revision/task state lost after OMO compaction/autocontinue;
- recovered session attaches stale PI context;
- deleted/idle/team sessions leak observations into another workspace.

Acceptance: task/workspace/session identity remains isolated; stale evidence cannot become fresh after
recovery.

### C6 — Team/worktree conflict

Examples:
- OMO members work in separate worktrees but ECA collapses them into one Twin;
- a lead sees stale evidence produced by a member workspace;
- merge/rebase changes invalidate PI without refresh.

Acceptance: every observed worktree maps to a distinct workspace/Twin identity until an explicit
merge/reconciliation event is proven.

## 5. Required test matrix

Do not test only the combined stack. Establish four baselines on the same repository/task/model:

A. OpenCode native
B. OpenCode + ExtendCodeAgent
C. OpenCode + OMO
D. OpenCode + OMO + ExtendCodeAgent

For order-sensitive plugin APIs, additionally test both configured plugin orders when practical:

- OMO -> ECA
- ECA -> OMO

For OMO Team Mode claims, run Team Mode both disabled and enabled. A single-agent run cannot validate
Team/worktree compatibility.

Use model tiers according to the feature claim. At minimum, compatibility acceptance should include a
practical local model and one stronger/current model when available. Weak-local combined-context tests
are required before claiming weak-local compatibility.

## 6. Mandatory coexistence scenarios

1. Startup/plugin registration and clean shutdown.
2. `pi_status` and all supported `pi_*` tools visible with OMO loaded.
3. OMO agents/tools visible with ECA loaded.
4. Normal read/edit/bash/test task with no duplicate tool execution.
5. Tool guard input mutation and ECA observation correctness.
6. Tool output transform/truncation and ECA runtime-evidence truthfulness.
7. Session restart/reconnect.
8. Context compaction and continuation.
9. OMO model fallback/provider failure while ECA records truthful state.
10. ECA sidecar unavailable/degraded while OMO task remains usable.
11. OMO disabled / ECA disabled/off-mode symmetry.
12. Team Mode: multiple members, independent worktrees where enabled, lead/member tool visibility,
    workspace identity, stale-context protection, and final verification.
13. Long-running/background task if OMO uses a separate session lifecycle.
14. Privacy profile forbidding remote escalation.

## 7. Metrics

Compatibility metrics:

- plugin load success;
- expected tool/agent count and visibility;
- duplicate/missing tool-call count;
- hook error count;
- session/recovery/compaction correctness;
- workspace/Twin identity correctness;
- provider/fallback loop count;
- stale-context incidents;
- ECA false verification count.

Outcome metrics:

- verified task success;
- tests/build/typecheck/lint/behavior correctness;
- wrong/unnecessary edits;
- unsupported claims;
- completion correctness;
- tool calls;
- input/context tokens;
- output/reasoning tokens where observable;
- wall time;
- retries/timeouts;
- startup overhead.

Compare D against both B and C. The combined stack is accepted only when it does not merely preserve
functionality but has a defensible reason to be recommended over either plugin alone for the relevant
task class.

## 8. Compatibility states

Track compatibility separately from feature rollout:

- `unknown` — not tested for current version tuple;
- `incompatible` — known correctness/runtime blocker;
- `degraded` — works with documented limitations;
- `compatible` — coexistence gates pass;
- `recommended` — compatible and combined-stack benefit is measured for representative tasks.

Compatibility is a tuple, not a timeless label:

`OpenCode version + OMO version + ExtendCodeAgent version + relevant mode/options`.

Do not automatically transfer a result across major/minor plugin/runtime changes without a smoke
recheck.

## 9. Release and roadmap gate

Add **OMO-C0 Coexistence Baseline** after the plain OpenCode RV-0 baseline is stable and before any
claim that OMO + ECA is a recommended stack.

OMO-C0 scope:
- current supported OpenCode;
- current selected OMO release;
- current ECA release candidate;
- Team Mode off;
- startup/tool/session/basic coding/verification compatibility;
- both plugin orders where meaningful.

Add **OMO-C1 Team/Worktree Compatibility** only when Team Mode or another multi-agent path is actually
part of the product claim.

OMO-C1 is the prerequisite for PI-aware parallel/worktree intelligence. It must not create a team
runtime inside ECA.

## 10. ControlDeck relationship

ControlDeck may later offer a convenient installer/profile containing OpenCode + ECA + OMO. That
installer is owned by ControlDeck and does not change ECA's architecture.

ECA's responsibility is only to publish generic installable artifacts/configuration and a compatibility
result that ControlDeck or any other distributor can consume. A ControlDeck-specific adapter or
installation API remains out of scope.

A ControlDeck "recommended stack" must only select an OpenCode/OMO/ECA version tuple marked
`compatible` or `recommended` by reproducible coexistence evidence.

## 11. Stop rules

Do not patch OMO or OpenCode from ECA merely to force compatibility. First classify the conflict and
prefer:

1. ECA namespacing/idempotence/order robustness;
2. documented config compatibility;
3. upstream issue/fix when the defect belongs to OpenCode or OMO;
4. temporary degraded compatibility classification;
5. only then a narrowly-scoped adapter workaround if it remains host-neutral and measured.

Never duplicate OMO orchestration features to avoid an integration problem.
