# Numerical and forecast diagnostics

These analyses were added after inspection of the primary results. They reuse the original five synthetic populations, retain the validation-selected settings, and do not replace the locked primary comparison. All intervals below are exploratory and conditional on the workload generator.

## Matched numerical tie-breaking

The original point-MPC implementation can postpone charging among nearly tied plans. Its small time-preference coefficient does not reliably resolve those ties. A matched diagnostic applies a two-stage solve to each of five MPC variants across all five populations, producing 25 runs.

The first linear program minimizes the original objective. The second minimizes slot-index-weighted planned energy while allowing at most 10^-7 dollars of objective degradation. A secondary solution is accepted within 2 × 10^-7 dollars; otherwise the first solution is retained. Existing action checks and feasible-allocation fallbacks remain active.

| Result | Estimate | 95% interval |
|---|---:|---:|
| Original point-MPC mean tail shortfall | 29.75% | — |
| Point-MPC mean tail shortfall with matched tie-breaking | 19.09% | — |
| Uncertainty-only minus point MPC | −0.18 percentage points | [−4.68, 4.31] |
| History-plus-uncertainty minus point-with-history MPC | −2.46 percentage points | [−6.54, 1.61] |
| History-plus-uncertainty minus proportional-fair MPC | −2.56 percentage points | [−3.73, −1.39] |

These comparisons do not establish an incremental tail-service benefit from distribution forecasts. The 25 runs contain 48 applied fallback decisions, and their maximum applied constraint violation remains below the declared 10^-7 tolerance. The diagnostic does not establish that this tie-breaker is optimal for future arrivals.

Evidence: [scores](../results/second_pass/lexicographic_scores.csv), [paired intervals](../results/second_pass/lexicographic_paired_intervals.csv), and [verification](../results/second_pass/verification.json).

## Forecast evaluation at later landmarks

The original one-hour landmark contains only 18 departure events among 3,769 eligible sessions at a 60-minute lead. Additional evaluation uses fixed landmarks at 1, 3, 5, 7, and 9 hours after request activation, with leads of 30, 60, 120, and 240 minutes. No model is refitted or selected using these scores.

Scores first average across available landmarks within a session, then across sessions within a population. This prevents long sessions from receiving more total weight merely because they survive to more landmarks. The evaluated populations still depend on remaining connected at each landmark.

At a 60-minute lead, the session-balanced mean Brier score is 0.0933 for empirical durations and 0.0842 for calibrated hazards. The paired difference is −0.00917, with interval [−0.01168, −0.00665]. Calibration versus the uncalibrated hazard is inconclusive. Improved forecast scores alone do not establish improved charging outcomes.

Evidence: [landmark scores and event counts](../results/second_pass/forecast_by_landmark.csv), [session-balanced scores](../results/second_pass/forecast_session_balanced.csv), and [paired forecast intervals](../results/second_pass/forecast_paired_intervals.csv).

## Request-update ordering

The original adapter excluded two records with distinct request-update timestamps that fell into the same rounded slot. A separate sensitivity adapter orders updates by exact availability before rounding, retaining the latest available update within a slot. It also rejects conflicting exact-time updates, duplicate session IDs, and malformed revisions.

This correction retains 14 sessions from ten users, compared with the original 12 sessions from eight users. Neither audit contains any user with at least five eligible sessions. The discovery sample therefore remains unsuitable for the proposed repeated-user evaluation; this finding does not characterize the complete ACN dataset.

Evidence: [ordering audit](../results/second_pass/revision_order_audit.json), [adapter](../scripts/audit_revision_order.py), and [tests](../tests/test_second_pass.py).

## Interpretation

The primary comparison shows a modest reduction relative to the selected proportional-fair controller, while the practical target remains unmet. Simple history-weighted sharing has lower mean tail shortfall than the full controller, with an inconclusive paired contrast. Together with the numerical diagnostic, this limits claims that optimization complexity or distribution forecasts are necessary for the observed service gains.

A confirmatory follow-up would need a common numerical implementation, validation-only retuning, and untouched evaluation populations. Empirical claims additionally require complete request and identity records with adequate repeated-user coverage. See the [methods](method_and_protocol.md), [primary results](results_report.md), and [related work](recent_literature_review.md) for the study's remaining assumptions and limitations.
