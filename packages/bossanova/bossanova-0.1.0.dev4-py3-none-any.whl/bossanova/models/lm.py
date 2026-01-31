"""Linear model (OLS regression) implementation.

This module provides the `lm` class for fitting linear models using
ordinary least squares (OLS), equivalent to R's `lm()` function.

Examples:
    >>> from bossanova import lm
    >>> model = lm("mpg ~ wt + hp", data=mtcars)
    >>> model.fit()
    >>> print(model.result_params)
"""

from __future__ import annotations

__all__ = ["lm"]

from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import polars as pl
from scipy import stats

from bossanova._backend import _lock_backend
from bossanova._utils import coerce_dataframe
from bossanova.models.base import BaseModel
from bossanova.results.builders import build_result_params, build_result_model
from bossanova.results.schemas import LMResultFit, LMResultFitDiagnostics

if TYPE_CHECKING:
    from typing_extensions import Self
    from pandas import DataFrame as PandasDataFrame
    from bossanova.resample.results import PermutationResult, BootstrapResult, CVResult
    from bossanova.results.wrappers import ResultFit


class lm(BaseModel):
    """Linear model with OLS estimation.

    Args:
        formula: Model formula in R-style syntax (e.g., "y ~ x1 + x2").
        data: Input data as pandas or polars DataFrame.
        missing: How to handle missing values in formula variables:
            - "drop" (default): Drop rows with NAs, warn user with count.
            - "fail": Raise ValueError if any NAs in formula variables.

    Attributes:
        formula: The model formula.
        data: The input data (converted to polars).
        designmat: Design matrix as DataFrame.
        is_fitted: Whether the model has been fitted.
        nobs: Number of observations used in fitting (excludes missing).
        nobs_total: Total rows in input data.
        nobs_missing: Number of rows dropped due to missing values.
        missing_info: Per-variable breakdown of rows with missing values.
        coef_: Coefficient estimates as numpy array (sklearn-compatible).
        params: Population-level coefficients as DataFrame with columns
            [term, estimate].
        fitted: Fitted values (predicted values for training data).
        residuals: Residuals (observed - fitted).
        vcov: Variance-covariance matrix of coefficients.
        result_params: Full fit results including estimates, standard errors,
            confidence intervals, and p-values.
    """

    def __init__(
        self,
        formula: str,
        data: pl.DataFrame | PandasDataFrame,
        missing: Literal["drop", "fail"] = "drop",
    ):
        """Initialize linear model.

        Args:
            formula: Model formula.
            data: Input data.
            missing: How to handle missing values ("drop" or "fail").
        """
        super().__init__(formula, data, missing=missing)

    def _repr_parts(self) -> list[tuple[str, Any]]:
        """Return (key, value) pairs for repr."""
        parts = super()._repr_parts()
        if self.is_fitted:
            parts.append(("estimation", "OLS"))
            parts.append(("inference", self._inference))
        return parts

    def fit(
        self,
        solver: str = "qr",
        weights: str | None = None,
    ) -> Self:
        """Fit the linear model using OLS.

        Computes parameter estimates only. Call `.infer()` after fitting to
        compute standard errors, confidence intervals, and p-values.

        Args:
            solver: Fitting method: "qr" (QR decomposition) or "svd" (SVD).
            weights: Column name for observation weights. If provided, must be
                a column in the data with non-negative values. Zero weights
                are allowed but will exclude those observations.

        Returns:
            Fitted model instance.

        Examples:
            >>> model = lm("y ~ x", data=df).fit()  # Estimates only
            >>> model.infer()  # Add asymptotic inference
            >>> model.infer(how="boot", n=999)  # Bootstrap inference
            >>> # Weighted least squares
            >>> model = lm("y ~ x", data=df).fit(weights="w")
        """
        # Lock backend to prevent switching after fit
        _lock_backend()

        # Handle weights parameter (column name -> array)
        self._weights_column = weights  # Store column name for ablation
        self._weight_info = None  # Initialize weight metadata

        if weights is not None:
            if weights not in self._data.columns:
                raise ValueError(f"weights column '{weights}' not found in data")

            # Check if weights column is categorical (factor)
            from bossanova.ops.weights import (
                detect_weight_type,
                compute_inverse_variance_weights,
            )

            if detect_weight_type(self._data, weights):
                # Categorical: compute inverse-variance weights
                self._weight_info = compute_inverse_variance_weights(
                    self._data, self._y_name, weights, self._valid_mask
                )
                self._weights = self._weight_info.weights
            else:
                # Numeric: use directly (existing behavior)
                weights_arr = self._data[weights].to_numpy()
                if np.any(weights_arr < 0):
                    raise ValueError("weights must be non-negative")
                self._weights = weights_arr
        else:
            self._weights = None

        # Import solver functions
        from bossanova.ops.linalg import qr_solve, svd_solve

        # Select solver
        if solver == "qr":
            solve_fn = qr_solve
        elif solver == "svd":
            solve_fn = svd_solve
        else:
            raise ValueError(f"Unknown solver: {solver}. Use 'qr' or 'svd'.")

        # Fit model on valid rows only (excludes rows with missing values)
        X_fit_orig = self._X[self._valid_mask]
        y_fit_orig = self._y[self._valid_mask]
        weights_fit = (
            self._weights[self._valid_mask] if self._weights is not None else None
        )

        # For weighted OLS, transform: X_w = sqrt(W) @ X, y_w = sqrt(W) @ y
        # This gives the same result as (X'WX)^{-1} X'Wy
        if weights_fit is not None:
            sqrt_w = np.sqrt(weights_fit)
            X_fit = X_fit_orig * sqrt_w[:, np.newaxis]
            y_fit = y_fit_orig * sqrt_w
        else:
            X_fit = X_fit_orig
            y_fit = y_fit_orig

        result = solve_fn(X_fit, y_fit)

        # Extract results
        self._coef = result.coef
        self._vcov = result.vcov
        self._sigma = np.sqrt(result.sigma2)  # Convert variance to std dev
        self._df_resid = result.df_resid
        self._rank = result.rank

        # Compute fitted values and residuals on original (unweighted) data
        fitted_valid = X_fit_orig @ self._coef
        residuals_valid = y_fit_orig - fitted_valid

        # Expand fitted values and residuals to full length (NaN for missing rows)
        self._fitted_values = self._expand_to_full_length(fitted_valid)
        self._residuals = self._expand_to_full_length(residuals_valid)

        # Compute leverage on (weighted) X for proper diagnostics
        from bossanova.ops.diagnostics import compute_leverage

        leverage_valid = compute_leverage(X_fit)
        self._leverage = self._expand_to_full_length(leverage_valid)

        # Set fitted flag
        self.is_fitted = True

        # Build result DataFrames (estimates only, no inference)
        self._result_params = self._compute_result_params_none()
        self._inference = None

        # Always compute diagnostics
        self._result_model = self._compute_result_model()

        # Augment data with diagnostic columns
        self._augment_data()

        # Track operation for .infer() dispatch
        self._last_operation = "fit"

        return self

    def _compute_result_params(self, conf_level: float = 0.95) -> pl.DataFrame:
        """Build coefficient table.

        Args:
            conf_level: Confidence level for CIs.

        Returns:
            Coefficient table with schema from LMResultFit.
        """
        from bossanova.ops.inference import (
            compute_ci,
            compute_se_from_vcov,
            compute_t_critical,
        )

        # Compute standard errors
        se = compute_se_from_vcov(self._vcov)

        # Compute t-statistics (handle SE=0 for perfect fit cases)
        t_stats = np.divide(
            self._coef, se, out=np.full_like(self._coef, np.nan), where=se != 0
        )

        # Compute p-values using t-distribution
        p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=self._df_resid))

        # Compute confidence intervals
        t_crit = compute_t_critical(conf_level, df=self._df_resid)
        ci_lower, ci_upper = compute_ci(self._coef, se, t_crit)

        # Build schema
        schema = LMResultFit(
            term=self._X_names,
            estimate=self._get_coef().tolist(),
            se=se.tolist(),
            statistic=t_stats.tolist(),
            df=[float(self._df_resid)] * len(self._coef),
            p_value=p_values.tolist(),
            ci_lower=ci_lower.tolist(),
            ci_upper=ci_upper.tolist(),
        )

        return build_result_params(schema)

    def _compute_result_params_none(self) -> pl.DataFrame:
        """Build coefficient table with estimates only (no inference).

        Returns:
            Coefficient table with NaN for inference columns.
        """
        n_coef = len(self._coef)
        nan_list = [float("nan")] * n_coef

        # Build schema with NaN for inference columns
        schema = LMResultFit(
            term=self._X_names,
            estimate=self._get_coef().tolist(),
            se=nan_list,
            statistic=nan_list,
            df=nan_list,
            p_value=nan_list,
            ci_lower=nan_list,
            ci_upper=nan_list,
        )

        return build_result_params(schema)

    def _compute_result_params_welch(self, conf_level: float = 0.95) -> pl.DataFrame:
        """Build coefficient table with Welch-Satterthwaite df.

        Uses Welch-Satterthwaite degrees of freedom for inference when
        factor-based inverse-variance weights were used in fitting.
        This makes WLS equivalent to Welch's t-test.

        Args:
            conf_level: Confidence level for CIs.

        Returns:
            Coefficient table with Welch df and adjusted inference.

        Raises:
            ValueError: If weights were not from a factor column.
        """
        if self._weight_info is None or not self._weight_info.is_factor:
            raise ValueError(
                "vcov_type='welch' requires weights from a factor column. "
                "Use fit(weights='column_name') where column_name is categorical."
            )

        from bossanova.ops.inference import (
            compute_se_from_vcov,
        )
        from bossanova.stats.welch import welch_satterthwaite_df

        # Compute Welch-Satterthwaite df
        welch_df = welch_satterthwaite_df(
            self._weight_info.group_variances,
            self._weight_info.group_counts,
        )

        # Compute standard errors
        se = compute_se_from_vcov(self._vcov)

        # Compute t-statistics (handle SE=0 for perfect fit cases)
        t_stats = np.divide(
            self._coef, se, out=np.full_like(self._coef, np.nan), where=se != 0
        )

        # Compute p-values using t-distribution with Welch df
        p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=welch_df))

        # Compute confidence intervals with Welch df
        t_crit = stats.t.ppf(1 - (1 - conf_level) / 2, df=welch_df)
        ci_lower = self._coef - t_crit * se
        ci_upper = self._coef + t_crit * se

        # Build schema
        schema = LMResultFit(
            term=self._X_names,
            estimate=self._get_coef().tolist(),
            se=se.tolist(),
            statistic=t_stats.tolist(),
            df=[float(welch_df)] * len(self._coef),
            p_value=p_values.tolist(),
            ci_lower=ci_lower.tolist(),
            ci_upper=ci_upper.tolist(),
        )

        return build_result_params(schema)

    def _compute_result_params_with_errors(
        self, conf_level: float, errors: str
    ) -> pl.DataFrame:
        """Build coefficient table with specified error structure.

        Handles different error assumptions for robust inference:
        - 'iid': Standard OLS (homoscedastic, independent)
        - 'hetero' or 'HC3': Sandwich HC3 estimator (arbitrary heteroscedasticity)
        - 'HC0', 'HC1', 'HC2': Other sandwich estimators
        - 'unequal_var': Welch-style (group-specific variances, auto-detect factors)

        Args:
            conf_level: Confidence level for CIs.
            errors: Error structure assumption.

        Returns:
            Coefficient table with appropriate inference.

        Raises:
            ValueError: If errors='unequal_var' but no factors in formula.
        """
        from bossanova.ops.inference import (
            compute_se_from_vcov,
        )

        # Determine vcov and df based on error structure
        if errors in ("auto", "iid"):
            # Standard OLS inference ('auto' defaults to 'iid')
            vcov = self._vcov
            df = self._df_resid
            self._cell_info = None  # Clear any previous cell info

        elif errors in ("hetero", "HC0", "HC1", "HC2", "HC3"):
            # Sandwich (HC) estimator
            from bossanova.stats.sandwich import compute_hc_vcov

            hc_type = "HC3" if errors == "hetero" else errors

            # Need XtX_inv - recompute from vcov if not stored
            # vcov = sigma^2 * (X'X)^{-1}, so (X'X)^{-1} = vcov / sigma^2
            XtX_inv = self._vcov / (self._sigma**2)

            vcov = compute_hc_vcov(
                self._X[self._valid_mask],
                self._residuals[self._valid_mask],
                XtX_inv,
                hc_type=hc_type,
            )
            df = self._df_resid  # Use OLS df (conservative)
            self._cell_info = None  # Clear any previous cell info

        elif errors == "unequal_var":
            # Welch-style inference with auto-detected factors
            from bossanova.stats.welch import (
                compute_cell_info,
                extract_factors_from_formula,
                welch_satterthwaite_df,
            )

            # Extract factors from formula
            factors = extract_factors_from_formula(self._formula, self._data)

            if not factors:
                raise ValueError(
                    "errors='unequal_var' requires at least one factor (categorical) "
                    "variable in the formula. Found only continuous predictors.\n"
                    "For arbitrary heteroscedasticity, use errors='hetero' instead."
                )

            # Compute cell-based variances from residuals
            # Use only valid (non-NA) data
            valid_data = self._data.filter(pl.Series(self._valid_mask))
            cell_info = compute_cell_info(
                self._residuals[self._valid_mask],
                valid_data,
                factors,
            )
            self._cell_info = cell_info  # Store for jointtest

            # Welch-Satterthwaite df
            df = welch_satterthwaite_df(
                cell_info.cell_variances,
                cell_info.cell_counts,
            )

            # Use OLS vcov (estimates unchanged, only df changes)
            vcov = self._vcov

        else:
            raise ValueError(
                f"Unknown errors type: {errors!r}. "
                "Use 'iid', 'hetero', 'unequal_var', or 'HC0'/'HC1'/'HC2'/'HC3'."
            )

        # Store the errors type for later use
        self._errors_type = errors

        # Compute standard errors from vcov
        se = compute_se_from_vcov(vcov)

        # Compute t-statistics (handle SE=0 for perfect fit cases)
        t_stats = np.divide(
            self._coef, se, out=np.full_like(self._coef, np.nan), where=se != 0
        )

        # Compute p-values using t-distribution
        p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=df))

        # Compute confidence intervals
        t_crit = stats.t.ppf(1 - (1 - conf_level) / 2, df=df)
        ci_lower = self._coef - t_crit * se
        ci_upper = self._coef + t_crit * se

        # Build schema
        schema = LMResultFit(
            term=self._X_names,
            estimate=self._get_coef().tolist(),
            se=se.tolist(),
            statistic=t_stats.tolist(),
            df=[float(df)] * len(self._coef),
            p_value=p_values.tolist(),
            ci_lower=ci_lower.tolist(),
            ci_upper=ci_upper.tolist(),
        )

        return build_result_params(schema)

    def _compute_result_model(self) -> pl.DataFrame:
        """Build fit statistics table.

        Returns:
            Fit statistics with schema from LMResultFitDiagnostics.
        """
        # Use valid (non-NA) values for R-squared calculation
        y_valid = self._y[self._valid_mask]
        resid_valid = self._residuals[self._valid_mask]

        # Compute R-squared
        y_mean = np.mean(y_valid)
        ss_tot = np.sum((y_valid - y_mean) ** 2)
        ss_res = np.sum(resid_valid**2)
        rsquared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        # Clamp to [0, 1] to handle floating point issues (e.g., intercept-only models)
        rsquared = float(np.clip(rsquared, 0.0, 1.0))

        # Compute adjusted R-squared
        n = self._n
        p = self._p
        rsquared_adj = 1 - (1 - rsquared) * (n - 1) / (n - p) if n > p else 0.0
        rsquared_adj = float(np.clip(rsquared_adj, 0.0, 1.0))

        # Compute F-statistic
        if p > 1 and rsquared < 1:
            fstatistic = (rsquared / (p - 1)) / ((1 - rsquared) / (n - p))
            fstatistic_pvalue = 1 - stats.f.cdf(fstatistic, p - 1, n - p)
        else:
            fstatistic = 0.0
            fstatistic_pvalue = 1.0

        # Compute AIC, BIC, logLik
        loglik = -0.5 * n * (np.log(2 * np.pi) + np.log(self._sigma**2) + 1)
        aic = -2 * loglik + 2 * (p + 1)  # +1 for sigma
        bic = -2 * loglik + np.log(n) * (p + 1)

        # Build schema
        schema = LMResultFitDiagnostics(
            nobs=int(n),
            df_model=int(p - 1),  # exclude intercept
            df_resid=float(self._df_resid),
            rsquared=float(rsquared),
            rsquared_adj=float(rsquared_adj),
            fstatistic=float(fstatistic),
            fstatistic_pvalue=float(fstatistic_pvalue),
            sigma=float(self._sigma),
            aic=float(aic),
            bic=float(bic),
            loglik=float(loglik),
        )

        return build_result_model(schema)

    def _compute_model_stats_from_coef(self, coef: np.ndarray) -> dict[str, float]:
        """Compute model-level stats for given coefficient vector.

        Used for bootstrap CIs of model-level statistics.

        Args:
            coef: Coefficient vector, shape (p,).

        Returns:
            Dictionary with rsquared, rsquared_adj, fstatistic, sigma.
        """
        # Compute fitted values and residuals for this coefficient
        y_valid = self._y[self._valid_mask]
        X_valid = self._X[self._valid_mask]
        fitted = X_valid @ coef
        resid = y_valid - fitted

        # Compute R-squared
        y_mean = np.mean(y_valid)
        ss_tot = np.sum((y_valid - y_mean) ** 2)
        ss_res = np.sum(resid**2)
        rsquared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        rsquared = float(np.clip(rsquared, 0.0, 1.0))

        # Compute adjusted R-squared
        n = self._n
        p = self._p
        rsquared_adj = 1 - (1 - rsquared) * (n - 1) / (n - p) if n > p else 0.0
        rsquared_adj = float(np.clip(rsquared_adj, 0.0, 1.0))

        # Compute F-statistic
        if p > 1 and rsquared < 1.0:
            fstatistic = (rsquared / (p - 1)) / ((1 - rsquared) / (n - p))
        else:
            fstatistic = 0.0

        # Compute sigma
        sigma = np.sqrt(ss_res / self._df_resid) if self._df_resid > 0 else 0.0

        return {
            "rsquared": rsquared,
            "rsquared_adj": rsquared_adj,
            "fstatistic": fstatistic,
            "sigma": float(sigma),
        }

    def _create_ablated_model(self, ablated_formula: str) -> "Self":
        """Create ablated model for CV importance."""
        return type(self)(ablated_formula, data=self._data).fit(
            weights=self._weights_column
        )

    def _simulate_response(self, mu: np.ndarray) -> np.ndarray:
        """Simulate Gaussian response given expected values.

        Adds normally distributed noise with standard deviation sigma.

        Args:
            mu: Expected values (fitted values).

        Returns:
            Simulated response: mu + N(0, sigma).
        """
        epsilon = np.random.randn(len(mu)) * self._sigma
        return mu + epsilon

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def coef_(self) -> np.ndarray:
        """Coefficient estimates as numpy array (sklearn-compatible).

        Returns:
            1D array of shape (p,) containing coefficient estimates,
            where p is the number of model terms (including intercept if present).
            Order matches `params["term"]`.
        """
        self._check_fitted()
        return self._coef

    @property
    def params(self) -> pl.DataFrame:
        """Population-level coefficients as DataFrame.

        Returns:
            DataFrame with columns ["term", "estimate"] containing coefficient
            names and their estimated values.
        """
        self._check_fitted()
        return pl.DataFrame(
            {"term": self._X_names, "estimate": self._get_coef().tolist()}
        )

    @property
    def fitted(self) -> np.ndarray:
        """Fitted values (y_hat) as numpy array."""
        self._check_fitted()
        return self._fitted_values

    @property
    def residuals(self) -> np.ndarray:
        """Response residuals (y - y_hat) as numpy array."""
        self._check_fitted()
        return self._residuals

    @property
    def result_params(self) -> "ResultFit":
        """Coefficient table with estimates, standard errors, and p-values.

        Returns a :class:`~bossanova.results.ResultFit` wrapper with methods:

        - :meth:`~bossanova.results.ResultFit.to_effect_size`: Standardized effect sizes
        - :meth:`~bossanova.results.ResultFit.recompute_ci`: CIs at different level
        - :meth:`~bossanova.results.ResultFit.filter_params`: Filter to specific terms
        - :meth:`~bossanova.results.ResultFit.filter_significant`: Filter by p-value
        - :meth:`~bossanova.results.ResultFit.exclude_intercept`: Remove intercept row

        All standard polars DataFrame operations (filter, select, etc.) also work.

        See Also:
            :class:`~bossanova.results.ResultFit`: Full API documentation.
        """
        from bossanova.results.wrappers import ResultFit

        self._check_fitted()
        return ResultFit(self._result_params, self)

    @property
    def result_model(self) -> pl.DataFrame:
        """Fit statistics table (R-squared, F-statistic, AIC, etc.)."""
        self._check_fitted()
        return self._result_model

    @property
    def vcov(self) -> np.ndarray:
        """Variance-covariance matrix of coefficient estimates.

        Returns:
            2D array of shape (p, p) where p is the number of coefficients.
            Diagonal elements are variances; off-diagonal are covariances.
            Use `np.sqrt(np.diag(model.vcov))` to get standard errors.
        """
        self._check_fitted()
        return self._vcov

    # =========================================================================
    # Methods
    # =========================================================================

    def predict(
        self,
        data: pl.DataFrame | PandasDataFrame,
        units: str = "data",
        pred_int: float | None = None,
        **kwargs,
    ) -> pl.DataFrame:
        """Predict response values for new data.

        This method is for making predictions on new observations.
        For fitted values on training data, use the `.fitted` property.

        Args:
            data: New data for prediction. Must contain all predictor columns.
            units: Units for predictions: "data" (only option for lm).
            pred_int: Prediction interval level (e.g., 0.95 for 95% intervals).
                None (default) returns point predictions only.

        Returns:
            DataFrame with prediction columns (fitted, and optionally lwr, upr).
        """
        self._check_fitted()
        from bossanova.ops.predict import get_valid_rows, init_na_array, fill_valid

        # Convert to polars and build design matrix
        data_pl = coerce_dataframe(data)
        X_pred = self._builder.evaluate_new_data(data_pl)

        # Handle NAs: get valid rows only
        valid_mask, X_valid, n_pred = get_valid_rows(X_pred)

        # Compute predictions for valid rows, fill NaN for invalid
        fitted = init_na_array(n_pred)
        if len(X_valid) > 0:
            fill_valid(fitted, valid_mask, X_valid @ self._coef)

        # Build base result
        result = pl.DataFrame({"fitted": fitted})

        # Add prediction intervals if requested
        if pred_int is not None:
            from bossanova.ops.inference import delta_method_se

            conf_level = self._parse_conf_int(pred_int)

            # Initialize interval bounds with NaN
            lwr = np.full(n_pred, np.nan)
            upr = np.full(n_pred, np.nan)

            # Compute intervals for valid rows only
            if len(X_valid) > 0:
                fitted_valid = fitted[valid_mask]

                # Compute standard errors for prediction interval
                # SE includes residual variance: sqrt(sigma^2 + se_pred^2)
                se_pred = delta_method_se(X_valid, self._vcov)
                se_pred_interval = np.sqrt(self._sigma**2 + se_pred**2)
                t_crit = stats.t.ppf(1 - (1 - conf_level) / 2, df=self._df_resid)

                lwr[valid_mask] = fitted_valid - t_crit * se_pred_interval
                upr[valid_mask] = fitted_valid + t_crit * se_pred_interval

            result = result.with_columns(
                pl.lit(lwr).alias("lwr"),
                pl.lit(upr).alias("upr"),
            )

        return result

    def summary(self, decimals: int = 3) -> None:
        """Print R-style model summary.

        Args:
            decimals: Number of decimal places to display.
        """
        self._check_fitted()

        # Header
        print("\nCall:")
        print(f"lm(formula = {self.formula}, data = <data>)")
        print()

        # Coefficients table
        print("Coefficients:")
        from bossanova.models.display import print_coefficient_table, print_signif_codes

        print_coefficient_table(
            self._result_params, decimals=decimals, inference=self._inference
        )
        # Only show signif codes for asymptotic inference (has p-values)
        if "p_value" in self._result_params.columns:  # type: ignore[union-attr]  # guarded by _check_fitted
            print_signif_codes()

        # Fit statistics (wide format: one row, metrics as columns)
        diag = self._result_model
        print(
            f"Residual standard error: {diag['sigma'].item():.3f} "
            f"on {int(diag['df_resid'].item())} degrees of freedom"
        )
        print(
            f"Multiple R-squared:  {diag['rsquared'].item():.4f},\t"
            f"Adjusted R-squared:  {diag['rsquared_adj'].item():.4f}"
        )
        print(
            f"F-statistic: {diag['fstatistic'].item():.2f} "
            f"on {int(diag['df_model'].item())} and {int(diag['df_resid'].item())} DF,  "
            f"p-value: {diag['fstatistic_pvalue'].item():.3e}"
        )
        print()

    # =========================================================================
    # Resampling Methods (Private - called by infer())
    # =========================================================================

    def _permute(
        self,
        n_perm: int = 999,
        seed: int | None = None,
        alternative: str = "two-sided",
        test_stat: str = "t",
        max_mem: float | None = None,
    ) -> "PermutationResult":
        """Run permutation test on fitted model.

        Uses efficient hat-matrix trick and batched jax.lax.map for 2-4x speedup.

        Args:
            n_perm: Number of permutations.
            seed: Random seed for reproducibility.
            alternative: Alternative hypothesis type: "two-sided", "greater", or "less".
            test_stat: Test statistic to use: "t" (t-statistic), "coef" (raw coefficient),
                or "abs_coef" (absolute coefficient).
            max_mem: Fraction of available system memory to use (0.0-1.0).
                Controls batch size for parallel computation. None defaults
                to 0.5 (50% of available memory).

        Returns:
            PermutationResult: Result with observed stats, null distribution, and p-values.

        Raises:
            RuntimeError: If model is not fitted.

        Examples:
            >>> model = lm("y ~ x", data=df).fit()
            >>> result = model._permute(n_perm=999, seed=42)
            >>> print(result.summary())
            >>> print(result.pvalues)
        """
        from bossanova.ops import get_ops
        from bossanova.resample.lm import lm_permute

        ops = get_ops()
        self._check_fitted()

        # Apply valid_mask to exclude rows with missing values
        mask = self._valid_mask
        return lm_permute(
            X=ops.asarray(self._X[mask]),
            y=ops.asarray(self._y[mask]),
            X_names=self._X_names,
            n_perm=n_perm,
            seed=seed,
            alternative=alternative,
            test_stat=test_stat,
            max_mem=max_mem,
        )

    def _bootstrap(
        self,
        n_boot: int = 999,
        seed: int | None = None,
        boot_type: str = "residual",
        ci_type: str = "bca",
        level: float = 0.95,
        max_mem: float | None = None,
    ) -> "BootstrapResult":
        """Run bootstrap inference on fitted model.

        Uses batched jax.lax.map for 2-4x speedup.

        Args:
            n_boot: Number of bootstrap samples.
            seed: Random seed for reproducibility.
            boot_type: Type of bootstrap:
                - "residual": Resample residuals, add to fitted values (assumes homoscedasticity).
                - "case": Resample (X, y) pairs together (robust to heteroscedasticity).
                - "parametric": Simulate from fitted model (assumes normality).
            ci_type: Type of confidence interval:
                - "bca": BCa (bias-corrected and accelerated) - default, most accurate.
                - "percentile": Percentile bootstrap.
                - "basic": Basic (pivotal) bootstrap.
            level: Confidence level.
            max_mem: Fraction of available system memory to use (0.0-1.0).
                Controls batch size for parallel computation. None defaults
                to 0.5 (50% of available memory).

        Returns:
            BootstrapResult: Result with observed stats, bootstrap samples, and CIs.

        Raises:
            RuntimeError: If model is not fitted.

        Examples:
            >>> model = lm("y ~ x", data=df).fit()
            >>> result = model._bootstrap(n_boot=999, ci_type="bca")
            >>> print(result.summary())
            >>> lower, upper = result.ci
        """
        from bossanova.ops import get_ops
        from bossanova.resample.lm import lm_bootstrap

        ops = get_ops()
        self._check_fitted()

        # Apply valid_mask to exclude rows with missing values
        mask = self._valid_mask
        return lm_bootstrap(
            X=ops.asarray(self._X[mask]),
            y=ops.asarray(self._y[mask]),
            X_names=self._X_names,
            fitted=ops.asarray(self._fitted_values[mask]),
            sigma=float(self._sigma),
            n_boot=n_boot,
            seed=seed,
            boot_type=boot_type,
            ci_type=ci_type,
            level=level,
            max_mem=max_mem,
        )

    def _cv(
        self,
        cv: int | str = 5,
        seed: int | None = None,
        return_predictions: bool = False,
    ) -> "CVResult":
        """Run cross-validation on fitted model.

        Args:
            cv: Cross-validation strategy:
                - int: K-fold with this many splits.
                - "loo": Leave-one-out cross-validation.
            seed: Random seed for k-fold shuffling.
            return_predictions: If True, return out-of-fold predictions.

        Returns:
            CVResult: Result with per-fold metrics (MSE, RMSE, MAE, R2).

        Raises:
            RuntimeError: If model is not fitted.

        Examples:
            >>> model = lm("y ~ x", data=df).fit()
            >>> result = model._cv(cv=5, seed=42)
            >>> print(result.summary())
            >>> print(result.mean_scores)
        """
        from bossanova.ops import get_ops
        from bossanova.resample.lm import lm_cv

        ops = get_ops()
        self._check_fitted()

        # Apply valid_mask to exclude rows with missing values
        mask = self._valid_mask
        return lm_cv(
            X=ops.asarray(self._X[mask]),
            y=ops.asarray(self._y[mask]),
            X_names=self._X_names,
            cv=cv,
            seed=seed,
            return_predictions=return_predictions,
        )

    # =========================================================================
    # Inference Method Overrides (called by BaseModel._infer())
    # =========================================================================

    def _infer_asymp(
        self,
        conf_level: float,
        errors: str = "auto",
    ) -> pl.DataFrame:
        """Compute asymptotic/Wald inference for lm.

        Args:
            conf_level: Confidence level for intervals.
            errors: Error structure assumption:
                - "auto": Standard OLS (default, same as "iid")
                - "iid": Standard OLS (homoscedastic, independent)
                - "hetero": Sandwich HC3 (arbitrary heteroscedasticity)
                - "unequal_var": Welch-style (group-specific variances)
                - "HC0", "HC1", "HC2", "HC3": Specific sandwich estimators

        Returns:
            DataFrame with coefficient table including Wald CIs and t-test p-values.

        Raises:
            ValueError: If errors='unequal_var' but no factors in formula.
        """
        return self._compute_result_params_with_errors(conf_level, errors)

    def _infer_boot(
        self,
        conf_level: float,
        n_boot: int,
        boot_type: str,
        ci_type: str,
        seed: int | None,
        n_jobs: int,
        verbose: bool,
    ) -> pl.DataFrame:
        """Compute bootstrap inference for lm.

        Args:
            conf_level: Confidence level for intervals.
            n_boot: Number of bootstrap samples.
            boot_type: Type of bootstrap ("parametric", "case", "residual").
            ci_type: Type of CI ("percentile", "basic", "bca").
            seed: Random seed.
            n_jobs: Number of parallel jobs (unused, kept for API consistency).
            verbose: Print progress (unused, kept for API consistency).

        Returns:
            DataFrame with coefficient table including bootstrap CIs.
        """
        # Run bootstrap
        boot_result = self._bootstrap(
            n_boot=n_boot,
            seed=seed,
            boot_type=boot_type,
            ci_type=ci_type,
            level=conf_level,
        )

        # Store for power users who want access to raw result
        self._boot_result = boot_result

        # Store in public attribute if save_resamples=True
        if self._save_resamples:
            self.boot_samples_ = boot_result

        # Compute bootstrap CIs for model-level stats
        self._compute_model_stats_boot_ci(boot_result, conf_level)

        # Build result DataFrame
        from bossanova.results.builders import build_boot_result_params
        from bossanova.results.schemas import BootResultFit

        schema = BootResultFit(
            term=self._X_names,
            estimate=self._get_coef().tolist(),
            se=np.array(boot_result.se).tolist(),
            ci_lower=np.array(boot_result.ci_lower).tolist(),
            ci_upper=np.array(boot_result.ci_upper).tolist(),
            n=self._n_valid,
            ci_type=ci_type,
            n_boot=n_boot,
        )

        return build_boot_result_params(schema)

    def _compute_model_stats_boot_ci(
        self, boot_result: "BootstrapResult", conf_level: float
    ) -> None:
        """Compute bootstrap CIs for model-level statistics.

        Updates _result_model with CI columns for rsquared, rsquared_adj,
        fstatistic, and sigma.

        Args:
            boot_result: Bootstrap result with boot_samples array.
            conf_level: Confidence level for intervals.
        """
        # Get bootstrap coefficient samples: shape (n_boot, p)
        boot_samples = np.asarray(boot_result.boot_samples)
        n_boot = boot_samples.shape[0]

        # Compute model stats for each bootstrap sample
        stats_names = ["rsquared", "rsquared_adj", "fstatistic", "sigma"]
        boot_stats = {name: np.zeros(n_boot) for name in stats_names}

        for i in range(n_boot):
            coef_i = boot_samples[i, :]
            stats_i = self._compute_model_stats_from_coef(coef_i)
            for name in stats_names:
                boot_stats[name][i] = stats_i[name]

        # Compute percentile CIs
        alpha = 1 - conf_level
        lower_pct = alpha / 2 * 100
        upper_pct = (1 - alpha / 2) * 100

        ci_columns = {}
        for name in stats_names:
            ci_columns[f"{name}_ci_lower"] = float(
                np.percentile(boot_stats[name], lower_pct)
            )
            ci_columns[f"{name}_ci_upper"] = float(
                np.percentile(boot_stats[name], upper_pct)
            )

        # Update _result_model with CI columns
        for col_name, col_value in ci_columns.items():
            self._result_model = self._result_model.with_columns(
                pl.lit(col_value).alias(col_name)
            )

    def _infer_perm(
        self,
        conf_level: float,
        n_perm: int,
        seed: int | None,
        n_jobs: int,
        verbose: bool,
    ) -> pl.DataFrame:
        """Compute permutation test inference for lm.

        Args:
            conf_level: Confidence level for reference asymptotic CIs.
            n_perm: Number of permutations.
            seed: Random seed.
            n_jobs: Number of parallel jobs (unused, kept for API consistency).
            verbose: Print progress (unused, kept for API consistency).

        Returns:
            DataFrame with coefficient table including permutation p-values.
        """
        # Run permutation test
        perm_result = self._permute(
            n_perm=n_perm,
            seed=seed,
        )

        # Store for power users
        self._perm_result = perm_result

        # Store in public attribute if save_resamples=True
        if self._save_resamples:
            self.perm_samples_ = perm_result

        # Build result DataFrame with permutation p-values
        from bossanova.ops.inference import (
            compute_ci,
            compute_se_from_vcov,
            compute_t_critical,
        )
        from bossanova.results.builders import build_perm_result_params
        from bossanova.results.schemas import PermResultFit

        # Compute asymptotic quantities for reference
        se = compute_se_from_vcov(self._vcov)
        t_stats = self._coef / se
        t_crit = compute_t_critical(conf_level, df=self._df_resid)
        ci_lower, ci_upper = compute_ci(self._coef, se, t_crit)

        schema = PermResultFit(
            term=self._X_names,
            estimate=self._get_coef().tolist(),
            se=se.tolist(),
            statistic=t_stats.tolist(),
            n=self._n_valid,
            p_value=np.array(perm_result.pvalues).tolist(),
            ci_lower=ci_lower.tolist(),
            ci_upper=ci_upper.tolist(),
            n_perm=n_perm,
            test_stat="t",
        )

        return build_perm_result_params(schema)

    def _infer_cv(
        self,
        conf_level: float,
        k: int,
        loo: bool,
        seed: int | None,
        n_jobs: int,
        verbose: bool,
    ) -> pl.DataFrame:
        """Compute cross-validation metrics and predictor importance for lm.

        Runs k-fold CV on the full model, then ablates each predictor to
        compute importance scores (drop in R² when predictor is removed).

        Args:
            conf_level: Confidence level (unused for CV).
            k: Number of folds.
            loo: Use leave-one-out CV.
            seed: Random seed.
            n_jobs: Number of parallel jobs (unused, kept for API consistency).
            verbose: Print progress (unused, kept for API consistency).

        Returns:
            DataFrame with CV metrics (MSE, RMSE, MAE, R2).
        """
        # Determine CV strategy
        cv_strategy: int | str = "loo" if loo else k

        # Run CV on full model
        cv_result = self._cv(
            cv=cv_strategy,
            seed=seed,
        )

        # Store for power users
        self._cv_result = cv_result

        # Store in public attribute if save_resamples=True
        if self._save_resamples:
            self.cv_results_ = cv_result

        # Get mean scores across folds
        mean_scores = cv_result.mean_scores
        full_cv_metric = float(mean_scores[self._cv_metric_name])

        # Compute ablation importance using base class template method
        importance = self._compute_cv_importance(
            full_cv_metric=full_cv_metric,
            cv_strategy=cv_strategy,
            seed=seed,
        )

        # Add importance column to result_params using base class method
        self._add_cv_importance_to_result_params(importance)

        # Build diagnostics DataFrame with CV metrics
        existing_diag = self._compute_result_model()

        # Add CV metrics as additional columns to the wide format
        return existing_diag.with_columns(
            pl.lit(float(mean_scores["mse"])).alias("cv_mse"),
            pl.lit(float(mean_scores["rmse"])).alias("cv_rmse"),
            pl.lit(float(mean_scores["mae"])).alias("cv_mae"),
            pl.lit(float(mean_scores["r2"])).alias("cv_r2"),
            pl.lit(float(k if not loo else self._n)).alias("cv_folds"),
        )
