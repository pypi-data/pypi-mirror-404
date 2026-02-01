import pytest
import numpy as np
from scipy.integrate import quad
from mjf_finance import distributions

# --- Constants for consistent testing ---
TAU = 1.0
ALPHA = 0.0001
THETA = 0.0002
MU = 0.001

# --- Student-t Tests ---

def test_pdf_student_t_integration():
    """Verify the PDF integrates to 1.0 over (-inf, inf)."""
    integral, _ = quad(
        lambda x: distributions.pdf_student_t(
            x, 
            shape_param_alpha=ALPHA, 
            mean_variance_theta=THETA, 
            time_increment_tau=TAU
        ),
        -np.inf, np.inf
    )
    assert integral == pytest.approx(1.0, rel=1e-4)

def test_pdf_student_t_symmetry():
    """Verify f(x) == f(-x) for standard Student-t centered at 0."""
    x = 0.05
    pos = distributions.pdf_student_t(
        x, 
        shape_param_alpha=ALPHA, 
        mean_variance_theta=THETA, 
        time_increment_tau=TAU
    )
    neg = distributions.pdf_student_t(
        -x, 
        shape_param_alpha=ALPHA, 
        mean_variance_theta=THETA, 
        time_increment_tau=TAU
    )
    assert pos == pytest.approx(neg)

# --- mJF1 Tests (Modified Jones-Faddy 1) ---

def test_normalization_constant_mjf1():
    """Test the normalization constant C calculation (Eq 21)."""
    alpha_g = 1e-4
    alpha_l = 2e-4
    
    # Calculate C using the utility
    C = distributions.normalization_constant_mjf1(alpha_g, alpha_l, THETA, TAU)
    
    # Verify PDF integrates to 1 using this C implicitly via the pdf function
    integral, _ = quad(
        lambda x: distributions.pdf_mjf1(x, location_param_mu=MU, shape_param_alpha_gains=alpha_g, 
                                         shape_param_alpha_losses=alpha_l, mean_variance_theta=THETA, 
                                         time_increment_tau=TAU),
        -np.inf, np.inf
    )
    assert integral == pytest.approx(1.0, rel=1e-4)

def test_pdf_mjf1_reduction_to_student_t():
    """If alpha_g == alpha_l, mJF1 should behave symmetrically around mu."""
    # Using same alpha for gains and losses
    val = 0.02
    pdf_pos = distributions.pdf_mjf1(
        detrended_log_return=MU + val, 
        location_param_mu=MU,
        shape_param_alpha_gains=ALPHA, 
        shape_param_alpha_losses=ALPHA, 
        mean_variance_theta=THETA, 
        time_increment_tau=TAU
    )
    pdf_neg = distributions.pdf_mjf1(
        detrended_log_return=MU - val, 
        location_param_mu=MU,
        shape_param_alpha_gains=ALPHA, 
        shape_param_alpha_losses=ALPHA, 
        mean_variance_theta=THETA, 
        time_increment_tau=TAU
    )
    
    assert pdf_pos == pytest.approx(pdf_neg, rel=1e-6)

def test_cdf_mjf1_limits():
    """CDF should be 0 at -inf and 1 at +inf."""
    # Since we can't test infinity, we test very large numbers relative to parameters
    large_val = 10.0 # Returns are usually < 1.0
    
    # F_losses (Eq 23) as x -> -inf
    f_loss = distributions.cdf_losses_mjf1(-large_val, location_param_mu=MU, 
                                           shape_param_alpha_gains=1e-4, 
                                           shape_param_alpha_losses=1e-4, 
                                           mean_variance_theta=THETA, 
                                           time_increment_tau=TAU)
    assert f_loss == pytest.approx(0.0, abs=1e-3)
    
    # F_gains (Eq 22) as x -> +inf
    f_gain = distributions.cdf_gains_mjf1(large_val, location_param_mu=MU, 
                                          shape_param_alpha_gains=1e-4, 
                                          shape_param_alpha_losses=1e-4, 
                                          mean_variance_theta=THETA, 
                                          time_increment_tau=TAU)
    assert f_gain == pytest.approx(1.0, abs=1e-3)

# --- mJF2 Tests ---

def test_pdf_mjf2_integration():
    """Verify mJF2 integrates to 1.0 with different thetas."""
    theta_g = 1.5e-4
    theta_l = 2.0e-4
    alpha_g = 1e-4
    alpha_l = 2e-4
    
    integral, _ = quad(
        lambda x: distributions.pdf_mjf2(x, MU, alpha_g, theta_g, alpha_l, theta_l, TAU),
        -np.inf, np.inf
    )
    assert integral == pytest.approx(1.0, rel=1e-4)