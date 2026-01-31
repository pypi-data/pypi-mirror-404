"""Data generating process for linear mixed models.

Generates synthetic data from LMMs with known parameters:
    y = X @ beta + Z @ b + epsilon
    b ~ N(0, G)
    epsilon ~ N(0, sigma^2 * I)

where G is the random effects covariance matrix parameterized by theta.
"""

from collections.abc import Sequence
from typing import Literal

import jax
import jax.numpy as jnp
import numpy as np
import polars as pl

ArrayLike = Sequence[float] | np.ndarray | jnp.ndarray

__all__ = ["generate_lmer_data"]


def generate_lmer_data(
    n_obs: int,
    n_groups: int,
    beta: ArrayLike,
    theta: ArrayLike,
    sigma: float = 1.0,
    re_structure: Literal["intercept", "slope", "both"] = "intercept",
    obs_per_group: int | None = None,
    seed: int | None = None,
) -> tuple[pl.DataFrame, dict]:
    """Generate linear mixed model data with known parameters.

    Creates synthetic data from the model:
        y_ij = X_ij @ beta + Z_ij @ b_i + epsilon_ij
        b_i ~ N(0, G)
        epsilon_ij ~ N(0, sigma^2)

    Args:
        n_obs: Total number of observations. If obs_per_group is None,
            observations are distributed evenly across groups.
        n_groups: Number of groups/clusters.
        beta: Fixed effect coefficients [intercept, slope1, ...].
        theta: Random effect parameters. Interpretation depends on re_structure:
            - "intercept": [sigma_intercept] - SD of random intercepts
            - "slope": [sigma_slope] - SD of random slopes (no random intercept)
            - "both": [sigma_intercept, sigma_slope, corr] or [sigma_int, sigma_slope]
              If length 2, assumes uncorrelated (corr=0).
        sigma: Residual standard deviation (default 1.0).
        re_structure: Random effects structure:
            - "intercept": Random intercepts only (1|group)
            - "slope": Random slopes only (0 + x1|group)
            - "both": Random intercepts and slopes (1 + x1|group)
        obs_per_group: Observations per group. If None, uses n_obs // n_groups.
        seed: Random seed for reproducibility.

    Returns:
        A tuple of (data, true_params) where:
        - data: DataFrame with columns y, x1, group
        - true_params: dict with beta, theta, sigma, and ranef (actual random effects)

    Examples:
        >>> # Random intercepts model
        >>> data, params = generate_lmer_data(
        ...     n_obs=200, n_groups=20,
        ...     beta=[1.0, 0.5],
        ...     theta=[0.5],  # SD of random intercepts
        ...     sigma=1.0,
        ... )
    """
    beta = jnp.asarray(beta, dtype=jnp.float64)
    theta = jnp.asarray(theta, dtype=jnp.float64)

    if len(beta) < 2:
        raise ValueError("beta must have at least 2 elements [intercept, slope]")

    if sigma <= 0:
        raise ValueError("sigma must be positive")

    # Determine observations per group
    if obs_per_group is None:
        obs_per_group = n_obs // n_groups
    actual_n_obs = obs_per_group * n_groups

    # Initialize random key
    resolved_seed: int = (
        seed if seed is not None else int(np.random.default_rng().integers(0, 2**31))
    )
    key = jax.random.PRNGKey(resolved_seed)

    # Split keys
    key_x, key_b, key_eps = jax.random.split(key, 3)

    # Generate group assignments (balanced design)
    groups = jnp.repeat(jnp.arange(n_groups), obs_per_group)

    # Generate fixed effect predictors (x1)
    n_fixed_predictors = len(beta) - 1
    X = jax.random.normal(key_x, shape=(actual_n_obs, n_fixed_predictors))

    # Build fixed effects design matrix
    intercept = jnp.ones((actual_n_obs, 1))
    X_full = jnp.hstack([intercept, X])

    # Generate random effects based on structure
    if re_structure == "intercept":
        # Random intercepts only: b_i ~ N(0, theta[0]^2)
        if len(theta) < 1:
            raise ValueError("theta must have at least 1 element for intercept RE")
        sigma_int = float(theta[0])
        b_intercepts = jax.random.normal(key_b, shape=(n_groups,)) * sigma_int
        b_slopes = jnp.zeros(n_groups)
        ranef = {"intercept": np.asarray(b_intercepts)}

    elif re_structure == "slope":
        # Random slopes only (no random intercept)
        if len(theta) < 1:
            raise ValueError("theta must have at least 1 element for slope RE")
        sigma_slope = float(theta[0])
        b_intercepts = jnp.zeros(n_groups)
        b_slopes = jax.random.normal(key_b, shape=(n_groups,)) * sigma_slope
        ranef = {"slope": np.asarray(b_slopes)}

    else:  # "both"
        # Random intercepts and slopes
        if len(theta) < 2:
            raise ValueError(
                "theta must have at least 2 elements for intercept+slope RE"
            )
        sigma_int = float(theta[0])
        sigma_slope = float(theta[1])
        corr = float(theta[2]) if len(theta) > 2 else 0.0

        # Build covariance matrix
        cov = jnp.array(
            [
                [sigma_int**2, corr * sigma_int * sigma_slope],
                [corr * sigma_int * sigma_slope, sigma_slope**2],
            ]
        )

        # Generate correlated random effects
        key_b1, key_b2 = jax.random.split(key_b)
        # Use Cholesky decomposition for correlated sampling
        L = jnp.linalg.cholesky(cov + 1e-10 * jnp.eye(2))
        z = jax.random.normal(key_b1, shape=(n_groups, 2))
        b = z @ L.T
        b_intercepts = b[:, 0]
        b_slopes = b[:, 1]
        ranef = {
            "intercept": np.asarray(b_intercepts),
            "slope": np.asarray(b_slopes),
        }

    # Compute random effects contribution for each observation
    re_contribution = b_intercepts[groups]
    if re_structure in ["slope", "both"]:
        # Add slope contribution: b_slope_i * x1_ij
        re_contribution = re_contribution + b_slopes[groups] * X[:, 0]

    # Generate response
    fixed_part = X_full @ beta
    epsilon = jax.random.normal(key_eps, shape=(actual_n_obs,)) * sigma
    y = fixed_part + re_contribution + epsilon

    # Build DataFrame
    data_dict = {
        "y": np.asarray(y),
        "group": np.asarray(groups),
    }
    for i in range(n_fixed_predictors):
        data_dict[f"x{i + 1}"] = np.asarray(X[:, i])

    data = pl.DataFrame(data_dict)

    true_params = {
        "beta": np.asarray(beta),
        "theta": np.asarray(theta),
        "sigma": float(sigma),
        "ranef": ranef,
        "re_structure": re_structure,
    }

    return data, true_params
