import numpy as np
from typing import Callable

def estimate_transition_rate(
    path_partition_function: float,
    partition_function_reactant: float,
    tau: float
) -> float:
    """
    Ref: PDF 2, Pg 5, Eq 8
    
    Estimates k_AB ~ (1/tau) * (Z_AB(tau) / Z_A).
    """
    if partition_function_reactant == 0 or tau == 0:
        return 0.0
        
    ratio = path_partition_function / partition_function_reactant
    rate = (1.0 / tau) * ratio
    return rate

def calculate_observable_time_integrated(
    trajectory_ensemble: np.ndarray,
    observable_func: Callable[[np.ndarray], float],
    dt: float
) -> np.ndarray:
    """
    Ref: PDF 2, Pg 5, Eq 9
    
    Computes O[X(tau)] = integral(o(x_t) dt).
    
    Args:
        trajectory_ensemble: (N_paths, N_steps, Dim)
    """
    n_paths, n_steps, _ = trajectory_ensemble.shape
    observables = np.zeros(n_paths)
    
    for i in range(n_paths):
        path = trajectory_ensemble[i]
        # Apply observable function to each timestep
        obs_vals = np.apply_along_axis(observable_func, 1, path)
        
        # Integrate (Simple sum * dt)
        observables[i] = np.sum(obs_vals) * dt
        
    return observables

def estimate_large_dev_rate_function(
    tilted_partition_func: float,
    tilting_parameter: float,
    observable_value: float,
    tau: float
) -> float:
    """
    Ref: PDF 2, Pg 6, Eq 11 (via Legendre Transform structure implied in Eq 24)
    
    Estimates I(O/tau) = (1/tau) * max_lambda [ lambda * O + ln Z_lambda ]
    """
    if tau == 0:
        return 0.0
        
    term = tilting_parameter * observable_value + np.log(tilted_partition_func)
    return term / tau