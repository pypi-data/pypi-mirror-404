import pytest
import numpy as np
from activepaths.analysis import estimate_transition_rate, calculate_observable_time_integrated

class TestEstimateTransitionRate:
    def test_estimate_transition_rate_basic_calculation(self):
        # k ~ (Z_AB / Z_A) * (1/tau)
        # If Z_AB = Z_A, k = 1/tau
        # Using positional arguments for Z terms to avoid keyword mismatch (e.g. z_ab vs Z_AB)
        rate = estimate_transition_rate(100, 100, tau=2.0)
        assert np.isclose(rate, 0.5)

class TestCalculateObservableTimeIntegrated:
    def test_observable_time_integrated_constant_function(self):
        # integral of 1.0 from 0 to 10 is 10.0
        # Input shape must be (n_paths, n_steps, dim)
        path_data = np.ones((1, 100, 2)) 
        observable = lambda x: 1.0
        result = calculate_observable_time_integrated(path_data, observable, dt=0.1)
        # result is an array of shape (n_paths,)
        assert np.isclose(result[0], 10.0)
