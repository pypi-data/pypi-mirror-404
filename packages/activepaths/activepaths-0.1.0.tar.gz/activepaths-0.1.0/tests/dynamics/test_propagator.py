import pytest
import numpy as np
from activepaths.dynamics.propagator import calculate_fwd_propagator_prob

class TestCalculateFwdPropagatorProb:
    def test_fwd_propagator_prob_spatial_term_normalization(self):
        # Prob should decrease as distance from drift-point increases (Gaussian)
        r_i = np.array([0., 0.])
        r_next_close = np.array([0.01, 0.0])
        r_next_far = np.array([5.0, 0.0])
        
        p_close = calculate_fwd_propagator_prob(r_next_close, r_i, s=0, s_next=0, 
                                               force=np.zeros(2), mu=1.0, D=1.0, dt=0.1)
        p_far = calculate_fwd_propagator_prob(r_next_far, r_i, s=0, s_next=0, 
                                             force=np.zeros(2), mu=1.0, D=1.0, dt=0.1)
        assert p_close > p_far