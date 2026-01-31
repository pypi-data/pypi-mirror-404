"""Data generating process for linear models.

Generates synthetic data from a linear model with known parameters:
    y = X @ beta + epsilon
    epsilon ~ N(0, sigma^2)
"""

from collections.abc import Sequence
from typing import Literal

import jax
import jax.numpy as jnp
import numpy as np
import polars as pl

# Type alias for array-like inputs
ArrayLike = Sequence[float] | np.ndarray | jnp.ndarray

__all__ = ["generate_lm_data"]


def generate_lm_data(
    n: int,
    beta: ArrayLike,
    sigma: float = 1.0,
    x_type: Literal["gaussian", "uniform", "binary"] = "gaussian",
    seed: int | None = None,
) -> tuple[pl.DataFrame, dict]:
    """Generate linear model data with known parameters.

    Creates synthetic data from the model:
        y = intercept + beta[1]*x1 + beta[2]*x2 + ... + epsilon
        epsilon ~ N(0, sigma^2)

    Args:
        n: Number of observations to generate.
        beta: True coefficients as [intercept, slope1, slope2, ...].
            Length determines number of predictors (len(beta) - 1).
        sigma: Residual standard deviation (default 1.0).
        x_type: Distribution for predictors:
            - "gaussian": Standard normal N(0, 1)
            - "uniform": Uniform on [0, 1]
            - "binary": Bernoulli(0.5), values in {0, 1}
        seed: Random seed for reproducibility. If None, uses random state.

    Returns:
        A tuple of (data, true_params) where:
        - data: polars DataFrame with columns y, x1, x2, ...
        - true_params: dict with keys "beta" (array) and "sigma" (float)

    Examples:
        >>> data, params = generate_lm_data(n=100, beta=[1.0, 2.0], sigma=0.5)
        >>> data.shape
        (100, 2)
        >>> params["beta"]
        array([1., 2.])
    """
    beta = jnp.asarray(beta, dtype=jnp.float64)
    n_predictors = len(beta) - 1

    if n_predictors < 1:
        raise ValueError("beta must have at least 2 elements [intercept, slope]")

    if sigma <= 0:
        raise ValueError("sigma must be positive")

    # Initialize random key
    resolved_seed: int = (
        seed if seed is not None else int(np.random.default_rng().integers(0, 2**31))
    )
    key = jax.random.PRNGKey(resolved_seed)

    # Split keys for X and epsilon
    key_x, key_eps = jax.random.split(key)

    # Generate predictors based on x_type
    if x_type == "gaussian":
        X = jax.random.normal(key_x, shape=(n, n_predictors))
    elif x_type == "uniform":
        X = jax.random.uniform(key_x, shape=(n, n_predictors))
    elif x_type == "binary":
        X = jax.random.bernoulli(key_x, p=0.5, shape=(n, n_predictors)).astype(
            jnp.float64
        )
    else:
        raise ValueError(
            f"Unknown x_type: {x_type}. Use 'gaussian', 'uniform', 'binary'"
        )

    # Build design matrix with intercept
    intercept = jnp.ones((n, 1))
    X_full = jnp.hstack([intercept, X])

    # Generate response: y = X @ beta + epsilon
    epsilon = jax.random.normal(key_eps, shape=(n,)) * sigma
    y = X_full @ beta + epsilon

    # Build DataFrame
    data_dict = {"y": np.asarray(y)}
    for i in range(n_predictors):
        data_dict[f"x{i + 1}"] = np.asarray(X[:, i])

    data = pl.DataFrame(data_dict)

    true_params = {
        "beta": np.asarray(beta),
        "sigma": float(sigma),
    }

    return data, true_params
