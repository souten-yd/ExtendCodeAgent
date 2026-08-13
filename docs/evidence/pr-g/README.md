# PR-G live routing and Strategy evidence

`model-evaluation.json` records compact summaries from `tools/local/pr-g-evaluate`. Raw model
transcripts are intentionally not committed. The controlled fixture asks the same six repository
questions in off/advisory/active modes: implementation location, impact, test selection,
multi-file diagnosis, medium Strategy scope, and stale-test risk.

Local successful-path results and the final host comparison were measured on implementation commit
`7023585a45d1a77cd6d8e0c71240bf7b5dd59197`. Frontier failure handling was then corrected and
verified on `30bac66a08e1d1364d4c226bbfca69ccbd48e647`. OpenCode was 1.18.18.

The local paths used Ollama `qwen3:0.6b` and `qwen3.6-27b-q5_k_m:latest` through the
OpenAI-compatible adapter with a 128-token output bound and thinking disabled. The host path used
OpenCode `opencode/big-pickle`. Active supplied the same bounded deterministic facts as advisory
but instructed the model to treat them as primary context; it did not authorize edits. The
worktree remained unchanged in every run.

Key result: host native succeeded 6/6 but used 40 tool calls, 39,606 new input tokens, 352,000
cached input tokens, and 78.016 seconds. Host active succeeded 6/6 with zero tool calls, 1,226 new
input tokens, 12,544 cached input tokens, and 14.509 seconds. Local-medium advisory and active both
succeeded 6/6. Local-low was less stable across repeated runs; the recorded exact run was 1/6 off,
4/6 advisory, and 6/6 active. This is evidence that bounded facts help, not enough distributional
evidence to make active the default.

The configured `llama/llama-3.3-70b-instruct` frontier path returned OpenCode `APIError` for all 18
attempts. The adapter now rejects provider failures instead of treating an empty response as
available. Frontier quality is therefore unavailable, not passed, and remains a release-gate item.

An earlier 27B run exceeded ten minutes because the OpenAI-compatible request had no output bound.
Adding `max_output_tokens=128` alone consumed the whole budget in Qwen thinking and produced empty
answers. Current Ollama OpenAI-compatible `reasoning_effort=none` plus the output bound reduced the
final 36 local cases to about 23 seconds. These measured corrections are recorded in
`docs/handoff/DECISIONS.md`.
