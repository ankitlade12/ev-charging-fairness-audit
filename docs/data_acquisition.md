# Real-session data acquisition and provenance

The active study uses **official Caltech ACN-Data JPL records for 2019**, downloaded on 22 September 2026 local time. The recorded data contain arrivals, disconnections, pseudonymous users, station identifiers and timestamped requested-energy/departure revisions. Historical delivered energy is not substituted for requested energy. Alternative-controller outcomes are simulated retrospective replays.

## Source and completeness

The [official dataset page](https://ev.caltech.edu/dataset) supplies a public download form. Annual and monthly exports truncated; 53 small weekly windows from 2019-01-01 through 2020-01-02 UTC succeeded. The extra boundary day covers the final California local day. Each window passed JSON parsing, a site check, a comparison against the official `_num_sessions` endpoint and a SHA-256 check. Identical duplicates are removed; conflicting duplicate contents fail acquisition. This establishes completeness relative to the queried export, not completeness of every charging event ever occurring at the site.

- Acquisition: `scripts/acquire_real_data.py`.
- Per-window provenance, counts and checksums: `results/real_data/acquisition.json`.
- Combined raw records: **17,414**.
- Combined SHA-256: `bdddc9cad2bf9738908ea6180f89e9b813e535a382adeaf0e9175caaeb513825`.
- Local raw file: `data/raw/real_study/jpl_2019_complete.json`.
- Raw data, normalized sessions, fitted personal summaries and individual outcomes remain under ignored `data/` paths. The source package redistributes only code and aggregates; no standalone data license is inferred.

The original dataset paper is Lee, Li and Low, “ACN-Data: Analysis and Applications of an Open EV Charging Dataset,” ACM e-Energy 2019, DOI [10.1145/3307772.3328313](https://doi.org/10.1145/3307772.3328313). Cite the dataset creators when using their records.

## Normalization and coverage

Two records with invalid revisions are quarantined. The original conservative adapter then excludes 564 missing identities, 227 sessions crossing local midnight, and 91 sessions without a full service slot. There are no retained same-port overlaps. Of 16,530 eligible records, one lies outside the study periods; **16,529 are assigned**.

Exact revision timestamps determine ordering before conservative 15-minute rounding: connection and request availability round up; departure rounds down. The latest same-bin revision supersedes earlier available updates (2,529 superseded updates). Rounding removes 4,108.39 connection-hours across eligible records. Local timezone is America/Los_Angeles. Split boundaries are exclusive on the right; spanning sessions are not split between periods.

| 2019 local period | Purpose | Sessions | Users | Users with ≥5 sessions |
|---|---|---:|---:|---:|
| Jan 1–Apr 30 | Training | 5,324 | 243 | 180 |
| May 1–May 31 | Calibration | 1,530 | 207 | 116 |
| Jun 1–Jun 30 | Validation | 1,323 | 203 | 105 |
| Jul 1–Sep 30 | Primary test | 4,206 | 260 | 176 |
| Oct 1–Dec 31 | Secondary test | 4,146 | 277 | 194 |

Identities may recur across periods; user counts must not be summed as unique users. There are 367 eligible identities in the full acquisition. The tests include 126 and 145 sessions with energy revisions, and 201 and 203 with late first requests. Excluded records supply no background charging load. Selection and conservative rounding limit representativeness.

## What is modeled

All eligible sessions assume 6.6-kW continuous charging and 0.92 efficiency. Training peak connected nominal power is 343.2 kW, making the primary cap 120.12 kW. These are model quantities, not observed feeder headroom or a verified physical station inventory. The designed tariff is $0.12/grid-kWh, or $0.30 during UTC 21:00–01:00. Arrivals, departure behavior and requests stay fixed when simulated service changes. The model omits taper, discrete pilot constraints, electrical-network limits, excluded-session load and behavior feedback.

## Historical acquisition attempts

The previous ORNL discovery sample retained only 14 sessions from ten users and no repeated-user endpoint. That was a limitation of that sample, not the full ACN dataset. The successful official weekly JPL acquisition supersedes the earlier statement that empirical evaluation was unavailable. Caltech and Office 1 investigation downloads and an unofficial JPL mirror are **not inputs to this study**. Historical notes remain in `docs/historical_synthetic/`.

## Reproduction

Use a separate working copy with a fresh `results/real_data/` and `data/processed/real_study/`; preserve supplied reference results. Run the commands in the repository README. Official exports can change over time; compare source checksums before claiming exact reproduction. The local original lock records an absolute runner filename, so it cannot be reused verbatim from another directory. New runs create their own local lock before evaluation; the original reference lock remains evidence of the original execution sequence.
