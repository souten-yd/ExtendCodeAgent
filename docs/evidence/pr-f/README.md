# PR-F Blueprint and task convergence evidence

`benchmark.json` is the compact output of `tools/local/pr-f-benchmark` on commit
`eebf823aa8c61a291156109bd46d2e05d8fee5b6`.

The bounded deterministic fixture contains 200 immutable planned elements, 200 separate Actual
elements, and current-revision verification evidence. It measures create/review/approve/activate,
50 pure convergence evaluations, deterministic completion, persisted report/state, and restart.

This benchmark measures mechanism overhead and durability, not model quality or real-project
semantic accuracy. PR-F intentionally contains no model or OpenCode adapter changes.
