# ControlDeck-first OpenCode Validation and Adoption Plan

Status: canonical immediate validation policy
Date: 2026-08-16
Primary runtime: OpenCode
Primary integration host: ControlDeck

## 1. Decision

ExtendCodeAgent remains architecturally host-neutral, but productization is **OpenCode-first**.
The first real user-facing integration and acceptance environment is the OpenCode feature already
implemented in `souten-yd/ControlDeck`.

This is deliberate focus, not architectural retreat:

- Core contracts remain runtime-neutral.
- OpenCode remains the reference and only production-target runtime during the current phase.
- ControlDeck provides the first end-to-end host for real daily-use validation.
- Other harnesses are studied for ideas and future adapter requirements, but they are not current
  product targets.
- A second runtime adapter is deferred until the OpenCode baseline is production-capable and the
  generic adapter boundary has proven useful.

## 2. Why ControlDeck first

ControlDeck already isolates OpenCode as an opt-in feature, has a generic CodeAgent boundary, supports
headless jobs and interactive TUI use, can select local OpenAI-compatible model endpoints, and owns job
lifecycle/cancel/progress. This makes it a practical end-to-end test host without requiring a new
harness or UI.

The validation target is therefore not a synthetic sidecar smoke alone. It is:

```text
ControlDeck
  -> OpenCode feature/runtime
  -> ExtendCodeAgent OpenCode adapter
  -> Project Intelligence
  -> selected LLM/model route
  -> real repository task
  -> objective verification/evidence
```

## 3. Critical objections and mitigations

### Objection A — ControlDeck-only tuning can overfit

A feature that improves only tasks used to design it is not a general PI capability.

Mitigation:

1. ControlDeck is the **primary** project and integration environment.
2. Keep a held-out ControlDeck task set that cannot be used for tuning rules.
3. After a feature passes ControlDeck, run a small held-out repository set through the **same OpenCode
   runtime** before enabling the feature by default.
4. Do not add another harness merely to obtain generalization evidence.

### Objection B — ControlDeck can confound host improvements with PI improvements

ControlDeck job lifecycle, provider management, OpenCode updates, and model changes can alter results.

Mitigation:

- pin and record ControlDeck commit, ExtendCodeAgent commit, OpenCode version, model/provider,
  repository commit and PI mode for every accepted run;
- compare paired runs from the same environment;
- classify failures as ControlDeck host, OpenCode runtime, model/provider, PI adapter, PI core,
  task-selection or verification failures;
- do not credit a ControlDeck/OpenCode fix as a PI gain.

### Objection C — copied/managed projects can break revision identity

ControlDeck headless flows may operate on a managed/imported project rather than the user's original
working tree. PI must never associate evidence from one workspace with another solely because content
looks similar.

Mitigation:

- use explicit project/workspace identity and exact Git SHA/worktree fingerprint;
- for reproducible benchmarks, create fixed clones/fixtures under ControlDeck's managed project root;
- record source repository and managed-copy identity separately;
- never reuse Twin/runtime evidence across copied workspaces unless an explicit import relation exists.

### Objection D — one LLM can make a feature look better or worse than it is

Mitigation: every significant PI feature is evaluated with the necessary runtime/agent/model
combinations, not with a single model result.

## 4. Required comparison configurations

Use the smallest matrix needed for the feature under test. The baseline set is:

### Runtime / extension modes

A. ControlDeck -> OpenCode native, ExtendCodeAgent absent/disabled
B. ControlDeck -> OpenCode + ExtendCodeAgent `off`
C. ControlDeck -> OpenCode + ExtendCodeAgent `shadow`
D. ControlDeck -> OpenCode + ExtendCodeAgent `advisory`
E. ControlDeck -> OpenCode + ExtendCodeAgent `active`

For orchestration-specific competitive tests only, after the normal OpenCode baseline is stable:

F. OpenCode + OMO
G. OpenCode + OMO + ExtendCodeAgent

OMO is optional and must not become a release dependency.

### Model tiers

Evaluate logical tiers rather than hard-coding product names:

1. `local-low` — deliberately weak/small local model;
2. `local-practical` — practical local coding/reasoning model;
3. `host-default` — current normal OpenCode model path if applicable;
4. `frontier` — functioning current frontier path when available and allowed.

A feature need not run the full cross-product when the model/runtime dimension is irrelevant. The test
plan must state why omitted combinations cannot change the adoption decision.

## 5. Harness / agent / LLM combination rule

Every new or materially changed intelligence capability MUST identify the combination required to
prove its claimed value.

Examples:

- Weak-Local Evidence Protocol -> OpenCode + local-low and local-practical, repeated runs.
- Context selection -> OpenCode native/advisory/active across local-practical and at least one stronger
  model to prove PI is not merely compensating for one weak model.
- Convergence/completion gate -> OpenCode agent execution + objective test/build/runtime evidence;
  model diversity is required when completion reasoning can affect the result.
- PI-aware parallel work -> a runtime configuration that actually creates distinct agent/worktree/task
  identities; a single sequential agent cannot validate the feature.
- OMO complementarity -> OpenCode+OMO versus OpenCode+OMO+E on the same parallel/background task.
- Project Evidence Memory -> repeated/cross-session tasks with and without memory; same source revision
  plus changed-revision invalidation cases.

No feature is accepted from unit tests or mocked adapters alone.

## 6. Task corpus

### Primary ControlDeck corpus

Use real tasks drawn from ControlDeck's Python backend, TypeScript/React frontend, workflow engine,
OpenCode integration, model management and cross-boundary behavior.

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

Reserve tasks and paraphrased prompts that are not used to tune classifier rules, thresholds or
context profiles. Passing the tuning set alone cannot enable `active` by default.

### Secondary held-out repositories

After ControlDeck passes, use a small set representing at least:

- Python-heavy code;
- JS/TS-heavy code;
- mixed project if practical.

Use OpenCode for these runs as well. Their purpose is anti-overfit evidence, not multi-harness support.

## 7. Metrics

A capability claim must be tied to objective metrics appropriate to the feature.

Core outcome metrics:

- verified task success;
- tests/build/typecheck/lint or behavior result;
- unsupported/fabricated claims;
- wrong/unnecessary edits;
- completion correctness;
- stale-evidence false acceptance;
- regression rate.

Efficiency metrics:

- tool calls;
- file reads;
- input/context tokens;
- cached/prefix tokens when observable;
- output/reasoning tokens when observable;
- wall time;
- retries/timeouts;
- model escalations;
- startup/sidecar overhead;
- CPU/RAM/DB growth where relevant.

PI-specific quality metrics:

- context useful-item precision and missing-fact failures;
- Impact precision/recall;
- test-selection precision/recall;
- freshness/provenance correctness;
- task/capability selection precision/recall;
- worktree/cross-agent stale-context detection when applicable;
- Convergence false-positive/false-negative rate.

## 8. Feature adoption states

A feature is not simply implemented/not implemented. Use these states:

- `experimental` — implementation exists, evidence insufficient;
- `shadow` — executes/records but does not influence the agent;
- `advisory` — exposed to agent/user but not authoritative;
- `active-scoped` — active only for accepted task/relation/model scopes;
- `active-default` — enabled by default for its supported scope;
- `deferred` — plausible but insufficient value;
- `rejected` — measured cost/complexity/regression outweighs value.

## 9. Adoption gate

A capability may move forward only when all applicable conditions pass:

1. real ControlDeck-hosted OpenCode task evidence exists;
2. claimed LLM/harness/agent combinations were actually tested;
3. repeated runs are used for stochastic local models;
4. objective correctness does not regress on critical accepted tasks;
5. improvement is attributable to the capability rather than a host/model/version change;
6. overhead is bounded for tasks that do not benefit;
7. privacy/fallback/off-mode semantics remain correct;
8. confidence/freshness is sufficient for the requested rollout level;
9. a held-out task set does not show critical overfitting;
10. before `active-default`, at least one secondary held-out repository confirms the capability is not
   ControlDeck-specific, unless the capability is intentionally ControlDeck-specific integration code.

A feature that improves only one model tier may still be kept, but rollout must be model-scoped and the
reason must be explicit.

## 10. Comparative adoption rule

Competitive inspiration does not establish value. For every adopted idea from Atomic/Claude/Codex/
Cline/OMO, record:

- source idea;
- ExtendCodeAgent-specific problem it addresses;
- smallest implementation;
- runtime/model combinations needed to test it;
- baseline(s);
- measurable expected gain;
- actual result;
- decision: adopt, scope, defer or reject.

This prevents the roadmap from becoming a feature collection.

## 11. Immediate application to the competitive roadmap

### Weak-Local Evidence Protocol

Primary proof: ControlDeck + OpenCode on ControlDeck tasks with local-low/local-practical. Compare
native/off/advisory/active and measure success, structured-output validity, tokens, time and tool calls.
Do not enable stable-prefix-specific optimizations if the current provider/runtime cannot demonstrate a
cache or reliability benefit.

### Project Evidence Memory + PI Trace/Replay

Primary proof: repeated ControlDeck maintenance tasks across sessions and source revisions. It must
improve retrieval/verification or debugging while correctly invalidating stale evidence. Generic chat
memory remains out of scope.

### Verification Intelligence 2.0

Primary proof: ControlDeck bug/API/refactor tasks where baseline test selection or completion is
provably incomplete. Add only the smallest missing stale/mock/flaky/requirement/mutation signal.

### PI-aware Parallel Development

Do not implement merely because other harnesses support teams. First prove OpenCode/OMO or another
OpenCode-compatible execution path exposes stable distinct task/workspace signals. Then test semantic
cross-worktree conflicts on ControlDeck. If OpenCode cannot expose enough identity, defer rather than
creating a team runtime inside ExtendCodeAgent.

## 12. Current runtime expansion policy

During the current productization phase:

- **Production target:** OpenCode only.
- **Primary end-to-end host:** ControlDeck OpenCode integration.
- **Reference repository:** ControlDeck first, then held-out repositories.
- **Optional orchestration comparison:** OMO on OpenCode, only for relevant features.
- **Second independent harness:** architecture proof after the OpenCode production baseline, not a
  current feature-development dependency.

A future Cline/Claude/Codex adapter remains valid architectural scope, but no current PR should add one
unless the explicit RA-3 gate is reached.

## 13. Sequence impact

This validation policy changes the roadmap order as follows:

1. COMP-0 competitive strategy documentation.
2. RV-0 ControlDeck-first OpenCode baseline and environment capture.
3. RV-1 blocking ControlDeck/OpenCode/provider/lifecycle repair if measured.
4. RA-0 minimum OpenCode runtime contract needed by task-aware PI.
5. TA-0 shadow planner.
6. WL-0 weak-local protocol if baseline evidence justifies it.
7. TA-1 advisory selection.
8. VI-0 verification/confidence/Convergence quality.
9. TA-2 bounded active.
10. TA-3 progressive expansion.
11. conditional Runtime Bridge / bounded deep analysis.
12. RV-FINAL OpenCode production baseline, with ControlDeck primary + held-out repo confirmation.
13. EM-0 Evidence Memory/Trace if not pulled earlier by measured need.
14. optional OMO complementarity benchmark.
15. RA-3 second-harness architectural proof.
16. MA-0 PI-aware parallel/worktree intelligence when a stable runtime signal path exists.

## 14. Decision principle

OpenCode focus is a product decision; host neutrality is an architecture decision. They are not in
conflict.

Do not pay the implementation and validation cost of several harnesses before the differentiated PI
capabilities are proven on one real runtime. Conversely, do not let ControlDeck/OpenCode-specific
convenience leak into the core contracts in a way that blocks future adapters.
