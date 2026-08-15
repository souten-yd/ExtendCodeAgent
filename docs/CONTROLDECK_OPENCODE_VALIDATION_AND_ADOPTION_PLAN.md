# ControlDeck OpenCode Evaluation and Adoption Plan

Status: canonical immediate validation policy
Date: 2026-08-16
Primary runtime: OpenCode
Primary evaluation platform: ControlDeck

## 1. Decision

ExtendCodeAgent remains architecturally host-neutral, while current productization is **OpenCode-first**.
ControlDeck is used as the first practical **evaluation platform** because it already provides a usable
OpenCode environment and real development workflows.

ControlDeck is **not** an ExtendCodeAgent integration target or adapter boundary.

The ownership boundary is explicit:

- ExtendCodeAgent integrates with **OpenCode** through its normal OpenCode adapter/plugin/MCP surfaces.
- ControlDeck decides independently how it installs, launches, configures, exposes, or updates OpenCode
  and how it makes ExtendCodeAgent available to that OpenCode environment.
- ExtendCodeAgent MUST NOT add ControlDeck-specific installation code, discovery protocols, lifecycle
  management, APIs, provider contracts, UI contracts, or configuration formats.
- Evaluation may record ControlDeck state/version because it is part of the experiment environment,
  but that does not make ControlDeck part of the ExtendCodeAgent product architecture.
- A second runtime adapter remains deferred until the OpenCode baseline is production-capable and
  portability evidence justifies it.

The product claim under test is therefore:

> Does ExtendCodeAgent measurably improve OpenCode coding-agent work on real projects and model tiers?

ControlDeck is one platform on which that question is evaluated.

## 2. Evaluation topology

The conceptual evaluation path is:

```text
Evaluation platform: ControlDeck
        |
        v
OpenCode runtime  <---- ExtendCodeAgent OpenCode integration
        |
        v
selected agent/model configuration
        |
        v
real repository task
        |
        v
objective verification/evidence
```

The arrow between ControlDeck and OpenCode belongs to ControlDeck.
The arrow between OpenCode and ExtendCodeAgent belongs to ExtendCodeAgent.
There is intentionally no ControlDeck <-> ExtendCodeAgent product interface.

A direct OpenCode invocation outside ControlDeck remains a valid and important control condition. A
capability that works only because of ControlDeck-specific behavior must not be described as a generic
OpenCode/ExtendCodeAgent capability.

## 3. Why ControlDeck is useful as a platform

ControlDeck already provides practical OpenCode execution, local model/provider selection, interactive
and headless workflows, job lifecycle, project selection and a real Python/TypeScript application on
which to run development tasks. This makes it useful for end-to-end evaluation without requiring
ExtendCodeAgent to build or own another host application.

The benefit is experimental convenience and realistic workload coverage, not architectural coupling.

## 4. Critical objections and mitigations

### Objection A — ControlDeck-only tuning can overfit

Mitigation:

1. Use ControlDeck as the primary evaluation platform and ControlDeck itself as the first rich task
   corpus.
2. Keep held-out ControlDeck tasks/prompts outside tuning.
3. Before a generic capability reaches `active-default`, repeat an accepted subset on at least one
   held-out repository using the same OpenCode runtime.
4. Where practical, repeat a small control outside ControlDeck with direct OpenCode invocation to
   detect platform-specific effects.
5. Do not add another harness merely to obtain generalization evidence.

### Objection B — platform effects can be mistaken for PI effects

ControlDeck job handling, OpenCode version, provider selection, model startup and project-copy behavior
can all change results.

Mitigation:

- record ControlDeck commit/version as environment metadata;
- pin and record ExtendCodeAgent commit, OpenCode version, model/provider, repository commit, workspace
  identity and PI mode;
- compare paired runs in the same environment;
- include direct OpenCode control runs where platform behavior may affect the metric;
- classify failures as evaluation-platform, OpenCode runtime, model/provider, PI adapter, PI core,
  task-selection, verification or performance;
- never credit a ControlDeck-only improvement as an ExtendCodeAgent capability gain.

### Objection C — managed/copied projects can break revision identity

If the evaluation platform copies/imports a project, Project Intelligence must treat the resulting
workspace as a distinct workspace unless an explicit relation proves otherwise.

Record source repository identity, managed-copy identity, Git SHA/worktree fingerprint and Twin
revision. Do not merge evidence merely because files are content-similar.

### Objection D — one model can distort the result

Every significant capability must be tested with the harness/agent/LLM combinations required by its
claim. A single favorable model result is not sufficient evidence.

## 5. Required comparison configurations

Use the smallest matrix that can actually prove or falsify the feature claim.

### OpenCode / ExtendCodeAgent modes

A. OpenCode native, ExtendCodeAgent absent/disabled
B. OpenCode + ExtendCodeAgent `off`
C. OpenCode + ExtendCodeAgent `shadow`
D. OpenCode + ExtendCodeAgent `advisory`
E. OpenCode + ExtendCodeAgent `active`

Run these primarily through ControlDeck where that platform provides the desired real workflow. Add a
direct OpenCode control when ControlDeck itself could materially influence the measured outcome.

For orchestration-specific competitive tests only, after the normal OpenCode baseline is stable:

F. OpenCode + OMO
G. OpenCode + OMO + ExtendCodeAgent

OMO remains optional and is never a release dependency.

### Model tiers

Use logical tiers rather than fixed product names:

1. `local-low` — deliberately weak/small local model;
2. `local-practical` — practical local coding/reasoning model;
3. `host-default` — current normal OpenCode model path when applicable;
4. `frontier` — functioning current frontier path when available and allowed.

The test plan may omit irrelevant combinations, but it must explain why those omissions cannot change
the adoption decision.

## 6. Harness / agent / LLM combination rule

No capability is accepted from unit tests, mocks, or one convenient model alone.

Examples:

- Weak-Local Evidence Protocol -> OpenCode + local-low and local-practical, repeated runs.
- Context selection -> OpenCode native/advisory/active across local-practical and at least one stronger
  model.
- Convergence/completion -> OpenCode agent execution plus objective test/build/runtime evidence;
  multiple model tiers when model reasoning can change the completion decision.
- PI-aware parallel work -> an OpenCode-compatible configuration that actually exposes distinct
  agent/workspace/task identities.
- OMO complementarity -> OpenCode+OMO versus OpenCode+OMO+ExtendCodeAgent on identical tasks.
- Project Evidence Memory -> repeated/cross-session tasks with changed-revision invalidation cases.

ControlDeck is a platform dimension in these experiments, not an ExtendCodeAgent adapter dimension.

## 7. Task corpus

### Primary ControlDeck corpus

Use real tasks from ControlDeck because it supplies Python backend, TypeScript/React frontend,
workflow/runtime behavior, model management and cross-boundary changes.

Required classes:

- locate/explain;
- bounded bug fix;
- multi-file refactor;
- API change with frontend/backend consumer impact;
- workflow/runtime defect;
- test selection;
- stale or insufficient verification evidence;
- UI/backend boundary diagnosis;
- architecture/migration decision;
- completion decision after implementation.

### Held-out ControlDeck set

Reserve tasks and paraphrased prompts not used to tune rules, thresholds or context profiles.

### Secondary held-out repositories

Before generic `active-default`, confirm a representative subset on at least a Python-heavy or
JS/TS-heavy held-out repository using the same OpenCode runtime. Use a mixed project when practical.
The purpose is anti-overfit evidence, not multi-harness support.

## 8. Metrics

Core outcomes:

- verified task success;
- tests/build/typecheck/lint/behavior correctness;
- unsupported claims;
- wrong/unnecessary edits;
- completion correctness;
- stale-evidence false acceptance;
- regression rate.

Efficiency:

- tool calls and file reads;
- input/context tokens;
- cached/prefix tokens when observable;
- output/reasoning tokens when observable;
- wall time, retries and timeouts;
- model escalations;
- OpenCode/PI startup overhead;
- CPU/RAM/DB growth where relevant.

PI-specific quality:

- context useful-item precision and missing-fact failures;
- Impact precision/recall;
- test-selection precision/recall;
- freshness/provenance correctness;
- task/capability selection precision/recall;
- worktree/cross-agent stale-context detection when applicable;
- Convergence false-positive/false-negative rate.

Platform-only metrics may be recorded for reproducibility, but they are not ExtendCodeAgent product
KPIs unless the capability claim directly depends on them.

## 9. Feature adoption states

Use explicit states:

`experimental -> shadow -> advisory -> active-scoped -> active-default`

or `deferred/rejected` when evidence does not justify cost.

## 10. Adoption gate

A capability advances only when all applicable conditions pass:

1. real OpenCode task evidence exists, normally using ControlDeck as the primary evaluation platform;
2. required harness/agent/LLM combinations were tested;
3. stochastic local models use repeated runs;
4. objective correctness does not regress on critical accepted tasks;
5. the gain is attributable to ExtendCodeAgent rather than ControlDeck/OpenCode/model/version changes;
6. overhead is bounded for tasks that do not benefit;
7. privacy/fallback/off-mode semantics remain correct;
8. confidence/freshness supports the requested rollout level;
9. held-out tasks do not show critical overfitting;
10. before generic `active-default`, held-out repository evidence confirms the capability is not
    ControlDeck-specific;
11. when platform influence is plausible, a direct OpenCode control does not contradict the claimed
    ExtendCodeAgent effect.

A feature may remain model-scoped or task-scoped when that is where evidence shows value.

## 11. Competitive adoption rule

For every idea inspired by Atomic/Claude/Codex/Cline/OMO, record:

- source idea;
- ExtendCodeAgent-specific problem addressed;
- smallest implementation;
- required runtime/agent/model combinations;
- baseline(s);
- expected measurable gain;
- actual result;
- decision: adopt, scope, defer or reject.

Competitive inspiration never establishes value by itself.

## 12. Current differentiated candidates

### Weak-Local Evidence Protocol

Evaluate primarily on OpenCode with local-low/local-practical models using ControlDeck tasks. Measure
success, structured-output validity, tokens, cache/prefix behavior, time and tool calls. Keep only
optimizations with measured benefit.

### Project Evidence Memory + PI Trace/Replay

Evaluate repeated maintenance tasks across sessions and revisions. It must improve project-specific
retrieval/verification/debugging while correctly invalidating stale evidence. Generic chat memory is
out of scope.

### Verification Intelligence 2.0

Use bug/API/refactor tasks where baseline test selection or completion is provably incomplete. Add only
the smallest missing signal that improves objective verification.

### PI-aware Parallel Development

Do not implement a team runtime. First prove OpenCode/OMO or another OpenCode-compatible path exposes
stable distinct task/workspace signals. Then evaluate semantic cross-workspace conflicts. If signals
are insufficient, defer the feature instead of adding host-specific orchestration.

## 13. Current runtime and platform policy

During current productization:

- **Production runtime target:** OpenCode only.
- **Primary evaluation platform:** ControlDeck.
- **Primary rich task corpus:** ControlDeck repository.
- **ExtendCodeAgent integration boundary:** OpenCode, not ControlDeck.
- **ControlDeck-specific intake/install/config IF:** owned entirely by ControlDeck and out of scope for
  ExtendCodeAgent.
- **Optional orchestration comparison:** OMO on OpenCode, only when relevant.
- **Second independent harness:** later portability proof, not a current development dependency.

A future Cline/Claude/Codex adapter remains valid architecture scope, but no current PR should add one
before the explicit portability gate.

## 14. Sequence impact

1. COMP-0 competitive strategy documentation.
2. RV-0 OpenCode baseline using ControlDeck as the primary evaluation platform.
3. RV-1 blocking **OpenCode / ExtendCodeAgent / model-provider** defects if measured. ControlDeck-only
   defects are reported to/handled by ControlDeck and are not ExtendCodeAgent production scope.
4. RA-0 minimum OpenCode runtime contract needed by task-aware PI.
5. TA-0 shadow planner.
6. WL-0 weak-local protocol if baseline evidence justifies it.
7. TA-1 advisory selection.
8. VI-0 verification/confidence/Convergence quality.
9. TA-2 bounded active.
10. TA-3 progressive expansion.
11. conditional Runtime Bridge / bounded deep analysis.
12. RV-FINAL OpenCode production baseline, ControlDeck primary plus held-out confirmation.
13. EM-0 Evidence Memory/Trace if not pulled earlier by measured need.
14. optional OMO complementarity benchmark.
15. RA-3 second-harness portability proof.
16. MA-0 PI-aware parallel/worktree intelligence when stable runtime signals exist.

## 15. Decision principle

**OpenCode is the product/runtime target. ControlDeck is an evaluation platform.**

Do not let experimental convenience create an architectural dependency. ExtendCodeAgent should work
with OpenCode according to its own runtime contract regardless of whether OpenCode is launched from
ControlDeck, directly from a terminal, or by another platform.
