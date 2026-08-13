# Current Handoff

Updated: 2026-08-13 (Asia/Tokyo)

Current branch: `agent/pr-d-opencode-mcp`
Current PR: not created
Base commit: `4a73c6f1a2903fb37185e3afd312c30c76c394f4`
Latest commit: `4a73c6f1a2903fb37185e3afd312c30c76c394f4` (PR-C closeout)
Current milestone: PR-D OpenCode + MCP real integration
Current task: verify current stable interfaces and establish versioned adapter boundary
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
- confirmed `opencode` is not initially installed;
- checked official stable plugin, custom-tool, MCP, config, CLI, and V2 beta documentation;
- queried current npm versions: `opencode-ai` 1.18.18, `@opencode-ai/plugin` 1.18.18,
  `@modelcontextprotocol/sdk` 1.30.0.

In progress:
- install OpenCode 1.18.18 and inspect its stable package type declarations.

Not started:
- behavior tests, local interface/core service, plugin/MCP implementation, and real-host evidence.

Important architecture decisions:
- Target stable `@opencode-ai/plugin` 1.18.18 for PR-D; V2 is beta and remains a separate adapter.
- Stable project plugins load from `.opencode/plugins/` and expose event/tool hook objects.
- Stable local MCP config is a named entry under `mcp` with `type: local`, command array, and
  `enabled`; do not use the incompatible V2 `mcp.servers`/`disabled` shape.

Important invariants:
- `analysis`, `core`, `graph`, `storage`, and `twin` never import OpenCode/plugin/MCP SDK types.
- Hooks enqueue bounded events and return quickly; no AST/graph refresh runs synchronously in hooks.
- Plugin tools and MCP tools call the same Python service; business logic is not duplicated.
- off is inert, shadow cannot alter native behavior, advisory requires explicit tool/query use.

Files changed: PR-D start handoff/decision documentation only.
Files currently being edited: OpenCode interface evidence and adapter test design.

Exact tests executed:
- `tools/local/all-fast` on merged PR-C closeout main
- `tools/local/build`
Exact results: Ruff PASS; strict mypy PASS; `45 passed in 0.21s`; sdist/wheel build success.
Benchmark results: none for PR-D yet.
OpenCode version: unavailable before installation; target npm stable is 1.18.18.
Model/provider: none required for initial plugin/MCP load; real model use is not a PR-D capability.
Routing profile: not applicable.
Known failures: `opencode --version` returned command not found before installation.
Known limitations: V2 plugin/MCP APIs differ materially and are beta; PR-D targets stable only.
Uncommitted work: this start handoff until committed.
Temporary work: none.

Next exact action: install `opencode-ai@1.18.18`, record its version, inspect stable plugin package
types, then add behavior-first adapter/interface tests.
Next files: installed npm package type declarations; `docs/handoff/DECISIONS.md`; new adapter/MCP
package manifests and tests only after interface confirmation.
Next commands: `npm install -g opencode-ai@1.18.18`; `opencode --version`; inspect package roots and
stable `@opencode-ai/plugin` declarations.
Rollback path: uninstall the globally added OpenCode version if required; delete/revert this branch;
do not reset unrelated work.
