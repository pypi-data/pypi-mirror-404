"""Reference grid construction for EMM computation.

This module provides utilities for building reference grids - the
cartesian product of factor levels with covariates at representative
values. These grids are used to compute estimated marginal means.

Examples:
    >>> from bossanova.marginal.grid import build_reference_grid
    >>> grid = build_reference_grid(
    ...     data=df,
    ...     factors=["group", "treatment"],
    ...     covariates=["age"],
    ... )
    >>> grid.shape
    (6, 3)  # 2 groups × 3 treatments, age at mean
"""

from __future__ import annotations

from typing import Any

import polars as pl

__all__ = [
    "build_reference_grid",
]


def build_reference_grid(
    data: pl.DataFrame,
    factors: list[str],
    covariates: list[str] | None = None,
    at: dict[str, Any] | None = None,
) -> pl.DataFrame:
    """Build reference grid for EMM computation.

    Creates a cartesian product of factor levels with covariates at
    representative values (means by default, or values specified in `at`).

    Args:
        data: Original data (for extracting factor levels and covariate means).
        factors: Factor variables to create grid for. Each factor contributes
            its unique levels to the cartesian product.
        covariates: Numeric variables to include in grid. By default, set to
            their means. Override with `at` parameter.
        at: Override values for specific variables. Can specify factor levels
            to subset or covariate values to use instead of means.

    Returns:
        DataFrame with one row per EMM cell (cartesian product of factor levels),
        plus covariate columns at their representative values.

    Raises:
        ValueError: If a factor is not found in data or has no levels.
        ValueError: If a covariate is not found in data.

    Examples:
        >>> data = pl.DataFrame({
        ...     "y": [1, 2, 3, 4],
        ...     "group": ["A", "A", "B", "B"],
        ...     "treatment": ["ctrl", "drug", "ctrl", "drug"],
        ...     "age": [25, 30, 35, 40],
        ... })
        >>> grid = build_reference_grid(data, factors=["group", "treatment"])
        >>> grid
        shape: (4, 2)
        ┌───────┬───────────┐
        │ group ┆ treatment │
        │ str   ┆ str       │
        ╞═══════╪═══════════╡
        │ A     ┆ ctrl      │
        │ A     ┆ drug      │
        │ B     ┆ ctrl      │
        │ B     ┆ drug      │
        └───────┴───────────┘

        >>> grid = build_reference_grid(
        ...     data, factors=["group"], covariates=["age"]
        ... )
        >>> grid
        shape: (2, 2)
        ┌───────┬──────┐
        │ group ┆ age  │
        │ str   ┆ f64  │
        ╞═══════╪══════╡
        │ A     ┆ 32.5 │
        │ B     ┆ 32.5 │
        └───────┴──────┘
    """
    at = at or {}

    # Validate factors exist in data
    for factor in factors:
        if factor not in data.columns:
            raise ValueError(
                f"Factor '{factor}' not found in data columns: {data.columns}"
            )

    # Validate covariates exist in data
    if covariates:
        for cov in covariates:
            if cov not in data.columns:
                raise ValueError(
                    f"Covariate '{cov}' not found in data columns: {data.columns}"
                )

    # Build factor level lists
    factor_levels: dict[str, list] = {}
    for factor in factors:
        if factor in at:
            # Use specified levels (subset)
            specified = at[factor]
            if not isinstance(specified, (list, tuple)):
                specified = [specified]
            factor_levels[factor] = list(specified)
        else:
            # Get unique levels from data
            unique_vals = data[factor].unique().sort().to_list()
            if len(unique_vals) == 0:
                raise ValueError(f"Factor '{factor}' has no levels in data")
            factor_levels[factor] = unique_vals

    # Create cartesian product of factor levels
    grid = _cartesian_product(factor_levels)

    # Handle edge case: no factors but covariates with multiple values
    # In this case, we need to build the grid from covariate values
    if grid.is_empty() and covariates:
        # Find first covariate with multiple values to seed the grid
        for cov in covariates:
            if cov in at:
                value = at[cov]
                if isinstance(value, (list, tuple)) and len(value) > 1:
                    grid = pl.DataFrame({cov: list(value)})
                    covariates = [
                        c for c in covariates if c != cov
                    ]  # Remove from further processing
                    break

    # Add covariates at representative values
    if covariates:
        for cov in covariates:
            if cov in at:
                # Use specified value(s)
                value = at[cov]
                if isinstance(value, (list, tuple)) and len(value) > 1:
                    # Multiple values specified - expand grid
                    # This happens with bracket syntax like mee("cyl | wt[3, 4]")
                    grid = _expand_grid_for_values(grid, cov, list(value))
                else:
                    # Single value - add as constant
                    if isinstance(value, (list, tuple)):
                        value = value[0]
                    grid = grid.with_columns(pl.lit(value).alias(cov))
            else:
                # Use mean from data
                value = data[cov].mean()
                grid = grid.with_columns(pl.lit(value).alias(cov))

    return grid


def _expand_grid_for_values(
    grid: pl.DataFrame, var_name: str, values: list
) -> pl.DataFrame:
    """Expand grid to include all specified values for a variable.

    Creates a cross product of existing grid rows with the specified values.

    Args:
        grid: Existing reference grid.
        var_name: Variable name to expand.
        values: List of values to include.

    Returns:
        Expanded grid with one row per original row × value combination.

    Examples:
        >>> grid = pl.DataFrame({"cyl": [4, 6, 8]})
        >>> _expand_grid_for_values(grid, "wt", [3.0, 4.0])
        shape: (6, 2)
        ┌─────┬─────┐
        │ cyl ┆ wt  │
        │ i64 ┆ f64 │
        ╞═════╪═════╡
        │ 4   ┆ 3.0 │
        │ 4   ┆ 4.0 │
        │ 6   ┆ 3.0 │
        │ 6   ┆ 4.0 │
        │ 8   ┆ 3.0 │
        │ 8   ┆ 4.0 │
        └─────┴─────┘
    """
    # Create DataFrame with the values
    values_df = pl.DataFrame({var_name: values})

    # Cross join to expand
    return grid.join(values_df, how="cross")


def _cartesian_product(level_dict: dict[str, list]) -> pl.DataFrame:
    """Create cartesian product of factor levels.

    Args:
        level_dict: Mapping from factor name to list of levels.

    Returns:
        DataFrame with cartesian product of all factor levels.

    Examples:
        >>> _cartesian_product({"A": [1, 2], "B": ["x", "y"]})
        shape: (4, 2)
        ┌─────┬─────┐
        │ A   ┆ B   │
        ╞═════╪═════╡
        │ 1   ┆ x   │
        │ 1   ┆ y   │
        │ 2   ┆ x   │
        │ 2   ┆ y   │
        └─────┴─────┘
    """
    if not level_dict:
        return pl.DataFrame()

    # Start with first factor
    factors = list(level_dict.keys())
    result = pl.DataFrame({factors[0]: level_dict[factors[0]]})

    # Cross join with remaining factors
    for factor in factors[1:]:
        other = pl.DataFrame({factor: level_dict[factor]})
        result = result.join(other, how="cross")

    return result
