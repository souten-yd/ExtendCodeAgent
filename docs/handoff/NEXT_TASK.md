# Next Task

Start the integration-only final Release Validation PR after merging this PR-I closeout.

1. Fast-forward main and create `agent/release-validation`.
2. Audit every Release Gate against current code and evidence; classify PASS, FAIL, UNAVAILABLE, or
   NOT TESTED. Do not convert prior milestone evidence into a new pass without checking drift.
3. Compare native/off/advisory/active on small Python, medium Python, JS/TS, and a real mixed
   project across available weak-local, practical-local, host/default, and frontier paths.
4. Record correctness, task success, impact/test recall, calls, tokens, latency, memory, DB size,
   startup overhead, unnecessary edits, stale-context prevention, and completion correctness under
   `docs/evidence/final/`. Keep raw large logs out.
5. Re-run real OpenCode plugin/edit/external-edit/MCP/restart/reconnect and current local builds.
6. If a required path is unavailable (including frontier credentials/provider), record the failed
   gate and do not mark `PRODUCTION-CAPABLE BASELINE COMPLETE`.

Resume:

```bash
cd /home/souten/ExtendCodeAgent
git switch main
git pull --ff-only origin main
git status --short
git switch -c agent/release-validation
```
