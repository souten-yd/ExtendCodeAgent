# Known Issues

## PR-A environment

- The local machine has Python 3.12.3 but no Python 3.11 executable, so the declared 3.11 lower
  bound was checked through syntax/tool configuration rather than a second interpreter run.
- The `opencode` command is not installed locally. PR-A therefore makes no real OpenCode claim;
  real plugin/MCP evaluation remains a PR-D acceptance gate.
- PR-A has fake model evidence only. Live local/host/frontier routing remains a PR-G gate.
- `timeout_seconds` is validated configuration but the synchronous fake adapter does not simulate
  wall-clock timeout enforcement; live adapters must implement that contract in PR-G.

## PR-B measured limitation

- On the 50-source-file ExtendCodeAgent repository, file-level refresh took 182.145 ms versus
  185.638 ms cold build. The fact update is incremental, but workspace fingerprint scanning
  dominates. Before claiming scale benefit, benchmark a Git-status fast path and automatic
  full-rebuild selection for small repositories.
- Snapshot import validates integrity and restores current facts, but deliberately creates a new
  local revision instead of importing foreign revision identity. Cross-store lineage preservation
  remains future work.

## PR-C current limitations

- Dependency-aware semantic refresh repairs unchanged importers of a removed/renamed symbol, but it
  currently parses every Python AST to build the symbol index before emitting only affected facts.
  The 64-file sample improved from 637.215 ms cold to 280.653 ms incremental; larger-repository
  scaling and a persisted symbol index remain future measurements.
- Dynamic receiver calls are deliberately emitted as inferred `may_call` edges at confidence 0.35.
  This avoids false certainty but can produce name-collision false positives through alias bridging;
  the PR-C FP/FN report must quantify representative cases.
