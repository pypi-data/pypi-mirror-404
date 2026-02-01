import numpy as np

def inverse_weyl_transform(
    ps_diabatic_hamiltonian: np.ndarray,
    nuclear_position_grid: np.ndarray,
    nuclear_momentum_grid: np.ndarray
) -> np.ndarray:
    """
    Ref: Page 8, Eq 20
    Performs the Inverse Weyl Transform to requantize the Phase Space 
    Hamiltonian back into a Hilbert space operator.
    
    <R | H | R'> = Integral[dP/2pi*hbar] exp(i/hbar * P * (R - R')) * H_W((R+R')/2, P)

    Args:
        ps_diabatic_hamiltonian (np.ndarray): H_W^PS(R,P) [N_P, N_R, K, K].
        nuclear_position_grid (np.ndarray): Grid R [N_R].
        nuclear_momentum_grid (np.ndarray): Grid P [N_P].

    Returns:
        np.ndarray: requantized_vib_hamiltonian [K*N_R, K*N_R].
    """
    N_P, N_R, K, _ = ps_diabatic_hamiltonian.shape
    
    # Initialize output matrix
    # The basis size is (Number of nuclear points * Number of electronic states)
    dim_H = K * N_R
    H_vib = np.zeros((dim_H, dim_H), dtype=np.complex128)
    
    dP = nuclear_momentum_grid[1] - nuclear_momentum_grid[0]
    hbar = 1.0 # Atomic units
    
    # We iterate over blocks (R_i, R_j)
    # Each block is a KxK matrix corresponding to electronic states
    
    for i in range(N_R):
        R_i = nuclear_position_grid[i]
        
        for j in range(N_R):
            R_j = nuclear_position_grid[j]
            
            # Midpoint R
            R_mid = (R_i + R_j) / 2.0
            
            # Find R_mid in the grid (Interpolation)
            # Since grid is linear: index = (R - R_min) / dR
            # R_mid index corresponds exactly to (i + j) / 2
            
            mid_idx_float = (i + j) / 2.0
            idx_low = int(np.floor(mid_idx_float))
            idx_high = int(np.ceil(mid_idx_float))
            
            # Extract H_W(R_mid, P) for all P
            if idx_low == idx_high:
                # Exact grid point
                H_W_slice = ps_diabatic_hamiltonian[:, idx_low, :, :]
            else:
                # Linear Interpolation
                # For uniform grid, the weight is 0.5 since mid_idx is x.5
                H_W_slice = 0.5 * (ps_diabatic_hamiltonian[:, idx_low, :, :] + 
                                   ps_diabatic_hamiltonian[:, idx_high, :, :])
            
            # Integration over P
            # Term: exp( i * P * (R_i - R_j) )
            # We compute the phase factor for all P
            phase_factor = np.exp((1.0j / hbar) * nuclear_momentum_grid * (R_i - R_j))
            
            # Integrate: Sum( H_W(P) * phase(P) ) * dP / (2*pi*hbar)
            # Broadcasting: phase_factor is [N_P], H_W_slice is [N_P, K, K]
            integral = np.sum(H_W_slice * phase_factor[:, np.newaxis, np.newaxis], axis=0)
            
            block_val = integral * dP / (2.0 * np.pi * hbar)
            
            # Place block into large Hamiltonian
            # Rows: i*K to (i+1)*K
            # Cols: j*K to (j+1)*K
            H_vib[i*K : (i+1)*K, j*K : (j+1)*K] = block_val
            
    return H_vib