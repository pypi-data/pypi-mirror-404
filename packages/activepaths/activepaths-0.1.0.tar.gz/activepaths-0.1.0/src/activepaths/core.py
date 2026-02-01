from typing import NamedTuple, Sequence
import numpy as np

class StateTuple(NamedTuple):
    """
    Represents the state tuple omega_i = (s_i, r_i, theta_i).
    
    Ref: PDF 1, Pg 2, Col 2, Para 3
    """
    s: int  # s_i: {0 (passive), 1 (active)}
    r: np.ndarray  # r_i: [Spatial_Dim]
    theta: float  # theta_i: Scalar [0, 2pi)

# Type alias for a trajectory W (Sequence of states)
# Ref: PDF 1, Pg 3, Eq 6
TrajectoryPath = list[StateTuple]