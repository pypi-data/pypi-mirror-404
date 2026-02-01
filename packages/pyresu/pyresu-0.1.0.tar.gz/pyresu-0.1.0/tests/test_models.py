import numpy as np
import pytest
from pyresu.models import ReSUCell
from pyresu.preprocessing import construct_lag_vectors

# Mock data fixture
@pytest.fixture
def sample_data():
    T = 200
    return np.random.randn(T)

def test_resu_cell_initialization():
    """
    Test that ReSUCell initializes with correct parameters and None weights.
    """
    m, h, r = 10, 5, 2
    cell = ReSUCell(memory_horizon=m, prediction_horizon=h, rank=r)
    
    assert cell.memory_horizon == m
    assert cell.prediction_horizon == h
    assert cell.rank == r
    # Weights should be None before fitting
    assert not hasattr(cell, "projection_matrix") or cell.projection_matrix is None

def test_resu_cell_fit_sets_projection_matrix(sample_data):
    """
    Verify that fit() populates the projection_matrix attribute.
    """
    m, h, r = 10, 5, 2
    cell = ReSUCell(memory_horizon=m, prediction_horizon=h, rank=r)
    # Prepare lag vectors from sample_data
    pt, ft = construct_lag_vectors(sample_data, m, h)
    cell.fit(pt, ft)
    assert cell.projection_matrix is not None

def test_resu_cell_fit_sets_inverse_sqrt_covariance(sample_data):
    """
    Verify that fit() computes and stores the whitening matrix (or related stats).
    """
    m, h, r = 10, 5, 2
    cell = ReSUCell(memory_horizon=m, prediction_horizon=h, rank=r)
    
    # FIX: Construct lag vectors before calling fit
    pt, ft = construct_lag_vectors(sample_data, m, h)
    cell.fit(pt, ft)
    
    # Depending on implementation details, this might be stored. 
    assert hasattr(cell, "cov_past_past_inv_sqrt")

def test_resu_cell_compute_latent_representation_shape():
    """
    Check that the latent representation z_t has shape [Batch, r].
    """
    m, r = 10, 3
    batch_size = 50
    cell = ReSUCell(memory_horizon=m, prediction_horizon=5, rank=r)
    
    # Manually set projection matrix for test
    cell.projection_matrix = np.random.randn(r, m)
    
    # Input batch of past lag vectors
    pt = np.random.randn(batch_size, m)
    
    z = cell.compute_latent_representation(pt)
    assert z.shape == (batch_size, r)

def test_resu_cell_compute_latent_representation_values():
    """
    Verify linear projection logic against manual numpy operations.
    """
    m, r = 4, 2
    cell = ReSUCell(memory_horizon=m, prediction_horizon=2, rank=r)
    cell.projection_matrix = np.ones((r, m)) # Matrix of ones
    
    pt = np.array([[1, 1, 1, 1]]) # Sum is 4
    
    z = cell.compute_latent_representation(pt)
    
    # 1.0 * 1 + ... = 4.0
    expected = np.full((1, r), 4.0)
    assert np.allclose(z, expected)

def test_resu_cell_forward_rectification_logic_on():
    """
    Ensure ON output is max(projection, 0).
    """
    m, r = 2, 1
    cell = ReSUCell(memory_horizon=m, prediction_horizon=2, rank=r)
    cell.projection_matrix = np.array([[1, -1]]) # Projects [2, 0] -> 2, [0, 2] -> -2
    
    pt_positive_proj = np.array([[2, 0]]) # Proj = 2
    
    on_out, off_out = cell.forward(pt_positive_proj)
    
    assert on_out[0, 0] == 2.0
    assert off_out[0, 0] == 0.0

def test_resu_cell_forward_rectification_logic_off():
    """
    Ensure OFF output is max(-projection, 0).
    """
    m, r = 2, 1
    cell = ReSUCell(memory_horizon=m, prediction_horizon=2, rank=r)
    cell.projection_matrix = np.array([[1, -1]])
    
    pt_negative_proj = np.array([[0, 2]]) # Proj = -2
    
    on_out, off_out = cell.forward(pt_negative_proj)
    
    assert on_out[0, 0] == 0.0
    assert off_out[0, 0] == 2.0 # |-2| = 2

def test_resu_cell_forward_non_negative():
    """
    Property test: ON and OFF outputs should never be negative.
    """
    m, r = 5, 3
    cell = ReSUCell(memory_horizon=m, prediction_horizon=5, rank=r)
    cell.projection_matrix = np.random.randn(r, m)
    
    pt = np.random.randn(20, m)
    
    on_out, off_out = cell.forward(pt)
    
    assert np.all(on_out >= 0)
    assert np.all(off_out >= 0)

def test_resu_cell_forward_shape():
    """
    Check that forward pass returns two arrays of shape [Batch, r].
    """
    m, r = 10, 4
    batch = 15
    cell = ReSUCell(memory_horizon=m, prediction_horizon=5, rank=r)
    cell.projection_matrix = np.random.randn(r, m)
    
    pt = np.random.randn(batch, m)
    on_out, off_out = cell.forward(pt)
    
    assert on_out.shape == (batch, r)
    assert off_out.shape == (batch, r)