# ICCA 2026 camera-ready reviewer response

Paper 308 (1571357521), “History- and Forecast-Aware EV Charging Underperforms Max-Min Sharing on Worst-User Service: A Real-Session Replay Audit”

## Reviewer A

1. **Priority for pregnant people, children/newborns, older adults, disabled users and first responders.** Section VI now states that ACN-Data contains none of these attributes, so the study cannot encode or evaluate those priorities and must not use service history as their proxy. It identifies governed priority attributes, an explicit benefit definition and prospective evaluation as requirements for that extension.

2. **Structural reason the weighted objective cannot guarantee the tail metric.** Immediately after (4), Section III now explains that the controller minimizes an additive session-level weighted shortfall and cost, while the endpoint is a nonlinear order statistic of per-user means. An additive objective can accept harm concentrated among a few users in exchange for dispersed gains; bounded, lagged history weights impose neither a max-min constraint nor a tail guarantee.

3. **Guardrails and the tail-versus-delivery frontier.** Section V and Fig. 3 now report all 21 validation configurations. All pass the 103% cost guardrail and seven fail the 98% delivery guardrail. Max-min sharing is admissible and has the lowest validation tail. The locked candidate is admissible and has both the lowest tail and highest delivery among its four settings. The two-point tail-delivery Pareto frontier contains max-min sharing and least laxity, so the guardrails did not hide a better-tail candidate.

## Reviewer B

1. **Make the negative result prominent.** The title now says that the proposed controller underperforms max-min sharing on worst-user service. The abstract reports that its primary tail shortfall is 5.95 percentage points worse despite passing the delivery and cost guardrails. The conclusion retains the negative finding without a superiority claim.

2. **Avoid generalization beyond one site.** The abstract limits the conclusion to this site. Sections IV and VI retain the single-site, shared-user and non-independent-period limitations.

3. **Clarify policy-specific tail membership.** The abstract, endpoint definition and primary-results subsection now state that users are reranked within each policy, so the comparison does not track a fixed group or establish that the same people improve.

4. **Keep fixed behavior and causal limits prominent.** The abstract states that policy outcomes are simulated with behavior held fixed. Sections IV and VI retain the explanation that recorded requests and departures do not respond to simulated allocation, so the replay does not establish a causal field effect.

No test result, policy setting or frozen experimental outcome was changed for these revisions.
