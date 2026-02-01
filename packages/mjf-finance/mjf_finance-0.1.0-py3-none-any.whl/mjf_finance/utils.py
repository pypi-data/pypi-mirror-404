import numpy as np
from scipy.special import beta, betainc
from typing import Union

ArrayLike = Union[float, np.ndarray]

def beta_function(a: ArrayLike, b: ArrayLike) -> ArrayLike:
    """
    Ref: Pg 6, Eq 21
    
    Computes the Beta function B(a, b) = Gamma(a)Gamma(b)/Gamma(a+b).
    
    Args:
        a: First input parameter (must be > 0).
        b: Second input parameter (must be > 0).
        
    Returns:
        Value of the Beta function.
    """
    return beta(a, b)

def regularized_incomplete_beta(x: ArrayLike, a: ArrayLike, b: ArrayLike) -> ArrayLike:
    """
    Ref: Pg 4, Eq 11; Pg 6, Eq 22
    
    Computes the Regularized Incomplete Beta function I(x; a, b).
    
    Args:
        x: The upper limit of integration (must be in [0, 1]).
        a: First shape parameter (must be > 0).
        b: Second shape parameter (must be > 0).
        
    Returns:
        Value of the regularized incomplete beta function (probability).
    """
    return betainc(a, b, x)