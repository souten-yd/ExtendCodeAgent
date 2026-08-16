# Codex Productization Execution Guide

> **Consolidated 2026-08-16.** Agent working rules. Read order (section 1) and first task (section 4) are superseded by `docs/PI_MASTER_EXECUTION_PLAN.md` and `docs/handoff/NEXT_TASK.md`.

Status: execution instructions for post-PR-I productization
Date: 2026-08-14

## 0. Mission

Take the current ExtendCodeAgent implementation from feature-complete prototype/baseline to a production-capable OpenCode extension by measuring real behavior, fixing only high-value gaps, optimizing local-model and OpenCode usage, and proving the result with reproducible local evidence.

Do NOT resume broad feature expansion. Low-priority work is frozen unless a measured failure proves it necessary.

The primary optimization objective is:

> maximize correct task completion and verification quality per unit of tool calls, tokens, wall time, memory, and user configuration effort.

Secondary objectives:

- weak local models must remain first-class;
- practical local models should get most routine work done without frontier dependency;
- frontier models should work when configured but must not be required for basic correctness;
- OpenCode native behavior must remain a safe fallback;
- host-specific code must remain in adapters;
- all normal evaluation remains local-first.

## 1. Required read order

At the start of a new session read only:

1. `docs/handoff/CURRENT_HANDOFF.md`
2. `docs/handoff/NEXT_TASK.md`
3. `docs/PRODUCTIZATION_AND_MODEL_EVALUATION_PLAN.md`
4. the relevant slice of `docs/IMPLEMENTATION_EXECUTION_LOCAL_VALIDATION_PLAN.md`
5. source/tests for the active task
6. prior compact evidence for the feature under test

Do not repeatedly load the full historical planning set unless a design conflict requires it.

## 2. Handoff discipline

The project must remain resumable after token exhaustion, account switching, or agent replacement.

Maintain continuously:

- `docs/handoff/CURRENT_HANDOFF.md`
- `docs/handoff/NEXT_TASK.md`
- `docs/handoff/IMPLEMENTATION_LOG.md`
- `docs/handoff/DECISIONS.md`
- `docs/handoff/KNOWN_ISSUES.md`

Update handoff before and after every major evaluation slice and before starting any risky refactor.

`CURRENT_HANDOFF.md` must contain:

- branch/PR/base/latest commit;
- exact milestone and current task;
- completed/in-progress/not-started;
- exact files being changed;
- exact commands and results;
- OpenCode version;
- model/provider/profile names;
- feature modes/config used;
- benchmark/evaluation summary;
- known failures/limitations;
- uncommitted/temporary work;
- next exact action/files/commands;
- rollback path.

If context/token budget is low: stop new work, run the smallest useful tests, commit coherent work if possible, update handoff, and leave exact resume commands.

## 3. Branch and PR strategy

Use small evidence-driven PRs.

Recommended sequence:

- `agent/release-validation-baseline`
- `agent/opencode-productization` only if needed
- `agent/task-aware-intelligence` if required by baseline evidence
- `agent/evidence-quality` if required
- `agent/runtime-bridge` only if required
- `agent/deep-analysis` only if required
- `agent/release-validation-final`

Do not put all productization changes into one PR.

Each PR must state:

- measured problem;
- root cause classification;
- why existing code/config cannot solve it;
- smallest change selected;
- local validation;
- real-host/model evidence where applicable;
- performance/quality delta;
- limitations and rollback.

## 4. First task: baseline release validation

Start from current `main` after syncing.

Suggested local commands:

```bash
cd /home/souten/ExtendCodeAgent
git switch main
git pull --ff-only origin main
git status --short
tools/local/all-fast
tools/local/test-integration
tools/local/build
```

Create the release-validation branch only after existing main gates pass.

### 4.1 Capture environment

Record without secrets:

- OS/kernel;
- Python version;
- Node/Bun versions where used;
- OpenCode version;
- plugin/package version/commit;
- local LLM endpoints and logical profiles;
- exact model IDs actually tested;
- frontier provider/model availability;
- CPU/RAM/GPU if relevant to local model timing;
- repository commit SHAs.

Write compact metadata under `docs/evidence/final/`.

### 4.2 Validate current OpenCode integration before changing it

Run:

- plugin load;
- `pi.status`;
- symbol/reference/path/impact/test tools;
- MCP connect;
- MCP reconnect;
- file edit refresh;
- external edit refresh;
- rapid multi-file edits;
- restart/reopen persistence;
- off-mode inertness;
- shadow/advisory semantics;
- sidecar failure/restart;
- MCP-only fallback if supported.

Measure startup/load overhead and time-to-stable revision.

Do not optimize before reproducing current behavior.

## 5. Benchmark tasks

Create stable task definitions with objective expected outcomes. Store the definitions, not model transcripts.

Minimum tasks:

### T1 Locate implementation

Ask where a behavior is implemented and require file/symbol references.

Score:

- correct target;
- unsupported claims;
- tool calls;
- tokens/time.

### T2 Impact before change

Choose a known symbol/API and ask what must be reviewed if it changes.

Score against curated impacted files/symbols/tests.

### T3 Test selection

Use a bounded known change and compare selected tests against a known necessary set.

Measure precision/recall and fallback behavior.

### T4 Multi-file bug diagnosis

Use a reproducible defect or fixture whose root cause crosses more than one file.

Verify diagnosis independently.

### T5 Stale test/evidence

Use a fixture where implementation changed but test evidence is stale/partial.

Require the system not to declare safe completion.

### T6 Small refactor

Allow a small source edit. Compare unnecessary reads/edits, build/tests, and completion.

### T7 API consumer impact

Use an API/schema change with known consumers.

### T8 UI/browser diagnosis

Use a task where current static analysis may miss browser/API relationships. This is the runtime-bridge decision case.

### T9 Strategy

Use a medium architectural decision with measurable change scope/test burden/rollback differences.

### T10 Completion decision

Present current/stale/missing/conflicting evidence variants and verify correct convergence decisions.

## 6. Model matrix execution

### 6.1 Local-low

Use the available deliberately small local model. If `qwen3:0.6b` remains available, it is a valid continuity baseline; otherwise select an equivalent weak model and record it.

Critical scenarios must run at least five times in native/advisory/active where practical.

Track variance. Report success distribution, not only best run.

### 6.2 Local-practical

Use the practical local coding/reasoning model available on the machine. Existing 27B evidence may be repeated if the model is still available.

Run representative tasks at least three times per important mode.

### 6.3 Host-default

Resolve the current OpenCode default/host model at runtime. Do not assume the historical `opencode/big-pickle` identifier is unchanged.

Compare native and active on representative tasks with identical repository revision and task text.

### 6.4 Frontier

This is a release gate.

First test the frontier model natively in OpenCode with ExtendCodeAgent disabled. If native fails, classify provider path as unavailable and debug provider/auth separately; do not modify Project Intelligence core.

If native succeeds but adapter use fails, inspect adapter/provider shape and fix the adapter only.

Once a minimal adapter smoke passes, run at least three representative scenarios.

Never store keys/tokens in evidence.

## 7. Evaluation result classification

Every failed task should be classified as exactly one primary cause plus optional contributors:

- `MODEL_CAPABILITY`
- `MODEL_PROVIDER`
- `CONTEXT_MISSING`
- `CONTEXT_EXCESS`
- `GRAPH_FALSE_POSITIVE`
- `GRAPH_FALSE_NEGATIVE`
- `RUNTIME_BOUNDARY`
- `TEST_MAPPING`
- `STALE_EVIDENCE`
- `ROUTING`
- `TASK_SELECTION`
- `OPENCODE_ADAPTER`
- `SIDECAR_LIFECYCLE`
- `CONFIG_USABILITY`
- `PERFORMANCE`
- `OTHER`

Do not fix symptoms until the class is supported by evidence.

## 8. Local-model optimization loop

For each local failure:

1. verify deterministic facts are correct;
2. inspect whether the required fact was included;
3. inspect irrelevant fact count;
4. reduce/expand context before changing the model;
5. reduce task ambiguity and use structured outputs where supported;
6. verify reasoning/output bounds and timeout behavior;
7. only then consider routing/escalation changes.

Target progressive context:

- Stage 1: minimum symbols/path/tests;
- Stage 2: direct neighboring facts;
- Stage 3: transitive impact/runtime evidence;
- Stage 4: stronger model escalation if allowed.

Do not simply increase token budget until the task passes.

## 9. Task-aware controller implementation rule

Only implement after baseline evaluation shows that static profiles/manual modes cause measurable waste or failures.

Implement the smallest deterministic controller first.

Suggested domain contract:

```text
TaskIntent
RepositorySignals
ModelCapability
EvidenceAvailability
RiskSignals
    -> IntelligencePlan
```

`IntelligencePlan` should specify:

- capability list;
- context budget/profile;
- max graph depth/path count;
- runtime evidence requirement;
- Strategy/Convergence requirement;
- escalation policy;
- explanation/reasons.

No model call is required for first version.

Test examples:

- rename does not trigger Research/CFG;
- normal bug fix triggers impact/tests;
- UI bug can request runtime bridge only when current evidence is insufficient;
- architecture task may trigger Strategy/Convergence;
- security task may request on-demand DFG/Taint if implemented;
- privacy-deny prevents remote escalation.

## 10. Context engine optimization rule

Extend the existing engine; do not create a second context subsystem.

Required metrics per package:

- task/model profile;
- item count;
- token estimate/actual tokens if available;
- useful-item rate from post-task analysis;
- missing critical facts;
- confidence/provenance distribution;
- expansion stage.

Prefer ranking improvements and progressive expansion over increasing fixed limits.

Any new ranking feature must demonstrate improvement on at least one repeated real task without significant regression elsewhere.

## 11. Evidence/confidence work

Do not claim confidence values are probabilities unless validated.

Create a curated set and report precision/recall for high-value relation classes.

At minimum:

- definitions/references;
- resolved calls;
- uncertain `may_call`;
- imports/dependencies;
- test links;
- impact outputs.

Use this work to choose thresholds for:

- active context inclusion;
- active test selection;
- completion decisions;
- runtime bridge promotion.

Prefer threshold correction to complex calibration models.

## 12. Runtime bridge decision and implementation

Do not build a broad UI graph first.

Use T8 and additional real UI/API tasks to quantify current failure. If failures are caused by missing browser/API/runtime relationships and materially affect task success/test recall, implement a narrow bridge.

Candidate generic edges/evidence:

- `dispatches_event`;
- `handles_event`;
- `requests_route`;
- `handles_route`;
- `observed_call`;
- `observed_request`;
- `observed_response`;
- `runtime_registers`.

Framework adapters may discover those facts, but the core graph must remain framework-neutral.

Every runtime-derived fact requires source revision/freshness/provenance.

Compare before/after:

- impact recall;
- test-link recall;
- false positives;
- graph size;
- refresh/runtime overhead;
- actual task success.

If improvement is small, revert/defer the bridge instead of keeping complexity.

## 13. Deep analysis rule

CFG/DFG/Taint/State are not general backlog items. They are solutions to specific failures.

If a measured task requires deep analysis:

1. define the failing task/ground truth;
2. choose the smallest analysis type;
3. implement bounded symbol/neighborhood analysis;
4. make it on-demand and separately configurable;
5. measure analysis latency/memory and answer improvement;
6. cache only if repeated use justifies it;
7. do not add project-wide persistence by default.

Priority when evidence supports it:

1. DFG/Taint for data origin/security/validation;
2. CFG for control/exception/retry logic;
3. State/Event for workflow/state-machine repositories.

## 14. OpenCode productization checks

The integration should feel like one feature, not a collection of manual components.

Audit:

- install/bootstrap commands;
- plugin discovery/config path;
- Python sidecar dependency setup;
- sidecar automatic start/stop;
- stale PID/port recovery;
- status/error messages;
- feature-mode configuration;
- model role configuration;
- privacy configuration;
- database/storage location;
- reset/reindex command if necessary;
- upgrade compatibility behavior;
- clean disable/uninstall path.

Do not build a GUI unless evaluation shows configuration is otherwise unusable. Prefer good config defaults, health output, and a small number of commands/tools.

## 15. OpenCode optimization checks

Measure native vs extension on the same tasks.

Look for:

- reduced exploratory read/grep/LSP/tool calls;
- no suppression of required source inspection;
- no repeated duplicate context injection;
- no revision refresh feedback loops;
- no unnecessary background indexing while disabled;
- bounded sidecar CPU/memory while idle;
- plugin startup overhead within an acceptable measured range;
- graceful behavior when Project Intelligence is stale/building/unavailable.

If active mode causes regressions for a task/model class, change the controller/default policy rather than forcing active universally.

## 16. Performance gates

Record on representative repositories:

- cold index;
- no-change/cache-hit check;
- single-file refresh;
- broad-change refresh;
- time to stable revision after edit burst;
- query latency;
- context build latency;
- memory peak/idle if practical;
- DB+WAL size;
- startup overhead.

Generalize full-vs-incremental selection only from measurements. Do not assume incremental is inherently better.

## 17. Quality gates before merge

For every implementation PR:

1. focused unit tests;
2. architecture/boundary tests;
3. relevant integration tests;
4. `tools/local/all-fast`;
5. build;
6. relevant real OpenCode smoke;
7. relevant repeated model evaluation if model behavior changed;
8. benchmark if performance-sensitive;
9. `git diff --check`;
10. handoff/status/evidence updated.

No GitHub CI is required unless local reproduction is impossible for a necessary gate.

## 18. Token-efficient Codex behavior

Codex itself must conserve tokens:

- inspect exact symbols/files instead of repeatedly reading directories;
- use existing evidence and handoff rather than rediscovering prior facts;
- search callers/tests before editing;
- avoid duplicating contracts/services;
- avoid long comments/docstrings describing obvious code;
- add only tests that protect meaningful behavior;
- run focused tests before broad suites;
- keep raw model transcripts local;
- record compact results in JSON/Markdown;
- commit coherent slices so another agent can continue.

## 19. Do not do these things

- do not implement all deferred graph types;
- do not port more KasaneCore subsystems for completeness;
- do not rewrite working graph/twin/router/context systems;
- do not add a second router/controller/context engine;
- do not hard-code model vendors in core;
- do not make frontier mandatory for local correctness;
- do not send source remotely when privacy policy forbids it;
- do not hide unavailable provider paths;
- do not mark a single model run as statistically stable;
- do not use GitHub CI for real model evaluation;
- do not optimize synthetic latency while real coding tasks regress.

## 20. Final release decision

After the final validation PR, classify each major capability:

- `PRODUCTION_DEFAULT`
- `PRODUCTION_OPTIONAL`
- `ADVISORY_ONLY`
- `EXPERIMENTAL`
- `DEFERRED`

Expected direction, subject to evidence:

- Project Model/semantic/impact: production default;
- bounded Context/Test/Runtime evidence: production default or model/task-aware default;
- Strategy/Convergence: production optional/task-aware;
- Research: optional;
- runtime bridge: optional/task-aware if proven;
- DFG/Taint/CFG: experimental/on-demand if implemented;
- full UI graph: deferred.

Set `PRODUCTION-CAPABLE BASELINE COMPLETE` only after the required release gates in `PRODUCTIZATION_AND_MODEL_EVALUATION_PLAN.md` are actually supported by current evidence.
