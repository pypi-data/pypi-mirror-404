"""Core LMM operations: PLS solving and deviance computation.

This module implements the Penalized Least Squares (PLS) formulation for linear
mixed models, matching lme4's canonical approach.

The PLS system solves:
    minimize: ||y - X*β - Z*Λ*u||² + ||u||²

where:
- X is the fixed effects design matrix
- Z is the random effects design matrix
- Λ is the Cholesky-like factor from theta parameters
- u are spherical random effects (u ~ N(0, I))

Architecture:
- Uses scipy.sparse for sparse matrices and scikit-sparse for CHOLMOD
- JAX for dense linear algebra (after CHOLMOD factorization)
- Returns NumPy arrays for downstream processing

lme4 Algorithm Reference:
    lme4 factors only S22 = Λ'Z'ZΛ + I (not the full augmented system)
    and uses the Schur complement to solve for beta. See:
    - lme4/src/predModule.cpp lines 263-301 (updateDecomp)
    - lme4/src/predModule.cpp lines 189-203 (solve)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

# Conditional JAX import for Pyodide compatibility
try:
    import jax
    import jax.numpy as jnp
except ImportError:
    import numpy as jnp

    class _FakeJax:
        @staticmethod
        def jit(fn):
            return fn

    jax = _FakeJax()
import scipy.sparse as sp

from bossanova.ops.sparse_solver import sparse_cholesky

if TYPE_CHECKING:
    from bossanova.ops.lambda_builder import LambdaTemplate

__all__ = [
    "PLSInvariants",
    "compute_pls_invariants",
    "solve_pls_sparse",
    "lmm_deviance_sparse",
    "extract_variance_components",
]


# =============================================================================
# Pre-computed Invariants (computed once per model)
# =============================================================================


@dataclass
class PLSInvariants:
    """Pre-computed quantities that don't change during theta optimization.

    These are computed once when the model is set up and reused for every
    deviance evaluation during BOBYQA optimization.

    Attributes:
        XtX: Gram matrix X'X, shape (p, p). JAX array.
        Xty: Cross-product X'y, shape (p,). JAX array.
        X_jax: Fixed effects design matrix as JAX array, shape (n, p).
        y_jax: Response vector as JAX array, shape (n,).
    """

    XtX: jnp.ndarray
    Xty: jnp.ndarray
    X_jax: jnp.ndarray
    y_jax: jnp.ndarray


def compute_pls_invariants(X: np.ndarray, y: np.ndarray) -> PLSInvariants:
    """Pre-compute quantities that are constant during optimization.

    Call this once before the optimization loop to avoid redundant computation.
    X'X and X'y don't depend on theta, so computing them once saves work.

    Args:
        X: Fixed effects design matrix, shape (n, p).
        y: Response vector, shape (n,).

    Returns:
        PLSInvariants with pre-computed X'X, X'y, and JAX arrays.

    Examples:
        >>> X = np.random.randn(100, 3)
        >>> y = np.random.randn(100)
        >>> inv = compute_pls_invariants(X, y)
        >>> inv.XtX.shape
        (3, 3)
    """
    X_jax = jnp.asarray(X)
    y_jax = jnp.asarray(y)
    XtX = X_jax.T @ X_jax
    Xty = X_jax.T @ y_jax

    return PLSInvariants(XtX=XtX, Xty=Xty, X_jax=X_jax, y_jax=y_jax)


# =============================================================================
# JIT-Compiled Dense Operations (Pure JAX)
# =============================================================================


@jax.jit
def _compute_schur_complement(
    XtX: jnp.ndarray,
    XtZL: jnp.ndarray,
    S22_inv_XtZL_T: jnp.ndarray,
) -> jnp.ndarray:
    """Compute Schur complement of the augmented system.

    The Schur complement is: X'X - X'ZΛ * S22^{-1} * Λ'Z'X

    This is the (1,1) block of the inverse of the augmented system,
    and represents the "effective" precision of beta after accounting
    for random effects.

    Args:
        XtX: Fixed effects Gram matrix X'X, shape (p, p).
        XtZL: Cross-product X'ZΛ, shape (p, q).
        S22_inv_XtZL_T: S22^{-1} * (X'ZΛ)', from CHOLMOD, shape (q, p).

    Returns:
        Schur complement matrix, shape (p, p).
    """
    return XtX - XtZL @ S22_inv_XtZL_T


@jax.jit
def _solve_beta_and_u(
    schur: jnp.ndarray,
    Xty: jnp.ndarray,
    XtZL: jnp.ndarray,
    cu: jnp.ndarray,
    S22_inv_XtZL_T: jnp.ndarray,
) -> tuple[jnp.ndarray, jnp.ndarray]:
    """Solve for fixed effects (beta) and spherical random effects (u).

    Uses the Schur complement to solve the blocked system:
        [X'X      X'ZΛ  ] [β]   [X'y  ]
        [Λ'Z'X   S22    ] [u] = [Λ'Z'y]

    Algorithm:
        1. beta = schur^{-1} * (X'y - X'ZΛ * cu)  where cu = S22^{-1} * Λ'Z'y
        2. u = cu - S22^{-1} * Λ'Z'X * beta

    Args:
        schur: Schur complement matrix, shape (p, p).
        Xty: Cross-product X'y, shape (p,).
        XtZL: Cross-product X'ZΛ, shape (p, q).
        cu: Intermediate S22^{-1} * Λ'Z'y from CHOLMOD, shape (q,).
        S22_inv_XtZL_T: S22^{-1} * (X'ZΛ)' from CHOLMOD, shape (q, p).

    Returns:
        Tuple of (beta, u):
        - beta: Fixed effects coefficients, shape (p,).
        - u: Spherical random effects, shape (q,).
    """
    rhs_beta = Xty - XtZL @ cu
    beta = jnp.linalg.solve(schur, rhs_beta)
    u = cu - S22_inv_XtZL_T @ beta
    return beta, u


@jax.jit
def _compute_logdet_schur(schur: jnp.ndarray) -> jnp.ndarray:
    """Compute log-determinant of Schur complement via Cholesky.

    For REML estimation, we need log|X'V^{-1}X| which equals log|schur|.
    Using Cholesky: log|A| = 2 * sum(log(diag(chol(A)))).

    Args:
        schur: Schur complement matrix (positive definite), shape (p, p).

    Returns:
        Log-determinant as scalar.
    """
    RX = jnp.linalg.cholesky(schur)
    return 2.0 * jnp.sum(jnp.log(jnp.diag(RX)))


@jax.jit
def _compute_rss(
    y: jnp.ndarray,
    X: jnp.ndarray,
    ZL: jnp.ndarray,
    beta: jnp.ndarray,
    u: jnp.ndarray,
) -> jnp.ndarray:
    """Compute residual sum of squares.

    RSS = ||y - X*beta - ZΛ*u||²

    This is the squared norm of residuals after removing both
    fixed effects and (scaled) random effects.

    Args:
        y: Response vector, shape (n,).
        X: Fixed effects design matrix, shape (n, p).
        ZL: Random effects design ZΛ, shape (n, q).
        beta: Fixed effects coefficients, shape (p,).
        u: Spherical random effects, shape (q,).

    Returns:
        RSS as scalar.
    """
    residuals = y - X @ beta - ZL @ u
    return jnp.sum(residuals**2)


def solve_pls_sparse(
    X: np.ndarray,
    Z: sp.csc_matrix,
    Lambda: sp.csc_matrix,
    y: np.ndarray,
    pls_invariants: PLSInvariants | None = None,
) -> dict:
    """Solve Penalized Least Squares system using Schur complement.

    Uses lme4's algorithm: factor only S22 = Λ'Z'ZΛ + I, then use Schur
    complement to solve for beta. This avoids factoring the full augmented
    system.

    Algorithm (matching lme4/src/predModule.cpp):
        1. Factor S22 = Λ'Z'ZΛ + I via CHOLMOD
        2. Compute RZX = L^{-1} * Λ'Z'X (forward solve)
        3. Compute Schur = X'X - RZX' * RZX (rank update)
        4. Solve for beta via Schur complement
        5. Back-solve for u

    Memory efficiency:
        ZΛ is kept sparse throughout. For InstEval-scale data (73k obs × 4k
        groups), this uses ~50MB instead of ~2.4GB per iteration.

    Args:
        X: Fixed effects design matrix, shape (n, p).
        Z: Random effects design matrix, shape (n, q), scipy sparse CSC.
        Lambda: Cholesky-like factor, shape (q, q), scipy sparse CSC.
        y: Response vector, shape (n,).
        pls_invariants: Optional pre-computed invariants (X'X, X'y, JAX arrays).
            If provided, avoids redundant computation in optimization loop.
            Use compute_pls_invariants() to create this before the loop.

    Returns:
        Dictionary with keys:
        - beta: Fixed effects coefficients, shape (p,).
        - u: Spherical random effects, shape (q,).
        - logdet_L: Log-determinant of (Λ'Z'ZΛ + I).
        - rss: Residual sum of squares ||y - Xβ - ZΛu||².
        - logdet_RX: Log-determinant of Schur complement (for REML).

    Examples:
        >>> import numpy as np
        >>> import scipy.sparse as sp
        >>> n, p, q = 100, 3, 10
        >>> X = np.random.randn(n, p)
        >>> Z = sp.random(n, q, density=0.1, format='csc')
        >>> Lambda = sp.eye(q, format='csc')
        >>> y = np.random.randn(n)
        >>> result = solve_pls_sparse(X, Z, Lambda, y)
        >>> result['beta'].shape
        (3,)
        >>> result['u'].shape
        (10,)

    Notes:
        - Converts Z and Lambda to CSC format if needed (CHOLMOD requirement)
        - Uses CHOLMOD for numerically stable sparse Cholesky of S22
        - JAX JIT-compiled functions for small dense linear algebra operations
        - ZΛ stays sparse; cross-products use efficient sparse-dense ops
        - Returns RSS without penalty term (PWRSS = RSS + ||u||²)
    """
    # Ensure CSC format for CHOLMOD
    if not sp.isspmatrix_csc(Z):
        Z = Z.tocsc()
    if not sp.isspmatrix_csc(Lambda):
        Lambda = Lambda.tocsc()

    q = Lambda.shape[0]

    # Compute ZΛ (sparse @ sparse = sparse) - KEEP SPARSE throughout
    ZL = Z @ Lambda

    # Build S22 = Λ'Z'ZΛ + I (sparse) - the ONLY matrix we factor
    # Ensure CSC format for CHOLMOD (ZL.T @ ZL may produce CSR)
    ZLtZL = (ZL.T @ ZL).tocsc()
    S22 = ZLtZL + sp.eye(q, format="csc")

    # Sparse factorization of S22 (CHOLMOD for JAX, splu for NumPy)
    factor_S22 = sparse_cholesky(S22)
    logdet_L = factor_S22.logdet()

    # --- Cross-products using sparse-dense operations ---
    # These produce small dense arrays: (q, p) and (q,)
    # Use pre-computed invariants if provided, otherwise compute on the fly
    if pls_invariants is not None:
        X_jax = pls_invariants.X_jax
        y_jax = pls_invariants.y_jax
        XtX = pls_invariants.XtX
        Xty = pls_invariants.Xty
        # For sparse ops, we need numpy arrays
        X_np = np.asarray(X_jax)
        y_np = np.asarray(y_jax)
    else:
        X_np = X
        y_np = y
        X_jax = jnp.asarray(X)
        y_jax = jnp.asarray(y)
        XtX = X_jax.T @ X_jax
        Xty = X_jax.T @ y_jax

    # Compute theta-dependent cross-products via sparse-dense ops
    # ZL.T @ X: sparse (q,n) @ dense (n,p) -> dense (q,p) - efficient!
    # ZL.T @ y: sparse (q,n) @ dense (n,) -> dense (q,) - efficient!
    XtZL_np = (ZL.T @ X_np).T  # (p, q) - transpose for consistency
    ZLty_np = ZL.T @ y_np  # (q,)

    # Convert to JAX for downstream operations
    XtZL = jnp.asarray(XtZL_np)

    # Compute RZX = L^{-1} * (Λ'Z'X) via forward solve
    # This is factor_S22 solving S22 @ x = XtZL.T
    S22_inv_XtZL_T = factor_S22(XtZL_np.T)  # Shape: (q, p)
    S22_inv_XtZL_T_jax = jnp.asarray(S22_inv_XtZL_T)

    # Compute Schur complement via JIT-compiled function
    schur = _compute_schur_complement(XtX, XtZL, S22_inv_XtZL_T_jax)

    # Solve for cu = S22^{-1} * Λ'Z'y (intermediate for u)
    cu = factor_S22(ZLty_np)  # Shape: (q,)
    cu_jax = jnp.asarray(cu)

    # Solve for beta and u via JIT-compiled function
    beta, u = _solve_beta_and_u(schur, Xty, XtZL, cu_jax, S22_inv_XtZL_T_jax)

    # Compute log-determinant of Schur complement (for REML) via JIT
    logdet_RX = _compute_logdet_schur(schur)

    # Compute residual sum of squares using sparse matvec
    # RSS = ||y - X*beta - ZΛ*u||²
    # This is efficient: sparse (n,q) @ dense (q,) -> dense (n,)
    beta_np = np.asarray(beta)
    u_np = np.asarray(u)
    fitted_fixed = X_np @ beta_np  # dense (n,)
    fitted_random = ZL @ u_np  # sparse @ dense -> dense (n,)
    residuals = y_np - fitted_fixed - fitted_random
    rss = float(np.sum(residuals**2))

    # Convert back to numpy for return
    return {
        "beta": beta_np,
        "u": u_np,
        "logdet_L": float(logdet_L),
        "rss": rss,
        "logdet_RX": float(logdet_RX),
    }


def lmm_deviance_sparse(
    theta: np.ndarray,
    X: np.ndarray,
    Z: sp.csc_matrix,
    y: np.ndarray,
    n_groups_list: list[int],
    re_structure: str,
    method: str = "REML",
    lambda_template: "LambdaTemplate | None" = None,
    pls_invariants: PLSInvariants | None = None,
    metadata: dict | None = None,
) -> float:
    """Compute LMM deviance for optimization.

    The deviance is -2 * log-likelihood, profiled over β and σ².

    For ML:
        -2 log L = log|Λ'Z'ZΛ+I| + n*log(2π*PWRSS/n) + n

    For REML:
        -2 REML = log|Λ'Z'ZΛ+I| + log|X'V⁻¹X| + (n-p)*log(2π*PWRSS/(n-p)) + (n-p)

    Args:
        theta: Cholesky factor elements (lower triangle, column-major).
        X: Fixed effects design matrix, shape (n, p).
        Z: Random effects design matrix, shape (n, q), scipy sparse.
        y: Response vector, shape (n,).
        n_groups_list: Number of groups per grouping factor.
        re_structure: Random effects structure type.
            Options: "intercept", "slope", "diagonal", "nested", "crossed", "mixed"
        method: Estimation method, either "ML" or "REML".
        lambda_template: Optional pre-built template for efficient Lambda updates.
            If provided, uses update_lambda_from_template instead of build_lambda_sparse.
            This avoids rebuilding the sparsity pattern on each call.
        pls_invariants: Optional pre-computed invariants (X'X, X'y, JAX arrays).
            If provided, avoids redundant matrix computation in optimization loop.
            Use compute_pls_invariants() to create this before the loop.
        metadata: Optional metadata dict with structure information.
            Required for crossed/nested/mixed structures with non-intercept factors.
            Should contain 're_structures_list' specifying each factor's structure.

    Returns:
        Deviance value (scalar).

    Examples:
        >>> import numpy as np
        >>> import scipy.sparse as sp
        >>> # Simple random intercept model
        >>> theta = np.array([1.5])
        >>> X = np.random.randn(100, 2)
        >>> Z = sp.random(100, 10, density=0.1, format='csc')
        >>> y = np.random.randn(100)
        >>> dev = lmm_deviance_sparse(theta, X, Z, y, [10], "intercept", "REML")
        >>> dev > 0
        True

    Notes:
        - Requires lambda_builder module for building Λ from theta
        - Returns ML deviance if method="ML", REML criterion if method="REML"
        - Used as objective function in BOBYQA optimization
        - Pass lambda_template for ~10-20% speedup in optimization loop
        - Pass pls_invariants for additional speedup (avoids X'X, X'y computation)
    """
    from bossanova.ops.lambda_builder import (
        build_lambda_sparse,
        update_lambda_from_template,
    )

    n, p = X.shape

    # Build Lambda from theta (use template if provided)
    if lambda_template is not None:
        Lambda = update_lambda_from_template(lambda_template, theta)
    else:
        Lambda = build_lambda_sparse(theta, n_groups_list, re_structure, metadata)

    # Solve PLS (pass invariants if provided)
    result = solve_pls_sparse(X, Z, Lambda, y, pls_invariants=pls_invariants)
    u = result["u"]
    logdet_L = result["logdet_L"]
    rss = result["rss"]
    logdet_RX = result["logdet_RX"]

    # Penalized residual sum of squares
    pwrss = rss + np.sum(u**2)

    # Compute deviance
    if method == "ML":
        # ML deviance
        deviance = logdet_L + n * (1.0 + np.log(2.0 * np.pi * pwrss / n))
    elif method == "REML":
        # REML criterion
        deviance = (
            logdet_L
            + logdet_RX
            + (n - p) * (1.0 + np.log(2.0 * np.pi * pwrss / (n - p)))
        )
    else:
        raise ValueError(f"Unknown method: {method}. Use 'ML' or 'REML'.")

    return float(deviance)


def extract_variance_components(
    theta: np.ndarray,
    pwrss: float,
    n: int,
    p: int,
    re_structure: str,
    metadata: dict,
    method: str = "REML",
) -> dict:
    """Extract interpretable variance components from theta.

    Converts theta (Cholesky factor elements on relative scale) to
    variance, SD, and correlation parameters on the absolute scale.

    Args:
        theta: Cholesky factor elements (lower triangle, column-major).
        pwrss: Penalized residual sum of squares (RSS + ||u||²).
        n: Number of observations.
        p: Number of fixed effects.
        re_structure: Random effects structure type.
        metadata: Dictionary with RE structure metadata.
            Should contain 'random_names' for naming variance components.
        method: Estimation method ("ML" or "REML").

    Returns:
        Dictionary with variance components:
        - sigma: Residual standard deviation.
        - sigma2: Residual variance.
        - groups: Dict of variance components per grouping factor.

    Examples:
        >>> theta = np.array([1.5])  # tau/sigma for random intercept
        >>> pwrss = 1000.0
        >>> n, p = 100, 2
        >>> metadata = {'random_names': ['Subject'], 'n_groups': [10]}
        >>> vc = extract_variance_components(theta, pwrss, n, p, "intercept", metadata)
        >>> 'sigma' in vc
        True
        >>> 'groups' in vc
        True

    Notes:
        - For REML, σ² = PWRSS / (n - p)
        - For ML, σ² = PWRSS / n
        - Theta is on relative scale (divided by σ), so multiply to get absolute
        - Returns variance, SD, and correlations where applicable
    """
    from bossanova.ops.lambda_builder import theta_to_variance_params

    # Residual variance (profiled out)
    if method == "REML":
        sigma2 = pwrss / (n - p)
    else:  # ML
        sigma2 = pwrss / n

    sigma = np.sqrt(sigma2)

    # Initialize result
    result = {
        "sigma": float(sigma),
        "sigma2": float(sigma2),
        "groups": {},
    }

    # Extract group names from metadata
    group_names = metadata.get("random_names", ["Group"])

    # Dispatch based on structure
    if re_structure == "intercept":
        # Single variance parameter per group
        if len(theta) == 1:
            # Simple intercept
            tau_rel = theta[0]
            tau = tau_rel * sigma
            result["groups"][group_names[0]] = {
                "var": float(tau**2),
                "sd": float(tau),
            }
        else:
            # Multiple groups (crossed or nested intercepts)
            for i, tau_rel in enumerate(theta):
                tau = tau_rel * sigma
                group_name = group_names[i] if i < len(group_names) else f"Group{i + 1}"
                result["groups"][group_name] = {
                    "var": float(tau**2),
                    "sd": float(tau),
                }

    elif re_structure == "diagonal":
        # Uncorrelated slopes: one variance per RE dimension
        # theta = [L00, L11, L22, ...] on relative scale
        sigmas_rel, _ = theta_to_variance_params(theta, is_diagonal=True)
        sigmas = sigmas_rel * sigma

        # Typically diagonal structure has multiple RE terms per group
        # Store as separate variance components
        group_name = group_names[0] if group_names else "Group"
        result["groups"][group_name] = {}
        re_names = metadata.get("re_terms", [f"RE{i + 1}" for i in range(len(theta))])

        for i, (re_name, sig) in enumerate(zip(re_names, sigmas)):
            result["groups"][group_name][re_name] = {
                "var": float(sig**2),
                "sd": float(sig),
            }

    elif re_structure == "slope":
        # Correlated slopes: full variance-covariance matrix
        # theta = [L00, L10, L11, ...] (lower triangle of Cholesky)
        sigmas_rel, rhos = theta_to_variance_params(theta, is_diagonal=False)
        sigmas = sigmas_rel * sigma

        group_name = group_names[0] if group_names else "Group"
        re_names = metadata.get("re_terms", [f"RE{i + 1}" for i in range(len(sigmas))])

        result["groups"][group_name] = {}

        # Variances and SDs
        for i, (re_name, sig) in enumerate(zip(re_names, sigmas)):
            result["groups"][group_name][re_name] = {
                "var": float(sig**2),
                "sd": float(sig),
            }

        # Correlations (if any)
        if len(rhos) > 0:
            result["groups"][group_name]["corr"] = {}
            idx = 0
            for i in range(len(sigmas)):
                for j in range(i):
                    corr_name = f"{re_names[j]}:{re_names[i]}"
                    result["groups"][group_name]["corr"][corr_name] = float(rhos[idx])
                    idx += 1

    else:
        # Nested, crossed, mixed structures
        # Need more complex logic based on metadata
        # For now, return basic structure
        result["groups"]["Complex"] = {
            "note": f"Structure '{re_structure}' variance extraction not yet implemented"
        }

    return result
