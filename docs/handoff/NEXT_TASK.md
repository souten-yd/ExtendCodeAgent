# Next Task

Next task is PR-B Graph/Twin persistence and source snapshot.

1. Start from updated `main`; verify PR-A is merged and `tools/local/all-fast` passes.
2. Read the PR-B section of `docs/IMPLEMENTATION_EXECUTION_LOCAL_VALIDATION_PLAN.md` and the
   Graph/Twin storage sections of `docs/KASANECORE_MIGRATION_AUDIT.md` only.
3. Inspect KasaneCore `agent/project_twin/contracts.py`, `store.py`, `source_adapter.py`, and the
   rebuild/refresh path in `module.py`.
4. Translate behavior first from `tests/test_project_twin_store.py`,
   `test_project_twin_source_adapter.py`, `test_project_twin_source_refresh_lifecycle.py`, and
   `test_project_twin_module_durability.py`; do not copy Atlas fixtures/DTOs.
5. Define the narrow graph revision/store/source snapshot ports using PR-A `ProjectRef`,
   `SourceRevision`, `TwinRevisionRef`, `Provenance`, and `Diagnostic` contracts.
6. Implement atomic immutable SQLite revision commits, project/workspace isolation, source/worktree
   fingerprinting, restart persistence, full rebuild, and changed-file invalidation.
7. Keep semantic/call/path/impact, OpenCode/MCP, runtime/context, and real model routing out of PR-B.
8. Add persistence/restart/incremental invalidation tests and a small real-repository benchmark for
   cold snapshot, incremental refresh, DB size, and memory/time evidence.
9. Run focused tests, `tools/local/all-fast`, `tools/local/build`, update all handoff/status evidence,
   then publish PR-B as a separate branch/PR.

Resume:

```bash
cd /home/souten/ExtendCodeAgent
git switch main
git pull --ff-only origin main
git status --short
```
