"""Generalized linear mixed-effects model (GLMM) implementation.

This module provides the `glmer` class for fitting generalized linear mixed-effects
models using PIRLS with BOBYQA optimization, matching lme4's approach.

Examples:
    >>> from bossanova import glmer
    >>> from bossanova.data import load_cbpp
    >>> cbpp = load_cbpp()
    >>> model = glmer("cbind(incidence, size - incidence) ~ period + (1|herd)",
    ...               data=cbpp, family="binomial")
    >>> model.fit()
    >>> print(model.result_params)
"""

from __future__ import annotations

__all__ = ["glmer"]

from typing import TYPE_CHECKING, Any, Literal

import warnings
import numpy as np

# Conditional JAX import for Pyodide compatibility
try:
    import jax.numpy as jnp
except ImportError:
    import numpy as jnp  # type: ignore[no-redef]
import polars as pl
from scipy import stats

from bossanova._backend import _lock_backend
from bossanova._utils import coerce_dataframe

from bossanova.models.base import BaseMixedModel
from bossanova.ops.family import binomial, poisson
from bossanova.ops.lambda_builder import build_lambda_sparse
from bossanova.results.builders import (
    build_glmer_optimizer_diagnostics,
    build_glmer_result_params,
    build_glmer_result_model,
)
from bossanova.results.schemas import (
    GLMerOptimizerDiagnostics,
    GLMerResultFit,
    GLMerResultFitDiagnostics,
)

if TYPE_CHECKING:
    from typing_extensions import Self
    from pandas import DataFrame as PandasDataFrame


class glmer(BaseMixedModel):
    """Generalized linear mixed-effects model with ML estimation.

    Fits GLMMs using Penalized Iteratively Reweighted Least Squares (PIRLS)
    with BOBYQA optimization, matching lme4's implementation.

    Args:
        formula: Model formula in R-style syntax with random effects.
            Examples:
            - "y ~ x + (1|group)" - random intercepts
            - "y ~ x + (1 + x|group)" - correlated random slopes
            - "y ~ x + (1 + x||group)" - uncorrelated random slopes
            - "y ~ x + (1|school/class)" - nested effects
            - "y ~ x + (1|subject) + (1|item)" - crossed effects
        data: Input data as pandas or polars DataFrame.
        family: Distribution family ("binomial" or "poisson").
        link: Link function ("default" for canonical, or specify).
            - binomial: "logit" (default), "probit"
            - poisson: "log" (default)

    Attributes:
        formula: The model formula (read-only).
        data: Input data, augmented after fit.
        designmat: Fixed-effects design matrix as DataFrame.
        is_fitted: Whether model has been fitted.
        family: Family name (read-only).
        link: Link function name (read-only).
        coef_: Fixed effect coefficient estimates as numpy array
            (sklearn-compatible).
        params: Population-level (fixed) coefficients as DataFrame with
            columns [term, estimate].
        varying: Varying effects (group deviations from population) as
            DataFrame with columns [group, level, (Intercept), slope, ...].
        params_group: Group-specific coefficients (params + varying) as
            DataFrame. Each group's coefficients are population + deviation.
        fitted: Fitted values on the response scale.
        vcov: Variance-covariance matrix of fixed effect coefficients.
        varying_var: Random effect variance components as DataFrame.
        result_params: Full fit results including estimates, standard errors,
            confidence intervals, and p-values.
    """

    def __init__(
        self,
        formula: str,
        data: pl.DataFrame | PandasDataFrame,
        family: str = "binomial",
        link: str = "default",
        reorder_terms: bool = True,
        missing: Literal["drop", "fail"] = "drop",
    ):
        """Initialize generalized linear mixed-effects model.

        Args:
            formula: R-style model formula with random effects.
            data: Input data.
            family: Distribution family ("binomial" or "poisson").
                For Gaussian family, use lmer() instead.
            link: Link function. Use "default" for canonical link.
                - binomial: "logit" (default), "probit"
                - poisson: "log" (default)
            reorder_terms: If True (default), reorder random effect terms by
                q = ℓ × p (levels × RE per group) to minimize Cholesky fill-in.
                This is a performance optimization with no statistical impact.
                Set to False for exact reproducibility with other software.
            missing: How to handle missing values ("drop" or "fail").

        Raises:
            ValueError: If formula contains no random effects terms.
            ValueError: If grouping variable not found in data.
            ValueError: If family is "gaussian" (use lmer instead).
            ValueError: If invalid family/link combination.
        """
        # Validate family first (before any other work)
        if family == "gaussian":
            raise ValueError(
                "For Gaussian family, use lmer() instead of glmer().\n\n"
                "glmer() is for non-Gaussian responses:\n"
                "  - 'binomial' - for binary/proportion outcomes\n"
                "  - 'poisson'  - for count outcomes"
            )

        if family not in ("binomial", "poisson"):
            raise ValueError(
                f"Unknown family '{family}'.\n\n"
                "Supported families for glmer:\n"
                "  - 'binomial' - for binary/proportion outcomes\n"
                "  - 'poisson'  - for count outcomes\n\n"
                "For continuous (Gaussian) responses, use lmer() instead."
            )

        # Create family object
        if family == "binomial":
            link_name = "logit" if link == "default" else link
            self._family = binomial(link_name)
        elif family == "poisson":
            link_name = "log" if link == "default" else link
            self._family = poisson(link_name)

        self._family_name = family
        self._link_name = self._family.link_name

        # Call parent (which does || expansion, RE parsing)
        super().__init__(formula, data, reorder_terms, missing=missing)

        # Note: _inference is inherited from BaseModel, no need to initialize here

    def _repr_parts(self) -> list[tuple[str, Any]]:
        """Return (key, value) pairs for repr."""
        parts: list[tuple[str, Any]] = [
            ("formula", self.formula),
            ("family", self.family),
            ("link", self.link),
            ("data", (self._n, self._p)),
            (
                "groups",
                self.ngroups
                if self.is_fitted
                else {g: n for g, n in zip(self._group_names, self._n_groups_list)},
            ),
            ("fitted", self.is_fitted),
        ]
        if self.is_fitted:
            parts.append(("estimation", "PIRLS"))
            parts.append(("inference", self._inference))
        return parts

    def _compute_conditional_loglik(self) -> float:
        """Compute lme4-style conditional log-likelihood.

        This matches lme4's internal aic() function for GLMMs, which returns
        -2 times the conditional log-likelihood. We return the log-likelihood
        (not -2 times it).

        For binomial with weights (grouped binomial):
            Uses full binomial log-likelihood with dbinom formula:
            (wt/m) * [log(choose(m,y)) + y*log(mu) + (m-y)*log(1-mu)]
            where m = weights (trials), y = m * proportion (counts)

        For poisson:
            Uses full Poisson log-likelihood with dpois formula:
            wt * [y*log(mu) - mu - log(y!)]

        Returns:
            Conditional log-likelihood (sum across observations).
        """
        from scipy import special

        if self._family_name == "binomial" and self._weights is not None:
            # lme4's binomial aic() formula:
            # -2 * sum( (wt/m) * dbinom(y, m, mu, log=TRUE) )
            # where dbinom includes log(choose(m,y))
            # Use fit-time y and weights (valid rows only, matching mu length)
            m = self._weights_fit  # number of trials (valid rows)
            y_counts = np.round(m * self._y_fit)  # actual successes

            # Full binomial log-likelihood:
            # log(choose(m, y)) + y*log(mu) + (m-y)*log(1-mu)
            mu_clipped = np.clip(self._mu, 1e-10, 1 - 1e-10)

            ll_obs = (
                special.gammaln(m + 1)
                - special.gammaln(y_counts + 1)
                - special.gammaln(m - y_counts + 1)
                + y_counts * np.log(mu_clipped)
                + (m - y_counts) * np.log(1 - mu_clipped)
            )
            # lme4 uses (wt/m) weighting, but wt = m here
            ll_weighted = (self._weights_fit / m) * ll_obs
            return float(np.sum(ll_weighted))

        elif self._family_name == "poisson":
            # Poisson log-likelihood: y*log(mu) - mu - log(y!)
            # Use fit-time y (valid rows only, matching mu length)
            mu_clipped = np.clip(self._mu, 1e-10, np.inf)
            ll_obs = (
                self._y_fit * np.log(mu_clipped)
                - mu_clipped
                - special.gammaln(self._y_fit + 1)
            )
            if self._weights_fit is not None:
                ll_obs = self._weights_fit * ll_obs
            return float(np.sum(ll_obs))

        else:
            # Fallback to family loglik (for unweighted binomial)
            # Use fit-time y (valid rows only, matching mu length)
            ll_obs = np.asarray(self._family.loglik(self._y_fit, self._mu))
            if self._weights_fit is not None:
                ll_obs = self._weights_fit * ll_obs
            return float(np.sum(ll_obs))

    def _compute_conditional_deviance(self) -> float:
        """Compute sum of unit deviances (lme4 style).

        This matches lme4's deviance() for GLMMs, which returns the sum of
        squared deviance residuals (conditional goodness-of-fit measure).

        Returns:
            Sum of weighted unit deviances.
        """
        # Use fit-time y (valid rows only, matching mu length)
        dev_obs = np.asarray(self._family.deviance(self._y_fit, self._mu))
        if self._weights_fit is not None:
            dev_obs = self._weights_fit * dev_obs
        return float(np.sum(dev_obs))

    def fit(
        self,
        method: Literal["ML"] = "ML",
        max_iter: int = 25,
        tol: float = 1e-8,
        max_outer_iter: int = 10000,
        restart_edge: bool = False,
        boundary_tol: float = 1e-5,
        verbose: bool = False,
        use_hessian: bool = True,
        weights: str | None = None,
    ) -> Self:
        """Fit the generalized linear mixed-effects model.

        Uses two-level optimization:
        1. Outer: BOBYQA optimizes theta (variance parameters)
        2. Inner: PIRLS solves for beta, u at fixed theta

        The likelihood is approximated using the Laplace method (nAGQ=1).
        Computes parameter estimates only. Call `.infer()` after fitting to
        compute standard errors, confidence intervals, and p-values.

        Args:
            method: Estimation method. Only "ML" is supported for GLMMs.
                (GLMMs do not support REML estimation.)
            max_iter: Maximum PIRLS iterations per theta evaluation.
            tol: Convergence tolerance for PIRLS (relative deviance change).
            max_outer_iter: Maximum BOBYQA iterations for theta optimization.
            restart_edge: If True, restart optimization when parameters land
                on boundary with negative gradient. Default False for glmer
                (matches lme4 default for GLMMs).
            boundary_tol: Tolerance for boundary detection. Parameters within
                this distance of their bounds are considered "at boundary".
                Default 1e-5 matches lme4.
            verbose: Print optimization progress.
            use_hessian: If True (default), compute vcov from numerical Hessian
                of the deviance function (matches lme4's default). If False,
                use faster Schur complement-based vcov. Hessian is more accurate
                but slower.
            weights: Column name for observation weights (not yet supported).
                Will raise NotImplementedError if provided.

        Returns:
            Fitted model instance.

        Raises:
            ValueError: If method="REML" (not supported for GLMMs).
            RuntimeError: If optimizer does not converge.
            NotImplementedError: If weights parameter is provided.

        Examples:
            >>> model = glmer("y ~ x + (1|group)", data=df, family="binomial").fit()
            >>> model.infer()  # Wald inference
            >>> model.infer(how="boot", n=999)  # Bootstrap inference
        """
        # Weighted fitting not yet implemented for mixed models
        if weights is not None:
            raise NotImplementedError(
                "Weighted fitting not yet implemented for generalized linear "
                "mixed models (glmer).\n\n"
                "For weighted analysis, consider:\n"
                "  - glm() with weights for generalized linear models\n"
                "  - Track progress: weighted lmer/glmer is planned for a future release"
            )

        # Validate method
        if method != "ML":
            raise ValueError(
                f"GLMMs only support ML estimation, got method='{method}'. "
                "REML is not applicable for generalized linear mixed models."
            )

        # Import fitting infrastructure
        from bossanova.ops.glmer_pirls import (
            fit_glmm_pirls,
            glmm_deviance_objective,
            pirls_sparse,
            _get_theta_lower_bounds,
        )

        # Slice data to valid rows only (excludes rows with missing values)
        X_fit = self._X[self._valid_mask]
        y_fit = self._y[self._valid_mask]
        Z_fit = self._Z[self._valid_mask]  # Sparse matrix row slicing
        weights_fit = None  # Weights not yet supported

        # Store fit-time matrices for inference computations
        self._X_fit = X_fit
        self._Z_fit = Z_fit
        self._y_fit = y_fit
        self._weights_fit = weights_fit

        # Fit the model
        fit_result = fit_glmm_pirls(
            X=X_fit,
            Z=Z_fit,
            y=y_fit,
            family=self._family,
            n_groups_list=self._n_groups_list,
            re_structure=self._re_structure,
            metadata=self._metadata,
            prior_weights=weights_fit,
            max_outer_iter=max_outer_iter,
            pirls_max_iter=max_iter,
            pirls_tol=tol,
            verbose=verbose,
        )

        # Extract theta and prepare for boundary handling
        theta_opt = fit_result["theta"]
        n_theta = len(theta_opt)
        theta_lower = _get_theta_lower_bounds(
            n_theta, self._re_structure, self._metadata
        )
        theta_upper = [np.inf] * n_theta
        restarted = False

        # Create deviance function for restart_edge and boundary check
        def devfun(theta):
            return glmm_deviance_objective(
                theta=theta,
                X=X_fit,
                Z=Z_fit,
                y=y_fit,
                family=self._family,
                n_groups_list=self._n_groups_list,
                re_structure=self._re_structure,
                metadata=self._metadata,
                prior_weights=weights_fit,
                pirls_max_iter=max_iter,
                pirls_tol=tol,
                verbose=False,
            )

        # Restart edge: if parameters landed on boundary with negative gradient,
        # restart optimization to potentially find better solution.
        # Default is False for glmer (matches lme4 behavior for GLMMs)
        if restart_edge:
            from bossanova.optimize import optimize_theta

            optimizer_kwargs = {
                "lower": theta_lower,
                "upper": theta_upper,
                "rhobeg": 2e-3,
                "rhoend": 2e-7,
                "maxfun": max_outer_iter,
                "verbose": verbose,
            }

            theta_opt, _, restarted = self._restart_edge(
                theta=theta_opt,
                lower_bounds=theta_lower,
                devfun=devfun,
                optimizer_fn=optimize_theta,
                optimizer_kwargs=optimizer_kwargs,
                boundary_tol=boundary_tol,
                verbose=verbose,
            )

        # Check boundary: snap near-boundary theta to exact boundary if it
        # improves fit. This is statistically principled (not just numerical):
        # - θ=0 exactly means variance is zero, clear interpretation
        # - θ≈0 is ambiguous for inference (50:50 mixture distribution applies at boundary)
        # Matches lme4's check.boundary() in modular.R
        theta_opt, boundary_adjusted = self._check_boundary(
            theta=theta_opt,
            lower_bounds=theta_lower,
            devfun=devfun,
            boundary_tol=boundary_tol,
        )

        if boundary_adjusted or restarted:
            # Re-run PIRLS at adjusted theta to get correct beta/u/eta/mu
            Lambda = build_lambda_sparse(
                theta_opt, self._n_groups_list, self._re_structure, self._metadata
            )
            pirls_result = pirls_sparse(
                X=X_fit,
                Z=Z_fit,
                Lambda=Lambda,
                y=y_fit,
                family=self._family,
                prior_weights=weights_fit,
                max_iter=max_iter,
                tol=tol,
                verbose=verbose,
            )
            # Update fit_result with new values
            fit_result["theta"] = theta_opt
            fit_result["beta"] = pirls_result["beta"]
            fit_result["u"] = pirls_result["u"]
            fit_result["eta"] = pirls_result["eta"]
            fit_result["mu"] = pirls_result["mu"]
            fit_result["logdet_L"] = pirls_result["logdet_L"]
            fit_result["deviance"] = pirls_result["deviance"]
            if verbose:
                if restarted:
                    print("Restart edge: restarted optimization, re-ran PIRLS")
                if boundary_adjusted:
                    print("Boundary check: adjusted theta, re-ran PIRLS")

        # Store results
        self._theta = fit_result["theta"]
        self._boundary_adjusted = boundary_adjusted
        self._coef = fit_result["beta"]
        self._u = fit_result["u"]
        self._eta = fit_result["eta"]
        self._mu = fit_result["mu"]
        self._logdet_L = fit_result["logdet_L"]

        # Store Laplace objective (what PIRLS optimizes)
        self._laplace_deviance = fit_result["deviance"]

        # Compute proper log-likelihood and deviance (lme4 style)
        # Formula: loglik = Σᵢ family.loglik(yᵢ, μᵢ) * wᵢ - (||u||² + logdet)/2
        cond_loglik = self._compute_conditional_loglik()
        sqrL = np.sum(self._u**2)
        self._loglik = cond_loglik - 0.5 * (sqrL + self._logdet_L)

        # Conditional deviance (lme4 style): sum of unit deviances
        self._deviance = self._compute_conditional_deviance()

        # Compute variance-covariance matrix of beta
        # Two approaches available:
        # 1. Hessian-based (use_hessian=True, default): Numerical Hessian of deviance
        #    at final [theta, beta]. Matches lme4's default behavior.
        # 2. Schur complement (use_hessian=False): Faster, uses final IRLS weights.
        #    Matches lme4's vcov(model, use.hessian=FALSE).

        if use_hessian:
            # Hessian-based vcov (matches lme4 default)
            from bossanova.ops.glmer_pirls import compute_hessian_vcov

            self._vcov, self._hessian_derivs = compute_hessian_vcov(
                theta=self._theta,
                beta=self._coef,
                X=X_fit,
                Z=Z_fit,
                y=y_fit,
                family=self._family,
                n_groups_list=self._n_groups_list,
                re_structure=self._re_structure,
                metadata=self._metadata,
                prior_weights=weights_fit,
                pirls_max_iter=max_iter,
                pirls_tol=tol,
                eta_init=self._eta,  # Use optimal eta as starting point
            )
            self._use_hessian = True
        else:
            # Schur complement-based vcov (faster)
            from bossanova.ops.glmer_pirls import compute_irls_quantities

            working_weights, _ = compute_irls_quantities(y_fit, self._eta, self._family)

            if weights_fit is not None:
                total_weights = weights_fit * working_weights
            else:
                total_weights = working_weights

            # Build Lambda for Schur complement
            Lambda = build_lambda_sparse(
                self._theta, self._n_groups_list, self._re_structure, self._metadata
            )

            # Compute vcov via Schur complement (dispersion=1 for GLMMs)
            self._vcov = np.asarray(
                self._compute_vcov_schur(
                    X=jnp.asarray(X_fit),
                    Z=Z_fit,
                    Lambda=Lambda,
                    W=jnp.asarray(total_weights),
                    sigma2=1.0,
                )
            )
            self._hessian_derivs = None
            self._use_hessian = False

        # Expand fitted values, linear predictor, and residuals to full length
        # (NaN for rows with missing values)
        self._fitted_values = self._expand_to_full_length(self._mu)
        self._linear_predictor = self._expand_to_full_length(self._eta)
        self._residuals = self._expand_to_full_length(y_fit - self._mu)

        # Compute AIC and BIC
        # Number of parameters: p (fixed) + n_theta (variance)
        n_theta = len(self._theta)
        n_params = self._p + n_theta

        self._aic = -2 * self._loglik + 2 * n_params
        self._bic = -2 * self._loglik + np.log(self._n) * n_params

        # Store method
        self._method = method

        # Diagnose convergence issues and generate user-friendly messages
        from bossanova._config import get_singular_tolerance
        from bossanova.ops.convergence import (
            diagnose_convergence,
            format_convergence_warnings,
        )

        sing_tol = get_singular_tolerance()
        # Use per-group structures if available (for crossed/nested), else use main structure
        re_struct = self._metadata.get("re_structures_list")
        if re_struct is None:
            if self._re_structure in ("crossed", "nested"):
                # Default to intercept-only for each group
                re_struct = ["intercept"] * len(self._group_names)
            else:
                re_struct = self._re_structure
        self._convergence_messages = diagnose_convergence(
            theta=self._theta,
            theta_lower=theta_lower,
            group_names=self._group_names,
            random_names=self._random_names,
            re_structure=re_struct,
            sigma=1.0,  # GLMMs have fixed dispersion
            converged=fit_result["converged"],
            boundary_adjusted=self._boundary_adjusted,
            restarted=restarted,
            optimizer_message="",  # glmer doesn't store optimizer message
            singular_tol=sing_tol,
        )

        # Check for singular fit
        singular = any(msg.category == "singular" for msg in self._convergence_messages)

        # Build optimizer diagnostics DataFrame (wide format, one row per theta)
        n_theta = len(self._theta)
        schema = GLMerOptimizerDiagnostics(
            optimizer="bobyqa",
            converged=bool(fit_result["converged"]),
            n_iter=fit_result["n_outer_iter"],
            n_func_evals=fit_result["n_func_evals"],
            final_objective=float(self._deviance),
            pirls_converged=bool(fit_result["pirls_converged"]),
            pirls_n_iter=fit_result["pirls_n_iter"],
            theta_index=list(range(n_theta)),
            theta_final=list(self._theta),
            boundary_adjusted=self._boundary_adjusted,
            restarted=restarted,
            singular=singular,
        )
        self._optimizer_diagnostics = build_glmer_optimizer_diagnostics(schema)

        # Emit warnings if there are any issues
        if self._convergence_messages:
            warning_text = format_convergence_warnings(self._convergence_messages)
            warnings.warn(warning_text, UserWarning)

        # Build ranef DataFrame
        self._build_ranef()

        # Add _orig columns for transformed variables
        self._add_orig_columns()

        # Set fitted flag
        self.is_fitted = True

        # Build result DataFrames (estimates only, no inference)
        self._result_params = self._compute_result_params_none()
        self._inference = None

        # Always compute diagnostics
        self._result_model = self._compute_result_model()

        # Lock backend to prevent switching after fit
        _lock_backend()

        # Track operation for .infer() dispatch
        self._last_operation = "fit"

        return self

    def _compute_wald_inference(self, conf_level: float) -> None:
        """Compute Wald inference using z-distribution.

        Args:
            conf_level: Confidence level for intervals.
        """
        from bossanova.ops.inference import (
            compute_ci,
            compute_se_from_vcov,
            compute_z_critical,
        )

        se = compute_se_from_vcov(self._vcov)
        self._z_stats = self._coef / se
        self._df = np.full(self._p, np.inf)  # Asymptotic
        self._p_values = 2 * (1 - stats.norm.cdf(np.abs(self._z_stats)))

        # Confidence intervals
        z_crit = compute_z_critical(conf_level)
        self._ci_lower, self._ci_upper = compute_ci(self._coef, se, z_crit)

    def _compute_result_params(self, conf_level: float = 0.95) -> pl.DataFrame:
        """Build coefficient table.

        Args:
            conf_level: Confidence level for CIs.

        Returns:
            Coefficient table with schema from GLMerResultFit.
        """
        from bossanova.ops.inference import compute_se_from_vcov

        se = compute_se_from_vcov(self._vcov)

        schema = GLMerResultFit(
            term=self._X_names,
            estimate=self._get_coef().tolist(),
            se=se.tolist(),
            statistic=self._z_stats.tolist(),  # type: ignore[union-attr]
            df=self._df.tolist(),  # type: ignore[union-attr]
            p_value=self._p_values.tolist(),  # type: ignore[union-attr]
            ci_lower=self._ci_lower.tolist(),  # type: ignore[union-attr]
            ci_upper=self._ci_upper.tolist(),  # type: ignore[union-attr]
        )

        return build_glmer_result_params(schema)

    def _compute_result_params_none(self) -> pl.DataFrame:
        """Build coefficient table with estimates only (no inference).

        Returns:
            Coefficient table with NaN for inference columns.
        """
        from bossanova.ops.inference import compute_se_from_vcov

        se = compute_se_from_vcov(self._vcov)
        nan_list = [float("nan")] * len(self._X_names)

        schema = GLMerResultFit(
            term=self._X_names,
            estimate=self._get_coef().tolist(),
            se=se.tolist(),
            statistic=nan_list,
            df=nan_list,
            p_value=nan_list,
            ci_lower=nan_list,
            ci_upper=nan_list,
        )

        return build_glmer_result_params(schema)

    def _compute_result_model(self) -> pl.DataFrame:
        """Build fit statistics table.

        Returns:
            Fit statistics with schema from GLMerResultFitDiagnostics.
        """
        schema = GLMerResultFitDiagnostics(
            nobs=int(self._n),
            df_model=int(self._p - 1),
            df_resid=float(self._n - self._p),
            family=self._family_name,
            link=self._link_name,
            deviance=float(self._deviance),
            objective=float(self._laplace_deviance),
            aic=float(self._aic),
            bic=float(self._bic),
            loglik=float(self._loglik),
        )

        return build_glmer_result_model(schema)

    def _compute_inference(self, conf_level: float) -> None:
        """Compute statistical inference (p-values, confidence intervals).

        For GLMMs, uses Wald inference with z-distribution.

        Args:
            conf_level: Confidence level for intervals.
        """
        self._compute_wald_inference(conf_level)

    def _make_deviance_function(self):
        """Create deviance function for Hessian computation.

        Returns a function that takes combined parameters [theta, beta] and
        returns the Laplace-approximated deviance. This is used for computing
        finite-difference Hessians matching lme4's approach.

        The deviance function:
        1. Extracts theta and beta from combined params
        2. Builds Lambda from theta
        3. Solves for u given fixed (theta, beta) via single weighted PLS
        4. Computes Laplace deviance: cond_deviance + ||u||² + log|L|

        Returns:
            Callable that maps params -> deviance (scalar)

        Note:
            For finite-difference Hessian, we fix both theta and beta, solving
            only for u. This differs from optimization where PIRLS iterates to
            convergence for both beta and u.
        """
        import scipy.sparse as sp
        from bossanova.ops.glmer_pirls import (
            compute_irls_quantities,
            solve_weighted_pls_sparse,
            glmm_deviance,
        )

        # Capture necessary state from fitted model
        X = self._X
        Z = self._Z
        y = self._y
        family = self._family
        n_groups_list = self._n_groups_list
        re_structure = self._re_structure
        metadata = self._metadata
        prior_weights = self._weights
        n_theta = len(self._theta)

        # Convert Z to sparse CSC once
        if not sp.isspmatrix_csc(Z):
            Z_sparse = sp.csc_matrix(Z)
        else:
            Z_sparse = Z

        def deviance_function(params: np.ndarray) -> float:
            """Compute Laplace deviance at given (theta, beta).

            For Hessian computation, we fix theta and beta, then iterate to find
            the conditional mode u|theta,beta. This requires a few PIRLS-like
            iterations to update the working weights and solve for u.

            Args:
                params: Combined parameters [theta, beta], shape (n_theta + p,).

            Returns:
                Laplace deviance (scalar).
            """
            # Extract theta and beta (convert to numpy for scipy.sparse compatibility)
            theta = np.asarray(params[:n_theta])
            beta = np.asarray(params[n_theta:])

            # Build Lambda from theta
            Lambda = build_lambda_sparse(theta, n_groups_list, re_structure, metadata)

            # Pre-compute ZΛ once (constant during inner iterations)
            ZL = Z_sparse @ Lambda

            # Initialize eta from fixed effects only
            eta = X @ beta

            # Do a few PIRLS-like iterations to find u|theta,beta
            # We fix beta but update u and working weights
            max_inner_iter = 10
            tol_inner = 1e-6

            for _ in range(max_inner_iter):
                eta_old = eta.copy()

                # Compute IRLS working weights and response at current eta
                working_weights, working_response = compute_irls_quantities(
                    y, eta, family
                )

                # Combine with prior weights
                if prior_weights is not None:
                    total_weights = prior_weights * working_weights
                else:
                    total_weights = working_weights

                # Solve weighted PLS for u (fixing beta, reuse pre-computed ZL)
                pls_result = solve_weighted_pls_sparse(
                    X=X,
                    Z=Z_sparse,
                    Lambda=Lambda,
                    z=working_response,
                    weights=total_weights,
                    ZL=ZL,
                )

                u = pls_result["u"]
                logdet_L = pls_result["logdet_L"]

                # Update eta with random effects contribution
                eta = X @ beta + ZL.toarray() @ u

                # Check convergence
                if np.max(np.abs(eta - eta_old)) < tol_inner:
                    break

            # Compute mu and deviance
            mu = np.asarray(family.link_inverse(eta))
            sqrL = np.sum(u**2)
            deviance = glmm_deviance(y, mu, family, logdet_L, sqrL, prior_weights)

            return deviance

        return deviance_function

    def _simulate_response(self, mu: np.ndarray) -> np.ndarray:
        """Simulate response given expected values.

        Adds appropriate noise based on family (binomial or poisson).

        Args:
            mu: Expected values (fitted values or predictions).

        Returns:
            Simulated response values.
        """
        if self._family_name == "binomial":
            # Binomial: draw from binomial distribution
            if self._weights is not None:
                # Grouped binomial: mu is proportion, weights is n_trials
                y_sim = np.random.binomial(self._weights.astype(int), mu)
                # Return as proportion
                return y_sim / self._weights
            else:
                # Binary: mu is probability
                return np.random.binomial(1, mu).astype(float)
        elif self._family_name == "poisson":
            # Poisson: draw from poisson distribution
            return np.random.poisson(mu).astype(float)
        else:
            raise ValueError(f"Unknown family: {self._family_name}")

    def _get_inference_df(self) -> float:
        """Get degrees of freedom for inference.

        GLMMs always use z-distribution (asymptotic) for fixed effects,
        regardless of family. This matches lme4's behavior.

        Returns:
            np.inf to indicate z-distribution (asymptotic).
        """
        return np.inf

    # =========================================================================
    # Properties
    # =========================================================================

    def _get_family(self):
        """Get the GLMM family for link transformations.

        Returns:
            Family object with link_inverse and link_deriv methods.
        """
        return self._family

    @property
    def family(self) -> str:
        """Distribution family name."""
        return self._family_name

    @property
    def link(self) -> str:
        """Link function name."""
        return self._link_name

    @property
    def method(self) -> str | None:
        """Estimation method used (always 'ML' for GLMM). None if not fitted."""
        return self._method

    @property
    def linear_predictor(self) -> np.ndarray:
        """Linear predictor (η̂)."""
        self._check_fitted()
        return self._linear_predictor  # type: ignore[return-value]

    @property
    def objective(self) -> float:
        """Laplace objective (optimization criterion).

        This is the value minimized during PIRLS optimization:
        Σ devresid + logdet + ||u||²

        Also known as the "Laplace deviance" in MixedModels.jl terminology.
        Useful for comparing optimization trajectories or debugging convergence.
        """
        self._check_fitted()
        return float(self._laplace_deviance)  # type: ignore[arg-type]

    @property
    def probabilities(self) -> np.ndarray | None:
        """Predicted probabilities for binomial models.

        Returns fitted values on the probability scale (0-1). For binomial GLMMs,
        this is the inverse link applied to linear predictor: P(Y=1|X,Z).

        Equivalent to `.fitted` for binomial models, but with clearer naming.

        Returns:
            Array of predicted probabilities, one per observation.
            None if family is not binomial.

        Examples:
            >>> model = glmer("success ~ treatment + (1|subject)", data=df, family="binomial").fit()
            >>> model.probabilities[:3]
            array([0.32, 0.45, 0.78])  # P(success=1) for first 3 observations
        """
        self._check_fitted()
        if self._family_name != "binomial":
            return None
        return self.fitted

    # =========================================================================
    # Methods
    # =========================================================================

    def predict(
        self,
        data: pl.DataFrame | PandasDataFrame,
        units: str = "data",
        pred_int: float | None = None,
        varying: Literal["include", "exclude"] = "include",
        allow_new_levels: bool = False,
        **kwargs,
    ) -> pl.DataFrame:
        """Predict response values for new data.

        This method is for making predictions on new observations.
        For fitted values on training data, use the `.fitted` property.

        Args:
            data: New data for prediction. Must contain all predictor columns
                and grouping factor columns.
            units: Units for predictions.

                - ``"data"``: Predictions on data scale (probabilities, counts).
                - ``"link"``: Predictions on link scale (log-odds, log counts).
                - ``"probability"``: Alias for "data". Only valid for binomial
                  family models. More explicit name for probability predictions.

            varying: How to handle varying effects.

                - ``"include"``: Use estimated varying effects (default).
                  Uses fitted BLUPs for known grouping levels.
                - ``"exclude"``: Population-level predictions (fixed effects only).

            allow_new_levels: Allow new levels of grouping factors in data.
                If True and varying="include", new levels get varying effect = 0
                (equivalent to population-level prediction for those observations).
                If False (default), raises ValueError on new levels.
            pred_int: Prediction interval level (not yet supported for GLMMs).
                Must be None. Non-None values raise NotImplementedError.

        Returns:
            DataFrame with `fitted` column containing predictions.

        Raises:
            ValueError: If units is not "data", "link", or "probability".
            ValueError: If new grouping levels found and allow_new_levels=False.
            NotImplementedError: If pred_int is requested (not yet supported for GLMMs).
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

        # Check for unsupported prediction interval
        if pred_int is not None:
            raise NotImplementedError(
                "Prediction intervals not yet supported for GLMMs. "
                "Use pred_int=None for point predictions."
            )

        # Convert to polars if pandas
        data_pl = coerce_dataframe(data)

        # Use shared infrastructure for prediction
        X_new, eta_valid = self._predict_newdata(data_pl, varying, allow_new_levels)

        # Handle NAs in new data: find valid rows based on X_new
        n_pred = X_new.shape[0]
        valid_pred = ~np.any(np.isnan(X_new), axis=1)

        # Initialize predictions with NaN
        eta = np.full(n_pred, np.nan)
        eta[valid_pred] = eta_valid[valid_pred]

        # Transform to data scale if requested
        if units == "link":
            fitted = eta
        elif units == "data":
            # Only transform valid rows
            fitted = np.full(n_pred, np.nan)
            if np.any(valid_pred):
                fitted[valid_pred] = np.asarray(
                    self._family.link_inverse(eta[valid_pred])
                )
        else:
            raise ValueError(
                f"units must be 'data', 'link', or 'probability', got '{units}'"
            )

        return pl.DataFrame({"fitted": fitted})

    def summary(self, decimals: int = 3) -> None:
        """Print model summary.

        Displays:
        - Model formula, family, and link
        - Random effects variance components
        - Number of observations and groups
        - Fixed effects coefficient table with z-statistics

        Args:
            decimals: Number of decimal places.
        """
        self._check_fitted()

        # Header
        print("\nGeneralized linear mixed model fit by maximum likelihood (Laplace)")
        print(f"Formula: {self.formula}")
        print(f"Family: {self.family} ({self.link})")
        print()

        # Random effects
        from bossanova.models.display import (
            print_coefficient_table,
            print_random_effects,
            print_signif_codes,
        )

        print_random_effects(self, var_decimals=4)

        # Fixed effects table
        print("Fixed effects:")

        print_coefficient_table(
            self._result_params,
            decimals=decimals,
            stat_label="z value",
            p_label="Pr(>|z|)",
            inference=self._inference,
        )
        # Only show signif codes for asymptotic inference (has p-values)
        if "p_value" in self._result_params.columns:  # type: ignore[union-attr]  # guarded by _check_fitted
            print_signif_codes()

    # =========================================================================
    # Resampling Methods (Private - called by infer())
    # =========================================================================

    def _bootstrap(
        self,
        n_boot: int = 999,
        boot_type: str = "parametric",
        ci_type: str = "percentile",
        level: float = 0.95,
        seed: int | None = None,
        which: str = "fixef",
        verbose: bool = False,
        n_jobs: int = 1,
    ):
        """Run bootstrap inference on fitted model (private implementation).

        Args:
            n_boot: Number of bootstrap samples.
            boot_type: Type of bootstrap ("parametric" or "case").
            ci_type: Confidence interval type ("percentile", "basic", "bca").
            level: Confidence level (e.g., 0.95 for 95% CI).
            seed: Random seed for reproducibility.
            which: Which parameters to bootstrap ("fixef" or "all").
            verbose: If True, show tqdm progress bar.
            n_jobs: Number of parallel jobs.

        Returns:
            BootstrapResult with observed stats, bootstrap samples, and CIs.

        Raises:
            RuntimeError: If model is not fitted.
        """
        self._check_fitted()

        from bossanova.resample.mixed import glmer_bootstrap

        # Only fixed effects are bootstrapped for GLMMs
        # (theta uses profile likelihood CIs)
        if which not in ("fixef", "all"):
            raise ValueError(f"which must be 'fixef' or 'all', got '{which}'")

        # Use fit-time matrices for bootstrap
        return glmer_bootstrap(
            X=self._X_fit,
            Z=self._Z_fit,
            y=self._y_fit,
            X_names=self._X_names,
            theta=self._theta,
            beta=self._coef,
            family=self._family,
            n_groups_list=self._n_groups_list,
            re_structure=self._re_structure,
            metadata=self._metadata,
            weights=self._weights_fit,
            n_boot=n_boot,
            seed=seed,
            boot_type=boot_type,
            ci_type=ci_type,
            level=level,
            max_iter=25,
            tol=1e-8,
            max_outer_iter=10000,
            verbose=verbose,
            n_jobs=n_jobs,
        )

    def jointtest(self, *, verbose: bool = True) -> pl.DataFrame:
        """Compute ANOVA table (Type III chi-square tests).

        Uses Wald chi-square tests for GLMMs.

        Args:
            verbose: If True (default), print a message when auto-fitting
                an unfitted model. Set to False to suppress the message.

        Returns:
            ANOVA table with columns [term, df, Chisq, p_value].
        """
        if not self.is_fitted:
            if verbose:
                print("Model not fitted. Fitting with default parameters...")
            self.fit()

        # Use joint_tests from marginal module
        from bossanova.marginal.joint_tests import joint_tests

        return joint_tests(self)

    def anova(self, *, verbose: bool = True) -> pl.DataFrame:
        """Alias for :meth:`jointtest`."""
        return self.jointtest(verbose=verbose)

    # =========================================================================
    # Inference Method Overrides (called by BaseModel._infer())
    # =========================================================================

    def _infer_asymp(
        self,
        conf_level: float,
        errors: str = "auto",
    ) -> pl.DataFrame:
        """Compute asymptotic/Wald inference for GLMER.

        Args:
            conf_level: Confidence level for intervals.
            errors: Error structure assumption (only 'auto'/'iid' for GLMER).

        Returns:
            DataFrame with coefficient table including Wald CIs and z-test p-values.
        """
        # Non-default errors values are not supported for glmer
        if errors not in ("auto", "iid"):
            raise ValueError(
                f"errors='{errors}' is only supported for lm models, not glmer. "
                "Use errors='auto' or 'iid' for Wald inference."
            )

        self._compute_wald_inference(conf_level)
        return self._compute_result_params(conf_level)

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
        """Compute bootstrap inference for GLMER.

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

        # GLMER only supports "case" or "parametric" bootstrap - default to "parametric"
        if boot_type not in ("case", "parametric"):
            boot_type = "parametric"

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
        # GLMER uses _X_names for fixed effect term names, _coef for estimates
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
        """Permutation not supported for mixed models.

        Raises:
            NotImplementedError: Permutation tests are not supported for mixed models.
        """
        raise NotImplementedError(
            "Permutation tests are not supported for mixed models."
        )

    def _infer_cv(
        self,
        conf_level: float,
        k: int,
        loo: bool,
        seed: int | None,
        n_jobs: int,
        verbose: bool,
    ) -> pl.DataFrame:
        """CV not supported for mixed models.

        Raises:
            NotImplementedError: Cross-validation is not supported for mixed models.
        """
        raise NotImplementedError("Cross-validation is not supported for mixed models.")

    def _infer_satterthwaite(self, conf_level: float) -> pl.DataFrame:
        """Satterthwaite not available for GLMMs.

        Raises:
            NotImplementedError: Satterthwaite approximation is only available
                for linear mixed models (lmer).
        """
        raise NotImplementedError(
            "Satterthwaite approximation is only available for linear mixed models (lmer)."
        )
