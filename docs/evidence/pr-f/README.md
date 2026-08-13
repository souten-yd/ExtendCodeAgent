# PR-F Blueprint and task convergence evidence

`benchmark.json` is the compact output of `tools/local/pr-f-benchmark` on commit
`73cfff97f4f3187c028f3adce3aa32a0c57144f2`.

The bounded deterministic fixture contains 200 immutable planned elements, 200 separate Actual
elements, and current-revision verification evidence. It measures create/review/approve/activate,
50 pure convergence evaluations, deterministic completion, persisted report/state, and restart.

This benchmark measures mechanism overhead and durability, not model quality or real-project
semantic accuracy. PR-F intentionally contains no model or OpenCode adapter changes.

The recorded result is a standalone run after the final gates. A concurrent run alongside the
test/build gates was slower because of host contention and is not used as the reference value.
