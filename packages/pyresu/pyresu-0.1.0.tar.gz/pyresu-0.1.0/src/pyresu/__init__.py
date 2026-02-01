"""
ReSU: Rectified Spectral Units implementation based on Qin et al. (2025).
"""

from .core import (
    compute_covariance_matrices,
    perform_truncated_cca,
    calculate_mutual_information
)
from .preprocessing import (
    construct_lag_vectors,
    center_lag_vectors
)
from .models import ReSUCell
from .simulation import (
    generate_ou_process,
    generate_gp_data,
    rational_quadratic_kernel
)

__all__ = [
    "compute_covariance_matrices",
    "perform_truncated_cca",
    "calculate_mutual_information",
    "construct_lag_vectors",
    "center_lag_vectors",
    "ReSUCell",
    "generate_ou_process",
    "generate_gp_data",
    "rational_quadratic_kernel",
]