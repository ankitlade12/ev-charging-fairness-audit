# Current real-session protocol

The active specification is [`config/real_data_protocol.json`](../config/real_data_protocol.json). It was written after the synthetic study and real-data coverage audit, then locally hash-locked before real-controller evaluation. This is not external preregistration. The frozen core and historical synthetic results remain unchanged.

## Observations and events

At each 15-minute boundary the evaluator processes observed departures and policy-specific history updates, then arrivals and available request revisions. Controllers receive immutable current observations. Actual future departures, revisions and arrivals are not exposed. Late requests activate only when recorded as available. Request decreases do not erase previously delivered energy; final shortfall uses the last valid request before departure, and excess over that final request is reported separately.

Forecast training uses January–April JPL sessions, calibration May and controller selection June. The primary test is July–September; October–December is a second period at the same site. Forecast summaries are frozen after training. History resets to zero for each split, policy and capacity; it is not carried from Q3 into Q4.

## Departure model and controller

The logistic discrete-time hazard uses elapsed time and its square, declared time remaining/overdue duration, local arrival hour/weekday and shrunk personal duration summaries. Training personal features use earlier completed sessions; population defaults and scaling use training data. Calibration fits an affine logit transform with a positive slope on the complete subsequent at-risk rows, without class reweighting. The pooled empirical conditional duration model is the forecasting baseline.

The 24-hour common plan enforces per-session power, a shared grid-side site cap, and total battery-side planned energy no greater than remaining demand. Under this cap, expected unserved energy equals remaining demand minus survival-weighted planned delivery. This identity is exact for the common-plan surrogate; it is not a solution to general stochastic recourse. Only the first action is applied; later actions are replanned, without forecasts of future arrivals.

The candidate weights normalized expected session shortfall by `1 + lambda * D[user]`. Completed shortfall updates `D <- 0.8 D + 0.2 shortfall`. This keeps history bounded, but gives no entitlement or eventual-service guarantee. The eleven policies are equal sharing, FCFS, declared EDF, least laxity, max–min cumulative fulfillment, history-weighted sharing, point MPC, uncertainty-only MPC, point MPC with history, proportional-fair MPC and the candidate. Proportional fairness uses a finite piecewise-linear tangent approximation to log cumulative normalized service.

The implementation retains a slot-index-weighted 1e-9 linear perturbation in the primary objective. All five MPC methods use the same two-stage numerical procedure: solve the original objective, then prefer earlier planned energy subject to a 1e-7-dollar primary allowance, accepting within 2e-7 dollars. First-stage solutions remain available if the second stage fails. Applied infeasibility or solver failure invokes the original capped remaining-demand fallback. Every applied inequality is checked at 1e-7 tolerance. Shared tie-breaking need not uniquely resolve allocation among vehicles.

## Selection and comparisons

The grids are gamma={10,40}, lambda={1,4}, rho=.2, horizon=96. Two-parameter history MPC policies get four configurations; other MPC policies get two. The 21 June runs select each policy's lowest tail subject to ≥98% equal-sharing energy and ≤103% unit cost. If none qualifies, delivery deficit is prioritized. The same rule chooses a primary comparator among equal, max–min, history sharing and proportional-fair MPC.

**Max–min sharing** was selected. Candidate and point-history use gamma=40/lambda=4; point, uncertainty-only and proportional-fair MPC use gamma=40; history sharing uses lambda=4. Selection was locked before either test period. The 31 evaluation runs comprise 11 policies × 2 periods at capacity fraction .35, plus three specified policies × three additional Q3 fractions (.20,.50,1.00). No test tuning or removal of unfavorable outcomes occurred.

## Endpoints and uncertainty

Average final-request shortfall within each user, retain users with ≥5 sessions in the evaluated period, and average the worst ceil(10% N) values. Each policy reranks users. Q3 has 176 eligible users/tail 18; Q4 has 194/tail 20. All eligible sessions enter aggregate energy and cost, including energy above final decreased requests. Cost is the simulated grid-energy bill divided by delivered battery energy.

The target is ≥5-percentage-point tail reduction with ≥98% comparator energy and ≤103% comparator cost/kWh. It is not met. Intervals use 2,000 paired five-observed-day moving-block outcome resamples, seed 20260922, recomputing eligibility and ranks. They hold realized histories, fitted forecasts and settings fixed. They are conditional resampling summaries, not independent-site or dynamic-replay confidence intervals. Two- and ten-day sensitivity applies to the primary comparison. Comparisons are pointwise, without multiple-testing adjustment; secondary endpoints are exploratory.

Forecast audits condition on still being connected at 1,3,5,7,9 hours after request activation, with leads of 30,60,120,240 minutes. Scores average landmarks within sessions before averaging sessions; event counts are supplied. Accuracy comparisons do not alone establish control benefit.

## Audit boundaries

`scripts/verify_real_data.py` independently reconstructs action-time requests, per-policy history, tariff costs and energy accounting for all 52 validation/evaluation runs. `scripts/reproduce_real_pair.py` freshly replays the locked Q3 pair in the same environment. These are automated checks, not independent human or cross-machine replication. The fixed-request offline bound in the historical artifact is not used for revision-containing real records. No live trial, demographic equity, behavioral response, transformer-health or electrical-network claim is supported.
