# Next Task

Finish PR-H JS/TS/deep-graph scope without mixing Research/Traceability.

1. Publish/merge the current documentation-only closeout with PR #14 merge hashes, post-merge gates,
   and the frontier limitation.
2. Fast-forward main and create `agent/pr-h-js-ts-deep-graph` from the exact closeout head.
3. Inspect the measured ControlDeck affected path ratio and add a minimal auto full-build selection
   path to the existing Twin lifecycle; do not add a parallel refresh engine.
4. Run focused Twin and JS/TS tests, then repeat the ControlDeck comparison.
5. Add compact benchmark and curated FP/FN evidence, then decide whether any on-demand framework or
   deep graph closes a measured task gap.
6. Read only PR-H and JS/TS analyzer slices, inspect current analyzer plugin contracts/callers/tests,
   and classify REUSE/ADAPT/NEW before implementation.
4. Implement JS/TS semantic analysis first. Use PR-G evidence to keep deeper CFG/DFG/framework
   graphs on-demand; do not add Research/Evidence/Traceability from PR-I.
5. Build curated JS/TS ground truth and real measurements before deciding which deep graph is worth
   its maintenance/query cost.

Resume:

```bash
cd /home/souten/ExtendCodeAgent
git switch main
git pull --ff-only origin main
git status --short
git switch -c agent/pr-h-js-ts-deep-graph
```

Keep Research/Traceability/project convergence (PR-I) outside PR-H.
