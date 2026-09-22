# IEEE CCWC 2027 submission checklist

Updated 21 September 2026 against the [submission instructions](https://ieee-ccwc.org/submissions/) and [call for papers](https://ieee-ccwc.org/call-for-papers/). The user confirmed this event as the target. No paper has been submitted and no organizer has been contacted.

## Delivered versions

- The local `manuscript/main.pdf` is the named author copy. Author order, names, emails and the shared Independent Researcher, Dallas, USA affiliation were provided by the user.
- The local `manuscript/review.pdf` is the anonymous review copy with Author 1 and Author 2, no affiliations or email links, and empty author metadata. Use this version for review after resolving the disclosure-placement question below.
- Both copies have seven US-letter pages, embedded non-Type-3 fonts and no undefined references or overfull boxes. They fit the regular-paper base limit, but exceed the six-page WIP base limit. Regular papers permit up to three paid extra pages; WIP permits up to two. Category selection remains the authors' decision.
- PDFs, manuscript sources and final delivery files stay local and are ignored by Git. The publication history was subsequently rewritten to exclude the manuscript. Because GitHub still served cached old commits, the original repository was retained as a private backup and a fresh repository received only the cleaned history. The old manuscript commit returns HTTP 404 in the replacement repository. Existing private backups and downloaded copies are not erased.

## Dates and format

The current event pages list full papers due **6 November 2026**, camera-ready papers due **4 December 2026**, and the conference on **4–6 January 2027**. The submission page links EDAS. It requires anonymous review papers and removes names, affiliations, IEEE grades, funding references and acknowledgments. The call contains duplicated historical dates; the 2027 block is used here. Deadline timezone and acceptance-notification date remain unspecified. PDF eXpress and copyright details remain placeholders. No identifier, copyright line or acceptance status has been invented.

## Scientific review completed

- [x] Recomputed metrics from all 220 primary and 55 supplementary saved session trajectories.
- [x] Recomputed the primary paired intervals and checked 16 numerical manuscript macros.
- [x] Checked all primary deliveries against saved offline upper bounds and session shortfall definitions.
- [x] Verified all 25 numerical-diagnostic runs and forecast score identities with the existing checker.
- [x] Ran all 23 existing tests; checked primary source/protocol and historical output hashes unchanged.
- [x] Clarified slot units, horizon indices, tail denominators and policy-specific reranking.
- [x] Disclosed pointwise intervals, no multiplicity correction, and conditioning on selected settings.
- [x] Retained failed practical targets, lack of superiority to simple history sharing, and synthetic-only scope.
- [x] Rechecked closest recent literature and updated the Puech preprint to the inspected v4.
- [x] Built and visually checked both PDFs; these are local checks, not IEEE PDF eXpress certification.

The new numerical review reuses saved outcomes; it is not a fresh full experiment, independent human replication or field validation. The earlier clean-environment reproduction remains documented separately.

## Remaining research limits

The empirical discovery sample has 14 eligible sessions from ten users, with no user meeting the five-session gate. All controller findings are synthetic. Only five designed populations support the uncertainty intervals. The candidate misses the five-percentage-point target and does not establish superiority over simple history-weighted sharing. Numerical tie-breaking undermines the original point-versus-distribution comparison. The revised numerical variants need validation-only retuning and untouched test populations before a new confirmatory superiority claim. The full model omits queues, battery taper, discrete pilots, network voltages, thermal dynamics and behavioral response. These are disclosed limitations, not completed experiments.

## AI disclosure placement

[IEEE's submission policy](https://conferences.ieeeauthorcenter.ieee.org/author-ethics/guidelines-and-policies/submission-policies/), checked 21 September 2026, requires AI-generated content to be disclosed in acknowledgments with the system, affected sections and extent of assistance. The named copy now includes this disclosure. The anonymous copy retains the same non-identifying text under **AI Assistance Disclosure**, with no acknowledgment heading or funding information, because CCWC instructs review authors to remove acknowledgments.

**Exact placement in the anonymous version remains an instruction conflict for the human submitter to resolve against conference guidance.** A separate heading preserves disclosure and anonymity but is not a verified exception to IEEE's specified location. No organizer confirmation has been obtained. See `ai_disclosure.md`. No Turnitin score or acceptance prediction is claimed.

## Turnitin AI-score check requested by the authors

Checked 21 September 2026. [CCWC](https://ieee-ccwc.org/submissions/) describes an acceptable Turnitin AI score as typically below 20%; this is conference-specific wording, not a guarantee of acceptance or a universal IEEE rule. [Turnitin's current documentation](https://guides.turnitin.com/hc/en-us/articles/22774058814093-Using-the-AI-Writing-Report) explains that nonzero results below 20% appear as `*%`, without an exact percentage or highlights, because false positives are more likely in that range. Its AI assessment can be wrong in either direction. An AI-writing indicator and a text-similarity score are separate measures; neither alone establishes research integrity.

The linked [IEEE RAS guidance](https://www.ieee-ras.org/publications/guidelines-for-generative-ai-usage/) requires disclosure and human responsibility and permits appropriate writing assistance. It does not state a general 20% limit. Actual substantial AI assistance must still be disclosed regardless of the detector output.

**This manuscript's Turnitin AI score is unverified.** No Turnitin report, authorized account or connected detector was available, and no paper was uploaded to any checking service. Do not describe the paper as under 20%, AI-free, plagiarism-free or detector-approved. An authorized Turnitin AI Writing Report for the final anonymous PDF is still needed to assess this criterion. Keep the report date and the exact PDF hash, and have the authors review any flagged passages and their supporting evidence. No wording change can guarantee a particular score.

## Human decisions before upload

- [ ] Review and approve the entire text, equations, code, citations and interpretation; independent domain review remains advisable.
- [ ] Confirm both authors' consent, contributions and corresponding-author designation. The supplied author order and affiliation are implemented; consent is not inferred.
- [ ] Select regular paper or WIP and confirm applicable page limits, tracks and submission fields in EDAS.
- [ ] Resolve AI-disclosure placement for anonymous review.
- [ ] Obtain and review the actual Turnitin AI Writing Report for the final anonymous PDF; no score has been verified.
- [ ] Reconfirm deadlines and final event instructions; obtain official copyright/PDF eXpress information only when provided.
- [ ] Upload only the intended anonymous PDF and approved anonymous supplementary files, if the event allows them. The named source bundle is an author working package, not a blind supplement.
- [ ] Choose a code license before any intended public redistribution and confirm applicable rights.

Submission, account creation, organizer contact and payment have not been authorized or performed. The user's request explicitly authorizes removing the manuscript from GitHub; that removal does not require another confirmation.
