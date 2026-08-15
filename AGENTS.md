# AGENTS.md — ExtendCodeAgent development entrypoint

For Codex work in this repository, read and follow in this order:

1. `docs/handoff/CODEX_OMO_COMPATIBILITY_INSTRUCTION.md`
2. `docs/handoff/NEXT_TASK.md`
3. `docs/ADAPTIVE_CAPABILITY_LEVELS_AND_TARGETED_VERIFICATION_PLAN.md`
4. `docs/VERIFICATION_OBLIGATION_AND_TEST_EXECUTION_PLAN.md`
5. `docs/TEST_PORTFOLIO_INTELLIGENCE_AND_BROAD_EVALUATION_PLAN.md`
6. `docs/COMPOSITIONAL_VERIFICATION_AND_EVIDENCE_REUSE_PLAN.md`
7. `docs/FAILURE_DRIVEN_PI_REEVALUATION_PLAN.md`
8. `docs/handoff/CURRENT_HANDOFF.md`
9. the canonical plans referenced by those files.

Current responsibility: develop ExtendCodeAgent for OpenCode and evaluate/fix coexistence with OMO. Do not implement ControlDeck installation/UI/stack-management logic here.

Preserve the host-neutral Project Intelligence core, keep OpenCode-specific behavior in its adapter, reuse existing components before adding new ones, and require real OpenCode/agent/LLM evidence before promoting a capability, capability depth, targeted-verification policy, Test Portfolio capability, compositional-evidence policy, failure-reevaluation policy, or an ECA+OMO version tuple.

Strengthened PI capabilities must remain depth-configurable rather than permanently maximum-cost. Keep rollout authority (`off/shadow/advisory/active`) separate from per-capability execution depth, and use evaluation evidence to recommend/promote/demote levels.

For verification, treat `docs/VERIFICATION_OBLIGATION_AND_TEST_EXECUTION_PLAN.md` as authoritative when older shorthand suggests a simple `direct -> impacted -> subsystem -> full` test ladder. Determine **what must be verified** from the semantic change, Impact closure, requirements and evidence coverage; then optimize **how to execute the required verification set** using duration/setup/parallelism data. Additional tests are driven by residual uncovered/conflicted obligations, not by a vague time-budget or "enough tests have passed" rule. Full-suite runs remain available for release/fallback/high-uncertainty cases and periodic calibration of PI misses.

For existing repositories, use the Test Portfolio plan's bootstrap model: first import a revision-aware initial Project/Twin/test baseline, but never treat that baseline as verified correctness. Test Intelligence may then audit, design, generate/update, evaluate, select and consolidate tests as evidence providers.

GUI verification must prove the required **user-visible/runtime outcome**, not merely DOM render/click success. For cross-boundary actions, model and verify the causal flow from UI action through state/API/IPC/backend/process/resource effects to the final observable state. Keep browser/runtime execution owned by the host; ECA owns the Project Intelligence/verification obligations and evidence interpretation.

For expensive verification, follow `docs/COMPOSITIONAL_VERIFICATION_AND_EVIDENCE_REUSE_PLAN.md`: evidence reuse is not a generic PASS cache. Reuse a prior segment only when its Evidence Dependency Closure, boundary pre/postconditions, runtime/config/environment assumptions, revision/workspace identity and freshness remain compatible. Model user-flow verification as a branching Evidence DAG rather than forcing a linear chain. Find the nearest trustworthy Verification Frontier, verify only residual invalidated/uncovered obligations, and compose fresh + reusable evidence conservatively. Preserve periodic/release full E2E calibration so hidden dependencies and composition misses remain discoverable.

For unexpected verification failures, follow `docs/FAILURE_DRIVEN_PI_REEVALUATION_PLAN.md`. Treat FAIL as new revision-aware evidence, not automatic proof of production-code error or test obsolescence. Re-evaluate in this order by default: **Test Intent/specification consistency -> Oracle quality -> fixture/mock/helper freshness -> harness/environment/runtime validity -> Impact/Evidence Dependency Closure -> static/runtime reconciliation -> production implementation**. Failure alone must never justify deleting, weakening or obsoleting a test. Expand only the relevant PI capability/scope when current evidence is insufficient, and record `PI_MODEL_MISS` / `EVIDENCE_REUSE_MISS` as product calibration evidence.
