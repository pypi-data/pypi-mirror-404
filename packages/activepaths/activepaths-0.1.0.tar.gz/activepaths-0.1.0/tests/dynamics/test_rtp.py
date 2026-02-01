import pytest
import numpy as np
from activepaths.dynamics.rtp import (
    update_activity_phase,
    update_position,
    update_orientation,
    get_propulsion_direction
)

class TestUpdateActivityPhase:
    def test_update_activity_phase_no_switch(self):
        # p_i = exp(-lambda * dt). If lambda=0, p_i=1. s_{i+1} must equal s_i.
        s_next = update_activity_phase(s_i=0, rate_switch=0.0, dt=1.0)
        assert s_next == 0

    def test_update_activity_phase_high_rate(self):
        # If rate is effectively infinite, it should always switch (p_i -> 0)
        s_next = update_activity_phase(s_i=1, rate_switch=1e10, dt=1.0)
        assert s_next == 0

class TestUpdatePosition:
    def test_update_position_deterministic_drift(self):
        r_i = np.array([0.0, 0.0])
        force = np.array([1.0, 0.0])
        mu = 1.0
        dt = 0.1
        # No noise, no propulsion
        r_next = update_position(r_i, mu, force, dt, velocity=0.0, s_i=0, angle=0.0, noise_scale=0.0)
        expected = r_i + mu * force * dt
        assert np.allclose(r_next, expected)

class TestUpdateOrientation:
    def test_update_orientation_tumbling_uniformity(self):
        # If s_i=0 and s_next=1, theta should be random (Equation 3 in Path1.pdf)
        # We test this by checking if many samples are within bounds [0, 2pi]
        thetas = [update_orientation(0.0, s_i=0, s_next=1, D_rot=0.1, dt=0.01) for _ in range(100)]
        assert all(0 <= t < 2*np.pi for t in thetas)

    def test_get_propulsion_direction_normalization(self):
        vec = get_propulsion_direction(angle=np.pi/4)
        assert np.isclose(np.linalg.norm(vec), 1.0)