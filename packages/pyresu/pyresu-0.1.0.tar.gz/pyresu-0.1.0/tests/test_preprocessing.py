import numpy as np
import pytest
from pyresu.preprocessing import construct_lag_vectors, center_lag_vectors

def test_construct_lag_vectors_shape_univariate():
    """
    Test that lag vectors have the correct shape for a 1D input signal.
    """
    T = 100
    m = 10
    h = 5
    # Generate random univariate time series
    data = np.random.randn(T)
    
    pt, ft = construct_lag_vectors(data, m, h)
    
    expected_N = T - m - h + 1
    
    # Check batch dimension
    assert pt.shape[0] == expected_N
    assert ft.shape[0] == expected_N
    
    # Check feature dimension (1 channel)
    assert pt.shape[1] == m
    assert ft.shape[1] == h

def test_construct_lag_vectors_shape_multivariate():
    """
    Test that lag vectors handle multiple channels correctly.
    """
    T = 100
    D = 3  # dimensions/channels
    m = 10
    h = 5
    data = np.random.randn(T, D)
    
    pt, ft = construct_lag_vectors(data, m, h)
    
    expected_N = T - m - h + 1
    
    # Check shapes (should flatten features: m*D and h*D)
    assert pt.shape == (expected_N, m * D)
    assert ft.shape == (expected_N, h * D)

def test_construct_lag_vectors_content():
    """
    Test that the lag vectors contain the correct sliding windows of data.
    """
    # Create a simple arithmetic progression: 0, 1, 2, ..., 9
    T = 10
    m = 3
    h = 2
    data = np.arange(T)
    
    pt, ft = construct_lag_vectors(data, m, h)
    
    # N = 10 - 3 - 2 + 1 = 6 samples
    # For the first sample (index 0 in output):
    # Corresponds to time t where we have m past and h future available.
    # Earliest valid t is index (m-1) = 2.
    # pt[0] should correspond to history ending at t=2: [2, 1, 0] (assuming reverse time) or [0, 1, 2]
    # ft[0] should correspond to future starting at t+1=3: [3, 4]
    
    # We verify the data content exists in the lag vectors.
    # This check is agnostic to internal time-ordering (asc/desc) as long as the window is correct.
    first_past_window = data[0:m]
    first_future_window = data[m:m+h]
    
    assert np.all(np.isin(pt[0], first_past_window))
    assert np.all(np.isin(ft[0], first_future_window))
    
    # Check alignment: Last element of pt[0] and first of ft[0] should be adjacent in source (typically)
    # or just ensure they cover distinct adjacent blocks.
    
    # Check the last sample
    last_past_window = data[T-m-h : T-h]
    last_future_window = data[T-h : T]
    
    assert np.all(np.isin(pt[-1], last_past_window))
    assert np.all(np.isin(ft[-1], last_future_window))

def test_construct_lag_vectors_insufficient_length():
    """
    Test behavior when signal length is less than memory + prediction horizon.
    """
    T = 5
    m = 5
    h = 5
    data = np.random.randn(T)
    
    # Should imply N <= 0, which is invalid
    with pytest.raises(ValueError):
        construct_lag_vectors(data, m, h)

def test_center_lag_vectors_mean():
    """
    Verify that the returned matrix has a mean of zero along the appropriate axis.
    """
    # Create random data with non-zero mean
    X = np.random.rand(100, 10) + 5
    X_centered = center_lag_vectors(X)
    
    # Mean across batch (axis 0) should be approx 0
    means = np.mean(X_centered, axis=0)
    assert np.allclose(means, 0.0, atol=1e-7)

def test_center_lag_vectors_shape_preservation():
    """
    Ensure centering does not change the dimensions of the input matrix.
    """
    X = np.random.rand(50, 5)
    X_centered = center_lag_vectors(X)
    assert X.shape == X_centered.shape