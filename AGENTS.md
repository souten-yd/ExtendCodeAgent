# AGENTS.md — ExtendCodeAgent development entrypoint

For Codex work in this repository, read and follow in this order:

1. `docs/handoff/CODEX_OMO_COMPATIBILITY_INSTRUCTION.md`
2. `docs/handoff/NEXT_TASK.md`
3. `docs/ADAPTIVE_CAPABILITY_LEVELS_AND_TARGETED_VERIFICATION_PLAN.md`
4. `docs/handoff/CURRENT_HANDOFF.md`
5. the canonical plans referenced by those files.

Current responsibility: develop ExtendCodeAgent for OpenCode and evaluate/fix coexistence with OMO. Do not implement ControlDeck installation/UI/stack-management logic here.

Preserve the host-neutral Project Intelligence core, keep OpenCode-specific behavior in its adapter, reuse existing components before adding new ones, and require real OpenCode/agent/LLM evidence before promoting a capability, capability depth, targeted-verification policy, or an ECA+OMO version tuple.

Strengthened PI capabilities must remain depth-configurable rather than permanently maximum-cost. Keep rollout authority (`off/shadow/advisory/active`) separate from per-capability execution depth, use evaluation evidence to recommend/promote/demote levels, and prefer graph-selected targeted verification with progressive full-suite fallback over running every test for every task.
