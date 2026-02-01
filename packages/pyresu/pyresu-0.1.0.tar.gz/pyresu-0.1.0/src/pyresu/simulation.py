import numpy as np
from typing import Callable, Tuple

def rational_quadratic_kernel(
    t1: float,
    t2: float,
    rational_quadratic_alpha: float = 1.0,
    length_scale: float = 1.0
) -> float:
    diff_sq = (t1 - t2) ** 2
    denominator = 2 * rational_quadratic_alpha * (length_scale ** 2)
    base = 1 + diff_sq / denominator
    return base ** (-rational_quadratic_alpha)

def generate_ou_process(
    T: int,
    hidden_dim: int = 1,
    process_noise_std: float = 1.0,
    obs_noise_std: float = 0.05
) -> Tuple[np.ndarray, np.ndarray]:
    # Match argument names expected by tests (T, hidden_dim, obs_noise_std)
    A_rand = np.random.randn(hidden_dim, hidden_dim)
    U, S, Vh = np.linalg.svd(A_rand)
    S = np.clip(S, 0, 0.95)
    A = U @ np.diag(S) @ Vh
    
    B = np.random.randn(hidden_dim, hidden_dim)
    C = np.random.randn(1, hidden_dim)

    x_t = np.zeros(hidden_dim)
    latent_states, observations = [], []
    
    v_noise = np.random.normal(0, process_noise_std, (T, hidden_dim))
    w_noise = np.random.normal(0, obs_noise_std, (T, 1))

    for t in range(T):
        y_t = C @ x_t + w_noise[t]
        observations.append(y_t)
        latent_states.append(x_t)
        x_t = A @ x_t + B @ v_noise[t]
        
    return np.array(latent_states), np.array(observations)

def generate_gp_data(
    time_steps: int,
    kernel_function: Callable[[float, float], float] = rational_quadratic_kernel,
    noise_std_dev: float = 0.1
) -> np.ndarray:
    # Ensure noise_std_dev matches the parameter logic in tests
    times = np.arange(time_steps).reshape(-1, 1)
    K = np.zeros((time_steps, time_steps))
    for i in range(time_steps):
        for j in range(i, time_steps):
            val = kernel_function(times[i, 0], times[j, 0])
            K[i, j] = K[j, i] = val
            
    K += 1e-6 * np.eye(time_steps)
    L = np.linalg.cholesky(K)
    z = np.random.normal(0, 1, (time_steps,))
    signal = L @ z
    observed_signal = signal + np.random.normal(0, noise_std_dev, (time_steps,))
    return observed_signal.reshape(-1, 1)