# Claude Handoff — Context-Aware Dynamic Concurrency

Status: implementation handoff. This does not change the canonical stage order in `docs/PI_MASTER_EXECUTION_PLAN.md` and must not turn ECA into a generic scheduler.

## Goal

Allow an external orchestrator to vary active concurrency automatically according to the actual semantic working set and expected context/resource demand of each task, while respecting a backend-configured maximum parallelism (for example a Llama-compatible server maximum).

The desired behavior is:

```text
backend/configured max_parallel = hard upper bound
                 +
per-task PI context/resource forecast
                 +
currently active workstreams
                 ↓
        safe_parallel_ceiling
                 ↓
external orchestrator admission control
```

A large project must not automatically imply low concurrency. Repository size is only a weak prior. Prefer the task's semantic working set: selected capabilities/depth, Evidence Envelope size, Impact closure, verification obligations, runtime-boundary needs, unresolved Evidence Gaps and expected expansion.

## Ownership

ECA owns **resource/intelligence hints**, not scheduling:

- ECA: derive bounded task/context/resource forecasts and reasons from C1/C2/C3 information.
- Runtime adapter: expose the host-neutral hint when the runtime can consume it.
- External orchestrator / host integration: decide admission, queueing and active parallel count.
- Llama/model backend: owns its configured maximum parallelism, slot/KV implementation and physical inference scheduling.

Do not implement a second generic scheduler, worker pool, team manager or backend slot engine in ECA. If the target runtime cannot dynamically admit/hold work based on the hint, expose/measure the hint and classify automatic consumption as unavailable rather than duplicating the runtime.

## Core invariant

**Context determines concurrency; concurrency never forces correctness-critical context pruning.**

1. First derive Minimum Sufficient Context/Evidence for each task.
2. Add explicit output headroom and expected targeted-expansion headroom.
3. Estimate context/resource demand and uncertainty.
4. Reduce/admit parallel work only after those quality requirements are preserved.
5. If safe capacity is insufficient, queue work or lower concurrency. Do not silently drop required evidence to keep more tasks active.

## Proposed host-neutral contracts

Use the existing `IntelligencePlan.context_budget_tokens` and C2 evidence telemetry as inputs. Prefer adding the smallest projection rather than a parallel planning system.

Conceptual shape:

```text
TaskResourceForecast
  project/workspace/revision/task identity
  initial_evidence_tokens
  estimated_prompt_context_tokens
  reserved_output_tokens
  expected_total_context_tokens
  p95_or_conservative_context_tokens
  expansion_ceiling_tokens
  semantic_working_set_size
  impact_closure_size
  verification_obligation_count
  uncertainty
  forecast_confidence
  memory_estimate_when_observable
  reason_codes

ConcurrencyHint
  configured_max_parallel
  active_workstreams
  safe_parallel_ceiling
  recommended_parallel
  headroom_ratio
  pressure_class
  forecast_confidence
  reason_codes
```

Field names are not frozen by this handoff. Reuse existing ProjectRef/runtime/task identity and telemetry instead of duplicating them.

## Capacity inputs

The orchestrator/runtime integration may provide a small `BackendCapacity` projection when observable:

```text
configured_max_parallel
model_context_limit
aggregate_context_or_kv_capacity_when_known
available_vram_or_memory_budget_when known
reserved_memory/headroom
active slot/workstream usage
```

Do not require provider-specific internals in ECA core. If exact KV bytes/token are unavailable, use measured context occupancy and conservative headroom rather than pretending precision.

## Scheduling policy

Use capacity/admission control, not fixed thresholds alone.

For homogeneous tasks the conceptual bound is:

```text
safe_parallel <= configured_max_parallel
safe_parallel <= floor(usable_context_or_memory_capacity / conservative_per_task_demand)
```

For heterogeneous tasks, prefer a cheap admission/bin-packing heuristic over the currently active + queued forecasts. Do not solve an expensive global optimizer in the runtime path.

Project/repository scale may increase forecast uncertainty or expansion headroom, but must not directly force concurrency down when the current semantic working set is small.

## Dynamic behavior and hysteresis

Avoid concurrency oscillation.

- Increase concurrency only after sustained low pressure / adequate headroom.
- Decrease future admissions promptly when actual context exceeds forecast or expansion risk rises.
- Prefer stopping new admissions over cancelling healthy active coding tasks.
- Emergency reduction/cancellation is reserved for explicit OOM/resource-safety behavior owned by the host/backend.
- Record forecast error (`actual / predicted`) and use it to calibrate later hints deterministically.

Suggested reason states include:

```text
FULL_PARALLEL_SAFE
CONTEXT_PRESSURE
EXPANSION_RISK
LOW_FORECAST_CONFIDENCE
MEMORY_PRESSURE
RUNTIME_CAPACITY_UNKNOWN
BACKEND_MAX_REACHED
QUALITY_HEADROOM_REQUIRED
```

## Quality and safety

A higher throughput result is not a win if any workstream loses correctness. The accepted single-workstream bounded-context profile remains the per-task quality baseline.

Hard failures:

- required evidence pruned only to preserve concurrency;
- Project/Workspace/Revision cross-contamination;
- PI-induced OOM or primary-model eviction/reload;
- context overflow/truncation causing correctness loss;
- concurrency recommendation above the backend-configured maximum;
- low-confidence forecast treated as precise without conservative headroom.

## Evaluation

Measure the hint itself before automatic scheduling.

### Shadow forecast phase

For real tasks, record predicted vs actual:

- total primary-model context;
- Evidence Envelope size;
- targeted expansion count/size;
- peak RAM/VRAM when observable;
- whether the task fit <=64k total context;
- forecast error and confidence calibration.

Acceptance should be conservative: under-prediction that causes context/resource failure is more serious than over-prediction that only reduces concurrency.

### Advisory concurrency phase

Given a recorded backend `configured_max_parallel`, replay/compute the recommended concurrency and compare it with actual safe capacity. No runtime behavior change yet.

### Automatic consumption phase

Only after forecast/advisory evidence is acceptable and the host exposes the needed admission-control surface:

- compare fixed max concurrency vs context-aware concurrency;
- use >=4 independent workstreams where capacity permits;
- include mixed small/medium/large-context tasks;
- measure per-task quality, aggregate throughput, p50/p95 completion time, peak memory/VRAM, OOM, model reloads, queueing and workspace/revision isolation;
- prove that large tasks automatically reduce active parallel count and that small tasks can return to the configured maximum after pressure falls.

Do not hide host/backend serialization as ECA failure. Distinguish logical workstream concurrency from physical simultaneous inference.

## Relation to existing stages

- C2: produce accurate bounded evidence/context telemetry and enough data for a resource forecast. Do not add generic scheduling.
- C3: natural point for shadow/advisory `TaskResourceForecast` / `ConcurrencyHint` because task-aware automatic capability/depth/context selection becomes production-like here.
- P3 or another host integration with real multi-worktree/task identities: consume the hint for automatic admission/concurrency control if the runtime supports it.
- R0/large-project evidence: record <=64k quality-preserving behavior; four-workstream claims require appropriate runtime/backend evidence.

If implementation evidence shows a smaller safe integration point earlier than P3 without duplicating host orchestration, use the existing Master Plan evidence/change process before moving it.

## Claude implementation instruction

Implement this feature only in the appropriate ownership layers:

1. Reuse C1/C2/C3 context/evidence data to create the smallest host-neutral deterministic task resource forecast.
2. Add a derived concurrency hint capped by the backend/runtime configured `max_parallel`; do not create scheduler state in Project Truth.
3. Keep the hint shadow first and evaluate predicted-vs-actual context/resource demand.
4. Add advisory consumption only after forecast accuracy is acceptable.
5. Add automatic concurrency only in an existing orchestrator/admission-control surface; if OpenCode/OMO/the selected host does not expose one, stop at advisory and document the gap instead of implementing a second scheduler inside ECA.
6. Concurrency must never force required-context pruning. Reduce/queue parallel work instead.
7. Use hysteresis/backpressure to avoid oscillation and calibrate forecasts from observed errors.
8. Respect the hard backend maximum and distinguish logical workstream concurrency from physical inference concurrency.
9. Validate mixed-size tasks, >=4 workstreams where capacity permits, <=64k target tasks, no workspace/revision leakage, no PI-induced OOM/model reload, and non-inferior per-task quality.
10. Reuse/consolidate existing contracts; no speculative parallel framework. PR and merge only after the relevant deterministic/local tests and evidence gates pass.
