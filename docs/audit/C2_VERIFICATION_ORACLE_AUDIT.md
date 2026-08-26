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

---

# Are norms and decision history the same kind of problem as negative knowledge?

Factors a and b were carried as unaddressed on the strength of being plausible. Negative
knowledge earned its mechanism by measurement — 77% of an agent's baseline actions were
searches that found nothing — so the question is whether these two resemble it. They are
separated by one property: whether the fact can be recomputed from the code.

`tools/local/c2_norms_and_rationale.py`, five repositories, 300 commits each.

## a — norms are derivable, and one example carries them

| convention | flask | httpx | requests | scrapy | django |
|---|---|---|---|---|---|
| test style | 1.000 | 1.000 | 1.000 | 0.999 | 0.890 |
| assertion style | 1.000 | 1.000 | 1.000 | 0.964 | **0.999 `self.assert*`** |
| import style | 0.747 | 0.586 | 0.779 | 0.863 | 0.912 |
| annotations on public functions | 0.725 | 0.561 | 1.000 | 0.541 | 1.000 |
| docstrings on public functions | 0.817 | 0.787 | 0.610 | 0.863 | 0.755 |

The conventions that exist are followed 89% to 100% of the time, and they disagree across
projects: Django's 99.9% is `self.assert*` where everyone else's 100% is a bare `assert`.
A rule written into the runtime would be wrong for one of them. The remaining rows are not
conventions at all — at 0.561 there is no rule to state, and asserting one would be false.

So a norm is unlike an absence in the way that matters: it is a fact *about* positive facts
and is recovered by counting them. It needs no store and no engine. It needs one real
example, which costs 74 to 117 tokens at the median against the 367-line file an agent
opens to find the same thing. `attach_exemplar` sends exactly one; a second adds nothing.

## b — rationale is rarely lost, and 20x rarer than absence

| | flask | httpx | requests | scrapy | django |
|---|---|---|---|---|---|
| commits stating a constraint | 4.0% | 2.7% | 3.0% | 6.0% | 14.0% |
| constraint not kept in the code | 3.7% | 2.3% | 1.7% | 4.0% | 6.0% |

A reason genuinely cannot be recomputed — no reading of current code recovers why an
alternative was rejected — so b is structurally like c. It is not like c in size. Between
1.7% and 6% of commits state a constraint that does not survive into the file they changed,
against the 77% of agent actions that were redundant searches. A mechanism earning its
place at 77% does not earn it at 4%.

b is therefore left unbuilt, and this is the measurement that says so rather than an
omission. If it is ever built, the same shape applies — the constraint, the revision it was
stated at, and what reverses it.

## Bounds

- The rationale measure is a keyword proxy: constraint-stating phrasing in a commit
  message, against whether that vocabulary survives in the changed files' comments. It will
  miss a constraint stated in unusual words and count a coincidence of vocabulary as
  recovery. It is reported as an order of magnitude, not a rate.
- Norm consistency is measured over conventions expressible in the AST. A convention about
  naming, layering or error handling is not covered.
