# Next Task

Start the evidence-driven productization baseline after this planning PR is merged.

Canonical execution documents:

1. `docs/PRODUCTIZATION_AND_MODEL_EVALUATION_PLAN.md`
2. `docs/CODEX_PRODUCTIZATION_EXECUTION_GUIDE.md`
3. `docs/handoff/CURRENT_HANDOFF.md`
4. existing implementation/evidence only as needed for the active slice.

## Immediate sequence

1. Fast-forward `main` and create `agent/release-validation-baseline`.
2. Run current local lint/typecheck/unit/integration/build before changing production code.
3. Record the exact environment, current OpenCode stable version, repository SHAs, local model profiles,
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
8. Only after the gap report, implement the smallest P0 fixes. Priority is task-aware capability/context
   selection, Verification/Confidence quality, OpenCode productization, and refresh/context optimization.
9. Implement Runtime Bridge only if real UI/API tasks demonstrate a material browser/runtime recall gap.
10. Implement on-demand DFG/Taint/CFG only if a measured high-value task specifically requires it.
11. Finish with a separate integration-only final Release Validation PR. Do not mark production-capable
    while required gates remain FAIL/UNAVAILABLE/NOT TESTED.

## Frozen by default

Do not implement repository-wide CFG/DFG, persistent full UI graphs, universal Blueprint/Strategy,
automatic Research, or other deferred graph types merely to complete the old roadmap.

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

Update `CURRENT_HANDOFF.md` before substantial code changes and after every major model/OpenCode
evaluation so another account/agent can resume without conversation history.
