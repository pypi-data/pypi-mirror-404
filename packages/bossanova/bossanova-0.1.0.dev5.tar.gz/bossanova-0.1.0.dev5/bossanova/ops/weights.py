"""Weight computation utilities for weighted least squares.

This module provides utilities for computing observation weights from
factor columns for WLS estimation. When a categorical column is specified
as weights, inverse-variance weights are computed automatically.

Examples:
    >>> from bossanova import lm, load_dataset
    >>> df = load_dataset("credit")
    >>> # Categorical weights: compute 1/var(y|group) per observation
    >>> model = lm("Balance ~ Student", data=df).fit(weights="Student")
"""

from __future__ import annotations

__all__ = ["WeightInfo", "detect_weight_type", "compute_inverse_variance_weights"]

from dataclasses import dataclass

import numpy as np
import polars as pl


@dataclass
class WeightInfo:
    """Metadata for weights derived from factor columns.

    This dataclass stores information needed for inference adjustments
    when weights come from a categorical column (inverse-variance weighting).

    Attributes:
        weights: Weight array, shape (n,). Contains w_i = 1/var(y|group_i).
        column: Original column name used for weights.
        is_factor: True if weights were derived from a categorical column.
        group_labels: Group names (factor levels).
        group_variances: Variance of y within each group, shape (k,).
        group_counts: Number of observations per group, shape (k,).
        group_indices: Group membership per observation, shape (n,).
            Values are 0-indexed indices into group_labels.
    """

    weights: np.ndarray
    column: str
    is_factor: bool
    group_labels: list[str]
    group_variances: np.ndarray
    group_counts: np.ndarray
    group_indices: np.ndarray


def detect_weight_type(data: pl.DataFrame, col: str) -> bool:
    """Check if a column is categorical (should use inverse-variance weights).

    Returns True for String, Categorical, and Enum dtypes, which indicate
    the column represents factor levels rather than numeric weights.

    Args:
        data: DataFrame containing the column.
        col: Column name to check.

    Returns:
        True if the column is categorical, False if numeric.

    Raises:
        ValueError: If column not found in data.

    Examples:
        >>> import polars as pl
        >>> df = pl.DataFrame({"group": ["A", "B", "A"], "w": [1.0, 2.0, 1.0]})
        >>> detect_weight_type(df, "group")
        True
        >>> detect_weight_type(df, "w")
        False
    """
    if col not in data.columns:
        raise ValueError(f"Column '{col}' not found in data")

    dtype = data[col].dtype
    return dtype in (pl.String, pl.Categorical, pl.Utf8) or isinstance(dtype, pl.Enum)


def compute_inverse_variance_weights(
    data: pl.DataFrame,
    y_col: str,
    group_col: str,
    valid_mask: np.ndarray | None = None,
) -> WeightInfo:
    """Compute inverse-variance weights from a factor column.

    For each observation, computes w_i = 1/var(y|group_i), where var(y|group_i)
    is the variance of y within the observation's group.

    This implements the standard inverse-variance weighting used in
    meta-analysis and Welch's t-test. When combined with WLS, this
    gives more weight to groups with less variability.

    Args:
        data: DataFrame containing both columns.
        y_col: Name of the response variable column.
        group_col: Name of the grouping column (factor).
        valid_mask: Boolean mask for valid (non-missing) observations.
            If None, all observations are considered valid.

    Returns:
        WeightInfo containing weights and group statistics.

    Raises:
        ValueError: If columns not found or group has zero variance.

    Notes:
        - Groups with a single observation get infinite weight (var=0);
          we use a small epsilon to avoid division by zero.
        - The weights are computed on valid observations only, but the
          returned weight array has length equal to the original data.

    Examples:
        >>> import polars as pl
        >>> df = pl.DataFrame({
        ...     "y": [1.0, 2.0, 3.0, 10.0, 11.0, 12.0],
        ...     "group": ["A", "A", "A", "B", "B", "B"],
        ... })
        >>> info = compute_inverse_variance_weights(df, "y", "group")
        >>> # Group A and B both have var=1.0, so weights are equal
        >>> info.weights
        array([1., 1., 1., 1., 1., 1.])
    """
    if y_col not in data.columns:
        raise ValueError(f"Response column '{y_col}' not found in data")
    if group_col not in data.columns:
        raise ValueError(f"Group column '{group_col}' not found in data")

    n = len(data)

    # Apply valid mask if provided
    if valid_mask is not None:
        work_data = data.filter(pl.lit(valid_mask))
    else:
        work_data = data
        valid_mask = np.ones(n, dtype=bool)

    # Get y values
    y = work_data[y_col].to_numpy().astype(np.float64)

    # Get group labels (as strings for consistency)
    groups = work_data[group_col].cast(pl.String).to_numpy()

    # Get unique groups in order of appearance (for consistent indexing)
    unique_groups = list(dict.fromkeys(groups))  # preserves order, removes dups
    k = len(unique_groups)

    # Compute per-group statistics
    group_variances = np.zeros(k, dtype=np.float64)
    group_counts = np.zeros(k, dtype=np.int64)

    for i, g in enumerate(unique_groups):
        mask = groups == g
        y_group = y[mask]
        group_counts[i] = len(y_group)
        if len(y_group) > 1:
            group_variances[i] = np.var(y_group, ddof=1)  # Sample variance
        else:
            # Single observation: use small variance to avoid infinite weight
            # This is a fallback; proper df adjustment handles this case
            group_variances[i] = np.finfo(np.float64).eps

    # Build group index for each observation (maps to position in unique_groups)
    group_to_idx = {g: i for i, g in enumerate(unique_groups)}
    group_indices_valid = np.array([group_to_idx[g] for g in groups], dtype=np.int64)

    # Compute weights for valid observations: w_i = 1/var(y|group_i)
    weights_valid = 1.0 / group_variances[group_indices_valid]

    # Expand to full length (NaN for invalid observations)
    weights = np.full(n, np.nan, dtype=np.float64)
    weights[valid_mask] = weights_valid

    group_indices = np.full(n, -1, dtype=np.int64)
    group_indices[valid_mask] = group_indices_valid

    return WeightInfo(
        weights=weights,
        column=group_col,
        is_factor=True,
        group_labels=unique_groups,
        group_variances=group_variances,
        group_counts=group_counts,
        group_indices=group_indices,
    )
