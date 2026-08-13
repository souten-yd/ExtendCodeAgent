# Next Task

Start PR-E Context + Test Intelligence + Runtime Ingest only after the PR-D closeout is merged.

1. Fast-forward `main`, pass `tools/local/all-fast` and `tools/local/build`, then create
   `agent/pr-e-context-test-runtime` from the exact updated head.
2. Read only the PR-E section of `IMPLEMENTATION_EXECUTION_LOCAL_VALIDATION_PLAN.md`, the runtime/
   test redesign and Test Obsolescence sections of `KASANECORE_MIGRATION_AUDIT.md`, and directly
   relevant KasaneCore runtime/context sources and tests.
3. Classify each slice before implementation. Expected direction: ADAPT runtime reconciliation and
   context evidence behavior; CONSOLIDATE revision/provenance with existing contracts; NEW a
   dedicated Test Obsolescence engine; DO NOT PORT Atlas runners/context DTOs.
4. Add behavior-first tests for a host-neutral immutable `RuntimeObservation` contract covering
   test, lint, build, typecheck, smoke, benchmark, and runtime results; include source revision,
   observed refs, timing, status, command/tool, and evidence artifacts.
5. Add revision-freshness tests proving historical green evidence is stale for a newer relevant
   source revision and unavailable evidence cannot become passed.
6. Extend existing graph-based test candidates into deterministic selection with explicit
   confidence and a configurable full-suite fallback when confidence/recall evidence is weak.
7. Implement the first evidence-based Test Obsolescence states: healthy, suspect, stale, obsolete,
   missing, and redundant. Use revision/impact/runtime/assertion/removed-symbol/disabled/duplicate
   signals; never auto-delete a test.
8. Build bounded revision-aware context packages whose items include why included, confidence,
   revision, provenance, and token estimate. Weak profiles must be materially smaller.
9. Add an adapter-only OpenCode tool-result normalization path and `pi.context`/test evidence query
   only after host-neutral behavior is proven. Do not introduce model routing in PR-E.
10. Run focused tests, all-fast, build, integration, real test-project scenarios, stale-evidence
    cases, context/test-selection benchmarks, and a bounded local A/B. Record unavailable model
    evidence honestly; do not claim real LLM evaluation unless a real model is exercised.
11. Publish/merge PR-E and a separate closeout PR before PR-F.

Resume:

```bash
cd /home/souten/ExtendCodeAgent
git switch main
git pull --ff-only origin main
git status --short
tools/local/all-fast
tools/local/build
git switch -c agent/pr-e-context-test-runtime
```

Keep Blueprint/Convergence (PR-F), live model routing/Strategy (PR-G), JS/TS semantic/deep graph
(PR-H), and Research/Traceability (PR-I) outside PR-E.
