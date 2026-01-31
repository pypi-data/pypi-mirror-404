"""Model comparison utilities for nested model testing.

This module provides functions for comparing nested statistical models
using F-tests (for lm), likelihood ratio tests (for lmer/glmer), and
deviance tests (for glm).

Examples:
    >>> from bossanova import lm, compare
    >>> compact = lm("mpg ~ 1", data=mtcars).fit()
    >>> augmented = lm("mpg ~ wt", data=mtcars).fit()
    >>> compare(compact, augmented)
    ┌───────────┬──────────┬─────────┬────┬─────────┬─────────┬──────────┬───────┐
    │ model     ┆ df_resid ┆ rss     ┆ df ┆ ss      ┆ F       ┆ p_value  ┆ PRE   │
    ├───────────┼──────────┼─────────┼────┼─────────┼─────────┼──────────┼───────┤
    │ mpg ~ 1   ┆ 31       ┆ 1126.05 ┆    ┆         ┆         ┆          ┆       │
    │ mpg ~ wt  ┆ 30       ┆ 278.32  ┆ 1  ┆ 847.73  ┆ 91.375  ┆ 1.29e-10 ┆ 0.753 │
    └───────────┴──────────┴─────────┴────┴─────────┴─────────┴──────────┴───────┘

Notes:
    For single-parameter comparisons, the F-statistic equals t²:
        F = t² where t is the t-statistic for the added parameter.
    This identity is verified in the parity tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import polars as pl

from bossanova.ops.rng import RNG
from bossanova.resample.core import generate_kfold_indices, generate_loo_indices
from scipy import stats

if TYPE_CHECKING:
    from bossanova.models.lm import lm

__all__ = ["compare"]

# =============================================================================
# Validation and Sorting Helpers
# =============================================================================


def _validate_models(
    models: tuple[Any, ...], method: str = "auto", refit: bool = False
) -> tuple[Any, ...]:
    """Validate that models can be compared, auto-fitting if needed.

    Checks:
    - At least 2 models provided
    - All models are fitted (auto-fits unfitted models)
    - All models are the same type
    - All models have the same response variable
    - All models have the same number of observations
    - For LRT: All models use ML estimation (not REML), unless refit=True

    Args:
        models: Tuple of model objects (fitted or unfitted).
        method: Comparison method (used to check REML for LRT).
        refit: If True, skip REML validation (models will be refitted).

    Returns:
        Tuple of fitted model objects.

    Raises:
        ValueError: If validation fails.
    """
    if len(models) < 2:
        raise ValueError("compare() requires at least 2 models")

    # Auto-fit unfitted models (mutates in place)
    for m in models:
        if not getattr(m, "is_fitted", False):
            m.fit()

    # Check same type
    model_types = [type(m).__name__ for m in models]
    if len(set(model_types)) > 1:
        raise ValueError(
            f"All models must be the same type. Got: {', '.join(model_types)}"
        )

    # Check same response
    responses = [m.response for m in models]
    if len(set(responses)) > 1:
        raise ValueError(
            f"All models must have the same response variable. Got: {', '.join(responses)}"
        )

    # Check same n observations
    n_obs = [m.nobs for m in models]
    if len(set(n_obs)) > 1:
        raise ValueError(
            f"All models must have the same number of observations. Got: {n_obs}"
        )

    # For LRT, check that all models use ML estimation (unless refit=True)
    model_type = model_types[0]
    inferred_method = method if method != "auto" else _infer_method(models[0])

    if inferred_method == "lrt" and model_type in ("lmer", "glmer") and not refit:
        methods = [getattr(m, "method", "unknown") for m in models]
        reml_models = [m for m, meth in zip(models, methods) if meth == "REML"]
        if reml_models:
            raise ValueError(
                "LRT requires ML estimation, but some models use REML. "
                "Refit models with method='ML' for valid likelihood ratio comparison, "
                "or use compare(..., refit=True) to auto-refit. "
                f"Current methods: {methods}"
            )

    return models


def _sort_models_by_complexity(models: tuple[Any, ...]) -> list[Any]:
    """Sort models from simplest (fewest parameters) to most complex.

    This matches R's anova() behavior which orders models by df.

    Args:
        models: Tuple of fitted model objects.

    Returns:
        List of models sorted by number of parameters (ascending).
    """

    def get_total_params(m: Any) -> int:
        """Get total parameter count for sorting."""
        model_type = type(m).__name__
        if model_type == "lmer":
            # Fixed effects + theta + sigma
            return m.nparams + len(m.theta_) + 1
        elif model_type == "glmer":
            # Fixed effects + theta (no sigma)
            return m.nparams + len(m.theta_)
        else:
            # lm/glm: just fixed effects
            return m.nparams

    return sorted(models, key=get_total_params)


def _infer_method(model: Any) -> str:
    """Infer the appropriate comparison method for a model type.

    Args:
        model: A fitted model object.

    Returns:
        Comparison method: "f" for lm, "lrt" for lmer/glmer, "deviance" for glm.
    """
    model_type = type(model).__name__

    if model_type == "lm":
        return "f"
    elif model_type == "glm":
        return "deviance"
    elif model_type in ("lmer", "glmer"):
        return "lrt"
    else:
        raise ValueError(f"Unknown model type: {model_type}")


def _check_nested(
    df_diffs: list[float | int | None],
    stat_diffs: list[float | None],
    model_formulas: list[str],
    method: str,
) -> None:
    """Check that models appear to be nested and raise error if not.

    Non-nested models are detected by:
    - df <= 0: No additional parameters in augmented model
    - stat_diff < 0: Augmented model fits worse (negative SS, deviance reduction, or chi2)

    Args:
        df_diffs: List of df differences for each comparison (None for first model).
        stat_diffs: List of statistic differences (SS, dev_diff, or chi2).
        model_formulas: List of model formula strings.
        method: Comparison method ("f", "deviance", or "lrt").

    Raises:
        ValueError: If models don't appear nested.
    """
    for i, (df, stat) in enumerate(zip(df_diffs, stat_diffs)):
        if df is None:
            continue  # First model has no comparison

        # Check for non-nested indicators
        if df <= 0:
            raise ValueError(
                f"Models don't appear to be nested: df={df} for comparison "
                f"'{model_formulas[i - 1]}' vs '{model_formulas[i]}'. "
                "Nested models should have strictly increasing parameters. "
                "Use method='cv' for cross-validation comparison of non-nested models."
            )

        if stat is not None and stat < 0:
            stat_name = {"f": "SS", "deviance": "deviance reduction", "lrt": "chi2"}[
                method
            ]
            raise ValueError(
                f"Models don't appear to be nested: {stat_name}={stat:.4f} < 0 for "
                f"comparison '{model_formulas[i - 1]}' vs '{model_formulas[i]}'. "
                "The augmented model fits worse than the compact model. "
                "Use method='cv' for cross-validation comparison of non-nested models."
            )


# =============================================================================
# F-Test Implementation
# =============================================================================


def _compute_rss(model: lm) -> float:
    """Compute residual sum of squares for a model.

    Args:
        model: Fitted lm model.

    Returns:
        RSS = sum(residuals^2).
    """
    return float(np.sum(model._residuals**2))


def _compare_f_test(models: list[Any]) -> pl.DataFrame:
    """Perform sequential F-tests for nested lm models.

    Computes F-statistics comparing each model to the previous (simpler) model
    in the sequence. This matches R's anova(m1, m2, ...) behavior.

    Args:
        models: List of fitted lm models, sorted by complexity (simplest first).

    Returns:
        DataFrame with columns:
        - model: Formula string
        - df_resid: Residual degrees of freedom
        - rss: Residual sum of squares
        - df: Degrees of freedom for this comparison (df_compact - df_augmented)
        - ss: Sum of squares explained (RSS_compact - RSS_augmented)
        - F: F-statistic
        - p_value: p-value from F distribution
        - PRE: Proportional reduction in error

    Notes:
        The F-statistic is computed as:
            F = (SS / df) / (RSS_augmented / df_resid_augmented)

        For a single-parameter comparison, F = t² where t is the t-statistic
        for the added parameter in the augmented model.
    """
    n_models = len(models)

    # Initialize result lists
    formulas: list[str] = []
    df_resids: list[float] = []
    rss_values: list[float] = []
    dfs: list[float | None] = []
    ss_values: list[float | None] = []
    f_stats: list[float | None] = []
    p_values: list[float | None] = []
    pre_values: list[float | None] = []

    # First model (baseline)
    m0 = models[0]
    rss0 = _compute_rss(m0)

    formulas.append(m0.formula)
    df_resids.append(float(m0._df_resid))
    rss_values.append(rss0)
    dfs.append(None)
    ss_values.append(None)
    f_stats.append(None)
    p_values.append(None)
    pre_values.append(None)

    # Compute MSE from final (most complex) model - used for all comparisons
    # This matches R's anova() behavior for sequential model comparison
    m_final = models[-1]
    rss_final = _compute_rss(m_final)
    df_final = m_final._df_resid
    mse_final = rss_final / df_final

    # Compare each model to previous
    for i in range(1, n_models):
        m_prev = models[i - 1]
        m_curr = models[i]

        rss_prev = _compute_rss(m_prev)
        rss_curr = _compute_rss(m_curr)

        df_prev = m_prev._df_resid
        df_curr = m_curr._df_resid

        # Degrees of freedom for this comparison
        df_diff = df_prev - df_curr

        # Sum of squares explained
        ss = rss_prev - rss_curr

        # F-statistic: (SS / df) / MSE_final
        # Uses MSE from final model for all comparisons (matches R's anova())
        f_stat = (ss / df_diff) / mse_final if df_diff > 0 and mse_final > 0 else 0.0

        # p-value from F distribution (using df_final for denominator)
        p_val = 1.0 - stats.f.cdf(f_stat, df_diff, df_final)

        # PRE: Proportional Reduction in Error
        # (RSS_compact - RSS_augmented) / RSS_compact
        pre = ss / rss_prev if rss_prev > 0 else 0.0

        formulas.append(m_curr.formula)
        df_resids.append(float(df_curr))
        rss_values.append(rss_curr)
        dfs.append(float(df_diff))
        ss_values.append(float(ss))
        f_stats.append(float(f_stat))
        p_values.append(float(p_val))
        pre_values.append(float(pre))

    # Check for non-nested models
    _check_nested(dfs, ss_values, formulas, method="f")

    # Build DataFrame
    return pl.DataFrame(
        {
            "model": formulas,
            "df_resid": df_resids,
            "rss": rss_values,
            "df": dfs,
            "ss": ss_values,
            "F": f_stats,
            "p_value": p_values,
            "PRE": pre_values,
        }
    )


# =============================================================================
# Deviance Test Implementation (GLM)
# =============================================================================


def _compare_deviance(models: list[Any], test: str = "chisq") -> pl.DataFrame:
    """Perform deviance tests for nested glm models.

    Computes deviance differences comparing each model to the previous (simpler)
    model in the sequence. This matches R's anova(glm1, glm2, test="Chisq").

    Args:
        models: List of fitted glm models, sorted by complexity (simplest first).
        test: Test type: "chisq" for chi-squared test (default), "f" for F-test.

    Returns:
        DataFrame with columns:
        - model: Formula string
        - df_resid: Residual degrees of freedom
        - deviance: Residual deviance
        - df: Degrees of freedom for this comparison
        - dev_diff: Deviance difference (reduction)
        - statistic: Chi-squared or F statistic
        - p_value: p-value from chi-squared or F distribution

    Notes:
        The deviance difference follows a chi-squared distribution with df degrees
        of freedom under the null hypothesis that the compact model is adequate.

        For quasi-families (where dispersion is estimated), the F-test is more
        appropriate and accounts for overdispersion.
    """
    n_models = len(models)

    # Initialize result lists
    formulas: list[str] = []
    df_resids: list[float] = []
    deviances: list[float] = []
    dfs: list[float | None] = []
    dev_diffs: list[float | None] = []
    statistics: list[float | None] = []
    p_values: list[float | None] = []

    # First model (baseline)
    m0 = models[0]
    formulas.append(m0.formula)
    df_resids.append(float(m0._df_resid))
    deviances.append(float(m0._deviance))
    dfs.append(None)
    dev_diffs.append(None)
    statistics.append(None)
    p_values.append(None)

    # Compare each model to previous
    for i in range(1, n_models):
        m_prev = models[i - 1]
        m_curr = models[i]

        dev_prev = m_prev._deviance
        dev_curr = m_curr._deviance

        df_prev = m_prev._df_resid
        df_curr = m_curr._df_resid

        # Degrees of freedom for this comparison
        df_diff = df_prev - df_curr

        # Deviance reduction
        dev_diff = dev_prev - dev_curr

        # Compute test statistic and p-value
        if test == "chisq":
            # Chi-squared test: deviance difference ~ chi2(df_diff)
            chi2_stat = dev_diff
            p_val = 1.0 - stats.chi2.cdf(chi2_stat, df_diff) if df_diff > 0 else 1.0
            stat = chi2_stat
        else:  # test == "f"
            # F-test: accounts for estimated dispersion
            # F = (dev_diff / df_diff) / dispersion
            dispersion = m_curr._dispersion
            f_stat = (dev_diff / df_diff) / dispersion if df_diff > 0 else 0.0
            p_val = 1.0 - stats.f.cdf(f_stat, df_diff, df_curr)
            stat = f_stat

        formulas.append(m_curr.formula)
        df_resids.append(float(df_curr))
        deviances.append(float(dev_curr))
        dfs.append(float(df_diff))
        dev_diffs.append(float(dev_diff))
        statistics.append(float(stat))
        p_values.append(float(p_val))

    # Check for non-nested models
    _check_nested(dfs, dev_diffs, formulas, method="deviance")

    # Build DataFrame - column name depends on test type
    stat_col_name = "chi2" if test == "chisq" else "F"

    return pl.DataFrame(
        {
            "model": formulas,
            "df_resid": df_resids,
            "deviance": deviances,
            "df": dfs,
            "dev_diff": dev_diffs,
            stat_col_name: statistics,
            "p_value": p_values,
        }
    )


# =============================================================================
# LRT Implementation (Mixed Models)
# =============================================================================


def _get_n_params(model: Any) -> int:
    """Get total number of parameters for a mixed model.

    Args:
        model: A fitted lmer or glmer model.

    Returns:
        Total parameter count: fixed effects + variance parameters + sigma (lmer only).
    """
    n_fixed = model._p
    n_theta = len(model._theta)

    # lmer has sigma as additional parameter, glmer does not
    if type(model).__name__ == "lmer":
        return n_fixed + n_theta + 1
    else:  # glmer
        return n_fixed + n_theta


def _compare_lrt(models: list[Any]) -> pl.DataFrame:
    """Perform likelihood ratio tests for nested lmer/glmer models.

    Computes likelihood ratio chi-squared statistics comparing each model
    to the previous (simpler) model. This matches lme4's anova() behavior.

    Args:
        models: List of fitted lmer/glmer models, sorted by complexity.
            All models must use ML estimation (validated by compare()).

    Returns:
        DataFrame with columns:
        - model: Formula string
        - npar: Number of parameters
        - AIC: Akaike Information Criterion
        - BIC: Bayesian Information Criterion
        - loglik: Log-likelihood
        - deviance: Deviance (-2 * loglik)
        - chi2: Likelihood ratio chi-squared statistic
        - df: Degrees of freedom for comparison
        - p_value: p-value from chi-squared distribution

    Notes:
        The LRT statistic is: chi2 = 2 * (loglik_aug - loglik_compact)
        which follows a chi-squared distribution with df = npar_aug - npar_compact
        under the null hypothesis that the simpler model is adequate.

        ML estimation is required for valid LRT - REML models are rejected
        by compare() before reaching this function.
    """
    n_models = len(models)

    # Initialize result lists
    formulas: list[str] = []
    npars: list[int] = []
    aics: list[float] = []
    bics: list[float] = []
    logliks: list[float] = []
    deviances: list[float] = []
    chi2s: list[float | None] = []
    dfs: list[int | None] = []
    p_values: list[float | None] = []

    # First model (baseline)
    m0 = models[0]
    npar0 = _get_n_params(m0)

    formulas.append(m0.formula)
    npars.append(npar0)
    aics.append(float(m0.aic))
    bics.append(float(m0.bic))
    logliks.append(float(m0.loglik))
    # Use -2*loglik for deviance (matches R's -2*log(L) column)
    deviances.append(float(-2 * m0.loglik))
    chi2s.append(None)
    dfs.append(None)
    p_values.append(None)

    # Compare each model to previous
    for i in range(1, n_models):
        m_prev = models[i - 1]
        m_curr = models[i]

        npar_prev = _get_n_params(m_prev)
        npar_curr = _get_n_params(m_curr)

        loglik_prev = m_prev.loglik
        loglik_curr = m_curr.loglik

        # Degrees of freedom for this comparison
        df = npar_curr - npar_prev

        # Likelihood ratio statistic: chi2 = 2 * (loglik_aug - loglik_compact)
        chi2 = 2 * (loglik_curr - loglik_prev)

        # p-value from chi-squared distribution
        p_val = 1.0 - stats.chi2.cdf(chi2, df) if df > 0 else 1.0

        formulas.append(m_curr.formula)
        npars.append(npar_curr)
        aics.append(float(m_curr.aic))
        bics.append(float(m_curr.bic))
        logliks.append(float(m_curr.loglik))
        # Use -2*loglik for deviance (matches R's -2*log(L) column)
        deviances.append(float(-2 * m_curr.loglik))
        chi2s.append(float(chi2))
        dfs.append(int(df))
        p_values.append(float(p_val))

    # Check for non-nested models
    _check_nested(dfs, chi2s, formulas, method="lrt")

    # Build DataFrame
    return pl.DataFrame(
        {
            "model": formulas,
            "npar": npars,
            "AIC": aics,
            "BIC": bics,
            "loglik": logliks,
            "deviance": deviances,
            "chi2": chi2s,
            "df": dfs,
            "p_value": p_values,
        }
    )


# =============================================================================
# Refit Helper for REML -> ML
# =============================================================================


def _refit_with_ml(model: Any) -> Any:
    """Refit a mixed model with ML estimation if it uses REML.

    Creates a new model instance and fits with method="ML". The original
    model is not mutated.

    Args:
        model: A fitted lmer or glmer model.

    Returns:
        If model uses REML: a new model fitted with ML.
        If model uses ML: the original model unchanged.
    """
    # Already ML - return unchanged
    if getattr(model, "_method", None) == "ML":
        return model

    # Get model type and refit with ML
    model_type = type(model).__name__

    if model_type == "lmer":
        from bossanova.models.lmer import lmer

        new_model = lmer(model._formula, data=model._data)
        new_model.fit(method="ML")
        return new_model

    elif model_type == "glmer":
        from bossanova.models.glmer import glmer

        new_model = glmer(
            model._formula,
            data=model._data,
            family=model._family_name,
            link=model._link_name,
        )
        new_model.fit(method="ML")
        return new_model

    else:
        # Not a mixed model - return unchanged
        return model


# =============================================================================
# CV Comparison Implementation
# =============================================================================


def _cv_fold_score(
    model: Any,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    metric: str,
) -> float:
    """Compute CV score for a single fold.

    Refits the model on training data and evaluates on test data.

    Args:
        model: A fitted model (lm or glm) to clone and refit.
        train_idx: Training set indices.
        test_idx: Test set indices.
        metric: Error metric ("mse", "rmse", "mae").

    Returns:
        Test set error for this fold.
    """
    model_type = type(model).__name__

    # Get original data
    data = model._data
    formula = model.formula

    # Subset data for training and testing
    train_data = data[train_idx.tolist()]
    test_data = data[test_idx.tolist()]

    # Import model class and refit on training data
    if model_type == "lm":
        from bossanova.models.lm import lm

        new_model = lm(formula, data=train_data).fit()
    elif model_type == "glm":
        from bossanova.models.glm import glm

        new_model = glm(
            formula, data=train_data, family=model.family, link=model.link
        ).fit()
    else:
        raise ValueError(f"CV comparison not supported for model type: {model_type}")

    # Predict on test data
    y_pred = new_model.predict(data=test_data)["fitted"].to_numpy()

    # Get actual test values
    y_true = test_data[model._y_name].to_numpy()

    # Compute error metric
    errors = y_true - y_pred

    if metric == "mse":
        return float(np.mean(errors**2))
    elif metric == "rmse":
        return float(np.sqrt(np.mean(errors**2)))
    elif metric == "mae":
        return float(np.mean(np.abs(errors)))
    else:
        raise ValueError(f"Unknown metric: {metric}. Use 'mse', 'rmse', or 'mae'.")


def _compare_cv(
    models: list[Any],
    cv: int | str = 5,
    seed: int | None = None,
    metric: str = "mse",
) -> pl.DataFrame:
    """Compare models using cross-validation with Nadeau-Bengio corrected t-test.

    Uses the corrected variance estimator from Nadeau & Bengio (2003) to account
    for the non-independence of CV folds (overlapping training sets).

    Args:
        models: List of fitted models (lm or glm) to compare.
        cv: Number of folds, or "loo" for leave-one-out.
        seed: Random seed for reproducible fold splits.
        metric: Error metric ("mse", "rmse", "mae").

    Returns:
        DataFrame with columns:
        - model: Formula string
        - cv_score: Mean CV score (error)
        - cv_se: Standard error of CV score
        - diff: Difference from reference model (first model)
        - diff_se: Corrected standard error of difference
        - t_stat: Nadeau-Bengio corrected t-statistic
        - p_value: Two-sided p-value
        - PRE: Proportional reduction in error

    Notes:
        The Nadeau-Bengio correction accounts for the fact that k-fold CV
        training sets overlap by approximately (k-2)/(k-1) fraction.

        Corrected variance: var_corrected = var(diff) * (1/k + n_test/n_train)
        t-statistic: t = mean(diff) / sqrt(var_corrected)
        p-value: 2 * (1 - t.cdf(|t|, df=k-1))

    References:
        Nadeau & Bengio (2003) "Inference for the Generalization Error"
    """
    n_models = len(models)
    n = models[0]._n

    # Generate shared fold splits for fair comparison
    rng = RNG.from_seed(seed)
    if cv == "loo":
        k = n  # LOO has n folds
        splits = generate_loo_indices(n)
    else:
        k = int(cv)
        splits = generate_kfold_indices(rng, n, k, shuffle=True)
    n_train = len(splits[0][0])
    n_test = len(splits[0][1])

    # Collect per-fold scores for each model
    fold_scores: dict[int, list[float]] = {i: [] for i in range(n_models)}

    for train_idx, test_idx in splits:
        for i, model in enumerate(models):
            score = _cv_fold_score(model, train_idx, test_idx, metric)
            fold_scores[i].append(score)

    # Convert to arrays
    scores_array = {i: np.array(fold_scores[i]) for i in range(n_models)}

    # Initialize result lists
    formulas: list[str] = []
    cv_scores: list[float] = []
    cv_ses: list[float] = []
    diffs: list[float | None] = []
    diff_ses: list[float | None] = []
    t_stats: list[float | None] = []
    p_values: list[float | None] = []
    pres: list[float | None] = []

    # Reference model (first)
    ref_scores = scores_array[0]
    ref_mean = np.mean(ref_scores)
    ref_se = np.std(ref_scores, ddof=1) / np.sqrt(k)

    formulas.append(models[0].formula)
    cv_scores.append(float(ref_mean))
    cv_ses.append(float(ref_se))
    diffs.append(None)
    diff_ses.append(None)
    t_stats.append(None)
    p_values.append(None)
    pres.append(None)

    # Compare each model to reference
    for i in range(1, n_models):
        model_scores = scores_array[i]
        model_mean = np.mean(model_scores)
        model_se = np.std(model_scores, ddof=1) / np.sqrt(k)

        # Difference from reference (positive = reference is better)
        diff_vals = ref_scores - model_scores
        mean_diff = np.mean(diff_vals)
        var_diff = np.var(diff_vals, ddof=1)

        # Nadeau-Bengio correction
        # var_corrected = var(diff) * (1/k + n_test/n_train)
        var_corrected = var_diff * (1 / k + n_test / n_train)
        se_corrected = np.sqrt(var_corrected)

        # t-statistic and p-value
        if se_corrected > 0:
            t_stat = mean_diff / se_corrected
            p_val = 2 * (1 - stats.t.cdf(np.abs(t_stat), df=k - 1))
        else:
            t_stat = 0.0
            p_val = 1.0

        # PRE: Proportional reduction in error
        # (error_ref - error_model) / error_ref
        # Positive PRE means model is better (lower error)
        pre = (ref_mean - model_mean) / ref_mean if ref_mean != 0 else 0.0

        formulas.append(models[i].formula)
        cv_scores.append(float(model_mean))
        cv_ses.append(float(model_se))
        diffs.append(float(mean_diff))
        diff_ses.append(float(se_corrected))
        t_stats.append(float(t_stat))
        p_values.append(float(p_val))
        pres.append(float(pre))

    # Build DataFrame
    return pl.DataFrame(
        {
            "model": formulas,
            "cv_score": cv_scores,
            "cv_se": cv_ses,
            "diff": diffs,
            "diff_se": diff_ses,
            "t_stat": t_stats,
            "p_value": p_values,
            "PRE": pres,
        }
    )


# =============================================================================
# Main Entry Point
# =============================================================================


def compare(
    *models: Any,
    method: str = "auto",
    sort: bool = True,
    test: str = "chisq",
    refit: bool = False,
    cv: int | str = 5,
    seed: int | None = None,
    metric: str = "mse",
) -> pl.DataFrame:
    """Compare nested statistical models.

    Performs sequential hypothesis tests comparing nested models.
    The appropriate test method is inferred from model type:

    - lm: F-test (equivalent to R's anova())
    - glm: Deviance test (chi-squared)
    - lmer/glmer: Likelihood ratio test
    - cv: Cross-validation with Nadeau-Bengio corrected t-test

    Args:
        *models: Two or more fitted model objects.
        method: Comparison method. Options:
            - "auto": Infer from model type (default)
            - "f": F-test (for lm)
            - "lrt": Likelihood ratio test (for mixed models)
            - "deviance": Deviance test (for glm)
            - "cv": Cross-validation comparison (for lm/glm)
        sort: If True, sort models by complexity before comparing.
            This ensures proper nesting order.
        refit: If True and models are lmer/glmer with REML estimation,
            automatically refit with ML for valid LRT comparison.
            Original models are not mutated. Default False.
        test: For GLM deviance comparisons only. Options:
            - "chisq": Chi-squared test (default)
            - "f": F-test (for quasi-families with estimated dispersion)
        cv: For CV comparison only. Number of folds or "loo" for leave-one-out.
        seed: For CV comparison only. Random seed for reproducible splits.
        metric: For CV comparison only. Error metric ("mse", "rmse", "mae").

    Returns:
        DataFrame with comparison results. Columns depend on method:

        For F-test (lm):
            - model: Formula string
            - df_resid: Residual degrees of freedom
            - rss: Residual sum of squares
            - df: Degrees of freedom for comparison
            - ss: Sum of squares explained
            - F: F-statistic
            - p_value: p-value
            - PRE: Proportional reduction in error

        For deviance test (glm):
            - model: Formula string
            - df_resid: Residual degrees of freedom
            - deviance: Residual deviance
            - df: Degrees of freedom for comparison
            - dev_diff: Deviance reduction
            - chi2 (or F): Test statistic
            - p_value: p-value

        For LRT (lmer/glmer):
            - model: Formula string
            - npar: Number of parameters
            - AIC: Akaike Information Criterion
            - BIC: Bayesian Information Criterion
            - loglik: Log-likelihood
            - deviance: Deviance (-2 * loglik)
            - chi2: Likelihood ratio chi-squared statistic
            - df: Degrees of freedom for comparison
            - p_value: p-value

        For CV comparison:
            - model: Formula string
            - cv_score: Mean CV error
            - cv_se: Standard error of CV error
            - diff: Difference from reference (first model)
            - diff_se: Nadeau-Bengio corrected standard error
            - t_stat: Corrected t-statistic
            - p_value: Two-sided p-value
            - PRE: Proportional reduction in error

    Raises:
        ValueError: If models are not valid for comparison.

    Examples:
        >>> # Models are auto-fitted if needed (calls .fit() with defaults)
        >>> compare(lm("mpg ~ 1", data=mtcars), lm("mpg ~ wt", data=mtcars))

        >>> # Equivalent to explicit .fit() calls:
        >>> compare(lm("mpg ~ 1", data=mtcars).fit(), lm("mpg ~ wt", data=mtcars).fit())

        >>> # Model objects are fitted in-place, so they're usable after compare()
        >>> compact = lm("mpg ~ 1", data=mtcars)
        >>> full = lm("mpg ~ wt", data=mtcars)
        >>> compare(compact, full)
        >>> full.coef_  # Works - model was auto-fitted

        >>> # glm example (deviance test)
        >>> compare(
        ...     glm("am ~ 1", data=mtcars, family="binomial"),
        ...     glm("am ~ wt", data=mtcars, family="binomial"),
        ... )

        >>> # lmer example (likelihood ratio test)
        >>> compare(
        ...     lmer("Reaction ~ Days + (1|Subject)", data=sleepstudy),
        ...     lmer("Reaction ~ Days + (Days|Subject)", data=sleepstudy),
        ... )

        >>> # CV example (Nadeau-Bengio corrected)
        >>> compare(
        ...     lm("mpg ~ 1", data=mtcars),
        ...     lm("mpg ~ wt", data=mtcars),
        ...     method="cv", cv=5, seed=42,
        ... )

    Notes:
        For single-parameter comparisons in lm models:
            F = t²
        where t is the t-statistic for the added parameter.
        This identity is fundamental and verified in parity tests.

        For GLM, the deviance difference follows a chi-squared distribution:
            chi2 = deviance_compact - deviance_augmented
        with df = df_compact - df_augmented degrees of freedom.

        For mixed models (lmer/glmer), the LRT statistic is:
            chi2 = 2 * (loglik_augmented - loglik_compact)
        with df = npar_augmented - npar_compact degrees of freedom.
        Models should use the same REML setting for valid comparison.

        For CV comparison, the Nadeau-Bengio correction accounts for
        overlapping training sets in k-fold CV:
            var_corrected = var(diff) * (1/k + n_test/n_train)
        This prevents the underestimation of variance that occurs with
        naive paired t-tests on CV folds.

    See Also:
        - lrt: Likelihood ratio test for mixed models
        - anova: Type I/II/III ANOVA tables
    """
    # Validate and auto-fit models (pass method and refit for REML check)
    models = _validate_models(models, method=method, refit=refit)

    # Sort if requested (not applicable for CV)
    if sort and method != "cv":
        model_list = _sort_models_by_complexity(models)
    else:
        model_list = list(models)

    # Infer method if auto
    if method == "auto":
        method = _infer_method(model_list[0])

    # For LRT with refit=True, refit REML models with ML
    if method == "lrt" and refit:
        model_list = [_refit_with_ml(m) for m in model_list]

    # Dispatch to appropriate comparison function
    if method == "f":
        return _compare_f_test(model_list)
    elif method == "lrt":
        return _compare_lrt(model_list)
    elif method == "deviance":
        return _compare_deviance(model_list, test=test)
    elif method == "cv":
        return _compare_cv(model_list, cv=cv, seed=seed, metric=metric)
    else:
        raise ValueError(
            f"Unknown method: {method}. Use 'auto', 'f', 'lrt', 'deviance', or 'cv'."
        )
