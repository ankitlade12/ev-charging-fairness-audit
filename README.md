# Service History and Forecast Value in Fair EV Charging

Research code and supplementary material for **Service History and Forecast Value in Fair EV Charging: A Reproducible Audit**.

[Paper (PDF)](manuscript/main.pdf) · [LaTeX source](manuscript/main.tex) · [Methods](docs/method_and_protocol.md) · [Results](docs/results_report.md) · [Diagnostic analyses](docs/diagnostics.md)

## Overview

When electric vehicles share limited charging capacity, some users may leave repeatedly undercharged. This study asks whether prioritizing past service shortfalls improves repeated-user outcomes, and whether departure distributions provide a scheduling advantage over point forecasts.

We evaluate eleven charging policies across five synthetic populations and four capacity levels. Forecast fitting, calibration, controller selection, and evaluation use chronological splits. The primary comparator and controller settings were fixed before test evaluation. Separate numerical and forecasting diagnostics examine the sensitivity of the findings.

All controller results are **synthetic**. The accessible ACN discovery sample does not contain enough repeated sessions per user for an empirical fairness evaluation.

## Main findings

At the primary capacity setting, the history-plus-uncertainty controller has a mean worst-decile user shortfall of **16.27%**, compared with **18.83%** for the validation-selected proportional-fair controller.

| Comparison | Estimate | 95% interval |
|---|---:|---:|
| Tail shortfall: history controller minus proportional-fair MPC | −2.56 percentage points | [−3.73, −1.38] |
| Delivered energy relative to proportional-fair MPC | 100.20% | [100.06%, 100.35%] |
| Unit cost relative to proportional-fair MPC | 100.17% | [100.07%, 100.26%] |
| Tail shortfall: history controller minus simple history-weighted sharing | +0.54 percentage points | [−1.81, 2.88] |

Intervals use paired results across five generated populations. The prespecified five-percentage-point improvement target is not met, and the results do not establish an advantage over simple history-weighted sharing.

In 25 exploratory runs with consistent numerical tie-breaking, point MPC's mean tail shortfall falls from 29.75% to 19.09%. Its comparison with uncertainty-only MPC becomes inconclusive. Better departure forecast scores therefore do not establish better service allocation. See the [diagnostic analyses](docs/diagnostics.md) and [claim-to-evidence map](docs/claim_evidence_map.md) for the supporting records.

## Repository structure

| Path | Contents |
|---|---|
| `manuscript/` | Current paper, LaTeX source, generated tables, and IEEEtran class |
| `src/evfair/` | Session processing, forecasts, controllers, simulation, and metrics |
| `config/` | Primary protocol and secondary-analysis specification |
| `results/` | Saved trajectories, summary tables, protocol locks, and verification records |
| `figures/` | Paper figures and supplementary plots |
| `scripts/` | Data acquisition, diagnostics, reporting, and verification |
| `tests/` | Information-timing, numerical, and physical-consistency checks |
| `docs/` | Methods, results, data provenance, related work, and author submission notes |
| `notebooks/audit.ipynb` | Interactive inspection of saved results |
| `data/` | Local acquisition records and processed discovery sample |

## Setup

The saved experiment was run on macOS with Python 3.14. The primary seed-11 comparison was reproduced in a separate Python 3.13 environment on the same machine. Python 3.13 is a suitable starting point for the pinned environment.

Run commands from the repository root:

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
export PYTHONPATH="$PWD/src"
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MPLCONFIGDIR="${TMPDIR:-/tmp}/evfair-mpl"
```

The synthetic experiments require no network access after dependencies are installed. A LaTeX installation providing `pdflatex` is needed to build the paper. PDF checks additionally require `python -m pip install -r requirements-review.lock`.

## Verify the saved results

```sh
python -m unittest discover -s tests -v
python scripts/verify_second_pass.py
python scripts/verify_artifact.py
```

These checks verify the locked source and protocol, saved outcomes, energy accounting, numerical feasibility, and exploratory diagnostics. They do not rerun the full experiment or establish external validity.

To rebuild and check the current paper:

```sh
python scripts/build_manuscript.py
python scripts/verify_pdf.py
python scripts/verify_artifact.py
```

## Reproduce the experiments

The commands below overwrite derived results. Use a separate working copy to retain the supplied reference outputs. Controller selection uses validation data; the later diagnostics reuse the inspected test populations and remain exploratory.

```sh
python -m evfair.cli validate
python -m evfair.cli evaluate --workers 3
python -m evfair.cli supplement --workers 2
python scripts/check_point_baseline.py
python scripts/check_point_tiebreak.py
python scripts/second_pass_diagnostics.py
python -m evfair.cli report
python scripts/finalize_secondary.py
python scripts/finalize_review.py
python scripts/report_second_pass.py
python scripts/make_information_figure.py
python scripts/reproduce_check.py
python scripts/build_manuscript.py
python scripts/verify_pdf.py
python scripts/verify_artifact.py
```

The primary study contains 220 runs; the supplementary study contains 55. Runtime depends on hardware and solver behavior. The source and analysis locks document the study sequence; they are local records, not an external preregistration. `verify_second_pass.py` also checks byte-for-byte preservation of the supplied primary outputs, including the original protocol timestamp and runtime diagnostics; use that historical check on the reference copy.

## Data and availability

The ACN discovery sample contains 26 records. The original adapter retained 12 sessions from eight users; a later correction to request-update ordering retains 14 sessions from ten users. Neither version contains a user with five eligible sessions. These records are used only to assess data coverage, and do not determine the simulation parameters.

Acquisition sources, exclusions, and commands are documented in [data acquisition](docs/data_acquisition.md). Real-session working files are excluded from review archives. The [related-work notes](docs/recent_literature_review.md) record the sources and access depth used in preparing the paper.

The manuscript is an unpublished research draft. Author information and submission decisions remain in the [submission checklist](docs/submission_checklist.md). No public license has been selected for the research code; the included IEEEtran class retains its own license notices.
