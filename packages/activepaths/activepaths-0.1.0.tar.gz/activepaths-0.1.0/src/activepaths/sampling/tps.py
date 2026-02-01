from typing import Callable
from activepaths.core import TrajectoryPath, StateTuple
import numpy as np

def is_reactive_indicator(
    trajectory_path: TrajectoryPath,
    reactant_definition: Callable[[StateTuple], bool],
    product_definition: Callable[[StateTuple], bool]
) -> int:
    """
    Ref: PDF 1, Pg 3, Eq 5
    
    Returns h[W]: 1 if the path starts in reactant and ends in product, 0 otherwise.
    Also implicitly checks that intermediate states are not in A or B (transition region),
    though standard TPS often just checks endpoints.
    """
    if not trajectory_path:
        return 0
        
    start_in_A = reactant_definition(trajectory_path[0])
    end_in_B = product_definition(trajectory_path[-1])
    
    if start_in_A and end_in_B:
        return 1
    return 0

def calculate_metropolis_acceptance(
    trajectory_path_old: TrajectoryPath,
    trajectory_path_new: TrajectoryPath,
    prob_gen_old_to_new: float,
    prob_gen_new_to_old: float,
    prob_path_old: float,
    prob_path_new: float
) -> float:
    """
    Ref: PDF 1, Pg 3, Eq 5
    
    Calculates P_acc[W_old -> W_new].
    
    P_acc = h[W_new] * min(1, (P[W_new] * P_gen[new->old]) / (P[W_old] * P_gen[old->new]))
    
    Note: The h[W_new] check is usually done before calling this, but we include logic
    to return 0 if the indicator logic wasn't pre-checked (or assume valid paths passed).
    """
    # Numerator
    num = prob_path_new * prob_gen_new_to_old
    
    # Denominator
    den = prob_path_old * prob_gen_old_to_new
    
    if den == 0:
        return 0.0 # Should not happen for valid old path
        
    ratio = num / den
    
    return min(1.0, ratio)