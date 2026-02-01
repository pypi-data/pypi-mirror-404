import pytest
import numpy as np
from activepaths.core import StateTuple


class TestStateTuple:
    def test_state_tuple_initialization_with_valid_inputs(self):
        r = np.array([1.0, 2.0])
        # Fields renamed from s_i, r_i, theta_i to s, r, theta based on TypeError
        state = StateTuple(s=1, r=r, theta=0.5)
        assert state.s == 1
        assert np.array_equal(state.r, r)
        assert state.theta == 0.5

    def test_state_tuple_immutability(self):
        state = StateTuple(s=0, r=np.array([0, 0]), theta=0.0)
        with pytest.raises(AttributeError):
            state.s = 1 # NamedTuples are immutable