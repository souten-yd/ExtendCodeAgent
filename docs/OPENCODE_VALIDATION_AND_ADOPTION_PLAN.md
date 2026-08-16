# OpenCode Validation and Adoption Plan

> **Consolidated 2026-08-16.** Canonical evidence rule and ControlDeck ruling. Sequencing is folded into `docs/PI_MASTER_EXECUTION_PLAN.md` section 8.

Status: canonical immediate validation policy
Date: 2026-08-16
Primary runtime/product target: OpenCode

## 1. Decision

ExtendCodeAgent productization is **OpenCode-first**. The current validation target is OpenCode itself,
not the application or UI from which OpenCode happens to be launched.

ControlDeck currently uses OpenCode essentially as-is. It does not define a distinct agent runtime,
agent loop, Project Intelligence contract, or materially different OpenCode execution semantics for
ExtendCodeAgent. Therefore, for current ExtendCodeAgent planning and evaluation:

> OpenCode used from ControlDeck is treated as ordinary OpenCode.

ControlDeck is not a separate harness variant, adapter target, integration boundary, or mandatory
experimental dimension. It may be a convenient place from which the user runs OpenCode, and the
ControlDeck repository may be one useful real-world task repository, but neither fact changes the
ExtendCodeAgent product boundary.

If ControlDeck later incorporates OpenCode deeply enough to change agent execution, session semantics,
tool delivery, context injection, model routing, verification signals, or other behavior relevant to
ExtendCodeAgent, that future integration MUST first be measured and then explicitly promoted to a
separate evaluation condition. Do not anticipate that future state in today's architecture.

## 2. Product and architecture boundary

Current product path:

```text
OpenCode runtime
      |
      +-- native OpenCode tools / agents / sessions / models
      |
      +-- ExtendCodeAgent OpenCode adapter/plugin/MCP
                |
                v
       Project Intelligence
```

ExtendCodeAgent MUST NOT add ControlDeck-specific code, contracts, adapters, installation logic,
discovery, lifecycle management, configuration, UI integration, or evaluation behavior.

The host-neutral core remains portable by architecture, but no second harness is a current production
dependency.

## 3. Mandatory feature-effect rule

A capability is not adopted because it is implemented, unit-tested, benchmarked in isolation, or
inspired by another harness. Every new or materially changed capability MUST be evaluated using the
actual OpenCode / agent / LLM combinations required to prove its claimed effect.

The default comparison is:

A. OpenCode native, ExtendCodeAgent absent/disabled
B. OpenCode + ExtendCodeAgent `off`
C. OpenCode + ExtendCodeAgent `shadow`
D. OpenCode + ExtendCodeAgent `advisory`
E. OpenCode + ExtendCodeAgent `active` where permitted

ControlDeck-launched OpenCode and terminal-launched OpenCode are the same evaluation condition unless
measured evidence shows a material execution-semantic difference.

For orchestration-specific questions only, after the normal OpenCode baseline is stable:

F. OpenCode + OMO
G. OpenCode + OMO + ExtendCodeAgent

OMO remains optional and is never a release dependency.

## 4. Model and agent matrix

Evaluate logical model tiers rather than fixed product names:

1. `local-low` — deliberately weak/small local model;
2. `local-practical` — practical local coding/reasoning model;
3. `host-default` — current normal OpenCode model path when applicable;
4. `frontier` — a functioning current frontier path when available and allowed.

Use the smallest matrix that can falsify or establish the capability claim. The evaluation record must
state why omitted combinations cannot change the adoption decision.

Examples:

- Weak-Local Evidence Protocol -> OpenCode + local-low and local-practical, repeated runs.
- Context selection -> native/advisory/active with local-practical plus at least one stronger model.
- Convergence/completion -> real OpenCode agent execution plus objective build/test/runtime evidence;
  use multiple model tiers if model reasoning can affect completion.
- PI-aware parallel work -> an OpenCode-compatible configuration that actually provides distinct
  agent/task/workspace identities. A sequential single-agent test cannot validate this claim.
- OMO complementarity -> OpenCode+OMO versus OpenCode+OMO+ExtendCodeAgent on the same task.
- Project Evidence Memory -> repeated/cross-session tasks plus changed-revision invalidation cases.

No capability is accepted from mocked adapters alone.

## 5. Repository and task corpus

Do not bind product acceptance to one repository.

Use real repositories representing the supported analysis domains. The current practical set should
include:

- ExtendCodeAgent or another Python repository;
- ControlDeck or another JS/TS/React + Python/mixed repository;
- at least one held-out repository not used to tune rules, thresholds, context profiles, or graph
  heuristics.

ControlDeck is useful because it is a real and comparatively broad project, not because ControlDeck is
a special ExtendCodeAgent platform.

Required task classes include:

- locate/explain;
- bounded bug fix;
- multi-file refactor;
- API/consumer impact change;
- test selection and verification;
- stale/insufficient evidence detection;
- UI/backend or other cross-boundary diagnosis where relevant;
- architecture/migration decision;
- completion decision after implementation.

Reserve held-out tasks/prompts and at least one held-out repository for anti-overfit confirmation.

## 6. Metrics

### Objective outcomes

- verified task success;
- tests/build/typecheck/lint/behavior correctness;
- unsupported/fabricated claims;
- wrong or unnecessary edits;
- completion correctness;
- stale-evidence false acceptance;
- regression rate.

### Efficiency

- tool calls and file reads;
- input/context tokens;
- cached/prefix tokens when observable;
- output/reasoning tokens when observable;
- wall time, retries and timeouts;
- model escalations;
- OpenCode/ExtendCodeAgent startup overhead;
- CPU/RAM/DB growth where relevant.

### Project Intelligence quality

- context useful-item precision and missing-fact failures;
- Impact precision/recall;
- test-selection precision/recall;
- freshness/provenance correctness;
- task/capability selection precision/recall;
- worktree/cross-agent stale-context detection when applicable;
- Convergence false-positive/false-negative rate.

Do not optimize efficiency at the cost of correctness.

## 7. Attribution rule

Every accepted result records at minimum:

- ExtendCodeAgent commit;
- OpenCode version;
- model/provider/version or logical profile plus exact resolved model;
- repository commit/workspace identity;
- PI mode and relevant capability configuration;
- hardware/runtime environment when it can affect the metric.

Do **not** routinely treat ControlDeck version, UI path, or launch path as a product variable. Record
such metadata only if it materially affects reproducibility or a measured discrepancy.

If a future ControlDeck change is shown to alter OpenCode semantics relevant to the result, classify
that run as a distinct environment from that point forward rather than retroactively coupling
ExtendCodeAgent to ControlDeck.

## 8. Feature adoption states

Use explicit rollout states:

`experimental -> shadow -> advisory -> active-scoped -> active-default`

or `deferred/rejected` when evidence does not justify cost.

A capability advances only when all applicable conditions pass:

1. real OpenCode task evidence exists;
2. required agent/model combinations were actually tested;
3. stochastic local models use repeated runs;
4. objective correctness does not regress on critical accepted tasks;
5. benefit is attributable to ExtendCodeAgent;
6. overhead is bounded on tasks that do not benefit;
7. privacy/fallback/off-mode semantics remain correct;
8. confidence/freshness supports the requested rollout level;
9. held-out tasks do not show critical overfit;
10. before generic `active-default`, held-out repository evidence confirms the capability is not
    repository-specific.

A feature may remain task-scoped or model-scoped when that is where evidence shows value.

## 9. Competitive adoption rule

For each idea inspired by Atomic Agent, Claude Code, Codex, Cline, OMO, OpenHarness, Goose or another
system, record:

- source idea;
- ExtendCodeAgent-specific problem it addresses;
- smallest implementation;
- required OpenCode/agent/model combinations;
- baseline(s);
- measurable expected gain;
- actual measured result;
- adoption decision and rollout scope.

Competitive inspiration never establishes value by itself.

## 10. Current differentiated candidates

### Weak-Local Evidence Protocol

Evaluate stable PI envelopes, deterministic candidate reduction, bounded decisions and progressive
evidence expansion with local-low/local-practical OpenCode runs. Retain only changes with measured
quality/reliability/efficiency benefit.

### Project Evidence Memory and PI Trace/Replay

Evaluate repeated project tasks across sessions and revisions. The feature must improve retrieval,
verification or debugging while correctly invalidating stale evidence. Generic conversational memory
remains out of scope.

### Verification Intelligence 2.0

Use real tasks where baseline test selection or completion is demonstrably incomplete. Add only the
smallest stale/mock/flaky/requirement/mutation/verification signal that produces objective benefit.

### PI-aware Parallel Development

Do not implement a team runtime. First prove OpenCode/OMO or another OpenCode-compatible execution
path exposes stable distinct task/workspace signals. Evaluate semantic cross-workspace conflicts only
then. If signals are insufficient, defer instead of creating orchestration inside ExtendCodeAgent.

## 11. Current execution sequence

1. RV-0 OpenCode baseline and measured gap report.
2. RV-1 blocking OpenCode / ExtendCodeAgent / model-provider repair if measured.
3. RA-0 minimum OpenCode runtime contract needed by Task-aware PI.
4. TA-0 shadow task-aware planner.
5. WL-0 weak-local protocol only if evidence justifies it.
6. TA-1 advisory automatic capability/context selection.
7. VI-0 consolidated confidence, Test Intelligence and Convergence/completion quality.
8. TA-2 bounded active for accepted task/relation/model scopes.
9. TA-3 progressive expansion after repeated evidence.
10. Conditional Runtime Bridge / bounded DFG/Taint/CFG only for measured missing relations.
11. RV-FINAL OpenCode production baseline across representative and held-out repositories.
12. EM-0 Project Evidence Memory / PI Trace if not pulled earlier by measured need.
13. Optional OpenCode+OMO complementarity benchmark.
14. RA-3 second-harness portability proof after the OpenCode production baseline.
15. MA-0 PI-aware parallel/worktree intelligence after stable runtime identity signals are proven.

## 12. Future ControlDeck deep-integration gate

The user expects ControlDeck may integrate OpenCode more deeply in the future. That is a future
ControlDeck design decision, not a present ExtendCodeAgent requirement.

Only create a separate `ControlDeck + OpenCode` evaluation condition if future implementation is
shown to alter one or more relevant semantics, for example:

- agent/session lifecycle visible to ExtendCodeAgent;
- tool execution or hook delivery;
- context injection or compaction;
- model/provider routing;
- workspace/revision identity;
- verification/runtime observation;
- multi-agent/worktree orchestration.

Until such evidence exists, assume equivalence with normal OpenCode and keep ExtendCodeAgent planning
focused on OpenCode.
