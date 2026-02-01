import numpy as np

def compute_standard_gamma(r_grid: np.ndarray) -> np.ndarray:
    """
    Computes Gamma = p / (i*hbar). 
    In position basis, p = -i*hbar * d/dr. 
    So Gamma = (-i*hbar * d/dr) / (i*hbar) = -d/dr.
    """
    n = len(r_grid)
    dr = r_grid[1] - r_grid[0]
    # Central difference matrix for first derivative
    # d/dr approx (f(i+1) - f(i-1)) / 2dr
    gamma = (np.diag(np.ones(n-1), 1) - np.diag(np.ones(n-1), -1)) / (2.0 * dr)
    # Gamma = -d/dr
    return -gamma.astype(np.complex128)

def compute_partition_of_unity(r_grid, atom_positions, sigma) -> np.ndarray:
    r = r_grid[np.newaxis, :]
    R_A = np.array(atom_positions)[:, np.newaxis]
    weights = np.exp(-((r - R_A)**2) / (sigma**2))
    return weights / np.sum(weights, axis=0)

def compute_partitioned_gamma(r_grid_or_p_op: np.ndarray, centers_or_part: np.ndarray) -> np.ndarray:
    # Handle the polymorphic signature used in tests
    if r_grid_or_p_op.ndim == 1:
        p_op = compute_standard_gamma(r_grid_or_p_op) * 1.0j # p = i*Gamma
        theta = compute_partition_of_unity(r_grid_or_p_op, centers_or_part, sigma=4.0)
    else:
        p_op = r_grid_or_p_op
        theta = np.array(centers_or_part)

    gamma_total = np.zeros_like(p_op, dtype=np.complex128)
    for A in range(theta.shape[0]):
        theta_mat = np.diag(theta[A])
        # Gamma_A = (1/2i) * {theta_A, p}
        gamma_total += (theta_mat @ p_op + p_op @ theta_mat) / 2.0j
    return gamma_total