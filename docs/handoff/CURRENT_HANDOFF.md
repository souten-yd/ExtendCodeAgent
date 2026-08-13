# Current Handoff

Updated: 2026-08-13 (Asia/Tokyo)

Current branch: `agent/pr-g-closeout`
Current PR: closeout not created
Base commit: `3386cfa429caf5b476e8abc5d52d87a8ab99c719`
Latest commit: `3386cfa429caf5b476e8abc5d52d87a8ab99c719` (PR-G squash merge)
Milestone: PR-G merged-state closeout
Current task: publish/merge closeout, then start PR-H JS/TS semantic work
Status: PR-G complete and merged; closeout in progress

Completed:
- PR #14 exact head `1189c966a71d410a42ab3f51ed35d18b4c2f5af9` was mergeable/CLEAN
  and squash-merged as `3386cfa429caf5b476e8abc5d52d87a8ab99c719`;
- post-merge main passed all-fast (85 Python in 0.64s, adapter 9) and Python/TypeScript builds;
- extended the existing `PolicyModelRouter`; no parallel router was introduced;
- added all deterministic adaptive signals, explainable endpoint decisions, execution wall time,
  escalation/locality, complete token/cache/tool/cost accounting, and fail-closed provider errors;
- added OpenAI-compatible local and stable OpenCode 1.18.18 host adapters behind `ModelAdapter`;
- preserved local-only and remote-source privacy enforcement in focused tests;
- added bounded output/reasoning control after an unbounded 27B run exceeded ten minutes;
- corrected OpenCode tool disabling from `{}` to `{"*": false}` after complete-session metrics
  proved that an empty map still allowed tools;
- added Strategy with deterministic scope/impact/test/migration/compatibility/rollbackability/
  performance/maintainability/cost/uncertainty metrics and provenance;
- model synthesis only proposes scope/explanation/rollback; no A/B/C fallback exists; tied scores
  produce no selection and require a decision;
- ran six same-repository scenarios across local-low/local-medium and host native/off/advisory/
  active; compact results are under `docs/evidence/pr-g/` and no run changed the worktree;
- verified frontier failure is reported unavailable for all 18 attempts, not as an empty success.

In progress:
- merged-state documentation closeout only.

Not started:
- PR-H JS/TS and on-demand deep graph;
- PR-I Research/Evidence/Traceability/project convergence;
- final multi-repository Release Validation.

Architecture classification:
- REUSE/EXTEND `PolicyModelRouter`, routing/config/privacy contracts, Graph evidence, and policy;
- NEW only the live transport implementations and Strategy domain behind existing boundaries;
- DO NOT PORT KasaneCore DeepPlanner, Atlas/Nexus schemas, or fixed fallback alternatives.

Files changed: `src/extendcodeagent/core/model_routing/`, `src/extendcodeagent/strategy/`, focused
tests, `tools/local/pr-g-evaluate`, PR-G evidence, and canonical handoff/status documents.
Files currently being edited: documentation/evidence only.

Exact tests executed:
- repeated focused Ruff/mypy and
  `.venv/bin/pytest -q tests/unit/test_model_routing.py tests/unit/test_live_model_adapters.py tests/unit/test_strategy.py`;
- latest focused result: 19 passed;
- final all-fast: Ruff/format/strict mypy PASS, Python 85 passed in 0.57s, adapter 9 passed;
- final build: Python sdist/wheel and TypeScript build PASS;
- final integration: Python 13 passed in 0.88s, adapter 9 passed;
- `tools/local/pr-g-evaluate --tiers local-low,local-medium --modes off,advisory,active`;
- `tools/local/pr-g-evaluate --tiers host --modes off,advisory,active`;
- `tools/local/pr-g-evaluate --tiers frontier --modes off,advisory,active`.

Exact results:
- focused Ruff and strict mypy PASS; focused pytest 19 passed;
- local-low off/advisory/active: 1/4/6 successes, 0 tool calls, 325/936/983 input+output tokens;
- local-medium off/advisory/active: 1/6/6, 0 calls, 310/911/958 tokens;
- host native/off/advisory/active: 6/2/4/6 successes; 40/0/0/0 tool calls;
- frontier: 0/18 available; all failed closed as OpenCode `APIError`;
- worktree mutation: false for every evaluation process.

Benchmark results:
- host native: 78,016 ms, 39,606 new input, 352,000 cached input, 2,431 output, 40 calls;
- host active: 14,509 ms, 1,226 new input, 12,544 cached input, 182 output, 0 calls;
- local-low active: 1,061 ms total for six cases; local-medium active: 6,327 ms.

OpenCode version: 1.18.18.
Model/provider: Ollama Qwen3 0.6B; Ollama Qwen 3.6 27B Q5; OpenCode
`opencode/big-pickle`; unavailable `llama/llama-3.3-70b-instruct` frontier path.
Routing profile: deterministic fake coverage plus real native/off/advisory/active controlled runs.

Known failures: configured frontier returns OpenCode `APIError`; no frontier quality claim.
Known limitations: local-low is stochastic; active is not made default; stable OpenCode prompt lacks
a per-request max-output field; host cache tokens must not be conflated with new input.
Uncommitted work: closeout documentation only.
Temporary work: evaluation-only Ollama `qwen3:0.6b` remains installed; no temporary repo files.

Next exact action: commit/push/merge the closeout, fast-forward main, create
`agent/pr-h-js-ts-deep-graph`, and begin bounded PR-H inspection.
Next files: current documentation/evidence only, then PR metadata.
Next commands:

```bash
cd /home/souten/ExtendCodeAgent
.venv/bin/python -m json.tool docs/evidence/pr-g/model-evaluation.json >/dev/null
tools/local/all-fast
tools/local/build
tools/local/test-integration
git diff --check
git status --short
```

Rollback path: revert only PR-G commits on this branch; merged PR-F closeout `7b1fb75` remains the
clean base. Do not remove or rewrite PR-B through PR-F implementations.
