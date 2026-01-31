"""Linear mixed-effects model (LMM) implementation.

This module provides the `lmer` class for fitting linear mixed-effects models using
Penalized Least Squares (PLS) with BOBYQA optimization, matching lme4's approach.

Examples:
    >>> from bossanova import lmer
    >>> from bossanova.data import load_sleepstudy
    >>> sleepstudy = load_sleepstudy()
    >>> model = lmer("Reaction ~ Days + (Days|Subject)", data=sleepstudy)
    >>> model.fit()
    >>> print(model.result_params)
"""

from __future__ import annotations

__all__ = ["lmer"]

from typing import TYPE_CHECKING, Any, Literal

import warnings
import numpy as np
import polars as pl
import scipy.sparse as sp
from scipy import stats

from bossanova._backend import _lock_backend
from bossanova._utils import coerce_dataframe
from bossanova.models.base import BaseMixedModel
from bossanova.ops.sparse_solver import sparse_cholesky
from bossanova.results.builders import (
    build_lmer_optimizer_diagnostics,
    build_lmer_result_params,
    build_lmer_result_model,
)
from bossanova.results.schemas import (
    LMerOptimizerDiagnostics,
    LMerResultFit,
    LMerResultFitDiagnostics,
)

if TYPE_CHECKING:
    from typing_extensions import Self
    from pandas import DataFrame as PandasDataFrame


class lmer(BaseMixedModel):
    """Linear mixed-effects model with REML/ML estimation.

    Fits linear mixed-effects models using the Penalized Least Squares (PLS)
    algorithm with BOBYQA optimization, matching lme4's implementation.

    Args:
        formula: Model formula in R-style syntax with random effects.
            Examples:
            - "y ~ x + (1|group)" - random intercepts
            - "y ~ x + (1 + x|group)" - correlated random slopes
            - "y ~ x + (1 + x||group)" - uncorrelated random slopes
            - "y ~ x + (1|school/class)" - nested effects
            - "y ~ x + (1|subject) + (1|item)" - crossed effects
        data: Input data as pandas or polars DataFrame.

    Attributes:
        formula: The model formula (read-only).
        data: Input data, augmented after fit.
        designmat: Fixed-effects design matrix as DataFrame.
        is_fitted: Whether model has been fitted.
        coef_: Fixed effect coefficient estimates as numpy array
            (sklearn-compatible).
        params: Population-level (fixed) coefficients as DataFrame with
            columns [term, estimate].
        varying: Varying effects (group deviations from population) as
            DataFrame with columns [group, level, (Intercept), slope, ...].
        params_group: Group-specific coefficients (params + varying) as
            DataFrame. Each group's coefficients are population + deviation.
        fitted: Fitted values (predicted values for training data).
        residuals: Residuals (observed - fitted).
        vcov: Variance-covariance matrix of fixed effect coefficients.
        varying_var: Random effect variance components as DataFrame.
        result_params: Full fit results including estimates, standard errors,
            confidence intervals, and p-values.
    """

    def __init__(
        self,
        formula: str,
        data: pl.DataFrame | PandasDataFrame,
        reorder_terms: bool = True,
        missing: Literal["drop", "fail"] = "drop",
    ):
        """Initialize linear mixed-effects model.

        Args:
            formula: R-style model formula with random effects.
            data: Input data.
            reorder_terms: If True (default), reorder random effect terms by
                q = ℓ × p (levels × RE per group) to minimize Cholesky fill-in.
                This is a performance optimization with no statistical impact.
                Set to False for exact reproducibility with other software.
            missing: How to handle missing values ("drop" or "fail").

        Raises:
            ValueError: If formula contains no random effects terms.
            ValueError: If grouping variable not found in data.
        """
        super().__init__(formula, data, reorder_terms, missing=missing)

        # Store estimation method (set by fit())
        self._method: str | None = None
        # Note: _inference is initialized in BaseModel.__init__()

    def _repr_parts(self) -> list[tuple[str, Any]]:
        """Return (key, value) pairs for repr."""
        parts: list[tuple[str, Any]] = [
            ("formula", self.formula),
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
            parts.append(("estimation", self._method))
            parts.append(("inference", self._inference))
        return parts

    def fit(
        self,
        method: Literal["REML", "ML"] = "REML",
        max_iter: int = 10000,
        tol: float = 1e-8,
        restart_edge: bool = True,
        boundary_tol: float = 1e-5,
        verbose: bool = False,
        weights: str | None = None,
    ) -> Self:
        """Fit the linear mixed-effects model.

        Uses Penalized Least Squares (PLS) with BOBYQA optimization,
        matching lme4's fitting algorithm. Computes parameter estimates only.
        Call `.infer()` after fitting to compute standard errors, confidence
        intervals, and p-values.

        Args:
            method: Estimation method.
                - "REML": Restricted maximum likelihood (default, less biased).
                - "ML": Maximum likelihood (for model comparison via LRT).
            max_iter: Maximum optimizer iterations. Default 10000.
            tol: Convergence tolerance (absolute). Matches lme4's ftol_abs/xtol_abs.
            restart_edge: If True (default), restart optimization when parameters
                land on boundary with negative gradient. Matches lme4 default
                for lmer. Can help escape suboptimal boundary solutions.
            boundary_tol: Tolerance for boundary detection. Parameters within
                this distance of their bounds are considered "at boundary" for
                restart_edge and check_boundary logic. Default 1e-5 matches lme4.
            verbose: Print optimization progress.
            weights: Column name for observation weights (not yet supported).
                Will raise NotImplementedError if provided.

        Returns:
            Fitted model instance.

        Raises:
            RuntimeError: If optimizer does not converge.
            NotImplementedError: If weights parameter is provided.

        Examples:
            >>> model = lmer("y ~ x + (1|group)", data=df).fit()
            >>> model.infer()  # Satterthwaite inference (default)
            >>> model.infer(how="boot", n=999)  # Bootstrap inference
        """
        # Weighted fitting not yet implemented for mixed models
        if weights is not None:
            raise NotImplementedError(
                "Weighted fitting not yet implemented for linear mixed models (lmer).\n\n"
                "For weighted analysis, consider:\n"
                "  - glm() with weights for generalized linear models\n"
                "  - lm() with weights for weighted least squares\n"
                "  - Track progress: weighted lmer/glmer is planned for a future release"
            )

        # Lock backend to prevent switching after fit
        _lock_backend()

        # Validate method parameter early (before optimizer callback)
        # Raising inside PDFO's Fortran callback causes fatal crash
        if method not in ("REML", "ML"):
            raise ValueError(
                f"Unknown estimation method: '{method}'\n\n"
                "Supported methods:\n"
                "  - 'REML' (default) - Restricted maximum likelihood\n"
                "                       Better variance estimates, use for most analyses\n"
                "  - 'ML'             - Maximum likelihood\n"
                "                       Required for comparing models with different fixed effects"
            )

        # Slice data to valid rows only (excludes rows with missing values)
        X_fit = self._X[self._valid_mask]
        y_fit = self._y[self._valid_mask]
        Z_fit = self._Z[self._valid_mask]  # Sparse matrix row slicing
        weights_fit = None  # Weights not yet supported

        # Slice group_ids to valid rows for moment initialization
        group_ids_fit = [ids[self._valid_mask] for ids in self._group_ids_list]

        # Store fit-time matrices for inference computations
        self._X_fit = X_fit
        self._Z_fit = Z_fit
        self._y_fit = y_fit
        self._weights_fit = weights_fit

        # Initialize theta
        from bossanova.ops.initialization import compute_moment_init

        # Slice X_re to valid rows to match group_ids_fit
        # X_re can be a numpy array or a list of arrays (for diagonal/uncorrelated models)
        if self._X_re is None:
            X_re_fit = None
        elif isinstance(self._X_re, list):
            X_re_fit = [arr[self._valid_mask] for arr in self._X_re]
        else:
            X_re_fit = self._X_re[self._valid_mask]

        theta_init = compute_moment_init(
            X=X_fit,
            Z=Z_fit,
            y=y_fit,
            group_ids_list=group_ids_fit,
            n_groups_list=self._n_groups_list,
            re_structure=self._re_structure,
            X_re=X_re_fit,
            metadata=self._metadata,
        )

        # Build Lambda template for efficient repeated updates during optimization
        from bossanova.ops.lambda_builder import build_lambda_template
        from bossanova.ops.lmer_core import (
            lmm_deviance_sparse,
            compute_pls_invariants,
        )

        # Try to build template; fall back to None if structure not supported
        try:
            lambda_template = build_lambda_template(
                self._n_groups_list, self._re_structure, self._metadata
            )
        except NotImplementedError:
            lambda_template = None

        # Pre-compute invariants (X'X, X'y) before optimization loop
        # These don't depend on theta, so computing them once saves work
        pls_invariants = compute_pls_invariants(X_fit, y_fit)

        def deviance_fn(theta):
            return lmm_deviance_sparse(
                theta=theta,
                X=X_fit,
                Z=Z_fit,
                y=y_fit,
                n_groups_list=self._n_groups_list,
                re_structure=self._re_structure,
                method=method,
                lambda_template=lambda_template,
                pls_invariants=pls_invariants,
                metadata=self._metadata,
            )

        # Set bounds for theta
        # Diagonal elements >= 0, off-diagonal unbounded
        n_theta = len(theta_init)
        lower_bounds = self._get_theta_lower_bounds(n_theta)
        upper_bounds = [np.inf] * n_theta

        # Optimize with BOBYQA via PDFO
        from bossanova.optimize import optimize_theta

        if verbose:
            print(f"Optimizing {n_theta} variance parameters...")

        # Match lme4's BOBYQA configuration (lme4/R/lmer.R:2662-2665)
        # Stage 1 uses rhobeg=2e-3 (0.002), rhoend=2e-7
        result = optimize_theta(
            objective=deviance_fn,
            theta0=theta_init,
            lower=lower_bounds,
            upper=upper_bounds,
            rhobeg=2e-3,  # lme4 Stage 1 default
            rhoend=2e-7,  # lme4 default
            maxfun=max_iter,
            verbose=verbose,
        )

        theta_opt = result["theta"]
        final_deviance = result["fun"]
        restarted = False

        # Restart edge: if parameters landed on boundary with negative gradient,
        # restart optimization to potentially find better solution.
        # Matches lme4's restart_edge logic in modular.R:610-644
        if restart_edge:
            # Build optimizer kwargs for potential restart
            optimizer_kwargs = {
                "lower": lower_bounds,
                "upper": upper_bounds,
                "rhobeg": 2e-3,
                "rhoend": 2e-7,
                "maxfun": max_iter,
                "verbose": verbose,
            }

            theta_opt, final_deviance, restarted = self._restart_edge(
                theta=theta_opt,
                lower_bounds=lower_bounds,
                devfun=deviance_fn,
                optimizer_fn=optimize_theta,
                optimizer_kwargs=optimizer_kwargs,
                boundary_tol=boundary_tol,
                verbose=verbose,
            )

        # Check boundary: snap near-boundary parameters to exact boundary if it
        # improves fit. This is statistically principled (not just numerical):
        # - θ=0 exactly has clear meaning (variance is zero, remove RE term)
        # - θ≈0 is ambiguous for inference
        # Matches lme4's check.boundary() in modular.R
        theta_opt, boundary_adjusted = self._check_boundary(
            theta=theta_opt,
            lower_bounds=lower_bounds,
            devfun=deviance_fn,
            boundary_tol=boundary_tol,
        )
        if boundary_adjusted:
            # Recompute deviance at adjusted theta
            final_deviance = deviance_fn(theta_opt)
            if verbose:
                print(
                    f"Boundary check: adjusted theta, new deviance={final_deviance:.4f}"
                )

        # Extract results at optimal theta
        from bossanova.ops.lmer_core import (
            solve_pls_sparse,
            extract_variance_components,
        )
        from bossanova.ops.lambda_builder import build_lambda_sparse

        Lambda = build_lambda_sparse(
            theta_opt, self._n_groups_list, self._re_structure, self._metadata
        )
        pls_result = solve_pls_sparse(X_fit, Z_fit, Lambda, y_fit)

        self._coef = pls_result["beta"]
        self._u = pls_result["u"]
        self._theta = np.array(theta_opt)
        self._logdet_L = pls_result["logdet_L"]
        self._logdet_RX = pls_result["logdet_RX"]
        self._rss = pls_result["rss"]

        # Compute PWRSS (penalized residual sum of squares)
        self._pwrss = self._rss + np.sum(self._u**2)

        # Estimate sigma (use valid observations count)
        if method == "REML":
            sigma2 = self._pwrss / (self._n - self._p)
        else:  # ML
            sigma2 = self._pwrss / self._n

        self._sigma = np.sqrt(sigma2)

        # Compute variance-covariance matrix via Schur complement
        self._vcov = self._compute_vcov_schur(
            X=X_fit,
            Z=Z_fit,
            Lambda=Lambda,
            W=None,  # lmer uses identity weights
            sigma2=sigma2,
        )

        # Compute fitted values and residuals on valid rows, then expand to full length
        # fitted = X*beta + Z*Lambda*u
        ZL = Z_fit @ Lambda
        fitted_valid = X_fit @ self._coef + ZL.toarray() @ self._u
        residuals_valid = y_fit - fitted_valid

        # Expand to full length (NaN for rows with missing values)
        self._fitted_values = self._expand_to_full_length(fitted_valid)
        self._residuals = self._expand_to_full_length(residuals_valid)

        # Compute variance components
        var_components = extract_variance_components(
            theta=self._theta,
            pwrss=self._pwrss,
            n=self._n,
            p=self._p,
            re_structure=self._re_structure,
            metadata=self._metadata,
            method=method,
        )

        self._varying_var_dict = var_components

        # Compute deviance and information criteria
        self._deviance = final_deviance

        # Log-likelihood
        if method == "REML":
            # REML log-likelihood
            self._loglik = -0.5 * self._deviance
        else:  # ML
            self._loglik = -0.5 * self._deviance

        # AIC and BIC
        # Number of parameters: p (fixed) + n_theta (variance) + 1 (sigma)
        n_params = self._p + n_theta + 1

        if method == "REML":
            # For REML, AIC/BIC based on REML likelihood
            self._aic = -2 * self._loglik + 2 * n_params
            self._bic = -2 * self._loglik + np.log(self._n - self._p) * n_params
        else:  # ML
            self._aic = -2 * self._loglik + 2 * n_params
            self._bic = -2 * self._loglik + np.log(self._n) * n_params

        # Store method and deviance function
        self._method = method
        self._deviance_fn = deviance_fn

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
            theta_lower=lower_bounds,
            group_names=self._group_names,
            random_names=self._random_names,
            re_structure=re_struct,
            sigma=self._sigma,
            converged=result["converged"],
            boundary_adjusted=boundary_adjusted,
            restarted=restarted,
            optimizer_message=result["message"],
            singular_tol=sing_tol,
        )

        # Check for singular fit
        singular = any(msg.category == "singular" for msg in self._convergence_messages)

        # Build optimizer diagnostics DataFrame (wide format, one row per theta)
        n_theta = len(self._theta)
        schema = LMerOptimizerDiagnostics(
            optimizer="bobyqa",
            converged=bool(result["converged"]),
            n_iter=result["n_evals"],
            final_objective=float(final_deviance),
            message=result["message"],
            theta_index=list(range(n_theta)),
            theta_initial=list(theta_init),
            theta_final=list(self._theta),
            boundary_adjusted=boundary_adjusted,
            restarted=restarted,
            singular=singular,
        )
        self._optimizer_diagnostics = build_lmer_optimizer_diagnostics(schema)

        # Emit warnings if there are any issues
        if self._convergence_messages:
            warning_text = format_convergence_warnings(self._convergence_messages)
            warnings.warn(warning_text, UserWarning)

        # Set fitted flag
        self.is_fitted = True

        # Build ranef DataFrame (needed before inference for some methods)
        self._build_ranef()

        # Set up for no inference (estimates only)
        self._t_stats = None
        self._df = None
        self._p_values = None
        self._ci_lower = None
        self._ci_upper = None
        self._vcov_varpar = None
        self._jac_list = None
        self._result_params = self._compute_result_params_none()
        self._inference = None

        self._result_model = self._compute_result_model()

        # Add _orig columns for transformed variables
        self._add_orig_columns()

        # Track operation for .infer() dispatch
        self._last_operation = "fit"

        return self

    def _compute_inference(self, conf_level: float) -> None:
        """Compute statistical inference (p-values, confidence intervals).

        Dispatches to Satterthwaite or Wald inference based on self._inference.

        Args:
            conf_level: Confidence level for intervals.
        """
        if self._inference == "satterthwaite":
            self._compute_satterthwaite_inference(conf_level)
        else:  # wald
            self._compute_wald_inference(conf_level)

    def _compute_satterthwaite_inference(self, conf_level: float) -> None:
        """Compute Satterthwaite degrees of freedom for fixed effects.

        Implements lmerTest's approach where derivatives are computed with respect
        to the full variance parameter vector varpar = [theta, sigma], not just theta.

        This matches the approach described in:
        Kuznetsova, Brockhoff, Christensen (2017). lmerTest Package.
        Journal of Statistical Software, 82(13).

        Args:
            conf_level: Confidence level for intervals.
        """
        from bossanova.stats.satterthwaite import (
            compute_hessian_richardson,
            compute_jacobian_richardson,
            satterthwaite_df,
            satterthwaite_t_test,
        )
        from bossanova.ops.lambda_builder import build_lambda_sparse

        # Build full variance parameter vector: varpar = [theta, sigma]
        # This matches lmerTest's devfun_varpar which operates on c(theta, sigma)
        varpar = np.concatenate([self._theta, [self._sigma]])

        # Define deviance as a function of varpar = [theta, sigma]
        # This matches lmerTest's devfun_varpar function
        #
        # PERFORMANCE: Uses sparse-dense operations throughout to avoid
        # converting ZL to dense. For InstEval (73k × 4k), this saves ~1.2GB
        # per evaluation. With Richardson extrapolation (~48 evals), this
        # reduces memory from ~57GB to ~2GB.
        # Use fit-time matrices for inference computations
        X_fit = self._X_fit
        Z_fit = self._Z_fit
        y_fit = self._y_fit

        def deviance_varpar(varpar):
            """Compute deviance as a function of varpar = [theta, sigma]."""
            theta = varpar[:-1]
            sigma = varpar[-1]
            sigma2 = sigma**2

            # Build Lambda from theta
            Lambda = build_lambda_sparse(
                theta, self._n_groups_list, self._re_structure, self._metadata
            )

            # Solve PLS to get components - ZL stays SPARSE throughout
            ZL = Z_fit @ Lambda
            # Ensure CSC format for CHOLMOD (ZL.T @ ZL may produce CSR)
            S22 = (ZL.T @ ZL).tocsc() + sp.eye(Lambda.shape[0], format="csc")

            factor_S22 = sparse_cholesky(S22)

            # Compute log determinants
            logdet_L = factor_S22.logdet()

            # Solve for u and beta using SPARSE-DENSE operations
            # ZL.T @ y: sparse (q,n) @ dense (n,) -> dense (q,) - efficient!
            ZLty = ZL.T @ y_fit
            cu = factor_S22(ZLty)

            XtX = X_fit.T @ X_fit
            # ZL.T @ X: sparse (q,n) @ dense (n,p) -> dense (q,p) - efficient!
            XtZL = (ZL.T @ X_fit).T  # Transpose to get (p, q)
            Xty = X_fit.T @ y_fit

            S22_inv_XtZL_T = factor_S22(XtZL.T)
            schur = XtX - XtZL @ S22_inv_XtZL_T
            rhs = Xty - XtZL @ cu

            # Robust solve: fallback to lstsq for near-singular Schur
            # This can happen when y is constant within groups (residual var ~ 0)
            try:
                beta = np.linalg.solve(schur, rhs)
            except np.linalg.LinAlgError:
                beta = np.linalg.lstsq(schur, rhs, rcond=None)[0]
            u = cu - S22_inv_XtZL_T @ beta

            # Compute RSS using SPARSE matvec
            # ZL @ u: sparse (n,q) @ dense (q,) -> dense (n,) - efficient!
            fitted = X_fit @ beta + ZL @ u
            resid = y_fit - fitted
            rss = np.sum(resid**2)
            pwrss = rss + np.sum(u**2)

            # Compute log determinant of RX (for REML)
            # Handle near-singular Schur with regularization
            try:
                chol_schur = np.linalg.cholesky(schur)
            except np.linalg.LinAlgError:
                # Add small regularization for near-singular case
                schur_reg = schur + 1e-8 * np.eye(schur.shape[0])
                chol_schur = np.linalg.cholesky(schur_reg)
            logdet_RX2 = 2 * np.sum(np.log(np.abs(np.diag(chol_schur))))

            # Compute deviance
            n = self._n
            p = self._p

            if self._method == "REML":
                df = n - p
                dev = (
                    df * np.log(2 * np.pi * sigma2)
                    + pwrss / sigma2
                    + logdet_L
                    + logdet_RX2
                )
            else:  # ML
                df = n
                dev = df * np.log(2 * np.pi * sigma2) + pwrss / sigma2 + logdet_L

            return dev

        # Compute Hessian of deviance w.r.t. varpar = [theta, sigma]
        H = compute_hessian_richardson(deviance_varpar, varpar)

        # Define vcov(beta) as a function of varpar = [theta, sigma]
        # PERFORMANCE: Uses sparse-dense operations to avoid ZL.toarray()
        def vcov_varpar(varpar):
            """Compute Vcov(beta) for given varpar = [theta, sigma]."""
            theta = varpar[:-1]
            sigma = varpar[-1]
            sigma2 = sigma**2

            Lambda = build_lambda_sparse(
                theta, self._n_groups_list, self._re_structure, self._metadata
            )
            ZL = Z_fit @ Lambda
            # Ensure CSC format for CHOLMOD (ZL.T @ ZL may produce CSR)
            S22 = (ZL.T @ ZL).tocsc() + sp.eye(Lambda.shape[0], format="csc")

            factor_S22 = sparse_cholesky(S22)
            XtX = X_fit.T @ X_fit
            # SPARSE-DENSE: ZL.T @ X -> dense (q, p)
            XtZL = (ZL.T @ X_fit).T  # (p, q)
            S22_inv_XtZL_T = factor_S22(XtZL.T)
            schur = XtX - XtZL @ S22_inv_XtZL_T

            # vcov(beta) = sigma^2 * inv(schur)
            # Use pseudo-inverse for near-singular cases
            try:
                schur_inv = np.linalg.inv(schur)
            except np.linalg.LinAlgError:
                schur_inv = np.linalg.pinv(schur)
            return sigma2 * schur_inv

        # Compute Jacobian of Vcov(beta) w.r.t. varpar = [theta, sigma]
        J = compute_jacobian_richardson(vcov_varpar, varpar)

        # Cache Satterthwaite ingredients for use with arbitrary contrasts (emmeans)
        # vcov_varpar = 2 * H^{-1} using Moore-Penrose pseudo-inverse
        # (same approach as in satterthwaite_df, but we cache it here)
        tol = 1e-8
        eig_vals, eig_vecs = np.linalg.eigh(H)
        pos = eig_vals > tol
        q = int(np.sum(pos))
        if q > 0:
            eig_vecs_pos = eig_vecs[:, pos]
            eig_vals_pos = eig_vals[pos]
            H_inv = eig_vecs_pos @ np.diag(1.0 / eig_vals_pos) @ eig_vecs_pos.T
            self._vcov_varpar = 2.0 * H_inv
        else:
            # Fallback: regularized pseudo-inverse
            k = H.shape[0]
            self._vcov_varpar = 2.0 * np.linalg.pinv(H + np.eye(k) * 1e-6)

        # Convert Jacobian array (p, p, k) to list of k matrices for satterthwaite_df_for_contrasts
        k = J.shape[2]
        self._jac_list = [J[:, :, i] for i in range(k)]

        from bossanova.ops.inference import compute_se_from_vcov

        # Compute Satterthwaite df
        df = satterthwaite_df(self._vcov, J, H)

        # Compute t-statistics, p-values, CIs
        se = compute_se_from_vcov(self._vcov)
        results = satterthwaite_t_test(self._coef, se, df, conf_level)

        # Store results
        self._t_stats = results["statistic"]
        self._df = df
        self._p_values = results["p_value"]
        self._ci_lower = results["ci_lower"]
        self._ci_upper = results["ci_upper"]

    def _compute_wald_inference(self, conf_level: float) -> None:
        """Compute Wald inference using z-distribution (df = infinity).

        Args:
            conf_level: Confidence level for intervals.
        """
        from bossanova.ops.inference import (
            compute_ci,
            compute_se_from_vcov,
            compute_z_critical,
        )

        se = compute_se_from_vcov(self._vcov)
        self._t_stats = self._coef / se
        self._df = np.full(self._p, np.inf)  # Asymptotic
        self._p_values = 2 * (1 - stats.norm.cdf(np.abs(self._t_stats)))

        # Confidence intervals
        z_crit = compute_z_critical(conf_level)
        self._ci_lower, self._ci_upper = compute_ci(self._coef, se, z_crit)

        # Satterthwaite ingredients not available for Wald inference
        self._vcov_varpar = None
        self._jac_list = None

    def _get_inference_df(self) -> float:
        """Return degrees of freedom for inference.

        For lmer with Satterthwaite, returns the mean df across coefficients.
        For Wald inference or when no inference was run, returns infinity
        (equivalent to z-distribution).

        Returns:
            Scalar df value for use in t-distribution or z-distribution.
        """
        if self._df is None:
            # No inference run; use asymptotic (z) inference
            return float(np.inf)
        return float(np.mean(self._df))

    def _compute_emm_df(self, X_ref: np.ndarray) -> float | np.ndarray:
        """Compute Satterthwaite df for EMMs.

        Overrides base class to provide per-EMM degrees of freedom using
        Satterthwaite approximation. Each row of X_ref defines a contrast
        (linear combination of coefficients), and each gets its own df.

        Args:
            X_ref: Prediction matrix, shape (n_emms, n_coef).

        Returns:
            Array of df values, shape (n_emms,). Returns infinity for all
            if Wald inference was used (Satterthwaite ingredients unavailable).
        """
        return self._compute_satterthwaite_df_for_contrasts(X_ref)

    def _compute_satterthwaite_df_for_contrasts(
        self, L: np.ndarray
    ) -> np.ndarray | float:
        """Compute Satterthwaite degrees of freedom for arbitrary contrasts.

        This method computes per-contrast df for linear combinations L @ β.
        It's used by emmeans to get proper df for each estimated marginal mean.

        Args:
            L: Contrast matrix, shape (n_contrasts, n_coef). Each row is a
                contrast vector. For a single contrast, shape can be (n_coef,).

        Returns:
            Array of df values, shape (n_contrasts,). For a single contrast,
            returns a scalar float. Returns infinity for all contrasts if
            Wald inference was used (Satterthwaite ingredients not available).

        Raises:
            RuntimeError: If model has not been fit.

        Examples:
            >>> model = LMer("y ~ x + (1|g)", data).fit()
            >>> # Get df for EMMs
            >>> df = model._compute_satterthwaite_df_for_contrasts(X_ref)
        """
        if self._vcov is None:
            raise RuntimeError("Model must be fit before computing df")

        # If Satterthwaite ingredients not available (Wald inference), return inf
        if self._vcov_varpar is None or self._jac_list is None:
            L = np.atleast_2d(L)
            n_contrasts = L.shape[0]
            if n_contrasts == 1:
                return float(np.inf)
            return np.full(n_contrasts, np.inf)

        # Use the stats function for the computation
        from bossanova.stats.satterthwaite import satterthwaite_df_for_contrasts

        return satterthwaite_df_for_contrasts(
            L=L,
            vcov_beta=self._vcov,
            vcov_varpar=self._vcov_varpar,
            jac_list=self._jac_list,
        )

    def _compute_result_params(self, conf_level: float = 0.95) -> pl.DataFrame:
        """Build coefficient table.

        Args:
            conf_level: Confidence level for CIs.

        Returns:
            Coefficient table with schema from LMerResultFit.
        """
        from bossanova.ops.inference import compute_se_from_vcov

        se = compute_se_from_vcov(self._vcov)

        schema = LMerResultFit(
            term=self._X_names,
            estimate=self._get_coef().tolist(),
            se=se.tolist(),
            statistic=self._t_stats.tolist(),  # type: ignore[union-attr]
            df=self._df.tolist(),  # type: ignore[union-attr]
            p_value=self._p_values.tolist(),  # type: ignore[union-attr]
            ci_lower=self._ci_lower.tolist(),  # type: ignore[union-attr]
            ci_upper=self._ci_upper.tolist(),  # type: ignore[union-attr]
        )

        return build_lmer_result_params(schema)

    def _compute_result_params_none(self) -> pl.DataFrame:
        """Build coefficient table with estimates only (no inference).

        Returns:
            Coefficient table with NaN for inference columns.
        """
        from bossanova.ops.inference import compute_se_from_vcov

        se = compute_se_from_vcov(self._vcov)
        n = len(self._coef)
        nan_list = [float("nan")] * n

        schema = LMerResultFit(
            term=self._X_names,
            estimate=self._get_coef().tolist(),
            se=se.tolist(),
            statistic=nan_list,
            df=nan_list,
            p_value=nan_list,
            ci_lower=nan_list,
            ci_upper=nan_list,
        )

        return build_lmer_result_params(schema)

    def _compute_result_model(self) -> pl.DataFrame:
        """Build fit statistics table.

        Returns:
            Fit statistics with schema from LMerResultFitDiagnostics.
        """
        # Compute Nakagawa-Schielzeth R² and ICC
        # Reference: Nakagawa & Schielzeth (2013) Methods Ecol Evol 4:133-142
        rsq_m, rsq_c, icc = self._compute_rsquared_and_icc()

        schema = LMerResultFitDiagnostics(
            nobs=int(self._n),
            df_model=int(self._p - 1),  # Exclude intercept
            df_resid=float(self._n - self._p),
            sigma=float(self._sigma),
            deviance=float(self._deviance),
            method=self._method,
            aic=float(self._aic),
            bic=float(self._bic),
            loglik=float(self._loglik),
            rsquared_marginal=float(rsq_m),
            rsquared_conditional=float(rsq_c),
            icc=float(icc),
        )

        return build_lmer_result_model(schema)

    def _compute_rsquared_and_icc(self) -> tuple[float, float, float]:
        """Compute Nakagawa-Schielzeth R² and ICC.

        The Nakagawa-Schielzeth method decomposes total variance into:
        - var_fixed: variance explained by fixed effects
        - var_random: variance explained by random effects
        - var_resid: residual variance (sigma²)

        Returns:
            Tuple of (rsquared_marginal, rsquared_conditional, icc).
            - R²_m = var_fixed / (var_fixed + var_random + var_resid)
            - R²_c = (var_fixed + var_random) / (var_fixed + var_random + var_resid)
            - ICC = var_random / (var_random + var_resid)

        Reference:
            Nakagawa & Schielzeth (2013) Methods Ecol Evol 4:133-142
        """
        # Variance of fixed effects: var(X @ beta)
        # Use fit-time design matrix (valid rows only)
        fixed_fitted = self._X_fit @ self._coef
        var_fixed = float(np.var(fixed_fitted, ddof=0))

        # Sum of random effect variances from varying_var DataFrame
        # Exclude Residual row, sum the variance column
        ranef_df = self.varying_var
        var_random = float(
            ranef_df.filter(pl.col("group") != "Residual")["variance"].sum()
        )

        # Residual variance
        var_resid = self._sigma**2

        # Total variance
        var_total = var_fixed + var_random + var_resid

        # Avoid division by zero
        if var_total == 0:
            return 0.0, 0.0, 0.0

        # Nakagawa-Schielzeth R²
        rsq_marginal = var_fixed / var_total
        rsq_conditional = (var_fixed + var_random) / var_total

        # ICC (proportion of variance from random effects)
        var_group_resid = var_random + var_resid
        icc = var_random / var_group_resid if var_group_resid > 0 else 0.0

        return rsq_marginal, rsq_conditional, icc

    def _simulate_response(self, mu: np.ndarray) -> np.ndarray:
        """Simulate response given expected values.

        Adds Gaussian noise with residual standard deviation sigma.

        Args:
            mu: Expected values (fitted values or predictions).

        Returns:
            Simulated response values.
        """
        epsilon = np.random.randn(len(mu)) * self._sigma
        return mu + epsilon

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def sigma(self) -> float:
        """Residual standard deviation."""
        self._check_fitted()
        return float(self._sigma)

    @property
    def method(self) -> str | None:
        """Estimation method used ('ML' or 'REML'). None if not fitted."""
        return self._method

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
            units: Units for predictions (always "data" for lmer).
            varying: How to handle varying effects:
                - "include": Use estimated varying effects (default).
                  Uses fitted BLUPs for known grouping levels.
                - "exclude": Population-level predictions (fixed effects only).
            allow_new_levels: Allow new levels of grouping factors in data.
                If True and varying="include", new levels get varying effect = 0
                (equivalent to population-level prediction for those observations).
                If False (default), raises ValueError on new levels.
            pred_int: Prediction interval level (not yet supported for LMMs).
                Must be None. Non-None values raise NotImplementedError.

        Returns:
            DataFrame with `fitted` column containing predictions.

        Raises:
            ValueError: If units is not "data".
            ValueError: If new grouping levels found and allow_new_levels=False.
            NotImplementedError: If pred_int is requested (not yet supported for LMMs).
        """
        self._check_fitted()

        # Check for unsupported prediction interval
        if pred_int is not None:
            raise NotImplementedError(
                "Prediction intervals not yet supported for LMMs. "
                "Use pred_int=None for point predictions."
            )

        if units != "data":
            raise ValueError(
                f"units='{units}' is not supported for linear mixed models.\n\n"
                "For lmer, predictions are always on the response scale (units='data').\n"
                "Link-scale predictions are only available for glm and glmer."
            )

        # Convert to polars if pandas
        data_pl = coerce_dataframe(data)

        # Use shared infrastructure for prediction
        X_new, fitted_valid = self._predict_newdata(data_pl, varying, allow_new_levels)

        # Handle NAs in new data: find valid rows based on X_new
        n_pred = X_new.shape[0]
        valid_pred = ~np.any(np.isnan(X_new), axis=1)

        # Initialize predictions with NaN, fill valid rows
        fitted = np.full(n_pred, np.nan)
        fitted[valid_pred] = fitted_valid[valid_pred]

        return pl.DataFrame({"fitted": fitted})

    def _bootstrap(
        self,
        n_boot: int = 999,
        boot_type: Literal["parametric", "case"] = "parametric",
        ci_type: Literal["percentile", "basic", "bca"] = "percentile",
        level: float = 0.95,
        seed: int | None = None,
        which: Literal["fixef", "ranef", "all"] = "fixef",
        verbose: bool = False,
        n_jobs: int = 1,
    ):
        """Internal bootstrap implementation for lmer.

        Args:
            n_boot: Number of bootstrap samples. Default 999.
            boot_type: Type of bootstrap ("parametric" or "case").
            ci_type: Confidence interval method ("percentile", "basic", "bca").
            level: Confidence level (e.g., 0.95 for 95% CI).
            seed: Random seed for reproducibility.
            which: Which parameters to bootstrap ("fixef", "ranef", "all").
            verbose: Print progress information.
            n_jobs: Number of parallel jobs.

        Returns:
            BootstrapResult object with bootstrap samples and confidence intervals.
        """
        from bossanova.resample.mixed import lmer_bootstrap

        self._check_fitted()

        # Get lower bounds for theta (same logic as fit())
        n_theta = len(self._theta)
        lower_bounds = self._get_theta_lower_bounds(n_theta)

        # Call lmer_bootstrap function (use fit-time matrices)
        result = lmer_bootstrap(
            X=self._X_fit,
            Z=self._Z_fit,
            y=self._y_fit,
            X_names=self._X_names,
            theta=self._theta,
            beta=self._coef,
            sigma=self._sigma,
            n_groups_list=self._n_groups_list,
            re_structure=self._re_structure,
            metadata=self._metadata,
            lower_bounds=lower_bounds,
            n_boot=n_boot,
            seed=seed,
            boot_type=boot_type,
            ci_type=ci_type,
            level=level,
            method=self._method,
            max_iter=10000,  # Match fit() defaults
            tol=1e-8,
            verbose=verbose,
            which=which,
            group_names=self._group_names,
            random_names=self._random_names,
            n_jobs=n_jobs,
        )

        return result

    def summary(self, decimals: int = 3) -> None:
        """Print R-style model summary.

        Displays:
        - Model formula and method (REML/ML)
        - Random effects variance components
        - Number of observations and groups
        - Fixed effects coefficient table

        Args:
            decimals: Number of decimal places to display.

        Examples:
            ```python
            model.fit()
            model.summary()

            # Linear mixed model fit by REML
            # Formula: Reaction ~ Days + (Days | Subject)
            #
            # Random effects:
            #  Groups   Name        Variance Std.Dev. Corr
            #  Subject  (Intercept) 612.10   24.74
            #           Days         35.07    5.92    0.07
            #  Residual             654.94   25.59
            # Number of obs: 180, groups:  Subject, 18
            #
            # Fixed effects:
            #             Estimate Std. Error df    t value Pr(>|t|)
            # (Intercept)  251.405     6.825   17.0   36.84  < 2e-16 ***
            # Days          10.467     1.546   17.0    6.77  3.3e-06 ***
            ```
        """
        self._check_fitted()

        # Header
        print(f"\nLinear mixed model fit by {self._method}")
        print(f"Formula: {self.formula}")
        print()

        # Random effects
        from bossanova.models.display import (
            print_coefficient_table,
            print_random_effects,
            print_signif_codes,
        )

        print_random_effects(self, var_decimals=2)

        # Fixed effects table
        print("Fixed effects:")

        print_coefficient_table(
            self._result_params,
            decimals=decimals,
            show_df=True,
            inference=self._inference,
        )
        # Only show signif codes for asymptotic inference (has p-values)
        if "p_value" in self._result_params.columns:  # type: ignore[union-attr]  # guarded by _check_fitted
            print_signif_codes()

    # =========================================================================
    # Inference Method Overrides (called by BaseModel._infer())
    # =========================================================================

    def _infer(
        self,
        method: str = "asymp",
        *,
        conf_int: float = 0.95,
        # Boot kwargs
        n_boot: int = 999,
        boot_type: str = "parametric",
        ci_type: str = "percentile",
        # Common
        seed: int | None = None,
        n_jobs: int = 1,
        verbose: bool = False,
        # Unused by lmer (kept for API consistency)
        n_perm: int = 999,
        k: int = 5,
        loo: bool = False,
        errors: str = "auto",
    ) -> Self:
        """Compute inference on fitted lmer model (internal).

        Called by fit() when inference parameter is specified.
        Always updates result_params in place.
        """
        self._check_fitted()

        # Non-default errors values are not supported for lmer
        if errors not in ("auto", "iid"):
            raise ValueError(
                f"errors='{errors}' is only supported for lm models, not lmer. "
                "Use errors='auto' or 'iid' for Satterthwaite inference."
            )

        # Parse conf_int
        conf_level = self._parse_conf_int(conf_int)

        # For lmer, "asymp" means Satterthwaite (NOT Wald like other models)
        # Keep "wald" as separate method for z-distribution inference
        if method == "asymp":
            method = "satterthwaite"

        # Dispatch to appropriate inference method
        if method == "satterthwaite":
            result_df = self._infer_satterthwaite(conf_level)
        elif method == "wald":
            result_df = self._infer_wald(conf_level)
        elif method == "boot":
            result_df = self._infer_boot(
                conf_level=conf_level,
                n_boot=n_boot,
                boot_type=boot_type,
                ci_type=ci_type,
                seed=seed,
                n_jobs=n_jobs,
                verbose=verbose,
            )
        elif method == "perm":
            result_df = self._infer_perm(
                conf_level=conf_level,
                n_perm=n_perm,
                seed=seed,
                n_jobs=n_jobs,
                verbose=verbose,
            )
        elif method == "cv":
            result_df = self._infer_cv(
                conf_level=conf_level,
                k=k,
                loo=loo,
                seed=seed,
                n_jobs=n_jobs,
                verbose=verbose,
            )
        else:
            raise NotImplementedError(
                f"Inference method '{method}' not supported for lmer. "
                f"Supported methods: 'asymp', 'satterthwaite', 'wald', 'boot'."
            )

        # Update model state
        self._result_params = result_df
        self._inference = method
        return self

    def _infer_asymp(
        self,
        conf_level: float,
        errors: str = "auto",
    ) -> pl.DataFrame:
        """Compute asymptotic/Wald inference for lmer.

        For lmer, "asymp" defaults to Satterthwaite for proper df approximation.
        Use inference="wald" explicitly for infinite df (z-distribution).

        Args:
            conf_level: Confidence level for intervals.
            errors: Error structure assumption (only 'auto'/'iid' for lmer).

        Returns:
            DataFrame with coefficient table including Satterthwaite-adjusted
            CIs and t-test p-values.
        """
        # Non-default errors values are not supported for lmer
        if errors not in ("auto", "iid"):
            raise ValueError(
                f"errors='{errors}' is only supported for lm models, not lmer. "
                "Use errors='auto' or 'iid' for Satterthwaite inference."
            )

        # For lmer, asymp means Satterthwaite by default
        return self._infer_satterthwaite(conf_level)

    def _infer_satterthwaite(self, conf_level: float) -> pl.DataFrame:
        """Compute Satterthwaite degrees of freedom inference for lmer.

        Args:
            conf_level: Confidence level for intervals.

        Returns:
            DataFrame with coefficient table including Satterthwaite-adjusted
            CIs and t-test p-values.
        """
        # Compute Satterthwaite inference
        self._compute_satterthwaite_inference(conf_level)
        return self._compute_result_params(conf_level)

    def _infer_wald(self, conf_level: float) -> pl.DataFrame:
        """Compute Wald inference (z-distribution) for lmer.

        Args:
            conf_level: Confidence level for intervals.

        Returns:
            DataFrame with coefficient table including Wald CIs and z-test p-values.
        """
        # Compute Wald inference
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
        """Compute bootstrap inference for lmer.

        Args:
            conf_level: Confidence level for intervals.
            n_boot: Number of bootstrap samples.
            boot_type: Type of bootstrap ("parametric" or "case").
            ci_type: Type of CI ("percentile", "basic", "bca").
            seed: Random seed.
            n_jobs: Number of parallel jobs.
            verbose: Print progress.

        Returns:
            DataFrame with coefficient table including bootstrap CIs.
        """
        from bossanova.results.builders import build_boot_result_params
        from bossanova.results.schemas import BootResultFit

        # Mixed models only support "parametric" bootstrap - default to it
        if boot_type != "parametric":
            boot_type = "parametric"

        # Set placeholders for Satterthwaite/Wald stats (not computed for boot)
        self._t_stats = None
        self._df = None
        self._p_values = None
        self._ci_lower = None
        self._ci_upper = None
        self._vcov_varpar = None
        self._jac_list = None

        # Run bootstrap
        boot_result = self._bootstrap(
            n_boot=n_boot,
            seed=seed,
            boot_type=boot_type,
            ci_type=ci_type,
            level=conf_level,
            verbose=verbose,
            which="fixef",
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
        """Permutation tests are not supported for mixed models.

        Args:
            conf_level: Confidence level (unused).
            n_perm: Number of permutations (unused).
            seed: Random seed (unused).
            n_jobs: Number of parallel jobs (unused).
            verbose: Print progress (unused).

        Raises:
            NotImplementedError: Permutation tests are not supported for mixed models.
        """
        raise NotImplementedError(
            "Permutation tests are not supported for mixed models. "
            "Consider using bootstrap inference instead: infer('boot', ...)"
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
        """Cross-validation is not supported for mixed models.

        Args:
            conf_level: Confidence level (unused).
            k: Number of folds (unused).
            loo: Use leave-one-out CV (unused).
            seed: Random seed (unused).
            n_jobs: Number of parallel jobs (unused).
            verbose: Print progress (unused).

        Raises:
            NotImplementedError: Cross-validation is not supported for mixed models.
        """
        raise NotImplementedError(
            "Cross-validation is not supported for mixed models. "
            "CV is available for linear models via lm and glm."
        )
