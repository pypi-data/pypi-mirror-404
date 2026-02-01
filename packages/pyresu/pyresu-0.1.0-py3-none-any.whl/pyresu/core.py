import numpy as np
from typing import Tuple

def compute_covariance_matrices(
    past_lag_vector: np.ndarray,
    future_lag_vector: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Computes the covariance matrices C_pp, C_ff, C_fp.
    """
    N = past_lag_vector.shape[0]
    if N < 2:
        raise ValueError("Batch size must be > 1 to compute covariance.")

    cov_past_past = (past_lag_vector.T @ past_lag_vector) / (N - 1)
    cov_future_future = (future_lag_vector.T @ future_lag_vector) / (N - 1)
    cov_future_past = (future_lag_vector.T @ past_lag_vector) / (N - 1)

    return cov_past_past, cov_future_future, cov_future_past

def _matrix_pow(matrix: np.ndarray, power: float, epsilon: float = 1e-6) -> np.ndarray:
    dim = matrix.shape[0]
    reg_matrix = matrix + epsilon * np.eye(dim)
    evals, evecs = np.linalg.eigh(reg_matrix)
    evals = np.maximum(evals, 1e-9)
    pow_evals = np.diag(evals ** power)
    return evecs @ pow_evals @ evecs.T

def perform_truncated_cca(
    cov_past_past: np.ndarray,
    cov_future_future: np.ndarray,
    cov_future_past: np.ndarray,
    rank: int,
    epsilon: float = 1e-6
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Solves CCA and returns (Psi, correlations, U_r, V_r_T).
    Note: Updated 'subspace_rank' to 'rank' to match tests.
    """
    cpp_inv_sqrt = _matrix_pow(cov_past_past, -0.5, epsilon)
    cff_inv_sqrt = _matrix_pow(cov_future_future, -0.5, epsilon)

    # K = C_ff^{-1/2} C_fp C_pp^{-1/2}
    whitened_cross_cov = cff_inv_sqrt @ cov_future_past @ cpp_inv_sqrt
    u, s, vh = np.linalg.svd(whitened_cross_cov, full_matrices=False)

    r = min(rank, len(s))
    u_r = u[:, :r]
    s_r = s[:r]
    vr_t = vh[:r, :] 

    projection_matrix = vr_t @ cpp_inv_sqrt

    return projection_matrix, s_r, u_r, vr_t

def calculate_mutual_information(canonical_correlations: np.ndarray) -> float:
    sigma_sq = np.clip(canonical_correlations ** 2, 0, 1.0 - 1e-9)
    return -0.5 * np.sum(np.log(1.0 - sigma_sq))