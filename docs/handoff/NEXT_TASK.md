# Next Task

Updated: 2026-08-16 (Asia/Tokyo)

The immediate product/runtime target is **OpenCode**. ControlDeck is the **primary evaluation
platform**, not an ExtendCodeAgent integration target. ExtendCodeAgent remains architecturally
host-neutral, while no second harness is a current production dependency.

Canonical execution documents:

1. `docs/PRODUCTIZATION_AND_MODEL_EVALUATION_PLAN.md`
2. `docs/COMPETITIVE_ANALYSIS_AND_FEATURE_GAP_ROADMAP.md`
3. `docs/CONTROLDECK_OPENCODE_VALIDATION_AND_ADOPTION_PLAN.md`
4. `docs/TRANSPARENT_PI_ORCHESTRATION_PLAN.md`
5. `docs/RUNTIME_ADAPTER_ARCHITECTURE_PLAN.md`
6. `docs/CODEX_PRODUCTIZATION_EXECUTION_GUIDE.md`
7. `docs/handoff/CURRENT_HANDOFF.md`

## Product boundary

ExtendCodeAgent integrates with OpenCode through the OpenCode adapter/plugin/MCP boundary.
ControlDeck independently owns any installation, launch, configuration, UI, job-management or intake
mechanism used to make OpenCode/ExtendCodeAgent available in ControlDeck.

ExtendCodeAgent MUST NOT add a ControlDeck-specific adapter, install protocol, discovery API,
lifecycle manager, provider contract, configuration schema or UI integration.

Describe the current product precisely as:

> a host-neutral Project Intelligence and Verification Runtime with OpenCode as its current reference
> and production-target runtime; ControlDeck is a primary real-world evaluation platform.

## Mandatory evidence rule

A capability is not adopted because implementation or unit tests exist. Every new or materially
changed capability MUST be evaluated with the OpenCode/agent/LLM combinations needed to prove its
claimed benefit.

Primary mode comparison:

- OpenCode native / ExtendCodeAgent absent or disabled;
- `off`;
- `shadow`;
- `advisory`;
- `active` when permitted.

Run these mainly through ControlDeck for realistic workflows. When ControlDeck behavior could affect a
metric, add a direct OpenCode control run. ControlDeck platform behavior must never be credited as an
ExtendCodeAgent gain.

Use model tiers according to the claim:

- local-low;
- local-practical;
- host/default when applicable;
- frontier when functioning/allowed.

Repeat stochastic local-model runs. A feature that benefits only one model tier may remain only with
an explicit scoped rollout.

## Anti-overfit rule

- Use real ControlDeck tasks as the first rich corpus.
- Reserve held-out ControlDeck tasks/prompts outside tuning.
- Before generic `active-default`, repeat an accepted subset on a held-out repository using the same
  OpenCode runtime.
- Where platform influence is plausible, repeat a small direct OpenCode control outside ControlDeck.
- Do not add another harness merely to prove generalization.

Workspace/revision identity must remain explicit when ControlDeck or any other platform copies or
manages a project. Never merge Twin/runtime evidence from different workspaces because content looks
similar.

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
- host/platform UI and integration lifecycle.

## Immediate sequence

1. Start RV-0 from synchronized `main` after this planning correction is merged.
2. Run local lint/typecheck/unit/integration/build before production changes.
3. Record ExtendCodeAgent commit, OpenCode version, model/provider profiles, repository/workspace
   identity and hardware/runtime environment. Record ControlDeck commit only as evaluation-platform
   metadata when used.
4. Establish an OpenCode-native baseline before PI optimization, normally through ControlDeck plus a
   direct OpenCode control where platform influence is plausible.
5. Revalidate OpenCode adapter/plugin/MCP/edit/restart/reconnect/off/shadow/advisory paths.
6. Reproduce frontier/provider failures with PI disabled first. Fix only OpenCode/ECA/model-provider
   defects in ExtendCodeAgent; ControlDeck-only defects remain ControlDeck responsibility.
7. Build versioned real-task and held-out task sets. Compare required runtime/mode/model combinations
   with objective test/build/behavior evidence.
8. Produce the RV-0 gap report and classify each failure as evaluation-platform, OpenCode runtime,
   model/provider, PI adapter, PI core, task selection, verification or performance.
9. RA-0: formalize only OpenCode signals consumed by Task-aware PI/Verification.
10. TA-0: deterministic shadow planning only.
11. WL-0: weak-local protocol only if measured failures justify it.
12. TA-1: advisory automatic capability/context selection.
13. VI-0: confidence, Test Intelligence and Convergence/completion quality; add 2.0 features only for
    measured failures.
14. TA-2: bounded active for accepted task/relation/model scopes.
15. TA-3: progressive expansion after repeated evidence.
16. Runtime Bridge or bounded DFG/Taint/CFG only when a repeated high-value OpenCode task proves the
    missing relation is the smallest fix.
17. RV-FINAL: OpenCode production baseline using ControlDeck as primary evaluation platform plus
    held-out repository confirmation; no new feature scope.
18. Project Evidence Memory/PI Trace remains P1 unless cross-session evidence loss is a release blocker.
19. Optional OpenCode+OMO comparisons only for relevant orchestration claims.
20. RA-3 second-harness proof only after the OpenCode production baseline.
21. PI-aware parallel/worktree work only after a stable OpenCode-compatible runtime signal path is
    demonstrated; start advisory/detection-only.

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

Update `CURRENT_HANDOFF.md` after each major OpenCode/model/controller evaluation. ControlDeck-specific
integration decisions belong in ControlDeck, not in this repository.
