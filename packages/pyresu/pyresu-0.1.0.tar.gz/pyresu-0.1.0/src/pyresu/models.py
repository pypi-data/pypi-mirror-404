import numpy as np
from typing import Tuple
from .core import compute_covariance_matrices, perform_truncated_cca, _matrix_pow

class ReSUCell:
    def __init__(self, memory_horizon: int, prediction_horizon: int, rank: int):
        self.memory_horizon = memory_horizon
        self.prediction_horizon = prediction_horizon
        self.rank = rank
        self.projection_matrix = None  
        self.canonical_correlations = None
        self.cov_past_past_inv_sqrt = None # Stored for whitening analysis

    def fit(self, past_lag_vector: np.ndarray, future_lag_vector: np.ndarray) -> None:
        c_pp, c_ff, c_fp = compute_covariance_matrices(past_lag_vector, future_lag_vector)
        
        # Store whitening matrix for testing/diagnostics
        self.cov_past_past_inv_sqrt = _matrix_pow(c_pp, -0.5)
        
        psi, sigmas, _, _ = perform_truncated_cca(
            c_pp, c_ff, c_fp, 
            rank=self.rank
        )
        
        self.projection_matrix = psi
        self.canonical_correlations = sigmas

    def compute_latent_representation(self, past_lag_vector: np.ndarray) -> np.ndarray:
        if self.projection_matrix is None:
            raise RuntimeError("ReSUCell must be fit before calling compute_latent_representation.")
        return past_lag_vector @ self.projection_matrix.T

    def forward(self, past_lag_vector: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        z_t = self.compute_latent_representation(past_lag_vector)
        return np.maximum(z_t, 0), np.maximum(-z_t, 0)