# Factor 4, measured against tests that were observed to verify

Factor 4 — knowing which tests must run for a change — has been the one unresolved factor.
Its recall was measured against an oracle that called a commit's required tests the test
files that commit edited. That oracle has now been audited, so this re-measures the factor
against tests observed to fail when the change was removed.

## The oracle change does not explain the shortfall

Same commits, same evidence selection, two definitions of the answer:

| repository | cheap oracle | revert oracle | cases |
|---|---|---|---|
| flask | 0.833 | 0.800 | 15 |
| httpx | 0.514 | 0.500 | 24 |

The prediction that recall was understated by the weak oracle was wrong: it moves by 1.5 to
3 points, inside the noise of fifteen cases. The audit was worth doing and the shortfall is
real. What the numbers do show is that difficulty is a property of the repository, not of
the factor: 0.80 against 0.50 on the same code.

## What is missed is absent, not mis-ranked

Six of httpx's thirteen misses are one file. `tests/models/test_url.py` imports `httpx` and
nothing else; the changes are to `httpx/_urlparse.py`. There is no import, call or
reference edge between them, and no amount of traversal finds one. The test verifies a
behaviour reached through the package's facade.

This is the distinction the structural model cannot make. A code graph holds
code-to-code relations. Which test verifies which change is a different relation that
happens to be *sometimes* correlated with it.

## Execution holds the pair, and the question is how wide to ask it

One coverage run of httpx's suite, `dynamic_context = test_function`, 6.7 seconds.
`tools/local/c2_coverage_selection.py`, 23 cases:

| | candidates | recall |
|---|---|---|
| tests that executed the changed **file** | 268.9 | 1.000 |
| tests that executed the changed **functions** | 159.9 | 0.957 |
| current structural selection | small | 0.500 |

Coverage recovers what the graph cannot: `tests.models.test_url.test_idna_url` executes
`_urlparse.py`, which is the pair no edge holds. Narrowing from file to changed function
sheds 40% of the candidates for four points of recall.

160 of 824 tests is 19% of the suite, which meets the stated target of a selection costing
20-30% of a full run. It is not a small candidate set, and it is not meant to be: this is
candidate generation, where recall is what matters, and cost-aware ranking is a separate
step that has not been built.

## What was built from this

The single miss at symbol granularity is a change that adds a function: there is no symbol
at the base revision for coverage to have reached, so the question returns nothing. Asking
the containing file instead recovers it, which is now `covering_tests(..., fallback_refs=)`
— a fallback and not a default, because the file question is 68% wider.

Fixing that exposed a second thing. `covering_tests` never checked that an observation had
reached the refs it was asked about; it returned the tests from every usable observation.
The narrow question was never actually being put, so the fallback could not have fired.

## Bounds

- Two repositories, 39 cases. flask's coverage run was not made; its 0.80 is against the
  structural relation only.
- Coverage was collected once, at the base revision, from a suite run that had eight
  pre-existing failures.
- Candidate width is counted in tests, not in runtime. A selection of 160 fast unit tests
  and one of 160 end-to-end tests are not the same cost, and this does not distinguish them.
