# PR-H JS/TS Ground-Truth Review

Date: 2026-08-14

The unit fixtures and ControlDeck sample are intentionally reviewable without trusting inferred
facts. `calls` requires a resolved local/import/class target; unresolved dynamic calls remain
`may_call` at confidence 0.35.

| Case | Expected | Observed | FP/FN review |
|---|---|---|---|
| imported function to caller | imported alias resolves to file-qualified definition | PASS | no FP/FN in fixture |
| class and inherited method | direct/inherited receiver resolves with reduced inherited confidence | PASS | no FP/FN in fixture |
| implementation to named test | reverse call path recommends the test | PASS | no FP/FN in fixture |
| Playwright inline test | `test(..., callback)` becomes a stable test node | PASS | 92/92 ControlDeck calls represented |
| ambiguous dynamic call | unresolved receiver emits inferred `may_call` | PASS | intentional candidate, never verified |
| same-name definitions | file-qualified refs remain distinct | PASS | no collision in fixture |

ControlDeck contains 92 textual Playwright `test(` declarations and the graph contains 92 inline
test nodes. Thirty-nine have at least one statically supported call/reference. Examples manually
checked against source include `terminal-input.spec.ts#test@10` to
`TerminalInputController.handleAck`, `prepareTerminalPaste`, and `enqueuePaste`.

Known false-positive boundary: an unresolved dynamic receiver may share a `jsname://` target with an
unrelated same-named member. It remains inferred at 0.35 and is excluded by a 0.7 confidence floor.

Known false-negative boundary: browser/API behavior, runtime dependency injection, computed member
names, callbacks passed through libraries, and JSX rendering are not verified static calls. The 53
ControlDeck tests without static evidence are retained as tests, not fabricated links. This gap does
not justify always-on CFG/DFG: those analyses would not resolve remote browser/API behavior. A
framework UI analyzer remains on-demand and independently configurable if a concrete UI impact
benchmark later demonstrates recall benefit.
