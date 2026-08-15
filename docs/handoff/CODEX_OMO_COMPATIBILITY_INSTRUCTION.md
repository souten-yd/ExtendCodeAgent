# Codex Instruction — ExtendCodeAgent development + OMO coexistence

Status: active handoff
Date: 2026-08-16

## Role

You own **ExtendCodeAgent development** and the technical evaluation of **OpenCode + OMO + ExtendCodeAgent**.

You do **not** implement ControlDeck installation/UI/stack-management code. ControlDeck independently consumes ordinary OpenCode/ECA/OMO releases and will use compatibility evidence produced here.

## Read first

1. `docs/OMO_COEXISTENCE_AND_COMPATIBILITY_PLAN.md`
2. `docs/OPENCODE_VALIDATION_AND_ADOPTION_PLAN.md`
3. `docs/COMPETITIVE_ANALYSIS_AND_FEATURE_GAP_ROADMAP.md`
4. `docs/RUNTIME_ADAPTER_ARCHITECTURE_PLAN.md`
5. `docs/TRANSPARENT_PI_ORCHESTRATION_PLAN.md`
6. `docs/PRODUCTIZATION_AND_MODEL_EVALUATION_PLAN.md`
7. `docs/handoff/NEXT_TASK.md`
8. `docs/handoff/CURRENT_HANDOFF.md`

Current product/runtime target is OpenCode. Keep Project Intelligence host-neutral and do not build a second harness.

## Immediate objectives

### A. Continue ECA productization

Follow the current RV/RA/TA/VI/WL/EM roadmap and evidence gates. A capability is not adopted merely because it is implemented: verify its effect with the OpenCode/agent/LLM combinations required by the claim, repeated stochastic-model runs where needed, objective correctness, held-out tasks/repositories, bounded overhead, privacy/fallback and truthful degradation.

### B. Establish OMO coexistence as a formal compatibility gate

Compare at minimum:

1. OpenCode native
2. OpenCode + ECA
3. OpenCode + OMO
4. OpenCode + ECA + OMO

Use exact OpenCode/ECA/OMO versions and record the tuple. Do not assume `latest` compatibility.

Test both plugin orders initially. If order is irrelevant, choose and document one deterministic order. If order matters, record the required order as compatibility evidence.

### C. Conflict matrix

Explicitly test and classify interactions in these areas:

- plugin initialization/disposal;
- tool IDs and duplicate/missing tool exposure;
- `event` hooks;
- `tool.execute.before` / `tool.execute.after` ordering and mutation;
- ECA runtime observation accuracy when OMO wraps/changes tool execution;
- message/system/context transforms;
- compaction/context-pruning behavior;
- model/provider routing, fallback and parameters;
- session lifecycle/recovery;
- file/watch/LSP events and revision freshness;
- ECA Task-aware context injection once active automation exists;
- verification/Convergence semantics;
- privacy and source-code routing policy;
- failure/degraded/native-fallback behavior;
- startup, latency, tokens, tool calls, memory and DB overhead.

The current ECA plugin is intentionally observation-oriented and `pi_*`-namespaced; preserve that low-conflict posture unless evidence justifies change.

### D. Team Mode is a separate gate

Do not certify OMO Team Mode from single-agent coexistence.

Only after basic coexistence passes, evaluate OpenCode + OMO Team Mode + ECA with real distinct agent/task/worktree identities. Verify Twin/workspace separation, stale-context detection, cross-worktree evidence, runtime observation attribution and merge/replan safety. If OpenCode/OMO does not expose stable identities, defer PI-aware parallel behavior rather than inventing a team runtime inside ECA.

### E. Fix ownership

When a failure is found, classify it first as:

- OpenCode runtime;
- ECA adapter/core;
- OMO behavior;
- model/provider;
- configuration/plugin order;
- genuine interaction defect.

Fix ECA only when the defect belongs to ECA or a small generic compatibility adaptation is justified. Do not fork OMO/OpenCode or add ControlDeck-specific interfaces.

## Evidence and output

Produce machine-readable and human-readable compatibility evidence containing:

- exact version tuple and plugin order;
- repository/task/model profile;
- mode (`off/shadow/advisory/active`);
- component health and tool/agent visibility;
- hook/transform conflict findings;
- verified task result and tests/build/runtime evidence;
- performance/token/tool-call deltas;
- known limitations;
- decision: `incompatible`, `degraded`, `compatible`, or `recommended`;
- whether OMO Team Mode is separately certified.

A `recommended` tuple requires repeated real OpenCode task evidence and no critical regression. Make this output easy for an external distributor such as ControlDeck to consume, but do not implement ControlDeck logic here.

## Completion rule

Do not claim ECA+OMO compatibility from plugin load alone. Basic coexistence is accepted only when both products retain their intended behavior under real OpenCode tasks, ECA evidence remains truthful, no critical hook/context/model interaction is found, native fallback remains functional, and the accepted version tuple is reproducible.
