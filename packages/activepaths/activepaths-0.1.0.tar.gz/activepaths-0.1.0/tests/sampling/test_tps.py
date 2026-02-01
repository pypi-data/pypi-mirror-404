import pytest
import numpy as np
from activepaths.sampling.tps import is_reactive_indicator, calculate_metropolis_acceptance

class TestIsReactiveIndicator:
    def test_is_reactive_indicator_valid_reactive_path(self):
        # Mock logic: R is x < -1, T is x > 1
        def in_R(state): return state[0] < -1
        def in_T(state): return state[0] > 1
        
        path = [np.array([-2, 0]), np.array([0, 0]), np.array([2, 0])]
        assert is_reactive_indicator(path, in_R, in_T) == 1

    def test_is_reactive_indicator_non_reactive_path(self):
        def in_R(state): return state[0] < -1
        def in_T(state): return state[0] > 1
        
        # Path ends back in R
        path = [np.array([-2, 0]), np.array([0, 0]), np.array([-2, 0])]
        assert is_reactive_indicator(path, in_R, in_T) == 0