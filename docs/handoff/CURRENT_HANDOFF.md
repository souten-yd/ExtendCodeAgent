# Current Handoff

Updated: 2026-08-13 (Asia/Tokyo)

Current branch: `agent/pr-d-closeout`
Current PR: not created
Base commit: `1cc7fd26a4e13aaca051edba2d92a91827a2e5b6`
Latest commit: `1cc7fd2` (PR-D squash merge)
Current milestone: PR-D closeout / PR-E preparation
Current task: publish merged-state handoff and open the PR-E starting boundary
Task status: in progress

Goal: record the verified PR-D merge without adding implementation, then begin a separate PR-E for
Context, Test, and Runtime Intelligence.

Scope:
- synchronize canonical status and handoff documents with merged PR #8;
- record post-merge local gates;
- define the bounded PR-E start order and exclusions.

Out of scope:
- PR-E production code on this closeout branch;
- Blueprint/Convergence, live model routing/Strategy, JS/TS semantic analysis, and Research.

Completed:
- PR-B Graph/Twin merged as `0618cd29` and its closeout merged;
- PR-C structural/Python semantic/path/impact merged as `ef6db532` and its closeout merged;
- PR-D stable OpenCode/MCP adapter published as PR #8 from exact remote head
  `86b7f511d789c7d191bcbbd0b378eb790d0d3a44`;
- PR #8 was `MERGEABLE/CLEAN`, had no configured GitHub checks, and was squash-merged as
  `1cc7fd26a4e13aaca051edba2d92a91827a2e5b6`;
- fast-forwarded local `main` to the exact merge and passed post-merge all-fast and integration.

In progress:
- closeout documentation branch and PR.

Not started:
- PR-E behavior tests or implementation.

Important architecture decisions:
- PR-D targets stable OpenCode 1.18.18; V2 remains a separate future adapter.
- Plugin and MCP share the authenticated `extendcodeagent.local.v1` sidecar/application service.
- Native and fallback file events share one bounded queue; Chokidar remains adapter-only.
- PR-E must extend the current CapabilityPolicy and Graph/Twin/Impact services rather than create a
  parallel coordinator or router.

Important invariants:
- host-neutral packages never import OpenCode/plugin/MCP SDK types;
- off computes nothing, shadow has no native behavior effect, advisory requires explicit use;
- historical green evidence is never treated as fresh for a newer source revision;
- unavailable evidence is never promoted to passed/verified.

Files changed: closeout documentation only.
Files currently being edited: `docs/CURRENT_STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`,
`docs/handoff/NEXT_TASK.md`, and `docs/handoff/IMPLEMENTATION_LOG.md`.

Exact tests executed:
- PR-D exact substantive head: `tools/local/all-fast`; `tools/local/test-integration`;
  `tools/local/build`; `tools/local/opencode-smoke`;
- PR-D final publication head: `tools/local/all-fast`;
- merged `main`: `tools/local/all-fast`; `tools/local/test-integration`.

Exact results: merged-main Ruff/mypy PASS; Python unit/architecture `49 passed in 0.31s`; adapter
`6 passed in 4.26s`; Python integration `9 passed in 0.43s`; repeated adapter `6 passed in 4.26s`.
Benchmark results: exact PR-D smoke startup medians native 1,046 ms and plugin 1,070 ms (+24 ms),
151 ms initial/tool/external revision observation, 1,109 ms reconnect, three stable/persisted
revisions, and no off-mode revision change. Raw startup samples remain in `docs/evidence/pr-d/`.
OpenCode version: 1.18.18.
Model/provider: none used for PR-D acceptance; real-model work begins at its planned milestone.
Routing profile: not applicable.
Known failures: native watcher events omitted ordinary source edits and Git lock events initially
caused a feedback loop; adapter filtering plus Chokidar fallback fixed the measured path.
Known limitations: the three-run startup measurement is smoke evidence, not a distribution; stable
OpenCode native watcher behavior should be retested on future versions.
Uncommitted work: closeout documentation only.
Temporary work: ignored build artifacts and dependency installs are reproducible; no tracked smoke
database is present.

Next exact action: commit/push this closeout, create and merge its docs-only PR, fast-forward main,
run all-fast, then create `agent/pr-e-context-test-runtime` from exact updated main.
Next files: closeout docs; then PR-E behavior tests and host-neutral contracts/services.
Next commands: `git diff --check`; commit; push; create/merge closeout PR; `git switch main`;
`git pull --ff-only origin main`; `tools/local/all-fast`; create the PR-E branch.
Rollback path: revert only the closeout documentation commit/PR; PR-D implementation is already
merged independently as `1cc7fd2`.
