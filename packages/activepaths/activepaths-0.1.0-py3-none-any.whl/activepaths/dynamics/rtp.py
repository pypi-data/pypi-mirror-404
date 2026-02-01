import numpy as np

def update_activity_phase(s_i: int, rate_switch: float, dt: float) -> int:
    prob_stay = np.exp(-rate_switch * dt)
    if np.random.rand() > prob_stay:
        return 1 - s_i
    return s_i

def update_position(r_i: np.ndarray, mu: float, force: np.ndarray, dt: float, velocity: float, s_i: int, angle: float, noise_scale: float) -> np.ndarray:
    propulsion_dir = np.array([np.cos(angle), np.sin(angle)])
    drift = (mu * force + velocity * s_i * propulsion_dir) * dt
    noise = noise_scale * np.sqrt(dt) * np.random.randn(*r_i.shape)
    return r_i + drift + noise

def update_orientation(theta_i: float, s_i: int, s_next: int, D_rot: float, dt: float) -> float:
    if s_i == 0 and s_next == 1:
        return np.random.uniform(0, 2 * np.pi)
    noise = np.sqrt(2 * D_rot * dt) * np.random.randn()
    return (theta_i + noise) % (2 * np.pi)

def get_propulsion_direction(angle: float) -> np.ndarray:
    return np.array([np.cos(angle), np.sin(angle)])