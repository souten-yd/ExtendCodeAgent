# Next Task

Finish PR-G publication, merge its closeout, then start PR-H without mixing Research/Traceability.

1. Run PR-G `tools/local/all-fast`, `tools/local/build`, relevant integration, diff inspection, and
   verify the compact evidence JSON.
2. Publish PR-G, verify exact remote head/mergeability, merge it, rerun main gates, then merge a
   documentation-only closeout with merged hashes and the frontier limitation.
3. Create `agent/pr-h-js-ts-deep-graph` from exact closeout main.
4. Read only PR-H and JS/TS analyzer slices, inspect current analyzer plugin contracts/callers/tests,
   and classify REUSE/ADAPT/NEW before implementation.
5. Implement JS/TS semantic analysis first. Use PR-G evidence to keep deeper CFG/DFG/framework
   graphs on-demand; do not add Research/Evidence/Traceability from PR-I.
6. Build curated JS/TS ground truth and real measurements before deciding which deep graph is worth
   its maintenance/query cost.

Resume:

```bash
cd /home/souten/ExtendCodeAgent
tools/local/all-fast
tools/local/build
git diff --check
git status --short
```

Keep Research/Traceability/project convergence (PR-I) outside PR-H.
