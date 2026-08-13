# Next Task

Next task is PR-C Structural/Python Semantic + Path/Impact.

1. Start from updated `main`; verify PR-B and its closeout are merged and all local gates pass.
2. Read only the PR-C and semantic/path/impact sections of the execution plan/migration audit.
3. Inspect KasaneCore `project_twin/static_graph.py`, `analyzers/python.py`, `analysis.py`, and their
   direct tests; classify behavior before implementation.
4. Add curated ground-truth fixtures first: function->caller, route->handler, handler->DB effect,
   implementation->test, transitive dependency, and ambiguous call.
5. Implement structural repository/directory/file/module/class/function/method/test/dependency facts,
   then Python AST definitions/references/imports/calls/decorators/inheritance.
6. Put `py://`/alias behavior behind a Python `CanonicalReferenceResolver`; do not hard-code it in
   generic traversal.
7. Implement bounded path queries and direct/transitive impact with weakest-link confidence,
   uncertainty, explanation paths, and test candidates.
8. Produce a human-reviewable false-positive/false-negative report and repeated-query benchmark.
9. Run focused/integration/all-fast/build/benchmark gates, update handoff, publish and merge PR-C.

Resume:

```bash
cd /home/souten/ExtendCodeAgent
git switch main
git pull --ff-only origin main
git switch -c agent/pr-c-semantic-impact
git status --short
```
