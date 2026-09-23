# Service History and Forecast Value in EV Charging

Research artifact for **Service History and Forecast Value in EV Charging: A Real-Session Replay Audit**.

[Results](docs/results_report.md) · [Protocol](docs/method_and_protocol.md) · [Data provenance](docs/data_acquisition.md) · [ICCA checklist](docs/submission_checklist.md)

The current study replays **recorded JPL ACN-Data sessions**, with chronological fitting, calibration, validation and two later test periods. It uses **16,529 assigned sessions**, including **4,206 Q3 and 4,146 Q4 test sessions**. Arrivals, departures, identities and requests are recorded; alternative-controller energy delivery, shortfalls and costs are simulated under common assumptions. This is not a live charging intervention.

## Main finding

The candidate does **not** beat validation-selected max–min sharing. Q3 worst-decile user shortfall is **58.30% versus 52.35%**, a difference of **+5.95 percentage points [2.69,10.85]**. Positive differences mean worse service. Its energy and unit-cost ratios are **98.83%** and **98.95%**, meeting those point-estimate guardrails but failing the five-point fairness target. The later period supports the same direction; complete results and ablations are in the linked report.

Intervals are conditional paired five-observed-day outcome-block resampling intervals. They hold fitted settings and realized histories fixed and do not represent independent-site or dynamic-replay uncertainty. Two test periods at one site are not independent replications.

All eleven policies use the same eligible data. Every MPC method uses consistent two-stage tie-breaking, with June-only tuning locked before testing. There are **21 validation and 31 test/sensitivity runs**, **27 passing automated tests**, and **3,292,992 independently audited applied-action rows**. A fresh primary-pair replay matches saved session results to numerical precision on the same machine/environment. No independent human replication is claimed.

## Files and privacy

| Path | Contents |
|---|---|
| `src/evfair/` | Frozen core session processing, forecasting, control and replay |
| `config/real_data_protocol.json` | Current real-session design, exclusions and comparison rules |
| `results/real_data/` | Aggregate outcomes, provenance, protocol/selection locks and verification |
| `scripts/*real*.py` | Acquisition, study runner, independent audit, fresh replay and portable verification |
| `figures/real_*.pdf` | Current real-session plots |
| `docs/` | Current methods, findings, claims and research notes |
| `docs/historical_synthetic/` | Earlier documents preserved as historical evidence |
| `notebooks/audit.ipynb` | Current aggregate inspection, followed by labeled historical cells |
| `manuscript/`, `final/` | Local author paper and submission package; excluded from Git publication |
| `data/` | Private working copies of raw/normalized records, model and individual traces; not packaged |

The earlier synthetic study remains unchanged in its original `results/` and `results/second_pass/` paths. It is separate evidence and is not pooled with the real-session results. Its small discovery sample does not describe the coverage of the successful full JPL acquisition.

## Environment

The real-session extension ran in Python 3.13 with the pinned scientific packages. From the project root:

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-review.lock
export PYTHONPATH="$PWD/src:$PWD"
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MPLCONFIGDIR="${TMPDIR:-/tmp}/evfair-mpl"
```

The pinned review environment includes the research dependencies and PyMuPDF used by local author tools. Public research verification does not require LaTeX or manuscript files. No public code license has been selected.

## Check a public checkout

```sh
python -m unittest discover -s tests -v
python scripts/verify_public_real_artifact.py
```

The portable public-artifact check verifies source locks and aggregate arithmetic without private records. The full action audit and fresh replay require the privately held raw data, normalized splits and traces. They cannot run against an aggregates-only package until data are acquired and the experiment is reproduced. The replay check runs the primary pair again in the same environment; it does not refit or create independent evidence. Manuscript prose, its reporting template, private editorial reports and submission archives stay local. The public checkout supports research verification and reproduction; it does not reconstruct the paper. See [AI assistance disclosure](docs/ai_disclosure.md).

## Reproduce from official records

Use a separate working copy. Preserve supplied `results/real_data/` as reference outputs and start with a fresh directory of that name and an empty `data/processed/real_study/`. Do not delete or rewrite the reference protocol lock. The original lock has a local absolute runner path; a fresh run makes a new directory-specific lock before evaluating controllers.

```sh
python scripts/acquire_real_data.py --workers 3
python scripts/real_data_study.py audit
python scripts/real_data_study.py prepare
python scripts/real_data_study.py validate --workers 3
python scripts/real_data_study.py evaluate --workers 3
python scripts/real_data_study.py summarize
python scripts/verify_real_data.py
python scripts/reproduce_real_pair.py
```

Acquisition needs network access to the public official export; no account is used. Compare raw checksums against the reference acquisition record before claiming exact data reproduction. Fitting, selection, histories and locked source are checked throughout. Full runtime depends on hardware and solver behavior. Private per-session records remain excluded from distribution; aggregate checksums establish correspondence without publishing identities.

The old synthetic workflow is preserved in [the historical README](docs/historical_synthetic/README.md). Its original `python -m evfair.cli report` regenerates historical tables and must not be used as the current manuscript reporting command.

## Publication boundary

This repository publishes research code, protocols, aggregate results, plots and documentation. The manuscript PDF, LaTeX source, extracted paper text, private Grammarly reports, manuscript-writing template and author source archive are excluded. Raw real-session data and individual action/history records also remain local. Publishing this research artifact is not a conference submission or a claim of acceptance. Author approval and conference-specific screening/certification remain separate steps.
