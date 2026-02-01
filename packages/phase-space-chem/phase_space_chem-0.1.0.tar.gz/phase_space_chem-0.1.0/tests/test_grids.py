import pytest
import numpy as np
from phase_space_chem import grids

def test_generate_position_grids_shapes(standard_grids):
    """
    Verifies that position grids have the correct number of points.
    """
    R_grid = grids.generate_position_grid(
        -standard_grids['R_lim'], 
        standard_grids['R_lim'], 
        standard_grids['nR']
    )
    assert R_grid.shape == (standard_grids['nR'],)

def test_generate_position_grids_bounds(standard_grids):
    """
    Verifies that the generated grids adhere to the specified extents.
    """
    lim = standard_grids['R_lim']
    R_grid = grids.generate_position_grid(-lim, lim, standard_grids['nR'])
    
    assert np.isclose(R_grid.min(), -lim)
    assert np.isclose(R_grid.max(), lim)
    # Check if grid is linearly spaced
    diffs = np.diff(R_grid)
    assert np.allclose(diffs, diffs[0])

def test_generate_momentum_grid_conjugacy(standard_grids):
    """
    Verifies that momentum grid satisfies Nyquist sampling relative to R.
    Ref: PDF Section III.A (P grid definition).
    """
    lim = standard_grids['R_lim']
    N = standard_grids['nP']
    
    # Generate R to get dR
    R_grid = np.linspace(-lim, lim, N)
    dR = R_grid[1] - R_grid[0]
    
    P_grid = grids.generate_momentum_grid(dR, N)
    
    # Fourier conjugate bounds are typically [-pi/dR, pi/dR]
    expected_bound = np.pi / dR
    
    assert len(P_grid) == N
    assert np.abs(P_grid.max()) <= expected_bound + 1e-9
    # Ensure 0 is in the grid (critical for symmetry checks)
    assert np.any(np.isclose(P_grid, 0.0))