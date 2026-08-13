# Current Handoff

Updated: 2026-08-14 (Asia/Tokyo)

Current branch: `agent/productization-phase-closeout`
Current PR: documentation-only productization closeout; not yet published
Base commit: `a87d2fc6453c2f0d7bb9d1ccb8e48e16e2b7f1a7`
Latest synchronized main: `a87d2fc6453c2f0d7bb9d1ccb8e48e16e2b7f1a7`
Milestone: A-I implementation complete; evidence-driven Productization active
Current task: merge this docs-only closeout, then start RV-0 Baseline Release Validation
Status: PR #20 and PR #21 merged; Transparent Task-aware PI planned; RV-0 next

## Current source of truth

- PR #20 merged as `731f587d600d5a563a26231d801e248f5f176c32`.
- PR #21 merged as `a87d2fc6453c2f0d7bb9d1ccb8e48e16e2b7f1a7`.
- The active sequence is RV-0, blocking defect fixes, TA-0, TA-1, TA-2, TA-3, conditional
  Runtime Bridge/deep analysis, TA-FINAL, then the production-capable decision.
- No later stage may start before the preceding acceptance evidence passes.
- Current installed and npm-stable OpenCode: `1.18.18` (checked 2026-08-14).
- Known frontier result: `0/18` available; OpenCode `APIError`; diagnose native provider/auth/model
  before changing the adapter or Project Intelligence Core.
- Known local-low limitation: Qwen3 0.6B is stochastic; use repeated distributions.

Canonical execution order:

1. `docs/PRODUCTIZATION_AND_MODEL_EVALUATION_PLAN.md`
2. `docs/TRANSPARENT_PI_ORCHESTRATION_PLAN.md`
3. `docs/CODEX_PRODUCTIZATION_EXECUTION_GUIDE.md`
4. `docs/handoff/NEXT_TASK.md`

## Exact baseline gates on synchronized main

- `tools/local/all-fast`: PASS; Ruff/format/strict mypy, Python 99 passed, adapter 9 passed.
- `tools/local/test-integration`: PASS; Python 16 passed, adapter 9 passed.
- `tools/local/build`: PASS; Python sdist/wheel and TypeScript build.
- Two pre-existing untracked validation helpers are preserved and must not enter the docs-only PR:
  `tools/local/release-validation-matrix` and `tools/local/release_validation_matrix.py`.

## Current environment/model continuity

- OpenCode: installed `1.18.18`; npm stable `1.18.18`.
- Local-low continuity: Ollama Qwen3 0.6B; repeated behavior is stochastic.
- Local-practical continuity: Ollama Qwen 3.6 27B Q5.
- Host continuity: OpenCode `opencode/big-pickle` from the PR-G evidence; RV-0 must discover and
  record the current default rather than assume it is unchanged.
- Frontier continuity: `llama/llama-3.3-70b-instruct` returned OpenCode `APIError` in all 18 prior
  attempts. RV-0 starts with PI completely off and a native minimal provider smoke.
- Exact current OpenCode configuration, endpoint availability, context sizes, privacy profiles,
  repository commits, CPU/RAM/GPU, and process lifecycle evidence remain RV-0 work.

## RV-0 scope and required outputs

RV-0 is validation-first and adds no production feature by default. It must revalidate plugin load,
automatic sidecar lifecycle, MCP/tool calls, edits and refresh, restart/reopen/reconnect, all rollout
modes, native fallback, and current model tiers across fixed repositories and repeated versioned
tasks. Failures receive one required primary classification and are ranked by frequency, severity,
and user value.

Required outputs under `docs/evidence/final/`:

- `environment.md`
- `baseline-gap-report.md`
- `model-matrix.json`
- `task-results.json`
- `opencode-integration.json`
- `performance.json`

Blocking defects may be fixed only after measured failure, root cause, insufficiency of existing
configuration/capability, minimal change, retest, and before/after evidence. TA-0 cannot start until
RV-0 and blocking defect acceptance are complete.

## Next exact commands

```bash
cd /home/souten/ExtendCodeAgent
git status --short
git diff --check
tools/local/all-fast
# publish and merge the docs-only PR, then:
git switch main
git pull --ff-only origin main
git status --short
git rev-parse HEAD
git switch -c agent/release-validation-baseline
```

After creating the RV-0 branch, first write `docs/evidence/final/environment.md`; do not import the
pre-existing untracked validation helpers until their provenance, scope, and correctness have been
reviewed against the new RV-0 requirements.

Rollback path: switch to synchronized `main`. The docs-only branch changes no production code.
