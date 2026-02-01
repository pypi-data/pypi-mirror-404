import pytest
import numpy as np
from scipy.integrate import quad
from scipy.optimize import minimize_scalar
from mjf_finance import statistics, distributions

# --- Fixtures ---
@pytest.fixture
def mjf1_params():
    return {
        'location_param_mu': 1e-3,
        'shape_param_alpha_gains': 8e-5,
        'shape_param_alpha_losses': 6e-5,
        'mean_variance_theta': 1.4e-4,
        'time_increment_tau': 1.0
    }

# --- mJF1 Statistical Tests ---

def test_mjf1_mean_analytical_vs_numerical(mjf1_params):
    """
    Compare analytical Mean (Eq 24) vs Numerical integration:
    E[X] = Integral(x * f(x) dx)
    """
    # 1. Analytical Result
    ana_mean = statistics.statistical_mean(**mjf1_params)
    
    # 2. Numerical Integration
    def integrand(x):
        return x * distributions.pdf_mjf1(detrended_log_return=x, **mjf1_params)
        
    num_mean, _ = quad(integrand, -0.5, 0.5) 
    
    # Tolerance relaxed to 5% as formula relies on approximations for non-integer parameters
    assert ana_mean == pytest.approx(num_mean, rel=0.05)

def test_mjf1_variance_analytical_vs_numerical(mjf1_params):
    """
    Compare analytical Variance (Eq 25) vs Numerical integration:
    Var(X) = E[X^2] - (E[X])^2
    """
    # 1. Analytical Result
    var_params = {
        'shape_param_alpha_gains': mjf1_params['shape_param_alpha_gains'],
        'shape_param_alpha_losses': mjf1_params['shape_param_alpha_losses'],
        'mean_variance_theta': mjf1_params['mean_variance_theta'],
        'time_increment_tau': mjf1_params['time_increment_tau']
    }
    ana_var = statistics.statistical_variance(**var_params)
    
    # 2. Numerical Integration
    mu_num, _ = quad(lambda x: x * distributions.pdf_mjf1(detrended_log_return=x, **mjf1_params), -1, 1)
    
    def integrand_sq(x):
        return (x**2) * distributions.pdf_mjf1(detrended_log_return=x, **mjf1_params)
    
    e_x2, _ = quad(integrand_sq, -1, 1)
    num_var = e_x2 - mu_num**2
    
    # Tolerance relaxed to 5%
    assert ana_var == pytest.approx(num_var, rel=0.05)

def test_mjf1_mode_check(mjf1_params):
    """
    Verify the Mode (Eq 26) is close to the numerical peak of the PDF.
    """
    ana_mode = statistics.statistical_mode(**mjf1_params)
    
    # Find numerical peak using optimization (negative PDF min)
    def neg_pdf(x):
        return -distributions.pdf_mjf1(detrended_log_return=x, **mjf1_params)
    
    # Search around the analytical mode
    res = minimize_scalar(neg_pdf, bounds=(ana_mode - 0.1, ana_mode + 0.1), method='bounded')
    
    assert res.success
    num_mode = res.x
    
    # Assert analytical mode is reasonably close to numerical peak
    # The analytical formula is often an approximation for heavy tails
    assert ana_mode == pytest.approx(num_mode, abs=1e-4)

# --- Skewness Tests ---

def test_pearson_skewness_coefficients(mjf1_params):
    """Test calculation of Pearson skewness coefficients (Eq 8)."""
    # Calculate components
    m1 = statistics.statistical_mean(**mjf1_params)
    var_params = {
        'shape_param_alpha_gains': mjf1_params['shape_param_alpha_gains'],
        'shape_param_alpha_losses': mjf1_params['shape_param_alpha_losses'],
        'mean_variance_theta': mjf1_params['mean_variance_theta'],
        'time_increment_tau': mjf1_params['time_increment_tau']
    }
    m2 = statistics.statistical_variance(**var_params)
    mode = statistics.statistical_mode(**mjf1_params)
    
    median = m1 - 0.0001 # Artificial median for testing
    
    zeta1 = statistics.skewness_coeff_pearson2(m1, median, m2)
    zeta2 = statistics.skewness_coeff_pearson1(m1, mode, m2)
    
    expected_z1 = (m1 - median) / np.sqrt(m2)
    expected_z2 = (m1 - mode) / np.sqrt(m2)
    
    assert zeta1 == pytest.approx(expected_z1)
    assert zeta2 == pytest.approx(expected_z2)