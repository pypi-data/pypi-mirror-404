"""Statistical inference utilities.

Functions for computing standard errors, confidence intervals, p-values,
and hypothesis tests using the delta method and asymptotic normality.
"""

import numpy as np
from scipy import stats

__all__ = [
    "parse_conf_int",
    "compute_t_critical",
    "compute_z_critical",
    "compute_se_from_vcov",
    "compute_ci",
    "compute_pvalue",
    "delta_method_se",
    "adjust_pvalues",
    "format_pvalue_with_stars",
]


def parse_conf_int(conf_int: float | int | str) -> float:
    """Parse flexible confidence interval input to float.

    Args:
        conf_int: Confidence interval specification. Accepts:
            float in (0, 1): treated as confidence level,
            int in (1, 99]: converted to proportion (e.g., 95 -> 0.95),
            str: parsed as number with optional '%' (e.g., "95%", "95").

    Returns:
        Confidence level as proportion in (0, 1).

    Raises:
        ValueError: If conf_int cannot be parsed or is out of valid range.

    Examples:
        >>> parse_conf_int(0.95)
        0.95
        >>> parse_conf_int(95)
        0.95
        >>> parse_conf_int("95%")
        0.95
    """
    if isinstance(conf_int, str):
        # Remove '%' if present
        conf_int = conf_int.strip().rstrip("%")
        try:
            conf_int = float(conf_int)
        except ValueError:
            raise ValueError(f"Cannot parse conf_int: {conf_int}")

    # Convert int/float to proportion
    if isinstance(conf_int, (int, float)):
        if 0 < conf_int < 1:
            # Already a proportion
            return float(conf_int)
        elif 1 < conf_int <= 100:
            # Percentage notation - but only accept integers to avoid mistakes
            # like conf_int=1.5 which is likely meant to be 0.95
            if conf_int != int(conf_int):
                raise ValueError(
                    f"conf_int={conf_int} is ambiguous. "
                    f"Use {conf_int / 100:.4f} for {conf_int}% CI, "
                    f"or an integer like 95 for 95% CI."
                )
            return float(conf_int) / 100.0
        else:
            raise ValueError(
                f"conf_int must be in (0, 1) or an integer in [2, 100], got {conf_int}"
            )
    else:
        raise ValueError(f"conf_int must be float, int, or str, got {type(conf_int)}")


def compute_t_critical(conf_int: float, df: float) -> float:
    """Compute t-distribution critical value for two-tailed confidence interval.

    Args:
        conf_int: Confidence level (0 < conf_int < 1).
        df: Degrees of freedom.

    Returns:
        Critical value from t-distribution.

    Examples:
        >>> crit = compute_t_critical(0.95, df=10)
        >>> abs(crit - 2.228) < 0.01
        True
    """
    if not 0 < conf_int < 1:
        raise ValueError(f"conf_int must be between 0 and 1, got {conf_int}")

    alpha = 1 - conf_int
    return stats.t.ppf(1 - alpha / 2, df=df)


def compute_z_critical(conf_int: float) -> float:
    """Compute z-distribution critical value for two-tailed confidence interval.

    Args:
        conf_int: Confidence level (0 < conf_int < 1).

    Returns:
        Critical value from standard normal distribution.

    Examples:
        >>> crit = compute_z_critical(0.95)
        >>> abs(crit - 1.96) < 0.01
        True
    """
    if not 0 < conf_int < 1:
        raise ValueError(f"conf_int must be between 0 and 1, got {conf_int}")

    alpha = 1 - conf_int
    return stats.norm.ppf(1 - alpha / 2)


def compute_se_from_vcov(vcov: np.ndarray) -> np.ndarray:
    """Compute standard errors from variance-covariance matrix.

    Args:
        vcov: Variance-covariance matrix of parameter estimates, shape (p, p).

    Returns:
        Standard errors for each parameter, shape (p,).

    Examples:
        >>> vcov = np.array([[0.04, 0.01], [0.01, 0.09]])
        >>> se = compute_se_from_vcov(vcov)
        >>> np.allclose(se, [0.2, 0.3])
        True
    """
    return np.sqrt(np.diag(vcov))


def compute_ci(
    estimate: np.ndarray,
    se: np.ndarray,
    critical: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute confidence interval bounds.

    Args:
        estimate: Point estimates.
        se: Standard errors.
        critical: Critical value from distribution (t or z).

    Returns:
        Tuple of (ci_lower, ci_upper) arrays with confidence bounds.

    Examples:
        >>> estimate = np.array([1.5, 2.0])
        >>> se = np.array([0.2, 0.3])
        >>> critical = 1.96
        >>> ci_lower, ci_upper = compute_ci(estimate, se, critical)
    """
    ci_lower = estimate - critical * se
    ci_upper = estimate + critical * se

    return ci_lower, ci_upper


def compute_pvalue(
    statistic: np.ndarray,
    df: float | None = None,
) -> np.ndarray:
    """Compute two-tailed p-values from test statistics.

    Uses t-distribution if df is provided, otherwise uses normal distribution.

    Args:
        statistic: Test statistics (t or z values).
        df: Degrees of freedom for t-distribution. If None, uses normal distribution.

    Returns:
        Two-tailed p-values.

    Examples:
        >>> statistic = np.array([2.5, -1.8])
        >>> p = compute_pvalue(statistic, df=20)
        >>> all((p >= 0) & (p <= 1))
        True
    """
    if df is not None:
        # t-distribution
        p_values = 2 * (1 - stats.t.cdf(np.abs(statistic), df=df))
    else:
        # Normal distribution
        p_values = 2 * (1 - stats.norm.cdf(np.abs(statistic)))

    return p_values


def delta_method_se(X_pred: np.ndarray, vcov: np.ndarray) -> np.ndarray:
    """Compute standard errors for predictions via delta method.

    For predictions Xβ, the variance is: Var(Xβ) = X Var(β) X^T

    Args:
        X_pred: Design matrix for predictions, shape (n, p).
        vcov: Variance-covariance matrix of parameter estimates, shape (p, p).

    Returns:
        Standard errors for each prediction, shape (n,).

    Note:
        Uses efficient computation: SE_i = sqrt(sum((X_pred @ vcov) * X_pred, axis=1))
        which avoids forming the full quadratic form.

    Examples:
        >>> X_new = np.array([[1, 2], [1, 3]])
        >>> vcov = np.array([[0.1, 0.01], [0.01, 0.05]])
        >>> se = delta_method_se(X_new, vcov)
    """
    # Efficient computation: sqrt(diag(X @ vcov @ X^T))
    se = np.sqrt(np.sum((X_pred @ vcov) * X_pred, axis=1))
    return se


def adjust_pvalues(
    pvalues: np.ndarray,
    method: str = "none",
) -> np.ndarray:
    """Adjust p-values for multiple comparisons.

    Implements standard p-value adjustment methods matching R's p.adjust().

    Args:
        pvalues: Raw p-values, shape (n,).
        method: Adjustment method. One of:
            - "none": No adjustment (return raw p-values)
            - "bonferroni": Bonferroni correction (p * n)
            - "holm": Holm step-down (default in many R packages)
            - "hochberg": Hochberg step-up
            - "bh" or "fdr": Benjamini-Hochberg FDR control
            - "by": Benjamini-Yekutieli FDR (conservative, handles dependence)

    Returns:
        Adjusted p-values, clipped to [0, 1].

    Examples:
        >>> p = np.array([0.01, 0.04, 0.03, 0.005])
        >>> adjust_pvalues(p, method="bonferroni")
        array([0.04, 0.16, 0.12, 0.02])
        >>> adjust_pvalues(p, method="holm")
        array([0.03, 0.08, 0.06, 0.02])
    """
    p = np.asarray(pvalues).copy()
    n = len(p)

    if n == 0:
        return p

    method = method.lower()

    if method == "none":
        return p

    elif method == "bonferroni":
        # Simple: multiply all p-values by n
        return np.minimum(p * n, 1.0)

    elif method == "holm":
        # Holm step-down: order p-values, adjust by position, enforce monotonicity
        order = np.argsort(p)
        sorted_p = p[order]
        adjusted = np.zeros(n)

        for i in range(n):
            adjusted[i] = sorted_p[i] * (n - i)

        # Enforce monotonicity (each adjusted p >= previous)
        for i in range(1, n):
            adjusted[i] = max(adjusted[i], adjusted[i - 1])

        # Restore original order
        result = np.zeros(n)
        result[order] = adjusted
        return np.minimum(result, 1.0)

    elif method == "hochberg":
        # Hochberg step-up: like Holm but works backwards
        order = np.argsort(p)[::-1]  # Descending order
        sorted_p = p[order]
        adjusted = np.zeros(n)

        for i in range(n):
            rank = n - i  # Rank from largest
            adjusted[i] = sorted_p[i] * rank

        # Enforce monotonicity (going backwards)
        for i in range(1, n):
            adjusted[i] = min(adjusted[i], adjusted[i - 1])

        # Restore original order
        result = np.zeros(n)
        result[order] = adjusted
        return np.minimum(result, 1.0)

    elif method in ("bh", "fdr"):
        # Benjamini-Hochberg: control FDR
        # Use scipy's implementation for correctness
        from scipy.stats import false_discovery_control

        return false_discovery_control(p, method="bh")

    elif method == "by":
        # Benjamini-Yekutieli: conservative FDR for dependent tests
        from scipy.stats import false_discovery_control

        return false_discovery_control(p, method="by")

    else:
        valid = ["none", "bonferroni", "holm", "hochberg", "bh", "fdr", "by"]
        raise ValueError(f"Unknown p_adjust method: {method!r}. Valid: {valid}")


def format_pvalue_with_stars(p_val: float) -> str:
    """Format p-value with R-style significance codes.

    Args:
        p_val: The p-value to format.

    Returns:
        Formatted string with p-value and significance stars (fixed 12-char width).
        Uses R's significance coding: '***' < 0.001 < '**' < 0.01 < '*' < 0.05 < '.' < 0.1

    Examples:
        >>> format_pvalue_with_stars(0.0001)
        '< 0.001 *** '
        >>> format_pvalue_with_stars(0.023)
        '  0.023 *   '
    """
    if p_val < 0.001:
        return "< 0.001 *** "
    elif p_val < 0.01:
        return f"{p_val:7.3f} **  "
    elif p_val < 0.05:
        return f"{p_val:7.3f} *   "
    elif p_val < 0.1:
        return f"{p_val:7.3f} .   "
    else:
        return f"{p_val:7.3f}     "
