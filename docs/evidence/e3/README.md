# E3 evidence

This directory contains compact, versioned evidence for the sealed Layer B task suite. Raw model
event logs, cloned task workspaces, credentials, OpenCode databases, and temporary package caches stay
under ignored local evaluation or temporary roots and are not committed.

- `omo-eca-coexistence-smoke-v1.json` records the model-free coexistence smoke. It does not promote
  the unavailable `local-low` model arm to PASS.
- `slow-suite-selection-v1.json` records rejected candidates and the clean 756-second PEDS suite
  selected at an immutable revision.
- `native-oracle-proof-v1.json` records the exact sealed-manifest native run: 4 PASS, 9 FAIL, no
  timeout or unavailability, for a 30.77% native success rate.
- The native one-run oracle proof is summarized here only after the corrected manifest is sealed and
  all tasks have been executed against that exact seal.
- Slow-suite evidence records both the immutable repository revision and a fresh wall-clock result;
  historical evidence is never silently substituted for a failed current run.
