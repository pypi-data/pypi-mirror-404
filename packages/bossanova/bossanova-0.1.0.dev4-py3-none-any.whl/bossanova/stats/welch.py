"""Welch-Satterthwaite degrees of freedom for unequal variance inference.

This module implements the Welch-Satterthwaite approximation for
degrees of freedom when group variances are unequal. It supports:

1. **Simple two-group comparisons**: Matches scipy's Welch t-test exactly
2. **Multi-group (ANOVA)**: Welch's ANOVA with adjusted F-statistic
3. **Factorial designs**: Welch-James procedure using cell-based variances

The Welch-Satterthwaite formula accounts for heterogeneous variances
across groups by computing an effective degrees of freedom based on
the contribution of each group's variance estimate.

References:
    - Welch, B. L. (1947). The generalization of Student's problem when
      several different population variances are involved. Biometrika, 34(1-2), 28-35.
    - Satterthwaite, F. E. (1946). An approximate distribution of estimates
      of variance components. Biometrics Bulletin, 2(6), 110-114.
    - James, G. S. (1951). The comparison of several groups of observations
      when the ratios of the population variances are unknown. Biometrika, 38(3/4), 324-329.

Examples:
    >>> from bossanova import lm, load_dataset
    >>> df = load_dataset("credit")
    >>> # Welch t-test equivalent (auto-detects Student as factor)
    >>> model = lm("Balance ~ Student", data=df).fit().infer(errors="unequal_var")
"""

from __future__ import annotations

__all__ = [
    "welch_satterthwaite_df",
    "CellInfo",
    "extract_factors_from_formula",
    "compute_cell_info",
    "compute_welch_se",
]

import re
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
import polars as pl


def welch_satterthwaite_df(
    group_variances: np.ndarray,
    group_counts: np.ndarray,
) -> float:
    """Compute Welch-Satterthwaite degrees of freedom.

    For k groups with sample variances s_i^2 and sample sizes n_i,
    computes the approximate degrees of freedom for the combined
    variance estimate under heterogeneous variances.

    For k=2 groups, this gives the exact Welch df:

        df = (s1²/n1 + s2²/n2)² / [(s1²/n1)²/(n1-1) + (s2²/n2)²/(n2-1)]

    For k>2 groups, the formula generalizes:

        df = (Σ s_i²/n_i)² / Σ[(s_i²/n_i)²/(n_i-1)]

    Args:
        group_variances: Sample variance of y within each group, shape (k,).
            These are s_i² values (sample variances with ddof=1).
        group_counts: Sample size per group, shape (k,).
            These are n_i values.

    Returns:
        Welch-Satterthwaite degrees of freedom (float).

    Raises:
        ValueError: If arrays have different lengths or any count < 2.

    Notes:
        - Matches scipy.stats.ttest_ind(equal_var=False) exactly for k=2
        - For groups with n_i = 1, that group cannot contribute to df
          (infinite variance of variance estimate)
        - Returns a positive float; may be non-integer

    Examples:
        >>> import numpy as np
        >>> # Two groups with different variances
        >>> var1, var2 = 1.0, 4.0  # Group 2 has 4x the variance
        >>> n1, n2 = 10, 10
        >>> df = welch_satterthwaite_df(
        ...     np.array([var1, var2]),
        ...     np.array([n1, n2])
        ... )
        >>> # df will be less than 18 (n1 + n2 - 2) due to unequal variances
    """
    group_variances = np.asarray(group_variances, dtype=np.float64)
    group_counts = np.asarray(group_counts, dtype=np.int64)

    if len(group_variances) != len(group_counts):
        raise ValueError(
            f"group_variances and group_counts must have same length, "
            f"got {len(group_variances)} and {len(group_counts)}"
        )

    k = len(group_variances)
    if k < 2:
        raise ValueError(f"Need at least 2 groups for Welch df, got {k}")

    # Check all groups have at least 2 observations
    if np.any(group_counts < 2):
        raise ValueError(
            "All groups must have at least 2 observations for Welch df. "
            f"Got counts: {group_counts.tolist()}"
        )

    # Compute variance contribution from each group: s_i² / n_i
    var_contrib = group_variances / group_counts

    # Numerator: (Σ s_i²/n_i)²
    numerator = np.sum(var_contrib) ** 2

    # Denominator: Σ [(s_i²/n_i)² / (n_i - 1)]
    denominator = np.sum(var_contrib**2 / (group_counts - 1))

    if denominator < 1e-15:
        # Avoid division by zero - return large df (near-equal variances)
        return 1e6

    df = numerator / denominator
    return float(df)


# =============================================================================
# Cell-based variance computation for Welch inference
# =============================================================================


@dataclass
class CellInfo:
    """Information about factor cells for Welch-style inference.

    When using `errors='unequal_var'`, residual variances are computed
    within each cell defined by the crossing of all factors in the model.
    This implements the Welch-James approach for factorial designs.

    Attributes:
        cell_labels: Labels for each cell as tuples of factor levels.
            For single factor: [("A",), ("B",), ...]
            For multiple factors: [("A", "X"), ("A", "Y"), ("B", "X"), ...]
        cell_variances: Sample variance of residuals within each cell.
        cell_counts: Number of observations in each cell.
        cell_indices: Cell membership for each observation (0-indexed).
        factor_columns: Names of factor columns used to define cells.
    """

    cell_labels: list[tuple[str, ...]]
    cell_variances: NDArray[np.float64]
    cell_counts: NDArray[np.int64]
    cell_indices: NDArray[np.int64]
    factor_columns: list[str]


def extract_factors_from_formula(formula: str, data: pl.DataFrame) -> list[str]:
    """Extract factor (categorical) column names from a model formula.

    Parses the RHS of the formula and identifies which columns are
    categorical (String, Categorical, or Enum type in polars).

    Args:
        formula: Model formula like "y ~ A + B + x" or "y ~ A * B + center(x)".
        data: DataFrame containing the columns referenced in the formula.

    Returns:
        List of column names that are categorical/factor variables.

    Examples:
        >>> import polars as pl
        >>> df = pl.DataFrame({
        ...     "y": [1.0, 2.0, 3.0],
        ...     "group": ["A", "B", "A"],
        ...     "x": [0.1, 0.2, 0.3],
        ... })
        >>> extract_factors_from_formula("y ~ group + x", df)
        ['group']

        >>> # Multiple factors
        >>> df2 = df.with_columns(pl.col("group").alias("treatment"))
        >>> extract_factors_from_formula("y ~ group * treatment", df2)
        ['group', 'treatment']

    Notes:
        - Handles interaction terms (*, :) by extracting component columns
        - Handles transforms like center(x) by extracting the inner column
        - Skips intercept terms (1, 0, -1)
        - Only returns columns that exist in the data
    """
    # Parse RHS of formula
    if "~" not in formula:
        raise ValueError(f"Formula must contain '~', got: {formula!r}")

    rhs = formula.split("~")[1].strip()

    # Extract column names by splitting on operators and cleaning
    # Handles: +, *, :, | (random effects separator)
    terms = re.split(r"[+*:|]", rhs)
    columns: list[str] = []

    for term in terms:
        term = term.strip()

        # Skip intercept terms
        if term in ("1", "0", "-1", ""):
            continue

        # Handle transforms like center(x), scale(y), log(z)
        # Extract the inner column name
        if "(" in term:
            match = re.search(r"\(([^)]+)\)", term)
            if match:
                term = match.group(1).strip()

        # Handle polynomial terms like I(x^2)
        if term.startswith("I("):
            continue  # Skip I() terms as they're transformations

        # Skip numeric literals
        if re.match(r"^[\d.]+$", term):
            continue

        if term and term not in columns:
            columns.append(term)

    # Filter to factors (categorical columns)
    factors = []
    for col in columns:
        if col not in data.columns:
            continue

        dtype = data[col].dtype
        # Check for categorical types in polars
        is_categorical = (
            dtype == pl.Utf8
            or dtype == pl.String
            or dtype == pl.Categorical
            or str(dtype).startswith("Enum")
        )

        if is_categorical:
            factors.append(col)

    return factors


def compute_cell_info(
    residuals: NDArray[np.float64],
    data: pl.DataFrame,
    factor_columns: list[str],
) -> CellInfo:
    """Compute cell-based variance information for Welch inference.

    For multi-factor models, cells are defined by the crossing of all factors.
    This implements the Welch-James approach for factorial designs.

    Args:
        residuals: OLS residuals, shape (n,).
        data: DataFrame with factor columns.
        factor_columns: List of factor column names.

    Returns:
        CellInfo containing variance information for each cell.

    Raises:
        ValueError: If factor_columns is empty or contains invalid columns.
        ValueError: If any cell has fewer than 2 observations.

    Examples:
        >>> import numpy as np
        >>> import polars as pl
        >>> df = pl.DataFrame({
        ...     "group": ["A", "A", "B", "B", "B"],
        ...     "x": [1.0, 2.0, 3.0, 4.0, 5.0],
        ... })
        >>> residuals = np.array([0.1, -0.1, 0.2, -0.1, -0.1])
        >>> info = compute_cell_info(residuals, df, ["group"])
        >>> info.cell_labels
        [('A',), ('B',)]
        >>> info.cell_counts
        array([2, 3])
    """
    if not factor_columns:
        raise ValueError("factor_columns cannot be empty")

    residuals = np.asarray(residuals, dtype=np.float64).ravel()
    n = len(residuals)

    # Validate columns exist
    for col in factor_columns:
        if col not in data.columns:
            raise ValueError(f"Factor column '{col}' not found in data")

    if len(factor_columns) == 1:
        # Single factor: simple grouping
        factor = factor_columns[0]
        groups = data[factor].to_numpy()
        unique_groups = np.unique(groups)
        k = len(unique_groups)

        cell_labels = [(str(g),) for g in unique_groups]
        cell_indices = np.zeros(n, dtype=np.int64)
        cell_variances = np.zeros(k, dtype=np.float64)
        cell_counts = np.zeros(k, dtype=np.int64)

        for i, g in enumerate(unique_groups):
            mask = groups == g
            cell_indices[mask] = i
            count = int(np.sum(mask))
            cell_counts[i] = count

            if count < 2:
                raise ValueError(
                    f"Cell '{g}' has only {count} observation(s). "
                    "All cells must have at least 2 observations for Welch inference."
                )

            cell_variances[i] = float(np.var(residuals[mask], ddof=1))

    else:
        # Multiple factors: use cell crossings
        cell_data = data.select(factor_columns)

        # Get unique cells (sorted for reproducibility)
        unique_cells = cell_data.unique().sort(factor_columns)
        k = len(unique_cells)

        cell_labels = [tuple(str(v) for v in row) for row in unique_cells.iter_rows()]
        cell_indices = np.zeros(n, dtype=np.int64)
        cell_variances = np.zeros(k, dtype=np.float64)
        cell_counts = np.zeros(k, dtype=np.int64)

        for i, cell_row in enumerate(unique_cells.iter_rows(named=True)):
            # Build mask for this cell by matching all factor levels
            mask = np.ones(n, dtype=bool)
            for col, val in cell_row.items():
                col_values = data[col].to_numpy()
                mask &= col_values == val

            cell_indices[mask] = i
            count = int(np.sum(mask))
            cell_counts[i] = count

            if count < 2:
                cell_label = ", ".join(f"{k}={v}" for k, v in cell_row.items())
                raise ValueError(
                    f"Cell ({cell_label}) has only {count} observation(s). "
                    "All cells must have at least 2 observations for Welch inference."
                )

            cell_variances[i] = float(np.var(residuals[mask], ddof=1))

    return CellInfo(
        cell_labels=cell_labels,
        cell_variances=cell_variances,
        cell_counts=cell_counts,
        cell_indices=cell_indices,
        factor_columns=factor_columns,
    )


def compute_welch_se(
    cell_info: CellInfo,
    contrast: NDArray[np.float64] | None = None,
) -> float:
    """Compute Welch standard error for a contrast or overall comparison.

    For a simple group comparison (intercept + treatment effect), the
    Welch SE for the treatment effect is:

        SE = sqrt(s₁²/n₁ + s₂²/n₂)

    For multiple groups or contrasts, generalizes to:

        SE = sqrt(Σ cⱼ² × sⱼ²/nⱼ)

    where cⱼ are contrast weights.

    Args:
        cell_info: Cell-based variance information from compute_cell_info().
        contrast: Optional contrast weights for each cell. If None, uses
            simple pooled variance (appropriate for pairwise comparison
            between first and second cell).

    Returns:
        Welch standard error.

    Examples:
        >>> # Simple two-group comparison
        >>> se = compute_welch_se(cell_info)

        >>> # Custom contrast (e.g., first vs average of others)
        >>> contrast = np.array([1, -0.5, -0.5])
        >>> se = compute_welch_se(cell_info, contrast)
    """
    var_over_n = cell_info.cell_variances / cell_info.cell_counts

    if contrast is None:
        # Default: sum of variance contributions (for pairwise)
        se_sq = np.sum(var_over_n)
    else:
        # Weighted: Σ c² × s²/n
        contrast = np.asarray(contrast, dtype=np.float64)
        se_sq = np.sum(contrast**2 * var_over_n)

    return float(np.sqrt(se_sq))
