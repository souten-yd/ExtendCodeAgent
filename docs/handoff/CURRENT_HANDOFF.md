# Current Handoff

Updated: 2026-08-13 (Asia/Tokyo)

Current branch: `agent/pr-d-opencode-mcp`
Current PR: not created
Base commit: `4a73c6f1a2903fb37185e3afd312c30c76c394f4`
Latest commit: `4ac0d12` (stable OpenCode and MCP adapters)
Current milestone: PR-D OpenCode + MCP real integration
Current task: complete real OpenCode watcher/mode evidence and local validation integration
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
  factory; moved testable path normalization to a separate module.

In progress:
- repeat the real watcher edit after committing the tracked smoke fixture, then verify revision
  change, no self-generated event loop, off/shadow/advisory behavior, and restart.

Not started:
- reproducible OpenCode smoke/benchmark scripts, final PR-D evidence report, local script wiring,
  publication and merge.

Important architecture decisions:
- Target stable `@opencode-ai/plugin` 1.18.18 for PR-D; V2 is beta and remains a separate adapter.
- Stable project plugins load from `.opencode/plugins/` and expose event/tool hook objects.
- Stable local MCP config is a named entry under `mcp` with `type: local`, command array, and
  `enabled`; do not use the incompatible V2 `mcp.servers`/`disabled` shape.

Important invariants:
- `analysis`, `core`, `graph`, `service`, `storage`, and `twin` never import OpenCode/plugin/MCP SDK
  types.
- Hooks enqueue bounded events and return quickly; no AST/graph refresh runs synchronously in hooks.
- Plugin tools and MCP tools call the same Python service; business logic is not duplicated.
- off is inert, shadow cannot alter native behavior, advisory requires explicit tool/query use.

Files changed: shared application service/sidecar, TypeScript plugin/MCP package, adapter tests,
architecture boundary, smoke fixture, ignore policy, and PR-D handoff.
Files currently being edited: watcher path filtering, real-host evidence, local validation scripts.

Exact tests executed:
- `tools/local/all-fast` on merged PR-C closeout main
- `tools/local/build`
- `.venv/bin/pytest tests/unit/test_application_service.py tests/integration/test_local_sidecar.py`
- `npm run typecheck`; `npm test` in `adapters/opencode`
- `tools/local/all-fast` after watcher-filter fix
Exact results: Python focused `5 passed`; TypeScript typecheck PASS; adapter `4 passed` including
real MCP stdio call in 4.25 s and sidecar reconnect in 1.17 s; Ruff/mypy PASS and Python
`49 passed in 0.28s`.
Benchmark results: real `debug config` plugin initialization approximately 2.7 s and MCP connection
approximately 0.75 s during manual smoke; exact reproducible measurements still required.
OpenCode version: 1.18.18; real plugin load/tool discovery/MCP connection verified.
Model/provider: none required for initial plugin/MCP load; real model use is not a PR-D capability.
Routing profile: not applicable.
Known failures: initial watcher run formed a `.git/index.lock` feedback loop; fixed and covered by a
path-filter test. Exporting `workspacePath` from the plugin entry caused real loader failure; fixed
by separating it into `paths.ts`.
Known limitations: V2 plugin/MCP APIs differ materially and are beta; PR-D targets stable only.
The Codex `apply_patch` rewrite path did not produce an observed OpenCode watcher event in the first
manual attempt; repeat with a tracked fixture and formatter/native host path.
Uncommitted work: watcher-filter fix, MCP integration test, architecture expansion, tracked smoke
fixture, and this handoff update.
Temporary work: preserved loop DB under `/tmp/extendcodeagent-pr-d-loop-evidence-20260813T0840JST`
and filtered smoke DB under `/tmp/extendcodeagent-pr-d-filtered-smoke-20260813T0850JST`; current
ignored `.extendcodeagent/graph.db` is disposable smoke state.

Next exact action: commit the coherent watcher-filter/MCP-test slice, run OpenCode 1.18.18 with the
tracked fixture, trigger an external formatter edit, and record pre/post Twin revision and latency.
Next files: `adapters/opencode/src/plugin.ts`, `paths.ts`, adapter tests,
`tests/fixtures/opencode_smoke/sample.py`, then `tools/local/*` and `docs/evidence/pr-d/`.
Next commands: `git diff --check`; commit; start OpenCode with `EXTENDCODEAGENT_MODE=shadow`; create
a session; format the tracked fixture; inspect `.extendcodeagent/graph.db`; repeat off/advisory.
Rollback path: stop OpenCode/SSE sessions, move ignored smoke DB to `/tmp`, revert PR-D commits, and
delete the branch; OpenCode can be uninstalled independently without changing core code.
