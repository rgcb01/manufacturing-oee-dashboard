# Technical Paper

## OEE-Based Manufacturing Loss Diagnostics: A Reproducible Synthetic Case Study

Author: Romulo Colorado

DOI: [10.5281/zenodo.21879822](https://doi.org/10.5281/zenodo.21879822)

Zenodo record: [https://zenodo.org/records/21879822](https://zenodo.org/records/21879822)

This paper is an independently published technical engineering case study hosted on Zenodo. It documents the methodology, synthetic experimental design, OEE aggregation logic, controlled ground-truth patterns, diagnostic workflow, results, limitations and reproducibility scope for this repository.

The canonical published version is hosted on Zenodo. The PDF in this folder is included as repository evidence for the software artifact associated with release `v1.0.0`.

## Relationship to the Repository

The paper describes the engineering analysis and controlled synthetic experiment. The repository provides the reproducible implementation through:

- Synthetic data generation
- KPI and OEE calculation modules
- SQLite data layer
- Pareto and loss-diagnostic analysis
- Deterministic engineering insights
- Streamlit dashboard
- Automated tests

## Reproducibility Parameters

- Experiment duration: 30 days
- Production lines: 3
- Shifts: 3
- Products: 4
- Pseudorandom seed: `42`

The software and paper use synthetic data and demonstrate reproducibility and engineering loss localization rather than industrial validation.
