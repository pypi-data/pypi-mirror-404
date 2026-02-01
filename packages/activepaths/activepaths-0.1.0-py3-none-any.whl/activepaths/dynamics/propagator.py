import numpy as np
from activepaths.core import StateTuple

def calculate_fwd_propagator_prob(
    r_next: np.ndarray, 
    r: np.ndarray, 
    s: int, 
    s_next: int, 
    force: np.ndarray, 
    mu: float, 
    D: float, 
    dt: float
) -> float:
    """Ref: PDF 2, Pg 3, Eq 4."""
    drift = mu * force * dt
    variance = 2 * D * dt
    dist_sq = np.sum((r_next - r - drift)**2)
    return np.exp(-dist_sq / (2 * variance))

def calculate_bwd_propagator_prob(
    current_state: StateTuple,
    previous_state: StateTuple,
    trans_diff_coeff: float,
    rot_diff_coeff: float,
    dt: float
) -> float:
    """Ref: PDF 1, Pg 4, Eq 13."""
    # Use standard names from StateTuple
    s_i, r_i, theta_i = previous_state.s, previous_state.r, previous_state.theta
    s_next, r_next, theta_next = current_state.s, current_state.r, current_state.theta
    
    u_i = np.array([np.cos(theta_i), np.sin(theta_i)])
    displacement = r_i - r_next + (float(s_i) * u_i * dt)
    spatial_dist_sq = np.sum(displacement**2)
    p_space = np.exp(-spatial_dist_sq / (4 * trans_diff_coeff * dt))

    if s_i == 0 and s_next == 1:
        p_theta = 1.0 / (2 * np.pi)
    else:
        diff_theta = (theta_i - theta_next + np.pi) % (2 * np.pi) - np.pi
        p_theta = np.exp(-(diff_theta**2) / (4 * rot_diff_coeff * dt))

    return p_space * p_theta