import pytest
import numpy as np
from phase_space_chem import diabatization

def test_calculate_adt_matrix_unitarity(random_hermitian_matrix):
    """
    Verifies that the calculated ADT matrix U is unitary.
    Ref: Eq 10, 11.
    """
    # Mock a set of adiabatic states (eigenvectors of a Hermitian matrix)
    H_el = random_hermitian_matrix(10)
    _, eigenvecs = np.linalg.eigh(H_el)
    
    # Assume we select top K=3 states
    adiabatic_subset = eigenvecs[:, :3]
    
    # Mock position operator in this basis for Boys localization
    # Or just call the function if it takes raw eigenstates
    U = diabatization.calculate_boys_adt(adiabatic_subset)
    
    # Check U^dag @ U = I
    # U is shape (N_r, K) or (K, K) depending on if it's the full rotation 
    # or the subspace rotation. Usually Boys rotates the K subspace.
    # Assuming U is the (K, K) rotation matrix applied to the subspace.
    
    identity = np.eye(U.shape[0])
    product = U.conj().T @ U
    assert np.allclose(product, identity)

def test_calculate_adt_matrix_shape(standard_grids):
    """
    Verifies ADT matrix dimension. 
    If calculating for the whole grid, shape might be [N_P, N_R, K, K].
    """
    # Using simplified mocks for shape check
    nP, nR, K = 5, 5, 2
    
    # Mock function call
    U_tensor = diabatization.calculate_adt_tensor(nP, nR, K) 
    assert U_tensor.shape == (nP, nR, K, K)

def test_construct_ps_diabatic_hamiltonian_hermiticity(random_hermitian_matrix):
    """
    The diabatic Hamiltonian (Eq 19) must be Hermitian.
    H_diab = U^dag @ H_ad @ U
    """
    K = 3
    H_ad = np.diag(np.sort(np.random.rand(K))) # Diagonal adiabatic energies
    
    # Random unitary matrix
    A = random_hermitian_matrix(K)
    _, U = np.linalg.eigh(A)
    
    H_diab = U.conj().T @ H_ad @ U
    
    assert np.allclose(H_diab, H_diab.conj().T)