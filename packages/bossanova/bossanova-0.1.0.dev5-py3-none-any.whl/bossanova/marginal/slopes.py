"""Marginal effects (slopes) computation for continuous variables.

Implements emtrends-style finite difference slope computation with
proper variance propagation via delta method.

The algorithm:
1. Centered finite difference: delta = 0.001 * range(var)
2. Compute predictions at x - delta/2 and x + delta/2
3. slope = (pred_plus - pred_minus) / delta
4. SE via delta method on differenced linear functional

This achieves parity with R's emmeans::emtrends().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
import polars as pl

from bossanova.marginal.grid import build_reference_grid
from bossanova.ops.inference import compute_se_from_vcov

if TYPE_CHECKING:
    from bossanova.formula.design import DesignMatrixBuilder

__all__ = [
    "SlopeResult",
    "compute_slopes",
    "compute_slopes_by_group",
    "average_slopes",
]


@dataclass
class SlopeResult:
    """Container for marginal effect (slope) results.

    Attributes:
        grid: Reference grid DataFrame (covariate values where slopes computed).
        slopes: Slope point estimates (marginal effects), shape (n_slopes,).
        se: Standard errors of slopes, shape (n_slopes,).
        df: Degrees of freedom for inference.
        var_name: Name of the continuous variable whose slope was computed.
        L_diff: Differenced linear functional, shape (n_slopes, n_coef).
            Used for joint_tests if needed.
        vcov_slopes: Variance-covariance matrix of slopes, shape (n_slopes, n_slopes).
    """

    grid: pl.DataFrame
    slopes: np.ndarray
    se: np.ndarray
    df: float | np.ndarray
    var_name: str
    L_diff: np.ndarray
    vcov_slopes: np.ndarray


def compute_slopes(
    builder: "DesignMatrixBuilder",
    grid: pl.DataFrame,
    var: str,
    coef: np.ndarray,
    vcov: np.ndarray,
    df: float,
    data: pl.DataFrame,
    delta_frac: float = 0.001,
) -> SlopeResult:
    """Compute marginal effects (slopes) for a continuous variable.

    Uses centered finite differences to estimate the derivative of the
    prediction function with respect to var, following emmeans::emtrends().

    Args:
        builder: DesignMatrixBuilder instance for evaluate_new_data().
        grid: Reference grid defining where to compute slopes.
        var: Name of the continuous variable to differentiate.
        coef: Fitted coefficient estimates, shape (p,).
        vcov: Variance-covariance matrix of coefficients, shape (p, p).
        df: Residual degrees of freedom.
        data: Original training data (for computing variable range).
        delta_frac: Fraction of variable range for finite difference step.
            Default 0.001 (matches emmeans).

    Returns:
        SlopeResult containing slopes, SEs, and differenced linear functional.

    Examples:
        >>> # Compute slope of 'age' averaged over other factors
        >>> grid = build_reference_grid(data, factors=["treatment"])
        >>> result = compute_slopes(builder, grid, "age", coef, vcov, df, data)
        >>> result.slopes  # One slope per treatment level
    """
    # Compute step size: delta = fraction * range(var)
    # Drop NaN values when computing range (data may include rows with missing values)
    var_values = data[var].drop_nulls().to_numpy()
    var_range = float(np.nanmax(var_values) - np.nanmin(var_values))

    if var_range == 0:
        raise ValueError(f"Variable {var!r} has zero range, cannot compute slope")

    delta = delta_frac * var_range

    # Create grids at x - delta/2 and x + delta/2
    # We need to add the continuous variable to the grid if not present
    if var not in grid.columns:
        # Use mean of var as the evaluation point
        # Cast to float for type safety (polars mean returns broad union)
        var_mean = data.select(pl.col(var).mean()).item()
        if var_mean is None:
            var_mean = 0.0
        grid = grid.with_columns(pl.lit(float(var_mean)).alias(var))

    # Get current values of var in grid
    var_current = grid[var].to_numpy()

    # Create perturbed grids
    grid_minus = grid.with_columns(pl.lit(var_current - delta / 2).alias(var))
    grid_plus = grid.with_columns(pl.lit(var_current + delta / 2).alias(var))

    # Build design matrices for perturbed grids
    X_minus = builder.evaluate_new_data(grid_minus)
    X_plus = builder.evaluate_new_data(grid_plus)

    # Differenced linear functional: (X_plus - X_minus) / delta
    L_diff = (X_plus - X_minus) / delta

    # Compute slopes as L_diff @ coef
    slopes = L_diff @ coef

    # Variance of slopes via delta method
    # Var(L @ β) = L @ Var(β) @ L.T
    vcov_slopes = L_diff @ vcov @ L_diff.T
    se = compute_se_from_vcov(vcov_slopes)

    return SlopeResult(
        grid=grid,
        slopes=slopes,
        se=se,
        df=df,
        var_name=var,
        L_diff=L_diff,
        vcov_slopes=vcov_slopes,
    )


def compute_slopes_by_group(
    builder: "DesignMatrixBuilder",
    var: str,
    by_vars: list[str],
    coef: np.ndarray,
    vcov: np.ndarray,
    df: float,
    data: pl.DataFrame,
    at_values: dict[str, list[Any]] | None = None,
    delta_frac: float = 0.001,
) -> SlopeResult:
    """Compute slopes stratified by grouping variables.

    This computes the slope of var separately for each combination
    of the by_vars levels, enabling analysis of interactions.

    Args:
        builder: DesignMatrixBuilder instance.
        var: Continuous variable to differentiate.
        by_vars: Grouping variables (slopes computed per group).
        coef: Fitted coefficients.
        vcov: Variance-covariance matrix.
        df: Degrees of freedom.
        data: Training data.
        at_values: Optional fixed values for other covariates.
        delta_frac: Finite difference step fraction.

    Returns:
        SlopeResult with one slope per group combination.

    Examples:
        >>> # Slope of age BY treatment level
        >>> result = compute_slopes_by_group(
        ...     builder, "age", ["treatment"], coef, vcov, df, data
        ... )
    """
    # Build reference grid from by_vars
    grid = build_reference_grid(
        data=data,
        factors=by_vars,
        at=at_values,
    )

    return compute_slopes(
        builder=builder,
        grid=grid,
        var=var,
        coef=coef,
        vcov=vcov,
        df=df,
        data=data,
        delta_frac=delta_frac,
    )


def average_slopes(
    slope_result: SlopeResult,
    weights: np.ndarray | None = None,
) -> dict[str, float]:
    """Compute average marginal effect (AME) from slope result.

    When slopes vary across the reference grid (e.g., due to interactions),
    this computes the weighted average slope.

    Args:
        slope_result: Result from compute_slopes().
        weights: Optional weights for averaging. If None, equal weights.

    Returns:
        Dict with 'slope', 'se', 'df' for the average marginal effect.
    """
    n = len(slope_result.slopes)

    if weights is None:
        weights = np.ones(n) / n
    else:
        weights = np.asarray(weights)
        weights = weights / weights.sum()

    # Weighted average slope
    ame = float(np.sum(weights * slope_result.slopes))

    # SE of weighted average: sqrt(w.T @ Vcov @ w)
    se = float(np.sqrt(weights @ slope_result.vcov_slopes @ weights))

    # For mixed models with Satterthwaite, df might be array
    # Use average df for AME
    if isinstance(slope_result.df, np.ndarray):
        df = float(np.mean(slope_result.df))
    else:
        df = slope_result.df

    return {"slope": ame, "se": se, "df": df}
