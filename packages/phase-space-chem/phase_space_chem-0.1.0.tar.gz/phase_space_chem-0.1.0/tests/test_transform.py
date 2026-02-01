import pytest
import numpy as np
from hypothesis import given, strategies as st
from hypothesis.extra.numpy import arrays
from phase_space_chem import transform

def test_inverse_weyl_transform_output_shape():
    """
    Verifies the requantized Hamiltonian has shape [K*N_R, K*N_R].
    Ref: Eq 20.
    """
    nP = 20
    nR = 20
    K = 2 # 2 states
    
    # Input: Phase space diabatic H of shape [nP, nR, K, K]
    H_ps = np.random.rand(nP, nR, K, K)
    
    # We need R and P grids for the transform
    R_grid = np.linspace(-5, 5, nR)
    P_grid = np.linspace(-2, 2, nP)
    
    H_hilbert = transform.inverse_weyl_transform(H_ps, R_grid, P_grid)
    
    expected_dim = K * nR
    assert H_hilbert.shape == (expected_dim, expected_dim)

def test_inverse_weyl_transform_hermiticity(random_hermitian_matrix):
    """
    Ref: Eq 20. The integral of Hermitian operators e^(iP(R-R')) 
    should result in a Hermitian operator in position space.
    """
    nP, nR, K = 11, 11, 2
    H_ps = np.zeros((nP, nR, K, K), dtype=complex)
    
    # Make every point (R,P) Hermitian
    for i in range(nP):
        for j in range(nR):
            mat = np.random.rand(K, K) + 1j*np.random.rand(K,K)
            H_ps[i,j] = mat + mat.conj().T

    R_grid = np.linspace(-5, 5, nR)
    P_grid = np.linspace(-2, 2, nP)
    
    H_hilbert = transform.inverse_weyl_transform(H_ps, R_grid, P_grid)
    
    assert np.allclose(H_hilbert, H_hilbert.conj().T, atol=1e-8)

# Property-based testing
@given(
    arrays(np.float64, (5, 5, 2, 2), elements=st.floats(-10, 10)),
    arrays(np.float64, (5, 5, 2, 2), elements=st.floats(-10, 10))
)
def test_inverse_weyl_transform_linearity(A_ps, B_ps):
    """
    Tests that T(A + B) == T(A) + T(B).
    """
    nR = 5
    nP = 5
    R_grid = np.linspace(-1, 1, nR)
    P_grid = np.linspace(-1, 1, nP)
    
    # Enforce complex type for internal FFTs if needed, 
    # though input here is float, transform handles it.
    
    T_A = transform.inverse_weyl_transform(A_ps, R_grid, P_grid)
    T_B = transform.inverse_weyl_transform(B_ps, R_grid, P_grid)
    T_Sum = transform.inverse_weyl_transform(A_ps + B_ps, R_grid, P_grid)
    
    assert np.allclose(T_Sum, T_A + T_B, atol=1e-8)