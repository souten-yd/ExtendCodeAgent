# Next Task

Start the evidence-driven productization baseline, then formalize the minimum runtime-adapter
contract required by transparent task-aware PI before implementing automatic behavior.

Canonical execution documents:

1. `docs/PRODUCTIZATION_AND_MODEL_EVALUATION_PLAN.md`
2. `docs/TRANSPARENT_PI_ORCHESTRATION_PLAN.md`
3. `docs/RUNTIME_ADAPTER_ARCHITECTURE_PLAN.md`
4. `docs/CODEX_PRODUCTIZATION_EXECUTION_GUIDE.md`
5. `docs/handoff/CURRENT_HANDOFF.md`
6. existing implementation/evidence only as needed for the active slice.

## Architectural product target

OpenCode is the **primary reference runtime and first native adapter**, not the architectural core of
ExtendCodeAgent. Project Intelligence, Task-aware orchestration, Context/Impact/Verification,
Runtime Evidence, Model Routing, Strategy and Convergence remain host-neutral.

Do not build a new generic agent harness. Reuse each runtime's agent loop, tools, shell, permissions,
session and UI. Cross-runtime integration occurs through a small capability-negotiated Runtime
Adapter Contract plus MCP as a compatibility floor.

Before a second harness is proven, describe the project precisely as:

> a host-neutral Intelligence Layer with OpenCode as its primary reference runtime.

Do not claim multi-harness production support before it is tested.

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
8. Fix blocking OpenCode/frontier/lifecycle defects before transparent orchestration.
9. Run **RA-0 Minimal Runtime Contract** before TA-0 production behavior:
   - inventory exactly which runtime signals TA-0/TA-1 need;
   - reuse existing host-neutral contracts first;
   - add only missing RuntimeCapabilities/observation/delivery contracts;
   - keep OpenCode-specific SDK/types inside `adapters/opencode`;
   - map unsupported hooks to explicit unavailable/degraded capabilities;
   - add architecture/conformance tests;
   - do not add a second harness and do not change user-visible behavior.
10. Implement `TA-0` on `agent/task-aware-shadow`: deterministic task signals/classification,
    `IntelligencePlan`, reasons and telemetry only. It MUST NOT alter context/model/test behavior.
11. Evaluate TA-0 against curated expected plans and the current manual/advisory baseline. Measure
    intent accuracy, capability precision/recall, under/over-selection, planner latency and unnecessary
    deep-analysis selection.
12. Implement `TA-1` advisory auto-selection only after TA-0 passes. Reuse existing Context/Impact/Test/
    Runtime services; do not create parallel query or context systems.
13. Implement `TA-2` bounded active only for empirically accepted low-risk relation/task classes.
    Stale/uncertain evidence must downgrade to advisory/source inspection/native fallback.
14. Implement `TA-3` progressive expansion only after repeated local-low/local-practical/host evaluation.
    Intelligence expansion and model escalation remain separate decisions.
15. Implement Runtime Bridge only if held-out UI/API tasks repeatedly fail because of a measured runtime
    boundary gap and a small generic bridge materially improves recall.
16. Implement bounded DFG/Taint/CFG only if a repeated high-value task proves a missing data/control
    relation is the root cause and deep analysis is the smallest measured fix.
17. Finish with `TA-FINAL`/integration-only final Release Validation. Compare transparent auto against
    both native OpenCode and manual/advisory PI across repositories and model tiers.
18. Run **RA-1 OpenCode adapter conformance** and **RA-2 MCP compatibility conformance** as part of or
    immediately after the production baseline. Capability declarations, observations, delivery,
    privacy, lifecycle and fallback semantics must be truthful and reproducible.
19. After the OpenCode production-capable baseline, run **RA-3 Second-Harness Proof** using exactly one
    additional runtime selected by API stability/accessibility/user value. The purpose is to prove the
    architecture, not to start broad platform expansion. Project Model/Impact/Context/Verification/
    Task Controller must not be rewritten for the second runtime.
20. Do not add further runtime adapters until RA-3 evidence shows the generic contract is stable and
    there is demonstrated user value.

## Runtime integration tiers

Treat runtime support as capability-based, not all-or-nothing:

1. **Tier 1 MCP/explicit tools** — PI queries are reachable; no claim of transparent automation.
2. **Tier 2 Native adapter** — host observations/tool/context integration are normalized.
3. **Tier 3 Transparent integration** — sufficient trusted signals/delivery exist for Task-aware PI.

The controller must downgrade honestly when runtime capabilities are missing. MCP-only compatibility
is not equivalent to a full runtime adapter.

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
automatic Research, a new independent agent harness, or multiple runtime adapters merely to complete
an architectural roadmap.

Deep capabilities and additional runtimes stay evidence-gated.

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
controller/runtime-adapter evaluation so another account/agent can resume without conversation
history.
