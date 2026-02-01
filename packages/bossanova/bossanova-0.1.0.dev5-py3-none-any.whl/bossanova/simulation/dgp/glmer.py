"""Data generating process for generalized linear mixed models.

Generates synthetic data from GLMMs with known parameters:
    g(E[y|b]) = X @ beta + Z @ b
    b ~ N(0, G)

where g is the link function and G is the random effects covariance.
"""

from collections.abc import Sequence
from typing import Literal

import jax
import jax.numpy as jnp
import numpy as np
import polars as pl
from jax.scipy.special import expit

ArrayLike = Sequence[float] | np.ndarray | jnp.ndarray
FamilyType = Literal["binomial", "poisson"]

__all__ = ["generate_glmer_data"]


def generate_glmer_data(
    n_obs: int,
    n_groups: int,
    beta: ArrayLike,
    theta: ArrayLike,
    family: FamilyType = "binomial",
    re_structure: Literal["intercept", "slope", "both"] = "intercept",
    obs_per_group: int | None = None,
    seed: int | None = None,
) -> tuple[pl.DataFrame, dict]:
    """Generate GLMM data with known parameters.

    Creates synthetic data from the model:
        g(E[y_ij|b_i]) = X_ij @ beta + Z_ij @ b_i
        b_i ~ N(0, G)

    where g is the canonical link function for the family.

    Args:
        n_obs: Total number of observations.
        n_groups: Number of groups/clusters.
        beta: Fixed effect coefficients [intercept, slope1, ...].
        theta: Random effect parameters (see generate_lmer_data for details).
        family: Response distribution:
            - "binomial": Binary outcomes (0/1) with logit link
            - "poisson": Count data with log link
        re_structure: Random effects structure:
            - "intercept": Random intercepts only
            - "slope": Random slopes only
            - "both": Random intercepts and slopes
        obs_per_group: Observations per group. If None, uses n_obs // n_groups.
        seed: Random seed for reproducibility.

    Returns:
        A tuple of (data, true_params) where:
        - data: DataFrame with columns y, x1, group
        - true_params: dict with beta, theta, family, and ranef

    Examples:
        >>> # Binomial GLMM with random intercepts
        >>> data, params = generate_glmer_data(
        ...     n_obs=400, n_groups=40,
        ...     beta=[0.0, 1.0],
        ...     theta=[0.5],  # SD of random intercepts
        ...     family="binomial",
        ... )
    """
    beta = jnp.asarray(beta, dtype=jnp.float64)
    theta = jnp.asarray(theta, dtype=jnp.float64)

    if len(beta) < 2:
        raise ValueError("beta must have at least 2 elements [intercept, slope]")

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
    key_x, key_b, key_y = jax.random.split(key, 3)

    # Generate group assignments (balanced design)
    groups = jnp.repeat(jnp.arange(n_groups), obs_per_group)

    # Generate fixed effect predictors
    n_fixed_predictors = len(beta) - 1
    X = jax.random.normal(key_x, shape=(actual_n_obs, n_fixed_predictors))

    # Build fixed effects design matrix
    intercept = jnp.ones((actual_n_obs, 1))
    X_full = jnp.hstack([intercept, X])

    # Generate random effects based on structure
    if re_structure == "intercept":
        if len(theta) < 1:
            raise ValueError("theta must have at least 1 element for intercept RE")
        sigma_int = float(theta[0])
        b_intercepts = jax.random.normal(key_b, shape=(n_groups,)) * sigma_int
        b_slopes = jnp.zeros(n_groups)
        ranef = {"intercept": np.asarray(b_intercepts)}

    elif re_structure == "slope":
        if len(theta) < 1:
            raise ValueError("theta must have at least 1 element for slope RE")
        sigma_slope = float(theta[0])
        b_intercepts = jnp.zeros(n_groups)
        b_slopes = jax.random.normal(key_b, shape=(n_groups,)) * sigma_slope
        ranef = {"slope": np.asarray(b_slopes)}

    else:  # "both"
        if len(theta) < 2:
            raise ValueError(
                "theta must have at least 2 elements for intercept+slope RE"
            )
        sigma_int = float(theta[0])
        sigma_slope = float(theta[1])
        corr = float(theta[2]) if len(theta) > 2 else 0.0

        cov = jnp.array(
            [
                [sigma_int**2, corr * sigma_int * sigma_slope],
                [corr * sigma_int * sigma_slope, sigma_slope**2],
            ]
        )

        key_b1, _ = jax.random.split(key_b)
        L = jnp.linalg.cholesky(cov + 1e-10 * jnp.eye(2))
        z = jax.random.normal(key_b1, shape=(n_groups, 2))
        b = z @ L.T
        b_intercepts = b[:, 0]
        b_slopes = b[:, 1]
        ranef = {
            "intercept": np.asarray(b_intercepts),
            "slope": np.asarray(b_slopes),
        }

    # Compute random effects contribution
    re_contribution = b_intercepts[groups]
    if re_structure in ["slope", "both"]:
        re_contribution = re_contribution + b_slopes[groups] * X[:, 0]

    # Compute linear predictor
    eta = X_full @ beta + re_contribution

    # Generate response based on family
    if family == "binomial":
        mu = expit(eta)
        y = jax.random.bernoulli(key_y, p=mu).astype(jnp.float64)
    elif family == "poisson":
        mu = jnp.exp(eta)
        # Clip mu to avoid extreme values
        mu = jnp.clip(mu, 0, 100)
        y = jnp.asarray(np.random.default_rng(int(key_y[0])).poisson(np.asarray(mu)))
    else:
        raise ValueError(f"Unknown family: {family}")

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
        "family": family,
        "ranef": ranef,
        "re_structure": re_structure,
    }

    return data, true_params
