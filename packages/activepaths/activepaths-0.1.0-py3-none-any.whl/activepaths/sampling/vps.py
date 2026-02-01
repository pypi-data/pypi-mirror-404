import numpy as np

def calculate_stochastic_action(velocities: np.ndarray, drifts: np.ndarray, mu: float, kBT: float, dt: float) -> np.ndarray:
    """Ref: PDF 2, Pg 3, Eq 4."""
    deviation = velocities - drifts
    # Action = 1/(4kT) * sum( (v - muF)^2 / mu ) * dt
    integrand = np.sum(deviation**2 / mu, axis=-1)
    return (1.0 / (4.0 * kBT)) * np.sum(integrand, axis=-1) * dt

def calculate_action_difference(grad_lambda: np.ndarray, velocities: np.ndarray, drifts: np.ndarray, mu: float, kBT: float, dt: float) -> np.ndarray:
    """Ref: PDF 2, Pg 9, Eq 19."""
    # Delta Gamma = -1/(4kT) * sum( gradL . (2v - 2drift + mu*gradL) ) * dt
    bracket = 2 * velocities - 2 * drifts + (mu * grad_lambda)
    dot_prod = np.sum(grad_lambda * bracket, axis=-1)
    return (-1.0 / (4.0 * kBT)) * np.sum(dot_prod, axis=-1) * dt

def calculate_tilted_partition_func(observable_time_integrated: np.ndarray, action_difference: np.ndarray, tilting_parameter: float) -> float:
    exponent = -tilting_parameter * observable_time_integrated - action_difference
    return float(np.mean(np.exp(exponent)))