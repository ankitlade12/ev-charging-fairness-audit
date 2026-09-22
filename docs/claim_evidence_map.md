# Claim-to-artifact map

| Claim | Evidence |
| --- | --- |
| Primary tail contrast | results/tables/paired_intervals.csv; results/primary_conclusion.json |
| Every baseline and capacity | results/test_scores.csv |
| Data feasibility gate | results/data_audit.json; data/raw/ornl_metadata.json |
| Forecast quality | results/tables/forecast_scores.csv; results/tables/reliability.csv |
| Ablations and stresses | results/tables/supplement_effects.csv |
| Offline service upper bounds | results/tables/offline_bounds.csv |
| Leakage/physics checks | tests/test_core.py; results/clean_environment_tests.txt |
| Fresh-environment reproduction | results/reproduction/verification.json |
| Protocol freeze | config/protocol.json; results/protocol_lock.json; config/secondary_analysis_lock.json |

## Second-pass claims (exploratory unless noted)

| Claim | Evidence |
| --- | --- |
| Matched tie-breaking, five MPC variants, 25 runs | results/second_pass/lexicographic_scores.csv; results/second_pass/lexicographic_paired_intervals.csv |
| Later-landmark forecast scores and event counts | results/second_pass/forecast_by_landmark.csv; results/second_pass/forecast_session_balanced.csv; results/second_pass/forecast_paired_intervals.csv |
| Revised eligibility: 14 sessions, ten users, no user with five sessions | results/second_pass/revision_order_audit.json; scripts/audit_revision_order.py |
| Primary source/protocol and outcomes preserved | results/second_pass/primary_preservation.json; results/second_pass/verification.json |
| New implementation checks | tests/test_second_pass.py; results/second_pass/tests.txt |
| Literature overlap and current version checks | docs/recent_literature_review.md |
| Seven-page author and anonymous review manuscripts; local format checks only | results/pdf_verification.json; results/pdf_review_verification.json; results/pdf_review/review.json |
