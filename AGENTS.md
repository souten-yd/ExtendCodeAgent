# AGENTS.md — ExtendCodeAgent development entrypoint

For Codex work in this repository, read and follow in this order:

1. `docs/handoff/CODEX_OMO_COMPATIBILITY_INSTRUCTION.md`
2. `docs/handoff/NEXT_TASK.md`
3. `docs/handoff/CURRENT_HANDOFF.md`
4. the canonical plans referenced by those files.

Current responsibility: develop ExtendCodeAgent for OpenCode and evaluate/fix coexistence with OMO. Do not implement ControlDeck installation/UI/stack-management logic here.

Preserve the host-neutral Project Intelligence core, keep OpenCode-specific behavior in its adapter, reuse existing components before adding new ones, and require real OpenCode/agent/LLM evidence before promoting a capability or an ECA+OMO version tuple.
