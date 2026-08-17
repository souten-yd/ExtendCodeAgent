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
  --compatibility docs/evaluation/b0a-checkpoint-compatibility-v3.json \
  --output .evaluation/unified-v1/old-result-audit.json
```

`REUSABLE` means functional outcome only; its timing remains `LEGACY_RUNNER_LATENCY`. Provider gaps,
timeouts, incomplete cells, seal mismatches and provenance failures never migrate. The audit report
is hash-bound to the source checkpoint, trace log, every source result and compatibility manifest,
and is itself sealed. Audit alone does not permit migration: a separately sealed Bridge Proof must
match the model/task classes selected by the active compatibility manifest first. The historical v1
contract used a 10–20-cell multi-provider sample; local-only v2 requires exactly three
`local-practical` cells covering symbol navigation, impact analysis and test selection.

Generate and execute the sealed Bridge Sample after the clean merged audit:

```bash
tools/local/evaluation-runner bridge-plan --audit <audit.json> \
  --compatibility docs/evaluation/b0a-checkpoint-compatibility-v3.json \
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

After a Bridge Proof, copy only permitted classes into a new checkpoint and a new trace chain:

```bash
tools/local/evaluation-runner migrate-checkpoint --source <old-result.json> \
  --audit <audit.json> --bridge <bridge-proof.json> \
  --raw-root <new-raw-root> --output <new-result.json>
```

Migration never edits the source. Every copied result records its original result hash, old runner,
validating runner, manifest/proof and `LEGACY_RUNNER` latency status. A Bridge mismatch excludes that
class, a Bridge-unavailable provider excludes that model tier, and sealed unavailable model cells
remain reusable without pretending they executed. The migrated checkpoint is sealed and binds fresh
activation/pilot evidence on its first current-head resume.

A current-head activation may be `PARTIAL_PROVIDER_GAP` only when every missing model exactly matches
a paused provider queue and every observed model passed PI route activation with no capability gap.
This permits unaffected providers to continue; it does not complete the activation gate or baseline.

An unchanged 27-cell pilot can be promoted only after its own checkpoint audit reports every cell
`REUSABLE` with valid trace integrity:

```bash
tools/local/evaluation-runner promote-pilot --source <old-pilot.json> \
  --audit <pilot-audit.json> --output <current-pilot-evidence.json>
```

Promoted pilot latency remains legacy and separate. Any non-reusable pilot cell rejects promotion.

B0a local-only screening additionally requires the complete, sealed, exact-head 54-cell
port-8090 `local-practical` baseline. The runner verifies the quality-target seal, result set,
target completion summary and append-only trace before creating a screening workspace. Sonnet,
Codex and `host-default` remain `NOT_RUN_USER_POLICY`; `local-low` remains `UNAVAILABLE` for this progression
gate and cannot be presented as passed:

```bash
tools/local/evaluation-runner run --scope b0a-screening \
  --activation-report <activation.json> --pilot-report <pilot.json> \
  --baseline-report <complete-baseline.json> \
  --raw-root <screening-raw> --output <screening-result.json>
```

Migrated and current-runner cells may coexist in a resumed baseline, but their counts and latency
populations remain separate. Legacy timing is excluded unless an explicit latency bridge permits
aggregation.

The sealed 714-cell B0a matrix is now the hard maximum for adaptive screening, not a mandatory call
schedule. Generate the exact-head model-free plan first; it records active-use relevance,
`NOT_TESTED_NO_ACTIVE_USE`, deterministic depth equivalence, p95/p99-derived limits, compatible
checkpoint reuse, workspace-strategy measurements and expected/max calls before inference:

```bash
tools/local/adaptive-screening-runner analyze \
  --source-checkpoint <preserved-714-checkpoint.json> \
  --source-raw-root <preserved-714-raw> --analysis-root <analysis-root> \
  --success-report <compatible-success-report.json> --output <adaptive-plan.json>

tools/local/adaptive-screening-runner run --plan <adaptive-plan.json> \
  --source-checkpoint <preserved-714-checkpoint.json> \
  --raw-root <adaptive-raw> --output <adaptive-result.json> --resume
```

The run keeps model inference serial and pipelines workspace preparation plus oracle/parsing/sealing
on CPU workers. It evaluates repetitions sequentially and closes a capability at a positive B0b
signal or a proven non-boundary. Model output is never reused as Project Truth; compatible results
and completed agent captures retain provenance/fingerprints and avoid identical model work only when
the evaluation contract does not require an independent repetition. Every cell is executed, reused,
invalidated, pending, or skipped with a machine-readable reason. All arms deny external-directory
access so a cell cannot mutate the runner's shared virtual environment.

`bridge` compares one preserved per-cell control with one fresh isolated `serve` + `run --attach`
observation. A single pair can reject semantic drift but cannot adopt persistence; adoption requires
repeated oracle-equivalent meaningful speedup without session/workspace/evidence sharing.
