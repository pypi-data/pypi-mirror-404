"""Data generating process for generalized linear models.

Generates synthetic data from GLMs with known parameters:
    g(E[y]) = X @ beta
where g is the link function.

Supported families:
- gaussian: identity link, y ~ N(mu, sigma^2)
- binomial: logit/probit link, y ~ Bernoulli(p)
- poisson: log link, y ~ Poisson(mu)
"""

from collections.abc import Sequence
from typing import Literal

import jax
import jax.numpy as jnp
import numpy as np
import polars as pl
from jax.scipy.special import expit  # logistic function

# Type alias for array-like inputs
ArrayLike = Sequence[float] | np.ndarray | jnp.ndarray
FamilyType = Literal["gaussian", "binomial", "poisson"]
LinkType = Literal["identity", "logit", "probit", "log"] | None

__all__ = ["generate_glm_data"]


def _get_canonical_link(
    family: FamilyType,
) -> Literal["identity", "logit", "log"]:
    """Return canonical link function for a family."""
    if family == "gaussian":
        return "identity"
    elif family == "binomial":
        return "logit"
    else:  # poisson
        return "log"


def _inverse_link(eta: jnp.ndarray, link: str) -> jnp.ndarray:
    """Apply inverse link function to get mu from eta."""
    if link == "identity":
        return eta
    elif link == "logit":
        return expit(eta)
    elif link == "probit":
        from jax.scipy.stats import norm

        return norm.cdf(eta)
    elif link == "log":
        return jnp.exp(eta)
    else:
        raise ValueError(f"Unknown link: {link}")


def generate_glm_data(
    n: int,
    beta: ArrayLike,
    family: FamilyType = "gaussian",
    link: LinkType = None,
    sigma: float = 1.0,
    x_type: Literal["gaussian", "uniform", "binary"] = "gaussian",
    seed: int | None = None,
) -> tuple[pl.DataFrame, dict]:
    """Generate GLM data with known parameters.

    Creates synthetic data from a generalized linear model:
        g(E[y]) = X @ beta
    where g is the link function determined by family/link.

    Args:
        n: Number of observations to generate.
        beta: True coefficients as [intercept, slope1, slope2, ...].
            Length determines number of predictors (len(beta) - 1).
        family: Response distribution:
            - "gaussian": Normal distribution (default)
            - "binomial": Binary outcomes (0/1)
            - "poisson": Count data
        link: Link function. If None, uses canonical link for family:
            - gaussian: "identity"
            - binomial: "logit"
            - poisson: "log"
        sigma: Residual SD (only used for gaussian family, default 1.0).
        x_type: Distribution for predictors:
            - "gaussian": Standard normal N(0, 1)
            - "uniform": Uniform on [0, 1]
            - "binary": Bernoulli(0.5), values in {0, 1}
        seed: Random seed for reproducibility. If None, uses random state.

    Returns:
        A tuple of (data, true_params) where:
        - data: polars DataFrame with columns y, x1, x2, ...
        - true_params: dict with keys "beta", "family", "link", and
            "sigma" (for gaussian)

    Examples:
        >>> # Logistic regression
        >>> data, params = generate_glm_data(
        ...     n=200, beta=[0.0, 1.5], family="binomial"
        ... )
        >>> data["y"].mean()  # Should be ~0.5 (balanced)

        >>> # Poisson regression
        >>> data, params = generate_glm_data(
        ...     n=100, beta=[1.0, 0.5], family="poisson"
        ... )
    """
    beta = jnp.asarray(beta, dtype=jnp.float64)
    n_predictors = len(beta) - 1

    if n_predictors < 1:
        raise ValueError("beta must have at least 2 elements [intercept, slope]")

    # Resolve link function
    resolved_link: str = link if link is not None else _get_canonical_link(family)

    # Validate sigma for gaussian
    if family == "gaussian" and sigma <= 0:
        raise ValueError("sigma must be positive for gaussian family")

    # Initialize random key
    resolved_seed: int = (
        seed if seed is not None else int(np.random.default_rng().integers(0, 2**31))
    )
    key = jax.random.PRNGKey(resolved_seed)

    # Split keys
    key_x, key_y = jax.random.split(key)

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
        raise ValueError(f"Unknown x_type: {x_type}")

    # Build design matrix with intercept
    intercept = jnp.ones((n, 1))
    X_full = jnp.hstack([intercept, X])

    # Compute linear predictor: eta = X @ beta
    eta = X_full @ beta

    # Apply inverse link to get mean: mu = g^{-1}(eta)
    mu = _inverse_link(eta, resolved_link)

    # Generate response based on family
    if family == "gaussian":
        y = mu + jax.random.normal(key_y, shape=(n,)) * sigma
    elif family == "binomial":
        # Bernoulli sampling: y ~ Bernoulli(mu)
        y = jax.random.bernoulli(key_y, p=mu).astype(jnp.float64)
    elif family == "poisson":
        # Poisson sampling: y ~ Poisson(mu)
        # JAX doesn't have poisson directly, use numpy for sampling
        y = jnp.asarray(np.random.default_rng(int(key_y[0])).poisson(np.asarray(mu)))
    else:
        raise ValueError(f"Unknown family: {family}")

    # Build DataFrame
    data_dict = {"y": np.asarray(y)}
    for i in range(n_predictors):
        data_dict[f"x{i + 1}"] = np.asarray(X[:, i])

    data = pl.DataFrame(data_dict)

    true_params = {
        "beta": np.asarray(beta),
        "family": family,
        "link": resolved_link,
    }
    if family == "gaussian":
        true_params["sigma"] = float(sigma)

    return data, true_params
