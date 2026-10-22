# PEM water electrolysis: load-transfer prediction audit

JIN HANZHE · Independent Researcher, Chongqing, China  
GRC_LoadTransfer_01 · Local release candidate 1.0.0-rc.1 · 2026-10-22  
[中文](README.md) · [Reproduction](REPRODUCING.md) · [Validation](VALIDATION.md)

This retrospective case study asks whether high-load anode outlet hydrogen concentration predicts the subsequent low-load concentration in long-term PEM water electrolysis. It uses the fixed [Zenodo 19361280 dataset](https://doi.org/10.5281/zenodo.19361280), with 547 paired cycles across four main membrane electrode assemblies (MEAs), one per configuration.

The Pt/C frozen high-load affine model underpredicts all 70 late evaluation cycles. Its MAE is 0.050421 vol.% points. The primary time-only baseline gives 0.027502; adding high-load level and slope gives 0.025490. Using all 46 calibration cycles up to 550 h instead gives 0.004152 for time alone. Calibration history therefore materially affects the comparison.

With one low-load label revealed every 10 eligible cycles, the recent-eight-label time model gives 0.003396 MAE on 63 non-recalibration evaluation cycles, versus 0.005800 for the updated time + high-load level + slope model. Every prediction precedes the current label reveal. All original low-load holds remain in the experimental history: label masking does not demonstrate savings in measurement time, energy or cost.

## Reproduce

Use Python 3.12 in the package directory.

```text
python reproduce.py
python -m pip install -r requirements.txt
python reproduce.py --mode analysis
python reproduce.py --mode full --download
```

The default audit uses only the standard library. It verifies checksums and recalculates saved scores; it does not refit models. Analysis mode refits from bundled processed data, regenerates six PNG/SVG figures, and runs five causal-order tests. Full mode downloads and validates the 199,357,168-byte raw archive, rebuilds all derived tables, and separately checks 32 raw GC tails. Use `--raw-archive "path/to/archive.zip"` instead of `--download` for offline full reconstruction. Outputs always go to a fresh directory. See [detailed instructions](REPRODUCING.md).

## Boundaries

Cycles are repeated observations within a trajectory, not independent MEAs. Configuration and batch are confounded. The study is exploratory and retrospective, with no preregistration, prospective intervention or external-MEA confirmation. The moving-block intervals describe the observed trajectory only. Exponential fits do not identify a unique transport or recombination mechanism.

The original research stage had not obtained the complete journal supplementary information as of 2026-10-12. This package does not establish the instrument's long-term calibration error, detection limits or drift, and does not claim the original authors omitted them. It is not a validation of operational safety control or an independent replacement of low-load measurements.

## Attribution and licensing

Author/contact: JIN HANZHE, jinhanzhe09@gmail.com. OpenAI Codex assisted source checking, analysis, drafting and preparation; it is not an author. Completed human scientific verification and independent-team replication are not claimed. See [AUTHORSHIP.md](AUTHORSHIP.md).

Original software: MIT. Project documentation, figures and derived tables: CC BY 4.0, subject to retained upstream attribution. The experimental data are by Steffen Brundiers and the associated study authors, not by the reanalysis author. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), [LICENSING.md](LICENSING.md) and [CITATION.cff](CITATION.cff).

Please cite this reanalysis, the [fixed dataset](https://doi.org/10.5281/zenodo.19361280), and the [associated paper](https://doi.org/10.1039/D6EY00106H). This local candidate is not yet published and has no public repository URL or project DOI.

