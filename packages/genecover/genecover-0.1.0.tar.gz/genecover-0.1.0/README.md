# GeneCover

[![PyPI-Server](https://img.shields.io/pypi/v/genecover.svg)](https://pypi.org/project/genecover/)
[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)

A combinatorial approach for **label-free marker gene selection** from scRNA-seq and spatial transcriptomics data, using gene-gene correlation and set cover.

This repository is a **Python packaging + PyPI-friendly** version of the original GeneCover pipeline, keeping the algorithm behavior as close as possible to the original implementation while supporting optional solver backends (uses lazy loading).

---

## Manuscript

Wang, A., Hicks, S., Geman, D., & Younes, L. (2025, April).  
*GeneCover: A Combinatorial Approach for Label-free Marker Gene Selection*.  
In International Conference on Research in Computational Molecular Biology (pp. 354–357). Cham: Springer Nature Switzerland.  
DOI: [10.1101/2024.10.30.621151](https://doi.org/10.1101/2024.10.30.621151)


```bibtex
@inproceedings{wang2025genecover,
  title={GeneCover: A Combinatorial Approach for Label-free Marker Gene Selection},
  author={Wang, An and Hicks, Stephanie and Geman, Donald and Younes, Laurent},
  booktitle={International Conference on Research in Computational Molecular Biology},
  pages={354--357},
  year={2025},
  organization={Springer}
}
```

Original resources:

- Original GitHub repo: https://github.com/ANWANGJHU/GeneCover  
- Original docs site: https://genecover.readthedocs.io/

---
This package exists to provide a lightweight, pip-installable interface to GeneCover without requiring users to clone the original repository or configure solvers unless needed.

## Features

- Compute gene–gene correlation matrices from scRNA-seq / spatial transcriptomics data:
  - Spearman correlation (default)
  - Pearson correlation
- Select marker genes via **minimal-weight set cover**, with multiple backends:
  - **Gurobi** (integer programming; requires license)
  - **SCIP** via PySCIPOpt (open-source solver)
  - **Greedy heuristic** (no solver dependencies; NumPy-only)
- Perform **iterative marker selection** (`Iterative_GeneCover`) to build gene panels in multiple rounds
- Behavior closely aligned with the original one-file GeneCover implementation

---

## Compatibility with the original GeneCover implementation

- The core GeneCover algorithm, thresholds, and optimization logic are preserved.
- `gene_gene_correlation`, `GeneCover`, and `Iterative_GeneCover` follow the same behavior and defaults as the original implementation.
- Differences from the original repository are limited to **packaging and dependency handling** (lazy imports, optional solver extras).
- Results should be directly comparable to those obtained using the original GeneCover code.

---

## Installation

### Install from PyPI
```bash
pip install genecover
```

This installs the core package and supports the Greedy backend (no external solver required).

### Optional solver backends

To use integer-programming solvers, install extras:
#### Gurobi backend (requires a valid Gurobi license)
```bash
pip install "genecover[gurobi]"
```

#### SCIP backend (via PySCIPOpt)
```bash
pip install "genecover[scip]"
```

#### Install all optional backends
```bash
pip install "genecover[all]"
```
---

## Usage and QuickStart
For full tutorials and usage examples, see the original GeneCover documentation. The function names should be the same, for instance:
```python
from genecover import gene_gene_correlation, GeneCover, Iterative_GeneCover
```
---

## Project Status

This package focuses on: a clean Python API (genecover), reproducibility with the original one-file pipeline, and solver backends as optional dependencies.
The interface may evolve as packaging/testing/docs are improved.

---

## Contributing

Bug reports, feature requests, and GitHub issues or pull requests are welcome.

Please submit issues and pull requests via the GitHub repository:
https://github.com/danielchen05/GeneCover

---

## Note

This project has been set up using PyScaffold 4.6.
For details and usage information on PyScaffold see https://pyscaffold.org/.