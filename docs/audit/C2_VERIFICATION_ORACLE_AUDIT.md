# What the corpus oracle actually measures

An external reviewer objected that the C2 corpus calls a commit's required tests the test
files that commit edited, and that recall measured against it therefore means less than it
appears to. The objection was correct about the definition — `tools/local/c2_pr_oracle.py`
says so in its own output, `required_tests_are_a_lower_bound: true` — and it had never been
measured. This is that measurement.

## Method

For a commit that changed production code and tests together, the production half is
restored to its parent state while the tests stay at the commit, and the suite is run
before and after. Whatever newly fails detects that change, by construction. No graph,
name or import relation is involved. `tools/local/c2_revert_oracle.py`.

Two guards were needed, and both were found by a wrong answer rather than by design:

- an older commit can hold a module the installed pytest cannot import, and pytest then
  stops before running anything, so before and after come back identical and every such
  commit reads as undetected. An early run reported 89% undetected purely from this.
- reverting a foundational change removes an API rather than a behaviour, and most of the
  suite then fails. Three flask commits produced 237 to 474 failing tests across sixteen or
  more files. Those say nothing about which test verifies what and are reported apart.

## Result — 59 commits across two repositories

| | flask | httpx | pooled |
|---|---|---|---|
| commits measured | 28 | 31 | 59 |
| with a detecting test | 20 | 25 | 45 |
| wholesale breakage (excluded) | 3 | 0 | 3 |
| usable as ground truth | 17 | 25 | 42 |
| **no test detects the change** | 28.6% | 19.4% | **23.7%** |
| cheap oracle missed a detecting file | 5.9% | 0.0% | **2.4%** |
| cheap oracle named a non-detecting file | 23.5% | 4.0% | **11.9%** |
| detecting tests per commit, median | 1 | 1 | **1** |

requests could not be measured at all: its checkout is from 2021 and no single installed environment runs the edited tests of any candidate commit. That is reported rather than worked around.

## What this changes

The error runs opposite to the objection. The cheap oracle was expected to be a lower
bound, missing tests that verify a change; measured, it misses one file in forty-two.
What it does instead is name test files that do not detect the change at all, in one
commit in eight — a commit edits five test files and one of them verifies the fix.

Two consequences:

- Recall measured against the cheap oracle is **understated**, not overstated. Part of what
  the current numbers count as missed is not required verification.
- 28.6% of production changes are detected by no test in the suite. For those commits the
  notion of required tests has no referent, and any selection over them is
  false-sufficient by construction rather than by algorithm.

The median commit is detected by exactly one test. Test selection for these projects is
mostly a problem of finding one test, not of ranking a large candidate set.

## Bounds on this result

- Two repositories, both small and fast, which is why they were measurable at all. The
  three large corpora (scrapy, django, requests) were not.
- Only commits whose own tests run in a single installed environment. Dependency drift
  makes this window narrow; commits outside it are skipped and reported as such.
- Reverting whole production files approximates reverting the commit's production hunks.
  For commits that also refactored, the revert is wider than the fix.
