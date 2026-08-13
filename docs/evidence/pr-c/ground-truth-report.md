# PR-C Ground-Truth Review

Date: 2026-08-13  
Substantive revision: `e3a65b7`

The curated fixtures are deliberately small enough to inspect without trusting the analyzer. They
exercise deterministic AST facts and typed graph facts separately so route/resource conventions do
not leak into the Python analyzer.

| Case | Expected | Observed | FP/FN review |
|---|---|---|---|
| function to caller | reverse `calls` reaches the caller directly | PASS | no FP/FN in fixture |
| route to handler | `handled_by` forward expansion marks handler direct | PASS | no FP/FN in fixture |
| handler to DB effect | forward typed side-effect traversal returns DB write | PASS | no FP/FN in fixture |
| implementation to test | reverse call chain projects the test candidate | PASS | no FP/FN in fixture |
| transitive dependency | weakest edge confidence is retained over multiple callers | PASS | no FP/FN in fixture |
| ambiguous call | `may_call` is inferred at 0.35 and appears in uncertainty | PASS | intentional name-collision FP risk |

The end-to-end persisted fixture additionally verifies `leaf -> caller -> test` and a dynamic
`client.leaf()` candidate after SQLite persistence. The dynamic candidate is not labeled verified.

Known false-positive boundary: `pyname://leaf` can bridge unrelated same-named symbols. These results
remain uncertainty items and can be excluded through `min_confidence >= 0.7`.

Known false-negative boundary: reflective calls, monkey patching, generated imports, and runtime-only
dispatch are not inferred by PR-C. LSP/runtime enrichment is deferred to a later bounded layer.

Incremental correctness sample: a removed imported definition re-analyzes the unchanged importer and
changes its former resolved `calls` edge into low-confidence `may_call`; the stale resolved edge is
invalidated.
