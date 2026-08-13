# Current Handoff

Updated: 2026-08-13 (Asia/Tokyo)

Current branch: `agent/pr-c-closeout` (docs-only closeout)
Current PR: [#6](https://github.com/souten-yd/ExtendCodeAgent/pull/6) (merged)
Base commit: `ef6db532f74be97cbd86483b0bbe89ee6ac95a29`
Latest commit: `ef6db532f74be97cbd86483b0bbe89ee6ac95a29` (PR-C squash merge)
Current milestone: PR-C Structural/Python Semantic + Path/Impact
Current task: PR-C merged-state closeout and PR-D handoff
Task status: complete and merged

Goal: extend the PR-B graph/twin foundation with deterministic structural and Python semantic facts,
bounded explainable path queries, and confidence-aware impact analysis without adding OpenCode,
runtime, test-obsolescence, or LLM behavior.

Scope:
- repository/directory/file/module/class/function/method/test/dependency facts;
- contains/defines/imports/references/depends_on plus Python call/decorator/inheritance relations;
- analyzer-owned Python canonical-reference aliases;
- bounded paths and direct/transitive impact with weakest-link confidence;
- test candidates, requirements, side effects, historical risk, uncertainty, and explanations;
- curated ground truth, human-reviewable FP/FN evidence, and repeated-query benchmark.

Out of scope:
- OpenCode/MCP adapters, runtime observations, test obsolescence, context injection, Blueprint,
  Convergence, live models/strategy, JS/TS/deep graphs, and Research/Evidence.

Completed:
- PR-B and its closeout merged to `main` (`0618cd2`, `faf307d`);
- created this branch from exact `origin/main`;
- reviewed the PR-C execution-plan and migration-audit slices;
- inspected KasaneCore static/Python analyzers, path/impact service, and direct tests.
- added structural/Python AST facts and analyzer-owned canonical reference resolution;
- added bounded path and confidence-aware impact contracts/service;
- integrated optional analysis into Twin full/incremental persistence without changing file-only use;
- added seven focused ground-truth tests plus semantic persistence/invalidation integration.
- added dependency-aware importer refresh, an end-to-end persisted impact/test-candidate fixture,
  expanded host-neutral architecture coverage, a human FP/FN report, and real-repository benchmark.
- published draft PR #6; initial remote head `699d0d39c42763ad28ab8c0fe1aaa49d4aff941d`.
- verified final remote head `d078b3c413cbdbbcd9d9a9ef78c00122eb5b3864`, marked PR
  ready at MERGEABLE/CLEAN with no GitHub checks, and squash-merged as `ef6db532`;
- fast-forwarded local `main`; post-merge all-fast and integration gates passed.

In progress: none.

Not started: PR-D OpenCode/MCP adapter implementation and real-host acceptance.

Important architecture decisions:
- ADAPT the newer deterministic Python semantic analyzer behavior and graph analysis algorithms.
- CONSOLIDATE facts into PR-B `GraphNode`/`GraphEdge`/`GraphSnapshot`; do not introduce duplicate DTOs.
- REPLACE hard-coded `py://`/`pyname://` traversal knowledge with an analyzer-owned resolver.
- DO NOT PORT Atlas/Pydantic DTOs, JS/HTML analysis, clone detection, LSP enrichment, runtime, or model code.

Important invariants:
- Core has no OpenCode, Atlas, Nexus, provider-SDK, or adapter imports.
- Ambiguous calls remain inferred `may_call` facts with reduced confidence, never verified calls.
- Path and impact queries are revision-aware, bounded, read-only, and preserve weakest-link confidence.
- Structural containers do not become behavioral impact items.

Files changed: `src/extendcodeagent/{analysis,graph/analyzers,twin/lifecycle.py}`; focused unit and
integration tests; handoff documentation.
Files currently being edited: final PR-C documentation and evidence metadata.

Exact tests executed:
- `.venv/bin/pytest -q tests/unit/test_python_semantic.py tests/unit/test_graph_analysis.py tests/integration/test_twin_lifecycle.py`
- `tools/local/all-fast`
- `tools/local/test-integration`
- `tools/local/build`
- `tools/local/benchmark-pr-c`
Exact results: focused `15 passed`; final PR head all-fast Ruff PASS, strict mypy PASS,
`45 passed in 0.18s`; integration `8 passed in 0.35s`; sdist/wheel build success. Post-merge
`main`: all-fast `45 passed in 0.16s`; integration `8 passed in 0.37s`.
Benchmark results: 64 files, 423 nodes, 2,194 edges; cold semantic index 623.969 ms;
dependency-aware two-file incremental refresh 282.761 ms; DB+WAL 3,975,808 bytes; max RSS
44,720 KiB; 100 impact queries p50 0.0649 ms/p95 0.3118 ms; 100 lexical `rg` baseline queries
p50 2.2538 ms/p95 3.3223 ms. The baselines are not quality-equivalent.
OpenCode version: not tested; PR-D acceptance.
Model/provider: none; PR-C is deterministic.
Routing profile: not applicable.
Known failures: none.
Known limitations: LSP enrichment is optional in the plan and deferred because no host-neutral LSP
consumer exists; Python analysis intentionally reports unresolved dynamic dispatch as uncertain;
incremental semantic refresh parses all Python ASTs to build a correct symbol index before emitting
only affected facts, so its scaling advantage is not yet proven.
Uncommitted work: this docs-only closeout until merged.
Temporary work: none.

Next exact action: merge this docs-only closeout, create `agent/pr-d-opencode-mcp` from updated main,
then verify current OpenCode stable plugin/MCP APIs and install/version before adapter design.
Next files: current OpenCode official docs/API/package types, PR-D execution-plan slice, then new
`adapters/opencode/`, `mcp/`, and versioned host-neutral interface tests.
Next commands: sync main; create PR-D branch; verify `opencode --version` or install current stable;
record API/version evidence before production adapter changes.
Rollback path: revert merge `ef6db532f74be97cbd86483b0bbe89ee6ac95a29`; do not reset unrelated work.
