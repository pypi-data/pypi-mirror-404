"""Estimated Marginal Means (EMM) computation.

This module provides the core algorithm for computing EMMs from
coefficients and design matrices. The key operation is:

    EMMs = X_ref @ β

Where X_ref is a design matrix built from the reference grid.

Examples:
    >>> from bossanova.marginal.emm import compute_emm
    >>> result = compute_emm(builder, grid, coef, vcov, df_resid)
    >>> result.emmeans  # EMM point estimates
    >>> result.se       # Standard errors
    >>> result.X_ref    # Prediction matrix (for joint_tests)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import polars as pl

from bossanova.ops.inference import (
    adjust_pvalues,
    compute_pvalue,
    compute_se_from_vcov,
    compute_t_critical,
)

if TYPE_CHECKING:
    from bossanova.formula.design import DesignMatrixBuilder

__all__ = [
    "parse_emmeans_formula",
    "EMMResult",
    "EMMContrastResult",
    "compute_emm",
    "compute_emm_contrasts",
    "format_emm_table",
    "format_contrast_table",
]


# =============================================================================
# Formula Parsing
# =============================================================================


def parse_emmeans_formula(
    specs: str | list[str],
) -> tuple[list[str], list[str] | None]:
    """Parse emmeans formula with optional | stratification operator.

    Supports two operators:
    - `+` combines variables into a cell means grid
    - `|` separates specs (left) from stratification variables (right)

    The `|` operator follows lmer random effects intuition:
    `group | treatment` reads as "group means by/given treatment"

    Args:
        specs: Formula string or list of variable names.
            Examples: "group", "group + treatment", "group | treatment"

    Returns:
        Tuple of (specs_vars, by_vars).
        - specs_vars: List of variables to compute EMMs for
        - by_vars: List of stratification variables, or None if no | present

    Raises:
        ValueError: If more than one | operator is present.

    Examples:
        >>> parse_emmeans_formula("group")
        (['group'], None)

        >>> parse_emmeans_formula("group + treatment")
        (['group', 'treatment'], None)

        >>> parse_emmeans_formula("group | treatment")
        (['group'], ['treatment'])

        >>> parse_emmeans_formula("group + cond | treatment + block")
        (['group', 'cond'], ['treatment', 'block'])

        >>> parse_emmeans_formula(["group", "treatment"])
        (['group', 'treatment'], None)
    """
    # Handle list input - pass through as specs, no stratification
    if isinstance(specs, list):
        return (specs, None)

    # String input - parse formula
    formula = specs.strip()

    # Check for | operator
    if "|" in formula:
        parts = formula.split("|")
        if len(parts) > 2:
            raise ValueError(
                f"Formula can contain at most one '|' operator. Got: {specs!r}"
            )

        left, right = parts
        specs_vars = _parse_plus_separated(left)
        by_vars = _parse_plus_separated(right)

        if not specs_vars:
            raise ValueError(f"No variables specified before '|' in: {specs!r}")
        if not by_vars:
            raise ValueError(f"No variables specified after '|' in: {specs!r}")

        return (specs_vars, by_vars)

    # No | operator - just parse + separated variables
    specs_vars = _parse_plus_separated(formula)
    return (specs_vars, None)


def _parse_plus_separated(s: str) -> list[str]:
    """Parse a + separated string into variable names.

    Args:
        s: String like "a + b + c" or just "a"

    Returns:
        List of variable names with whitespace stripped.
    """
    parts = s.split("+")
    return [p.strip() for p in parts if p.strip()]


@dataclass
class EMMResult:
    """Container for estimated marginal means results.

    Attributes:
        grid: Reference grid DataFrame (factor levels defining each EMM).
        emmeans: EMM point estimates, shape (n_emms,).
        se: Standard errors of EMMs, shape (n_emms,).
        df: Degrees of freedom (scalar for lm, array for lmer with Satterthwaite).
        X_ref: Prediction matrix mapping coefficients to EMMs, shape (n_emms, n_coef).
            This is critical for joint_tests() which needs to build contrasts.
        vcov_emm: Variance-covariance matrix of EMMs, shape (n_emms, n_emms).
    """

    grid: pl.DataFrame
    emmeans: np.ndarray
    se: np.ndarray
    df: float | np.ndarray
    X_ref: np.ndarray
    vcov_emm: np.ndarray


@dataclass
class EMMContrastResult:
    """Container for EMM contrast results.

    Attributes:
        estimates: Contrast estimates, shape (n_contrasts,).
        se: Standard errors, shape (n_contrasts,).
        L_emm: Composed contrast matrix L_emm = C @ X_ref, shape (n_contrasts, n_coef).
            This matrix satisfies L_emm @ beta = C @ EMMs and is used by
            joint_tests() to perform F-tests on EMM contrasts.
    """

    estimates: np.ndarray
    se: np.ndarray
    L_emm: np.ndarray


def compute_emm(
    builder: DesignMatrixBuilder,
    grid: pl.DataFrame,
    coef: np.ndarray,
    vcov: np.ndarray,
    df: float,
) -> EMMResult:
    """Compute estimated marginal means.

    This is the core EMM computation algorithm:
    1. Convert reference grid to design matrix using evaluate_new_data()
    2. Compute EMMs as linear combinations of coefficients
    3. Compute standard errors via delta method

    Args:
        builder: DesignMatrixBuilder instance. Used for evaluate_new_data()
            which correctly applies stored transform parameters.
        grid: Reference grid from build_reference_grid(). Each row defines
            the covariate values for one EMM.
        coef: Fitted coefficient estimates, shape (p,).
        vcov: Variance-covariance matrix of coefficients, shape (p, p).
        df: Residual degrees of freedom (for t-distribution CIs).

    Returns:
        EMMResult containing EMMs, SEs, and the prediction matrix.

    Note:
        The key insight is that evaluate_new_data() preserves transform
        parameters (e.g., centering mean) learned during model fitting.
        This ensures predictions use the training data's parameters.

    Examples:
        >>> from bossanova.marginal import build_reference_grid, compute_emm
        >>> grid = build_reference_grid(data, factors=["group"])
        >>> result = compute_emm(model._builder, grid, model._coef, model._vcov, model._df_resid)
        >>> print(result.emmeans)
        [23.45, 27.89]
    """
    # Build design matrix for reference grid using builder's evaluate_new_data
    # This preserves transform parameters from fitting
    X_ref = builder.evaluate_new_data(grid)

    # Compute EMMs: linear combination of coefficients
    emmeans = X_ref @ coef

    # Compute variance-covariance of EMMs
    # Var(X_ref @ β) = X_ref @ Var(β) @ X_ref.T
    vcov_emm = X_ref @ vcov @ X_ref.T

    # Standard errors are sqrt of diagonal
    se = compute_se_from_vcov(vcov_emm)

    return EMMResult(
        grid=grid,
        emmeans=emmeans,
        se=se,
        df=df,
        X_ref=X_ref,
        vcov_emm=vcov_emm,
    )


def compute_emm_contrasts(
    emm_result: EMMResult,
    contrast_matrix: np.ndarray,
    coef: np.ndarray,
    vcov: np.ndarray,
) -> EMMContrastResult:
    """Compute contrasts of EMMs.

    Given a contrast matrix C that maps EMMs to contrasts, compute
    the contrast estimates and their standard errors.

    Args:
        emm_result: Result from compute_emm().
        contrast_matrix: Contrast matrix C, shape (n_contrasts, n_emms).
            Each row defines one contrast as linear combination of EMMs.
        coef: Fitted coefficients (needed for composed contrast).
        vcov: Variance-covariance of coefficients.

    Returns:
        EMMContrastResult containing:
        - estimates: Contrast estimates, shape (n_contrasts,).
        - se: Standard errors, shape (n_contrasts,).
        - L_emm: Composed contrast matrix L_emm = C @ X_ref, shape (n_contrasts, n_coef).

    Note:
        The composed contrast L_emm satisfies:
            L_emm @ beta = C @ (X_ref @ beta) = C @ EMMs

        This is used by joint_tests() to perform F-tests on EMM contrasts.
    """
    C = contrast_matrix
    X_ref = emm_result.X_ref

    # Compose contrast with prediction matrix
    # L_emm @ beta = C @ EMMs
    L_emm = C @ X_ref

    # Contrast estimates
    estimates = L_emm @ coef

    # Variance of contrasts
    # Var(L @ beta) = L @ Var(beta) @ L.T
    vcov_contrast = L_emm @ vcov @ L_emm.T
    se = compute_se_from_vcov(vcov_contrast)

    return EMMContrastResult(
        estimates=estimates,
        se=se,
        L_emm=L_emm,
    )


def format_emm_table(
    emm_result: EMMResult,
    conf_int: float = 0.95,
    type: str = "link",  # noqa: A002
    family=None,
) -> pl.DataFrame:
    """Format EMM results as a polars DataFrame.

    Args:
        emm_result: Result from compute_emm().
        conf_int: Confidence level for intervals.
        type: Scale for output ("link" or "response"). For GLM/GLMM with
            type="response", applies inverse link and delta method for SE.
        family: GLM family object with link_inverse and link_deriv methods.
            Required when type="response" for GLM/GLMM. None for lm/lmer.

    Returns:
        DataFrame with columns from grid plus:
        [estimate, se, df, ci_lower, ci_upper]

    Note:
        Does not include t_value or p_value columns. Testing H0: mean = 0
        is not meaningful for marginal means. Use contrasts to get p-values
        for meaningful comparisons.
    """
    # Get link-scale values
    emmeans_link = emm_result.emmeans
    se_link = emm_result.se
    df = emm_result.df

    # Transform to response scale if requested and family is available
    if type == "response" and family is not None:
        # Apply inverse link to get response scale means
        # μ = g⁻¹(η)
        emmeans_resp = np.asarray(family.link_inverse(emmeans_link))

        # Delta method for SE: SE_μ = SE_η * |dμ/dη|
        # dμ/dη = 1 / (dη/dμ) = 1 / link_deriv(μ)
        link_deriv_vals = np.asarray(family.link_deriv(emmeans_resp))
        # Handle zero derivatives to avoid division by zero
        link_deriv_vals = np.where(
            np.abs(link_deriv_vals) < 1e-10, 1e-10, link_deriv_vals
        )
        se_resp = se_link / np.abs(link_deriv_vals)

        # Use response scale values
        emmeans = emmeans_resp
        se = se_resp
    else:
        # Use link scale values (default, or no family available)
        emmeans = emmeans_link
        se = se_link

    # Compute CI critical values
    if isinstance(df, np.ndarray):
        t_crit = np.array([compute_t_critical(conf_int, d) for d in df])
    else:
        t_crit = compute_t_critical(conf_int, df)

    # Compute CI on reported scale
    ci_lower = emmeans - t_crit * se
    ci_upper = emmeans + t_crit * se

    # Build result DataFrame
    result = emm_result.grid.clone()

    # Add EMM columns (no t_value/p_value - testing mean=0 is meaningless)
    columns = [
        pl.lit(emmeans).alias("estimate"),
        pl.lit(se).alias("se"),
        pl.lit(
            emm_result.df
            if not isinstance(emm_result.df, np.ndarray)
            else emm_result.df
        ).alias("df"),
        pl.lit(ci_lower).alias("ci_lower"),
        pl.lit(ci_upper).alias("ci_upper"),
    ]

    result = result.with_columns(columns)

    return result


def format_contrast_table(
    contrast_labels: list[str],
    estimates: np.ndarray,
    se: np.ndarray,
    df: float | np.ndarray,
    conf_int: float = 0.95,
    p_adjust: str = "none",
) -> pl.DataFrame:
    """Format contrast results as a polars DataFrame.

    Args:
        contrast_labels: Labels for each contrast (e.g., "B - A").
        estimates: Contrast estimates, shape (n_contrasts,).
        se: Standard errors, shape (n_contrasts,).
        df: Degrees of freedom (scalar or array for Satterthwaite).
        conf_int: Confidence level for intervals.
        p_adjust: P-value adjustment method.

    Returns:
        DataFrame with columns:
        [contrast, estimate, se, ci_lower, ci_upper, df, t_value, p_value]
        If p_adjust != "none", also includes p_adjusted column.
    """
    # Compute t-statistics (handle SE=0 without warning)
    t_values = np.divide(
        estimates, se, out=np.full_like(estimates, np.nan), where=se != 0
    )

    # Compute p-values (two-sided)
    if isinstance(df, np.ndarray):
        p_values = np.array(
            [compute_pvalue(np.array([t]), d)[0] for t, d in zip(t_values, df)]
        )
        t_crit = np.array([compute_t_critical(conf_int, d) for d in df])
    else:
        p_values = compute_pvalue(t_values, df)
        t_crit = compute_t_critical(conf_int, df)

    # Apply p-value adjustment if requested
    p_adjusted = None
    if p_adjust.lower() != "none":
        p_adjusted = adjust_pvalues(p_values, method=p_adjust)

    # Compute confidence intervals
    ci_lower = estimates - t_crit * se
    ci_upper = estimates + t_crit * se

    # Build result DataFrame
    result = pl.DataFrame({"contrast": contrast_labels})

    columns = [
        pl.lit(estimates).alias("estimate"),
        pl.lit(se).alias("se"),
        pl.lit(ci_lower).alias("ci_lower"),
        pl.lit(ci_upper).alias("ci_upper"),
        pl.lit(df if not isinstance(df, np.ndarray) else df).alias("df"),
        pl.lit(t_values).alias("t_value"),
        pl.lit(p_values).alias("p_value"),
    ]

    if p_adjusted is not None:
        columns.append(pl.lit(p_adjusted).alias("p_adjusted"))

    result = result.with_columns(columns)

    return result
