import numpy as np
from typing import Tuple, Union

def generate_position_grid(start: float, stop: float, num: int) -> np.ndarray:
    """Standard linear grid generation."""
    return np.linspace(start, stop, num)

def generate_position_grids(
    num_nuclear_points: int,
    num_electronic_points: int,
    nuclear_extent: float = 9.0,
    electronic_extent: float = 22.0
) -> Tuple[np.ndarray, np.ndarray]:
    R = generate_position_grid(-nuclear_extent, nuclear_extent, num_nuclear_points)
    r = generate_position_grid(-electronic_extent, electronic_extent, num_electronic_points)
    return R, r

def generate_momentum_grid(
    nuclear_grid_or_dR: Union[np.ndarray, float],
    num_momentum_points: int
) -> np.ndarray:
    if isinstance(nuclear_grid_or_dR, np.ndarray):
        dR = nuclear_grid_or_dR[1] - nuclear_grid_or_dR[0]
    else:
        dR = nuclear_grid_or_dR
    
    # Standard FFT-based conjugate grid
    P = 2.0 * np.pi * np.fft.fftshift(np.fft.fftfreq(num_momentum_points, d=dR))
    return P