# ICCA 2026 camera-ready reviewer response

Paper 308 (1571357521), “History- and Forecast-Aware EV Charging Underperforms Max-Min Sharing on Worst-User Service: A Real-Session Replay Audit”

## Reviewer A

1. **Priority for pregnant people, children and newborns, older adults, disabled users and first responders.** Section VI states that ACN-Data contains none of these attributes. The study therefore cannot encode or evaluate those priorities, and must not use service history as their proxy. Section VI also names what that extension would require: governed priority attributes, an explicit benefit definition and prospective evaluation.

2. **Structural reason the weighted objective cannot guarantee the tail metric.** Immediately after the controller objective, Eq. (6), Section III now names the mechanism directly.
   - The objective is linear in the allocation, so each planned kWh has the fixed value $S_i(k)[\gamma(1+\lambda D_{u(i)})/q_i-c_k/\eta_i]$, however little the session has already received.
   - It therefore favors small requests, and can offset large losses for a few users with many small gains.
   - The endpoint is instead an order statistic of per-user means. A fixed-weight sum reaches a max-min allocation only with weights matched to that allocation, and those weights depend on who ends up worst-served.
   - Bounded, lagged history weights do not track those weights, whereas max-min sharing serves the least-fulfilled session first.

   The introduction and the conclusion now also state this reason.

3. **Guardrails and the tail-versus-delivery frontier.** Section V-A and Fig. 3 report all 21 validation configurations.
   - All of them pass the 103% cost guardrail. Seven, all with $\gamma=10$, fail the 98% delivery guardrail.
   - The guardrails changed no selection. In every policy, the lowest-tail configuration is admissible, and each rejected configuration has a higher tail than its policy's choice.
   - Max-min sharing and least laxity form the tail–delivery frontier on the validation data. They form it again among the eleven locked policies in both test periods (Table II).
   - Max-min sharing has both a lower tail and higher delivery than the candidate in all three periods.
   - Fig. 3 now labels both frontier points.

## Reviewer B

1. **Make the negative result prominent.**
   - The title states that the proposed controller underperforms max-min sharing on worst-user service.
   - The abstract reports a primary tail shortfall 5.95 percentage points worse.
   - The introduction now states that the result is negative, with the gaps in both test periods (5.95 and 8.88 points).
   - The conclusion now states the loss in both periods, rather than only that the improvement target was missed.
   - Section V-C now states that the candidate is worse than simple history-weighted sharing in the later period.

2. **Avoid generalization beyond one site.** The abstract and the new introduction sentence limit the result to this site. Sections IV and VI retain the single-site, shared-user and non-independent-period limitations. The conclusion no longer implies that a deployment claim is made.

3. **Clarify policy-specific tail membership.** Users are reranked within each policy, so tail comparisons do not track a fixed group or establish that the same people improve. The paper now states this wherever tails are compared:
   - the abstract
   - the endpoint definition (Section IV-D)
   - the Table II and Fig. 3 captions
   - Sections V-B and V-C
   - the conclusion

4. **Keep fixed behavior and causal limits prominent.** The abstract states that policy outcomes are simulated with behavior held fixed. Sections IV and VI retain the explanation that recorded requests and departures do not respond to simulated allocation, so the replay does not establish a causal field effect.

No test result, policy setting or frozen experimental outcome was changed for these revisions.
