# Next Task

Start PR-I Research/Evidence/Traceability/project convergence without adding Release Validation.

1. Merge this PR-H closeout, fast-forward main, and create `agent/pr-i-research-traceability`.
2. Read only the PR-I plan/audit slices and inspect current Provenance, EvidenceRef, Runtime,
   Blueprint, Convergence, sidecar/MCP, SQLite, CapabilityPolicy callers and tests.
3. Inspect only the matching KasaneCore Nexus domain contracts/tests. Classify each behavior as
   REUSE, ADAPT, CONSOLIDATE, REPLACE, NEW, or DO NOT PORT before production code.
4. Move behavioral tests first for `ResearchRequest`, `ResearchPlan`, `SourceCandidate`, `Evidence`,
   `Claim`, `CoverageGap`, `RetrievalDeficit`, ports, and project-level requirement traceability.
5. Reuse OpenCode web/MCP retrieval through ports; external evidence must never become verified
   project fact. Keep provider/application infrastructure and raw large logs out.
6. Add project-level convergence through existing target/actual/evidence projections, then run
   focused gates, all-fast/build, relevant integration and benchmark evidence.

Resume:

```bash
cd /home/souten/ExtendCodeAgent
git switch main
git pull --ff-only origin main
git status --short
git switch -c agent/pr-i-research-traceability
```

Keep final multi-repository/model Release Validation in a separate PR after PR-I merge/closeout.
