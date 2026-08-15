# Next Task

Updated: 2026-08-16 (Asia/Tokyo)

The immediate product/runtime target is **OpenCode**. Current ControlDeck usage is treated as normal
OpenCode usage; ControlDeck is not a separate harness, adapter target, or evaluation variant unless a
future deep integration measurably changes OpenCode execution semantics relevant to ExtendCodeAgent.

Canonical execution documents:

1. `docs/PRODUCTIZATION_AND_MODEL_EVALUATION_PLAN.md`
2. `docs/COMPETITIVE_ANALYSIS_AND_FEATURE_GAP_ROADMAP.md`
3. `docs/OPENCODE_VALIDATION_AND_ADOPTION_PLAN.md`
4. `docs/TRANSPARENT_PI_ORCHESTRATION_PLAN.md`
5. `docs/RUNTIME_ADAPTER_ARCHITECTURE_PLAN.md`
6. `docs/CODEX_PRODUCTIZATION_EXECUTION_GUIDE.md`
7. `docs/handoff/CURRENT_HANDOFF.md`

## Product boundary

ExtendCodeAgent integrates with **OpenCode** through the existing OpenCode adapter/plugin/MCP
boundary. The host-neutral Project Intelligence core remains portable, but no second harness is a
current production dependency.

ControlDeck currently consumes OpenCode essentially as-is. Do not introduce ControlDeck-specific
adapters, install/discovery protocols, lifecycle behavior, configuration contracts, UI integration, or
special evaluation logic into ExtendCodeAgent.

Describe the current product as:

> a host-neutral Project Intelligence and Verification Runtime with OpenCode as its current reference
> and production-target runtime.

ControlDeck may be where OpenCode is launched today, and the ControlDeck repository may be one useful
real-world benchmark project, but neither is part of the ExtendCodeAgent product boundary.

## Mandatory evidence rule

A capability is not adopted because source code or unit tests exist. Every new or materially changed
capability MUST be evaluated with the OpenCode / agent / LLM combinations needed to prove its claim.

Primary mode comparison:

- OpenCode native / ExtendCodeAgent absent or disabled;
- `off`;
- `shadow`;
- `advisory`;
- `active` when permitted.

ControlDeck-launched and directly launched OpenCode are the same condition unless measured evidence
shows a material semantic difference.

Use model tiers according to the claim:

- local-low;
- local-practical;
- host/default when applicable;
- frontier when functioning/allowed.

Repeat stochastic local-model runs. A feature that benefits only one model tier may remain only with
an explicit scoped rollout.

## Anti-overfit rule

Do not tune product behavior against only one repository.

- Use real tasks from multiple representative repositories.
- ControlDeck is one useful mixed Python/JS/TS project, not the privileged acceptance target.
- Reserve held-out tasks/prompts and at least one held-out repository outside tuning.
- Before generic `active-default`, repeat an accepted subset on held-out repository work with the same
  OpenCode runtime.
- Do not add another harness merely to prove repository generalization.

Workspace/revision identity remains explicit for every repository/worktree/copy. Never merge
Twin/runtime evidence from different workspaces merely because files look similar.

## Competitive decisions

Adopt only when measured useful:

- stable-prefix-aware / bounded structured evidence for weak local models;
- deterministic candidate reduction and decision envelopes;
- Project Evidence Memory with provenance/revision/invalidation;
- compact PI trace/replay without raw private reasoning transcripts;
- stronger Verification Intelligence and evidence-backed completion;
- runtime-observed worktree/subagent/task identity for future PI-aware parallel development.

Delegate rather than reimplement:

- generic team/multi-agent orchestration;
- background execution/scheduling;
- browser/desktop automation;
- shell/edit/patch;
- sandbox/permissions;
- provider/model management;
- generic session recovery;
- worktree/checkpoint engines;
- host UI/integration plumbing.

## Immediate sequence

1. Start RV-0 from synchronized `main` after this correction is merged.
2. Run local lint/typecheck/unit/integration/build before production changes.
3. Record ExtendCodeAgent commit, OpenCode version, model/provider profiles, repository/workspace
   identity and hardware/runtime environment.
4. Establish OpenCode-native baselines before PI optimization.
5. Revalidate OpenCode adapter/plugin/MCP/edit/restart/reconnect/off/shadow/advisory paths.
6. Reproduce frontier/provider failures with PI disabled first; fix only measured OpenCode/ECA/provider
   defects.
7. Build versioned multi-repository real-task and held-out task sets. Compare required
   runtime/mode/model combinations with objective verification.
8. Produce the RV-0 gap report and classify each failure as OpenCode runtime, model/provider, PI
   adapter, PI core, task selection, verification or performance.
9. RA-0: formalize only OpenCode signals consumed by Task-aware PI/Verification.
10. TA-0: deterministic shadow planning only.
11. WL-0: weak-local protocol only if measured failures justify it.
12. TA-1: advisory automatic capability/context selection.
13. VI-0: confidence, Test Intelligence and Convergence/completion quality; add 2.0 features only for
    measured failures.
14. TA-2: bounded active for accepted task/relation/model scopes.
15. TA-3: progressive expansion after repeated evidence.
16. Runtime Bridge or bounded DFG/Taint/CFG only when repeated high-value OpenCode tasks prove a
    missing relation is the smallest fix.
17. RV-FINAL: OpenCode production baseline across representative + held-out repositories; no new
    feature scope.
18. Project Evidence Memory/PI Trace remains P1 unless cross-session evidence loss is a release blocker.
19. Optional OpenCode+OMO comparisons only for relevant orchestration claims.
20. RA-3 second-harness proof only after the OpenCode production baseline.
21. PI-aware parallel/worktree work only after a stable OpenCode-compatible runtime signal path is
    demonstrated; start advisory/detection-only.

## Future ControlDeck rule

Do not model hypothetical future ControlDeck integration now. If ControlDeck later changes OpenCode
session/tool/context/model/workspace/verification/multi-agent semantics, measure that implementation
first and only then decide whether `ControlDeck + OpenCode` is a distinct evaluation condition.

## Feature adoption states

`experimental -> shadow -> advisory -> active-scoped -> active-default`

or `deferred/rejected` when evidence does not justify cost.

## Resume

```bash
cd /home/souten/ExtendCodeAgent
git switch main
git pull --ff-only origin main
git status --short
tools/local/all-fast
tools/local/test-integration
tools/local/build
git switch -c agent/release-validation-baseline
```

Update `CURRENT_HANDOFF.md` after each major OpenCode/model/controller evaluation.
