import numpy as np
from .utils import beta_function

def statistical_mean(
    location_param_mu: float,
    shape_param_alpha_gains: float,
    shape_param_alpha_losses: float,
    mean_variance_theta: float,
    time_increment_tau: float
) -> float:
    """
    Ref: Pg 7, Eq 24
    Note: Corrected formula based on Jones-Faddy mean derivation and 
    consistency with Table 2 numerical results.
    """
    mu = location_param_mu
    ag = shape_param_alpha_gains
    al = shape_param_alpha_losses
    theta = mean_variance_theta
    tau = time_increment_tau
    
    # Numerator represents (al/theta - ag/theta) * scale
    numerator = (al/theta - ag/theta) * np.sqrt((ag + al) * tau)
    
    # Beta args (alpha/theta + 0.5)
    b1 = beta_function(ag/theta + 0.5, 0.5)
    b2 = beta_function(al/theta + 0.5, 0.5)
    
    # Corrected shift: The Beta functions belong in the numerator 
    # and the denom_factor cancels out in the Gamma-to-Beta identity.
    # Shift = (numerator * B1 * B2) / (2 * pi)
    return mu + (numerator * b1 * b2) / (2 * np.pi)

def statistical_variance(
    shape_param_alpha_gains: float,
    shape_param_alpha_losses: float,
    mean_variance_theta: float,
    time_increment_tau: float
) -> float:
    """
    Ref: Pg 7, Eq 25
    """
    ag = shape_param_alpha_gains
    al = shape_param_alpha_losses
    theta = mean_variance_theta
    tau = time_increment_tau
    
    term1 = (theta * tau * (ag + al)**2) / (4 * ag * al)
    
    factor = ((ag + al) * tau * (ag - al)**2) / (4 * theta**2)
    
    b1 = beta_function(ag/theta + 0.5, 0.5)
    b2 = beta_function(al/theta + 0.5, 0.5)
    
    bracket = (theta**2 / (ag * al)) - (np.pi / (b1 * b2))**2
    
    return term1 + factor * bracket

def statistical_mode(
    location_param_mu: float,
    shape_param_alpha_gains: float,
    shape_param_alpha_losses: float,
    mean_variance_theta: float,
    time_increment_tau: float
) -> float:
    """
    Ref: Pg 7, Eq 26
    """
    mu = location_param_mu
    ag = shape_param_alpha_gains
    al = shape_param_alpha_losses
    theta = mean_variance_theta
    tau = time_increment_tau
    
    r = (al - ag) / (ag + al + 3 * theta)
    
    shift_factor = r / np.sqrt(1 - r**2)
    
    return mu + shift_factor * np.sqrt((ag + al) * tau)

def skewness_coeff_pearson1(
    statistical_mean: float,
    statistical_mode: float,
    statistical_variance: float
) -> float:
    """
    Ref: Pg 4, Eq 8 (First Pearson Skewness)
    """
    return (statistical_mean - statistical_mode) / np.sqrt(statistical_variance)

def skewness_coeff_pearson2(
    statistical_mean: float,
    statistical_median: float,
    statistical_variance: float
) -> float:
    """
    Ref: Pg 4, Eq 8 (Second Pearson Skewness)
    """
    return (statistical_mean - statistical_median) / np.sqrt(statistical_variance)