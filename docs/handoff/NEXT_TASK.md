# Next Task

Start the evidence-driven productization baseline, then implement transparent task-aware PI in measured stages.

Canonical execution documents:

1. `docs/PRODUCTIZATION_AND_MODEL_EVALUATION_PLAN.md`
2. `docs/TRANSPARENT_PI_ORCHESTRATION_PLAN.md`
3. `docs/CODEX_PRODUCTIZATION_EXECUTION_GUIDE.md`
4. `docs/handoff/CURRENT_HANDOFF.md`
5. existing implementation/evidence only as needed for the active slice.

## Immediate sequence

1. Fast-forward `main` and create `agent/release-validation-baseline`.
2. Run current local lint/typecheck/unit/integration/build before changing production code.
3. Record exact environment, current OpenCode stable version, repository SHAs, local model profiles,
   host/default model, and frontier availability under `docs/evidence/final/`.
4. Re-run real OpenCode plugin/MCP/edit/external-edit/restart/reconnect/off/shadow/advisory behavior
   before optimizing it.
5. Reproduce and repair the frontier path in this order: native OpenCode provider smoke, provider/auth
   classification, then ExtendCodeAgent adapter only if native succeeds.
6. Build a versioned real-task benchmark set and compare native/off/advisory/active across weak-local,
   practical-local, host/default, and a functioning frontier path. Repeat weak/local runs; do not use
   one lucky run as acceptance evidence.
7. Produce `docs/evidence/final/baseline-gap-report.md` ranking failures by frequency, severity, and
   user value. Classify each failure as model/provider/context/graph/runtime/test/routing/task-selection/
   OpenCode-adapter/lifecycle/config/performance.
8. Fix blocking OpenCode/frontier/lifecycle defects before adding transparent orchestration.
9. Implement `TA-0` on `agent/task-aware-shadow`: deterministic task signals/classification,
   `IntelligencePlan`, reasons and telemetry only. It MUST NOT alter context/model/test behavior.
10. Evaluate TA-0 against curated expected plans and the current manual/advisory baseline. Measure
    intent accuracy, capability precision/recall, under/over-selection, planner latency and unnecessary
    deep-analysis selection.
11. Implement `TA-1` advisory auto-selection only after TA-0 passes. Reuse existing Context/Impact/Test/
    Runtime services; do not create parallel query or context systems.
12. Implement `TA-2` bounded active only for empirically accepted low-risk relation/task classes.
    Stale/uncertain evidence must downgrade to advisory/source inspection/native fallback.
13. Implement `TA-3` progressive expansion only after repeated local-low/local-practical/host evaluation.
    Intelligence expansion and model escalation remain separate decisions.
14. Implement Runtime Bridge only if held-out UI/API tasks repeatedly fail because of a measured runtime
    boundary gap and a small generic bridge materially improves recall.
15. Implement bounded DFG/Taint/CFG only if a repeated high-value task proves a missing data/control
    relation is the root cause and deep analysis is the smallest measured fix.
16. Finish with `TA-FINAL`/integration-only final Release Validation. Compare transparent auto against
    both native OpenCode and manual/advisory PI across repositories and model tiers.
17. Do not make transparent automation a default candidate while critical under-selection, false
    completion, frontier/provider, privacy, or native-fallback gates remain unresolved.

## Transparent PI product target

Users should be able to ask normal OpenCode questions/tasks without mentioning PI. The controller
must select the **minimum** useful intelligence, expand only when evidence requires it, and frequently
choose native/no-extra-PI when additional analysis has no demonstrated value.

Normal automation must remain inspectable through PI health/last-plan diagnostics, but it should not
require routine PI-specific prompts or a large new user-facing tool surface.

## Controller evaluation baselines

Always distinguish:

1. native OpenCode;
2. manual/advisory best-known PI plan;
3. transparent controller auto-selection.

This is required to prove not only that PI is useful, but that the controller selects it correctly.
Use counterfactual/ablation checks on disputed high-value tasks.

## Frozen by default

Do not implement repository-wide CFG/DFG, persistent full UI graphs, universal Blueprint/Strategy,
automatic Research, or deferred graph types merely to complete the historical roadmap.

Deep capabilities stay on-demand and evidence-gated.

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

Update `CURRENT_HANDOFF.md` before substantial code changes and after every major model/OpenCode/
controller evaluation so another account/agent can resume without conversation history.
