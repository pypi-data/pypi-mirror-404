import numpy as np
from typing import Tuple

def construct_lag_vectors(
    observed_signal: np.ndarray,
    memory_horizon: int,
    prediction_horizon: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Ref: Pg 3, Eq 3
    Constructs the past (p_t) and future (f_t) lag vectors from the observed time series.

    According to Eq 3:
    p_t = [y_t, y_{t-1}, ..., y_{t-m+1}]^T (Past includes current time t)
    f_t = [y_{t+1}, y_{t+2}, ..., y_{t+h}]^T (Future starts at t+1)

    Args:
        observed_signal: The accessible input data (y_t). Shape [T] or [T, Channels].
        memory_horizon: Length of the past lag vector (m).
        prediction_horizon: Length of the future lag vector (h).

    Returns:
        past_lag_matrix: Collection of past_lag_vector p_t. Shape [N_samples, m * Channels].
        future_lag_matrix: Collection of future_lag_vector f_t. Shape [N_samples, h * Channels].
    """
    # Ensure signal is at least 2D [T, Channels]
    if observed_signal.ndim == 1:
        observed_signal = observed_signal[:, np.newaxis]
    
    T, C = observed_signal.shape
    
    # Valid indices range
    # We need history back to t - (m - 1) >= 0  => t >= m - 1
    # We need future forward to t + h < T       => t <= T - h - 1
    
    start_idx = memory_horizon - 1
    end_idx = T - prediction_horizon
    
    if start_idx >= end_idx:
        raise ValueError("Signal too short for the requested memory and prediction horizons.")

    past_vectors = []
    future_vectors = []

    for t in range(start_idx, end_idx):
        # p_t: [y_t, y_{t-1}, ..., y_{t-m+1}]
        # Using stride trick or slice. Slice: signal[t - m + 1 : t + 1] -> reverse
        p_slice = observed_signal[t - memory_horizon + 1 : t + 1]
        p_vec = p_slice[::-1].flatten() # Reverse to get [t, t-1, ...]
        
        # f_t: [y_{t+1}, ..., y_{t+h}]
        f_slice = observed_signal[t + 1 : t + prediction_horizon + 1]
        f_vec = f_slice.flatten()
        
        past_vectors.append(p_vec)
        future_vectors.append(f_vec)

    return np.array(past_vectors), np.array(future_vectors)

def center_lag_vectors(
    lag_matrix: np.ndarray
) -> np.ndarray:
    """
    Ref: Pg 3, Eq 3, Para 3
    Ensures lag vectors are centered (mean subtracted) as required for covariance calculation.
    
    The paper mentions "centered p_t and f_t".

    Args:
        lag_matrix: Matrix of lag vectors (past or future). Shape [N, D].

    Returns:
        centered_matrix: The input matrix with column-wise mean subtracted.
    """
    mean_vec = np.mean(lag_matrix, axis=0)
    return lag_matrix - mean_vec