# Current Handoff

Updated: 2026-08-13 (Asia/Tokyo)

Current branch: `agent/pr-d-opencode-mcp`
Current PR: not created
Base commit: `4a73c6f1a2903fb37185e3afd312c30c76c394f4`
Latest commit: `736c2e9` (complete real OpenCode adapter evidence)
Current milestone: PR-D OpenCode + MCP real integration
Current task: finalize exact evidence, publish PR-D, verify remote head, and merge
Task status: in progress

Goal: add a thin stable OpenCode plugin, a shared versioned local core service, and MCP fallback
without importing OpenCode types into the host-neutral Project Intelligence packages.

Scope:
- TypeScript stable OpenCode plugin under adapter-only paths;
- versioned local JSON interface to the Python core;
- background event queue/coalescing for file/watcher/LSP/tool/session signals;
- one shared core query service used by plugin tools and MCP;
- `pi.status`, `pi.symbol`, `pi.references`, `pi.path`, `pi.impact`, `pi.tests`;
- off/shadow/advisory behavior and real plugin/MCP/restart/reconnect evidence.

Out of scope:
- automatic active context/test effects, runtime intelligence and test obsolescence (PR-E);
- Blueprint/Convergence, live model routing/Strategy, JS/TS semantic analysis, and Research.

Completed:
- PR-C merged as `ef6db532`; docs closeout PR #7 merged as `4a73c6f1`;
- fast-forwarded `main`, passed base all-fast/build, and created this branch;
- installed and verified OpenCode 1.18.18 at `/home/souten/.local/npm-global/bin/opencode`;
- checked official stable plugin, custom-tool, MCP, config, CLI, and V2 beta documentation;
- queried current npm versions: `opencode-ai` 1.18.18, `@opencode-ai/plugin` 1.18.18,
  `@modelcontextprotocol/sdk` 1.30.0;
- implemented a shared host-neutral application service and authenticated
  `extendcodeagent.local.v1` sidecar;
- implemented the stable TypeScript plugin, coalescing event queue, six plugin tools, and MCP
  stdio fallback over the same service;
- real OpenCode server loaded the plugin, exposed all six `pi_*` tools, and connected the MCP;
- real MCP handshake/list/call and sidecar stop/reconnect/revision persistence passed;
- caught and fixed a real watcher feedback loop caused by `.git/index.lock` and
  `.extendcodeagent` events; ignored paths are filtered before enqueue;
- caught the stable loader behavior that treats every exported plugin-module function as a plugin
  factory; moved testable path normalization to a separate module;
- added a Chokidar adapter fallback after the stable native watcher did not emit ordinary source
  changes in the real Linux run;
- verified an OpenCode session-shell format edit and a separate external edit produced distinct
  Twin revisions, then verified no-loop stability, restart persistence, MCP reconnect, and an off
  mode negative control;
- added a reproducible model-free real-host smoke and wired TypeScript validation into bootstrap,
  all-fast, integration, and build scripts.

In progress:
- final diff/evidence inspection and exact-head commit.

Not started:
- PR publication, remote-head inspection, ready/merge, post-merge local gate, and closeout handoff.

Important architecture decisions:
- Target stable `@opencode-ai/plugin` 1.18.18 for PR-D; V2 is beta and remains a separate adapter.
- Stable project plugins load from `.opencode/plugins/` and expose event/tool hook objects.
- Stable local MCP config is a named entry under `mcp` with `type: local`, command array, and
  `enabled`; do not use the incompatible V2 `mcp.servers`/`disabled` shape.
- Native and fallback file events share one adapter queue; Chokidar is an adapter-only ADAPT caused
  by measured stable-host behavior and is never imported by the Python core.

Important invariants:
- `analysis`, `core`, `graph`, `service`, `storage`, and `twin` never import OpenCode/plugin/MCP SDK
  types.
- Hooks enqueue bounded events and return quickly; no AST/graph refresh runs synchronously in hooks.
- Plugin tools and MCP tools call the same Python service; business logic is not duplicated.
- off is inert, shadow cannot alter native behavior, advisory requires explicit tool/query use.

Files changed: shared application service/sidecar, TypeScript plugin/MCP package, adapter tests,
architecture boundary, smoke fixture, ignore policy, and PR-D handoff.
Files currently being edited: final evidence/status/handoff and publication metadata.

Exact tests executed:
- `tools/local/all-fast` on merged PR-C closeout main
- `tools/local/build`
- `.venv/bin/pytest tests/unit/test_application_service.py tests/integration/test_local_sidecar.py`
- `npm run typecheck`; `npm test` in `adapters/opencode`
- `tools/local/all-fast` after watcher-filter fix
- `tools/local/opencode-smoke`
- final `tools/local/all-fast`; `tools/local/test-integration`; `tools/local/build`
Exact results: substantive-head Ruff/mypy PASS; Python unit/architecture `49 passed in 0.33s`;
adapter `6 passed in 4.26s`; Python integration `9 passed in 1.45s`; repeated adapter `6 passed in 4.26s`;
Python sdist/wheel and TypeScript build PASS.
Benchmark results: alternating three-run startup medians: native 1,046 ms, plugin 1,070 ms (+24
ms; native samples 1,609/1,044/1,046 ms); integration startup 1,062 ms; initial revision 151 ms;
OpenCode tool edit refresh 151 ms; external edit refresh 151 ms; reconnect 1,109 ms; three revisions
stable and persisted; off remained three revisions.
OpenCode version: 1.18.18; real plugin load/tool discovery/MCP connection verified.
Model/provider: none required for initial plugin/MCP load; real model use is not a PR-D capability.
Routing profile: not applicable.
Known failures: initial watcher run formed a `.git/index.lock` feedback loop; fixed and covered by a
path-filter test. Exporting `workspacePath` from the plugin entry caused real loader failure; fixed
by separating it into `paths.ts`.
Known limitations: V2 plugin/MCP APIs differ materially and are beta; PR-D targets stable only. The
three-run startup result is not a statistically stable distribution and includes one 1,609 ms
native outlier. Stable OpenCode's native watcher did not emit ordinary file events in this
environment, so the adapter fallback remains necessary.
Uncommitted work: exact substantive-head evidence and this handoff update.
Temporary work: preserved loop DB under `/tmp/extendcodeagent-pr-d-loop-evidence-20260813T0840JST`
and filtered smoke DB under `/tmp/extendcodeagent-pr-d-filtered-smoke-20260813T0850JST`; current
ignored `.extendcodeagent/graph.db` is disposable manual-smoke state.

Next exact action: commit the exact substantive-head evidence, rerun final documentation-head
all-fast/build gates, push, create PR-D, inspect remote head, and merge only if clean.
Next files: complete branch diff; `docs/evidence/pr-d/`; `docs/CURRENT_STATUS.md`; PR description.
Next commands: `git diff --check`; `git diff 4a73c6f..HEAD`; commit; exact-head local gates; `git push`;
create draft PR; verify mergeability and absence/presence of checks.
Rollback path: stop OpenCode/SSE sessions, move ignored smoke DB to `/tmp`, revert PR-D commits, and
delete the branch; OpenCode can be uninstalled independently without changing core code.
