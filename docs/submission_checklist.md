# IEEE CCWC submission checklist

Target: **IEEE CCWC 2027 at ieee-ccwc.org**. This is a local review package. No manuscript has been submitted, no account registered, no payment made, and nobody contacted.

## Conference rules checked on 13 September 2026

The [official call](https://ieee-ccwc.org/call-for-papers/) lists a regular-paper limit of seven pages, with up to three paid extra pages, and a work-in-progress limit of six pages, with up to two paid extra pages. It links the IEEE conference template. The page also contains older duplicated dates, so use the clearly labeled 2027 block and reconfirm before submission.

The [submission page](https://ieee-ccwc.org/submissions/) lists EDAS and requires double-blind review: replace author names with “Author 1,” etc., and omit identifying affiliations, funding and acknowledgments. The listed full-paper deadline is **6 November 2026**; camera-ready deadline **4 December 2026**; conference **4–6 January 2027**. No deadline timezone or acceptance-notification date was established from this page. PDF eXpress and copyright details were placeholders when checked. Do not invent those identifiers.

A separate similarly named `ccwc.in` site gives different dates and event details. It is not used for this package. Reviewers/authors should verify the intended event against the official IEEE conference listing before any transaction.

## Second-pass status

The [diagnostic analyses](diagnostics.md) found and addressed a misleading point-forecast comparison, sparse early forecast scoring, missing closely related literature, and unnecessary same-slot data exclusions. The [literature matrix](recent_literature_review.md) records access depth. Twenty-five new diagnostic runs and 23 tests pass. All new experiments remain exploratory. The revised six-page manuscript fits both the regular and WIP base limits. Scientific category selection remains open.

- [x] Apply consistent numerical tie-breaking to all five MPC variants in a separate sensitivity.
- [x] Report inconclusive distribution-versus-point tail contrasts prominently.
- [x] Extend proper-score evaluation to later fixed landmarks, with equal-session weighting.
- [x] Correct exact-time request ordering in a versioned data sensitivity (14 sessions, ten users; gate still fails).
- [x] Update related work and distinguish reputation, access priorities and repeated-user burden.
- [ ] Establish an incremental contribution with fresh evidence before presenting this as a superior new method.
- [ ] Retune any revised numerical implementation on validation only and use untouched evaluation populations before a confirmatory comparison.

## Scientific readiness

- [x] Identify absent assessment/pilot inputs; create a new assessment without pretending to have inspected missing files.
- [x] Audit accessible real records and disclose failure of the repeated-user gate.
- [x] Specify synthetic data generation and keep it separate from empirical evidence.
- [x] Include multiple fairness baselines, point and uncertainty ablations, and hindsight aggregate-energy reference; literature-faithful least-laxity-ratio and other advanced comparators remain potential next-study additions.
- [x] Lock controller settings and primary comparator before final evaluation.
- [x] Use independent generated populations as primary replication units.
- [x] Retain failed targets and negative findings in the results and abstract.
- [ ] Obtain independent research/domain review of novelty and scientific adequacy.
- [ ] Obtain the missing original assessment and pilot if they are intended to be part of the submission's provenance.
- [ ] Obtain a complete authorized dataset and establish empirical repeat-user coverage before making any real-driver fairness claim.
- [ ] If submitting this simulation-only study, explicitly approve that scope and evaluate whether work-in-progress is more appropriate than a regular paper.

The last two options represent different possible future scopes. The delivered manuscript is a complete simulation-study draft; it does not contain fabricated empirical placeholders that could be mistaken for completed data analysis.

## Author review

- [ ] Confirm author list, contribution statements, affiliations, corresponding author and ORCIDs outside the blind manuscript.
- [ ] Read the entire paper and source code; take responsibility for the claims and reported results.
- [ ] Verify every numerical claim against the generated tables and claim-to-artifact map.
- [ ] Review citations, overlap with prior work, originality, and any related submissions.
- [ ] Confirm code license and rights for future public redistribution. Raw individual histories are not included in the distributable artifact.
- [ ] Review conflicts of interest and any institution-specific research requirements applicable to a future real-data study.

## AI disclosure

[IEEE's author policy](https://conferences.ieeeauthorcenter.ieee.org/author-ethics/guidelines-and-policies/submission-policies/), rechecked on 19 September 2026, requires disclosure of generated content, identifying the system, affected sections, and extent of assistance. This package includes generated manuscript text and code; it is not merely grammar editing. At the author's request, the current local manuscript omits the disclosure section. `ai_disclosure.md` retains the disclosure for author review; this local draft is not ready for submission until the required disclosure is restored in the appropriate location.

There is an unresolved placement conflict between CCWC's removal of acknowledgments for blind review and IEEE's requested acknowledgment disclosure. The human submitter must reconcile placement against the final event instructions before submitting; no organizer has been contacted. Keeping the disclosure in a separate local document does not satisfy an in-article submission requirement. The conference page also mentions an AI-detection score; no score is claimed.

## Automated package verification

The revised PDF has six US-letter pages, embedded fonts with no Type 3 fonts, empty author metadata, and no undefined references or overfull boxes in the final build. Rendered pages were visually inspected by Codex. The primary experiment and saved ledger checks pass; see `results/package_verification.json`, `results/pdf_verification.json` and the clean-environment test transcript. These checks do not replace human author review.

## File and format checks

- [ ] Confirm manuscript category and page count in `results/pdf_verification.json` against the latest call.
- [ ] Visually inspect all pages, equations, legends, table widths and reference wrapping.
- [ ] Check PDF author metadata and anonymize self-identifying links and supplementary materials.
- [ ] Confirm readable embedded fonts and IEEE column/page geometry.
- [ ] Inspect the source archive and avoid packaging private data, usernames, environment paths or cached credentials.
- [ ] Confirm supplement/archive acceptance in the actual submission system; no such allowance is assumed.
- [ ] For camera-ready only: add real authors, required acknowledgments/disclosure, verified copyright notice and PDF eXpress validation when official details become available.

## External action gate

**Explicit authorization is still required for submission, public repository publication, contact with organizers or authors, account creation, and payment.** Finishing the local package does not authorize any of these actions. Acceptance, indexing, reviewer scores and field performance are not guaranteed.
