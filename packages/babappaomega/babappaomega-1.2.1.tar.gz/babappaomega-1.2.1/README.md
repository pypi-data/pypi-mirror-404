# BABAPPAΩ

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18195868.svg)](https://doi.org/10.5281/zenodo.18195868)
[![DOI](https://figshare.com/badge/doi/10.6084/m9.figshare.31199098.svg)](https://doi.org/10.6084/m9.figshare.31199098)

BABAPPAΩ is a likelihood-free neural inference framework for diagnosing the identifiability of episodic selection under branch–site evolution. Rather than performing hypothesis tests or estimating substitution parameters, BABAPPAΩ reframes branch–site analysis as the measurement of latent episodic selection burden supported by finite codon alignments.

The framework combines a forward-time mutation–selection simulator grounded in population-genetic theory with a frozen, amortized neural inference model trained against exact generative ground truth. Its purpose is diagnostic: to assess when episodic selection is statistically measurable, at what scale, and under which evolutionary regimes.

BABAPPAΩ is not a replacement for likelihood-based branch–site tests. Instead, it provides a principled way to study the limits of identifiability in branch–site evolution under biologically realistic complexity.

---

## Key Features

• Likelihood-free branch–site inference via amortized neural models  
• Estimation of latent episodic selection burden, not hypothesis testing  
• Forward-time mutation–selection simulation with exact ground truth  
• Robust to recombination, epistasis, transient fitness shifts, and alignment noise  
• GPU-accelerated inference with automatic CPU fallback  
• Deterministic, fully reproducible execution  
• Clean command-line interface for exploratory and large-scale scans  
• Strict separation between inference software and frozen model artifacts  

---

## Installation

Install BABAPPAΩ directly from PyPI:

    pip install babappaomega

Python ≥ 3.9 is required.

---

## Basic Usage

    babappaomega --alignment alignment.fasta --tree tree.nwk --out results.json

Each run performs a branch-conditioned exploratory scan, treating each branch in turn as foreground. In addition to machine-readable output, BABAPPAΩ automatically generates a human-readable interpretation report (results.txt).

---

## Output

BABAPPAΩ produces two complementary outputs.

Machine-readable JSON:
• Site-level episodic deviation (burden) scores  
• Branch-level deviation from background evolutionary patterns  
• Stable metadata describing software version, model hash, and runtime context  

Human-readable interpretation report:
• Ranked branches showing strongest deviation from background  
• Sites exhibiting elevated episodic burden  
• Conservative biological interpretation notes  
• Explicit warnings against over-interpretation  

---

## Interpreting Results

BABAPPAΩ does not report likelihood ratios, dN/dS estimates, p-values, or binary calls of positive selection. Scores are relative, not absolute. High burden indicates lineage-specific deviation, not guaranteed adaptation. Signals are often diffuse rather than sharply localized. Uninformative output under neutrality reflects correct calibration.

Episodic selection is frequently identifiable only at aggregate (gene-level) scales, long before it becomes localizable to individual sites. BABAPPAΩ is explicitly designed to expose this scale dependence.

---

## Model Weights and Reproducibility

BABAPPAΩ uses a single frozen reference neural model archived on Zenodo (https://doi.org/10.5281/zenodo.18195868). Artifact: babappaomega.pt.

The trained model is not bundled with the Python package. On first execution the frozen model is downloaded automatically from Zenodo, the SHA-256 checksum is verified, the artifact is cached locally, and subsequent runs reuse the cached model. Retraining or fine-tuning is intentionally not supported.

---

## Training Code and Simulation Artifacts

All training scripts, simulator code, and epoch-level artifacts used to train BABAPPAΩ are archived separately on figshare (https://doi.org/10.6084/m9.figshare.31199098). These materials are provided for transparency and auditability, not for routine end-user retraining.

---

## Performance

Inference is GPU-accelerated when available and automatically falls back to CPU execution otherwise. The software is suitable for high-throughput exploratory scans across genes, branches, and datasets on commodity hardware.

---

## License

MIT License

---

## Development Status

The inference engine, command-line interface, model freezing protocol, and distribution pipeline are finalized and stable. Ongoing work focuses on expanded benchmarking against classical likelihood-based methods, additional documentation and worked examples, and large-scale empirical applications.

---

## Citation

Until the accompanying manuscript is published, please cite:

Sinha, K. BABAPPAΩ: Diagnosing the identifiability of episodic selection under branch–site evolution using likelihood-free neural inference. Zenodo. https://doi.org/10.5281/zenodo.18195868

Training and simulation artifacts: figshare. https://doi.org/10.6084/m9.figshare.31199098
