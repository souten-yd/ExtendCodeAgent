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
