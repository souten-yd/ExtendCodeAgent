# Next Task

Start PR-G live Model Routing + Strategy only after the PR-F closeout is merged.

1. Fast-forward `main`, pass `tools/local/all-fast` and `tools/local/build`, then create
   `agent/pr-g-routing-strategy` from the exact updated head.
2. Read only PR-G/model-routing/Strategy sections of the execution plan and migration audit; inspect
   existing PR-A ModelRouter/contracts/fakes and current stable OpenCode host model interfaces.
3. Extend the existing router. Do not create a parallel router. Add OpenAI-compatible local and
   OpenCode host adapters behind the provider-neutral port; preserve local-only and remote-code deny.
4. Add deterministic adaptive signals: impact/file/language counts, uncertainty, strategy scope,
   evidence conflict, context requirement, and security sensitivity. Record explainable selection,
   escalation, fallback, token/time, and model tier.
5. Build Strategy Core anew: deterministic metrics and provenance; LLM only proposes alternatives
   and explains tradeoffs. Never invent A/B/C fallback choices or treat LLM output as verified fact.
6. Keep weak-local payloads bounded: graph facts, candidate filtering, one focused structured
   question. Do not send whole repositories.
7. Prove fake routing, privacy, failures, and structured-output behavior first; then run real
   local-low, local-medium, host/default, and frontier evaluations where available.
8. Compare the same tasks across native/off/advisory/active and record success, calls, tokens, wall
   time, unnecessary reads/edits, selected tests, escalations, and correction. Do not make active the
   default if weak local performance regresses.
9. Publish/merge PR-G and a separate closeout before PR-H.

Resume:

```bash
cd /home/souten/ExtendCodeAgent
git switch main
git pull --ff-only origin main
git status --short
tools/local/all-fast
tools/local/build
git switch -c agent/pr-g-routing-strategy
```

Keep JS/TS/deep graph (PR-H) and Research/Traceability/project convergence (PR-I) outside PR-G.
