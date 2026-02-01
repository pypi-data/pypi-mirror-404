from truncated_gamma_rvs import TruncatedGamma, truncgamma_rvs
import numpy as np
import numpy.testing as npt
import pytest

def test_initilization():
    x = TruncatedGamma(alpha = 4, theta = 25, A = 0, B = 1000)
    assert isinstance(x, TruncatedGamma)
    assert (x.alpha, x.theta, x.A, x.B) == (4, 25, 0, 1000)

    with pytest.raises(ValueError) as exc_info:
        TruncatedGamma(alpha = 0, theta = 25, A = 0, B = 1000)
    assert 'The value of alpha should be greater than zero.' in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        TruncatedGamma(alpha = 4, theta = 0, A = 0, B = 1000)
    assert 'The value of theta should be greater than zero.' in str(exc_info.value)
    
    with pytest.raises(ValueError) as exc_info:
        TruncatedGamma(alpha = 4, theta = 25, A = -1000, B = 1000)
    assert 'The lower bound A should be greater than or equal to zero.' in str(exc_info.value)
    
    with pytest.raises(ValueError) as exc_info:
        TruncatedGamma(alpha = 4, theta = 25, A = 0, B = 0)
    assert 'The upper bound B should be greater than A.' in str(exc_info.value)

def test_truncgamma_m1():
    x = TruncatedGamma(alpha = 4, theta = 25, A = 0, B = 1000)
    assert x.truncgamma_m1() == np.float64(99.99999999995468)

def test_truncgamma_m2():
    x = TruncatedGamma(alpha = 4, theta = 25, A = 0, B = 1000)
    assert x.truncgamma_m2() == np.float64(12499.99999994902)

def test_truncgamma_var():
    x = TruncatedGamma(alpha = 4, theta = 25, A = 0, B = 1000)
    assert x.truncgamma_var() == np.float64(2499.999999958083)

def test_truncgamma_cv():
    x = TruncatedGamma(alpha = 4, theta = 25, A = 0, B = 1000)
    assert x.truncgamma_cv() == np.float64(0.4999999999960349)

def test_truncgamma_rvs():
    actual = truncgamma_rvs(mean_target = 100, cv_target = 1/2, A = 0, B = 1000, size = 10, random_state = 123)
    expected = np.array([116.24621327,  35.02121931,  59.89023217,  55.47188101, 54.39446304, 140.63124805, 177.52242542,  66.43900397, 142.4522452 , 163.13733856])
    npt.assert_allclose(actual, expected)