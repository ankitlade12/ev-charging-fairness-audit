# Current claim-to-evidence map

| Claim | Evidence | Boundary |
|---|---|---|
| Recorded JPL inputs support a repeated-user replay | `results/real_data/acquisition.json`, `data_audit.json`, `coverage.csv` | Complete relative to queried official export; not every physical site event |
| 16,529 sessions assigned to chronological periods | Normalization audit, split files and hashes | Missing-ID, cross-day and partial-slot exclusions; excluded load absent |
| Candidate does not beat validation-selected max–min | `selection_lock.json`, `test_scores.csv`, `paired_intervals.csv` | One site; two periods share users; conditional outcome intervals |
| Q3 tail is 58.30% versus 52.35%; +5.95 pp [2.69,10.85] | Session-derived scores and paired five-day resampling | Policy-specific tails rerank users, not a fixed-person treatment effect |
| Primary energy/cost point guardrails pass, fairness target fails | `report_numbers.json`, paired endpoint ratios | Modeled electricity bill, efficiency and requests; final-request excess retained |
| History improves uncertainty-only MPC in Q3 | Matched history-versus-stochastic row in paired intervals | Does not establish superiority over other objective families |
| Departure forecast scores do not establish allocation benefit | Both `*_forecast_balanced.csv`, landmark counts; history-versus-point-history comparison | No test model selection; no causal forecast-quality claim |
| All applied actions satisfy model constraints and current requests | `independent_verification.json`: 52 runs, 3,292,992 action rows | Numerical tolerance 1e-7; not electrical-network or battery validation |
| Replayed primary pair matches saved outcomes | `fresh_pair_reproduction.json` | Same machine, environment and fitted model; not independent replication |
| ICCA formatting passes local checks | `pdf_verification.json`, rendered pages and package verification | IEEE PDF eXpress and EDAS validation outstanding |
| Text is specifically written and sources attributed | Manuscript review and limited local overlap screen | No iThenticate/Turnitin clearance, AI score or originality guarantee |

Source and protocol locks precede real controller outcomes; selection precedes tests. The extension was designed after historical synthetic work. The archived synthetic evidence supports a different workload and must not be pooled with this real-session analysis.
