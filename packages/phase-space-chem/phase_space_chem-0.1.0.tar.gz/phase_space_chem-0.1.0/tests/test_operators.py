import pytest
import numpy as np
from phase_space_chem import operators

def test_compute_standard_gamma_shape(standard_grids):
    """
    Verifies output shape is [N_r, N_r].
    Eq 23: Gamma = p / i*hbar
    """
    r_grid = np.linspace(-22, 22, standard_grids['nr'])
    gamma = operators.compute_standard_gamma(r_grid)
    
    assert gamma.shape == (standard_grids['nr'], standard_grids['nr'])
    
    # Gamma should be anti-hermitian (p is hermitian, divided by i)
    # Or Hermitian if defined differently, but based on Eq 23:
    # Gamma^dag = (p / i)^dag = p^dag / (-i) = p / -i = -Gamma.
    # The operator appearing in Hamiltonian is (P - i*hbar*Gamma).
    assert np.allclose(gamma, -gamma.conj().T)

def test_compute_partition_of_unity_summation(standard_grids):
    """
    CRITICAL: Sum_A theta_A(r) == 1.0.
    Ref: Eq 24, 25.
    """
    r_grid = np.linspace(-22, 22, standard_grids['nr'])
    centers = [-10.0, 0.0, 10.0] # 3 ions
    
    # Should return a list or array of shape [n_centers, n_r]
    partitions = operators.compute_partition_of_unity(r_grid, centers, sigma=4.0)
    
    summed_partitions = np.sum(partitions, axis=0)
    assert np.allclose(summed_partitions, 1.0)

def test_compute_partitioned_gamma_dimensions(standard_grids):
    """
    Verifies dimensions for Eq 24 type Gamma.
    """
    r_grid = np.linspace(-22, 22, standard_grids['nr'])
    centers = [-10.0, 0.0, 10.0]
    
    gamma_multi = operators.compute_partitioned_gamma(r_grid, centers)
    assert gamma_multi.shape == (standard_grids['nr'], standard_grids['nr'])