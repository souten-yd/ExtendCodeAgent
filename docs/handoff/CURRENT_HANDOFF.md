# Current Handoff

Updated: 2026-08-14 (Asia/Tokyo)

Current branch: `agent/pr-i-research-traceability`
Current PR: not created
Base commit: `f3d8016b30b0d7fa1972a1ee5bcb108f8f1148c8`
Latest commit: `f3d8016b30b0d7fa1972a1ee5bcb108f8f1148c8` (PR-H closeout merge)
Milestone: PR-I Research/Evidence/Traceability/project convergence
Current task: inspect existing contracts/callers/tests and KasaneCore domain behavior
Status: PR-I behavior-first contracts collected RED as expected

Completed:
- added official tree-sitter JavaScript/TypeScript/TSX parsing dependencies;
- added independently selected JS/TS and composite analyzers behind existing GraphAnalyzer;
- added file-qualified definitions, local import resolution, references, direct/inherited calls,
  low-confidence dynamic `may_call`, decorators, inheritance, test classification, diagnostics;
- composed language-owned Python and JS/TS canonical resolvers without changing generic Impact;
- verified SQLite incremental dependent-importer refresh and implementation-to-test impact;
- focused 12 tests PASS; all-fast PASS with 90 Python and 9 adapter tests;
- corrected py-tree-sitter 0.26.0 native crashes by pinning 0.25.2, retaining one parser per grammar,
  streaming Node traversal, and retaining only pure-Python descriptors across files;
- repeated the exact ControlDeck cold/incremental Twin path in three independent processes with no
  crash and stable 1,255 nodes / 3,888 edges;
- added language-neutral auto full refresh when the dependency closure covers at least 40% of
  current module facts; three ControlDeck runs improved from about 5.0s to about 1.19s;
- represented all 92 ControlDeck Playwright inline tests; 39 have static evidence and dynamic cases
  remain unlinked rather than falsely verified;
- recorded a reproducible benchmark and human-reviewable FP/FN report under `docs/evidence/pr-h/`;
- rejected always-on CFG/DFG/state/event/UI work because it does not close the measured browser/API
  evidence gap; deeper analyzers stay on-demand pending a concrete benchmark.
- created PR #16; no GitHub Actions checks are configured.
- PR #16 exact head `46306bf225035f2c40798a81992ac9f525eed5c0` was repeatedly
  `MERGEABLE/CLEAN` and squash-merged as `fdeeb4e694fa7f416bb3ac7e92f49952d31e1767`;
- post-merge main all-fast passed with 91 Python and 9 adapter tests; Python/TypeScript builds pass.
- PR-G closeout PR #15 squash-merged as `fe61a16e8f7f07e760d99ca449bc09c90166a6c5`;
- created PR-H branch from exact clean closeout main;
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
- implement minimal research and traceability domain behind existing contracts.

Not started:
- PR-I Research/Evidence/Traceability/project convergence;
- final multi-repository Release Validation.

Architecture classification:
- REUSE/EXTEND `PolicyModelRouter`, routing/config/privacy contracts, Graph evidence, and policy;
- NEW only the live transport implementations and Strategy domain behind existing boundaries;
- DO NOT PORT KasaneCore DeepPlanner, Atlas/Nexus schemas, or fixed fallback alternatives.

Files changed: `src/extendcodeagent/core/model_routing/`, `src/extendcodeagent/strategy/`, focused
tests, `tools/local/pr-g-evaluate`, PR-G evidence, and canonical handoff/status documents.
Files currently being edited: benchmark/evidence design next.

Exact tests executed:
- repeated focused Ruff/mypy and
  `.venv/bin/pytest -q tests/unit/test_model_routing.py tests/unit/test_live_model_adapters.py tests/unit/test_strategy.py`;
- latest focused result: 19 passed;
- final all-fast: Ruff/format/strict mypy PASS, Python 85 passed in 0.57s, adapter 9 passed;
- final build: Python sdist/wheel and TypeScript build PASS;
- final integration: Python 13 passed in 0.88s, adapter 9 passed;
- PR-H parser safety focused gate: Ruff PASS, strict mypy PASS, 5 focused tests PASS;
- auto refresh focused gate: Ruff PASS, strict mypy PASS, 18 focused tests PASS;
- three independent `PYTHONFAULTHANDLER=1` ControlDeck cold plus App.tsx refresh processes.
- final all-fast: Ruff/format/strict mypy PASS, Python 91 passed, adapter 9 passed;
- final build: Python sdist/wheel and TypeScript build PASS;
- final integration: Python 15 passed and adapter 9 passed;
- final benchmark rerun PASS; `git diff --check origin/main...HEAD` PASS; boundary grep found no
  OpenCode/model/research dependency in Graph/Twin implementation.
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
- PR-H ControlDeck parser safety: 3/3 PASS without native crash; each snapshot contained 1,255
  nodes and 3,888 edges before and after refresh.
- final PR-H gate: 91 Python tests, 9 adapter tests, 15 Python integration tests, both builds PASS.

Benchmark results:
- host native: 78,016 ms, 39,606 new input, 352,000 cached input, 2,431 output, 40 calls;
- host active: 14,509 ms, 1,226 new input, 12,544 cached input, 182 output, 0 calls;
- local-low active: 1,061 ms total for six cases; local-medium active: 6,327 ms.
- ControlDeck cold: 3,064 / 3,083 / 3,027 ms; incremental: 5,000 / 5,052 / 4,964 ms;
  DB 6,569,984 bytes; max RSS 69,544 / 69,032 / 69,276 KiB.
- equal-baseline ControlDeck explicit full: 1,187 ms versus incremental 4,931 ms; automatic full
  selection: 1,193 / 1,192 / 1,187 ms, identical fact counts.

OpenCode version: 1.18.18.
Model/provider: Ollama Qwen3 0.6B; Ollama Qwen 3.6 27B Q5; OpenCode
`opencode/big-pickle`; unavailable `llama/llama-3.3-70b-instruct` frontier path.
Routing profile: deterministic fake coverage plus real native/off/advisory/active controlled runs.

Known failures: configured frontier returns OpenCode `APIError`; no frontier quality claim.
Known limitations: local-low is stochastic; active is not made default; stable OpenCode prompt lacks
a per-request max-output field; host cache tokens must not be conflated with new input. PR-H's
current JS/TS analyzer builds a transient cross-file index; broad dependency closures therefore
select full refresh. A persisted symbol index remains a future optimization, not a PR-H requirement.
Uncommitted work: PR-I decision record and red behavior tests.
Temporary work: evaluation-only Ollama `qwen3:0.6b` remains installed; no temporary repo files.

Next exact action: commit red tests/decision, implement `research` and `traceability` pure domains,
then run focused Ruff/mypy/pytest before storage or adapter work.
Next files: PR-I plan/audit slices, current evidence/convergence/storage/adapter contracts and tests.
Next commands:

```bash
cd /home/souten/ExtendCodeAgent
git status --short
git status --short
rg -n "Evidence|Claim|Research|Traceability|Requirement" src tests
```

Rollback path: switch to main; PR-H closeout is `f3d8016`. PR-I changes stay isolated on this branch.
Do not rewrite PR-B through PR-H.
