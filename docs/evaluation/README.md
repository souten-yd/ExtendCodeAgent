# Evaluation manifests and runner

The canonical command is `tools/local/evaluation-runner`. It validates the sealed Layer A labels,
the sealed E3 Layer B suite, the pinned quality corpus, exact model routes, and the integrated metric
contract before planning or running any cell.

```bash
# Inspect the fixed schedule without making model calls.
tools/local/evaluation-runner plan --scope full

# Run or resume the complete fixed schedule. Raw logs/workspaces remain ignored.
tools/local/evaluation-runner run --scope full --resume \
  --output docs/evidence/final/model-matrix.json

# Run the wide/shallow pass owned by B0 before confirmation.
tools/local/evaluation-runner run --scope screening --resume \
  --output docs/evidence/final/screening-matrix.json
```

`--arm`, `--model-tier`, `--task`, and `--max-cells` produce bounded diagnostic slices. Such slices
must be labeled as runner/route proof and cannot support promotion, demotion, or model-quality claims.
The runner checkpoints atomically after every cell; `--resume` reuses completed cell IDs. A partial
workspace without a checkpoint is moved into the ignored archive before a fresh attempt, never
silently scored or destructively deleted.

The historical `benchmark_pr_b/c/h/i` and `pr_g_evaluate` scripts remain only to reproduce their
original PR evidence. They are retired as current evaluation entry points: new matrix, model, task,
metric, and Layer C work belongs in the unified runner and its versioned manifests.

Runner-only changes do not authorize either an unconditional resume or automatic deletion of prior
results. Audit an immutable checkpoint against a sealed compatibility manifest first:

```bash
tools/local/evaluation-runner audit-checkpoint \
  --source .evaluation/unified-v1/old-result.json \
  --compatibility docs/evaluation/b0a-checkpoint-compatibility-v1.json \
  --output .evaluation/unified-v1/old-result-audit.json
```

`REUSABLE` means functional outcome only; its timing remains `LEGACY_RUNNER_LATENCY`. Provider gaps,
timeouts, incomplete cells, seal mismatches and provenance failures never migrate. The audit report
is hash-bound to the source checkpoint, trace log, every source result and compatibility manifest,
and is itself sealed. Audit alone does not permit migration: a separately sealed 10–20-cell
multi-provider Bridge Proof must match the affected model/task classes first.

Generate and execute the sealed Bridge Sample after the clean merged audit:

```bash
tools/local/evaluation-runner bridge-plan --audit <audit.json> \
  --compatibility docs/evaluation/b0a-checkpoint-compatibility-v1.json \
  --output <bridge-plan.json>
tools/local/evaluation-runner run-bridge --bridge-plan <bridge-plan.json> \
  --raw-root <bridge-raw> --output <bridge-run.json>
tools/local/evaluation-runner prove-bridge --bridge-plan <bridge-plan.json> \
  --bridge-run <bridge-run.json> --source <old-result.json> --output <bridge-proof.json>
```

`run-bridge` accepts repeated `--model-tier` selections and `--resume`, so providers can be run as
separate shards. A Bridge mismatch is not averaged away: the related model/task class becomes replay
required. Bridge wall time is always excluded from functional equivalence and legacy timing remains
non-mergeable.

Provider failures pause only the affected model-tier queue. The triggering attempt is recorded under
`provider_attempts`, excluded from quality results, and leaves the evaluation cell pending. Recovery
requires a separate probe and sealed proof before resume:

```bash
tools/local/evaluation-runner probe-provider --model-tier host-default \
  --output <availability-proof.json>
tools/local/evaluation-runner run-bridge --resume --availability-proof <availability-proof.json> ...
```

The same `--availability-proof` option applies to normal `run`. A probe is never an evaluation retry
and is never included in correctness or latency aggregates.
