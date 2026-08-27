# What the envelope carries, and what is still unmeasured

Updated 2026-08-27. Written to separate what this session established from what it did not,
because most of it is deterministic and reusable while the part everyone wants — does the
envelope help an agent — is still open.

## Established, without a model

Every number here comes from a deterministic tool in `tools/local/` and can be re-run.

| | before | after |
|---|---|---|
| changed functions carried as source (flask, 16 applicable) | 6 of 17 | **12 of 16** |
| the same on httpx (24 applicable) | — | **19 of 24** |
| bodies cut for want of excerpt allowance | 13 | **0** |
| a change envelope's composition | — | 91.4% source, 1.1% names, 7.5% frame |
| tokens the needed bodies actually require, flask | — | **1,932 at most**, 1,218 median |
| the same on httpx | — | 6,748 at most, 1,371 median |
| changes whose bodies fit in 8,192 | — | **48 of 48**, both repositories |
| an unbounded envelope | — | 17,917 at most; 8,192 → 18,000 saturates |
| protocol item bound | 32 | **64** (recall 0.361→0.521 flask, 0.483→0.621 django) |
| `selected_evidence_ids` | 337 tokens | removed; ids travel on the items |
| locating files from a description alone | envelope came back empty | **10 of 15**, 3.9 candidate files |
| runtime-checkable sufficiency vs the oracle | — | **agrees 13 of 16** |

Sealed recall held at 1.00 throughout, and the preflight's six conditions pass.

## Established about the task, not the envelope

- `tools/local/c2_feature_bench.py` builds tasks from the changelog sentence alone — no
  tests, no file list, no diff. Fifteen flask cases, all fifteen reproduce.
- `tools/local/c2_acceptance.py` scores by behaviour rather than by the author's tests.
  Checked both ways on three changes: the author's implementation satisfies 4 of 4, and an
  implementation written here from the description, shaped differently, satisfies the same 4.

## The envelope is read, and the content is what does it

Ten flask changes, one frozen implementation, three arms. The control is the same shape,
built by the same path, sized within 23 tokens, and about another case.

| arm | passed | turns | edits | greps |
|---|---|---|---|---|
| the real envelope | **3 of 10** | 11.8 | 1.1 | **3.1** |
| no envelope | 1 of 10 | 13.9 | 1.3 | 4.4 |
| **an envelope about something else** | **0 of 10** | 14.0 | **0.7** | 4.2 |

Three beats zero at the same prompt length, so the content is what helps rather than the
length. And the wrong envelope scores below no envelope at all: wrong evidence is worse than
none, and its arm attempted the fewest edits, which is what being misdirected looks like.

The real envelope also searched least, 3.1 against 4.4, which is the mechanism doing what it
was built to do. It spent the most tokens - 17,262 against 12,837 - and that is the price of
the three runs that got somewhere.

Diagnostic route, not sealed evidence: `docs/evidence/c2-envelope-causality-diagnostic.json`.

## How much of a successful envelope was working

The three runs that passed had their envelopes halved and repeated, and halved again while
they kept passing. A pass at a smaller size was confirmed twice before the search committed
to it.

| change | sent | needed | cut |
|---|---|---|---|
| `provide_automatic_options` | 8,010 tok / 27 items | **2,765 / 6** | 65% |
| IPv6 session transactions | 5,857 / 17 | **3,393 / 8** | 42% |
| `app.query` route decorator | 8,005 / 27 | **8,005 / 27** | none — half already failed |

Two thirds of one envelope was being carried rather than working. The third could not be cut
at all, and it is the one that adds a method rather than changing one: the pattern its
siblings set is the evidence, so there is no small subset of them.

That splits the question by task rather than answering it. Changing an existing function
needs six to eight items; adding one needs the family, and the family is not small.

Three bounds on this. Items are cut from the end, so "six is enough" means those six in that
order and not that six is the number. Three successes, one model, one repository. And the
search only ever goes down, so `app.query` is known to fail at 13 items and unmeasured
between 14 and 27.

Diagnostic route: `docs/evidence/c2-minimum-working-set-diagnostic.json`.

## Still not established

Three of ten is where the local model gets to. Whether a stronger one, or a better envelope,
moves that is open, and so is everything about the feature-task format, where no comparison
has yet run.

## Bounds that are not defects

- **23.7% of production changes are detected by no test.** No selection fixes that.
- **29% of changed functions are not executed by the failing tests**, so coverage cannot rank
  them. `Flask.run` is the shape of it.
- **5 of 15 descriptions locate nothing.** Two name only what the change introduces —
  `TRUSTED_HOSTS` does not exist yet — which is Blueprint's domain, not the Twin's. The other
  three name attributes and class variables, which the graph does not index.
- **Two repositories now.** flask and httpx agree: 75% and 79% of changes carry every
  body, and the runtime-checkable sufficiency test agrees with the oracle 81% and 79% of
  the time. Nothing here is flask-shaped.

## Where the disagreement was

Three proposals were measured and rejected rather than adopted: shortest-first excerpt
ordering (6 of 17 fell to 4), raising the excerpt line limit (no change), and ranking
obligations by coverage (10 fell to 9). A fourth — excluding "obviously irrelevant" symbols —
was measured before implementing: dunders are changed at 6.7% against 8.2% for everything
else, so there was almost nothing safe to exclude.

## Next, in the order that survives being wrong

1. Minimise the context of the three runs that succeeded, by deletion, until they stop
   succeeding. That gives the working set a task actually needed rather than the one it was
   given, and it is the only way to tell which of the 17,262 tokens did anything.
2. Whether a wrong envelope hurts because of what it says or because of what it omits: a
   control that is empty at the same length would separate those.
