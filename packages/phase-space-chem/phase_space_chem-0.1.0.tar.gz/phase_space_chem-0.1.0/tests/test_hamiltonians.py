import pytest
import numpy as np
from phase_space_chem import hamiltonians

def test_construct_total_hamiltonian_exact_hermiticity(standard_grids, shin_metiu_params):
    """
    Verifies the exact Hamiltonian (Eq 21) is Hermitian in position basis.
    Dimension: N_R*N_r x N_R*N_r.
    """
    # Use very small grids for this expensive test
    r_grid = np.linspace(-5, 5, 10)
    R_grid = np.linspace(-2, 2, 10)
    
    H_total = hamiltonians.construct_exact_hamiltonian(r_grid, R_grid, **shin_metiu_params)
    
    assert np.allclose(H_total, H_total.conj().T)

def test_construct_ps_electronic_hamiltonian_shape(standard_grids, shin_metiu_params):
    """
    Verifies Phase Space Hamiltonian shape.
    Ref: Eq 15. H_PS(R, P) is an electronic operator [N_r, N_r].
    Tensor shape: [N_P, N_R, N_r, N_r].
    """
    r_grid = np.linspace(-22, 22, 10)
    R_grid = np.linspace(-9, 9, 5)
    P_grid = np.linspace(-1, 1, 5)
    
    H_ps = hamiltonians.construct_ps_hamiltonian(
        r_grid, R_grid, P_grid, **shin_metiu_params
    )
    
    assert H_ps.shape == (5, 5, 10, 10)

def test_ps_electronic_hamiltonian_hermiticity_at_point(standard_grids, shin_metiu_params):
    """
    Selects a random point (R_i, P_j) and verifies hermiticity.
    Eq 15: H_PS = (P - i hbar Gamma)^2 / 2M + V
    Since Gamma is anti-hermitian, i*Gamma is Hermitian. 
    Thus (P - i*Gamma) is Hermitian, and its square is Hermitian.
    """
    r_grid = np.linspace(-22, 22, 20)
    R_grid = np.array([1.5])
    P_grid = np.array([0.5])
    
    H_ps = hamiltonians.construct_ps_hamiltonian(
        r_grid, R_grid, P_grid, **shin_metiu_params
    )
    
    H_at_point = H_ps[0, 0, :, :]
    assert np.allclose(H_at_point, H_at_point.conj().T)