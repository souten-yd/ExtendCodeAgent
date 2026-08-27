# What the envelope carries, and what is still unmeasured

Updated 2026-08-27. Written to separate what this session established from what it did not,
because most of it is deterministic and reusable while the part everyone wants — does the
envelope help an agent — is still open.

## Established, without a model

Every number here comes from a deterministic tool in `tools/local/` and can be re-run.

| | before | after |
|---|---|---|
| changed functions carried as source (flask, 16 applicable) | 6 of 17 | **12 of 16** |
| bodies cut for want of excerpt allowance | 13 | **0** |
| a change envelope's composition | — | 91.4% source, 1.1% names, 7.5% frame |
| tokens the needed bodies actually require | — | **1,932 at most**, 1,218 median, against 8,192 |
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

## Not established

**Whether an agent given the envelope does better than one without it.** Every comparison
this session either measured a superseded implementation, or had one arm inert, or ran on a
task shape that hands over the location — the part the envelope is for.

The one clean data point is a single local-model case where the envelope converted a failure
into a pass (8 turns against 14 and no pass). One case.

## Bounds that are not defects

- **23.7% of production changes are detected by no test.** No selection fixes that.
- **29% of changed functions are not executed by the failing tests**, so coverage cannot rank
  them. `Flask.run` is the shape of it.
- **5 of 15 descriptions locate nothing.** Two name only what the change introduces —
  `TRUSTED_HOSTS` does not exist yet — which is Blueprint's domain, not the Twin's. The other
  three name attributes and class variables, which the graph does not index.
- **One repository.** Everything above is flask. httpx is rebuilt and unmeasured.

## Where the disagreement was

Three proposals were measured and rejected rather than adopted: shortest-first excerpt
ordering (6 of 17 fell to 4), raising the excerpt line limit (no change), and ranking
obligations by coverage (10 fell to 9). A fourth — excluding "obviously irrelevant" symbols —
was measured before implementing: dunders are changed at 6.7% against 8.2% for everything
else, so there was almost nothing safe to exclude.

## Next, in the order that survives being wrong

1. Measure whether any of this holds on httpx. Everything rests on one repository.
2. Only then, spend a model run — and freeze the implementation while it is in flight.
