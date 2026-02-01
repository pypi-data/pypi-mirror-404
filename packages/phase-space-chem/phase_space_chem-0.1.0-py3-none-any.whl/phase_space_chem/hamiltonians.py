import numpy as np
from .potentials import compute_shin_metiu
from .operators import compute_standard_gamma

def construct_exact_hamiltonian(r_grid, R_grid, **params):
    """Alias for test compatibility. Constructs H = T_n + T_e + V."""
    N_R, N_r = len(R_grid), len(r_grid)
    M, m_e = params.get('M', 1836.15), params.get('m_e', 1.0)
    
    # Kinetic energy using 3-point finite difference for simplicity
    def get_t_mat(grid, mass):
        n = len(grid)
        dx = grid[1] - grid[0]
        diag = np.ones(n) * (1.0 / (mass * dx**2))
        off = -0.5 * np.ones(n-1) * (1.0 / (mass * dx**2))
        return np.diag(diag) + np.diag(off, 1) + np.diag(off, -1)

    T_e = get_t_mat(r_grid, m_e)
    T_n = get_t_mat(R_grid, M)
    V = compute_shin_metiu(r_grid, R_grid, params['L'], params['Rf'], params['C'])
    
    H = np.kron(T_n, np.eye(N_r)) + np.kron(np.eye(N_R), T_e) + np.diag(V.T.flatten())
    return H

def construct_ps_hamiltonian(r_grid, R_grid, P_grid, **params):
    """Alias for test compatibility. Constructs the PS electronic Hamiltonian."""
    N_P, N_R, N_r = len(P_grid), len(R_grid), len(r_grid)
    M = params.get('M', 1836.15)
    
    # 1. H_el(R) = T_e + V(r, R)
    dx = r_grid[1] - r_grid[0]
    T_e = (np.diag(np.ones(N_r)) - 0.5*np.diag(np.ones(N_r-1), 1) - 0.5*np.diag(np.ones(N_r-1), -1)) / (dx**2)
    V = compute_shin_metiu(r_grid, R_grid, params['L'], params['Rf'], params['C'])
    
    # 2. Gamma operator
    Gamma = compute_standard_gamma(r_grid)
    Gamma2 = Gamma @ Gamma
    
    H_ps = np.zeros((N_P, N_R, N_r, N_r), dtype=np.complex128)
    for i, P in enumerate(P_grid):
        K_PS = (P**2 / (2*M)) * np.eye(N_r) - (1j * P * Gamma / M) - (Gamma2 / (2*M))
        for j in range(N_R):
            H_ps[i, j] = T_e + np.diag(V[:, j]) + K_PS
    return H_ps

# Keep original names as aliases
construct_total_hamiltonian_exact = construct_exact_hamiltonian
construct_ps_electronic_hamiltonian = construct_ps_hamiltonian