# Next Task

Finish PR-D publication and merge. Do not start PR-E on this branch.

1. Inspect `git diff 4a73c6f1..HEAD` plus uncommitted changes for adapter-only OpenCode/MCP scope.
2. Commit the Chokidar fallback, reproducible OpenCode smoke, local script integration, and compact
   PR-D evidence. Ensure the tracked smoke fixture is formatted and no ignored DB is staged.
3. Run exact-head `tools/local/all-fast`, `tools/local/test-integration`, `tools/local/build`, and
   `tools/local/opencode-smoke`.
4. Update exact results in `CURRENT_HANDOFF.md`, commit evidence if values changed, then repeat the
   fast/build gates on the final documentation head.
5. Push `agent/pr-d-opencode-mcp`, create a draft PR against `main`, and verify the exact remote head,
   diff scope, mergeability, review state, and checks. GitHub Actions are not required or expected.
6. Mark ready and squash-merge only after local evidence and remote metadata are clean.
7. Fast-forward local `main`, rerun `tools/local/all-fast` and `tools/local/test-integration`, then
   create a narrow closeout branch/PR that records the merged commit and makes PR-E the next task.

Resume:

```bash
cd /home/souten/ExtendCodeAgent
git switch agent/pr-d-opencode-mcp
git status --short
git diff --check
tools/local/all-fast
tools/local/build
tools/local/opencode-smoke
```

PR-E starts only after PR-D and its closeout handoff are merged. Its first slice must define
`RuntimeObservation` and behavior-first tests for revision freshness, test selection fallback, and
test-obsolescence states; do not mix Blueprint, live model routing, or JS/TS semantic work into it.
