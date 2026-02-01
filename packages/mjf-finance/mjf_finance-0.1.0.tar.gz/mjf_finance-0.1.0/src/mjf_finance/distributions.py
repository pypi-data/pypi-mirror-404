import numpy as np
from scipy.special import gamma
from typing import Union
from .utils import ArrayLike, beta_function, regularized_incomplete_beta

def pdf_student_t(
    detrended_log_return: ArrayLike,
    shape_param_alpha: float,
    mean_variance_theta: float,
    time_increment_tau: float
) -> ArrayLike:
    """
    Ref: Pg 3, Eq 7
    """
    x = detrended_log_return
    alpha = shape_param_alpha
    theta = mean_variance_theta
    tau = time_increment_tau
    
    term1_num = gamma(alpha / theta + 1.5)
    term1_den = np.sqrt(np.pi) * gamma(alpha / theta + 1.0) * np.sqrt(2 * alpha * tau)
    term2 = np.power((x**2) / (2 * alpha * tau) + 1, -(alpha / theta + 1.5))
    
    return (term1_num / term1_den) * term2

def pdf_half_student_t(
    detrended_log_return: ArrayLike,
    weight_gains: float,
    weight_losses: float,
    shape_param_alpha_gains: float,
    mean_variance_theta_gains: float,
    shape_param_alpha_losses: float,
    mean_variance_theta_losses: float,
    time_increment_tau: float
) -> ArrayLike:
    """
    Ref: Pg 4, Eq 15 (Eq 13, 14)
    """
    x = np.array(detrended_log_return, copy=True) if isinstance(detrended_log_return, np.ndarray) else np.array([detrended_log_return])
    is_scalar = np.isscalar(detrended_log_return)
    
    # Parameters
    wg = weight_gains
    wl = weight_losses
    ag = shape_param_alpha_gains
    tg = mean_variance_theta_gains
    al = shape_param_alpha_losses
    tl = mean_variance_theta_losses
    tau = time_increment_tau

    # Constants
    const_g = (2 * gamma(ag/tg + 1.5)) / (np.sqrt(np.pi) * gamma(ag/tg + 1) * np.sqrt(2*ag*tau))
    const_l = (2 * gamma(al/tl + 1.5)) / (np.sqrt(np.pi) * gamma(al/tl + 1) * np.sqrt(2*al*tau))

    # Calculate PDF
    # Gains part (x >= 0)
    pdf_vals = np.zeros_like(x, dtype=float)
    
    mask_g = x >= 0
    if np.any(mask_g):
        pdf_vals[mask_g] = wg * const_g * np.power((x[mask_g]**2)/(2*ag*tau) + 1, -(ag/tg + 1.5))
        
    mask_l = x < 0
    if np.any(mask_l):
        pdf_vals[mask_l] = wl * const_l * np.power((x[mask_l]**2)/(2*al*tau) + 1, -(al/tl + 1.5))

    return pdf_vals[0] if is_scalar else pdf_vals

def normalization_constant_mjf1(
    shape_param_alpha_gains: float,
    shape_param_alpha_losses: float,
    mean_variance_theta: float,
    time_increment_tau: float
) -> float:
    """
    Ref: Pg 6, Eq 21
    """
    ag = shape_param_alpha_gains
    al = shape_param_alpha_losses
    theta = mean_variance_theta
    tau = time_increment_tau
    
    exponent = (al/theta) + 1 + (ag/theta)
    denom = (2**exponent) * beta_function(al/theta + 1, ag/theta + 1) * np.sqrt((ag + al) * tau)
    return 1.0 / denom

def pdf_mjf1(
    detrended_log_return: ArrayLike,
    location_param_mu: float,
    shape_param_alpha_gains: float,
    shape_param_alpha_losses: float,
    mean_variance_theta: float,
    time_increment_tau: float
) -> ArrayLike:
    """
    Ref: Pg 6, Eq 20
    """
    x = detrended_log_return
    mu = location_param_mu
    ag = shape_param_alpha_gains
    al = shape_param_alpha_losses
    theta = mean_variance_theta
    tau = time_increment_tau
    
    C = normalization_constant_mjf1(ag, al, theta, tau)
    
    denominator_sqrt = np.sqrt((x - mu)**2 + (ag + al) * tau)
    fraction = (x - mu) / denominator_sqrt
    
    term1 = np.power(1 - fraction, ag/theta + 1.5)
    term2 = np.power(1 + fraction, al/theta + 1.5)
    
    return C * term1 * term2

def cdf_gains_mjf1(
    detrended_log_return: ArrayLike,
    location_param_mu: float,
    shape_param_alpha_gains: float,
    shape_param_alpha_losses: float,
    mean_variance_theta: float,
    time_increment_tau: float
) -> ArrayLike:
    """
    Ref: Pg 6, Eq 22
    """
    x = detrended_log_return
    mu = location_param_mu
    ag = shape_param_alpha_gains
    al = shape_param_alpha_losses
    theta = mean_variance_theta
    tau = time_increment_tau
    
    denominator_sqrt = np.sqrt((x - mu)**2 + (ag + al) * tau)
    fraction = (x - mu) / denominator_sqrt
    z = 0.5 * (1 + fraction)
    
    a_param = ag / theta + 1
    b_param = al / theta + 1
    
    return regularized_incomplete_beta(z, a_param, b_param)

def cdf_losses_mjf1(
    detrended_log_return: ArrayLike,
    location_param_mu: float,
    shape_param_alpha_gains: float,
    shape_param_alpha_losses: float,
    mean_variance_theta: float,
    time_increment_tau: float
) -> ArrayLike:
    """
    Ref: Pg 6, Eq 23
    Note: To ensure CDF behavior (0 at -inf), we use the standard mapping
    z = 0.5 * (1 + fraction), similar to gains.
    """
    x = detrended_log_return
    mu = location_param_mu
    ag = shape_param_alpha_gains
    al = shape_param_alpha_losses
    theta = mean_variance_theta
    tau = time_increment_tau
    
    denominator_sqrt = np.sqrt((x - mu)**2 + (ag + al) * tau)
    fraction = (x - mu) / denominator_sqrt
    z = 0.5 * (1 + fraction)
    
    a_param = ag / theta + 1
    b_param = al / theta + 1
    
    return regularized_incomplete_beta(z, a_param, b_param)

def normalization_constant_mjf2(
    shape_param_alpha_gains: float,
    mean_variance_theta_gains: float,
    shape_param_alpha_losses: float,
    mean_variance_theta_losses: float,
    time_increment_tau: float
) -> float:
    """
    Ref: Pg 7, Eq 28
    """
    ag = shape_param_alpha_gains
    tg = mean_variance_theta_gains
    al = shape_param_alpha_losses
    tl = mean_variance_theta_losses
    tau = time_increment_tau
    
    exponent = (al/tl) + 1 + (ag/tg)
    denom = (2**exponent) * beta_function(al/tl + 1, ag/tg + 1) * np.sqrt((ag + al) * tau)
    return 1.0 / denom

def pdf_mjf2(
    detrended_log_return: ArrayLike,
    location_param_mu: float,
    shape_param_alpha_gains: float,
    mean_variance_theta_gains: float,
    shape_param_alpha_losses: float,
    mean_variance_theta_losses: float,
    time_increment_tau: float
) -> ArrayLike:
    """
    Ref: Pg 7, Eq 27
    """
    x = detrended_log_return
    mu = location_param_mu
    ag = shape_param_alpha_gains
    tg = mean_variance_theta_gains
    al = shape_param_alpha_losses
    tl = mean_variance_theta_losses
    tau = time_increment_tau
    
    C = normalization_constant_mjf2(ag, tg, al, tl, tau)
    
    denominator_sqrt = np.sqrt((x - mu)**2 + (ag + al) * tau)
    fraction = (x - mu) / denominator_sqrt
    
    term1 = np.power(1 - fraction, ag/tg + 1.5)
    term2 = np.power(1 + fraction, al/tl + 1.5)
    
    return C * term1 * term2