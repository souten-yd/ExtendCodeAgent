# Next Task

Finish PR-C publication and merge; do not add new PR-C capability.

1. Inspect the complete branch diff against `origin/main`, including the host-neutral architecture
   test and `docs/evidence/pr-c/`.
2. Commit the dependency-aware refresh, benchmark, evidence, and final documentation slice.
3. Run exact-head `tools/local/all-fast`, `tools/local/test-integration`, `tools/local/build`, and
   `tools/local/benchmark-pr-c`; record exact results if they differ from current evidence.
4. Create a scoped PR-C draft, verify the remote head and absence of required GitHub Actions, mark
   ready only after local evidence matches that head, then squash-merge.
5. Fast-forward local `main`, rerun fast/integration gates, and create a small closeout commit/PR if
   the merged-state handoff cannot truthfully be represented by the PR branch documentation.
6. Create `agent/pr-d-opencode-mcp` only after PR-C closeout. Re-check the current stable OpenCode
   plugin/MCP APIs before implementing adapters.

Resume:

```bash
cd /home/souten/ExtendCodeAgent
git switch agent/pr-c-semantic-impact
git status --short
git diff --check
tools/local/all-fast
tools/local/test-integration
tools/local/build
tools/local/benchmark-pr-c
```
