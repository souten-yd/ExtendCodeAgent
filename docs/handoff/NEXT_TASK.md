# Next Task

Next task is PR-D OpenCode + MCP real integration. Keep PR-E context/test/runtime and PR-G live
model routing out of this slice.

1. Merge the PR-C docs-only closeout and fast-forward local `main`.
2. Create `agent/pr-d-opencode-mcp` from exact updated `origin/main`; run `tools/local/all-fast` and
   `tools/local/build` before implementation.
3. Re-read only the PR-D execution-plan section and current handoff. Re-check current official
   OpenCode stable plugin, custom-tool, event-hook, MCP configuration, and CLI documentation; inspect
   the installed package/type declarations rather than relying on the planning snapshot.
4. Install or locate current stable OpenCode, record `opencode --version`, and capture the exact
   plugin/MCP surfaces being adapted in `DECISIONS.md`.
5. Define one versioned host-neutral local interface to the Python core. Keep TypeScript OpenCode
   types under `adapters/opencode/`; the existing `analysis`, `core`, `graph`, `storage`, and `twin`
   packages must not import them.
6. Add behavior tests for off/shadow/advisory, queue/coalescing, reconnect, and MCP tools before
   business logic. Plugin and MCP must call the same core service.
7. Implement initial tools: `pi.status`, `pi.symbol`, `pi.references`, `pi.path`, `pi.impact`,
   `pi.tests`. Hooks enqueue events; they do not analyze synchronously.
8. Run real OpenCode plugin load, project open, file edit, external edit, Twin revision update, MCP
   query, restart, and reconnect. Record version/config/timings/errors; mock-only is not acceptance.

Resume:

```bash
cd /home/souten/ExtendCodeAgent
git switch main
git pull --ff-only origin main
tools/local/all-fast
tools/local/build
git switch -c agent/pr-d-opencode-mcp
git status --short
opencode --version
```
