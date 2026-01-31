"""Joint tests for model terms (emmeans-style ANOVA).

This module implements joint_tests() which tests each model term using
direct coefficient F-tests (or chi-square for GLMs). This matches
R's emmeans::joint_tests() behavior.

For each term type:
- Continuous variables: F-test on single coefficient (df1=1)
- Categorical factors: Joint F-test on all indicator coefficients
- Interactions: Joint F-test on all interaction coefficients

This is the ONLY ANOVA method in bossanova - we intentionally don't
implement Type I, II, or III sequential ANOVA.

Examples:
    >>> from bossanova import lm
    >>> model = lm("y ~ x * group", data=df)  # x continuous, group factor
    >>> model.fit()
    >>> model.jointtest()  # Calls joint_tests internally
    shape: (3, 5)
    ┌─────────┬─────┬──────┬─────────┬─────────┐
    │ term    ┆ df1 ┆ df2  ┆ f_ratio ┆ p_value │
    │ str     ┆ i64 ┆ f64  ┆ f64     ┆ f64     │
    ╞═════════╪═════╪══════╪═════════╪═════════╡
    │ x       ┆ 1   ┆ 96.0 ┆ 0.57    ┆ 0.4536  │
    │ group   ┆ 1   ┆ 96.0 ┆ 0.41    ┆ 0.5246  │
    │ x:group ┆ 1   ┆ 96.0 ┆ 0.01    ┆ 0.9039  │
    └─────────┴─────┴──────┴─────────┴─────────┘
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import polars as pl

from bossanova.marginal.hypothesis import compute_f_test, compute_chi2_test

if TYPE_CHECKING:
    from bossanova.models.base import BaseModel

__all__ = [
    "joint_tests",
]


def joint_tests(
    model: BaseModel,
    errors: str = "auto",
) -> pl.DataFrame:
    """Compute joint tests for all model terms (emmeans-style ANOVA).

    Tests each model term (continuous variables, factors, and interactions)
    using direct coefficient tests. This matches R's emmeans::joint_tests()
    behavior.

    For each term:
    - Continuous variables: F-test on the single coefficient (df1=1)
    - Categorical factors: Joint F-test on all indicator coefficients
    - Interactions: Joint F-test on all interaction coefficients

    Args:
        model: Fitted model (lm, glm, lmer, glmer).
        errors: Error structure assumption for robust F-tests (lm only):
            - None: Use standard OLS F-test (default)
            - "hetero": Robust F-test with HC3 sandwich covariance
            - "unequal_var": Welch's ANOVA (group-specific variances)
            - "HC0", "HC1", "HC2", "HC3": Specific sandwich estimators

    Returns:
        DataFrame with columns:
        - term: Model term name
        - df1: Numerator degrees of freedom (number of coefficients tested)
        - df2: Denominator df (for lm/lmer) or omitted (for glm/glmer)
        - f_ratio or Chisq: Test statistic
        - p_value: P-value

    Raises:
        RuntimeError: If model is not fitted.
        ValueError: If errors is specified for non-lm models.

    Note:
        This function is the underlying implementation for BaseModel.jointtest().
        Terms are tested in model order: main effects first, then interactions.

    Examples:
        >>> model = lm("y ~ x * A", data=df)  # x continuous, A factor
        >>> model.fit()
        >>> joint_tests(model)
        shape: (3, 5)
        ┌──────┬─────┬──────┬─────────┬─────────┐
        │ term ┆ df1 ┆ df2  ┆ f_ratio ┆ p_value │
        │ str  ┆ i64 ┆ f64  ┆ f64     ┆ f64     │
        ╞══════╪═════╪══════╪═════════╪═════════╡
        │ x    ┆ 1   ┆ 96.0 ┆ 0.57    ┆ 0.4536  │
        │ A    ┆ 1   ┆ 96.0 ┆ 0.41    ┆ 0.5246  │
        │ x:A  ┆ 1   ┆ 96.0 ┆ 0.01    ┆ 0.9039  │
        └──────┴─────┴──────┴─────────┴─────────┘

        >>> # Welch's ANOVA (unequal variances)
        >>> joint_tests(model, errors="unequal_var")

        >>> # Robust ANOVA with HC3
        >>> joint_tests(model, errors="hetero")
    """
    # Check fitted status
    if not model.is_fitted:
        raise RuntimeError("Model must be fitted before computing joint tests")

    # Detect model type for dispatch
    model_type = _get_model_type(model)

    # Validate errors parameter
    # - 'unequal_var' is lm-specific (Welch)
    # - 'hetero' works for lm and glm
    # - lmer/glmer only support 'auto'/'iid'
    if errors == "unequal_var":
        if model_type == "lm":
            pass  # Valid for lm
        elif model_type == "glm":
            raise ValueError(
                "errors='unequal_var' is not applicable to GLM.\n\n"
                "GLM already handles group-specific variances through the variance "
                "function (e.g., μ(1-μ) for binomial). Unlike linear models where "
                "Welch's approach corrects for unequal group variances, GLM builds "
                "this into the likelihood.\n\n"
                "If you suspect the variance function is misspecified (e.g., "
                "overdispersion), use errors='hetero' for sandwich standard errors."
            )
        else:
            raise ValueError(
                f"errors='unequal_var' is only supported for lm models, got {model_type}."
            )
    elif errors in ("hetero", "HC0", "HC1", "HC2", "HC3"):
        if model_type not in ("lm", "glm"):
            raise ValueError(
                f"errors='{errors}' is only supported for lm/glm models, got {model_type}. "
                "For mixed models, use errors='auto' or 'iid'."
            )
        # HC2/HC3 not well-defined for GLM
        if model_type == "glm" and errors in ("HC2", "HC3"):
            raise ValueError(
                f"errors='{errors}' is not supported for GLM. "
                "Use 'hetero', 'HC0', or 'HC1' instead."
            )
    elif errors not in ("auto", "iid"):
        raise ValueError(
            f"Unknown errors type: {errors!r}. "
            "Use 'auto', 'iid', 'hetero', 'unequal_var', or 'HC0'/'HC1'/'HC2'/'HC3'."
        )

    # Get model components
    coef = np.asarray(model._coef)
    vcov = np.asarray(model._vcov)
    X_names = model._X_names

    # Handle errors parameter for lm models
    df_resid = None
    welch_df = None

    if model_type == "lm":
        df_resid = model._df_resid

        if errors in ("hetero", "HC0", "HC1", "HC2", "HC3"):
            # Compute HC vcov for robust F-test
            from bossanova.stats.sandwich import compute_hc_vcov

            hc_type = "HC3" if errors == "hetero" else errors

            # (X'X)^{-1} = vcov / sigma^2
            sigma_sq = model._sigma**2
            XtX_inv = model._vcov / sigma_sq

            # Get valid (non-NA) data
            X_valid = model._X[model._valid_mask]
            resid_valid = model._residuals[model._valid_mask]

            vcov = compute_hc_vcov(X_valid, resid_valid, XtX_inv, hc_type=hc_type)

        elif errors == "unequal_var":
            # Welch's ANOVA - compute cell-based variances
            from bossanova.stats.welch import (
                compute_cell_info,
                extract_factors_from_formula,
                welch_satterthwaite_df,
            )

            factors = extract_factors_from_formula(model._formula, model._data)

            if not factors:
                raise ValueError(
                    "errors='unequal_var' requires at least one factor (categorical) "
                    "variable in the formula. Found only continuous predictors.\n"
                    "For arbitrary heteroscedasticity, use errors='hetero' instead."
                )

            # Compute cell-based variances
            valid_data = model._data.filter(pl.Series(model._valid_mask))
            cell_info = compute_cell_info(
                model._residuals[model._valid_mask],
                valid_data,
                factors,
            )

            # Welch df replaces standard df_resid
            welch_df = welch_satterthwaite_df(
                cell_info.cell_variances,
                cell_info.cell_counts,
            )

    elif model_type == "glm":
        # GLM uses chi-square tests (df_resid stays None)
        if errors in ("hetero", "HC0", "HC1"):
            # Compute sandwich vcov for robust chi-square test
            from bossanova.stats.sandwich import compute_glm_hc_vcov

            hc_type = "HC0" if errors == "hetero" else errors

            X_valid = model._X[model._valid_mask]
            resid_valid = model._residuals[model._valid_mask]
            weights_valid = model._irls_weights[model._valid_mask]

            vcov = compute_glm_hc_vcov(
                X_valid, resid_valid, weights_valid, model._XtWX_inv, hc_type=hc_type
            )

    elif model_type == "lmer":
        df_resid = model._df_resid
    # else: glmer uses chi-square, df_resid stays None

    # Build L matrices for each term (groups coefficients by term)
    term_L = _build_term_L_matrices(model._builder, X_names)

    # Exclude random effects grouping factors (lmer/glmer only test fixed effects)
    if hasattr(model, "_group_names") and model._group_names:
        term_L = {k: v for k, v in term_L.items() if k not in model._group_names}

    if not term_L:
        # No testable terms - return empty DataFrame
        if model_type in ("lm", "lmer"):
            return pl.DataFrame(
                schema={
                    "term": pl.Utf8,
                    "df1": pl.Int64,
                    "df2": pl.Float64,
                    "f_ratio": pl.Float64,
                    "p_value": pl.Float64,
                }
            )
        else:
            return pl.DataFrame(
                schema={
                    "term": pl.Utf8,
                    "df1": pl.Int64,
                    "Chisq": pl.Float64,
                    "p_value": pl.Float64,
                }
            )

    results = []

    # Order terms: main effects first (no ":"), then interactions (with ":")
    main_effects = [t for t in term_L.keys() if ":" not in t]
    interactions = [t for t in term_L.keys() if ":" in t]
    ordered_terms = main_effects + interactions

    for term_name in ordered_terms:
        L = term_L[term_name]

        try:
            # Perform test based on model type
            if model_type in ("lm", "lmer") and df_resid is not None:
                # Use Welch df if available, otherwise standard df
                test_df = welch_df if welch_df is not None else df_resid
                test_result = compute_f_test(L, coef, vcov, test_df)
                results.append(
                    {
                        "term": term_name,
                        "df1": test_result.num_df,
                        "df2": test_result.den_df,
                        "f_ratio": test_result.F_value,
                        "p_value": test_result.p_value,
                    }
                )
            else:
                # glm/glmer use chi-square
                test_result = compute_chi2_test(L, coef, vcov)
                results.append(
                    {
                        "term": term_name,
                        "df1": test_result.num_df,
                        "Chisq": test_result.chi2,
                        "p_value": test_result.p_value,
                    }
                )

        except (ValueError, np.linalg.LinAlgError) as e:
            import warnings

            warnings.warn(f"Could not compute joint test for term '{term_name}': {e}")
            continue

    # Create result DataFrame
    if not results:
        if model_type in ("lm", "lmer"):
            return pl.DataFrame(
                schema={
                    "term": pl.Utf8,
                    "df1": pl.Int64,
                    "df2": pl.Float64,
                    "f_ratio": pl.Float64,
                    "p_value": pl.Float64,
                }
            )
        else:
            return pl.DataFrame(
                schema={
                    "term": pl.Utf8,
                    "df1": pl.Int64,
                    "Chisq": pl.Float64,
                    "p_value": pl.Float64,
                }
            )

    return pl.DataFrame(results)


def _get_model_type(model: BaseModel) -> str:
    """Detect model type using isinstance checks.

    Args:
        model: A fitted model instance.

    Returns:
        Model type: 'lm', 'glm', 'lmer', or 'glmer'.

    Raises:
        ValueError: If model type is not recognized.
    """
    # Lazy imports to avoid circular dependencies
    from bossanova.models.lm import lm as LMClass
    from bossanova.models.glm import glm as GLMClass
    from bossanova.models.lmer import lmer as LMERClass
    from bossanova.models.glmer import glmer as GLMERClass

    # Check in order of specificity (mixed models first, then base models)
    if isinstance(model, GLMERClass):
        return "glmer"
    if isinstance(model, LMERClass):
        return "lmer"
    if isinstance(model, GLMClass):
        return "glm"
    if isinstance(model, LMClass):
        return "lm"

    raise ValueError(
        f"Unknown model type: {model.__class__.__name__}. "
        "Expected one of: lm, glm, lmer, glmer"
    )


def _build_term_L_matrices(
    builder,
    X_names: list[str],
) -> dict[str, np.ndarray]:
    """Build contrast matrices (L) for each model term.

    This is a helper for bootstrap/permutation ANOVA that extracts
    the L matrix for each term without recomputing EMMs.

    The L matrix for a term is constructed by:
    1. Identifying which coefficient indices belong to that term
    2. Creating an identity-like contrast for those coefficients

    Args:
        builder: DesignMatrixBuilder with term info.
        X_names: List of coefficient names from the model.

    Returns:
        Dictionary mapping term names to L matrices.
        Each L has shape [n_coefs_in_term, n_total_coefs].
    """
    n_coefs = len(X_names)
    term_L: dict[str, np.ndarray] = {}

    # Group coefficient indices by term
    # Terms are identified by coefficient names:
    # - "intercept" -> intercept term
    # - "factor(group)[T.B]" -> term "factor(group)" or "group"
    # - "x" -> term "x"
    # - "x:y" -> interaction term

    term_indices: dict[str, list[int]] = {}

    for i, name in enumerate(X_names):
        if name.lower() == "intercept":
            continue  # Skip intercept, not tested in ANOVA

        # Extract term name
        term_name = _get_term_from_coef(name)
        if term_name:
            if term_name not in term_indices:
                term_indices[term_name] = []
            term_indices[term_name].append(i)

    # Build L matrix for each term
    for term_name, indices in term_indices.items():
        if len(indices) < 1:
            continue

        n_contrasts = len(indices)
        L = np.zeros((n_contrasts, n_coefs))
        for j, idx in enumerate(indices):
            L[j, idx] = 1.0

        term_L[term_name] = L

    return term_L


def _get_term_from_coef(coef_name: str) -> str | None:
    """Extract term name from coefficient name.

    Examples:
        "factor(group)[T.B]" -> "group"
        "x" -> "x"
        "x:y" -> "x:y"
        "factor(a)[T.1]:factor(b)[T.2]" -> "a:b"

    Args:
        coef_name: Coefficient name from model.

    Returns:
        Term name, or None if not determinable.
    """
    if not coef_name:
        return None

    # Handle interaction terms
    if ":" in coef_name:
        # Split by : and extract each part's term
        parts = coef_name.split(":")
        term_parts = []
        for part in parts:
            term = _extract_term_part(part)
            if term:
                term_parts.append(term)
        if term_parts:
            return ":".join(term_parts)
        return None

    return _extract_term_part(coef_name)


def _extract_term_part(part: str) -> str | None:
    """Extract term name from a single coefficient part.

    Examples:
        "factor(group)[T.B]" -> "group"
        "x" -> "x"
        "group_B" -> "group" (if contains underscore after factor name)

    Args:
        part: Single coefficient part.

    Returns:
        Term name.
    """
    # Handle factor(var)[T.level] pattern
    if part.startswith("factor(") and "[" in part:
        start = part.find("(") + 1
        end = part.find(")")
        return part[start:end]

    # Handle var[T.level] pattern (without factor())
    if "[" in part:
        end = part.find("[")
        return part[:end]

    # Plain variable name
    return part
