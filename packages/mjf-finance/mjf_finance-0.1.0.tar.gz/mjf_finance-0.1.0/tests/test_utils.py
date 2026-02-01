import pytest
import numpy as np
import scipy.special as sp
from mjf_finance import utils

# --- Fixtures ---
@pytest.fixture
def scalar_inputs():
    return 2.5, 3.5

@pytest.fixture
def array_inputs():
    a = np.array([1.0, 2.0, 3.0])
    b = np.array([4.0, 5.0, 6.0])
    return a, b

# --- Beta Function Tests ---

def test_beta_function_scalar(scalar_inputs):
    a, b = scalar_inputs
    result = utils.beta_function(a, b)
    expected = sp.beta(a, b)
    assert result == pytest.approx(expected, rel=1e-9)

def test_beta_function_array(array_inputs):
    a, b = array_inputs
    result = utils.beta_function(a, b)
    expected = sp.beta(a, b)
    np.testing.assert_allclose(result, expected, rtol=1e-9)

def test_beta_function_invalid_input():
    # Beta function is generally undefined or infinite for negative integers
    # Numpy/Scipy typically returns inf or nan for invalid inputs
    res = utils.beta_function(-1, 2)
    assert np.isinf(res) or np.isnan(res)

# --- Regularized Incomplete Beta Tests ---

def test_regularized_incomplete_beta_scalar():
    x = 0.5
    a, b = 2.0, 3.0
    # Paper uses I(x; a, b). Scipy uses betainc(a, b, x)
    result = utils.regularized_incomplete_beta(x, a, b)
    expected = sp.betainc(a, b, x)
    assert result == pytest.approx(expected, rel=1e-9)

def test_regularized_incomplete_beta_boundaries():
    a, b = 2.0, 2.0
    assert utils.regularized_incomplete_beta(0.0, a, b) == 0.0
    assert utils.regularized_incomplete_beta(1.0, a, b) == 1.0

def test_regularized_incomplete_beta_array():
    x = np.array([0.1, 0.5, 0.9])
    a, b = 2.0, 3.0
    result = utils.regularized_incomplete_beta(x, a, b)
    expected = sp.betainc(a, b, x)
    np.testing.assert_allclose(result, expected, rtol=1e-9)