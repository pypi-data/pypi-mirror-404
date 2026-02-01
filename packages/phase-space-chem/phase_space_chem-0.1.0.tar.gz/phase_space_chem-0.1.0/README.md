# PhaseSpaceChem
![](https://img.shields.io/badge/SciPy-654FF0?logo=SciPy&logoColor=white)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff)](#)
[![NumPy](https://img.shields.io/badge/NumPy-4DABCF?logo=numpy&logoColor=fff)](#)
[![Pytest](https://img.shields.io/badge/Pytest-fff?logo=pytest&logoColor=000)](#)
[![PyPI](https://img.shields.io/badge/PyPI-3775A9?logo=pypi&logoColor=fff)](#)
![License](https://img.shields.io/github/license/kuslavicek/phase_space_chem)
![Version](https://img.shields.io/github/v/release/kuslavicek/phase_space_chem)
![Maintained](https://img.shields.io/badge/Maintained%3F-yes-green.svg)
[![zread](https://img.shields.io/badge/Ask_Zread-_.svg?style=flat&color=00b0aa&labelColor=000000&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuOTYxNTYgMS42MDAxSDIuMjQxNTZDMS44ODgxIDEuNjAwMSAxLjYwMTU2IDEuODg2NjQgMS42MDE1NiAyLjI0MDFWNC45NjAxQzEuNjAxNTYgNS4zMTM1NiAxLjg4ODEgNS42MDAxIDIuMjQxNTYgNS42MDAxSDQuOTYxNTZDNS4zMTUwMiA1LjYwMDEgNS42MDE1NiA1LjMxMzU2IDUuNjAxNTYgNC45NjAxVjIuMjQwMUM1LjYwMTU2IDEuODg2NjQgNS4zMTUwMiAxLjYwMDEgNC45NjE1NiAxLjYwMDFaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00Ljk2MTU2IDEwLjM5OTlIMi4yNDE1NkMxLjg4ODEgMTAuMzk5OSAxLjYwMTU2IDEwLjY4NjQgMS42MDE1NiAxMS4wMzk5VjEzLjc1OTlDMS42MDE1NiAxNC4xMTM0IDEuODg4MSAxNC4zOTk5IDIuMjQxNTYgMTQuMzk5OUg0Ljk2MTU2QzUuMzE1MDIgMTQuMzk5OSA1LjYwMTU2IDE0LjExMzQgNS42MDE1NiAxMy43NTk5VjExLjAzOTlDNS42MDE1NiAxMC42ODY0IDUuMzE1MDIgMTAuMzk5OSA0Ljk2MTU2IDEwLjM5OTlaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik0xMy43NTg0IDEuNjAwMUgxMS4wMzg0QzEwLjY4NSAxLjYwMDEgMTAuMzk4NCAxLjg4NjY0IDEwLjM5ODQgMi4yNDAxVjQuOTYwMUMxMC4zOTg0IDUuMzEzNTYgMTAuNjg1IDUuNjAwMSAxMS4wMzg0IDUuNjAwMUgxMy43NTg0QzE0LjExMTkgNS42MDAxIDE0LjM5ODQgNS4zMTM1NiAxNC4zOTg0IDQuOTYwMVYyLjI0MDFDMTQuMzk4NCAxLjg4NjY0IDE0LjExMTkgMS42MDAxIDEzLjc1ODQgMS42MDAxWiIgZmlsbD0iI2ZmZiIvPgo8cGF0aCBkPSJNNCAxMkwxMiA0TDQgMTJaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00IDEyTDEyIDQiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K&logoColor=ffffff)](https://zread.ai/kuslavicek/phase_space_chem)


**Electron Transfer, Diabatic Couplings, and Vibronic Energy Gaps in a Phase Space Framework**

PhaseSpaceChem is a Python library designed to calculate electronic states and vibronic energy gaps using a novel Phase Space (PS) framework. By treating the electronic system as dependent on both the position ($R$) and momentum ($P$) of the nuclei, this method achieves significantly higher accuracy than standard Born-Oppenheimer or Born-Huang approximations, while naturally conserving momentum.

## Features

-   **Shin-Metiu Model Generator**: Flexible 1D 1-electron, 3-ion Hamiltonian matrix generation.
-   **Phase Space Hamiltonian**: Construction of $\hat{H}_{W,el}^{PS}(R, P)$ directly in phase space.
-   **Diabatization Engine**: Generalized Mulliken-Hush (GMH) diabatization optimized for phase space adiabatic states ($U(R, P)$).
-   **Inverse Weyl Transform**: Re-quantization of phase space operators back into Hilbert space.
-   **Momentum Conservation**: Inherently respects conservation laws often violated by truncated ad-hoc corrections.

## Installation

You can install `phase_space_chem` directly from source:

```bash
git clone https://github.com/username/phase_space_chem.git
cd phase_space_chem
pip install .
```

For development (editable install):

```bash
pip install -e .[dev]
```

## Usage

Here is a basic example of how to initialize the grids and compute a Shin-Metiu potential:

```python
import numpy as np
import matplotlib.pyplot as plt
from phase_space_chem import grids, potentials

# 1. Define Grid Parameters
n_r = 151  # Electronic points
n_R = 151  # Nuclear points
n_P = 151  # Momentum points

# 2. Generate Grids
R_grid, r_grid = grids.generate_position_grids(
    num_nuclear_points=n_R, 
    num_electronic_points=n_r
)
P_grid = grids.generate_momentum_grid(R_grid, n_P)

# 3. Compute Potential
# Parameters: Fixed Separation=20.0, Mobile Screening=5.0, Fixed Screening=4.0
V_rR = potentials.compute_shin_metiu_potential(
    electronic_position_grid=r_grid, 
    nuclear_position_grid=R_grid, 
    fixed_ion_separation=20.0, 
    mobile_ion_screening=5.0, 
    fixed_ion_screening=4.0
)

print(f"Potential Shape: {V_rR.shape}")
```



## References

This project incorporates research from the following paper:

- **Electron Transfer, Diabatic Couplings and Vibronic Energy Gaps in a Phase Space Framework**
  Zain Zaidi, Xuezhi Bian, Joseph E. Subotnik
  *arXiv:2601.16209*
