"""Likelihood ratio test for comparing nested mixed models.

This module provides the lrt() convenience function as a thin wrapper
around compare() for mixed model comparisons.
"""

from typing import Any

import polars as pl

from bossanova.stats.compare import compare

__all__ = ["lrt"]


def lrt(*models: Any, sort: bool = True) -> pl.DataFrame:
    """Likelihood ratio test for comparing nested mixed models.

    Convenience wrapper for `compare(*models, method="lrt")` specifically
    designed for comparing lmer and glmer models.

    Args:
        *models: Two or more fitted lmer or glmer models to compare.
            Models should be nested (simpler model is a subset of complex model).
        sort: If True (default), sort models by complexity (fewest parameters first),
            matching R's anova() behavior. Set to False to preserve input order.

    Returns:
        DataFrame with columns:
            - model: Model formula string
            - npar: Number of parameters
            - AIC: Akaike Information Criterion
            - BIC: Bayesian Information Criterion
            - loglik: Log-likelihood
            - deviance: -2 * log-likelihood
            - chi2: Chi-squared statistic (deviance difference)
            - df: Degrees of freedom (parameter difference)
            - p_value: P-value from chi-squared distribution

    Raises:
        ValueError: If fewer than 2 models are provided.
        TypeError: If models are not lmer or glmer instances.

    Note:
        For valid likelihood ratio tests, models should be fit with the same
        method (both REML or both ML). A warning is issued if REML settings
        differ between models.

    Examples:
        >>> from bossanova import lmer, lrt
        >>> m1 = lmer("Reaction ~ Days + (1|Subject)", data=sleepstudy).fit(method="ML")
        >>> m2 = lmer("Reaction ~ Days + (Days|Subject)", data=sleepstudy).fit(method="ML")
        >>> lrt(m1, m2)
        ┌───────────────────────────────┬──────┬────────┬────────┬─────────┬──────────┬───────┬────┬──────────┐
        │ model                         ┆ npar ┆ AIC    ┆ BIC    ┆ loglik  ┆ deviance ┆ chi2  ┆ df ┆ p_value  │
        ├───────────────────────────────┼──────┼────────┼────────┼─────────┼──────────┼───────┼────┼──────────┤
        │ Reaction ~ Days + (1|Subject) ┆ 4    ┆ 1802.1 ┆ 1814.8 ┆ -897.04 ┆ 1794.1   ┆       ┆    ┆          │
        │ Reaction ~ Days + (Days|Subj) ┆ 6    ┆ 1763.9 ┆ 1783.1 ┆ -875.97 ┆ 1751.9   ┆ 42.14 ┆ 2  ┆ 7.07e-10 │
        └───────────────────────────────┴──────┴────────┴────────┴─────────┴──────────┴───────┴────┴──────────┘
    """
    # Validate model types
    for model in models:
        model_type = type(model).__name__
        if model_type not in ("lmer", "glmer"):
            raise TypeError(
                f"lrt() requires lmer or glmer models, got {model_type}. "
                "For lm models, use compare(..., method='f'). "
                "For glm models, use compare(..., method='deviance')."
            )

    return compare(*models, method="lrt", sort=sort)
