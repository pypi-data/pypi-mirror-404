import numpy as np
from scipy.special import erf

def compute_shin_metiu(
    electronic_position_grid: np.ndarray,
    nuclear_position_grid: np.ndarray,
    L: float, Rf: float, C: float,
    **kwargs
) -> np.ndarray:
    """
    Computes the Shin-Metiu potential for a 1D model of a proton between two ions.
    
    Args:
        electronic_position_grid: Grid for electronic coordinate r.
        nuclear_position_grid: Grid for nuclear coordinate R.
        L: Distance between fixed ions.
        Rf: Screening length for the mobile ion.
        C: Screening length for the fixed ions.
        **kwargs: Ignores extra parameters (like 'M' or 'm_e') passed from fixtures.
    """
    r = electronic_position_grid[:, np.newaxis]
    R = nuclear_position_grid[np.newaxis, :]
    
    # Nuclear Repulsion
    V_nuc = 1.0/np.abs(L/2 - R + 1e-15) + 1.0/np.abs(-L/2 - R + 1e-15)
    
    # Electronic terms using soft-Coulomb potential
    def soft_coulomb(dist, width):
        return np.where(dist < 1e-12, 2.0/(width*np.sqrt(np.pi)), erf(dist/width)/dist)

    term_mob = soft_coulomb(np.abs(R - r), Rf)
    term_fix1 = soft_coulomb(np.abs(L/2 - r), C)
    term_fix2 = soft_coulomb(np.abs(-L/2 - r), C)
    
    return V_nuc - term_mob - term_fix1 - term_fix2

# Alias
compute_shin_metiu_potential = compute_shin_metiu