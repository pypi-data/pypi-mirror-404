"""Builder functions for constructing result DataFrames from schemas.

These functions take validated schema objects and produce polars DataFrames
with consistent column ordering and types.

Examples:
    >>> from bossanova.results import LMResultFit, build_result_params
    >>> schema = LMResultFit(
    ...     term=["Intercept", "x"],
    ...     estimate=[1.0, 2.0],
    ...     se=[0.1, 0.2],
    ...     statistic=[10.0, 10.0],
    ...     df=[28.0, 28.0],
    ...     p_value=[0.001, 0.001],
    ...     ci_lower=[0.8, 1.6],
    ...     ci_upper=[1.2, 2.4],
    ... )
    >>> df = build_result_params(schema)
"""

from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    import numpy as np

from bossanova.results.schemas import (
    BaseResultFit,
    BaseResultFitDiagnostics,
    BootResultFit,
    GLMerOptimizerDiagnostics,
    GLMerResultFit,
    GLMerResultFitDiagnostics,
    GLMOptimizerDiagnostics,
    GLMResultFit,
    GLMResultFitDiagnostics,
    LMerOptimizerDiagnostics,
    LMerResultFit,
    LMerResultFitDiagnostics,
    LMResultFit,
    LMResultFitDiagnostics,
    MeeAsympResult,
    MeeBootResult,
    MeeContrastResult,
    MeeResult,
    PermResultFit,
    RidgeResultFit,
    RidgeResultFitDiagnostics,
)

__all__ = [
    "build_result_params",
    "build_boot_result_params",
    "build_perm_result_params",
    "build_result_model",
    "build_glm_result_params",
    "build_glm_result_model",
    "build_glm_optimizer_diagnostics",
    "build_lmer_optimizer_diagnostics",
    "build_glmer_optimizer_diagnostics",
    "build_lmer_result_params",
    "build_lmer_result_model",
    "build_ranef_dataframe",
    "build_varying_var_df",
    "build_varying_corr_df",
    "theta_to_variance_components",
    "build_glmer_result_params",
    "build_glmer_result_model",
    "build_ridge_result_params",
    "build_ridge_result_model",
    # MEE builders
    "build_mee_result",
    "build_mee_asymp_result",
    "build_mee_boot_result",
    "build_mee_contrast_result",
]

# =============================================================================
# Column ordering constants
# =============================================================================

# Standard column order for result_params
_RESULT_FIT_COLUMNS_BASE = [
    "term",
    "estimate",
    "se",
    "ci_lower",
    "ci_upper",
    "statistic",
    "p_value",
]

# lm/lmer adds df after statistic
_RESULT_FIT_COLUMNS_LM = [
    "term",
    "estimate",
    "se",
    "ci_lower",
    "ci_upper",
    "statistic",
    "df",
    "p_value",
]

# Bootstrap result_params columns (no statistic/df/p_value, but includes n_resamples)
_RESULT_FIT_COLUMNS_BOOT = [
    "term",
    "estimate",
    "se",
    "ci_lower",
    "ci_upper",
    "n_resamples",
]

# Permutation result_params columns (statistic but no df, includes n_resamples)
_RESULT_FIT_COLUMNS_PERM = [
    "term",
    "estimate",
    "se",
    "ci_lower",
    "ci_upper",
    "statistic",
    "n_resamples",
    "p_value",
]

# Standard row order for result_model (base)
_RESULT_FIT_DIAGNOSTICS_ROWS_BASE = [
    "nobs",
    "df_model",
    "df_resid",
    "aic",
    "bic",
    "loglik",
]

# lm adds these rows
_RESULT_FIT_DIAGNOSTICS_ROWS_LM = [
    "nobs",
    "df_model",
    "df_resid",
    "rsquared",
    "rsquared_adj",
    "fstatistic",
    "fstatistic_pvalue",
    "sigma",
    "aic",
    "bic",
    "loglik",
]

# glm adds these rows
_RESULT_FIT_DIAGNOSTICS_ROWS_GLM = [
    "nobs",
    "df_model",
    "df_resid",
    "null_deviance",
    "deviance",
    "dispersion",
    "pseudo_rsquared",
    "aic",
    "bic",
    "loglik",
]

# lmer adds these rows
# Note: "method" is not included as it's a string, not a numeric statistic
_RESULT_FIT_DIAGNOSTICS_ROWS_LMER = [
    "nobs",
    "df_model",
    "df_resid",
    "sigma",
    "deviance",
    "aic",
    "bic",
    "loglik",
    "rsquared_marginal",
    "rsquared_conditional",
    "icc",
]

# glmer rows
# Note: "family" and "link" are not included as they are strings
_RESULT_FIT_DIAGNOSTICS_ROWS_GLMER = [
    "nobs",
    "df_model",
    "df_resid",
    "deviance",
    "objective",
    "aic",
    "bic",
    "loglik",
]


# =============================================================================
# Result Fit Builders
# =============================================================================


def build_result_params(
    schema: BaseResultFit | LMResultFit | GLMResultFit | LMerResultFit | GLMerResultFit,
) -> pl.DataFrame:
    """Build result_params DataFrame from schema.

    Args:
        schema: Validated schema containing coefficient table data.

    Returns:
        Coefficient table with standardized column order.

    Examples:
        >>> schema = LMResultFit(
        ...     term=["Intercept", "x"],
        ...     estimate=[1.0, 2.0],
        ...     se=[0.1, 0.2],
        ...     ci_lower=[0.8, 1.6],
        ...     ci_upper=[1.2, 2.4],
        ...     statistic=[10.0, 10.0],
        ...     df=[28.0, 28.0],
        ...     p_value=[0.001, 0.001],
        ... )
        >>> df = build_result_params(schema)
        >>> df.columns
        ['term', 'estimate', 'se', 'ci_lower', 'ci_upper', 'statistic', 'df', 'p_value']
    """
    # Build base columns
    data = {
        "term": list(schema.term),
        "estimate": list(schema.estimate),
        "se": list(schema.se),
        "statistic": list(schema.statistic),
        "p_value": list(schema.p_value),
        "ci_lower": list(schema.ci_lower),
        "ci_upper": list(schema.ci_upper),
    }

    # Add df column for lm/glm/lmer/glmer
    if (
        isinstance(schema, (LMResultFit, GLMResultFit, LMerResultFit, GLMerResultFit))
        and len(schema.df) > 0
    ):
        data["df"] = list(schema.df)
        columns = _RESULT_FIT_COLUMNS_LM
    else:
        columns = _RESULT_FIT_COLUMNS_BASE

    # Create DataFrame with correct column order
    df = pl.DataFrame(data)

    # Reorder columns (filter to only those present)
    present_columns = [c for c in columns if c in df.columns]
    return df.select(present_columns)


def build_boot_result_params(schema: BootResultFit) -> pl.DataFrame:
    """Build result_params DataFrame from bootstrap schema.

    Args:
        schema: Validated bootstrap schema.

    Returns:
        Coefficient table with bootstrap SE and CIs.

    Examples:
        >>> schema = BootResultFit(
        ...     term=["Intercept", "x"],
        ...     estimate=[1.0, 2.0],
        ...     se=[0.1, 0.2],
        ...     ci_lower=[0.8, 1.6],
        ...     ci_upper=[1.2, 2.4],
        ...     n=100,
        ...     ci_type="bca",
        ...     n_boot=999,
        ... )
        >>> df = build_boot_result_params(schema)
        >>> df.columns
        ['term', 'estimate', 'se', 'ci_lower', 'ci_upper', 'n_resamples']
    """
    n_terms = len(schema.term)
    data = {
        "term": list(schema.term),
        "estimate": list(schema.estimate),
        "se": list(schema.se),
        "ci_lower": list(schema.ci_lower),
        "ci_upper": list(schema.ci_upper),
        "n_resamples": [schema.n_boot] * n_terms,
    }

    df = pl.DataFrame(data)
    return df.select(_RESULT_FIT_COLUMNS_BOOT)


def build_perm_result_params(schema: PermResultFit) -> pl.DataFrame:
    """Build result_params DataFrame from permutation schema.

    Args:
        schema: Validated permutation schema.

    Returns:
        Coefficient table with permutation p-values.

    Examples:
        >>> schema = PermResultFit(
        ...     term=["Intercept", "x"],
        ...     estimate=[1.0, 2.0],
        ...     se=[0.1, 0.2],
        ...     statistic=[10.0, 10.0],
        ...     n=100,
        ...     p_value=[0.001, 0.001],
        ...     ci_lower=[0.8, 1.6],
        ...     ci_upper=[1.2, 2.4],
        ...     n_perm=999,
        ... )
        >>> df = build_perm_result_params(schema)
        >>> df.columns
        ['term', 'estimate', 'se', 'ci_lower', 'ci_upper', 'statistic', 'n_resamples', 'p_value']
    """
    n_terms = len(schema.term)
    data = {
        "term": list(schema.term),
        "estimate": list(schema.estimate),
        "se": list(schema.se),
        "statistic": list(schema.statistic),
        "n_resamples": [schema.n_perm] * n_terms,
        "p_value": list(schema.p_value),
        "ci_lower": list(schema.ci_lower),
        "ci_upper": list(schema.ci_upper),
    }

    df = pl.DataFrame(data)
    return df.select(_RESULT_FIT_COLUMNS_PERM)


# =============================================================================
# Result Fit Diagnostics Builders
# =============================================================================


def build_result_model(
    schema: BaseResultFitDiagnostics
    | LMResultFitDiagnostics
    | GLMResultFitDiagnostics
    | LMerResultFitDiagnostics
    | GLMerResultFitDiagnostics,
) -> pl.DataFrame:
    """Build result_model DataFrame from schema.

    Returns a single-row wide DataFrame with one column per metric.

    Args:
        schema: Validated schema containing fit statistics.

    Returns:
        Single-row DataFrame with metrics as columns.

    Examples:
        >>> schema = LMResultFitDiagnostics(
        ...     nobs=32, df_model=2, df_resid=29, rsquared=0.83,
        ...     rsquared_adj=0.81, fstatistic=69.2, fstatistic_pvalue=1e-11,
        ...     sigma=2.59, aic=156.4, bic=162.3, loglik=-74.2,
        ... )
        >>> df = build_result_model(schema)
        >>> df.columns
        ['nobs', 'df_model', 'df_resid', 'rsquared', 'rsquared_adj', ...]
        >>> df["rsquared"].item()
        0.83
    """
    # Determine column order based on schema type
    if isinstance(schema, LMResultFitDiagnostics):
        col_order = _RESULT_FIT_DIAGNOSTICS_ROWS_LM
    elif isinstance(schema, GLMResultFitDiagnostics):
        col_order = _RESULT_FIT_DIAGNOSTICS_ROWS_GLM
    elif isinstance(schema, LMerResultFitDiagnostics):
        col_order = _RESULT_FIT_DIAGNOSTICS_ROWS_LMER
    elif isinstance(schema, GLMerResultFitDiagnostics):
        col_order = _RESULT_FIT_DIAGNOSTICS_ROWS_GLMER
    else:
        col_order = _RESULT_FIT_DIAGNOSTICS_ROWS_BASE

    # Build single-row dict with each metric as a column
    data = {}
    for stat_name in col_order:
        if hasattr(schema, stat_name):
            data[stat_name] = [float(getattr(schema, stat_name))]

    return pl.DataFrame(data)


# =============================================================================
# GLM Result Builders
# =============================================================================
#
# Note: These model-specific wrappers (build_glm_*, build_lmer_*, build_glmer_*)
# delegate to the generic build_result_* functions. They exist for:
# 1. Type narrowing - accept only the specific schema type for static checking
# 2. Model-specific docstrings with appropriate examples
# 3. Discoverability - easier to find the right function for each model
# The one-line delegation is intentional, not redundancy.
# =============================================================================


def build_glm_result_params(schema: GLMResultFit) -> pl.DataFrame:
    """Build glm result_params DataFrame from schema.

    Args:
        schema: Validated GLM schema containing coefficient table data.

    Returns:
        Coefficient table with z-statistics and df=inf.

    Examples:
        >>> schema = GLMResultFit(
        ...     term=["Intercept", "x"],
        ...     estimate=[1.0, 2.0],
        ...     se=[0.1, 0.2],
        ...     statistic=[10.0, 10.0],
        ...     df=[float('inf'), float('inf')],
        ...     p_value=[0.001, 0.001],
        ...     ci_lower=[0.8, 1.6],
        ...     ci_upper=[1.2, 2.4],
        ... )
        >>> df = build_glm_result_params(schema)
        >>> df.columns
        ['term', 'estimate', 'se', 'ci_lower', 'ci_upper', 'statistic', 'df', 'p_value']
    """
    return build_result_params(schema)


def build_glm_result_model(schema: GLMResultFitDiagnostics) -> pl.DataFrame:
    """Build glm result_model DataFrame from schema.

    Args:
        schema: Validated GLM schema containing fit statistics.

    Returns:
        Single-row DataFrame with deviance-based diagnostics as columns.

    Examples:
        >>> schema = GLMResultFitDiagnostics(
        ...     nobs=100, df_model=2, df_resid=97,
        ...     null_deviance=138.63, deviance=98.21,
        ...     dispersion=1.0, pseudo_rsquared=0.291,
        ...     aic=104.21, bic=112.05, loglik=-49.10,
        ... )
        >>> df = build_glm_result_model(schema)
        >>> df.columns
        ['nobs', 'df_model', 'df_resid', 'null_deviance', ...]
    """
    return build_result_model(schema)


def build_glm_optimizer_diagnostics(schema: GLMOptimizerDiagnostics) -> pl.DataFrame:
    """Build GLM optimizer_diagnostics DataFrame (wide format, single row).

    Args:
        schema: Validated GLM optimizer diagnostics schema.

    Returns:
        Single-row DataFrame with columns for each diagnostic metric.

    Examples:
        >>> schema = GLMOptimizerDiagnostics(
        ...     optimizer="irls",
        ...     converged=True,
        ...     n_iter=5,
        ...     tol=1e-8,
        ...     final_objective=98.21,
        ...     has_separation=False,
        ... )
        >>> df = build_glm_optimizer_diagnostics(schema)
        >>> df["converged"][0]
        True
    """
    data: dict = {
        "optimizer": [schema.optimizer],
        "converged": [schema.converged],
        "n_iter": [schema.n_iter],
        "tol": [schema.tol],
        "final_objective": [schema.final_objective],
    }

    # Add optional fields if present
    if schema.n_func_evals is not None:
        data["n_func_evals"] = [schema.n_func_evals]
    if schema.has_separation is not None:
        data["has_separation"] = [schema.has_separation]

    return pl.DataFrame(data)


def build_lmer_optimizer_diagnostics(schema: LMerOptimizerDiagnostics) -> pl.DataFrame:
    """Build lmer optimizer_diagnostics DataFrame (wide format, multi-row).

    Creates one row per theta parameter, with scalar convergence info
    repeated across rows.

    Args:
        schema: Validated lmer optimizer diagnostics schema.

    Returns:
        DataFrame with one row per theta parameter.

    Examples:
        >>> schema = LMerOptimizerDiagnostics(
        ...     optimizer="bobyqa",
        ...     converged=True,
        ...     n_iter=12,
        ...     final_objective=1743.6,
        ...     message="Optimization converged",
        ...     theta_index=[0, 1],
        ...     theta_initial=[1.0, 0.5],
        ...     theta_final=[0.97, 0.48],
        ...     boundary_adjusted=False,
        ...     restarted=False,
        ...     singular=False,
        ... )
        >>> df = build_lmer_optimizer_diagnostics(schema)
        >>> len(df)
        2
        >>> df["theta_final"].to_list()
        [0.97, 0.48]
    """
    n_rows = len(schema.theta_index)

    return pl.DataFrame(
        {
            "optimizer": [schema.optimizer] * n_rows,
            "converged": [schema.converged] * n_rows,
            "n_iter": [schema.n_iter] * n_rows,
            "final_objective": [schema.final_objective] * n_rows,
            "message": [schema.message] * n_rows,
            "theta_index": list(schema.theta_index),
            "theta_initial": list(schema.theta_initial),
            "theta_final": list(schema.theta_final),
            "boundary_adjusted": [schema.boundary_adjusted] * n_rows,
            "restarted": [schema.restarted] * n_rows,
            "singular": [schema.singular] * n_rows,
        }
    )


def build_glmer_optimizer_diagnostics(
    schema: GLMerOptimizerDiagnostics,
) -> pl.DataFrame:
    """Build glmer optimizer_diagnostics DataFrame (wide format, multi-row).

    Creates one row per theta parameter, with scalar convergence info
    repeated across rows.

    Args:
        schema: Validated glmer optimizer diagnostics schema.

    Returns:
        DataFrame with one row per theta parameter.

    Examples:
        >>> schema = GLMerOptimizerDiagnostics(
        ...     optimizer="bobyqa",
        ...     converged=True,
        ...     n_iter=8,
        ...     n_func_evals=45,
        ...     final_objective=184.05,
        ...     pirls_converged=True,
        ...     pirls_n_iter=3,
        ...     theta_index=[0],
        ...     theta_final=[0.85],
        ...     boundary_adjusted=False,
        ...     restarted=False,
        ...     singular=False,
        ... )
        >>> df = build_glmer_optimizer_diagnostics(schema)
        >>> df["pirls_converged"][0]
        True
    """
    n_rows = len(schema.theta_index)

    return pl.DataFrame(
        {
            "optimizer": [schema.optimizer] * n_rows,
            "converged": [schema.converged] * n_rows,
            "n_iter": [schema.n_iter] * n_rows,
            "n_func_evals": [schema.n_func_evals] * n_rows,
            "final_objective": [schema.final_objective] * n_rows,
            "pirls_converged": [schema.pirls_converged] * n_rows,
            "pirls_n_iter": [schema.pirls_n_iter] * n_rows,
            "theta_index": list(schema.theta_index),
            "theta_final": list(schema.theta_final),
            "boundary_adjusted": [schema.boundary_adjusted] * n_rows,
            "restarted": [schema.restarted] * n_rows,
            "singular": [schema.singular] * n_rows,
        }
    )


# =============================================================================
# LMER Result Builders
# =============================================================================


def build_lmer_result_params(schema: LMerResultFit) -> pl.DataFrame:
    """Build lmer result_params DataFrame from schema.

    Args:
        schema: Validated LMer schema containing coefficient table data.

    Returns:
        Coefficient table with t-statistics and Satterthwaite df.

    Examples:
        >>> schema = LMerResultFit(
        ...     term=["(Intercept)", "Days"],
        ...     estimate=[251.405, 10.467],
        ...     se=[6.825, 1.546],
        ...     statistic=[36.84, 6.77],
        ...     df=[17.0, 17.0],
        ...     p_value=[0.0, 3.3e-06],
        ...     ci_lower=[237.0, 7.21],
        ...     ci_upper=[265.8, 13.72],
        ... )
        >>> df = build_lmer_result_params(schema)
        >>> df.columns
        ['term', 'estimate', 'se', 'ci_lower', 'ci_upper', 'statistic', 'df', 'p_value']
    """
    return build_result_params(schema)


def build_lmer_result_model(schema: LMerResultFitDiagnostics) -> pl.DataFrame:
    """Build lmer result_model DataFrame from schema.

    Args:
        schema: Validated LMer schema containing fit statistics.

    Returns:
        Single-row DataFrame with REML/ML-specific diagnostics as columns.

    Examples:
        >>> schema = LMerResultFitDiagnostics(
        ...     nobs=180, df_model=2, df_resid=178,
        ...     sigma=25.59, deviance=1743.6, method="REML",
        ...     aic=1763.9, bic=1783.1, loglik=-875.97,
        ... )
        >>> df = build_lmer_result_model(schema)
        >>> df.columns
        ['nobs', 'df_model', 'df_resid', 'sigma', ...]
    """
    return build_result_model(schema)


def build_ranef_dataframe(
    ranef_dict: "dict[str, np.ndarray]",
    group_levels: dict[str, list[str]],
    random_names: list[str] | dict[str, list[str]],
) -> pl.DataFrame:
    """Build random effects DataFrame.

    Args:
        ranef_dict: Dict mapping group names to (n_levels, n_re) arrays.
        group_levels: Dict mapping group names to level labels.
        random_names: Names of random effects (e.g., ["Intercept", "Days"])
            or dict mapping group to RE names for multi-group models.

    Returns:
        Polars DataFrame with columns [group, level, Intercept, Days, ...].

    Examples:
        >>> import numpy as np
        >>> ranef_dict = {"Subject": np.array([[2.26, 9.20], [-40.40, -8.62]])}
        >>> group_levels = {"Subject": ["308", "309"]}
        >>> random_names = ["Intercept", "Days"]
        >>> df = build_ranef_dataframe(ranef_dict, group_levels, random_names)
        >>> df.shape
        (2, 4)
        >>> df.columns
        ['group', 'level', 'Intercept', 'Days']
    """

    rows = []

    for group_name, ranef_values in ranef_dict.items():
        # Handle multi-group case where random_names is a dict
        if isinstance(random_names, dict):
            re_names = random_names[group_name]
        else:
            re_names = random_names

        levels = group_levels[group_name]

        # ranef_values is shape (n_levels, n_re)
        for i, level_name in enumerate(levels):
            row = {"group": group_name, "level": level_name}
            for j, re_name in enumerate(re_names):
                row[re_name] = float(ranef_values[i, j])
            rows.append(row)

    return pl.DataFrame(rows)


def build_varying_var_df(
    theta: "np.ndarray",
    group_names: list[str],
    random_names: list[str] | dict[str, list[str]],
    re_structure: str | list[str] | dict[str, str],
    sigma: float | None = None,
) -> "pl.DataFrame":
    """Build variance components DataFrame for varying effects.

    Works for both LMMs (with sigma) and GLMMs (without sigma).

    Args:
        theta: Optimized theta parameters (relative scale for LMM, absolute for GLMM).
        group_names: Names of grouping factors.
        random_names: Names of random effects per group.
        re_structure: RE structure type(s).
        sigma: Residual standard deviation. If provided (LMM), theta is scaled
            by sigma^2 and a Residual row is added. If None (GLMM), theta is
            used directly with no Residual row.

    Returns:
        DataFrame with columns [group, effect, variance, sd].

    Examples:
        >>> import numpy as np
        >>> theta = np.array([0.967, 0.015, 0.231])  # Relative scale
        >>> sigma = 25.59
        >>> df = build_varying_var_df(theta, ["Subject"], ["Intercept", "Days"], "slope", sigma=sigma)
        >>> df.columns
        ['group', 'effect', 'variance', 'sd']
    """
    import numpy as np
    import polars as pl

    rows: list[dict] = []

    # Parse RE structure for each group
    if isinstance(re_structure, str):
        structure_dict = {gn: re_structure for gn in group_names}
    elif isinstance(re_structure, list):
        structure_dict = dict(zip(group_names, re_structure))
    else:
        structure_dict = re_structure

    if isinstance(random_names, list):
        if isinstance(re_structure, list) and len(random_names) == len(group_names):
            names_dict = {gn: [random_names[i]] for i, gn in enumerate(group_names)}
        else:
            names_dict = {gn: random_names for gn in group_names}
    else:
        names_dict = random_names

    theta_idx = 0

    for group_name in group_names:
        structure = structure_dict[group_name]
        re_names = names_dict[group_name]
        n_re = len(re_names)

        # Extract theta for this group
        if structure == "intercept":
            L = np.array([[theta[theta_idx]]])
            theta_idx += 1
        elif structure == "diagonal":
            L = np.diag(theta[theta_idx : theta_idx + n_re])
            theta_idx += n_re
        elif structure == "slope":
            n_theta = n_re * (n_re + 1) // 2
            L = np.zeros((n_re, n_re))
            k = theta_idx
            for j in range(n_re):
                for i in range(j, n_re):
                    L[i, j] = theta[k]
                    k += 1
            theta_idx += n_theta
        else:
            raise ValueError(f"Unknown RE structure: {structure}")

        # Compute variance-covariance matrix
        # For LMM (sigma provided): Sigma = sigma^2 * L @ L.T
        # For GLMM (no sigma): Sigma = L @ L.T
        if sigma is not None:
            Sigma = sigma**2 * (L @ L.T)
        else:
            Sigma = L @ L.T

        # Add rows for each random effect
        for i, re_name in enumerate(re_names):
            rows.append(
                {
                    "group": group_name,
                    "effect": re_name,
                    "variance": float(Sigma[i, i]),
                    "sd": float(np.sqrt(Sigma[i, i])),
                }
            )

    # Add residual variance (LMM only)
    if sigma is not None:
        rows.append(
            {
                "group": "Residual",
                "effect": "Residual",
                "variance": sigma**2,
                "sd": sigma,
            }
        )

    return pl.DataFrame(rows)


def build_varying_corr_df(
    theta: "np.ndarray",
    group_names: list[str],
    random_names: list[str] | dict[str, list[str]],
    re_structure: str | list[str] | dict[str, str],
    sigma: float | None = None,
) -> "pl.DataFrame":
    """Build varying effects correlation DataFrame.

    Works for both LMMs and GLMMs. The sigma parameter only affects variance
    scaling but not correlations (sigma cancels out in correlation formula).

    Args:
        theta: Optimized theta parameters.
        group_names: Names of grouping factors.
        random_names: Names of random effects per group.
        re_structure: RE structure type(s).
        sigma: Residual standard deviation (optional, for API consistency).

    Returns:
        DataFrame with columns [group, effect1, effect2, corr].
        Empty DataFrame if no correlations exist.

    Examples:
        >>> import numpy as np
        >>> theta = np.array([0.967, 0.015, 0.231])  # Relative scale
        >>> sigma = 25.59
        >>> df = build_varying_corr_df(theta, ["Subject"], ["Intercept", "Days"], "slope", sigma=sigma)
        >>> df.columns
        ['group', 'effect1', 'effect2', 'corr']
    """
    import numpy as np
    import polars as pl

    rows: list[dict] = []

    # Parse RE structure for each group
    if isinstance(re_structure, str):
        structure_dict = {gn: re_structure for gn in group_names}
    elif isinstance(re_structure, list):
        structure_dict = dict(zip(group_names, re_structure))
    else:
        structure_dict = re_structure

    if isinstance(random_names, list):
        if isinstance(re_structure, list) and len(random_names) == len(group_names):
            names_dict = {gn: [random_names[i]] for i, gn in enumerate(group_names)}
        else:
            names_dict = {gn: random_names for gn in group_names}
    else:
        names_dict = random_names

    theta_idx = 0

    for group_name in group_names:
        structure = structure_dict[group_name]
        re_names = names_dict[group_name]
        n_re = len(re_names)

        # Extract theta for this group
        if structure == "intercept":
            theta_idx += 1
            continue  # No correlations for intercept-only
        elif structure == "diagonal":
            theta_idx += n_re
            continue  # No correlations for diagonal
        elif structure == "slope":
            n_theta = n_re * (n_re + 1) // 2
            L = np.zeros((n_re, n_re))
            k = theta_idx
            for j in range(n_re):
                for i in range(j, n_re):
                    L[i, j] = theta[k]
                    k += 1
            theta_idx += n_theta
        else:
            raise ValueError(f"Unknown RE structure: {structure}")

        # Compute variance-covariance matrix
        # Note: sigma cancels out in correlation formula, so we use L @ L.T directly
        Sigma = L @ L.T

        # Add correlation rows
        for i in range(n_re):
            for j in range(i + 1, n_re):
                denom = np.sqrt(Sigma[i, i] * Sigma[j, j])
                corr = Sigma[i, j] / denom if denom > 0 else 0.0
                rows.append(
                    {
                        "group": group_name,
                        "effect1": re_names[i],
                        "effect2": re_names[j],
                        "corr": float(corr),
                    }
                )

    # Return empty DataFrame with correct schema if no correlations
    if not rows:
        return pl.DataFrame(
            schema={
                "group": pl.Utf8,
                "effect1": pl.Utf8,
                "effect2": pl.Utf8,
                "corr": pl.Float64,
            }
        )

    return pl.DataFrame(rows)


def theta_to_variance_components(
    theta: "np.ndarray",
    sigma: float,
    group_names: list[str],
    random_names: list[str] | dict[str, list[str]],
    re_structure: str | list[str] | dict[str, str],
) -> tuple[list[str], list[float]]:
    """Convert theta parameters to named variance components.

    This function converts the raw Cholesky factor (theta) and residual
    standard deviation (sigma) to interpretable variance component values
    with standardized naming for use in bootstrap DataFrames.

    Args:
        theta: Optimized theta parameters (Cholesky factors, relative scale).
        sigma: Residual standard deviation.
        group_names: Names of grouping factors (e.g., ["Subject"]).
        random_names: Names of random effects per group.
            For single-structure models: list of names applied to all groups.
            For mixed-structure models: dict mapping group to names.
        re_structure: Random effects structure.
            "intercept", "slope", "diagonal" for single structure.
            List or dict for mixed structures.

    Returns:
        Tuple of (term_names, values) where:
        - term_names: List of standardized term names
        - values: List of corresponding SD or correlation values

    Naming convention:
        - Random effect SDs: "{Group}:{RE_name}_sd"
          e.g., "Subject:Intercept_sd", "Subject:Days_sd"
        - Correlations: "{Group}:corr_{RE1}:{RE2}"
          e.g., "Subject:corr_Intercept:Days"
        - Residual SD: "Residual_sd"

    Examples:
        >>> import numpy as np
        >>> theta = np.array([0.967, 0.015, 0.231])  # 2x2 Cholesky
        >>> sigma = 25.59
        >>> group_names = ["Subject"]
        >>> random_names = ["Intercept", "Days"]
        >>> re_structure = "slope"
        >>> names, values = theta_to_variance_components(
        ...     theta, sigma, group_names, random_names, re_structure
        ... )
        >>> names  # doctest: +SKIP
        ['Subject:Intercept_sd', 'Subject:Days_sd', 'Subject:corr_Intercept:Days', 'Residual_sd']
    """
    import numpy as np

    term_names = []
    values = []

    # Parse RE structure for each group
    if isinstance(re_structure, str):
        structure_dict = {gn: re_structure for gn in group_names}
    elif isinstance(re_structure, list):
        structure_dict = dict(zip(group_names, re_structure))
    else:
        structure_dict = re_structure

    # Parse random effect names
    if isinstance(random_names, list):
        if isinstance(re_structure, list) and len(random_names) == len(group_names):
            names_dict = {gn: [random_names[i]] for i, gn in enumerate(group_names)}
        else:
            names_dict = {gn: random_names for gn in group_names}
    else:
        names_dict = random_names

    theta_idx = 0

    for group_name in group_names:
        structure = structure_dict[group_name]
        re_names = names_dict[group_name]
        n_re = len(re_names)

        # Extract theta for this group and build Cholesky factor
        if structure == "intercept":
            L = np.array([[theta[theta_idx]]])
            theta_idx += 1
        elif structure == "diagonal":
            L = np.diag(theta[theta_idx : theta_idx + n_re])
            theta_idx += n_re
        elif structure == "slope":
            n_theta = n_re * (n_re + 1) // 2
            L = np.zeros((n_re, n_re))
            k = theta_idx
            for j in range(n_re):
                for i in range(j, n_re):
                    L[i, j] = theta[k]
                    k += 1
            theta_idx += n_theta
        else:
            raise ValueError(f"Unknown RE structure: {structure}")

        # Compute variance-covariance matrix: Σ = σ² × L @ L.T
        Sigma = sigma**2 * (L @ L.T)

        # Add SD terms
        for i, re_name in enumerate(re_names):
            sd = float(np.sqrt(Sigma[i, i]))
            term_names.append(f"{group_name}:{re_name}_sd")
            values.append(sd)

        # Add correlation terms (only for "slope" structure with multiple REs)
        # Diagonal and intercept structures have no correlations
        if structure == "slope" and n_re > 1:
            for i in range(n_re):
                for j in range(i + 1, n_re):
                    denom = np.sqrt(Sigma[i, i] * Sigma[j, j])
                    corr = float(Sigma[i, j] / denom) if denom > 0 else 0.0
                    term_names.append(f"{group_name}:corr_{re_names[i]}:{re_names[j]}")
                    values.append(corr)

    # Add residual SD
    term_names.append("Residual_sd")
    values.append(float(sigma))

    return term_names, values


# =============================================================================
# GLMER Result Builders
# =============================================================================


def build_glmer_result_params(schema: GLMerResultFit) -> pl.DataFrame:
    """Build glmer result_params DataFrame from schema.

    Args:
        schema: Validated GLMer schema containing coefficient table data.

    Returns:
        Coefficient table with z-statistics and df=inf.

    Examples:
        >>> schema = GLMerResultFit(
        ...     term=["(Intercept)", "period2"],
        ...     estimate=[-1.40, -0.99],
        ...     se=[0.23, 0.30],
        ...     statistic=[-6.09, -3.30],
        ...     df=[float('inf'), float('inf')],
        ...     p_value=[1.1e-09, 0.001],
        ...     ci_lower=[-1.85, -1.58],
        ...     ci_upper=[-0.95, -0.40],
        ... )
        >>> df = build_glmer_result_params(schema)
        >>> df.columns
        ['term', 'estimate', 'se', 'ci_lower', 'ci_upper', 'statistic', 'df', 'p_value']
    """
    return build_result_params(schema)


def build_glmer_result_model(
    schema: GLMerResultFitDiagnostics,
) -> pl.DataFrame:
    """Build glmer result_model DataFrame from schema.

    Args:
        schema: Validated GLMer schema containing fit statistics.

    Returns:
        Single-row DataFrame with Laplace-specific diagnostics as columns.

    Examples:
        >>> schema = GLMerResultFitDiagnostics(
        ...     nobs=56, df_model=4, df_resid=52,
        ...     family="binomial", link="logit",
        ...     deviance=184.05,
        ...     aic=194.05, bic=204.28, loglik=-92.02,
        ... )
        >>> df = build_glmer_result_model(schema)
        >>> df.columns
        ['nobs', 'df_model', 'df_resid', 'deviance', ...]
    """
    return build_result_model(schema)


# =============================================================================
# Ridge Result Builders
# =============================================================================


def build_ridge_result_params(schema: RidgeResultFit) -> pl.DataFrame:
    """Build ridge coefficient table from schema.

    Args:
        schema: Validated ridge schema containing coefficient table data.

    Returns:
        Coefficient table with optional SE and CI columns.

    Examples:
        >>> schema = RidgeResultFit(
        ...     term=["Intercept", "x"],
        ...     estimate=[1.0, 2.0],
        ...     se=[0.1, 0.2],
        ...     ci_lower=[0.8, 1.6],
        ...     ci_upper=[1.2, 2.4],
        ... )
        >>> df = build_ridge_result_params(schema)
        >>> df.columns
        ['term', 'estimate', 'se', 'ci_lower', 'ci_upper']
    """
    data = {
        "term": list(schema.term),
        "estimate": list(schema.estimate),
    }

    # Handle optional columns (None for fixed/cv asymp mode)
    if schema.se is not None:
        data["se"] = list(schema.se)
        data["ci_lower"] = list(schema.ci_lower)
        data["ci_upper"] = list(schema.ci_upper)
    else:
        # Add null columns to maintain consistent schema
        n = len(schema.term)
        data["se"] = [None] * n
        data["ci_lower"] = [None] * n
        data["ci_upper"] = [None] * n

    return pl.DataFrame(data)


def build_ridge_result_model(
    schema: RidgeResultFitDiagnostics,
) -> pl.DataFrame:
    """Build ridge fit statistics table from schema.

    Returns a single-row wide DataFrame with one column per metric.

    Args:
        schema: Validated ridge schema containing fit statistics.

    Returns:
        Single-row DataFrame with metrics as columns.

    Examples:
        >>> schema = RidgeResultFitDiagnostics(
        ...     nobs=32, df_model=2, df_effective=1.8, rsquared=0.83,
        ...     rsquared_adj=0.81, mode="auto", alpha=None, c_hat=1.5,
        ...     cv_score=None, prior_scale=2.5, sigma=2.59, gcv=7.2,
        ...     aic=156.4, bic=162.3,
        ... )
        >>> df = build_ridge_result_model(schema)
        >>> df.columns
        ['nobs', 'df_model', 'df_effective', 'rsquared', ...]
    """
    col_order = [
        "nobs",
        "df_model",
        "df_effective",
        "rsquared",
        "rsquared_adj",
        "mode",
        "alpha",
        "c_hat",
        "cv_score",
        "prior_scale",
        "sigma",
        "gcv",
        "aic",
        "bic",
    ]

    data = {}
    for stat_name in col_order:
        value = getattr(schema, stat_name)
        data[stat_name] = [value]

    return pl.DataFrame(data)


# =============================================================================
# MEE (Marginal Estimated Effects) Builders
# =============================================================================

# Column ordering constants for MEE results
_RESULT_MEE_COLUMNS_MINIMAL = ["term", "level", "estimate"]

_RESULT_MEE_COLUMNS_ASYMP = [
    "term",
    "level",
    "estimate",
    "se",
    "df",
    "ci_lower",
    "ci_upper",
]

_RESULT_MEE_COLUMNS_ASYMP_CONTRAST = [
    "term",
    "level",
    "estimate",
    "se",
    "df",
    "statistic",
    "p_value",
    "ci_lower",
    "ci_upper",
]

_RESULT_MEE_COLUMNS_BOOT = [
    "term",
    "level",
    "estimate",
    "se",
    "ci_lower",
    "ci_upper",
    "n_resamples",
]

_RESULT_MEE_COLUMNS_CONTRAST = [
    "term",
    "contrast",
    "estimate",
    "se",
    "df",
    "statistic",
    "p_value",
    "ci_lower",
    "ci_upper",
]


def build_mee_result(schema: MeeResult) -> pl.DataFrame:
    """Build minimal MEE DataFrame from schema.

    Args:
        schema: Validated MEE schema containing term, level, estimate.

    Returns:
        MEE table with columns: term, level, estimate.

    Examples:
        >>> schema = MeeResult(
        ...     term=["treatment", "treatment"],
        ...     level=["A", "B"],
        ...     estimate=[2.5, 3.5],
        ... )
        >>> df = build_mee_result(schema)
        >>> df.columns
        ['term', 'level', 'estimate']
    """
    data = {
        "term": list(schema.term),
        "level": list(schema.level),
        "estimate": list(schema.estimate),
    }

    df = pl.DataFrame(data)
    return df.select(_RESULT_MEE_COLUMNS_MINIMAL)


def build_mee_asymp_result(schema: MeeAsympResult) -> pl.DataFrame:
    """Build MEE DataFrame with asymptotic inference from schema.

    Args:
        schema: Validated MEE schema with SE, df, and CIs.

    Returns:
        MEE table with asymptotic inference columns.

    Examples:
        >>> schema = MeeAsympResult(
        ...     term=["treatment", "treatment"],
        ...     level=["A", "B"],
        ...     estimate=[2.5, 3.5],
        ...     se=[0.3, 0.4],
        ...     df=[28.0, 28.0],
        ...     ci_lower=[1.9, 2.7],
        ...     ci_upper=[3.1, 4.3],
        ... )
        >>> df = build_mee_asymp_result(schema)
        >>> df.columns
        ['term', 'level', 'estimate', 'se', 'df', 'ci_lower', 'ci_upper']
    """
    data = {
        "term": list(schema.term),
        "level": list(schema.level),
        "estimate": list(schema.estimate),
        "se": list(schema.se),
        "df": list(schema.df),
        "ci_lower": list(schema.ci_lower),
        "ci_upper": list(schema.ci_upper),
    }

    # Add optional contrast columns if present
    if schema.statistic is not None:
        data["statistic"] = list(schema.statistic)
    if schema.p_value is not None:
        data["p_value"] = list(schema.p_value)

    df = pl.DataFrame(data)

    # Choose column order based on presence of contrast columns
    if "statistic" in data:
        columns = _RESULT_MEE_COLUMNS_ASYMP_CONTRAST
    else:
        columns = _RESULT_MEE_COLUMNS_ASYMP

    # Filter to present columns and reorder
    present_columns = [c for c in columns if c in df.columns]
    return df.select(present_columns)


def build_mee_boot_result(schema: MeeBootResult) -> pl.DataFrame:
    """Build MEE DataFrame with bootstrap inference from schema.

    Args:
        schema: Validated bootstrap MEE schema.

    Returns:
        MEE table with bootstrap SE and CIs.

    Examples:
        >>> schema = MeeBootResult(
        ...     term=["treatment", "treatment"],
        ...     level=["A", "B"],
        ...     estimate=[2.5, 3.5],
        ...     se=[0.35, 0.42],
        ...     ci_lower=[1.8, 2.6],
        ...     ci_upper=[3.2, 4.4],
        ...     n_resamples=999,
        ...     ci_type="bca",
        ... )
        >>> df = build_mee_boot_result(schema)
        >>> df.columns
        ['term', 'level', 'estimate', 'se', 'ci_lower', 'ci_upper', 'n_resamples']
    """
    n_rows = len(schema.term)
    data = {
        "term": list(schema.term),
        "level": list(schema.level),
        "estimate": list(schema.estimate),
        "se": list(schema.se),
        "ci_lower": list(schema.ci_lower),
        "ci_upper": list(schema.ci_upper),
        "n_resamples": [schema.n_resamples] * n_rows,
    }

    df = pl.DataFrame(data)
    return df.select(_RESULT_MEE_COLUMNS_BOOT)


def build_mee_contrast_result(schema: MeeContrastResult) -> pl.DataFrame:
    """Build MEE contrast DataFrame from schema.

    Args:
        schema: Validated contrast schema with full inference.

    Returns:
        Contrast table with p-values and test statistics.

    Examples:
        >>> schema = MeeContrastResult(
        ...     term=["treatment"],
        ...     contrast=["A - B"],
        ...     estimate=[-1.0],
        ...     se=[0.5],
        ...     df=[28.0],
        ...     statistic=[-2.0],
        ...     p_value=[0.055],
        ...     ci_lower=[-2.0],
        ...     ci_upper=[0.0],
        ... )
        >>> df = build_mee_contrast_result(schema)
        >>> df.columns
        ['term', 'contrast', 'estimate', 'se', 'df', 'statistic', 'p_value', ...]
    """
    data = {
        "term": list(schema.term),
        "contrast": list(schema.contrast),
        "estimate": list(schema.estimate),
        "se": list(schema.se),
        "df": list(schema.df),
        "statistic": list(schema.statistic),
        "p_value": list(schema.p_value),
        "ci_lower": list(schema.ci_lower),
        "ci_upper": list(schema.ci_upper),
    }

    df = pl.DataFrame(data)
    return df.select(_RESULT_MEE_COLUMNS_CONTRAST)
