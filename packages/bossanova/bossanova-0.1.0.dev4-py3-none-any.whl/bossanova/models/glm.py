"""Generalized linear model (GLM) implementation.

This module provides the `glm` class for fitting generalized linear models using
IRLS (Iteratively Reweighted Least Squares), equivalent to R's `glm()` function.

Examples:
    >>> from bossanova import glm
    >>> model = glm("survived ~ age + fare", data=titanic, family="binomial")
    >>> model.fit()
    >>> print(model.result_params)
"""

from __future__ import annotations

__all__ = ["glm"]

from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import polars as pl
from scipy import stats

from bossanova._backend import _lock_backend
from bossanova._utils import coerce_dataframe
from bossanova.models.base import BaseModel
from bossanova.ops.family import binomial, gaussian, poisson, tdist
from bossanova.ops.predict import fill_valid, get_valid_rows, init_na_array
from bossanova.ops.glm_fit import fit_glm_irls
from bossanova.results.builders import (
    build_glm_optimizer_diagnostics,
    build_glm_result_params,
    build_glm_result_model,
)
from bossanova.results.schemas import (
    GLMOptimizerDiagnostics,
    GLMResultFit,
    GLMResultFitDiagnostics,
)

if TYPE_CHECKING:
    from pandas import DataFrame as PandasDataFrame
    from typing_extensions import Self

    from bossanova.ops.family import Family
    from bossanova.resample.results import BootstrapResult, CVResult, PermutationResult
    from bossanova.results.wrappers import ResultFit


class glm(BaseModel):
    """Generalized linear model with IRLS estimation.

    Args:
        formula: Model formula in R-style syntax (e.g., "y ~ x1 + x2").
        data: Input data as pandas or polars DataFrame.
        family: Distribution family ("gaussian", "binomial", or "poisson").
        link: Link function. Use "default" for canonical link.

    Attributes:
        formula: The model formula.
        data: The input data (converted to polars).
        designmat: Design matrix as DataFrame.
        is_fitted: Whether the model has been fitted.
        family: Family name (read-only).
        link: Link function name (read-only).
        coef_: Coefficient estimates as numpy array (sklearn-compatible).
        params: Population-level coefficients as DataFrame with columns
            [term, estimate].
        fitted: Fitted values on the response scale.
        residuals: Deviance residuals.
        vcov: Variance-covariance matrix of coefficients.
        result_params: Full fit results including estimates, standard errors,
            confidence intervals, and p-values.
    """

    # Valid family/link combinations
    _VALID_FAMILIES = {
        "gaussian": ["identity"],
        "binomial": ["logit", "probit"],
        "poisson": ["log"],
        "tdist": ["identity"],
    }

    def __init__(
        self,
        formula: str,
        data: pl.DataFrame | PandasDataFrame,
        family: str = "gaussian",
        link: str = "default",
        missing: Literal["drop", "fail"] = "drop",
    ):
        """Initialize generalized linear model.

        Args:
            formula: Model formula.
            data: Input data.
            family: Distribution family.
            link: Link function (use "default" for canonical).
            missing: How to handle missing values ("drop" or "fail").
        """
        super().__init__(formula, data, missing=missing)

        # Validate family
        if family not in self._VALID_FAMILIES:
            raise ValueError(
                f"Unknown family '{family}'.\n\n"
                "Supported families:\n"
                "  - 'gaussian' - for continuous outcomes (default)\n"
                "  - 'binomial' - for binary/proportion outcomes\n"
                "  - 'poisson'  - for count outcomes\n"
                "  - 'tdist'    - for robust regression (t-distributed errors)"
            )

        # Determine link (use canonical if "default")
        if link == "default":
            link = self._VALID_FAMILIES[family][0]

        # Validate family/link combination
        if link not in self._VALID_FAMILIES[family]:
            valid_links = self._VALID_FAMILIES[family]
            links_desc = "\n".join(
                f"  - '{lnk}'" + (" (default)" if lnk == valid_links[0] else "")
                for lnk in valid_links
            )
            raise ValueError(
                f"Link function '{link}' is not compatible with the {family} family.\n\n"
                f"Supported links for {family}:\n{links_desc}\n\n"
                "Tip: Use link='default' to automatically select the canonical link."
            )

        # Create Family object
        # For tdist, we defer family creation to fit() since df = n - p
        self._family_name = family  # Store for tdist deferred creation
        if family == "gaussian":
            self._family: Family = gaussian(link)
        elif family == "binomial":
            self._family: Family = binomial(link)
        elif family == "poisson":
            self._family: Family = poisson(link)
        elif family == "tdist":
            # Placeholder: actual family created in fit() with df = n - p
            self._family = None  # type: ignore[assignment]

        # Validate response for specific families
        if family == "poisson":
            # Poisson requires non-negative response values
            if np.any(self._y < 0):
                n_neg = int(np.sum(self._y < 0))
                raise ValueError(
                    f"Poisson models require non-negative response values.\n\n"
                    f'Found {n_neg} negative value(s) in "{self._y_name}".\n\n'
                    "Poisson regression models count data (0, 1, 2, ...).\n"
                    "If your response can be negative, consider:\n"
                    "  - family='gaussian' for continuous outcomes\n"
                    "  - Transforming your data (e.g., shifting to positive)"
                )

        # Initialize weights (will be set in fit() if provided)
        self._weights = None

    def _repr_parts(self) -> list[tuple[str, Any]]:
        """Return (key, value) pairs for repr."""
        parts: list[tuple[str, Any]] = [
            ("formula", self.formula),
            ("family", self.family),
            ("link", self.link),
            ("data", (self._n, self._p)),
            ("fitted", self.is_fitted),
        ]
        if self.is_fitted:
            parts.append(("estimation", "IRLS"))
            parts.append(("inference", self._inference))
        return parts

    @property
    def family(self) -> str:
        """Family name (read-only)."""
        return self._family.name

    @property
    def link(self) -> str:
        """Link function name (read-only)."""
        return self._family.link_name

    @property
    def _cv_metric_name(self) -> str:
        """Metric for CV importance: pseudo_r2 for GLM."""
        return "pseudo_r2"

    def _create_ablated_model(self, ablated_formula: str) -> "Self":
        """Create ablated model with same family."""
        return type(self)(
            ablated_formula, data=self._data, family=self._family.name
        ).fit(weights=self._weights_column)

    def _get_family(self):
        """Get the GLM family for link transformations.

        Returns:
            Family object with link_inverse and link_deriv methods.
        """
        return self._family

    def _get_inference_df(self) -> float:
        """Get degrees of freedom for inference.

        GLM always uses z-distribution (asymptotic normality) for Wald
        inference, regardless of family. This matches R's confint.default()
        behavior.

        Returns:
            np.inf (z-distribution) for all GLM families.
        """
        return np.inf

    def fit(
        self,
        max_iter: int = 25,
        tol: float = 1e-8,
        verbose: bool = False,
        weights: str | None = None,
    ) -> Self:
        """Fit the GLM using IRLS.

        Computes parameter estimates only. Call `.infer()` after fitting to
        compute standard errors, confidence intervals, and p-values.

        Args:
            max_iter: Maximum IRLS iterations.
            tol: Convergence tolerance (relative deviance change).
            verbose: If True, show progress during IRLS.
            weights: Column name for observation weights. If provided, must be
                a column in the data with non-negative values. Zero weights are
                allowed for GLMs.

        Returns:
            Fitted model instance.

        Examples:
            >>> model = glm("y ~ x", data=df, family="binomial").fit()
            >>> model.infer()  # Asymptotic Wald inference
            >>> model.infer(how="boot", n=999)  # Bootstrap inference
            >>> # Weighted GLM
            >>> model = glm("y ~ x", data=df, family="poisson").fit(weights="w")
        """
        # Lock backend to prevent switching after fit
        _lock_backend()

        # Handle weights parameter (column name -> array)
        self._weights_column = weights  # Store column name for ablation
        if weights is not None:
            if weights not in self._data.columns:
                raise ValueError(f"weights column '{weights}' not found in data")
            weights_arr = self._data[weights].to_numpy()
            if np.any(weights_arr < 0):
                raise ValueError("weights must be non-negative")
            self._weights = weights_arr
        else:
            self._weights = None

        # Fit model on valid rows only (excludes rows with missing values)
        X_fit = self._X[self._valid_mask]
        y_fit = self._y[self._valid_mask]
        weights_fit = (
            self._weights[self._valid_mask] if self._weights is not None else None
        )

        # For tdist, create family now that we know n and p
        if self._family_name == "tdist":
            n_valid = int(np.sum(self._valid_mask))
            p = X_fit.shape[1]
            df_resid = n_valid - p
            if df_resid <= 0:
                raise ValueError(
                    f"Not enough observations for t-distribution family. "
                    f"Need n > p, but got n={n_valid}, p={p}."
                )
            self._family = tdist(df=df_resid)

        result = fit_glm_irls(
            y=y_fit,
            X=X_fit,
            family=self._family,
            weights=weights_fit,
            max_iter=max_iter,
            tol=tol,
        )

        # Extract coefficient-level results (not expanded)
        self._coef = result["coef"]
        self._vcov = result["vcov"]
        self._dispersion = result["dispersion"]
        self._deviance = result["deviance"]
        self._null_deviance = result["null_deviance"]
        self._df_resid = result["df_residual"]
        self._aic = result["aic"]
        self._bic = result["bic"]
        self._loglik = result["loglik"]
        self._converged = result["converged"]
        self._n_iter = result["n_iter"]
        self._has_separation = result["has_separation"]
        self._irls_weights = result["irls_weights"]
        self._XtWX_inv = result["XtWX_inv"]

        # Expand fitted values, linear predictor, and residuals to full length
        # (NaN for rows with missing values)
        self._fitted_values = self._expand_to_full_length(result["fitted"])
        self._linear_predictor = self._expand_to_full_length(result["linear_predictor"])
        self._residuals = self._expand_to_full_length(result["residuals"])

        # Compute leverage on valid rows only, then expand
        from bossanova.ops.diagnostics import compute_leverage

        leverage_valid = compute_leverage(
            X_fit, weights=self._irls_weights, XtWX_inv=self._XtWX_inv
        )
        self._leverage = self._expand_to_full_length(leverage_valid)

        # Set fitted flag
        self.is_fitted = True

        # Build result DataFrames (estimates only, no inference)
        self._result_params = self._compute_result_params_none()
        self._inference = None

        # Always compute diagnostics
        self._result_model = self._compute_result_model()
        self._optimizer_diagnostics = self._compute_optimizer_diagnostics(max_iter, tol)

        # Augment data with diagnostic columns
        self._augment_data()

        # Track operation for .infer() dispatch
        self._last_operation = "fit"

        return self

    def _compute_result_params(self, conf_level: float = 0.95) -> pl.DataFrame:
        """Build coefficient table with z-statistics.

        Args:
            conf_level: Confidence level for CIs.

        Returns:
            Coefficient table with schema from GLMResultFit.
        """

        from bossanova.ops.inference import (
            compute_ci,
            compute_se_from_vcov,
            compute_t_critical,
            compute_z_critical,
        )

        # Compute standard errors
        se = compute_se_from_vcov(self._vcov)

        # Compute test statistics (z or t depending on family)
        test_stats = self._coef / se

        # For gaussian family, dispersion is estimated so use t-distribution
        # For other families (binomial, poisson), dispersion is fixed so use z-distribution
        # This matches R's glm() behavior
        if self._family.name == "gaussian":
            # t-distribution with df_resid degrees of freedom
            p_values = 2 * (1 - stats.t.cdf(np.abs(test_stats), df=self._df_resid))
            crit = compute_t_critical(conf_level, df=self._df_resid)
            df_values = [float(self._df_resid)] * len(self._coef)
        else:
            # z-distribution (normal) for fixed dispersion families
            p_values = 2 * (1 - stats.norm.cdf(np.abs(test_stats)))
            crit = compute_z_critical(conf_level)
            df_values = [float("inf")] * len(self._coef)

        ci_lower, ci_upper = compute_ci(self._coef, se, crit)

        # Build schema
        schema = GLMResultFit(
            term=self._X_names,
            estimate=self._get_coef().tolist(),
            se=se.tolist(),
            statistic=test_stats.tolist(),
            df=df_values,
            p_value=p_values.tolist(),
            ci_lower=ci_lower.tolist(),
            ci_upper=ci_upper.tolist(),
        )

        return build_glm_result_params(schema)

    def _compute_result_params_none(self) -> pl.DataFrame:
        """Build coefficient table with estimates only (no inference).

        Returns:
            Coefficient table with NaN for inference columns.
        """
        n_coef = len(self._coef)
        nan_list = [float("nan")] * n_coef

        # Build schema with NaN for inference columns
        schema = GLMResultFit(
            term=self._X_names,
            estimate=self._get_coef().tolist(),
            se=nan_list,
            statistic=nan_list,
            df=nan_list,
            p_value=nan_list,
            ci_lower=nan_list,
            ci_upper=nan_list,
        )

        return build_glm_result_params(schema)

    def _compute_result_model(self) -> pl.DataFrame:
        """Build fit statistics table.

        Returns:
            Fit statistics with schema from GLMResultFitDiagnostics.
        """
        # Compute pseudo R-squared (McFadden)
        if self._null_deviance > 0:
            pseudo_rsquared = 1 - (self._deviance / self._null_deviance)
        else:
            pseudo_rsquared = 0.0

        # Build schema
        schema = GLMResultFitDiagnostics(
            nobs=int(self._n),
            df_model=int(self._p - 1),  # exclude intercept
            df_resid=float(self._df_resid),
            null_deviance=float(self._null_deviance),
            deviance=float(self._deviance),
            dispersion=float(self._dispersion),
            pseudo_rsquared=float(pseudo_rsquared),
            aic=float(self._aic),
            bic=float(self._bic),
            loglik=float(self._loglik),
        )

        return build_glm_result_model(schema)

    def _compute_optimizer_diagnostics(self, max_iter: int, tol: float) -> pl.DataFrame:
        """Build optimizer diagnostics table (wide format, single row).

        Args:
            max_iter: Maximum iterations used.
            tol: Tolerance used.

        Returns:
            Single-row DataFrame with optimizer diagnostics.
        """
        schema = GLMOptimizerDiagnostics(
            optimizer="irls",
            converged=bool(self._converged),
            n_iter=int(self._n_iter),
            tol=float(tol),
            final_objective=float(self._deviance),
            n_func_evals=None,  # Not applicable for IRLS
            has_separation=self._has_separation,
        )

        return build_glm_optimizer_diagnostics(schema)

    def _compute_augment_residuals(self) -> np.ndarray:
        """Compute Pearson residuals for GLM augmentation diagnostics.

        GLM uses Pearson residuals (raw residuals / sqrt(variance)) for
        standardized residual computation, matching R's behavior.

        Returns:
            Pearson residuals for studentized residual computation.
        """
        return self._residuals / np.sqrt(self._family.variance(self._fitted_values))

    def _get_augment_sigma(self) -> float:
        """Get sigma for GLM augmentation diagnostics.

        GLM uses sigma=1.0 for standardization (dispersion already factored in).

        Returns:
            1.0 for GLM standardization.
        """
        return 1.0

    def _simulate_response(self, mu: np.ndarray) -> np.ndarray:
        """Simulate response given expected values based on family.

        Uses numpy's global random state (set by np.random.seed in simulate()).
        Dispatches to family-specific simulation:
        - Gaussian: mu + N(0, sqrt(dispersion))
        - Binomial: Bernoulli(mu)
        - Poisson: Poisson(mu)

        Args:
            mu: Expected values (fitted values on response scale).

        Returns:
            Simulated response values.
        """
        family_name = self._family.name

        if family_name == "gaussian":
            sigma = np.sqrt(self._dispersion)
            return mu + np.random.randn(len(mu)) * sigma
        elif family_name == "binomial":
            return np.random.binomial(1, mu).astype(float)
        elif family_name == "poisson":
            return np.random.poisson(mu).astype(float)
        else:
            raise ValueError(f"Unsupported family for simulation: {family_name}")

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def coef_(self) -> np.ndarray:
        """Coefficient estimates as numpy array (sklearn-compatible).

        Returns:
            1D array of shape (p,) containing coefficient estimates on the link scale,
            where p is the number of model terms (including intercept if present).
            Order matches `params["term"]`.
        """
        self._check_fitted()
        return self._coef  # type: ignore[return-value]

    @property
    def params(self) -> pl.DataFrame:
        """Population-level coefficients as DataFrame.

        Returns:
            DataFrame with columns ["term", "estimate"] containing coefficient
            names and their estimated values (on link scale).
        """
        self._check_fitted()
        return pl.DataFrame(
            {"term": self._X_names, "estimate": self._get_coef().tolist()}
        )  # type: ignore[union-attr]

    @property
    def fitted(self) -> np.ndarray:
        """Fitted values (μ̂) on response scale as numpy array."""
        self._check_fitted()
        return self._fitted_values  # type: ignore[return-value]

    @property
    def residuals(self) -> np.ndarray:
        """Response residuals (y - μ̂) as numpy array."""
        self._check_fitted()
        return self._residuals  # type: ignore[return-value]

    @property
    def result_params(self) -> "ResultFit":
        """Coefficient table with estimates, standard errors, and p-values.

        Returns a :class:`~bossanova.results.ResultFit` wrapper with methods:

        - :meth:`~bossanova.results.ResultFit.to_odds_ratio`: Odds ratio scale (binomial)
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
        return ResultFit(self._result_params, self)  # type: ignore[arg-type]

    @property
    def result_model(self) -> pl.DataFrame:
        """Fit statistics table (deviance, pseudo R-squared, AIC, etc.)."""
        self._check_fitted()
        return self._result_model  # type: ignore[return-value]

    @property
    def vcov(self) -> np.ndarray:
        """Variance-covariance matrix of coefficient estimates.

        Returns:
            2D array of shape (p, p) where p is the number of coefficients.
            Diagonal elements are variances; off-diagonal are covariances.
            Use `np.sqrt(np.diag(model.vcov))` to get standard errors.
        """
        self._check_fitted()
        return self._vcov  # type: ignore[return-value]

    @property
    def probabilities(self) -> np.ndarray | None:
        """Predicted probabilities for binomial models.

        Returns fitted values on the probability scale (0-1). For binomial GLMs,
        this is the inverse link applied to linear predictor: P(Y=1|X).

        Equivalent to `.fitted` for binomial models, but with clearer naming.

        Returns:
            Array of predicted probabilities, one per observation.
            None if family is not binomial.

        Examples:
            >>> model = glm("survived ~ age + fare", data=titanic, family="binomial").fit()
            >>> model.probabilities[:3]
            array([0.32, 0.45, 0.78])  # P(survived=1) for first 3 passengers
        """
        self._check_fitted()
        if self._family.name != "binomial":
            return None
        return self.fitted

    @property
    def optimizer_diagnostics(self) -> pl.DataFrame:
        """Optimizer convergence diagnostics (converged, n_iter, etc.)."""
        self._check_fitted()
        return self._optimizer_diagnostics  # type: ignore[return-value]

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
            units: Units for predictions:

                - ``"data"``: Response scale (μ). For binomial models, this is
                  the probability scale (0-1).
                - ``"link"``: Link function scale (η). For logit, this is log-odds.
                - ``"probability"``: Alias for "data". Only valid for binomial
                  family models (logit, probit, cloglog). More explicit name for
                  probability predictions.

            pred_int: Prediction interval level (e.g., 0.95 for 95% intervals).
                None (default) returns point predictions only.

        Returns:
            DataFrame with prediction columns (fitted, and optionally lwr, upr).
        """
        self._check_fitted()

        # Handle probability alias
        if units == "probability":
            if self._family.name != "binomial":
                raise ValueError(
                    f"units='probability' only valid for binomial family, "
                    f"got '{self._family.name}'. Use units='data' instead."
                )
            units = "data"

        # Validate units
        if units not in ["data", "link"]:
            raise ValueError(
                f"units must be 'data', 'link', or 'probability', got '{units}'"
            )

        # Convert to polars if pandas
        data_pl = coerce_dataframe(data)

        # Use evaluate_new_data() to preserve transform parameters
        X_pred = self._builder.evaluate_new_data(data_pl)

        # Handle NAs: get valid rows only
        valid_mask, X_valid, n_pred = get_valid_rows(X_pred)

        # Initialize predictions with NaN
        eta = init_na_array(n_pred)
        mu = init_na_array(n_pred)

        # Compute predictions for valid rows only
        if len(X_valid) > 0:
            eta_valid = X_valid @ self._coef
            mu_valid = np.asarray(self._family.link_inverse(eta_valid))
            fill_valid(eta, valid_mask, eta_valid)
            fill_valid(mu, valid_mask, mu_valid)

        # Build base result
        if units == "data":
            result = pl.DataFrame({"fitted": mu})
        else:  # units == "link"
            result = pl.DataFrame({"fitted": eta})

        # Add prediction intervals if requested
        if pred_int is not None:
            from bossanova.ops.inference import delta_method_se

            conf_level = self._parse_conf_int(pred_int)

            # Initialize interval bounds with NaN
            lwr = init_na_array(n_pred)
            upr = init_na_array(n_pred)

            # Compute intervals for valid rows only
            if len(X_valid) > 0:
                eta_valid = eta[valid_mask]

                # Compute standard errors on link scale
                se_eta = delta_method_se(X_valid, self._vcov)

                # Interval on link scale
                z_crit = stats.norm.ppf(1 - (1 - conf_level) / 2)
                eta_lower = eta_valid - z_crit * se_eta
                eta_upper = eta_valid + z_crit * se_eta

                if units == "link":
                    fill_valid(lwr, valid_mask, eta_lower)
                    fill_valid(upr, valid_mask, eta_upper)
                else:  # units == "data"
                    # Transform intervals to response scale
                    fill_valid(
                        lwr,
                        valid_mask,
                        np.asarray(self._family.link_inverse(eta_lower)),
                    )
                    fill_valid(
                        upr,
                        valid_mask,
                        np.asarray(self._family.link_inverse(eta_upper)),
                    )

            result = result.with_columns(
                pl.Series("lwr", lwr),
                pl.Series("upr", upr),
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
        print(
            f"glm(formula = {self.formula}, data = <data>, "
            f"family = {self.family}(link = {self.link}))"
        )
        print()

        # Coefficients table
        print("Coefficients:")
        from bossanova.models.display import print_coefficient_table, print_signif_codes

        # Use t-value for gaussian, z-value otherwise (matches R)
        if self._family.name == "gaussian":
            stat_label, p_label = "t value", "Pr(>|t|)"
        else:
            stat_label, p_label = "z value", "Pr(>|z|)"

        print_coefficient_table(
            self._result_params,
            decimals=decimals,
            stat_label=stat_label,
            p_label=p_label,
            inference=self._inference,
        )
        # Only show signif codes for asymptotic inference (has p-values)
        if "p_value" in self._result_params.columns:  # type: ignore[union-attr]  # guarded by _check_fitted
            print_signif_codes()

        # Fit statistics (wide format: one row, metrics as columns)
        diag = self._result_model
        print(
            f"Null deviance: {diag['null_deviance'].item():.2f} "
            f"on {int(self._n - 1)} degrees of freedom"
        )
        print(
            f"Residual deviance: {diag['deviance'].item():.2f} "
            f"on {int(diag['df_resid'].item())} degrees of freedom"
        )
        print(f"AIC: {diag['aic'].item():.2f}")
        print()
        print(f"Pseudo R-squared (McFadden): {diag['pseudo_rsquared'].item():.3f}")
        print()

    # confint() inherited from BaseModel - uses _get_inference_df() for dispatch

    # =========================================================================
    # Resampling Methods (Private - called by infer())
    # =========================================================================

    def _bootstrap(
        self,
        n_boot: int = 999,
        seed: int | None = None,
        boot_type: str = "case",
        ci_type: str = "percentile",
        level: float = 0.95,
        max_iter: int = 25,
        tol: float = 1e-8,
        verbose: bool = False,
        n_jobs: int = 1,
    ) -> "BootstrapResult":
        """Run bootstrap inference on fitted model.

        Args:
            n_boot: Number of bootstrap samples.
            seed: Random seed for reproducibility.
            boot_type: Type of bootstrap:
                - "case": Resample (X, y) pairs (robust, recommended).
                - "parametric": Simulate from fitted model.
            ci_type: Confidence interval type:
                - "percentile": Simple percentile method.
                - "basic": Basic pivotal method.
                - "bca": Bias-corrected accelerated (most accurate, slowest).
            level: Confidence level (e.g., 0.95 for 95% CI).
            max_iter: Maximum IRLS iterations for each refit.
            tol: Convergence tolerance for IRLS.
            verbose: If True, show tqdm progress bar.
            n_jobs: Number of parallel jobs.

        Returns:
            BootstrapResult with observed stats, bootstrap samples, and CIs.

        Raises:
            RuntimeError: If model is not fitted.
        """
        self._check_fitted()

        from bossanova.resample.glm import glm_bootstrap

        # Apply valid_mask to exclude rows with missing values
        # This ensures bootstrap operates on the same data used for fitting
        mask = self._valid_mask
        return glm_bootstrap(
            X=self._X[mask],
            y=self._y[mask],
            X_names=self._X_names,
            family=self._family,
            fitted=self._fitted_values[mask],
            dispersion=self._dispersion,
            weights=self._weights[mask] if self._weights is not None else None,
            n_boot=n_boot,
            seed=seed,
            boot_type=boot_type,
            ci_type=ci_type,
            level=level,
            max_iter=max_iter,
            tol=tol,
            verbose=verbose,
            n_jobs=n_jobs,
        )

    def _permute(
        self,
        n_perm: int = 999,
        seed: int | None = None,
        alternative: str = "two-sided",
        test_stat: str = "coef",
        max_iter: int = 25,
        tol: float = 1e-8,
    ) -> "PermutationResult":
        """Run permutation test on fitted model.

        Args:
            n_perm: Number of permutations.
            seed: Random seed for reproducibility.
            alternative: Alternative hypothesis:
                - "two-sided": |T| >= |T_obs|
                - "greater": T >= T_obs
                - "less": T <= T_obs
            test_stat: Test statistic to use:
                - "coef": Raw coefficient estimates.
                - "wald": Wald z-statistic (coef / SE).
                - "deviance": Model deviance (overall fit).
            max_iter: Maximum IRLS iterations for each refit.
            tol: Convergence tolerance for IRLS.

        Returns:
            PermutationResult with observed stats, null distribution, and p-values.

        Raises:
            RuntimeError: If model is not fitted.
        """
        self._check_fitted()

        from bossanova.resample.glm import glm_permute

        # Apply valid_mask to exclude rows with missing values
        mask = self._valid_mask
        return glm_permute(
            X=self._X[mask],
            y=self._y[mask],
            X_names=self._X_names,
            family=self._family,
            weights=self._weights[mask] if self._weights is not None else None,
            n_perm=n_perm,
            seed=seed,
            alternative=alternative,
            test_stat=test_stat,
            max_iter=max_iter,
            tol=tol,
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
            CVResult with per-fold metrics (MSE, RMSE, MAE, deviance, pseudo_r2).

        Raises:
            RuntimeError: If model is not fitted.
        """
        self._check_fitted()

        from bossanova.resample.glm import glm_cv

        # Apply valid_mask to exclude rows with missing values
        mask = self._valid_mask
        return glm_cv(
            X=np.asarray(self._X[mask]),
            y=np.asarray(self._y[mask]),
            X_names=self._X_names,
            family=self._family,
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
        """Compute asymptotic/Wald inference for GLM.

        Args:
            conf_level: Confidence level for intervals.
            errors: Error structure assumption:
                - "auto"/"iid": Standard GLM inference (uses variance function)
                - "hetero": Sandwich estimator (robust to variance misspecification)

        Returns:
            DataFrame with coefficient table including Wald CIs and z/t-test p-values.
        """
        if errors == "unequal_var":
            raise ValueError(
                "errors='unequal_var' is not applicable to GLM.\n\n"
                "GLM already handles group-specific variances through the variance "
                "function (e.g., μ(1-μ) for binomial). Unlike linear models where "
                "Welch's approach corrects for unequal group variances, GLM builds "
                "this into the likelihood.\n\n"
                "If you suspect the variance function is misspecified (e.g., "
                "overdispersion), use errors='hetero' for sandwich standard errors."
            )

        if errors in ("auto", "iid"):
            return self._compute_result_params(conf_level)

        if errors in ("hetero", "HC0", "HC1"):
            return self._compute_result_params_robust(conf_level, errors)

        raise ValueError(
            f"Unknown errors type for GLM: {errors!r}. "
            "Use 'auto', 'iid', 'hetero', 'HC0', or 'HC1'."
        )

    def _compute_result_params_robust(
        self, conf_level: float, errors: str
    ) -> pl.DataFrame:
        """Compute coefficient table with sandwich (robust) standard errors.

        Args:
            conf_level: Confidence level for CIs.
            errors: "hetero", "HC0", or "HC1".

        Returns:
            DataFrame with robust inference.
        """
        from scipy import stats as scipy_stats

        from bossanova.stats.sandwich import compute_glm_hc_vcov

        # Determine HC type
        hc_type = "HC0" if errors == "hetero" else errors

        # Get valid data
        X_valid = self._X[self._valid_mask]
        resid_valid = self._residuals[self._valid_mask]
        weights_valid = self._irls_weights[self._valid_mask]

        # Compute sandwich vcov
        vcov_robust = compute_glm_hc_vcov(
            X_valid, resid_valid, weights_valid, self._XtWX_inv, hc_type=hc_type
        )

        # Compute SEs and test statistics
        se = np.sqrt(np.diag(vcov_robust))
        test_stats = self._coef / se

        # Use z-distribution for GLM (except Gaussian which uses t)
        if self._family.name == "gaussian":
            df_values = [float(self._df_resid)] * len(self._coef)
            crit = scipy_stats.t.ppf((1 + conf_level) / 2, self._df_resid)
            p_values = 2 * (1 - scipy_stats.t.cdf(np.abs(test_stats), self._df_resid))
        else:
            df_values = [float("inf")] * len(self._coef)
            crit = scipy_stats.norm.ppf((1 + conf_level) / 2)
            p_values = 2 * (1 - scipy_stats.norm.cdf(np.abs(test_stats)))

        ci_lower = self._coef - crit * se
        ci_upper = self._coef + crit * se

        schema = GLMResultFit(
            term=self._X_names,
            estimate=self._get_coef().tolist(),
            se=se.tolist(),
            statistic=test_stats.tolist(),
            df=df_values,
            p_value=p_values.tolist(),
            ci_lower=ci_lower.tolist(),
            ci_upper=ci_upper.tolist(),
        )

        return build_glm_result_params(schema)

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
        """Compute bootstrap inference for GLM.

        Args:
            conf_level: Confidence level for intervals.
            n_boot: Number of bootstrap samples.
            boot_type: Type of bootstrap ("parametric", "case").
            ci_type: Type of CI ("percentile", "basic", "bca").
            seed: Random seed.
            n_jobs: Number of parallel jobs.
            verbose: Print progress.

        Returns:
            DataFrame with coefficient table including bootstrap CIs.
        """
        from bossanova.results.builders import build_boot_result_params
        from bossanova.results.schemas import BootResultFit

        # GLM only supports "case" or "parametric" bootstrap - default to "case"
        if boot_type not in ("case", "parametric"):
            boot_type = "case"

        # Run bootstrap
        boot_result = self._bootstrap(
            n_boot=n_boot,
            seed=seed,
            boot_type=boot_type,
            ci_type=ci_type,
            level=conf_level,
            verbose=verbose,
            n_jobs=n_jobs,
        )

        # Store for power users who want access to raw result
        self._boot_result = boot_result

        # Store in public attribute if save_resamples=True
        if self._save_resamples:
            self.boot_samples_ = boot_result

        # Build result DataFrame
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

    def _infer_perm(
        self,
        conf_level: float,
        n_perm: int,
        seed: int | None,
        n_jobs: int,
        verbose: bool,
    ) -> pl.DataFrame:
        """Compute permutation test inference for GLM.

        Args:
            conf_level: Confidence level for reference asymptotic CIs.
            n_perm: Number of permutations.
            seed: Random seed.
            n_jobs: Number of parallel jobs (unused, kept for API consistency).
            verbose: Print progress (unused, kept for API consistency).

        Returns:
            DataFrame with coefficient table including permutation p-values.
        """
        from bossanova.ops.inference import (
            compute_ci,
            compute_se_from_vcov,
            compute_t_critical,
            compute_z_critical,
        )
        from bossanova.results.builders import build_perm_result_params
        from bossanova.results.schemas import PermResultFit

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

        # Compute asymptotic quantities for reference
        se = compute_se_from_vcov(self._vcov)
        test_stats = self._coef / se

        # For gaussian family, use t-distribution; otherwise use z-distribution
        if self._family.name == "gaussian":
            crit = compute_t_critical(conf_level, df=self._df_resid)
        else:
            crit = compute_z_critical(conf_level)

        ci_lower, ci_upper = compute_ci(self._coef, se, crit)

        schema = PermResultFit(
            term=self._X_names,
            estimate=self._get_coef().tolist(),
            se=se.tolist(),
            statistic=test_stats.tolist(),
            n=self._n_valid,
            p_value=np.array(perm_result.pvalues).tolist(),
            ci_lower=ci_lower.tolist(),
            ci_upper=ci_upper.tolist(),
            n_perm=n_perm,
            test_stat="coef",
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
        """Compute cross-validation metrics and predictor importance for GLM.

        Runs k-fold CV on the full model, then ablates each predictor to
        compute importance scores (drop in pseudo-R² when predictor is removed).

        Args:
            conf_level: Confidence level (unused for CV).
            k: Number of folds.
            loo: Use leave-one-out CV.
            seed: Random seed.
            n_jobs: Number of parallel jobs (unused, kept for API consistency).
            verbose: Print progress (unused, kept for API consistency).

        Returns:
            DataFrame with CV metrics (MSE, RMSE, MAE, deviance, pseudo_r2).
        """
        # Determine CV strategy
        cv_strategy: int | str = "loo" if loo else k

        # Run CV
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

        # Get existing diagnostics (wide format: one row, metrics as columns)
        existing_diag = self._compute_result_model()

        # Add CV metrics as additional columns to the wide format
        return existing_diag.with_columns(
            pl.lit(float(mean_scores.get("mse", float("nan")))).alias("cv_mse"),
            pl.lit(float(mean_scores.get("rmse", float("nan")))).alias("cv_rmse"),
            pl.lit(float(mean_scores.get("mae", float("nan")))).alias("cv_mae"),
            pl.lit(float(mean_scores.get("deviance", float("nan")))).alias(
                "cv_deviance"
            ),
            pl.lit(float(mean_scores.get("pseudo_r2", float("nan")))).alias(
                "cv_pseudo_r2"
            ),
            pl.lit(float(k if not loo else self._n)).alias("cv_folds"),
        )
