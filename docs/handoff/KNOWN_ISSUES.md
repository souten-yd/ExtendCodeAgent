# Known Issues

## E3 evaluation limitations

- The ControlDeck-managed OpenCode selected for E3 is 1.18.16, while earlier npm-stable evidence used
  1.18.18. E4/B0 must report the executable and version actually used rather than treating these as
  interchangeable.
- No permitted non-Ollama weak-local endpoint is registered. `OpenCode + OMO + ECA @ local-low` is
  therefore UNAVAILABLE; model-free coexistence PASS is not model-task evidence.
- OMO 4.19.4 and ECA expose unique ECA `pi_*` names, but generic raw IDs such as `glob`, `grep`,
  `skill`, and `task` overlap. B2 must assess semantic dispatch/conflict behavior.
- OMO's installer wrote `~/.omo/omo.jsonc` despite an isolated XDG configuration. The newly created
  file was moved into the temporary evidence root and the previously absent directory was restored;
  future automation must not assume XDG isolation is complete.
- GitHub candidate popularity and activity observations drift. OpenCode, Hermes Agent, Atomic Agents,
  and Codex require a fresh immutable pin and clean dependency/test audit before any corpus promotion.
- A supplemental repository-wide Ruff scan reports one pre-existing E501 long line in
  `tools/local/benchmark_pr_b.py`. Normal all-fast/integration/build gates pass; E4 already owns
  retiring that per-PR benchmark into the unified runner.

## E4 evaluation limitations

- E4 route proof uses one repetition per representative cell. It proves wiring and objective scoring,
  not comparative quality; B0 owns minimum-repetition distributions and screening/confirmation.
- The sealed full schedule is 5,083 cells, of which 1,495 are visible local-low UNAVAILABLE cells.
  Running all cells without screening would violate the execution-capacity design.
- Integrated metric keys whose implementing verification stage does not yet exist are emitted as
  `NOT_TESTED`. They must not be numerically aggregated or interpreted as zero.
- Historical `benchmark_pr_b/c/h/i` and `pr_g_evaluate` remain executable only to reproduce their
  original evidence. They contain obsolete route assumptions and are not current entry points.

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
  The 64-file sample improved from 623.969 ms cold to 282.761 ms incremental; larger-repository
  scaling and a persisted symbol index remain future measurements.
- Dynamic receiver calls are deliberately emitted as inferred `may_call` edges at confidence 0.35.
  This avoids false certainty but can produce name-collision false positives through alias bridging;
  the PR-C FP/FN report must quantify representative cases.

## PR-D current limitations

- Stable OpenCode 1.18.18 emits `.git/index.lock` watcher events while the Twin computes its Git
  fingerprint. Unfiltered handling caused a self-sustaining refresh loop. The plugin now discards
  `.git`, `.extendcodeagent`, dependency, cache, and build paths before enqueue; the final real-host
  smoke must retain explicit no-loop evidence.
- Stable OpenCode's native event stream did not expose ordinary tracked edits in the tested Linux
  environment. The adapter-only Chokidar fallback passed both OpenCode-tool and external-edit
  evidence, but future stable OpenCode releases should be retested so the extra watcher can be
  removed when the native contract is reliable.
- The three-run temporary-repository startup comparison had a +24 ms median delta and one 1,609 ms
  native outlier. It is not statistically conclusive; retain broader native/extension comparisons
  for final release validation.

## PR-E current limitations

- Stable OpenCode 1.18.18 does not route the model-free session-shell endpoint through
  `tool.execute.after`. Real runtime-hook evidence therefore requires an actual agent tool call.
- The real local Qwen agent `bash` hook omitted explicit exit metadata, so its successful command is
  truthfully stored as `observed`, not `passed`.
- The first real-repository test-selection sample found no graph-linked candidate for
  `reconcile_observations` and correctly selected full-suite fallback. A bounded diagnosis confirmed
  a Python `src.`/package re-export alias gap; the language-owned resolver now uses exact import
  evidence and a collision fixture. This repairs the measured sample without claiming general
  dynamic-import or alias completeness.
- OpenCode smoke processes share the host OpenCode database and must run serially; a concurrent
  evidence attempt produced `database is locked`. Serial model-free and model-backed reruns passed.

## PR-G current limitations

- The configured `llama/llama-3.3-70b-instruct` frontier path returned OpenCode `APIError` for all
  18 mode/scenario attempts. Provider failures now fail closed, but no real frontier quality result
  exists; the final release gate remains unmet until a usable frontier credential/path is available.
- Qwen3 0.6B varied across repeated six-case runs. Bounded Project Intelligence consistently beat
  off, but advisory versus active was not stable enough to justify an active default. The central
  default remains off and active must stay explicit until multi-repository distributions exist.
- OpenCode's host token report separates cache reads from new input. Evidence records both; adding
  them as if billed identically would be misleading. Host big-pickle was free in the measured setup
  (`cost: 0`) but that does not generalize to other providers.
- Stable session prompt does not expose a per-request output-token bound. The OpenAI-compatible path
  is bounded; the host path relies on focused prompts and a transport timeout. Final validation
  should reassess this against the then-current stable OpenCode API.

## PR-H measurement incident

- py-tree-sitter 0.26.0 segfaulted even after cross-file `Node` state was replaced with serializable
  descriptors; the same isolated ControlDeck TSX analysis passed repeatedly on 0.25.2. The analyzer
  pins 0.25.2, reuses one `Parser` per grammar, streams traversal, and retains only descriptors
  across files. This remains open until three repetitions of the real-repository cold/incremental
  path and full local gates pass; a recurrence requires replacing the Python binding path.

## PR-I current limitations

- PR-I defines and exercises provider-neutral Search/Fetch/Extract/Synthesis ports and exposes the
  shared bounded plan through MCP, but does not claim a new standalone web provider. OpenCode/web or
  MCP retrieval adapters supply those ports; live cross-provider research quality belongs in final
  Release Validation.
- External evidence is deliberately never promoted to verified project fact. A claim needing both
  external truth and implementation verification must carry separate external and current project
  evidence; this may leave more explicit coverage gaps but prevents false completion.

## E5 trace limitations

- The required local-low route is not registered under the permitted environment, so the all-arm
  E5 demonstration has 115 `UNAVAILABLE` outcomes. Its capability states are scheduled matrix values,
  not observed runtime values, and it provides no quality comparison.
- The real advisory trace observed capability state through `pi_status`, but its `pi_symbol` output
  exposed neither a selected evidence ID nor a Twin revision ID. Those trace fields correctly remain
  empty/null.
- E5 is a serial evaluation log without cross-process locking and is not durable cross-session
  Project Evidence Memory. The sealed runner is serial; broader durability/replay belongs to P0.

## B0a bootstrap performance observation

- The first pinned KasaneCore initial Twin spent multiple minutes applying edges in
  `SqliteGraphStore._close_current`. The schema indexes current nodes by canonical reference but has
  no equivalent current-edge ID index, so the per-edge supersession update is a suspected scaling
  defect. This is observed diagnosis, not yet a confirmed repair; B0a records bounded timeout/build
  evidence and B1 owns a product fix if the completed gap report confirms it is blocking.
