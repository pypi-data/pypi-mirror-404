"""Result DataFrame wrappers with transformation methods.

Provides wrapper classes that behave like DataFrames but add
domain-specific transformation methods for statistical results.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import polars as pl
from scipy import stats

if TYPE_CHECKING:
    from bossanova.models.base.model import BaseModel

__all__ = [
    "BaseResultWrapper",
    "ResultFit",
    "ResultMee",
]


# =============================================================================
# Base Wrapper Class
# =============================================================================


class BaseResultWrapper:
    """Base wrapper providing DataFrame delegation and shared methods.

    Behaves like a polars DataFrame for all standard operations through
    attribute delegation. Subclasses add domain-specific transformation
    methods.

    Examples:
        >>> result = model.result_params
        >>> result.shape              # Delegated to DataFrame
        >>> result.filter(...)        # Polars filtering works
        >>> result.to_dataframe()     # Get raw DataFrame
    """

    def __init__(self, df: pl.DataFrame, model: BaseModel):
        """Initialize wrapper.

        Args:
            df: The underlying result DataFrame.
            model: Reference to the fitted model (for vcov, family, etc.).
        """
        self._df = df
        self._model = model

    def __repr__(self) -> str:
        """Show the underlying DataFrame."""
        return repr(self._df)

    def __str__(self) -> str:
        """Show the underlying DataFrame."""
        return str(self._df)

    def _repr_html_(self) -> str:
        """HTML representation for Jupyter notebooks."""
        return self._df._repr_html_()

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to underlying DataFrame."""
        return getattr(self._df, name)

    def __getitem__(self, key: Any) -> Any:
        """Delegate indexing to underlying DataFrame."""
        return self._df[key]

    def __len__(self) -> int:
        """Return number of rows."""
        return len(self._df)

    def __iter__(self):
        """Iterate over columns."""
        return iter(self._df)

    # =========================================================================
    # Shared Methods
    # =========================================================================

    def to_dataframe(self) -> pl.DataFrame:
        """Return the underlying polars DataFrame.

        Use this if you need the raw DataFrame without the wrapper.

        Returns:
            The underlying polars DataFrame.
        """
        return self._df

    def filter_significant(self, alpha: float = 0.05) -> pl.DataFrame:
        """Filter to statistically significant results.

        Args:
            alpha: Significance threshold. Default 0.05.

        Returns:
            DataFrame containing only rows where p_value < alpha.

        Raises:
            ValueError: If p_value column not present.

        Examples:
            >>> model.result_params.filter_significant()        # p < 0.05
            >>> model.result_params.filter_significant(0.01)   # p < 0.01
        """
        if "p_value" not in self._df.columns:
            raise ValueError(
                "Cannot filter by significance: 'p_value' column not found. "
                "Call .infer() first to compute p-values."
            )
        return self._df.filter(pl.col("p_value") < alpha)

    def recompute_ci(self, conf_level: float = 0.95) -> pl.DataFrame:
        """Recompute confidence intervals at a different confidence level.

        Uses the standard errors from the original fit to compute new
        confidence intervals at the specified level.

        Args:
            conf_level: Confidence level (0-1). Default 0.95 for 95% CI.

        Returns:
            DataFrame with updated ci_lower and ci_upper columns.

        Raises:
            ValueError: If se column not present.

        Examples:
            >>> model.result_params.recompute_ci(0.99)  # 99% CIs
        """
        if "se" not in self._df.columns:
            raise ValueError(
                "Cannot recompute CIs: 'se' column not found. "
                "Call .infer() first to compute standard errors."
            )

        # Determine critical value using model's inference df
        # Uses _get_inference_df() which returns inf for glm/glmer (z-distribution)
        # and residual df for lm (t-distribution)
        df = self._model._get_inference_df()
        if np.isfinite(df):
            # t-distribution for lm/lmer
            crit = stats.t.ppf(1 - (1 - conf_level) / 2, df=df)
        else:
            # z-distribution for glm/glmer
            crit = stats.norm.ppf(1 - (1 - conf_level) / 2)

        # Recompute CIs
        return self._df.with_columns(
            [
                (pl.col("estimate") - crit * pl.col("se")).alias("ci_lower"),
                (pl.col("estimate") + crit * pl.col("se")).alias("ci_upper"),
            ]
        )


# =============================================================================
# ResultFit - Coefficient Results Wrapper
# =============================================================================


class ResultFit(BaseResultWrapper):
    """Wrapper around result_params DataFrame with transformation methods.

    Behaves like a polars DataFrame for all standard operations, but adds
    methods for common statistical transformations like odds ratios,
    effect sizes, and confidence interval recomputation.

    Examples:
        >>> model = lm("y ~ x", data=df).fit()
        >>> model.result_params                    # Shows DataFrame
        >>> model.result_params.shape              # (3, 8) - delegated
        >>> model.result_params.filter(...)        # Polars filtering works
        >>> model.result_params.to_odds_ratio()    # Transformed DataFrame
        >>> model.result_params.recompute_ci(0.99) # New CIs at 99%
    """

    # =========================================================================
    # Coefficient-Specific Methods
    # =========================================================================

    def to_odds_ratio(self) -> pl.DataFrame:
        """Transform coefficients and CIs to odds ratio scale.

        Exponentiates estimate, ci_lower, and ci_upper columns.
        Only meaningful for binomial GLM models (logit, probit, cloglog).

        Returns:
            DataFrame with exponentiated values. Column names unchanged
            but values are now on odds ratio scale.

        Raises:
            ValueError: If model is not a binomial GLM.

        Examples:
            >>> model = glm("y ~ x", data=df, family="binomial").fit()
            >>> model.result_params.to_odds_ratio()
        """
        # Check if model has family attribute and is binomial
        if not hasattr(self._model, "_family"):
            raise ValueError(
                "to_odds_ratio() only valid for GLM models. "
                "This model does not have a family attribute."
            )
        if self._model._family.name != "binomial":
            raise ValueError(
                f"to_odds_ratio() only valid for binomial family, "
                f"got '{self._model._family.name}'."
            )

        # Exponentiate the relevant columns
        cols_to_exp = ["estimate", "ci_lower", "ci_upper"]
        existing_cols = [c for c in cols_to_exp if c in self._df.columns]

        return self._df.with_columns([pl.col(c).exp() for c in existing_cols])

    def to_effect_size(self, *, include_intercept: bool = False) -> pl.DataFrame:
        """Compute standardized effect sizes.

        Computes multiple effect size measures:
        - **d** (Cohen's d): estimate / residual SD
        - **r_semi** (semi-partial r): |t| / sqrt(t² + df_resid)
        - **eta_sq** (eta-squared): t² / (t² + df_resid)
        - **odds_ratio**: exp(estimate) for binomial GLM only

        Args:
            include_intercept: Whether to include intercept in output.
                Default False since intercept effect size is rarely meaningful.

        Returns:
            DataFrame with columns:
                - term, estimate, statistic
                - d, d_lower, d_upper (Cohen's d with CIs)
                - r_semi, eta_sq
                - odds_ratio (binomial GLM only)

        Examples:
            >>> model = lm("y ~ x", data=df).fit()
            >>> model.result_params.to_effect_size()
        """
        # Get residual SD from model (required for Cohen's d)
        sigma = None
        if hasattr(self._model, "_sigma"):
            sigma = self._model._sigma
        elif hasattr(self._model, "sigma"):
            sigma = self._model.sigma

        # Get df_resid for r_semi and eta_sq
        df_resid = None
        if hasattr(self._model, "result_model"):
            diag = self._model.result_model
            if "df_resid" in diag.columns:
                df_resid = float(diag["df_resid"][0])

        # Check if binomial GLM
        is_binomial = False
        if hasattr(self._model, "family"):
            family = self._model.family
            if isinstance(family, str):
                is_binomial = family.lower() in ("binomial", "logistic")

        # Start with base columns
        result = self._df.clone()

        # Filter intercept first if requested
        if not include_intercept:
            result = result.filter(pl.col("term") != "Intercept")

        # Compute Cohen's d with CIs (requires sigma)
        if sigma is not None and sigma > 0:
            result = result.with_columns(
                (pl.col("estimate") / sigma).alias("d"),
                (pl.col("ci_lower") / sigma).alias("d_lower"),
                (pl.col("ci_upper") / sigma).alias("d_upper"),
            )
        else:
            result = result.with_columns(
                pl.lit(None).cast(pl.Float64).alias("d"),
                pl.lit(None).cast(pl.Float64).alias("d_lower"),
                pl.lit(None).cast(pl.Float64).alias("d_upper"),
            )

        # Compute r_semi and eta_sq (requires statistic and df_resid)
        if "statistic" in result.columns and df_resid is not None and df_resid > 0:
            result = result.with_columns(
                # r_semi = |t| / sqrt(t^2 + df)
                (
                    pl.col("statistic").abs()
                    / (pl.col("statistic").pow(2) + df_resid).sqrt()
                ).alias("r_semi"),
                # eta_sq = t^2 / (t^2 + df)
                (
                    pl.col("statistic").pow(2) / (pl.col("statistic").pow(2) + df_resid)
                ).alias("eta_sq"),
            )
        else:
            result = result.with_columns(
                pl.lit(None).cast(pl.Float64).alias("r_semi"),
                pl.lit(None).cast(pl.Float64).alias("eta_sq"),
            )

        # Add odds_ratio for binomial GLM
        if is_binomial:
            result = result.with_columns(
                pl.col("estimate").exp().alias("odds_ratio"),
            )

        return result

    def filter_params(self, params: list[str] | str) -> pl.DataFrame:
        """Filter to specific parameter terms.

        Convenience method for filtering the result to specific coefficients.

        Args:
            params: Parameter name(s) to include.

        Returns:
            Filtered DataFrame with only the specified parameters.

        Examples:
            >>> model.result_params.filter_params("Income")
            >>> model.result_params.filter_params(["Income", "Age"])
        """
        if isinstance(params, str):
            params = [params]

        return self._df.filter(pl.col("term").is_in(params))

    def exclude_intercept(self) -> pl.DataFrame:
        """Return results excluding the intercept term.

        Convenience method for filtering out the intercept, which is often
        not of substantive interest.

        Returns:
            DataFrame with intercept row removed.

        Examples:
            >>> model.result_params.exclude_intercept()
        """
        return self._df.filter(pl.col("term") != "Intercept")


# =============================================================================
# ResultMee - Marginal Effects Results Wrapper
# =============================================================================


class ResultMee(BaseResultWrapper):
    """Wrapper around result_mee DataFrame with transformation methods.

    Behaves like a polars DataFrame for all standard operations, but adds
    methods for filtering and transforming marginal effects results.

    Examples:
        >>> model = lm("y ~ treatment * age", data=df).fit()
        >>> model.mee("treatment").infer()
        >>> model.result_mee                      # Shows DataFrame
        >>> model.result_mee.filter_terms("treatment")
        >>> model.result_mee.filter_levels(["A", "B"])
    """

    # =========================================================================
    # MEE-Specific Methods
    # =========================================================================

    def filter_terms(self, terms: list[str] | str) -> pl.DataFrame:
        """Filter to specific focal variable terms.

        Args:
            terms: Term name(s) to include (e.g., "treatment", "age").

        Returns:
            Filtered DataFrame with only the specified terms.

        Examples:
            >>> model.result_mee.filter_terms("treatment")
            >>> model.result_mee.filter_terms(["treatment", "age"])
        """
        if isinstance(terms, str):
            terms = [terms]

        return self._df.filter(pl.col("term").is_in(terms))

    def filter_levels(self, levels: list[str] | str) -> pl.DataFrame:
        """Filter to specific factor levels.

        Args:
            levels: Level name(s) to include (e.g., "A", "B", "slope").

        Returns:
            Filtered DataFrame with only the specified levels.

        Examples:
            >>> model.result_mee.filter_levels("A")
            >>> model.result_mee.filter_levels(["A", "B"])
        """
        if isinstance(levels, str):
            levels = [levels]

        return self._df.filter(pl.col("level").is_in(levels))

    def filter_contrasts(self, contrasts: list[str] | str) -> pl.DataFrame:
        """Filter to specific contrasts (for contrast results only).

        Args:
            contrasts: Contrast name(s) to include (e.g., "A - B").

        Returns:
            Filtered DataFrame with only the specified contrasts.

        Raises:
            ValueError: If 'contrast' column not present.

        Examples:
            >>> model.mee("treatment", contrasts="pairwise").infer()
            >>> model.result_mee.filter_contrasts("A - B")
        """
        if "contrast" not in self._df.columns:
            raise ValueError(
                "Cannot filter by contrast: 'contrast' column not found. "
                "This result does not contain contrasts."
            )

        if isinstance(contrasts, str):
            contrasts = [contrasts]

        return self._df.filter(pl.col("contrast").is_in(contrasts))

    def to_response_scale(self) -> pl.DataFrame:
        """Transform estimates from link scale to response scale.

        For GLM/GLMER models, applies the inverse link function to
        transform estimates (and CIs if present) to the response scale.

        Returns:
            DataFrame with transformed values on response scale.

        Raises:
            ValueError: If model does not have a link function.

        Examples:
            >>> model = glm("y ~ x", data=df, family="binomial").fit()
            >>> model.mee("x", units="link").infer()
            >>> model.result_mee.to_response_scale()  # Probabilities
        """
        if not hasattr(self._model, "_family"):
            raise ValueError(
                "to_response_scale() only valid for GLM/GLMER models. "
                "This model does not have a family attribute."
            )

        family = self._model._family
        linv = family.link_inverse

        # Transform estimate and CIs if present
        cols_to_transform = ["estimate"]
        if "ci_lower" in self._df.columns:
            cols_to_transform.extend(["ci_lower", "ci_upper"])

        return self._df.with_columns(
            [
                pl.col(c).map_elements(linv, return_dtype=pl.Float64)
                for c in cols_to_transform
            ]
        )
