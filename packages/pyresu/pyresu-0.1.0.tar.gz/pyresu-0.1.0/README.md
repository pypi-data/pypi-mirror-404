# pyresu: Rectified Spectral Units

![](https://img.shields.io/badge/SciPy-654FF0?logo=SciPy&logoColor=white)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff)](#)
[![NumPy](https://img.shields.io/badge/NumPy-4DABCF?logo=numpy&logoColor=fff)](#)
[![Pytest](https://img.shields.io/badge/Pytest-fff?logo=pytest&logoColor=000)](#)
[![PyPI](https://img.shields.io/badge/PyPI-3775A9?logo=pypi&logoColor=fff)](#)
![License](https://img.shields.io/github/license/kuslavicek/pyresu)
![Version](https://img.shields.io/github/v/release/kuslavicek/pyresu)
![Maintained](https://img.shields.io/badge/Maintained%3F-yes-green.svg)
[![zread](https://img.shields.io/badge/Ask_Zread-_.svg?style=flat&color=00b0aa&labelColor=000000&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuOTYxNTYgMS42MDAxSDIuMjQxNTZDMS44ODgxIDEuNjAwMSAxLjYwMTU2IDEuODg2NjQgMS42MDE1NiAyLjI0MDFWNC45NjAxQzEuNjAxNTYgNS4zMTM1NiAxLjg4ODEgNS42MDAxIDIuMjQxNTYgNS42MDAxSDQuOTYxNTZDNS4zMTUwMiA1LjYwMDEgNS42MDE1NiA1LjMxMzU2IDUuNjAxNTYgNC45NjAxVjIuMjQwMUM1LjYwMTU2IDEuODg2NjQgNS4zMTUwMiAxLjYwMDEgNC45NjE1NiAxLjYwMDFaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00Ljk2MTU2IDEwLjM5OTlIMi4yNDE1NkMxLjg4ODEgMTAuMzk5OSAxLjYwMTU2IDEwLjY4NjQgMS42MDE1NiAxMS4wMzk5VjEzLjc1OTlDMS42MDE1NiAxNC4xMTM0IDEuODg4MSAxNC4zOTk5IDIuMjQxNTYgMTQuMzk5OUg0Ljk2MTU2QzUuMzE1MDIgMTQuMzk5OSA1LjYwMTU2IDE0LjExMzQgNS42MDE1NiAxMy43NTk5VjExLjAzOTlDNS42MDE1NiAxMC42ODY0IDUuMzE1MDIgMTAuMzk5OSA0Ljk2MTU2IDEwLjM5OTlaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik0xMy43NTg0IDEuNjAwMUgxMS4wMzg0QzEwLjY4NSAxLjYwMDEgMTAuMzk4NCAxLjg4NjY0IDEwLjM5ODQgMi4yNDAxVjQuOTYwMUMxMC4zOTg0IDUuMzEzNTYgMTAuNjg1IDUuNjAwMSAxMS4wMzg0IDUuNjAwMUgxMy43NTg0QzE0LjExMTkgNS42MDAxIDE0LjM5ODQgNS4zMTM1NiAxNC4zOTg0IDQuOTYwMVYyLjI0MDFDMTQuMzk4NCAxLjg4NjY0IDE0LjExMTkgMS42MDAxIDEzLjc1ODQgMS42MDAxWiIgZmlsbD0iI2ZmZiIvPgo8cGF0aCBkPSJNNCAxMkwxMiA0TDQgMTJaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00IDEyTDEyIDQiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K&logoColor=ffffff)](https://zread.ai/kuslavicek/pyresu)


`pyresu` is a Python package implementing **Rectified Spectral Units (ReSU)**, a biologically inspired neural building block based on the research by Qin et al. (2025). Unlike traditional deep learning that relies on backpropagation, ReSUs learn temporal features through spectral decomposition (CCA) and rectification.

## Features

- **Backprop-Free Training**: Implements a layer-wise, feed-forward training regime using analytical solutions.
- **Spectral Learning**: Uses Canonical Correlation Analysis (CCA) to align past and future temporal windows.
- **Biologically Inspired**: Mimics self-supervised learning in biological circuits.
- **Temporal Lag Management**: Built-in utilities for Hankel matrix construction and lag vector handling.
- **Interpretability**: Learnable filters (Canonical Directions) are directly interpretable as temporal features.

## Mathematical Mapping

| Concept | Symbol | Implementation |
| :--- | :--- | :--- |
| **Past/Future Lags** | $p_t, f_t$ | `construct_lag_vectors` |
| **Covariances** | $C_{pp}, C_{ff}, C_{fp}$ | `compute_covariance_matrices` |
| **Spectral Solution** | $\Psi, \sigma_i$ | `perform_truncated_cca` |
| **ReSU Output** | $z_{t,i}^+, z_{t,i}^-$ | `ReSUCell.forward` (ON/OFF) |
| **Mutual Info** | $I_r$ | `calculate_mutual_information` |

## Installation

Install the package in editable mode for development:

```bash
git clone https://github.com/username/pyresu.git
cd pyresu
pip install -e .
```

For development dependencies (tests, linting):

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
import numpy as np
from pyresu.preprocessing import construct_lag_vectors, center_lag_vectors
from pyresu.models import ReSUCell

# 1. Prepare some time-series data
data = np.random.randn(1000, 1)

# 2. Create past and future lag vectors
# memory=10 (past), horizon=5 (future)
past, future = construct_lag_vectors(data, memory=10, horizon=5)
past_c, future_c = center_lag_vectors(past, future)

# 3. Initialize and fit the ReSU Cell
# rank=3 (number of neurons)
cell = ReSUCell(rank=3)
cell.fit(past_c, future_c)

# 4. Forward pass
on_output, off_output = cell.forward(past_c)

print(f"ON shape: {on_output.shape}")  # (N, 3)
print(f"OFF shape: {off_output.shape}") # (N, 3)
```

## Project Structure

- `src/pyresu/`: Main implementation code.
  - `core.py`: CCA and spectral solvers.
  - `models.py`: ReSUCell implementation.
  - `preprocessing.py`: Lag vector and whitening utilities.
  - `simulation.py`: Synthetic data generators (OU processes, GP).
- `tests/`: Comprehensive test suite using `pytest` and `hypothesis`.

## Testing

Run the tests using `pytest`:

```bash
pytest
```

## References

This project incorporates research from the following paper:

- **A Network of Biologically Inspired Rectified Spectral Units (ReSUs) Learns Hierarchical Features Without Error Backpropagation**
  Shanshan Qin, Joshua L. Pughe-Sanford, Alexander Genkin, Pembe Gizem Ozdil, Philip Greengard, Anirvan M. Sengupta, Dmitri B. Chklovskii
  *arXiv:2512.23146*


