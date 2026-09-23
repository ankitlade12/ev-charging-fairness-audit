# Data acquisition and privacy notes

The [diagnostic analyses](diagnostics.md) describe the matched numerical comparisons, later forecast landmarks, and corrected request-update ordering. These exploratory analyses supplement the locked primary study.

The original research brief was the only intake document; it is not included in this repository. No existing assessment, pilot code, credentials or session export was supplied.

The live ACN web form was attempted for January 2019 and calendar year 2019. Each response was HTTP 200, 178 bytes and invalid JSON ending at the opening `_items` array. These files are retained locally as failed acquisition evidence and rejected by the parser. The exact acquisition date was 13 September 2026. No registration or contact occurred.

The coauthor's static README and session export were fetched from `https://raw.githubusercontent.com/tongxin-li/ACN-Data-Static/main/`. The README states the session export is empty. The downloaded export was two bytes. It is not research session evidence.

The ORNL discovery sample was downloaded from `https://openenergyhub.ornl.gov/api/explore/v2.1/catalog/datasets/acn-data/records?limit=100`, with metadata at the same path without `/records`. The API reported 26 total records and all 26 were retrieved. Its metadata calls this a discovery sample and assigns CC BY 4.0 with attribution to Caltech. `scripts/acquire_sample.py` regenerates the download and key-name transformation. No values are inferred or filled from historical delivered energy.

Raw pseudonymous records are local working material. The review archive omits real session rows, individual exclusion IDs, HTML downloads and failed exports. It contains aggregate audit counts and public source links. Synthetic session/user keys in experiment outputs represent generated people and are safe to inspect as synthetic records.

Future use of the full ACN dataset must verify its own terms, acquisition completeness, identity/request coverage, timestamp provenance and physical metadata. This sample's license and coverage do not establish those properties for another export. No demographic attributes are inferred.

## Reproduce the coverage audits

After completing the environment setup in the README, run from the repository root:

```sh
python scripts/acquire_sample.py
python -m evfair.cli validate-data --input data/raw/ornl_acn.json
python scripts/audit_revision_order.py
```

Acquisition requires network access. The two audit commands use the downloaded local sample. The original audit and the later ordering sensitivity are retained separately. Neither is required to run the synthetic experiments.
