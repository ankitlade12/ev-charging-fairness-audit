# Real-session replay results

The current study uses recorded JPL sessions from official ACN-Data exports. Alternative-policy delivery, cost and service shortfall are simulated under common simplified physics. These are not measured controller interventions.

## Main result

The validation-selected comparator is **max–min sharing**. The candidate's worst-tail shortfall is **58.30% versus 52.35%** in July–September: **+5.95 [+2.69, +10.85] percentage points**. Positive differences mean worse shortfall. October–December gives **64.79% versus 55.91%**, or **+8.88 [+5.92, +13.53] points**. The five-point improvement target fails in both periods.

Primary energy ratio: **98.83% [98.60, 99.22]**. Primary unit-cost ratio: **98.95% [98.79, 99.21]**. These point estimates meet the 98% delivery and 103% cost guardrails.

Intervals are paired five-observed-day moving-block percentile outcome-resampling intervals (2,000 replicates), conditional on fitted settings and realized histories. They are not independent-site, refitting, selection or deployment confidence intervals. Tail eligibility and ranks are recomputed within each resample.

## All primary-capacity policies

| Policy | Q3 tail % | Q3 MWh | Q3 $/kWh | Q4 tail % | Q4 MWh | Q4 $/kWh |
|---|---:|---:|---:|---:|---:|---:|
| Equal sharing | 60.87 | 75.600 | 0.1861 | 64.72 | 75.627 | 0.1903 |
| FCFS | 68.61 | 76.179 | 0.1868 | 71.46 | 75.709 | 0.1902 |
| EDF | 67.63 | 75.302 | 0.1855 | 70.99 | 75.093 | 0.1894 |
| Least laxity | 58.82 | 77.755 | 0.1901 | 62.15 | 77.621 | 0.1923 |
| Max-min sharing | 52.35 | 77.031 | 0.1891 | 55.91 | 76.998 | 0.1921 |
| History-weighted sharing | 56.47 | 76.479 | 0.1874 | 61.14 | 76.198 | 0.1908 |
| Point MPC | 64.03 | 75.775 | 0.1860 | 65.21 | 75.778 | 0.1893 |
| Uncertainty-only MPC | 69.64 | 74.965 | 0.1852 | 70.99 | 75.069 | 0.1897 |
| Point MPC + history | 56.69 | 76.113 | 0.1865 | 62.49 | 75.976 | 0.1896 |
| Proportional-fair MPC | 61.19 | 76.074 | 0.1869 | 63.32 | 75.964 | 0.1907 |
| History + uncertainty | 58.30 | 76.133 | 0.1871 | 64.79 | 75.877 | 0.1906 |

## Complete comparison record

`results/real_data/paired_intervals.csv` contains every specified candidate comparison, both periods and all three endpoints. `block_sensitivity.json` retains the two- and ten-day checks. No test-outcome tuning was used. All policies retain their unfavorable outcomes.

### test_q3

| Comparator | Tail difference, pp [interval] | Energy ratio, % [interval] | Unit-cost ratio, % [interval] |
|---|---:|---:|---:|
| Max-min sharing | +5.95 [+2.69, +10.85] | +98.83 [+98.60, +99.22] | +98.95 [+98.79, +99.21] |
| History-weighted sharing | +1.83 [-0.26, +5.02] | +99.55 [+99.36, +99.83] | +99.82 [+99.68, +100.01] |
| Proportional-fair MPC | -2.89 [-4.08, +2.74] | +100.08 [+99.91, +100.30] | +100.10 [+100.00, +100.24] |
| Point MPC + history | +1.61 [-1.35, +3.74] | +100.03 [+99.87, +100.26] | +100.30 [+100.15, +100.49] |
| Uncertainty-only MPC | -11.34 [-12.52, -5.16] | +101.56 [+101.32, +101.88] | +101.03 [+100.84, +101.28] |

### test_q4

| Comparator | Tail difference, pp [interval] | Energy ratio, % [interval] | Unit-cost ratio, % [interval] |
|---|---:|---:|---:|
| Max-min sharing | +8.88 [+5.92, +13.53] | +98.54 [+98.30, +98.87] | +99.24 [+98.99, +99.57] |
| History-weighted sharing | +3.65 [+1.55, +6.68] | +99.58 [+99.33, +99.77] | +99.90 [+99.76, +99.98] |
| Proportional-fair MPC | +1.47 [-1.48, +5.89] | +99.89 [+99.74, +100.11] | +99.94 [+99.87, +100.05] |
| Point MPC + history | +2.30 [-0.63, +4.30] | +99.87 [+99.56, +100.25] | +100.56 [+100.21, +100.99] |
| Uncertainty-only MPC | -6.20 [-9.02, -2.69] | +101.08 [+100.89, +101.32] | +100.49 [+100.37, +100.65] |

## Verification and limits

21 validation runs and 31 test/sensitivity runs; 27 passing tests; 61 test/sensitivity fallback decisions; maximum applied violation 9.989e-08, within 1e-7. Every run retains private actions and history. See `independent_verification.json` for action, request, history, tariff and metric checks.

Request decreases leave candidate excess delivery of 259.34 kWh (Q3) and 62.38 kWh (Q4) above final requests; action-time limits still hold. Delivery includes that energy. Model power/efficiency/tariff are assumptions; excluded sessions supply no background demand. Forecast performance does not by itself establish better control.

Earlier synthetic findings and their numerical sensitivity remain in `results/` and `results/second_pass/`, with documents preserved under `docs/historical_synthetic/`. They are separate evidence and do not replace or pool with the real-session findings.
