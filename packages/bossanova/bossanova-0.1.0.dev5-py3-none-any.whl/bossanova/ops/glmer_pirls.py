"""PIRLS (Penalized Iteratively Reweighted Least Squares) algorithm for GLMMs.

This module implements the PIRLS algorithm for fitting generalized linear mixed
models using Laplace approximation. The algorithm combines IRLS (from GLMs) with
penalized least squares (from LMMs).

PIRLS Algorithm:
================
For fixed variance components θ (theta):
    1. Initialize η from GLM fit
    2. Until convergence:
        a. Compute working weights: w = 1 / (V(μ) * (dη/dμ)²)
        b. Compute working response: z = η + (y - μ) * dη/dμ
        c. Solve weighted penalized least squares:
           [X'WX      X'WZΛ    ] [β]   [X'Wz  ]
           [Λ'Z'WX  Λ'Z'WZΛ + I] [u] = [Λ'Z'Wz]
        d. Update: η = Xβ + ZΛu
        e. Check convergence on |Δη|

GLMM Deviance (Laplace approximation):
======================================
    -2 log L ≈ sum(dev_resid) + log|Λ'Z'WZΛ + I| + ||u||²

where:
    - sum(dev_resid) = sum of GLM deviance residuals
    - log|Λ'Z'WZΛ + I| = log-determinant from Cholesky
    - ||u||² = penalty term for spherical random effects

Reference:
----------
lme4 external.cpp:
    - pwrssUpdate (lines 308-375)
MixedModels.jl generalizedlinearmixedmodel.jl:
    - pirls! function (lines 600-655)
    - deviance function (lines 84-109)
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

import numpy as np
import scipy.sparse as sp

from bossanova.ops.family import Family
from bossanova.ops.sparse_solver import sparse_cholesky

if TYPE_CHECKING:
    from bossanova.ops.lambda_builder import LambdaTemplate, PatternTemplate
    from bossanova.ops.sparse_solver import SparseFactorization

__all__ = [
    "compute_irls_quantities",
    "solve_weighted_pls_sparse",
    "glmm_deviance",
    "pirls_sparse",
    "glmm_deviance_objective",
    "glmm_deviance_at_fixed_theta_beta",
    "fit_glmm_pirls",
    "deriv12",
    "compute_hessian_vcov",
]


def compute_irls_quantities(
    y: np.ndarray,
    eta: np.ndarray,
    family: Family,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute IRLS working weights and working response.

    Args:
        y: Response values (n,)
        eta: Linear predictor (n,)
        family: GLM family object

    Returns:
        working_weights: IRLS weights w = 1 / (V(μ) * (dη/dμ)²)
        working_response: Pseudo-response z = η + (y - μ) * dη/dμ
    """
    # Compute μ from η via inverse link
    mu = np.asarray(family.link_inverse(eta))

    # Link derivative and variance
    deta_dmu = np.asarray(family.link_deriv(mu))
    var_mu = np.asarray(family.variance(mu))

    # Working weights (clip for numerical stability)
    working_weights = 1.0 / (var_mu * deta_dmu**2 + 1e-10)
    working_weights = np.clip(working_weights, 1e-10, 1e10)

    # Working response
    working_response = eta + (y - mu) * deta_dmu

    return working_weights, working_response


def solve_weighted_pls_sparse(
    X: np.ndarray,
    Z: sp.csc_matrix,
    Lambda: sp.csc_matrix,
    z: np.ndarray,
    weights: np.ndarray,
    beta_fixed: np.ndarray | None = None,
    ZL: sp.csc_matrix | None = None,
    factor_S22: "SparseFactorization | None" = None,
    factor_S: "SparseFactorization | None" = None,
    pattern_template: "PatternTemplate | None" = None,
) -> dict:
    """Solve weighted Penalized Least Squares for GLMM.

    Solves the weighted augmented system:
        [X'WX        X'WZΛ    ] [β]   [X'Wz  ]
        [Λ'Z'WX   Λ'Z'WZΛ + I ] [u] = [Λ'Z'Wz]

    using sparse Cholesky factorization.

    If beta_fixed is provided, solves only for u with beta held constant:
        [Λ'Z'WZΛ + I] [u] = [Λ'Z'W(z - Xβ)]

    This is critical for Stage 2 optimization where we need to evaluate
    deviance at arbitrary (theta, beta) points without PIRLS re-optimizing beta.

    Args:
        X: Fixed effects design matrix (n, p)
        Z: Random effects design matrix (n, q), scipy sparse CSC
        Lambda: Cholesky-like factor (q, q), scipy sparse CSC
        z: Working response (n,)
        weights: IRLS weights (n,)
        beta_fixed: If provided, solve only for u with beta fixed to this value.
        ZL: Pre-computed Z @ Lambda. If provided, avoids redundant computation
            when called repeatedly with same Z and Lambda (e.g., in PIRLS loop).
        factor_S22: Cached Cholesky factor for S22 block. If provided, uses
            cholesky_inplace() to update with new values (same sparsity pattern).
            This avoids expensive symbolic analysis on repeated calls.
        factor_S: Cached Cholesky factor for full augmented system S.
            Only used in full solve mode (when beta_fixed is None).
        pattern_template: PatternTemplate for preserving sparsity patterns.
            When provided, ensures S22 has consistent pattern for cross-theta
            caching. Required when using factor_S22 with cross-theta caching.

    Returns:
        Dictionary with keys:
        - beta: Fixed effects coefficients (p,)
        - u: Spherical random effects (q,)
        - logdet_L: Log-determinant of (Λ'Z'WZΛ + I)
        - fitted_z: Fitted working response Xβ + ZΛu
        - factor_S22: Cholesky factor for S22 (for caching)
        - factor_S: Cholesky factor for full system S (for caching, full mode only)
    """
    # Ensure CSC format
    if not sp.isspmatrix_csc(Z):
        Z = Z.tocsc()
    if not sp.isspmatrix_csc(Lambda):
        Lambda = Lambda.tocsc()

    n, p = X.shape
    q = Lambda.shape[0]

    # Create diagonal weight matrix (sparse)
    W = sp.diags(weights, format="csc")

    # Use pre-computed ZΛ if provided, otherwise compute it
    # When pattern_template is provided, use pattern-preserving computation
    if ZL is None:
        if pattern_template is not None:
            from bossanova.ops.lambda_builder import compute_zl_preserve_pattern

            ZL = compute_zl_preserve_pattern(Z, Lambda, pattern_template.ZL_pattern)
        else:
            ZL = Z @ Lambda

    # Bottom-right: Λ'Z'WZΛ + I (sparse) - needed for both modes
    # When pattern_template is provided, preserve sparsity pattern for caching
    if pattern_template is not None:
        from bossanova.ops.lambda_builder import compute_s22_preserve_pattern

        S22 = compute_s22_preserve_pattern(ZL, W, pattern_template.S22_pattern)
    else:
        ZLtWZL = ZL.T @ W @ ZL
        S22 = ZLtWZL + sp.eye(q, format="csc")

    # Compute log-determinant of S22 block (Λ'Z'WZΛ + I)
    if not sp.isspmatrix_csc(S22):
        S22 = S22.tocsc()

    # Use cached factor if provided, otherwise create new
    if factor_S22 is not None:
        # Reuse symbolic analysis, only do numeric factorization
        factor_S22.cholesky_inplace(S22)
    else:
        factor_S22 = sparse_cholesky(S22)
    logdet_L = factor_S22.logdet()

    if beta_fixed is not None:
        # U-only mode: solve [Λ'Z'WZΛ + I] [u] = [Λ'Z'W(z - Xβ)]
        # This matches lme4's approach in Stage 2 where beta is in the offset
        z_adjusted = z - X @ beta_fixed
        ZLtWz_adj = ZL.T @ (weights * z_adjusted)

        # Solve for u only
        u = factor_S22(ZLtWz_adj)
        beta = beta_fixed

        # Compute fitted working response
        fitted_z = X @ beta + ZL.toarray() @ u

        return {
            "beta": beta,
            "u": u,
            "logdet_L": float(logdet_L),
            "fitted_z": fitted_z,
            "factor_S22": factor_S22,
        }

    # Full solve mode: solve for both beta and u

    # Build augmented system components
    # Top-left: X'WX (dense, typically small)
    XtWX = X.T @ W @ X

    # Top-right: X'WZΛ (mixed)
    XtWZL = X.T @ W @ ZL.toarray()

    # Right-hand side
    XtWz = X.T @ (weights * z)
    ZLtWz = ZL.T @ (weights * z)

    # Build full augmented system
    S11 = sp.csc_matrix(XtWX)
    S12 = sp.csc_matrix(XtWZL)
    S = sp.bmat([[S11, S12], [S12.T, S22]], format="csc")

    rhs = np.concatenate([XtWz, ZLtWz])

    # Sparse Cholesky factorization with caching
    if factor_S is not None:
        # Reuse symbolic analysis, only do numeric factorization
        factor_S.cholesky_inplace(S)
    else:
        factor_S = sparse_cholesky(S)
    solution = factor_S(rhs)

    beta = solution[:p]
    u = solution[p:]

    # Compute fitted working response
    fitted_z = X @ beta + ZL.toarray() @ u

    return {
        "beta": beta,
        "u": u,
        "logdet_L": float(logdet_L),
        "fitted_z": fitted_z,
        "factor_S22": factor_S22,
        "factor_S": factor_S,
    }


def glmm_deviance(
    y: np.ndarray,
    mu: np.ndarray,
    family: Family,
    logdet: float,
    sqrL: float,
    prior_weights: np.ndarray | None = None,
) -> float:
    """Compute GLMM deviance via Laplace approximation.

    The Laplace approximation to -2 log L:
        deviance_GLMM = sum(dev_resid) + logdet + ||u||²

    Args:
        y: Response values (n,)
        mu: Fitted values μ = g⁻¹(η) (n,)
        family: GLM family
        logdet: Log-determinant log|Λ'Z'WZΛ + I|
        sqrL: Sum of squared spherical random effects ||u||²
        prior_weights: Prior weights for observations (n,). For binomial with
            proportions, this is the number of trials.

    Returns:
        GLMM deviance (scalar)
    """
    # Compute GLM deviance residuals
    dev_resids = np.asarray(family.deviance(y, mu))

    # Weight deviance residuals by prior weights
    if prior_weights is None:
        deviance_glm = np.sum(dev_resids)
    else:
        deviance_glm = np.sum(prior_weights * dev_resids)

    # Laplace approximation
    return float(deviance_glm + logdet + sqrL)


def pirls_sparse(
    X: np.ndarray,
    Z: sp.csc_matrix,
    Lambda: sp.csc_matrix,
    y: np.ndarray,
    family: Family,
    eta_init: np.ndarray | None = None,
    prior_weights: np.ndarray | None = None,
    beta_fixed: np.ndarray | None = None,
    max_iter: int = 30,
    tol: float = 1e-7,
    verbose: bool = False,
    factor_S22: "SparseFactorization | None" = None,
    factor_S: "SparseFactorization | None" = None,
    pattern_template: "PatternTemplate | None" = None,
) -> dict:
    """Penalized Iteratively Reweighted Least Squares using sparse operations.

    For fixed variance parameters encoded in Lambda, iteratively solves for β and u
    using weighted penalized least squares. This is the inner loop of GLMM optimization.

    Args:
        X: Fixed effects design matrix (n, p)
        Z: Random effects design matrix (n, q), scipy sparse
        Lambda: Cholesky-like factor from theta (q, q), scipy sparse
        y: Response vector (n,)
        family: GLM family (binomial, poisson)
        eta_init: Initial linear predictor (optional)
        prior_weights: Prior observation weights (n,). For binomial with
            proportions, this should be the number of trials.
        beta_fixed: If provided, solve only for u with beta held fixed.
            This is used in Stage 2 optimization to evaluate deviance at
            arbitrary (theta, beta) points without re-optimizing beta.
        max_iter: Maximum PIRLS iterations
        tol: Convergence tolerance on relative deviance change (1e-7 matches lme4)
        verbose: Print iteration info
        factor_S22: Cached Cholesky factor for S22 block (Λ'Z'WZΛ + I).
            If provided, reuses symbolic analysis across calls. Useful for
            caching across theta evaluations in the optimizer.
        factor_S: Cached Cholesky factor for full augmented system.
            Only used when beta_fixed is None (full solve mode).
        pattern_template: PatternTemplate for preserving sparsity patterns.
            When provided, ensures S22 has consistent pattern for cross-theta
            caching. This is required for cross-theta factor caching to work
            correctly when theta has boundary values (θ=0).

    Returns:
        Dictionary with keys:
        - beta: Fixed effects coefficients (p,)
        - u: Spherical random effects (q,)
        - eta: Final linear predictor (n,)
        - mu: Final fitted values (n,)
        - deviance: GLMM deviance at convergence
        - converged: Whether PIRLS converged
        - n_iter: Number of iterations
        - logdet_L: Log-determinant
        - factor_S22: Cholesky factor for S22 (for caching)
        - factor_S: Cholesky factor for full system (for caching, full mode only)
    """
    n, p = X.shape

    # Initialize prior weights
    if prior_weights is None:
        prior_weights = np.ones(n)
    else:
        prior_weights = np.asarray(prior_weights).ravel()

    # Initialize linear predictor
    if eta_init is None:
        if beta_fixed is not None:
            # When beta is fixed, initialize eta from beta
            eta = X @ beta_fixed
        else:
            # Use GLM initialization with prior weights (matches lme4's behavior)
            # For binomial: mustart = (weights * y + 0.5) / (weights + 1)
            mu_init = np.asarray(family.initialize(y, prior_weights))
            eta = np.asarray(family.link(mu_init))
    else:
        eta = eta_init.copy()

    # Initialize deviance tracking
    dev_old = np.inf
    converged = False
    max_step_halving = 20  # Match lme4's PIRLS step-halving limit

    # Track u for step-halving (needed when beta is fixed)
    u = np.zeros(Lambda.shape[0])

    # Pre-compute ZΛ once (constant during PIRLS iterations)
    ZL = Z @ Lambda

    # factor_S22 and factor_S are passed as parameters for cross-call caching
    # They will be updated in-place during iterations and returned for reuse

    for iteration in range(max_iter):
        eta_old = eta.copy()
        u_old = u.copy()

        # Compute IRLS quantities
        working_weights, working_response = compute_irls_quantities(y, eta, family)

        # Combine prior weights with IRLS working weights
        total_weights = prior_weights * working_weights

        # Solve weighted PLS (with beta_fixed if provided, reuse pre-computed ZL)
        # Pass cached factors and pattern_template to avoid repeated symbolic analysis
        pls_result = solve_weighted_pls_sparse(
            X,
            Z,
            Lambda,
            working_response,
            total_weights,
            beta_fixed=beta_fixed,
            ZL=ZL,
            factor_S22=factor_S22,
            factor_S=factor_S,
            pattern_template=pattern_template,
        )

        beta = pls_result["beta"]
        u = pls_result["u"]
        logdet_L = pls_result["logdet_L"]

        # Cache factors for next iteration (avoids repeated symbolic analysis)
        factor_S22 = pls_result.get("factor_S22")
        factor_S = pls_result.get("factor_S")

        # Update linear predictor: η = Xβ + ZΛu
        eta_new = X @ beta + ZL.toarray() @ u

        # Compute deviance for convergence check
        mu_new = np.asarray(family.link_inverse(eta_new))
        sqrL = np.sum(u**2)
        dev_new = glmm_deviance(y, mu_new, family, logdet_L, sqrL, prior_weights)

        # Step-halving if deviance increased
        n_halving = 0
        while (np.isnan(dev_new) or dev_new > dev_old) and n_halving < max_step_halving:
            n_halving += 1
            # Halve both eta and u steps
            eta_new = (eta_new + eta_old) / 2.0
            u = (u + u_old) / 2.0
            mu_new = np.asarray(family.link_inverse(eta_new))
            sqrL = np.sum(u**2)
            dev_new = glmm_deviance(y, mu_new, family, logdet_L, sqrL, prior_weights)

            if verbose:
                print(f"  Step-halving {n_halving}: deviance = {dev_new:.6f}")

        # Check convergence
        dev_change = np.abs(dev_new - dev_old)
        rel_change = dev_change / (np.abs(dev_new) + 1e-10)

        if verbose:
            print(
                f"PIRLS iter {iteration + 1}: "
                f"deviance = {dev_new:.6f}, "
                f"rel_change = {rel_change:.2e}"
            )

        if rel_change < tol:
            converged = True
            if verbose:
                print(f"PIRLS converged after {iteration + 1} iterations")
            break

        eta = eta_new
        dev_old = dev_new

    # Final values
    mu_final = np.asarray(family.link_inverse(eta))
    sqrL_final = np.sum(u**2)
    deviance = glmm_deviance(y, mu_final, family, logdet_L, sqrL_final, prior_weights)

    return {
        "beta": beta,
        "u": u,
        "eta": eta,
        "mu": mu_final,
        "deviance": float(deviance),
        "converged": converged,
        "n_iter": iteration + 1,
        "logdet_L": logdet_L,
        "factor_S22": factor_S22,
        "factor_S": factor_S,
    }


def glmm_deviance_objective(
    theta: np.ndarray,
    X: np.ndarray,
    Z: sp.csc_matrix,
    y: np.ndarray,
    family: Family,
    n_groups_list: list[int],
    re_structure: str,
    metadata: dict | None = None,
    prior_weights: np.ndarray | None = None,
    pirls_max_iter: int = 30,
    pirls_tol: float = 1e-7,
    verbose: bool = False,
    lambda_template: "LambdaTemplate | None" = None,
    factor_cache: dict | None = None,
    pattern_template: "PatternTemplate | None" = None,
) -> float:
    """Compute GLMM deviance for outer optimization.

    This is the objective function for BOBYQA optimization over theta.

    Args:
        theta: Cholesky factor elements (lower triangle, column-major)
        X: Fixed effects design matrix (n, p)
        Z: Random effects design matrix (n, q), scipy sparse
        y: Response vector (n,)
        family: GLM family (binomial, poisson)
        n_groups_list: Number of groups per grouping factor
        re_structure: Random effects structure type
        metadata: Additional RE metadata
        prior_weights: Prior observation weights
        pirls_max_iter: Maximum PIRLS iterations per theta evaluation
        pirls_tol: PIRLS convergence tolerance (1e-7 matches lme4)
        verbose: Print verbose output
        lambda_template: Optional pre-built template for efficient Lambda updates.
            If provided, uses update_lambda_from_template instead of build_lambda_sparse.
            This avoids rebuilding the sparsity pattern on each call (~10-15% speedup).
        factor_cache: Optional mutable dict for caching Cholesky factors across
            theta evaluations. Should contain keys 'factor_S22' and 'factor_S'.
            Pass an empty dict {} to enable caching; factors will be stored
            and reused across calls, avoiding repeated symbolic analysis.
        pattern_template: PatternTemplate for preserving sparsity patterns.
            Required for cross-theta factor caching. When provided, ensures S22
            has consistent sparsity pattern even when theta hits boundaries (θ=0).

    Returns:
        GLMM deviance (scalar) - the Laplace approximation of -2*logLik
    """
    from bossanova.ops.lambda_builder import (
        build_lambda_sparse,
        update_lambda_from_template,
    )

    # Build Lambda from theta (use template if provided for efficiency)
    if lambda_template is not None:
        Lambda = update_lambda_from_template(lambda_template, theta)
    else:
        Lambda = build_lambda_sparse(theta, n_groups_list, re_structure, metadata)

    # Extract cached factors if caching is enabled
    factor_S22 = factor_cache.get("factor_S22") if factor_cache is not None else None
    factor_S = factor_cache.get("factor_S") if factor_cache is not None else None

    # Run PIRLS to convergence (passing cached factors for symbolic reuse)
    pirls_result = pirls_sparse(
        X=X,
        Z=Z,
        Lambda=Lambda,
        y=y,
        family=family,
        prior_weights=prior_weights,
        max_iter=pirls_max_iter,
        tol=pirls_tol,
        verbose=verbose,
        factor_S22=factor_S22,
        factor_S=factor_S,
        pattern_template=pattern_template,
    )

    # Update cache with factors for next call
    if factor_cache is not None:
        factor_cache["factor_S22"] = pirls_result.get("factor_S22")
        factor_cache["factor_S"] = pirls_result.get("factor_S")

    return pirls_result["deviance"]


def glmm_deviance_at_fixed_theta_beta(
    theta: np.ndarray,
    beta: np.ndarray,
    X: np.ndarray,
    Z: sp.csc_matrix,
    y: np.ndarray,
    family: Family,
    n_groups_list: list[int],
    re_structure: str,
    metadata: dict | None = None,
    prior_weights: np.ndarray | None = None,
    pirls_max_iter: int = 30,
    pirls_tol: float = 1e-7,
    verbose: bool = False,
    eta_init: np.ndarray | None = None,
    lambda_template: "LambdaTemplate | None" = None,
    factor_cache: dict | None = None,
    pattern_template: "PatternTemplate | None" = None,
) -> float:
    """Compute GLMM deviance at fixed (theta, beta) by solving only for u.

    This is the Stage 2 objective function for joint (theta, beta) optimization.
    Unlike glmm_deviance_objective which optimizes beta via PIRLS, this function
    holds beta fixed and only solves for the random effects u.

    This matches lme4's approach in Stage 2 where beta is added to the offset
    before PIRLS runs, so PIRLS only solves for u.

    Args:
        theta: Cholesky factor elements (lower triangle, column-major)
        beta: Fixed effects coefficients (p,) - held constant
        X: Fixed effects design matrix (n, p)
        Z: Random effects design matrix (n, q), scipy sparse
        y: Response vector (n,)
        family: GLM family (binomial, poisson)
        n_groups_list: Number of groups per grouping factor
        re_structure: Random effects structure type
        metadata: Additional RE metadata
        prior_weights: Prior observation weights
        pirls_max_iter: Maximum PIRLS iterations per theta evaluation
        pirls_tol: PIRLS convergence tolerance (1e-7 matches lme4)
        verbose: Print verbose output
        eta_init: Initial linear predictor for PIRLS. If provided, used as
            starting point instead of X @ beta. This matches lme4's lp0
            mechanism where the full linear predictor from Stage 1
            (X*beta + Z*Lambda*u) is saved and restored for Stage 2.
        lambda_template: Optional pre-built template for efficient Lambda updates.
            If provided, uses update_lambda_from_template instead of build_lambda_sparse.
            This avoids rebuilding the sparsity pattern on each call (~10-15% speedup).
        factor_cache: Optional mutable dict for caching Cholesky factors across
            theta evaluations. Pass an empty dict {} to enable caching.
        pattern_template: PatternTemplate for preserving sparsity patterns.
            Required for cross-theta factor caching. When provided, ensures S22
            has consistent sparsity pattern even when theta hits boundaries (θ=0).

    Returns:
        GLMM deviance (scalar) at the exact (theta, beta) point
    """
    from bossanova.ops.lambda_builder import (
        build_lambda_sparse,
        update_lambda_from_template,
    )

    # Build Lambda from theta (use template if provided for efficiency)
    if lambda_template is not None:
        Lambda = update_lambda_from_template(lambda_template, theta)
    else:
        Lambda = build_lambda_sparse(theta, n_groups_list, re_structure, metadata)

    # Extract cached factors if caching is enabled
    factor_S22 = factor_cache.get("factor_S22") if factor_cache is not None else None
    factor_S = factor_cache.get("factor_S") if factor_cache is not None else None

    # Run PIRLS with beta fixed - only solves for u
    # If eta_init is provided, use it as starting point (lme4's lp0 mechanism)
    pirls_result = pirls_sparse(
        X=X,
        Z=Z,
        Lambda=Lambda,
        y=y,
        family=family,
        prior_weights=prior_weights,
        beta_fixed=beta,  # KEY: beta is fixed, PIRLS only solves for u
        eta_init=eta_init,  # Use Stage 1's full linear predictor if provided
        max_iter=pirls_max_iter,
        tol=pirls_tol,
        verbose=verbose,
        factor_S22=factor_S22,
        factor_S=factor_S,
        pattern_template=pattern_template,
    )

    # Update cache with factors for next call
    if factor_cache is not None:
        factor_cache["factor_S22"] = pirls_result.get("factor_S22")
        factor_cache["factor_S"] = pirls_result.get("factor_S")

    return pirls_result["deviance"]


def fit_glmm_pirls(
    X: np.ndarray,
    Z: sp.csc_matrix,
    y: np.ndarray,
    family: Family,
    n_groups_list: list[int],
    re_structure: str,
    metadata: dict | None = None,
    theta_init: np.ndarray | None = None,
    prior_weights: np.ndarray | None = None,
    max_outer_iter: int = 10000,
    pirls_max_iter: int = 30,
    pirls_tol: float = 1e-7,
    verbose: bool = False,
    two_stage: bool = True,
    lambda_template: "LambdaTemplate | None" = None,
) -> dict:
    """Fit GLMM using PIRLS with outer optimization over theta.

    Optimization strategy (matching lme4):
    - Stage 1: BOBYQA optimizes theta only, PIRLS solves for (beta, u) at each theta
    - Stage 2: Nelder-Mead optimizes [theta, beta] jointly, PIRLS only solves for u

    The two-stage approach matches lme4 exactly:
    - Stage 1 (nAGQ=0): Optimize theta via BOBYQA, with PIRLS finding optimal
      (beta, u) for each theta.
    - Stage 2 (nAGQ>0): Joint optimization of [theta, beta] via Nelder-Mead,
      where beta is held fixed in PIRLS (added to offset) so PIRLS only solves
      for u. This allows the optimizer to find the global (theta, beta) optimum.

    Args:
        X: Fixed effects design matrix (n, p)
        Z: Random effects design matrix (n, q), scipy sparse
        y: Response vector (n,)
        family: GLM family (binomial, poisson)
        n_groups_list: Number of groups per grouping factor
        re_structure: Random effects structure type
        metadata: Additional RE metadata
        theta_init: Initial theta values (optional)
        prior_weights: Prior observation weights
        max_outer_iter: Maximum BOBYQA iterations for Stage 1
        pirls_max_iter: Maximum PIRLS iterations per theta evaluation
        pirls_tol: PIRLS convergence tolerance (1e-7 matches lme4)
        verbose: Print optimization progress
        two_stage: Use two-stage optimization matching lme4 (default True)
        lambda_template: Optional pre-built template for efficient Lambda updates.
            If provided, uses this template instead of building a new one.
            This is useful for bootstrap where the same template can be reused.

    Returns:
        Dictionary with:
        - theta: Optimized theta parameters
        - beta: Fixed effects coefficients
        - u: Spherical random effects
        - eta: Linear predictor
        - mu: Fitted values
        - deviance: Final GLMM deviance
        - loglik: Laplace log-likelihood
        - converged: Whether optimizer converged
        - n_outer_iter: Number of outer iterations
        - n_func_evals: Number of deviance evaluations
        - pirls_converged: Whether final PIRLS converged
        - pirls_n_iter: Final PIRLS iterations
    """
    import nlopt

    from bossanova.ops.lambda_builder import (
        build_lambda_sparse,
        build_lambda_template,
        build_pattern_template,
    )
    from bossanova.optimize import optimize_theta

    n, p = X.shape

    # Initialize theta
    if theta_init is None:
        theta_init = _init_theta_glmm(n_groups_list, re_structure, metadata)

    n_theta = len(theta_init)

    # Pre-build lambda template for efficient updates during optimization
    # This caches the sparsity pattern and only updates values (~10-15% speedup)
    # Use provided template if available (e.g., from bootstrap caller)
    if lambda_template is None:
        try:
            lambda_template = build_lambda_template(
                n_groups_list, re_structure, metadata
            )
        except NotImplementedError:
            # Complex structures (nested/crossed) fall back to build_lambda_sparse
            lambda_template = None

    # Build pattern template for cross-theta caching
    # This is critical for matching lme4's behavior: sparsity pattern is fixed at
    # initialization and never changes during optimization, even when theta hits
    # boundaries (θ=0). Without this, CHOLMOD would use different permutations for
    # different patterns, causing numerical differences.
    pattern_template = None
    if lambda_template is not None:
        if not sp.isspmatrix_csc(Z):
            Z = Z.tocsc()
        pattern_template = build_pattern_template(Z, lambda_template)

    # =========================================================================
    # Stage 1: BOBYQA over theta only (matches lme4's nAGQ=0 stage)
    # =========================================================================
    # Cross-theta factor caching is ENABLED when pattern_template is available.
    # The pattern_template ensures S22 has a consistent sparsity pattern even when
    # theta hits boundaries (θ=0). This matches lme4's approach where the pattern
    # is fixed at initialization and never changes during optimization.
    #
    # Without pattern preservation, boundary theta values would cause:
    # - S22 at θ=[1,1,1] has 1062 nnz
    # - S22 at θ=[1.26,0,0] has 590 nnz (different pattern!)
    # - Different sparsity → different CHOLMOD permutation → numerical differences
    #
    # With pattern preservation, S22 always has the maximal pattern (1062 nnz).

    # Initialize factor cache for cross-theta caching (if pattern_template available)
    factor_cache_stage1 = {} if pattern_template is not None else None

    def theta_objective(theta):
        return glmm_deviance_objective(
            theta=theta,
            X=X,
            Z=Z,
            y=y,
            family=family,
            n_groups_list=n_groups_list,
            re_structure=re_structure,
            metadata=metadata,
            prior_weights=prior_weights,
            pirls_max_iter=pirls_max_iter,
            pirls_tol=pirls_tol,
            verbose=False,
            lambda_template=lambda_template,
            factor_cache=factor_cache_stage1,
            pattern_template=pattern_template,
        )

    # Set bounds: diagonal elements >= 0, off-diagonal unbounded
    theta_lower = _get_theta_lower_bounds(n_theta, re_structure, metadata)
    theta_upper = [float("inf")] * n_theta

    if verbose:
        print(f"Stage 1: Optimizing {n_theta} theta parameters with BOBYQA...")

    # Run Stage 1 with PDFO BOBYQA
    # Match lme4's minqa::bobyqa defaults (NOT optwrap's adj=TRUE settings)
    # minqa calculates: rhobeg = min(0.95, 0.2 * max(abs(par)))
    # For theta0=[1,1,...], this gives rhobeg=0.2
    # rhoend = 1e-6 * rhobeg = 2e-7
    rhobeg_stage1 = min(0.95, 0.2 * np.max(np.abs(theta_init)))
    stage1_result = optimize_theta(
        objective=theta_objective,
        theta0=theta_init,
        lower=theta_lower,
        upper=theta_upper,
        rhobeg=rhobeg_stage1,  # minqa default: min(0.95, 0.2*max(abs(par)))
        rhoend=1e-6 * rhobeg_stage1,  # minqa default: 1e-6 * rhobeg
        maxfun=max_outer_iter,
        verbose=verbose,
    )

    theta_stage1 = stage1_result["theta"]
    stage1_deviance = stage1_result["fun"]
    stage1_evals = stage1_result["n_evals"]
    stage1_converged = stage1_result["converged"]

    if verbose:
        print(
            f"  Stage 1 complete: deviance={stage1_deviance:.4f}, evals={stage1_evals}"
        )

    # Get beta from Stage 1 result
    Lambda_stage1 = build_lambda_sparse(
        theta_stage1, n_groups_list, re_structure, metadata
    )
    pirls_stage1 = pirls_sparse(
        X=X,
        Z=Z,
        Lambda=Lambda_stage1,
        y=y,
        family=family,
        prior_weights=prior_weights,
        max_iter=pirls_max_iter,
        tol=pirls_tol,
        verbose=False,
    )
    beta_stage1 = pirls_stage1["beta"]
    u_stage1 = pirls_stage1["u"]

    # Save full linear predictor from Stage 1 (lme4's lp0 mechanism)
    # This includes both fixed and random effects: η = Xβ + ZΛu
    # Used as starting point for Stage 2 PIRLS evaluations
    ZL_stage1 = Z @ Lambda_stage1
    eta_stage1 = X @ beta_stage1 + ZL_stage1.toarray() @ u_stage1

    # =========================================================================
    # Stage 2: Nelder-Mead over [theta, beta] jointly (if two_stage=True)
    # =========================================================================
    if two_stage:
        if verbose:
            print(
                f"Stage 2: Joint optimization of {n_theta} theta + {p} beta "
                "with Nelder-Mead..."
            )

        # Cross-theta caching is ENABLED when pattern_template is available.
        # Same pattern preservation approach as Stage 1.
        factor_cache_stage2 = {} if pattern_template is not None else None

        # Combined objective for joint [theta, beta] optimization
        # KEY: Uses glmm_deviance_at_fixed_theta_beta which holds beta fixed
        # and only solves for u via PIRLS. This matches lme4's Stage 2 exactly.
        # We pass eta_stage1 as initial linear predictor (lme4's lp0 mechanism).
        def joint_objective(params):
            """Deviance as function of combined [theta, beta] vector.

            Unlike Stage 1 where PIRLS optimizes both beta and u,
            Stage 2 holds beta fixed and PIRLS only solves for u.
            This allows the optimizer to find the joint (theta, beta) optimum.

            Uses eta_stage1 (the full linear predictor from Stage 1) as
            the starting point for PIRLS, matching lme4's lp0 mechanism.
            """
            theta = params[:n_theta]
            beta = params[n_theta:]

            # Enforce theta bounds (Nelder-Mead is unconstrained)
            for i, (t, lb) in enumerate(zip(theta, theta_lower)):
                if t < lb:
                    return 1e10  # Penalty for constraint violation

            # Compute deviance at this (theta, beta) by solving only for u
            # Pass eta_stage1 as initial linear predictor (lme4's lp0 mechanism)
            return glmm_deviance_at_fixed_theta_beta(
                theta=theta,
                beta=beta,
                X=X,
                Z=Z,
                y=y,
                family=family,
                n_groups_list=n_groups_list,
                re_structure=re_structure,
                metadata=metadata,
                prior_weights=prior_weights,
                pirls_max_iter=pirls_max_iter,
                pirls_tol=pirls_tol,
                verbose=False,
                eta_init=eta_stage1,  # lme4's lp0: full linear predictor from Stage 1
                lambda_template=lambda_template,
                factor_cache=factor_cache_stage2,
                pattern_template=pattern_template,
            )

        # Initial guess: [theta_stage1, beta_stage1]
        x0 = np.concatenate([theta_stage1, beta_stage1])
        n_params = len(x0)

        # Use NLopt's Nelder-Mead for Stage 2 (closer to lme4's implementation)
        # Match lme4's Nelder-Mead settings (lme4/R/optimizer.R:27-33)
        # FtolAbs=1e-5, FtolRel=1e-15, XtolRel=1e-7, maxfun=10000
        def nlopt_objective(params, grad):
            return joint_objective(params)

        opt2 = nlopt.opt(nlopt.LN_NELDERMEAD, n_params)
        opt2.set_min_objective(nlopt_objective)
        opt2.set_maxeval(10000)
        opt2.set_ftol_abs(1e-5)  # Match lme4's FtolAbs
        opt2.set_ftol_rel(1e-15)  # Match lme4's FtolRel
        opt2.set_xtol_rel(1e-7)  # Match lme4's XtolRel

        # Set bounds: theta >= lower_bounds, beta unbounded (-inf, inf)
        lower_bounds = theta_lower + [float("-inf")] * p
        upper_bounds = [float("inf")] * n_params
        opt2.set_lower_bounds(lower_bounds)
        opt2.set_upper_bounds(upper_bounds)

        try:
            x_opt = np.array(opt2.optimize(x0.tolist()))
            final_deviance = opt2.last_optimum_value()
            converged = opt2.last_optimize_result() > 0
            stage2_evals = opt2.get_numevals()
        except nlopt.RoundoffLimited:
            # Optimization stopped due to roundoff - use last values
            x_opt = x0
            final_deviance = joint_objective(x0)
            converged = True
            stage2_evals = 1

        theta_opt = x_opt[:n_theta]
        beta_opt = x_opt[n_theta:]
        total_evals = stage1_evals + stage2_evals

        if verbose:
            print(
                f"  Stage 2 complete: deviance={final_deviance:.4f}, "
                f"evals={stage2_evals}"
            )

        # Get final results using beta_fixed to ensure we return values at the optimum
        # Pass eta_stage1 as initial linear predictor (lme4's lp0 mechanism)
        Lambda = build_lambda_sparse(theta_opt, n_groups_list, re_structure, metadata)
        pirls_result = pirls_sparse(
            X=X,
            Z=Z,
            Lambda=Lambda,
            y=y,
            family=family,
            prior_weights=prior_weights,
            beta_fixed=beta_opt,  # Use optimized beta
            eta_init=eta_stage1,  # lme4's lp0: full linear predictor from Stage 1
            max_iter=pirls_max_iter,
            tol=pirls_tol,
            verbose=verbose,
        )
    else:
        # Single-stage: just use Stage 1 results
        theta_opt = theta_stage1
        final_deviance = stage1_deviance
        total_evals = stage1_evals
        converged = stage1_converged
        pirls_result = pirls_stage1

    # Compute log-likelihood from deviance
    loglik = -0.5 * final_deviance

    return {
        "theta": theta_opt,
        "beta": pirls_result["beta"],
        "u": pirls_result["u"],
        "eta": pirls_result["eta"],
        "mu": pirls_result["mu"],
        "deviance": final_deviance,
        "loglik": loglik,
        "converged": converged,
        "n_outer_iter": total_evals,
        "n_func_evals": total_evals,
        "pirls_converged": pirls_result["converged"],
        "pirls_n_iter": pirls_result["n_iter"],
        "logdet_L": pirls_result["logdet_L"],
    }


def _init_theta_glmm(
    n_groups_list: list[int],
    re_structure: str,
    metadata: dict | None = None,
) -> np.ndarray:
    """Initialize theta for GLMM fitting.

    Uses conservative defaults. Unlike LMMs, GLMMs work on the link scale
    so moment-based initialization is less useful.

    Args:
        n_groups_list: Number of groups per grouping factor.
        re_structure: Random effects structure type.
        metadata: Optional metadata dict containing 'random_names' or 're_terms'
            to determine correct number of theta parameters.

    Returns:
        Initial theta values.
    """
    if re_structure == "intercept":
        # One variance component per grouping factor
        return np.array([1.0] * len(n_groups_list))
    elif re_structure == "diagonal":
        # One variance component per RE term (uncorrelated slopes from || syntax)
        # Get number of terms from metadata
        n_terms = 1  # Default fallback
        if metadata:
            if "random_names" in metadata:
                n_terms = len(metadata["random_names"])
            elif "re_terms" in metadata:
                n_terms = len(metadata["re_terms"])
        return np.array([0.5] * n_terms)
    elif re_structure == "slope":
        # Cholesky factor: n_terms*(n_terms+1)/2 parameters
        # Get number of terms from metadata
        n_terms = 2  # Default: intercept + 1 slope
        if metadata:
            if "random_names" in metadata:
                n_terms = len(metadata["random_names"])
            elif "re_terms" in metadata:
                n_terms = len(metadata["re_terms"])
        # Build initial Cholesky: diagonal = [1.0, 0.5, 0.5, ...], off-diag = 0
        n_theta = n_terms * (n_terms + 1) // 2
        theta = np.zeros(n_theta)
        idx = 0
        for col in range(n_terms):
            for row in range(col, n_terms):
                if row == col:
                    theta[idx] = 1.0 if col == 0 else 0.5
                # Off-diagonal stays 0
                idx += 1
        return theta
    elif re_structure in ("crossed", "nested", "mixed"):
        # Crossed/nested/mixed: compute theta for each factor based on its structure
        re_structures_list = metadata.get("re_structures_list") if metadata else None

        if re_structures_list is None:
            # Fallback: assume all intercepts (one theta per factor)
            return np.array([1.0] * len(n_groups_list))

        # Compute theta for each factor based on its structure
        theta_list = []
        for factor_structure in re_structures_list:
            if factor_structure == "intercept":
                theta_list.append(1.0)
            elif factor_structure == "slope":
                # 2x2 Cholesky: [L00, L10, L11] = 3 params
                theta_list.extend([1.0, 0.0, 0.5])
            elif factor_structure == "diagonal":
                # Default to 2 terms (intercept + slope, uncorrelated)
                theta_list.extend([0.5, 0.5])
            else:
                theta_list.append(1.0)

        return np.array(theta_list)
    else:
        return np.array([1.0])


def _get_theta_lower_bounds(
    n_theta: int,
    re_structure: str,
    metadata: dict | None = None,
) -> list[float]:
    """Get lower bounds for theta parameters.

    Diagonal elements of Cholesky factor must be non-negative.
    Off-diagonal elements are unbounded.

    Args:
        n_theta: Number of theta parameters
        re_structure: Random effects structure type
        metadata: Optional metadata dict with 're_structures_list' for
            crossed/nested/mixed structures

    Returns:
        List of lower bounds
    """
    if re_structure in ("intercept", "diagonal"):
        # All theta are diagonal elements
        return [0.0] * n_theta
    elif re_structure == "slope":
        # Cholesky factor: diagonal >= 0, off-diagonal unbounded
        dim = int((-1 + np.sqrt(1 + 8 * n_theta)) / 2)
        bounds = []
        for col in range(dim):
            for row in range(col, dim):
                if row == col:
                    bounds.append(0.0)
                else:
                    bounds.append(float("-inf"))
        return bounds
    elif re_structure in ("crossed", "nested", "mixed"):
        # Crossed/nested/mixed: compute bounds for each factor based on its structure
        re_structures_list = metadata.get("re_structures_list") if metadata else None

        if re_structures_list is None:
            # Fallback: assume all intercepts (all bounds = 0)
            return [0.0] * n_theta

        bounds = []
        for factor_structure in re_structures_list:
            if factor_structure == "intercept":
                bounds.append(0.0)
            elif factor_structure == "slope":
                # 2x2 Cholesky: [L00, L10, L11]
                bounds.extend([0.0, float("-inf"), 0.0])
            elif factor_structure == "diagonal":
                bounds.extend([0.0, 0.0])
            else:
                bounds.append(0.0)

        return bounds
    else:
        # Conservative: all non-negative
        return [0.0] * n_theta


def deriv12(
    func: Callable[[np.ndarray], float],
    x: np.ndarray,
    delta: float = 1e-4,
    fx: float | None = None,
) -> dict:
    """Compute gradient and Hessian using central finite differences.

    This matches lme4's deriv12() function exactly (lme4/R/deriv.R).
    Uses simple central differences with step size delta.

    The Hessian is computed simultaneously with the gradient for efficiency:
    - Diagonal: H[j,j] = (f(x+δ) - 2f(x) + f(x-δ)) / δ²
    - Off-diag: H[i,j] = (f(x+δi+δj) - f(x+δi-δj) - f(x-δi+δj) + f(x-δi-δj)) / (4δ²)

    Args:
        func: Scalar function R^n -> R to differentiate.
        x: Point at which to compute derivatives, shape (n,).
        delta: Step size for finite differences (default 1e-4, matches lme4).
        fx: Optional pre-computed f(x) to avoid redundant evaluation.

    Returns:
        Dictionary with:
            - "gradient": First derivative vector, shape (n,)
            - "Hessian": Second derivative matrix, shape (n, n)

    Note:
        This is O(h²) accurate, matching lme4's approach. For higher accuracy
        (O(h⁸)), use compute_hessian_richardson from bossanova.stats.satterthwaite.
    """
    x = np.asarray(x, dtype=np.float64)
    n = len(x)

    if fx is None:
        fx = func(x)

    H = np.zeros((n, n), dtype=np.float64)
    g = np.zeros(n, dtype=np.float64)

    # Perturbed points
    x_add = x + delta
    x_sub = x - delta

    for j in range(n):
        # Evaluate at x + delta*e_j and x - delta*e_j
        x_plus_j = x.copy()
        x_plus_j[j] = x_add[j]
        f_add = func(x_plus_j)

        x_minus_j = x.copy()
        x_minus_j[j] = x_sub[j]
        f_sub = func(x_minus_j)

        # Diagonal Hessian element: (f(x+δ) - 2f(x) + f(x-δ)) / δ²
        H[j, j] = (f_add - 2.0 * fx + f_sub) / (delta**2)

        # Gradient: (f(x+δ) - f(x-δ)) / (2δ)
        g[j] = (f_add - f_sub) / (2.0 * delta)

        # Off-diagonal elements (upper triangle, then mirror)
        for i in range(j):
            # Four-point stencil for mixed partial
            x_pp = x.copy()
            x_pp[i] = x_add[i]
            x_pp[j] = x_add[j]

            x_pm = x.copy()
            x_pm[i] = x_add[i]
            x_pm[j] = x_sub[j]

            x_mp = x.copy()
            x_mp[i] = x_sub[i]
            x_mp[j] = x_add[j]

            x_mm = x.copy()
            x_mm[i] = x_sub[i]
            x_mm[j] = x_sub[j]

            # Mixed partial: (f++ - f+- - f-+ + f--) / (4δ²)
            H[i, j] = (func(x_pp) - func(x_pm) - func(x_mp) + func(x_mm)) / (
                4.0 * delta**2
            )
            H[j, i] = H[i, j]  # Symmetric

    return {"gradient": g, "Hessian": H}


def compute_hessian_vcov(
    theta: np.ndarray,
    beta: np.ndarray,
    X: np.ndarray,
    Z: sp.csc_matrix,
    y: np.ndarray,
    family: Family,
    n_groups_list: list[int],
    re_structure: str,
    metadata: dict | None = None,
    prior_weights: np.ndarray | None = None,
    pirls_max_iter: int = 30,
    pirls_tol: float = 1e-7,
    delta: float = 1e-4,
    eta_init: np.ndarray | None = None,
) -> tuple[np.ndarray, dict]:
    """Compute Hessian-based vcov for fixed effects.

    Matches lme4's use.hessian=TRUE approach:
    1. Compute numerical Hessian of deviance w.r.t. [theta, beta]
    2. Invert the Hessian
    3. Extract beta-beta block
    4. Symmetrize

    This uses lme4's deriv12() approach (simple central differences with
    delta=1e-4) for exact parity with R.

    Args:
        theta: Final theta (variance component) estimates
        beta: Final beta (fixed effect) estimates
        X: Fixed effects design matrix (n, p)
        Z: Random effects design matrix (n, q), scipy sparse
        y: Response vector (n,)
        family: GLM family (binomial, poisson)
        n_groups_list: Number of groups per grouping factor
        re_structure: Random effects structure type
        metadata: Additional RE metadata
        prior_weights: Prior observation weights
        pirls_max_iter: Maximum PIRLS iterations per deviance evaluation
        pirls_tol: PIRLS convergence tolerance
        delta: Finite difference step size (default 1e-4, matches lme4)
        eta_init: Initial linear predictor for PIRLS. If provided, used as
            starting point for all deviance evaluations. This provides
            numerical stability for models with large random effects.

    Returns:
        Tuple of:
            - vcov_beta: Variance-covariance matrix for beta, shape (p, p)
            - derivs: Dictionary with "gradient" and "Hessian" (for diagnostics)

    Notes:
        If the Hessian is not positive definite, this function returns the
        pseudo-inverse of the beta-beta block, with a warning.
    """
    import warnings

    n_theta = len(theta)

    # Combined parameter vector [theta, beta] - matches lme4 ordering
    params = np.concatenate([theta, beta])

    # Deviance function over [theta, beta]
    # Uses eta_init as starting point for PIRLS, providing stability for
    # models with large random effects (like intercept-only Poisson GLMMs).
    def deviance_fn(p: np.ndarray) -> float:
        t = p[:n_theta]
        b = p[n_theta:]
        return glmm_deviance_at_fixed_theta_beta(
            theta=t,
            beta=b,
            X=X,
            Z=Z,
            y=y,
            family=family,
            n_groups_list=n_groups_list,
            re_structure=re_structure,
            metadata=metadata,
            prior_weights=prior_weights,
            pirls_max_iter=pirls_max_iter,
            pirls_tol=pirls_tol,
            verbose=False,
            eta_init=eta_init,  # Pass through for stability
        )

    # Compute gradient and Hessian via deriv12 (matches lme4)
    derivs = deriv12(deviance_fn, params, delta=delta)
    H = derivs["Hessian"]

    # Invert Hessian with error handling
    try:
        H_inv = np.linalg.inv(H)
        bad_hessian = False
    except np.linalg.LinAlgError:
        # Singular Hessian - use pseudo-inverse
        H_inv = np.linalg.pinv(H)
        bad_hessian = True

    # Check positive definiteness via eigenvalues (lme4's checkHess approach)
    if not bad_hessian:
        eig_vals = np.linalg.eigvalsh(H_inv)
        if np.min(eig_vals) <= 0:
            bad_hessian = True

    if bad_hessian:
        warnings.warn(
            "Hessian is not positive definite. "
            "Consider using use_hessian=False for Schur complement-based vcov.",
            RuntimeWarning,
        )

    # Extract beta-beta block (drop first n_theta rows/cols)
    vcov_beta = H_inv[n_theta:, n_theta:]

    # Apply factor of 2 and symmetrize (matches lme4's forceSymmetric(h + t(h)))
    # The Hessian is of deviance = -2*loglik, so vcov = 2*solve(H)[beta, beta]
    # lme4's forceSymmetric(h + t(h)) is equivalent to 2*(h+h^T)/2 = h + h^T
    # Since our H_inv is already symmetric, this equals 2*H_inv
    vcov_beta = vcov_beta + vcov_beta.T  # This gives 2*vcov_beta since symmetric

    return vcov_beta, derivs
