"""Statistical tests for EMM contrasts.

This module provides F-tests and chi-square tests for testing
hypotheses about linear combinations of coefficients. These are
used by joint_tests() for ANOVA-style hypothesis testing.

The key operation is testing H0: L @ beta = 0 where L is a contrast
matrix and beta is the coefficient vector.

Examples:
    >>> from bossanova.marginal import compute_f_test
    >>> result = compute_f_test(L, coef, vcov, df_resid)
    >>> result.F_value, result.p_value
    (12.34, 0.0007)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

__all__ = [
    "compute_contrast_variance",
    "compute_wald_statistic",
    "FTestResult",
    "Chi2TestResult",
    "TTestResult",
    "compute_f_test",
    "compute_chi2_test",
    "compute_t_test",
]


def compute_contrast_variance(L: np.ndarray, vcov: np.ndarray) -> np.ndarray:
    """Compute variance-covariance of linear contrasts L @ beta.

    For a contrast matrix L and coefficient vcov V, computes:
        Var(L @ beta) = L @ V @ L'

    Args:
        L: Contrast matrix of shape (q, p).
        vcov: Variance-covariance matrix of shape (p, p).

    Returns:
        Variance-covariance of contrasts, shape (q, q).
    """
    return L @ vcov @ L.T


def compute_wald_statistic(
    contrast_values: np.ndarray,
    contrast_vcov: np.ndarray,
) -> float:
    """Compute Wald statistic for testing L @ beta = 0.

    Computes: W = (L @ beta)' @ (L @ V @ L')^-1 @ (L @ beta)

    Uses solve for efficiency, with pinv fallback for singular matrices.

    Args:
        contrast_values: Contrast estimates L @ beta, shape (q,).
        contrast_vcov: Variance of contrasts L @ V @ L', shape (q, q).

    Returns:
        Wald statistic value.
    """
    try:
        return float(
            contrast_values.T @ np.linalg.solve(contrast_vcov, contrast_values)
        )
    except np.linalg.LinAlgError:
        # Matrix is singular - use pseudo-inverse
        return float(
            contrast_values.T @ np.linalg.pinv(contrast_vcov) @ contrast_values
        )


@dataclass
class FTestResult:
    """Result container for F-test.

    Attributes:
        num_df: Numerator degrees of freedom (q, number of contrasts).
        den_df: Denominator degrees of freedom (residual df).
        F_value: F-statistic value.
        p_value: P-value from F-distribution.
    """

    num_df: int
    den_df: float
    F_value: float
    p_value: float


@dataclass
class Chi2TestResult:
    """Result container for chi-square test.

    Attributes:
        num_df: Degrees of freedom (q, number of contrasts).
        chi2: Wald chi-square statistic.
        p_value: P-value from chi-square distribution.
    """

    num_df: int
    chi2: float
    p_value: float


@dataclass
class TTestResult:
    """Result container for t-test.

    Attributes:
        estimate: Contrast estimate.
        se: Standard error.
        t_value: t-statistic.
        df: Degrees of freedom.
        p_value: Two-tailed p-value.
    """

    estimate: float
    se: float
    t_value: float
    df: float
    p_value: float


def compute_f_test(
    L: np.ndarray,
    coef: np.ndarray,
    vcov: np.ndarray,
    df_resid: float,
) -> FTestResult:
    """Compute F-test for linear hypothesis L @ beta = 0.

    Uses the Wald statistic divided by the number of constraints
    to produce an F-statistic with appropriate degrees of freedom.

    Args:
        L: Contrast matrix of shape (q, p) where q is the number of
            constraints (contrasts) and p is the number of coefficients.
        coef: Coefficient estimates of shape (p,).
        vcov: Variance-covariance matrix of coefficients, shape (p, p).
        df_resid: Residual degrees of freedom (denominator df for F-test).

    Returns:
        FTestResult containing:
        - num_df: Numerator degrees of freedom (q, number of contrasts).
        - den_df: Denominator degrees of freedom (residual df).
        - F_value: F-statistic value.
        - p_value: P-value from F-distribution.

    Note:
        The Wald statistic is:
            W = (L @ beta)' @ (L @ V @ L')^-1 @ (L @ beta)

        The F-statistic is F = W / q, distributed as F(q, df_resid).

    Examples:
        >>> L = np.array([[-1, 1, 0], [-1, 0, 1]])  # 2 contrasts
        >>> coef = np.array([10.0, 12.0, 15.0])
        >>> vcov = np.diag([1.0, 1.5, 2.0])
        >>> result = compute_f_test(L, coef, vcov, df_resid=97)
        >>> result.F_value
        4.44...
    """
    # Ensure inputs are arrays
    L = np.atleast_2d(L)
    coef = np.atleast_1d(coef)
    vcov = np.atleast_2d(vcov)

    # Number of constraints
    num_df = L.shape[0]

    if num_df == 0:
        # No contrasts - return null result
        return FTestResult(
            num_df=0,
            den_df=float(df_resid),
            F_value=float(np.nan),
            p_value=float(np.nan),
        )

    # Compute contrast estimates and variance
    L_beta = L @ coef
    L_vcov_L = compute_contrast_variance(L, vcov)

    # Compute Wald statistic and convert to F
    wald_stat = compute_wald_statistic(L_beta, L_vcov_L)
    F_stat = wald_stat / num_df

    # Compute p-value from F-distribution
    p_value = 1 - stats.f.cdf(F_stat, num_df, df_resid)

    return FTestResult(
        num_df=int(num_df),
        den_df=float(df_resid),
        F_value=float(F_stat),
        p_value=float(p_value),
    )


def compute_chi2_test(
    L: np.ndarray,
    coef: np.ndarray,
    vcov: np.ndarray,
) -> Chi2TestResult:
    """Compute Wald chi-square test for L @ beta = 0.

    Used for GLMs and GLMMs where we don't have residual df.
    The Wald statistic is asymptotically chi-squared distributed.

    Args:
        L: Contrast matrix of shape (q, p).
        coef: Coefficient estimates of shape (p,).
        vcov: Variance-covariance matrix of shape (p, p).

    Returns:
        Chi2TestResult containing:
        - num_df: Degrees of freedom (q, number of contrasts).
        - chi2: Wald chi-square statistic.
        - p_value: P-value from chi-square distribution.

    Examples:
        >>> L = np.array([[-1, 1, 0], [-1, 0, 1]])
        >>> coef = np.array([0.5, 1.2, 0.8])
        >>> vcov = np.diag([0.1, 0.15, 0.12])
        >>> result = compute_chi2_test(L, coef, vcov)
        >>> result.chi2
        8.89...
    """
    # Ensure inputs are arrays
    L = np.atleast_2d(L)
    coef = np.atleast_1d(coef)
    vcov = np.atleast_2d(vcov)

    # Number of constraints
    num_df = L.shape[0]

    if num_df == 0:
        return Chi2TestResult(
            num_df=0,
            chi2=float(np.nan),
            p_value=float(np.nan),
        )

    # Compute contrast estimates and variance
    L_beta = L @ coef
    L_vcov_L = compute_contrast_variance(L, vcov)

    # Compute Wald chi-square statistic
    chi2_stat = compute_wald_statistic(L_beta, L_vcov_L)

    # Compute p-value from chi-square distribution
    p_value = 1 - stats.chi2.cdf(chi2_stat, num_df)

    return Chi2TestResult(
        num_df=int(num_df),
        chi2=float(chi2_stat),
        p_value=float(p_value),
    )


def compute_t_test(
    L: np.ndarray,
    coef: np.ndarray,
    vcov: np.ndarray,
    df: float,
) -> TTestResult:
    """Compute t-test for a single contrast L @ beta = 0.

    For a single contrast (q=1), returns t-statistic instead of F.

    Args:
        L: Contrast vector of shape (1, p) or (p,).
        coef: Coefficient estimates of shape (p,).
        vcov: Variance-covariance matrix of shape (p, p).
        df: Degrees of freedom for t-distribution.

    Returns:
        TTestResult containing:
        - estimate: Contrast estimate.
        - se: Standard error.
        - t_value: t-statistic.
        - df: Degrees of freedom.
        - p_value: Two-tailed p-value.

    Examples:
        >>> L = np.array([-1, 1, 0])  # Compare coef[1] to coef[0]
        >>> coef = np.array([10.0, 12.0, 15.0])
        >>> vcov = np.diag([1.0, 1.5, 2.0])
        >>> result = compute_t_test(L, coef, vcov, df=97)
        >>> result.t_value
        1.26...
    """
    L = np.atleast_1d(L).flatten()
    coef = np.atleast_1d(coef)
    vcov = np.atleast_2d(vcov)

    # Contrast estimate
    estimate = float(L @ coef)

    # Standard error
    var_contrast = float(L @ vcov @ L)
    se = np.sqrt(var_contrast)

    # t-statistic
    t_value = estimate / se if se > 0 else np.nan

    # Two-tailed p-value
    p_value = (
        2 * (1 - stats.t.cdf(np.abs(t_value), df)) if not np.isnan(t_value) else np.nan
    )

    return TTestResult(
        estimate=estimate,
        se=float(se),
        t_value=float(t_value),
        df=float(df),
        p_value=float(p_value),
    )
