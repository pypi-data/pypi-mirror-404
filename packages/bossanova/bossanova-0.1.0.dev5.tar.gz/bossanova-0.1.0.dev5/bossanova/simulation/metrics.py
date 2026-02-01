"""Metrics for Monte Carlo simulation studies.

Provides functions for computing bias, RMSE, coverage, and rejection rates
from simulation results.
"""

import numpy as np
from numpy.typing import ArrayLike

__all__ = [
    "bias",
    "rmse",
    "mean_se",
    "empirical_se",
    "coverage",
    "rejection_rate",
    "se_ratio",
]


def bias(estimates: ArrayLike, true_value: float) -> float:
    """Compute bias: E[β̂] - β_true.

    Args:
        estimates: Array of parameter estimates from simulations.
        true_value: True parameter value.

    Returns:
        Bias (positive = overestimate, negative = underestimate).

    Examples:
        >>> estimates = np.array([1.02, 0.98, 1.01, 0.99, 1.00])
        >>> bias(estimates, true_value=1.0)
        0.0
    """
    estimates = np.asarray(estimates)
    return float(np.mean(estimates) - true_value)


def rmse(estimates: ArrayLike, true_value: float) -> float:
    """Compute root mean squared error.

    RMSE = sqrt(E[(β̂ - β)²]) = sqrt(Var(β̂) + Bias²)

    Args:
        estimates: Array of parameter estimates from simulations.
        true_value: True parameter value.

    Returns:
        RMSE value.

    Examples:
        >>> estimates = np.array([1.1, 0.9, 1.0, 1.0, 1.0])
        >>> rmse(estimates, true_value=1.0)  # doctest: +ELLIPSIS
        0.063...
    """
    estimates = np.asarray(estimates)
    return float(np.sqrt(np.mean((estimates - true_value) ** 2)))


def mean_se(std_errors: ArrayLike) -> float:
    """Compute mean of standard errors across simulations.

    Args:
        std_errors: Array of SE estimates from simulations.

    Returns:
        Mean SE.
    """
    std_errors = np.asarray(std_errors)
    return float(np.mean(std_errors))


def empirical_se(estimates: ArrayLike) -> float:
    """Compute empirical standard error (SD of estimates).

    This is the "true" standard error as estimated from the
    simulation distribution.

    Args:
        estimates: Array of parameter estimates from simulations.

    Returns:
        Empirical SE (standard deviation of estimates).
    """
    estimates = np.asarray(estimates)
    return float(np.std(estimates, ddof=1))


def coverage(
    ci_lower: ArrayLike,
    ci_upper: ArrayLike,
    true_value: float,
) -> float:
    """Compute coverage probability.

    Coverage = P(CI_lower ≤ β_true ≤ CI_upper)

    For a correctly calibrated 95% CI, coverage should be ~0.95.

    Args:
        ci_lower: Array of CI lower bounds from simulations.
        ci_upper: Array of CI upper bounds from simulations.
        true_value: True parameter value.

    Returns:
        Coverage probability (0 to 1).

    Examples:
        >>> ci_lower = np.array([0.8, 0.9, 0.85, 0.95, 0.88])
        >>> ci_upper = np.array([1.2, 1.1, 1.15, 1.05, 1.12])
        >>> coverage(ci_lower, ci_upper, true_value=1.0)
        1.0
    """
    ci_lower = np.asarray(ci_lower)
    ci_upper = np.asarray(ci_upper)
    covered = (ci_lower <= true_value) & (true_value <= ci_upper)
    return float(np.mean(covered))


def rejection_rate(p_values: ArrayLike, alpha: float = 0.05) -> float:
    """Compute rejection rate (proportion of p-values < alpha).

    For null effects (β=0), this estimates Type I error rate.
    For non-null effects (β≠0), this estimates power.

    Args:
        p_values: Array of p-values from simulations.
        alpha: Significance level (default 0.05).

    Returns:
        Rejection rate (0 to 1).

    Examples:
        >>> p_values = np.array([0.01, 0.06, 0.03, 0.12, 0.04])
        >>> rejection_rate(p_values, alpha=0.05)
        0.6
    """
    p_values = np.asarray(p_values)
    return float(np.mean(p_values < alpha))


def se_ratio(mean_se: float, empirical_se: float) -> float:
    """Compute ratio of mean estimated SE to empirical SE.

    A ratio of 1.0 indicates correctly estimated SEs.
    Ratio < 1 means SEs are underestimated (anti-conservative).
    Ratio > 1 means SEs are overestimated (conservative).

    Args:
        mean_se: Mean of estimated standard errors.
        empirical_se: Empirical SE (SD of estimates).

    Returns:
        SE ratio.
    """
    if empirical_se == 0:
        return float("inf") if mean_se > 0 else float("nan")
    return mean_se / empirical_se
