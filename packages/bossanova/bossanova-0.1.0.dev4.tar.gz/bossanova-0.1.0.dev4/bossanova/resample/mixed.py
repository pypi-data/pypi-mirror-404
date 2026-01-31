"""Mixed model resampling with full PIRLS/PLS refitting.

This module provides bootstrap procedures for linear (lmer) and generalized
linear (glmer) mixed-effects models. Unlike LM/GLM, mixed models require
full optimization (PLS for lmer, PIRLS for glmer) for each resample.

Key differences from LM/GLM:
- Sequential loop (cannot vmap due to scipy.sparse operations)
- Parametric bootstrap: simulate random effects b* ~ N(0, ΛΛ') then response
- Case bootstrap: cluster-level resampling (not observation-level)
- Full model refit per sample (expensive but necessary)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np
import scipy.sparse as sp
from joblib import Parallel, delayed
from tqdm.auto import tqdm

# Type alias for arrays (works with both JAX and NumPy)
if TYPE_CHECKING:
    from jax import Array

from bossanova.ops.family import Family
from bossanova.ops.rng import RNG
from bossanova.ops.glmer_pirls import fit_glmm_pirls
from bossanova.ops.lambda_builder import (
    build_lambda_sparse,
    build_lambda_template,
)
from bossanova.ops.lmer_core import (
    PLSInvariants,
    lmm_deviance_sparse,
    solve_pls_sparse,
)
from bossanova.optimize import optimize_theta
from bossanova.resample.core import (
    bootstrap_ci_basic,
    bootstrap_ci_percentile,
)
from bossanova.resample.glm import simulate_response
from bossanova.resample.results import BootstrapResult

__all__ = [
    "glmer_bootstrap",
    "lmer_bootstrap",
]


# =============================================================================
# GLMER Bootstrap
# =============================================================================


def _simulate_from_glmer(
    rng: RNG,
    X: np.ndarray,
    Z: sp.csc_matrix,
    beta: np.ndarray,
    theta: np.ndarray,
    family: Family,
    n_groups_list: list[int],
    re_structure: list[dict],
    metadata: dict,
    weights: np.ndarray | None = None,
) -> Array:
    """Simulate response from fitted GLMER model.

    Algorithm:
    1. Simulate random effects: b* ~ N(0, ΛΛ')
    2. Compute linear predictor: η* = Xβ̂ + Zb*
    3. Compute mean: μ* = g⁻¹(η*)
    4. Simulate response from family distribution

    Args:
        rng: RNG object for random number generation.
        X: Fixed effects design matrix (n, p).
        Z: Random effects design matrix (sparse CSC, n, q).
        beta: Fixed effects coefficients (p,).
        theta: Variance parameters (n_theta,).
        family: GLM family object.
        n_groups_list: List of group sizes per RE term.
        re_structure: Random effects structure metadata.
        metadata: Additional metadata for Lambda construction.
        weights: Prior observation weights (only for binomial trials).

    Returns:
        Simulated response (n,) as numpy/JAX array.
    """
    # Build Lambda from theta
    Lambda = build_lambda_sparse(theta, n_groups_list, re_structure, metadata)

    # Simulate spherical random effects: u* ~ N(0, I_q)
    q = Lambda.shape[0]
    u_star = rng.normal(shape=(q,))

    # Transform to original scale: b* = Λu*
    b_star = Lambda @ u_star

    # Compute linear predictor: η* = Xβ + Zb*
    Zb = Z @ b_star
    if sp.issparse(Zb):
        Zb = Zb.toarray().ravel()
    else:
        Zb = np.asarray(Zb).ravel()
    eta_star = X @ beta + Zb

    # Compute mean: μ* = g⁻¹(η*)
    mu_star = np.asarray(family.link_inverse(eta_star))

    # Simulate response from family distribution
    # Use shared simulate_response from glm.py (already handles binomial, poisson)
    _, rng_response = rng.split_one()
    y_star = simulate_response(
        rng_response,
        mu_star,
        family,
        dispersion=1.0,  # GLMMs have fixed dispersion
        weights=weights,
    )

    return y_star


def _glmer_bootstrap_single_iteration(
    rng: RNG,
    X_np: np.ndarray,
    Z_sparse: sp.csc_matrix,
    beta_np: np.ndarray,
    theta_np: np.ndarray,
    family: Family,
    n_groups_list: list[int],
    re_structure: list[dict],
    metadata: dict,
    weights_np: np.ndarray | None,
    boot_type: str,
    max_iter: int,
    tol: float,
    max_outer_iter: int,
    p: int,
    lambda_template=None,
) -> np.ndarray:
    """Execute a single GLMER bootstrap iteration.

    This is a standalone function (not a closure) to enable joblib parallelization.

    Args:
        rng: RNG object for random number generation.
        X_np: Fixed effects design matrix as numpy array (n, p).
        Z_sparse: Random effects design matrix as sparse CSC.
        beta_np: Fixed effects as numpy array (p,).
        theta_np: Variance parameters as numpy array.
        family: GLM family object.
        n_groups_list: List of group sizes per RE term.
        re_structure: Random effects structure metadata.
        metadata: Additional metadata for Lambda construction.
        weights_np: Prior weights as numpy array or None.
        boot_type: "parametric" or "case".
        max_iter: Maximum PIRLS iterations.
        tol: Convergence tolerance.
        max_outer_iter: Maximum BOBYQA iterations.
        p: Number of fixed effects coefficients.
        lambda_template: Pre-built Lambda template for efficient updates.

    Returns:
        Bootstrap coefficient estimates (p,), or NaN array if failed.
    """
    try:
        if boot_type == "parametric":
            # Parametric bootstrap: simulate from fitted model
            y_boot_jax = _simulate_from_glmer(
                rng,
                X_np,
                Z_sparse,
                beta_np,
                theta_np,
                family,
                n_groups_list,
                re_structure,
                metadata,
                weights_np,
            )
            y_boot = np.asarray(y_boot_jax)

            # Refit model with simulated y
            result = fit_glmm_pirls(
                X=X_np,
                Z=Z_sparse,
                y=y_boot,
                family=family,
                n_groups_list=n_groups_list,
                re_structure=re_structure,
                metadata=metadata,
                prior_weights=weights_np,
                max_outer_iter=max_outer_iter,
                pirls_max_iter=max_iter * 4,  # More PIRLS iterations for bootstrap
                pirls_tol=tol * 10,  # Relax PIRLS tolerance for bootstrap
                verbose=False,
                lambda_template=lambda_template,  # Reuse pre-built template
            )

        elif boot_type == "case":
            # Case bootstrap: cluster-level resampling
            raise NotImplementedError(
                "Case bootstrap for GLMER not yet implemented. "
                "Use boot_type='parametric' for now."
            )

        # Check convergence and extract coefficients
        if result["converged"]:
            return result["beta"]
        else:
            return np.full(p, np.nan)

    except Exception:
        return np.full(p, np.nan)


def glmer_bootstrap(
    X: Array,
    Z: sp.csc_matrix | Array,
    y: Array,
    X_names: list[str],
    theta: Array,
    beta: Array,
    family: Family,
    n_groups_list: list[int],
    re_structure: list[dict],
    metadata: dict,
    weights: Array | None = None,
    n_boot: int = 999,
    seed: int | None = None,
    boot_type: Literal["parametric", "case"] = "parametric",
    ci_type: Literal["percentile", "basic", "bca"] = "percentile",
    level: float = 0.95,
    max_iter: int = 25,
    tol: float = 1e-8,
    max_outer_iter: int = 10000,
    verbose: bool = False,
    n_jobs: int = 1,
) -> BootstrapResult:
    """Bootstrap inference for GLMER coefficients.

    Each bootstrap iteration requires full PIRLS optimization.
    Supports parallel execution via joblib.

    Bootstrap types:
    - parametric (default): Simulate y* from fitted model (b* ~ N(0, ΛΛ'), then
        y* from family distribution). Assumes model is correct.
    - case: Resample entire clusters with replacement. Robust to misspecification.

    Note:
        Residual bootstrap is not available for mixed models because the
        residual structure involves multiple variance components (within-group
        and between-group). Parametric bootstrap properly accounts for this
        hierarchical structure by simulating new random effects.

    Args:
        X: Fixed effects design matrix, shape (n, p).
        Z: Random effects design matrix, sparse CSC or dense array (n, q).
        y: Response vector, shape (n,).
        X_names: Fixed effects coefficient names.
        theta: Variance parameters from fitted model (n_theta,).
        beta: Fixed effects from fitted model (p,).
        family: GLM family object (binomial or poisson).
        n_groups_list: List of group sizes per RE term.
        re_structure: Random effects structure metadata.
        metadata: Additional metadata for Lambda construction.
        weights: Prior observation weights (n,) or None.
            For binomial: number of trials per observation.
        n_boot: Number of bootstrap samples.
        seed: Random seed for reproducibility.
        boot_type: Type of bootstrap: "parametric" or "case".
        ci_type: Confidence interval type: "percentile", "basic", or "bca".
        level: Confidence level (e.g., 0.95 for 95% CI).
        max_iter: Maximum PIRLS iterations per refit.
        tol: Convergence tolerance for PIRLS.
        max_outer_iter: Maximum BOBYQA iterations for theta optimization.
        verbose: If True, show tqdm progress bar.
        n_jobs: Number of parallel jobs. Default 1 (sequential). Use -1 for all cores.

    Returns:
        BootstrapResult with observed stats, bootstrap samples, and CIs.

    Raises:
        ValueError: If boot_type is not "parametric" or "case".
        ValueError: If ci_type is not "percentile", "basic", or "bca".
        NotImplementedError: If boot_type="case" (not yet implemented).

    Examples:
        >>> from bossanova.ops.family import binomial
        >>> family = binomial()
        >>> result = glmer_bootstrap(
        ...     X, Z, y, ["Intercept", "x"],
        ...     theta=theta_hat, beta=beta_hat,
        ...     family=family, n_groups_list=[15],
        ...     re_structure=[{"type": "intercept"}],
        ...     metadata={}, n_boot=999
        ... )
        >>> print(result.ci)
    """
    # Input validation
    if boot_type not in ("parametric", "case"):
        raise ValueError(f"boot_type must be 'parametric' or 'case', got {boot_type}")
    if ci_type not in ("percentile", "basic", "bca"):
        raise ValueError(
            f"ci_type must be 'percentile', 'basic', or 'bca', got {ci_type}"
        )
    if boot_type == "case":
        raise NotImplementedError(
            "Case bootstrap for glmer is not yet implemented. "
            "Use boot_type='parametric' instead."
        )

    # Convert to appropriate types
    X_np = np.asarray(X)
    theta_np = np.asarray(theta)
    beta_np = np.asarray(beta)
    n, p = X_np.shape

    # Convert Z to sparse CSC if needed
    if not sp.isspmatrix_csc(Z):
        Z_sparse = sp.csc_matrix(np.asarray(Z))
    else:
        Z_sparse = Z

    if weights is not None:
        weights_np = np.asarray(weights)
    else:
        weights_np = None

    rng = RNG.from_seed(seed)

    # Observed coefficients (from input)
    coef_obs = np.asarray(beta_np)

    # Generate all RNGs upfront
    rngs = rng.split(n_boot)

    # Pre-build lambda template for efficient updates during bootstrap iterations
    # This caches the sparsity pattern and only updates values (~10-15% speedup)
    try:
        lambda_template = build_lambda_template(n_groups_list, re_structure, metadata)
    except NotImplementedError:
        # Complex structures (nested/crossed) fall back to build_lambda_sparse
        lambda_template = None

    # Shared iteration arguments
    iter_args = {
        "X_np": X_np,
        "Z_sparse": Z_sparse,
        "beta_np": beta_np,
        "theta_np": theta_np,
        "family": family,
        "n_groups_list": n_groups_list,
        "re_structure": re_structure,
        "metadata": metadata,
        "weights_np": weights_np,
        "boot_type": boot_type,
        "max_iter": max_iter,
        "tol": tol,
        "max_outer_iter": max_outer_iter,
        "p": p,
        "lambda_template": lambda_template,
    }

    # Bootstrap iterations with optional parallelization
    if n_jobs == 1:
        # Sequential execution with tqdm progress bar
        boot_samples_list = []
        for i in tqdm(range(n_boot), desc="Bootstrap", disable=not verbose):
            result = _glmer_bootstrap_single_iteration(rng=rngs[i], **iter_args)
            boot_samples_list.append(result)
    else:
        # Parallel execution with joblib
        if verbose:
            print(f"Running {n_boot} bootstrap iterations with {n_jobs} workers...")
        boot_samples_list = Parallel(n_jobs=n_jobs, return_as="generator")(
            delayed(_glmer_bootstrap_single_iteration)(rng=rngs[i], **iter_args)
            for i in range(n_boot)
        )
        # Wrap generator with tqdm for progress
        boot_samples_list = list(
            tqdm(boot_samples_list, total=n_boot, desc="Bootstrap", disable=not verbose)
        )

    # Count failures
    n_failed = sum(1 for coef in boot_samples_list if np.any(np.isnan(coef)))

    # Stack bootstrap samples
    boot_samples = np.stack(boot_samples_list, axis=0)

    # Warn if many failures
    if n_failed > n_boot * 0.1:
        import warnings

        warnings.warn(
            f"Bootstrap: {n_failed}/{n_boot} iterations failed to converge. "
            f"Consider increasing max_iter or max_outer_iter.",
            RuntimeWarning,
        )

    # Compute confidence intervals (excluding NaN samples)
    valid_mask = ~np.any(np.isnan(boot_samples), axis=1)
    boot_samples_valid = boot_samples[valid_mask]
    n_valid = np.sum(valid_mask)

    # Check if we have enough valid samples
    if n_valid == 0:
        raise RuntimeError(
            "All bootstrap iterations failed to converge. "
            "Cannot compute confidence intervals. "
            f"Consider increasing max_outer_iter (currently {max_outer_iter}) "
            f"or max_iter (currently {max_iter})."
        )
    elif n_valid < 50:
        import warnings

        warnings.warn(
            f"Only {n_valid}/{n_boot} bootstrap iterations succeeded. "
            f"Confidence intervals may be unreliable. "
            "Consider increasing max_outer_iter or max_iter.",
            RuntimeWarning,
        )

    if ci_type == "percentile":
        ci_lower, ci_upper = bootstrap_ci_percentile(boot_samples_valid, level=level)
    elif ci_type == "basic":
        ci_lower, ci_upper = bootstrap_ci_basic(
            coef_obs, boot_samples_valid, level=level
        )
    else:  # bca
        # BCa requires jackknife - expensive for GLMMs
        # For now, fall back to percentile with a warning
        import warnings

        warnings.warn(
            "BCa intervals for GLMER require expensive jackknife computation. "
            "Falling back to percentile intervals.",
            RuntimeWarning,
        )
        ci_lower, ci_upper = bootstrap_ci_percentile(boot_samples_valid, level=level)

    return BootstrapResult(
        observed=coef_obs,
        boot_samples=boot_samples,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        param_names=X_names,
        n_boot=n_boot,
        ci_type=ci_type,
        level=level,
        term_types=["fixef"] * p,
    )


# =============================================================================
# LMER Bootstrap
# =============================================================================


def _simulate_from_lmer(
    rng: RNG,
    X: np.ndarray,
    Z: sp.csc_matrix,
    beta: np.ndarray,
    theta: np.ndarray,
    sigma: float,
    n_groups_list: list[int],
    re_structure: str,
    metadata: dict | None = None,
) -> np.ndarray:
    """Simulate response from fitted lmer model.

    Generates y* = Xβ + Zb* + ε* where:
    - b* ~ N(0, σ²ΛΛ') are simulated random effects
    - ε* ~ N(0, σ²I) are simulated residuals

    Args:
        rng: RNG object for random number generation.
        X: Fixed effects design matrix, shape (n, p).
        Z: Random effects design matrix, shape (n, q), scipy sparse CSC.
        beta: Fixed effects coefficients, shape (p,).
        theta: Variance parameters for Lambda.
        sigma: Residual standard deviation.
        n_groups_list: Number of groups per grouping factor.
        re_structure: Random effects structure type.
        metadata: Additional metadata for complex structures.

    Returns:
        Simulated response vector, shape (n,).
    """
    # Build Lambda from theta
    Lambda = build_lambda_sparse(theta, n_groups_list, re_structure, metadata)

    # Simulate spherical random effects: u* ~ N(0, I)
    q = Lambda.shape[0]
    rng_u, rng_eps = rng.split_one()
    u_star = rng_u.normal(shape=(q,))

    # Transform to b* = σΛu* ~ N(0, σ²ΛΛ')
    # Note: theta are relative to sigma, so we must scale by sigma
    b_star = sigma * (Lambda @ u_star)

    # Simulate residuals: ε* ~ N(0, σ²I)
    n = X.shape[0]
    eps_star = sigma * rng_eps.normal(shape=(n,))

    # Compute fitted + random effects + residuals
    # y* = Xβ + Zb* + ε*
    y_star = X @ beta + Z.toarray() @ b_star + eps_star

    return np.asarray(y_star)


def _lmer_bootstrap_single_iteration(
    rng: RNG,
    X_np: np.ndarray,
    Z_sparse: sp.csc_matrix,
    beta_np: np.ndarray,
    theta_np: np.ndarray,
    sigma: float,
    n_groups_list: list[int],
    re_structure: str,
    metadata: dict | None,
    method: str,
    lower_bounds: list[float],
    upper_bounds: list[float],
    max_iter: int,
    lambda_template,
    X_arr: np.ndarray,
    XtX: np.ndarray,
    n: int,
    p: int,
    n_params: int,
    which: str,
    group_names: list[str] | None,
    random_names: list[str] | None,
) -> np.ndarray:
    """Execute a single bootstrap iteration.

    This is a standalone function (not a closure) to enable joblib parallelization.
    All arguments are passed explicitly to avoid pickling issues.

    Args:
        rng: RNG object for random number generation.
        X_np: Fixed effects design matrix.
        Z_sparse: Random effects design matrix (sparse CSC).
        beta_np: Fixed effects coefficients.
        theta_np: Variance parameters (starting values).
        sigma: Residual standard deviation.
        n_groups_list: Number of groups per factor.
        re_structure: Random effects structure type.
        metadata: Model metadata.
        method: Estimation method ("REML" or "ML").
        lower_bounds: Lower bounds for theta optimization.
        upper_bounds: Upper bounds for theta optimization.
        max_iter: Maximum optimizer iterations.
        lambda_template: Pre-built Lambda template (or None).
        X_arr: X as array (pre-computed).
        XtX: X'X matrix (pre-computed).
        n: Number of observations.
        p: Number of fixed effects.
        n_params: Number of parameters to return.
        which: Which parameters ("fixef", "ranef", or "all").
        group_names: Names of grouping factors.
        random_names: Names of random effects.

    Returns:
        Array of bootstrap estimates, or NaN array if iteration failed.
    """
    try:
        # Parametric bootstrap: simulate from fitted model
        y_boot = _simulate_from_lmer(
            rng=rng,
            X=X_np,
            Z=Z_sparse,
            beta=beta_np,
            theta=theta_np,
            sigma=sigma,
            n_groups_list=n_groups_list,
            re_structure=re_structure,
            metadata=metadata,
        )

        # Build PLS invariants for this bootstrap sample
        # X'X is pre-computed (constant), only X'y changes with y_boot
        y_boot_arr = np.asarray(y_boot)
        Xty_boot = X_arr.T @ y_boot_arr
        pls_invariants = PLSInvariants(
            XtX=XtX,
            Xty=Xty_boot,
            X_jax=X_arr,
            y_jax=y_boot_arr,
        )

        # Deviance function for this bootstrap sample
        def deviance_fn_boot(theta_boot):
            return lmm_deviance_sparse(
                theta=theta_boot,
                X=X_np,
                Z=Z_sparse,
                y=y_boot,
                n_groups_list=n_groups_list,
                re_structure=re_structure,
                method=method,
                lambda_template=lambda_template,
                pls_invariants=pls_invariants,
                metadata=metadata,
            )

        # Optimize theta
        result = optimize_theta(
            objective=deviance_fn_boot,
            theta0=theta_np,
            lower=lower_bounds,
            upper=upper_bounds,
            rhobeg=2e-3,
            rhoend=2e-7,
            maxfun=max_iter,
            verbose=False,
        )

        if not result["converged"]:
            return np.full(n_params, np.nan)

        # Extract estimates at optimal theta
        theta_boot = result["theta"]
        Lambda_boot = build_lambda_sparse(
            theta_boot, n_groups_list, re_structure, metadata
        )
        pls_result_boot = solve_pls_sparse(
            X_np,
            Z_sparse,
            Lambda_boot,
            y_boot,
            pls_invariants=pls_invariants,
        )

        if which == "fixef":
            return pls_result_boot["beta"]

        # For ranef or all, need sigma_boot and variance components
        from bossanova.results.builders import theta_to_variance_components

        u_boot = pls_result_boot["u"]
        rss_boot = pls_result_boot["rss"]
        pwrss_boot = rss_boot + np.sum(u_boot**2)

        if method == "REML":
            sigma_boot = np.sqrt(pwrss_boot / (n - p))
        else:
            sigma_boot = np.sqrt(pwrss_boot / n)

        _, vc_values = theta_to_variance_components(
            theta=theta_boot,
            sigma=sigma_boot,
            group_names=group_names,
            random_names=random_names,
            re_structure=re_structure,
        )

        if which == "ranef":
            return np.array(vc_values)
        else:  # which == "all"
            return np.concatenate([pls_result_boot["beta"], np.array(vc_values)])

    except Exception:
        # Numerical failure: return NaN
        return np.full(n_params, np.nan)


def lmer_bootstrap(
    X: Array,
    Z: sp.csc_matrix | Array,
    y: Array,
    X_names: list[str],
    theta: Array,
    beta: Array,
    sigma: float,
    n_groups_list: list[int],
    re_structure: str,
    metadata: dict | None = None,
    lower_bounds: list[float] | None = None,
    n_boot: int = 999,
    seed: int | None = None,
    boot_type: Literal["parametric", "case"] = "parametric",
    ci_type: Literal["percentile", "basic", "bca"] = "percentile",
    level: float = 0.95,
    method: Literal["REML", "ML"] = "REML",
    max_iter: int = 10000,
    tol: float = 1e-8,
    verbose: bool = False,
    which: Literal["fixef", "ranef", "all"] = "fixef",
    group_names: list[str] | None = None,
    random_names: list[str] | None = None,
    n_jobs: int = 1,
) -> BootstrapResult:
    """Bootstrap inference for lmer parameters.

    Supports parallel execution via joblib for significant speedups on
    multi-core machines. Each bootstrap iteration requires a full PLS
    optimization, making parallelization highly beneficial.

    Bootstrap types:
    - parametric: Simulate y* from fitted model (y* = Xβ̂ + Zb* + ε*).
      Assumes the fitted model is correct. This is the standard approach
      for mixed models.
    - case: Resample entire groups (clusters) with replacement. More robust
      to model misspecification but less efficient. Note: Not yet implemented.

    Note:
        Residual bootstrap is not available for mixed models because the
        residual structure involves multiple variance components (within-group
        and between-group). Parametric bootstrap properly accounts for this
        hierarchical structure by simulating new random effects.

    Args:
        X: Fixed effects design matrix, shape (n, p).
        Z: Random effects design matrix, shape (n, q), scipy sparse CSC.
        y: Response vector, shape (n,).
        X_names: Fixed effects coefficient names.
        theta: Variance parameters from fitted model.
        beta: Fixed effects coefficients from fitted model.
        sigma: Residual standard deviation from fitted model.
        n_groups_list: Number of groups per grouping factor.
        re_structure: Random effects structure type.
        metadata: Additional metadata for complex structures.
        lower_bounds: Lower bounds for theta optimization. If None, uses 0 for all.
        n_boot: Number of bootstrap samples.
        seed: Random seed for reproducibility.
        boot_type: Type of bootstrap: "parametric" or "case".
        ci_type: Confidence interval type: "percentile", "basic", or "bca".
        level: Confidence level (e.g., 0.95 for 95% CI).
        method: Estimation method for refitting: "REML" or "ML".
        max_iter: Maximum optimizer iterations for each refit.
        tol: Convergence tolerance for optimizer.
        verbose: Print progress information.
        which: Which parameters to bootstrap:
            - "fixef": Fixed effects coefficients (default).
            - "ranef": Variance components (SDs and correlations).
            - "all": Both fixed effects and variance components.
        group_names: Grouping factor names (required if which="ranef" or "all").
        random_names: Random effect names (required if which="ranef" or "all").
        n_jobs: Number of parallel jobs. Default 1 (sequential).
            Use -1 for all available cores. Parallelization uses joblib
            with the loky backend for process-based parallelism.

    Returns:
        BootstrapResult with observed stats, bootstrap samples, and CIs.
        For which="ranef", param_names are variance component names
        (e.g., "Subject:Intercept_sd", "Subject:corr_Intercept:Days", "Residual_sd").
        For which="all", fixed effects come first, then variance components.

    Raises:
        ValueError: If boot_type is not "parametric" or "case".
        ValueError: If ci_type is not "percentile", "basic", or "bca".
        ValueError: If which="ranef" but group_names or random_names not provided.
        NotImplementedError: If boot_type="case" (not yet implemented).

    Examples:
        >>> # Parametric bootstrap for fixed effects
        >>> result = lmer_bootstrap(
        ...     X, Z, y, ["Intercept", "Days"], theta, beta, sigma,
        ...     n_groups_list=[18], re_structure="slope",
        ...     n_boot=999, boot_type="parametric"
        ... )
        >>> print(result.ci)

        >>> # Bootstrap for variance components
        >>> result = lmer_bootstrap(
        ...     X, Z, y, ["Intercept", "Days"], theta, beta, sigma,
        ...     n_groups_list=[18], re_structure="slope",
        ...     n_boot=999, which="ranef",
        ...     group_names=["Subject"], random_names=["Intercept", "Days"]
        ... )

    Warning:
        Bootstrap refitting can fail to converge for some samples. Convergence
        failures > 10% will trigger a warning. Failed samples are excluded from
        CI computation.
    """
    # Input validation
    if boot_type not in ("parametric", "case"):
        raise ValueError(f"boot_type must be 'parametric' or 'case', got {boot_type}")
    if ci_type not in ("percentile", "basic", "bca"):
        raise ValueError(
            f"ci_type must be 'percentile', 'basic', or 'bca', got {ci_type}"
        )
    if which not in ("fixef", "ranef", "all"):
        raise ValueError(f"which must be 'fixef', 'ranef', or 'all', got {which}")
    if which in ("ranef", "all") and (group_names is None or random_names is None):
        raise ValueError(
            "group_names and random_names are required when which='ranef' or 'all'"
        )
    if boot_type == "case":
        raise NotImplementedError(
            "case bootstrap for lmer is not yet implemented. "
            "Use boot_type='parametric' instead."
        )

    # Setup
    X_np = np.asarray(X)
    theta_np = np.asarray(theta)
    beta_np = np.asarray(beta)
    n, p = X_np.shape
    n_theta = len(theta_np)

    # Convert Z to sparse CSC if needed
    if not sp.isspmatrix_csc(Z):
        Z_sparse = sp.csc_matrix(np.asarray(Z))
    else:
        Z_sparse = Z

    if lower_bounds is None:
        lower_bounds = [0.0] * n_theta
    upper_bounds = [np.inf] * n_theta

    rng = RNG.from_seed(seed)

    # Compute observed values, param names, and term types based on which
    if which == "fixef":
        observed = np.asarray(beta_np)
        param_names = X_names
        term_types = ["fixef"] * p
        n_params = p
    elif which == "ranef":
        from bossanova.results.builders import theta_to_variance_components

        param_names, obs_values = theta_to_variance_components(
            theta=theta_np,
            sigma=sigma,
            group_names=group_names,
            random_names=random_names,
            re_structure=re_structure,
        )
        observed = np.asarray(obs_values)
        term_types = ["ranef"] * len(param_names)
        n_params = len(param_names)
    else:  # which == "all"
        from bossanova.results.builders import theta_to_variance_components

        vc_names, vc_values = theta_to_variance_components(
            theta=theta_np,
            sigma=sigma,
            group_names=group_names,
            random_names=random_names,
            re_structure=re_structure,
        )
        # Fixed effects first, then variance components
        param_names = list(X_names) + vc_names
        term_types = ["fixef"] * p + ["ranef"] * len(vc_names)
        observed = np.concatenate([np.asarray(beta_np), np.asarray(vc_values)])
        n_params = len(param_names)

    # Generate all RNGs upfront
    rngs = rng.split(n_boot)

    # ==========================================================================
    # Pre-compute invariants for optimization (PERFORMANCE CRITICAL)
    # ==========================================================================
    # Lambda template: caches sparsity pattern, only updates values per theta
    # This avoids rebuilding sparse matrix structure on every deviance evaluation
    try:
        lambda_template = build_lambda_template(n_groups_list, re_structure, metadata)
    except NotImplementedError:
        # Complex structures (nested/crossed) fall back to build_lambda_sparse
        lambda_template = None

    # Pre-compute X-related quantities that are constant across all iterations
    # X'X doesn't change (X is fixed), only X'y changes with each y_boot
    X_arr = np.asarray(X_np)
    XtX = X_arr.T @ X_arr

    # ==========================================================================
    # Bootstrap execution (sequential or parallel)
    # ==========================================================================
    # Common arguments for each iteration
    iter_args = dict(
        X_np=X_np,
        Z_sparse=Z_sparse,
        beta_np=beta_np,
        theta_np=theta_np,
        sigma=sigma,
        n_groups_list=n_groups_list,
        re_structure=re_structure,
        metadata=metadata,
        method=method,
        lower_bounds=lower_bounds,
        upper_bounds=upper_bounds,
        max_iter=max_iter,
        lambda_template=lambda_template,
        X_arr=X_arr,
        XtX=XtX,
        n=n,
        p=p,
        n_params=n_params,
        which=which,
        group_names=group_names,
        random_names=random_names,
    )

    if n_jobs == 1:
        # Sequential execution with tqdm progress bar
        boot_samples_list = []
        for i in tqdm(range(n_boot), desc="Bootstrap", disable=not verbose):
            result = _lmer_bootstrap_single_iteration(rng=rngs[i], **iter_args)
            boot_samples_list.append(result)
    else:
        # Parallel execution with joblib
        if verbose:
            print(f"Running {n_boot} bootstrap iterations with {n_jobs} workers...")

        # Use joblib.Parallel with tqdm progress
        # return_as="generator" allows tqdm to show progress
        boot_samples_list = Parallel(n_jobs=n_jobs, return_as="generator")(
            delayed(_lmer_bootstrap_single_iteration)(rng=rngs[i], **iter_args)
            for i in range(n_boot)
        )
        # Consume generator with tqdm progress bar
        boot_samples_list = list(
            tqdm(
                boot_samples_list,
                total=n_boot,
                desc="Bootstrap",
                disable=not verbose,
            )
        )

    # Count failures (NaN samples)
    n_failed = sum(1 for s in boot_samples_list if np.any(np.isnan(s)))

    # Stack bootstrap samples
    boot_samples = np.stack(boot_samples_list, axis=0)

    # Warn if many failures
    if n_failed > n_boot * 0.1:
        import warnings

        warnings.warn(
            f"Bootstrap: {n_failed}/{n_boot} iterations failed to converge. "
            f"Consider increasing max_iter or checking model specification.",
            RuntimeWarning,
        )

    # Compute confidence intervals (excluding NaN samples)
    valid_mask = ~np.any(np.isnan(boot_samples), axis=1)
    boot_samples_valid = boot_samples[valid_mask]

    if ci_type == "percentile":
        ci_lower, ci_upper = bootstrap_ci_percentile(boot_samples_valid, level=level)
    elif ci_type == "basic":
        ci_lower, ci_upper = bootstrap_ci_basic(
            observed, boot_samples_valid, level=level
        )
    else:  # bca
        # BCa requires jackknife - this is expensive for mixed models
        # For now, fall back to percentile with a warning
        import warnings

        warnings.warn(
            "BCa intervals not yet implemented for lmer. Using percentile instead.",
            UserWarning,
        )
        ci_lower, ci_upper = bootstrap_ci_percentile(boot_samples_valid, level=level)

    return BootstrapResult(
        observed=observed,
        boot_samples=boot_samples,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        param_names=param_names,
        n_boot=n_boot,
        ci_type=ci_type,
        level=level,
        term_types=term_types,
    )
