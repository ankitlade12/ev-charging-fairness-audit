# Experimental results

The [diagnostic analyses](diagnostics.md) describe the matched numerical comparisons, later forecast landmarks, and corrected request-update ordering. These exploratory analyses supplement the locked primary study.

The prespecified practical target was not met. All numerical policy results below come from designed synthetic workloads. The real ACN discovery sample is used only for the separate coverage audit.

## Primary result

Validation selected `pf_mpc` as the fairness comparator. The candidate's worst-decile user shortfall was 16.27% versus 18.83%. The paired difference was -2.56 percentage points (lower (better)); the 95% t interval across five generated populations was [-3.73, -1.38]. The target required a reduction of at least five percentage points.

Mean paired delivery ratio was 100.20% (95% interval [100.06, 100.35]); unit-cost ratio was 100.17% ([100.07, 100.26]). Entrant mean-shortfall difference was 0.06 percentage points ([-0.58, 0.70]). Ratios average paired population ratios, not ratios of pooled totals.

| Policy | Worst-tail % | Mean shortfall % | MWh | $/delivered kWh | Entrant shortfall % |
| --- | --- | --- | --- | --- | --- |
| equal | 20.53 | 5.738 | 13.624 | 0.153 | 4.224 |
| fcfs | 20.708 | 5.596 | 13.719 | 0.157 | 6.181 |
| edf | 18.177 | 4.839 | 13.848 | 0.158 | 4.735 |
| laxity | 18.978 | 5.311 | 13.906 | 0.156 | 4.925 |
| maxmin | 19.801 | 7.669 | 13.497 | 0.15 | 7.776 |
| debt_share | 15.734 | 5.323 | 13.718 | 0.154 | 4.429 |
| point | 29.754 | 15.125 | 12.39 | 0.153 | 15.289 |
| stochastic | 18.911 | 4.583 | 13.897 | 0.155 | 3.821 |
| point_history | 29.028 | 15.097 | 12.392 | 0.153 | 14.66 |
| pf_mpc | 18.829 | 4.579 | 13.909 | 0.156 | 3.788 |
| history | 16.272 | 4.356 | 13.938 | 0.156 | 3.848 |

These are means across five replications at 0.35 times the training peak. Energy is mean MWh per replication. All session counts, per-seed values and other capacities are saved in `test_scores.csv`. The tail uses each policy's own ranking and a minimum of five sessions per user. No session-level significance test is used.

## Data coverage and pilot

The real-data adapter retained 12 of 26 discovery records, with eight users and no user having five sessions. Six records lacked identity, three crossed a local-day boundary, three had no full service slot after request availability, and two had ambiguous updates within one rounded slot. These are mutually exclusive primary exclusions; raw records are preserved. No empirical fairness result is inferred from this sample.

The validation pilot contained 21 controller configurations. `validation_grid.csv` preserves every result, including configurations failing the delivery or unit-cost selection guardrails. Candidate parameters were gamma 40, lambda 4, rho 0.2; the matched point-history and no-history ablations also selected gamma 40. The primary comparator and all settings were locked before test evaluation.

## Uncertainty and structural limits

The seed-11 conditional five-day block bootstrap interval for the candidate-minus-comparator tail difference was [-2.19, -0.28] percentage points. This sensitivity resamples realized outcomes without rerunning service-history dynamics. It is not interchangeable with the primary interval across independently generated populations. Five replications offer limited precision and describe the specified generator family only.

`tables/strata.csv` reports requested-energy ranges, dwell-time ranges, training-defined variability groups, entrants and individual full-power infeasibility. The latter is only an individual physical lower bound; shared congestion can add further shortage. `tables/offline_bounds.csv` contains maximum aggregate energy under actual future arrivals and departures. Every causal run was checked against that bound; the oracle is never ranked as a deployable controller.

## Forecasting, ablations and interventions

`tables/forecast_scores.csv` and `tables/forecast_cohorts.csv` report Brier score, log loss, event counts and denominators at 30, 60 and 120 minutes from the one-hour landmark. This conditioning excludes sessions already disconnected. `tables/reliability.csv` contains all plotted bins; small bins are not evidence of calibrated probabilities.

`tables/supplement_means.csv` and `tables/supplement_effects.csv` retain calibration, empirical-distribution, horizon, earlier/later forecast, spread, shorter-stay and request-inflation results with no retuning. They are secondary analyses, not new primary hypotheses. A distribution spread transform reconditions on current survival and does not guarantee an unchanged conditional median. Error parity was not established and no real-world causal attribution is made.

## Correctness and computation

Across the 220 primary policy/capacity/population runs, 18 fallback decisions were recorded. Maximum recorded numerical constraint excess was 8.46e-08; the largest per-run 95th-percentile decision latency was 0.0735 seconds. The tolerance is 1e-7 in the checked numerical units. Runtime includes Python planning overhead and concurrent workloads on this machine; it is not a production latency guarantee. The full action and continuous-plan trace is saved for the seed-11 primary pair; all runs save session outcomes, settings, aggregate diagnostics and history-dependent results. Other full decision traces can be generated by enabling `trace=True`.

A separate clean Python environment reproduces the primary seed-11 pair within the documented tolerance when `reproduction/verification.json` reports success. This is same-machine automated reproduction, not independent author validation. The test transcript and final manifest provide the actual status.

## Contribution decision

The evidence supports an inspectable comparison protocol and a bounded, model-conditional statement about history weighting under uncertain departures. It does not establish a new fairness algorithm, universal improvement, actual driver disadvantage, or grid protection. The manuscript should be evaluated as a controlled audit with an honest negative-result pathway. Independent novelty review and author sign-off remain necessary before any submission.

## Additional interpretation and development-population sensitivity

At the 60-minute lead, mean Brier scores are 0.0047 for empirical durations, 0.0048 for the uncalibrated hazard and 0.0048 after calibration. These forecast scores alone do not establish better control.

Removing calibration changes candidate tail shortfall by 0.16 percentage points (interval [-0.22,0.54]) relative to its unperturbed run.

Later forecasts change candidate tail shortfall by 21.91 percentage points (interval [13.59,30.23]) relative to its unperturbed run.

Under shorter stays, the candidate-minus-comparator tail change is -3.81 percentage points ([-5.13,-2.48]).

Under larger requests, the candidate-minus-comparator tail change is -6.05 percentage points ([-7.15,-4.95]).

Because seed 11 also supplies controller validation, a sensitivity excludes that development population. Across the remaining four populations, tail change is -2.81 percentage points ([-4.20,-1.42]). This guards against mistaking within-population temporal validation for wholly independent population selection.

## Simpler-controller and numerical-tie diagnostics

The simpler history-weighted sharing policy has mean worst-tail shortfall 15.73%, compared with 16.27% for the full candidate. Candidate-minus-sharing difference is 0.54 percentage points (95% interval [-1.81, 2.88]); the interval does not establish a tail advantage for either. Candidate delivery is 101.60% and its unit cost 101.31% of simple sharing. This comparison does not replace the locked proportional-fair primary comparator. It limits any claim that the more complex controller is necessary.

A post-primary point-MPC diagnostic freezes the predicted deadline at arrival. Its mean tail shortfall is 27.21%, versus 29.75% for the original rolling-median point MPC. A second diagnostic minimizes planned energy-weighted slot index after constraining the economic objective within 1e-7 dollars of its first optimum. That lexicographic tie-break gives 19.09% mean tail shortfall. This large change shows that point-MPC comparisons depend on optimization tie-breaking, not only departure uncertainty. The original 1e-9 preference is too small to reliably resolve numerical ties. Neither diagnostic is validation-selected or used to rewrite the locked primary result. The lexicographic diagnostic recorded 17 feasible fallback decisions, included in its outcomes; it still obeys the applied-action tolerance. The full candidate's matched point comparison should therefore not be interpreted as an isolated causal estimate of the value of uncertainty.
