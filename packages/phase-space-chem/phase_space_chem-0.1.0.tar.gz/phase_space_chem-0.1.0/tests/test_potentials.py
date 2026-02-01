import pytest
import numpy as np
from phase_space_chem import potentials

def test_compute_shin_metiu_potential_shape(standard_grids, shin_metiu_params):
    """
    Verifies the potential matrix has shape [N_r, N_R].
    """
    r_grid = np.linspace(-22, 22, standard_grids['nr'])
    R_grid = np.linspace(-9, 9, standard_grids['nR'])
    
    V = potentials.compute_shin_metiu(r_grid, R_grid, **shin_metiu_params)
    
    assert V.shape == (standard_grids['nr'], standard_grids['nR'])

def test_shin_metiu_potential_symmetry_at_origin(standard_grids, shin_metiu_params):
    """
    At nuclear position R=0, the potential V(r, 0) should be symmetric 
    with respect to electronic position r (V(r) == V(-r)).
    Ref: PDF Eq. 22. At R=0, terms are |r|, |L/2 - r| and |-L/2 - r|.
    The fixed ions are symmetric around 0.
    """
    # Create a perfectly symmetric grid including 0
    r_grid = np.linspace(-20, 20, 101) 
    R_grid = np.array([0.0])
    
    V = potentials.compute_shin_metiu(r_grid, R_grid, **shin_metiu_params)
    V_at_R0 = V[:, 0]
    
    # Check symmetry V(r) == V(-r)
    # Since grid is symmetric, V array should equal its reverse
    assert np.allclose(V_at_R0, V_at_R0[::-1])

def test_shin_metiu_potential_finite_values(standard_grids, shin_metiu_params):
    """
    Ensures no NaNs or Infs are generated.
    """
    r_grid = np.linspace(-22, 22, standard_grids['nr'])
    R_grid = np.linspace(-9, 9, standard_grids['nR'])
    
    V = potentials.compute_shin_metiu(r_grid, R_grid, **shin_metiu_params)
    assert np.all(np.isfinite(V))