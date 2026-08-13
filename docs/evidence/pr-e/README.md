# PR-E context, test, and runtime evidence

These compact artifacts were produced from commit `47d47cde2520d872787fb6307213c0fd716840dd`
on 2026-08-13 (Asia/Tokyo).

- `real-repository-benchmark.json`: `tools/local/pr-e-benchmark`
- `real-opencode-smoke.json`: `tools/local/opencode-smoke`
- `real-opencode-runtime-smoke.json`:
  `EXTENDCODEAGENT_SMOKE_MODEL=ollama/qwen3.6-27b-q5_k_m:latest tools/local/opencode-runtime-smoke`

The benchmark demonstrates a bounded weak context package and two graph-linked test candidates for
the measured implementation ref without a full-suite fallback. The candidate health remains
`suspect`; candidate discovery is not verification evidence.

The model-free smoke confirms stable OpenCode 1.18.18 integration without creating runtime
observations. The real local-model smoke confirms that an actual OpenCode agent `bash` tool event is
normalized and persists across restart. Stable OpenCode did not provide explicit exit metadata, so
the observation truthfully remains `observed`, not `passed`.

The two OpenCode smokes were initially started concurrently and one failed with `database is
locked` because both used OpenCode's shared database. That orchestration error is not counted as a
product result. Both commands were rerun serially and passed; the JSON artifacts contain the serial
runs.

This is PR-E evidence only. It does not claim live model routing or cross-model quality evaluation,
which remain PR-G scope.
