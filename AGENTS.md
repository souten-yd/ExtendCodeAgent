# AGENTS.md — ExtendCodeAgent development entrypoint

For Codex work in this repository, read and follow in this order:

1. `docs/PI_MASTER_EXECUTION_PLAN.md` — canonical product definition, unified backlog (§8), release gates.
2. `docs/handoff/NEXT_TASK.md` — the currently assigned stage.
3. `docs/CURRENT_STATUS.md` — program state and evidence ledger.
4. only the design detail registered in master plan §2 that the active stage actually needs.

No individual plan document is standing required reading. §2 of the master plan records each document's disposition; pull in a design detail when the active stage calls for it, not by default.

Do not schedule work by legacy identifiers (`RV-x`, `TA-x`, `AL-x`, `CV-x`, `TP-x`, `VI-Xx`, `RA-x`, `EM-0`, `MA-0`) — they are mapped to current stages in master plan §9 and must not be used for scheduling.

Current responsibility: develop ExtendCodeAgent for OpenCode and evaluate/fix coexistence with OMO. Do not implement ControlDeck installation/UI/stack-management logic here.

Preserve the host-neutral Project Intelligence core, keep OpenCode-specific behavior in its adapter, reuse existing components before adding new ones, and require real OpenCode/agent/LLM evidence before promoting a capability, capability depth, targeted-verification policy, Test Portfolio capability, compositional-evidence policy, failure-reevaluation policy, integrated verification capability, or an ECA+OMO version tuple.

Strengthened PI capabilities must remain depth-configurable rather than permanently maximum-cost. Keep rollout authority (`off/shadow/advisory/active`) separate from per-capability execution depth, and use evaluation evidence to recommend/promote/demote levels.

ECA development must dogfood the Master Plan's Minimum Sufficient Reasoning invariant. Before spending an LLM call, first determine whether deterministic analysis, sealed evidence, compatible prior results, PI-only preflight, or a narrower task/depth/context can resolve the decision. Start with the minimum sufficient capability, depth and context, expand only for an explicit unresolved Evidence Gap, and do not repeat model work on identical inputs unless an evaluation contract explicitly requires independent repetition. Call reduction never permits skipping required correctness evidence or treating untested work as no effect.

For verification, treat `docs/VERIFICATION_OBLIGATION_AND_TEST_EXECUTION_PLAN.md` as authoritative when older shorthand suggests a simple `direct -> impacted -> subsystem -> full` test ladder. Determine **what must be verified** from the semantic change, Impact closure, requirements and evidence coverage; then optimize **how to execute the required verification set** using duration/setup/parallelism data. Additional tests are driven by residual uncovered/conflicted obligations, not by a vague time-budget or "enough tests have passed" rule. Full-suite runs remain available for release/fallback/high-uncertainty cases and periodic calibration of PI misses.

For existing repositories, use the Test Portfolio plan's bootstrap model: first import a revision-aware initial Project/Twin/test baseline, but never treat that baseline as verified correctness. Test Intelligence may then audit, design, generate/update, evaluate, select and consolidate tests as evidence providers.

GUI verification must prove the required **user-visible/runtime outcome**, not merely DOM render/click success. For cross-boundary actions, model and verify the causal flow from UI action through state/API/IPC/backend/process/resource effects to the final observable state. Keep browser/runtime execution owned by the host; ECA owns the Project Intelligence/verification obligations and evidence interpretation.

For expensive verification, follow `docs/COMPOSITIONAL_VERIFICATION_AND_EVIDENCE_REUSE_PLAN.md`: evidence reuse is not a generic PASS cache. Reuse a prior segment only when its Evidence Dependency Closure, boundary pre/postconditions, runtime/config/environment assumptions, revision/workspace identity and freshness remain compatible. Model user-flow verification as a branching Evidence DAG rather than forcing a linear chain. Find the nearest trustworthy Verification Frontier, verify only residual invalidated/uncovered obligations, and compose fresh + reusable evidence conservatively. Preserve periodic/release full E2E calibration so hidden dependencies and composition misses remain discoverable.

For unexpected verification failures, follow `docs/FAILURE_DRIVEN_PI_REEVALUATION_PLAN.md`. Treat FAIL as new revision-aware evidence, not automatic proof of production-code error or test obsolescence. Re-evaluate in this order by default: **Test Intent/specification consistency -> Oracle quality -> fixture/mock/helper freshness -> harness/environment/runtime validity -> Impact/Evidence Dependency Closure -> static/runtime reconciliation -> production implementation**. Failure alone must never justify deleting, weakening or obsoleting a test. Expand only the relevant PI capability/scope when current evidence is insufficient, and record `PI_MODEL_MISS` / `EVIDENCE_REUSE_MISS` as product calibration evidence.

For the next verification refinements, follow `docs/PI_VERIFICATION_OBSERVABILITY_INTEGRATED_DESIGN.md`. Do not build standalone competing truth stores for Observability Gap, Environment Matrix, Verification Certificate, Nondeterminism, Evidence Diversity, Regression Knowledge, Performance Obligations, or Verification Debt. Project them from the same revision-aware Digital Twin / Project Graph / Impact / Test Intent / Runtime Evidence / Traceability / Convergence model. Missing observability is not automatically a missing test; environment verification must be impact-selected rather than Cartesian; certificates are auditable reason records rather than permanent proof; and Evidence Diversity must protect independent unit/contract/runtime/GUI/calibration value during test consolidation.
