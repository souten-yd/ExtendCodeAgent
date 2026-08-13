# PR-I Research, Evidence, and Traceability Evidence

Date: 2026-08-14

The PR-I core uses provider-neutral ports. The MCP/OpenCode tool returns the same bounded
`ResearchPlan`; actual Search/Fetch implementations remain adapters and no OpenCode result shape is
imported by Core.

Safety cases verified in focused tests:

- external evidence can support an external claim but never sets `verified_project_fact`;
- external-only requirement evidence projects to `observed`, so Convergence returns `continue`;
- only explicit requirement ID, matching actual ref, current source revision, and verified project
  evidence can reach `verified` and `complete`;
- missing, conflicting, stale, and unmapped evidence remain gaps/incomplete;
- evidence is immutable, idempotent, restart-durable, and workspace-isolated in shared SQLite;
- fake Search/Fetch/Extract/Repository/Synthesis ports exercise the same bounded orchestration;
- MCP `pi_research_plan` calls the shared sidecar/application and returns the micro budget.

The real ExtendCodeAgent repository benchmark created 200 explicit requirements and 200 current
verification records. Twenty full project-convergence projections averaged 0.5424 ms (p50 0.5290
ms). One thousand deterministic research plans averaged 0.0020 ms. Persisting 200 external evidence
records took 196.650 ms and restart lookup passed. DB+WAL was 17,771,744 bytes and max RSS 59,644
KiB; the database also contains the benchmark repository Twin, so this is not evidence-only size.

No external network retrieval or LLM is claimed by this benchmark. PR-I validates the domain,
durability, and adapter boundary; final Release Validation separately evaluates current real host,
model, repository, and mode combinations.
