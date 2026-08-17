# B0 Baseline Gap Report

- Captured: 2026-08-17
- Execution scope: `local-only`
- Model: Qwen3.6 27B (`127.0.0.1:8090`, context 262144, output limit 8192)
Claim scope: `active-scoped(local-practical)`

## Outcome

B0b completed all 57/57 exact-main held-out cells at source revision
`f15064c389e776a875faf1009648696343cbf9e0`. All 48 forced-use cells were trace-compliant. There were
no provider, process, timeout or unavailable outcomes. The result was 21 PASS and 36 FAIL.

No held-out causal PI effect was confirmed. `forced_pi` versus `forced_off` had zero PASS delta on all
three tasks. Graph, Semantic and Twin each had nine compliant ON/ablation pairs with equal outcomes;
Test Selection had three equal PASS/PASS pairs. Blueprint, Impact, Strategy and Test Obsolescence are
`NO_HELD_OUT_TASK_COVERAGE`, not no effect. B0a observational and corrective positive signals remain
valid screening evidence, but they are not promoted over this confirmation result.

This result does not support a claim that PI currently improves Qwen completion correctness on the
covered held-out tasks. It also does not prove that PI is generally ineffective: four candidates lack
held-out coverage, only local-practical is permitted, and the measured failures expose fixable PI
projection and selection gaps.

Authoritative compact evidence is
`docs/evidence/final/b0b-confirmation-result-v1.json`. Its sealed raw inputs are retained under
`.evaluation/unified-v1/`; raw result SHA256 is
`edc821d2218281808257127a1a83c2347d70b51ae1aaaabdb800cb242d66cbc5` and trace SHA256 is
`665cf672e3a4ddbf38429271f6869827a65a8cf79b961a67ccacb813f0077c63`.

## Held-out effects

| Comparison | Pairs | PI/ON PASS | Control PASS | Delta | Decision |
|---|---:|---:|---:|---:|---|
| intrinsic: cross-boundary | 3 | 0 | 0 | 0 | `NO_CONFIRMED_CAUSAL_EFFECT`; `PI_CAPABILITY_GAP` |
| intrinsic: requirement tracing | 3 | 0 | 0 | 0 | `NO_CONFIRMED_CAUSAL_EFFECT`; `PI_CAPABILITY_GAP` |
| intrinsic: test selection | 3 | 3 | 3 | 0 | `NO_CONFIRMED_CAUSAL_EFFECT`; task solved without PI |
| Graph ON/ablation | 9 | 3 | 3 | 0 | `NO_CONFIRMED_CAUSAL_EFFECT` |
| Semantic ON/ablation | 9 | 3 | 3 | 0 | `NO_CONFIRMED_CAUSAL_EFFECT` |
| Twin ON/ablation | 9 | 3 | 3 | 0 | `NO_CONFIRMED_CAUSAL_EFFECT` |
| Test Selection ON/ablation | 3 | 3 | 3 | 0 | `NO_CONFIRMED_CAUSAL_EFFECT` |

The absolute two-PASS threshold and critical correctness override were unchanged. Neither was met.
No capability is promoted or demoted at B0b; the Layer C promotion gate remains pending.

## Failure classification

| Class | Count | Interpretation |
|---|---:|---|
| PASS | 21 | all test-selection variants returned the exact required provider set |
| `AGENT_REASONING_ERROR` | 16 | required task facts or exact answer were incomplete |
| `PROJECTION_SCHEMA_ERROR` | 20 | required facts were present but the final exact projection was wrong |
| provider/runtime/process | 0 | local-practical route and execution lifecycle were available |

Cross-boundary and requirement tracing failed 18/18 cells each. Cross-boundary errors expanded or
misordered the required browser-to-runtime causal chain. Requirement errors over-selected or omitted
implementation files. These are PI core/projection and agent-reasoning gaps, not provider failures.

## Selection quality

Auto selection remains independent of capability efficacy. Across nine measurable auto cells:

- mean capability-selection precision: 0.650794;
- mean recall: 0.530952;
- under-selection rate: 0.469048;
- over-selection rate: 0.293651;
- `EXPECTED_BUT_NOT_USED`: 22;
- six auto/forced comparisons were `PI_CAPABILITY_GAP`; three were `AUTO_SKIP_WAS_CORRECT`.

The low recall is a C1/C3 input. It is not a reason to relabel an unselected capability as ineffective.

## Verification-set result

The sealed test-selection oracle measured 21 cells, 84 true positives, zero false positives and zero
false negatives: micro precision and recall are both 1.0. This proves the required provider set was
selected accurately in those cells. It is not yet a PI effect because `auto_pi`, `forced_pi`,
`forced_off` and every eligible ablation all passed.

The verification-only product pivot is therefore not triggered: Project Truth did not show a covered
held-out gain, but Verification Intelligence also did not show an attributable gain over off.

## Context and cost

The 57 calls consumed 2,392,101 input tokens and 140,982 output tokens. Model wall time summed across
cells was 12,610,218 ms; deterministic `pi_*` tool intervals summed to 699,326 ms. OpenCode emitted 538
step-level requests. Full prompt context (`input + cache-read + cache-write`) was:

| Statistic | Tokens |
|---|---:|
| mean | 35,187.537 |
| p50 | 29,437 |
| p90 | 62,875 |
| p95 | 68,512 |
| p99 | 86,351 |
| maximum | 93,189 |

With the 8,192 output limit the maximum observed requirement is 101,381 tokens. A 128k context is a
practical lower-bound candidate for this workload; 96k has insufficient output/headroom and 64k misses
the tail. The configured 262,144 context remains unchanged until a bounded context Bridge proves
truncation and oracle equivalence on broader tasks.

PI tools returned 2,043,852 serialized characters over 240 calls. `pi_symbol` contributed 54.8584%,
`pi_context` 30.5821% and `pi_status` 11.7246%. Exact per-tool token attribution is unavailable in the
OpenCode trace, so character counts are recorded as a size metric rather than presented as tokens.
Reducing symbol/context projection is the first context-efficiency target.

The immutable raw report's context fields summed cell input and its deterministic PI time included
post-tool model reasoning. Corrected values above are derived from the sealed per-step logs; the raw
artifact is retained unchanged.

## Competition-derived concerns

| Concern | B0 disposition |
|---|---|
| weak-local behavior | local-practical measured; local-low `UNAVAILABLE / NOT_CONFIGURED`, so no local-low claim |
| lifecycle/worktree isolation | 57 exact-workspace sidecars terminated; no session/workspace sharing; completed worktree retention in the evaluation runner was found and repaired in closeout |
| subagent capability | `NOT_TESTED`; no qualifying multi-agent configuration in B0b |
| completion correctness | measured directly: 21 PASS, 16 reasoning failures, 20 projection failures |
| cross-session evidence loss | `NOT_TESTED`; it does not satisfy the P0 early-promotion condition |
| host-native overlap | forced-off control measured; host-default is `NOT_RUN_USER_POLICY`, with no host-default claim |
| required verification set | precision/recall 1.0, but no attributable PI delta |
| cross-boundary truth | 18/18 FAIL across all arms; establishes X0's repeated real-boundary failure signal |

## Ranked gaps

1. **PI cross-boundary and requirement projection.** Forced evidence did not produce exact causal-chain
   or implementation-file answers; repair the smallest missing relation/projection rather than widen
   repository context.
2. **Automatic capability selection.** Recall 0.530952 and 22 expected-but-unused states require C1
   ground-truth comparison and later C3 routing improvement.
3. **Exact output/schema reasoning.** Twenty cells had sufficient required facts but still produced an
   incorrect final projection; PI evidence presentation and bounded output construction need repair.
4. **Held-out coverage.** Blueprint, Impact, Strategy and Test Obsolescence remain unmeasured. Do not
   invent replacement tasks or infer no effect.
5. **Context/tool-output size.** `pi_symbol` and `pi_context` dominate injected data; use minimum
   sufficient symbol/neighborhood projections before broader context.
6. **Unmeasured runtime modes.** Cross-session and subagent evidence remain not tested; P0/P3 entry
   conditions are unchanged.

## Program-level stop and pivot criteria

- **Verification-only pivot: NOT TRIGGERED.** No covered Project Truth improvement was confirmed, but
  Verification Intelligence also did not improve over off; equal test-selection accuracy is not an
  attributable effect.
- **Weak-local-only pivot: NOT EVALUABLE under the local-only exception.** Local-low is unavailable and
  host-default/frontier calls are prohibited. No cross-tier claim is made.
- **Stop: NOT TRIGGERED.** Covered local-practical capabilities did not survive held-out ablation, but
  four candidates lack held-out coverage, Layer C M-scale budgets are not yet established, and fixable
  PI selection/projection defects are present. The three conjunctive stop conditions do not hold.

## Stage decisions

| Stage | Decision | Evidence-based reason |
|---|---|---|
| B1 | `SKIP_NO_ENTRY_CONDITION` | no product lifecycle/config/provider blocker remained; the evaluation-only worktree-retention defect is repaired and gated in this closeout |
| B2 | `KEEP_NEXT` | B0 is stable and prior smoke records OMO 4.19.4 installability; the required two-load-order compatibility baseline remains unmeasured |
| C0 | `KEEP` | task/session/workspace/tool/advisory observations are required inputs to selection and isolation |
| C1 | `KEEP` | precision 0.650794, recall 0.530952 and under/over-selection gaps give a direct acceptance baseline |
| C2 | `KEEP_CONDITIONAL` | context/output bloat is measured, but C1 and configured local-low evidence required by its entry/exit are not yet available |
| C3 | `KEEP` | auto versus forced divergence and context overhead require production-like advisory routing comparison |
| V0–V4 | `KEEP` | required-set accuracy is measured but not attributable; contracts, calibration, depth, reuse and failure re-evaluation remain required |
| V5 | `KEEP_CONDITIONAL` | cross-boundary misses are a signal; formal entry still requires V2/V4 unobservable or environment-dependent obligations |
| A0–A1 | `KEEP_AFTER_GATES` | no active-default promotion is supported by B0b |
| X0 | `KEEP_ENTRY_SATISFIED` | repeated 18/18 failures occurred at a real browser/API/runtime boundary |
| X1 | `DEFER_NO_ENTRY_CONDITION` | no measured data-origin/security task failure exists |
| R0 | `KEEP` | release remains bounded to a production-capable local-only baseline |
| P0 | `KEEP_AT_P0` | cross-session evidence loss was not shown release-blocking |
| P1–P4 | `KEEP_EXISTING_ENTRY_CONDITIONS` | no B0 result removes adapter, second-harness, worktree or same-Qwen OMO comparison obligations |
| Deferred set | `UNCHANGED` | no new measurement justifies implementation |

## Next

Close the runner metric/worktree defects with tests and immutable evidence, merge this B0b report, skip
conditional B1 explicitly, and start B2 under the existing OMO coexistence contract. No Copilot,
host-default or local-low quality call/probe is authorized.
