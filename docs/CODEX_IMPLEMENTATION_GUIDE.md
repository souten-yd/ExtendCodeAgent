# ExtendCodeAgent — Codex Implementation Guide

Status: execution rules for implementation agents
Date: 2026-08-13

## 1. Mission

Implement ExtendCodeAgent incrementally with minimal token waste, minimal duplication, strong local validation, and strict preservation of OpenCode/KasaneCore authority boundaries.

Codex must treat existing code as the first implementation candidate. Search, inspect, adapt, consolidate, or delete duplication before creating new subsystems.

The implementation must remain effective with both weak local LLMs and frontier models. Do not let high-end model capability hide poor interfaces, excessive context, or missing deterministic analysis.

## 2. Required read order per task

Read only what is necessary for the active slice:

1. `docs/PROJECT_INTELLIGENCE_MASTER_PLAN.md` relevant section.
2. `docs/KASANECORE_MIGRATION_AUDIT.md` relevant component classification.
3. `docs/IMPLEMENTATION_EXECUTION_LOCAL_VALIDATION_PLAN.md` active PR/milestone section.
4. `docs/CURRENT_STATUS.md`.
5. target source, direct callers, tests, and dependencies.

Do not repeatedly load all planning documents into context.

## 3. Investigation before implementation

For every non-trivial change:

- search for existing symbols and analogous behavior;
- inspect direct callers/consumers;
- identify existing tests and fixtures;
- check whether KasaneCore already implements the required algorithm/contract;
- determine whether OpenCode/LSP/Git/MCP/test framework already supplies the primitive;
- classify work as `REUSE`, `ADAPT`, `CONSOLIDATE`, `REPLACE`, or `NEW`;
- avoid parallel implementations unless a compatibility adapter is deliberately temporary.

## 4. Code quality / token efficiency

Prefer:
- small explicit data structures;
- pure functions for policies/algorithms;
- coarse interfaces at real system boundaries;
- shared mapping/conversion helpers;
- deterministic logic instead of model calls;
- short comments describing non-obvious invariants only;
- parameterized tests and fixture builders;
- incremental migrations rather than broad rewrites.

Avoid:
- generated boilerplate abstractions;
- one interface per tiny service;
- duplicate DTOs with only naming differences;
- wrappers that add no policy or compatibility value;
- speculative future-provider code;
- broad formatting/refactoring unrelated to the active PR;
- verbose documentation repeated in source comments;
- model prompts containing repository content that Project Graph can supply structurally.

## 5. Model-aware implementation rule

No domain feature may require a frontier model to function.

Implement in this order:

```text
deterministic algorithm
-> parser/LSP/runtime evidence
-> small structured local-model assist when useful
-> host/frontier reasoning only when ambiguity/risk warrants it
```

All model calls must go through a model-routing port and logical role. Never call a named vendor/model directly from graph/twin/impact/test/strategy/convergence domain code.

Model behavior must support:
- weak/low-context local model;
- practical medium local model;
- OpenCode host/default model;
- frontier model;
- local-only privacy mode;
- host-only mode;
- explicit no-fallback mode.

For weak models, reduce problem size before adding prompt instructions: use graph facts, candidate filtering, compact schemas, single-purpose calls, and lower context budgets.

For frontier models, permit richer synthesis but preserve the same deterministic evidence, privacy policy, and completion rules. Do not make a stronger model an excuse to bypass tests or provenance.

## 6. Configuration rule

Every major feature must be wired through the centralized resolved configuration/capability policy. Do not introduce independent environment-variable checks inside feature modules.

New configurable behavior requires:
- default;
- validation;
- project/user override semantics;
- tests for disabled and enabled paths;
- safe behavior when configuration is invalid.

Model/provider settings must be role-based and endpoint-configured. Exact model IDs belong in config, never in domain source.

## 7. Local-first validation sequence

Run the cheapest relevant checks first:

```text
focused unit
-> affected component
-> affected integration
-> local benchmark/E2E when behavior warrants it
-> real OpenCode test at integration milestones
-> real LLM A/B only at designated milestone gates
```

Do not use GitHub Actions to debug ordinary implementation failures.

Do not require internet/model access for unit or normal integration suites.

## 8. Real LLM evaluation discipline

Real-LLM evaluation must be reproducible enough to compare trends:

- fixed scenario prompt/task;
- fixed repository revision;
- recorded OpenCode version;
- recorded ExtendCodeAgent config;
- recorded model/provider identifier;
- same tool permissions;
- same timeout/retry budget;
- compare native/off/shadow/advisory/active where relevant.

At minimum, milestone evaluation should cover a weak local profile and a strong host/frontier profile when both are available. Use the same task and ground truth so improvements are attributable to Project Intelligence rather than model class alone.

Store result summaries, not huge transcripts, unless a transcript is necessary to explain a failure.

## 9. PR discipline

One PR should implement one coherent milestone slice. Before opening/merging:

- inspect diff for unnecessary new code;
- verify no direct OpenCode types leaked into core;
- verify disabled mode;
- verify relevant local tests;
- record benchmark/E2E evidence when required;
- update `CURRENT_STATUS.md` and decisions when architecture changed;
- identify known limitations truthfully.

Do not merge a PR whose only proof is a design document or mocked test when the acceptance criteria require real OpenCode/runtime evidence.

## 10. Stop / reconsider conditions

Stop expanding the current approach and document/reassess if:

- a KasaneCore port requires copying broad Atlas-specific infrastructure;
- an abstraction has only one trivial implementation and complicates usage;
- a graph feature cannot provide reliable provenance/confidence;
- incremental refresh is slower than practical full rebuild for target scale;
- a feature increases tokens/tool calls without improving task outcomes;
- weak local models become materially worse because context is too complex;
- frontier-model success hides failures in deterministic/local-model paths;
- OpenCode API changes require edits outside the adapter boundary;
- Python sidecar lifecycle/packaging cost outweighs reuse benefit;
- real tests contradict design assumptions.

## 11. Required implementation order

Do not skip ahead merely because later functionality is more visible.

1. Foundation contracts/config/model-router contracts/local harness.
2. Graph revision/store/source snapshot.
3. Structural/Python semantic/path/impact.
4. OpenCode adapter + MCP advisory tools.
5. Context/Test/runtime evidence.
6. Blueprint/Convergence.
7. Live model routing + Strategy.
8. JS/TS/framework/deep graph expansion.
9. Research/project-level convergence.

Later phases may be reordered only with documented evidence that dependencies permit it.

## 12. Completion report template

At the end of each Codex work package record:

```text
Goal:
Classification: REUSE / ADAPT / CONSOLIDATE / REPLACE / NEW
Existing code inspected:
Changed files:
Behavior added/changed:
Feature flags/config affected:
Local commands and exact results:
Benchmark/E2E evidence:
Real OpenCode/LLM evidence, if required:
Model profiles evaluated:
Unavailable checks:
Performance/token observations:
Known limitations:
Rollback/revert path:
Next recommended slice:
```

Evidence must distinguish deterministic test success from real-host/model validation.
