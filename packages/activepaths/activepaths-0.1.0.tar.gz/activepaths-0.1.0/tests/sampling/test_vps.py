import pytest
import numpy as np
from activepaths.sampling.vps import calculate_stochastic_action, calculate_action_difference

class TestCalculateStochasticAction:
    def test_stochastic_action_positivity(self):
        # Action Gamma = 1/(4kBT) * integral( (rdot - mu*F)^2 )
        # Path2.pdf Eq 4. Always non-negative.
        velocities = np.array([[1.0, 0.0], [1.0, 0.0]])
        drifts = np.array([[0.5, 0.0], [0.5, 0.0]])
        action = calculate_stochastic_action(velocities, drifts, mu=1.0, kBT=1.0, dt=0.1)
        assert action >= 0

class TestCalculateActionDifference:
    def test_action_difference_zero_control_force(self):
        # Path2.pdf Eq 19. If Lambda (control potential) is 0, Delta Gamma is 0.
        grad_lambda = np.zeros((10, 2))
        x_dot = np.random.randn(10, 2)
        mu_F = np.zeros((10, 2))
        diff = calculate_action_difference(grad_lambda, x_dot, mu_F, mu=1.0, kBT=1.0, dt=0.1)
        assert np.isclose(diff, 0.0)