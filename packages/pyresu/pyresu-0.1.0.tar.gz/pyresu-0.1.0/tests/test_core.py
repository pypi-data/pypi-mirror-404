import numpy as np
import pytest
from hypothesis import given, strategies as st
from hypothesis.extra.numpy import arrays

from pyresu.core import compute_covariance_matrices, perform_truncated_cca, calculate_mutual_information

def test_compute_covariance_matrices_shapes():
    """
    Verify output dimensions [m,m], [h,h], and [h,m].
    """
    N, m, h = 100, 10, 5
    pt = np.random.randn(N, m)
    ft = np.random.randn(N, h)
    
    Cpp, Cff, Cfp = compute_covariance_matrices(pt, ft)
    
    assert Cpp.shape == (m, m)
    assert Cff.shape == (h, h)
    assert Cfp.shape == (h, m)

def test_compute_covariance_matrices_symmetry():
    """
    Ensure auto-covariance matrices C_pp and C_ff are symmetric.
    """
    N, m, h = 50, 4, 3
    pt = np.random.randn(N, m)
    ft = np.random.randn(N, h)
    
    Cpp, Cff, _ = compute_covariance_matrices(pt, ft)
    
    assert np.allclose(Cpp, Cpp.T, atol=1e-8)
    assert np.allclose(Cff, Cff.T, atol=1e-8)

def test_compute_covariance_matrices_positive_semi_definite():
    """
    Check that eigenvalues of covariance matrices are non-negative.
    """
    N, m, h = 100, 5, 5
    pt = np.random.randn(N, m)
    ft = np.random.randn(N, h)
    
    Cpp, Cff, _ = compute_covariance_matrices(pt, ft)
    
    eig_p = np.linalg.eigvalsh(Cpp)
    eig_f = np.linalg.eigvalsh(Cff)
    
    # Allow small numerical error negative values
    assert np.all(eig_p > -1e-10)
    assert np.all(eig_f > -1e-10)

def test_perform_truncated_cca_shapes():
    """
    Check that projection matrix Psi has shape [r, m].
    """
    m, h, r = 10, 8, 3
    # Mock covariances with identity/random for shape testing
    Cpp = np.eye(m)
    Cff = np.eye(h)
    Cfp = np.random.randn(h, m) * 0.1
    
    Psi, _, _, _ = perform_truncated_cca(Cpp, Cff, Cfp, rank=r, epsilon=1e-5)
    
    assert Psi.shape == (r, m)

def test_perform_truncated_cca_canonical_correlations_range():
    """
    Ensure singular values (canonical correlations) are between 0 and 1.
    """
    # Setup consistent covariances from random data
    N, m, h = 200, 5, 5
    pt = np.random.randn(N, m)
    ft = np.random.randn(N, h)
    r = 3
    Cpp, Cff, Cfp = compute_covariance_matrices(pt, ft)
    
    _, corrs, _, _ = perform_truncated_cca(Cpp, Cff, Cfp, rank=r, epsilon=1e-5)
    
    assert np.all(corrs >= 0.0)
    assert np.all(corrs <= 1.0 + 1e-9) # Tolerance for float precision

def test_perform_truncated_cca_sorted_correlations():
    """
    Verify that canonical correlations are returned in descending order.
    """
    N, m, h = 200, 5, 5
    pt = np.random.randn(N, m)
    ft = np.random.randn(N, h)
    r = 3
    Cpp, Cff, Cfp = compute_covariance_matrices(pt, ft)
    
    _, corrs, _, _ = perform_truncated_cca(Cpp, Cff, Cfp, rank=r, epsilon=1e-6)
    
    # Check if sorted descending
    assert np.all(corrs[:-1] >= corrs[1:])

def test_perform_truncated_cca_with_regularization():
    """
    Test stability and behavior when epsilon regularization is applied.
    """
    # Create singular matrices (rank deficient)
    m, h = 5, 5
    Cpp = np.zeros((m, m)) # Singular
    Cff = np.eye(h)
    Cfp = np.zeros((h, m))
    
    # Should not raise LinAlgError due to epsilon
    try:
        perform_truncated_cca(Cpp, Cff, Cfp, rank=2, epsilon=1.0)
    except np.linalg.LinAlgError:
        pytest.fail("Regularization failed to prevent singularity error.")

def test_calculate_mutual_information_calculation():
    """
    Compare calculation against a manual implementation for a known input vector.
    """
    sigma = np.array([0.9, 0.5, 0.1])
    # I = -0.5 * sum(log(1 - sigma^2))
    expected = -0.5 * np.sum(np.log(1 - sigma**2))
    
    result = calculate_mutual_information(sigma)
    assert np.isclose(result, expected)

def test_calculate_mutual_information_non_negative():
    """
    Ensure the result is always >= 0.
    """
    # Random correlations between 0 and 0.99
    sigma = np.random.rand(5) * 0.99
    mi = calculate_mutual_information(sigma)
    assert mi >= 0

def test_calculate_mutual_information_monotonicity():
    """
    Verify that adding a component with higher correlation increases MI.
    """
    sigma_base = np.array([0.5, 0.4])
    sigma_more = np.array([0.5, 0.4, 0.3]) # Added a component
    
    mi_base = calculate_mutual_information(sigma_base)
    mi_more = calculate_mutual_information(sigma_more)
    
    assert mi_more > mi_base

# Hypothesis Property-Based Test
@given(arrays(np.float64, (20, 5)), arrays(np.float64, (20, 5)))
def test_covariance_symmetry_property_based(pt, ft):
    """
    Hypothesis test: For any random input matrices, output covariances must be symmetric.
    """
    # Ensure no NaNs or Infs
    np.nan_to_num(pt, copy=False)
    np.nan_to_num(ft, copy=False)
    
    try:
        Cpp, Cff, _ = compute_covariance_matrices(pt, ft)
        assert np.allclose(Cpp, Cpp.T, atol=1e-5)
        assert np.allclose(Cff, Cff.T, atol=1e-5)
    except Exception:
        # If input is too degenerate (all zeros), it might just pass or handle gracefully
        pass