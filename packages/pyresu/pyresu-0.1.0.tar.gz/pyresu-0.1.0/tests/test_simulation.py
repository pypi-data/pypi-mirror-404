import numpy as np
import pytest
from pyresu.simulation import rational_quadratic_kernel, generate_ou_process, generate_gp_data

def test_rational_quadratic_kernel_symmetry():
    """
    Verify k(t1, t2) == k(t2, t1).
    """
    t1 = 1.5
    t2 = 3.2
    k12 = rational_quadratic_kernel(t1, t2)
    k21 = rational_quadratic_kernel(t2, t1)
    assert np.isclose(k12, k21)

def test_rational_quadratic_kernel_maximum():
    """
    Verify that k(t, t) is the maximum value (usually 1.0 for base kernels).
    """
    t = 2.0
    t_diff = 2.5
    k_diag = rational_quadratic_kernel(t, t)
    k_off = rational_quadratic_kernel(t, t_diff)
    
    assert k_diag >= k_off
    # Assuming standard normalization k(x,x)=1
    assert np.isclose(k_diag, 1.0)

def test_rational_quadratic_kernel_parameters():
    """
    Test that changing alpha and length_scale affects the decay correctly.
    """
    t1, t2 = 0, 1
    # Short length scale -> fast decay -> lower correlation
    k_short = rational_quadratic_kernel(t1, t2, length_scale=0.1)
    # Long length scale -> slow decay -> higher correlation
    k_long = rational_quadratic_kernel(t1, t2, length_scale=10.0)
    
    assert k_long > k_short

def test_generate_ou_process_shape():
    """
    Verify output shapes for latent state [T, n] and observation [T, 1].
    """
    T = 100
    n = 2
    latent, obs = generate_ou_process(T=T, hidden_dim=n)
    
    assert latent.shape == (T, n)
    assert obs.shape == (T, 1)

def test_generate_ou_process_stability():
    """
    Ensure the process does not produce NaN or Inf values over long durations.
    """
    T = 1000
    latent, obs = generate_ou_process(T=T)
    assert np.all(np.isfinite(latent))
    assert np.all(np.isfinite(obs))

def test_generate_ou_process_noise_levels():
    """
    Check that process noise and observation noise parameters affect output variance.
    """
    T = 1000
    # High noise
    _, obs_noisy = generate_ou_process(T=T, obs_noise_std=5.0)
    # Low noise
    _, obs_quiet = generate_ou_process(T=T, obs_noise_std=0.01)
    
    assert np.var(obs_noisy) > np.var(obs_quiet)

def test_generate_gp_data_shape():
    """
    Verify output shape matches requested time_steps.
    """
    T = 150
    data = generate_gp_data(time_steps=T)
    # Typically returns 1D array or (T,1)
    assert len(data) == T

def test_generate_gp_data_noise_addition():
    """
    Verify that observation noise is actually added to the clean GP sample.
    """
    T = 100
    
    data_clean = generate_gp_data(time_steps=T, noise_std_dev=0.0)
    data_noisy = generate_gp_data(time_steps=T, noise_std_dev=10.0)
    
    # Variance of noisy signal should be higher (statistically)
    assert np.var(data_noisy) > np.var(data_clean)
    
    # FIX: Correct keyword argument from 'noise_std' to 'noise_std_dev'
    np.random.seed(42)
    d1 = generate_gp_data(time_steps=T, noise_std_dev=0.0)
    np.random.seed(42)
    d2 = generate_gp_data(time_steps=T, noise_std_dev=1.0)
    
    # d2 should differ from d1
    assert not np.allclose(d1, d2)