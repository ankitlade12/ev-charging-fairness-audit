# Current claim-to-evidence map

| Claim | Evidence | Boundary |
|---|---|---|
| Recorded JPL inputs support a repeated-user replay | `results/real_data/acquisition.json`, `data_audit.json`, `coverage.csv` | Complete relative to queried official export; not every physical site event |
| 16,529 sessions assigned to chronological periods | Normalization audit, split files and hashes | Missing-ID, cross-day and partial-slot exclusions; excluded load absent |
| Candidate does not beat validation-selected max–min | `selection_lock.json`, `test_scores.csv`, `paired_intervals.csv` | One site; two periods share users; conditional outcome intervals |
| Q3 tail is 58.30% versus 52.35%; +5.95 pp [2.69,10.85] | Session-derived scores and paired five-day resampling | Policy-specific tails rerank users, not a fixed-person treatment effect |
| Primary energy/cost point guardrails pass, fairness target fails | `report_numbers.json`, paired endpoint ratios | Modeled electricity bill, efficiency and requests; final-request excess retained |
| Validation guardrails did not hide a better-tail candidate | All 21 rows in `validation_grid.csv`; `validation_tradeoff.pdf` | Tail--delivery frontier is validation-only; cost is checked separately |
| History improves uncertainty-only MPC in Q3 | Matched history-versus-stochastic row in paired intervals | Does not establish superiority over other objective families |
| Departure forecast scores do not establish allocation benefit | Both `*_forecast_balanced.csv`, landmark counts; history-versus-point-history comparison | No test model selection; no causal forecast-quality claim |
| Demographic or critical-user priority is not evaluated | ACN-Data fields and Section VI limitation | No pregnancy, dependent-child/newborn, age, disability or first-responder attributes; service history is not a proxy |
| All applied actions satisfy model constraints and current requests | `independent_verification.json`: 52 runs, 3,292,992 action rows | Numerical tolerance 1e-7; not electrical-network or battery validation |
| Replayed primary pair matches saved outcomes | `fresh_pair_reproduction.json` | Same machine, environment and fitted model; not independent replication |
| ICCA formatting passes local checks | `pdf_verification.json`, rendered pages and package verification | IEEE PDF eXpress and EDAS validation outstanding |
| Text is specifically written and sources attributed | Manuscript review and limited local overlap screen | No iThenticate/Turnitin clearance or originality guarantee |

Source and protocol locks precede real controller outcomes; selection precedes tests. The extension was designed after historical synthetic work. The archived synthetic evidence supports a different workload and must not be pooled with this real-session analysis.
