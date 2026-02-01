# `PrimeFeat`
![Logo](docs/assets/logo-gh.png)

<!-- <p align="center">
  <img src="docs/assets/logo-gh.png" alt="primefeat Logo" width="400"/>
</p> -->

**Primordial Power Spectrum Feature Analysis for Cosmology**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![image](https://img.shields.io/pypi/v/primefeat.svg)](https://pypi.org/project/primefeat/)
[![image](https://img.shields.io/badge/arXiv-260X.0XXXX%20-green.svg)](https://arxiv.org/abs/260X.0XXXX)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docs](https://badgen.net/badge/icon/Documentation/yellow/?icon=https://cdn.jsdelivr.net/npm/simple-icons@v13/icons/gitbook.svg&label)](https://rcalderonb6.github.io/primefeat/)





[![image](https://github.com/rcalderonb6/primefeat/workflows/build/badge.svg)](https://github.com/rcalderonb6/primefeat/actions?query=workflow%3Abuild)
[![image](https://github.com/rcalderonb6/primefeat/workflows/docs/badge.svg)](https://github.com/rcalderonb6/primefeat/actions?query=workflow%3Adocs)

A Python package for detecting and characterizing features in the primordial power spectrum from MCMC cosmological parameter chains. Designed for precision cosmology research seeking evidence of physics beyond the standard inflationary paradigm.

## Features

🎯 **Power Spectrum Analysis**
- Fast computation of $\mathcal{P}_\zeta(k)$ posteriors from MCMC chains with intelligent caching
- Support for binned features: $\mathcal{P}_\zeta(k) = A_s \left(\frac{k}{k_*}\right)^{n_s-1}[1 + \delta(k)]$
- Automatic detection of amplitude parameter names across different samplers

🔬 **Statistical Analysis**
- Gaussian Process-based significance testing for feature detection
- Principal Component Analysis (PCA) for dimensionality reduction
- Bin correlation analysis and effective degrees of freedom estimation

⚙️ **Workflow Automation**
- YAML-based chain configuration for reproducible analyses
- Automatic chain loading with `get_chains(kmin)`
- Integration with GetDist for MCMC analysis

## Quick Start

```python
import primefeat as pf
import numpy as np

# Load chains from YAML config
chains = pf.get_chains(kmin=1e-4)

# Compute power spectrum posteriors
k = np.logspace(-4, 0, 100)
samples = {
    label: pf.compute_Pk_samples(
        k, chain, 
        nbins=20, 
        k_start=1e-4, 
        k_end=0.23,
        include_powerlaw=True
    )
    for label, chain in chains.items()
}

# Plot with publication style
colors = ['#2E86AB', '#A23B72', '#F18F01']
fig = pf.plot.posteriors_PPS(
    k, samples, colors=colors,
    mode="full",  # Full P(k) with A_s and n_s
    figsize=(8, 5)
)
```

## Installation

```bash
pip install primefeat
```

Or install from source:

```bash
git clone https://github.com/rcalderonb6/primefeat.git
cd primefeat
pip install -e .
```

## Configuration

Create a `chains.yaml` file to manage your MCMC chains:

```yaml
chains:
  1e-4:
    Planck:
      path: '/path/to/planck_chain'
    ACTDR6:
      path: '/path/to/actdr6_chain'
      add_h_parameter: true

default:
  skip: 0.3  # Burn-in fraction
```

Then load chains with:

```python
chains = pf.get_chains(1e-4)  # Loads all chains for kmin = 1e-4
```

## Citation

If you use PrimeFeat in your research, please cite:

```bibtex
@software{primefeat2025,
  author = {Calderon, Rodrigo},
  title = {PrimeFeat: Primordial Power Spectrum Feature Analysis},
  year = {2025},
  url = {https://github.com/rcalderonb6/primefeat}
}
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contact

Rodrigo Calderon - calderon.cosmology@gmail.com

---

*Looking for features in the primordial power spectrum that hint at new physics beyond vanilla inflation.*