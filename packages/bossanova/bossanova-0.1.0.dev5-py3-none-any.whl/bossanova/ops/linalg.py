"""Linear algebra utilities for ordinary least squares.

This module provides numerically stable OLS solvers using QR and SVD decomposition.

Architecture:
- Internal functions (`_qr_solve_core`, `_svd_solve_core`) implement the math
  using the backend abstraction layer (get_ops).
- JIT compilation is applied lazily via caching for the active backend.
- Public functions (`qr_solve`, `svd_solve`) wrap the internal functions and
  convert outputs to numpy arrays for user-facing APIs.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np

from bossanova._backend import get_backend
from bossanova.ops._get_ops import get_ops

# Type alias for arrays (could be np.ndarray or jax.Array)
Array = Any

__all__ = [
    "QRSolveResult",
    "SVDSolveResult",
    "qr_solve_jax",
    "svd_solve_jax",
    "qr_solve",
    "svd_solve",
]


# =============================================================================
# Internal JAX Result Containers
# =============================================================================


@dataclass
class QRSolveResult:
    """Result container for QR solve (JAX arrays).

    Attributes:
        coef: Coefficient estimates, shape (p,).
        vcov: Variance-covariance matrix, shape (p, p).
        sigma2: Residual variance (scalar).
        fitted: Fitted values, shape (n,).
        residuals: Residuals, shape (n,).
        df_resid: Residual degrees of freedom.
        rank: Rank of design matrix.
        R: R matrix from QR decomposition (upper triangular).
    """

    coef: Array
    vcov: Array
    sigma2: Array
    fitted: Array
    residuals: Array
    df_resid: int
    rank: int
    R: Array


@dataclass
class SVDSolveResult:
    """Result container for SVD solve (JAX arrays).

    Attributes:
        coef: Coefficient estimates, shape (p,).
        vcov: Variance-covariance matrix, shape (p, p).
        sigma2: Residual variance (scalar).
        fitted: Fitted values, shape (n,).
        residuals: Residuals, shape (n,).
        df_resid: Residual degrees of freedom.
        rank: Effective rank of design matrix.
        s: Singular values, shape (min(n, p),).
    """

    coef: Array
    vcov: Array
    sigma2: Array
    fitted: Array
    residuals: Array
    df_resid: int
    rank: int
    s: Array


# =============================================================================
# Core Functions (Backend-Agnostic)
# =============================================================================

# Cache for JIT-compiled functions per backend
_qr_solve_cache: dict[str, Any] = {}
_svd_solve_cache: dict[str, Any] = {}


def _make_qr_solve_fn(ops: Any) -> Any:
    """Create QR solve function with ops captured as closure constant.

    This ensures ops is captured at function creation time (not at JIT trace time),
    preserving JAX's ability to trace through to the underlying primitives efficiently.
    """
    xp = ops.np

    def _core(X: Array, y: Array) -> tuple[Array, Array, Array, Array, Array, Array]:
        """QR solve core computation.

        Returns tuple instead of dataclass for JIT compatibility.
        Order: (coef, vcov, sigma2, fitted, residuals, R)
        """
        n, p = X.shape

        # QR decomposition
        Q, R = ops.qr(X)

        # Solve R β = Q^T y
        Qty = Q.T @ y
        coef = ops.solve(R, Qty)

        # Fitted values and residuals
        fitted = X @ coef
        residuals = y - fitted

        # Residual variance (handle saturated models where df_resid=0)
        df_resid = n - p
        sigma2 = xp.where(df_resid > 0, xp.sum(residuals**2) / df_resid, 0.0)

        # Variance-covariance matrix: σ² (R^T R)^{-1}
        # Compute via backsolve to avoid explicit inversion
        R_inv = ops.solve(R, ops.eye(p))
        vcov = sigma2 * (R_inv @ R_inv.T)

        return coef, vcov, sigma2, fitted, residuals, R

    return ops.jit(_core)


def _get_qr_solve_fn() -> Any:
    """Get (potentially JIT-compiled) QR solve function for current backend."""
    backend = get_backend()
    if backend not in _qr_solve_cache:
        ops = get_ops()
        _qr_solve_cache[backend] = _make_qr_solve_fn(ops)
    return _qr_solve_cache[backend]


def _make_svd_solve_fn(ops: Any) -> Any:
    """Create SVD solve function with ops captured as closure constant.

    This ensures ops is captured at function creation time, preserving
    JAX's ability to trace through to the underlying primitives efficiently.
    """
    xp = ops.np

    def _core(
        X: Array, y: Array, rcond: float
    ) -> tuple[Array, Array, Array, Array, Array, Array, Array]:
        """SVD solve core computation.

        Returns tuple instead of dataclass for JIT compatibility.
        Order: (coef, vcov, sigma2, fitted, residuals, rank_float, s)

        Note: rank is returned as float for JIT compatibility, convert to int externally.
        """
        n, p = X.shape

        # SVD decomposition
        U, s, Vt = ops.svd(X, full_matrices=False)

        # Determine rank (number of non-zero singular values)
        threshold = rcond * s[0]
        rank_float = xp.sum(s > threshold).astype(xp.float64)

        # Solve using pseudoinverse for rank-deficient case
        # β̂ = V S^{-1} U^T y
        s_inv = xp.where(s > threshold, 1.0 / s, 0.0)
        coef = Vt.T @ (s_inv * (U.T @ y))

        # Fitted values and residuals
        fitted = X @ coef
        residuals = y - fitted

        # Residual variance (use effective rank)
        df_resid_float = n - rank_float
        sigma2 = xp.where(
            df_resid_float > 0, xp.sum(residuals**2) / df_resid_float, 0.0
        )

        # Variance-covariance matrix: σ² V S^{-2} V^T
        s_inv_sq = xp.where(s > threshold, 1.0 / (s**2), 0.0)
        vcov = sigma2 * (Vt.T @ xp.diag(s_inv_sq) @ Vt)

        return coef, vcov, sigma2, fitted, residuals, rank_float, s

    # JAX can handle rcond as a traced value (it's used in JAX-compatible operations).
    # JIT provides significant speedup on repeated calls.
    return ops.jit(_core)


def _get_svd_solve_fn() -> Any:
    """Get SVD solve function for current backend."""
    backend = get_backend()
    if backend not in _svd_solve_cache:
        ops = get_ops()
        _svd_solve_cache[backend] = _make_svd_solve_fn(ops)
    return _svd_solve_cache[backend]


# =============================================================================
# Internal API (Backend Arrays)
# =============================================================================


def qr_solve_jax(X: Array, y: Array) -> QRSolveResult:
    """Solve least squares via QR decomposition (returns backend arrays).

    This is the internal API for use within bossanova where backend arrays
    are preferred. For user-facing code, use `qr_solve()` instead.

    Args:
        X: Design matrix of shape (n, p), as backend array.
        y: Response variable of shape (n,), as backend array.

    Returns:
        QRSolveResult with backend arrays.
    """
    n, p = X.shape
    qr_fn = _get_qr_solve_fn()
    coef, vcov, sigma2, fitted, residuals, R = qr_fn(X, y)

    return QRSolveResult(
        coef=coef,
        vcov=vcov,
        sigma2=sigma2,
        fitted=fitted,
        residuals=residuals,
        df_resid=n - p,
        rank=p,
        R=R,
    )


def svd_solve_jax(X: Array, y: Array, rcond: float = 1e-15) -> SVDSolveResult:
    """Solve least squares via SVD (returns backend arrays).

    This is the internal API for use within bossanova where backend arrays
    are preferred. For user-facing code, use `svd_solve()` instead.

    Args:
        X: Design matrix of shape (n, p), as backend array.
        y: Response variable of shape (n,), as backend array.
        rcond: Relative condition number for rank determination.

    Returns:
        SVDSolveResult with backend arrays.
    """
    n, p = X.shape
    svd_fn = _get_svd_solve_fn()
    coef, vcov, sigma2, fitted, residuals, rank_float, s = svd_fn(X, y, rcond)

    # Convert rank to int (can't do inside JIT)
    rank = int(rank_float)
    df_resid = n - rank

    return SVDSolveResult(
        coef=coef,
        vcov=vcov,
        sigma2=sigma2,
        fitted=fitted,
        residuals=residuals,
        df_resid=df_resid,
        rank=rank,
        s=s,
    )


# =============================================================================
# Public API (NumPy Arrays)
# =============================================================================


def qr_solve(X: np.ndarray, y: np.ndarray) -> QRSolveResult:
    """Solve least squares via QR decomposition.

    QR decomposition is numerically stable and efficient for most problems.

    Args:
        X: Design matrix of shape (n, p).
        y: Response variable of shape (n,).

    Returns:
        QRSolveResult containing:

        - coef: Coefficient estimates, shape (p,)
        - vcov: Variance-covariance matrix, shape (p, p)
        - sigma2: Residual variance
        - fitted: Fitted values, shape (n,)
        - residuals: Residuals, shape (n,)
        - df_resid: Residual degrees of freedom
        - rank: Rank of design matrix
        - R: R matrix from QR decomposition (upper triangular)

    Note:
        Uses Householder QR decomposition:
        X = QR where Q is orthogonal and R is upper triangular.
        beta_hat = R^{-1} Q^T y, and Var(beta_hat) = sigma^2 (R^T R)^{-1}.

    Examples:
        >>> X = np.array([[1, 2], [1, 3], [1, 4]])
        >>> y = np.array([1.0, 2.0, 3.0])
        >>> result = qr_solve(X, y)
        >>> result.coef
        array([-1.,  1.])
    """
    # Convert to backend arrays, compute, convert back
    ops = get_ops()
    X_arr = ops.asarray(X)
    y_arr = ops.asarray(y)

    result = qr_solve_jax(X_arr, y_arr)

    return QRSolveResult(
        coef=np.asarray(result.coef),
        vcov=np.asarray(result.vcov),
        sigma2=float(result.sigma2),
        fitted=np.asarray(result.fitted),
        residuals=np.asarray(result.residuals),
        df_resid=result.df_resid,
        rank=result.rank,
        R=np.asarray(result.R),
    )


def svd_solve(X: np.ndarray, y: np.ndarray, rcond: float = 1e-15) -> SVDSolveResult:
    """Solve least squares via SVD (handles rank deficiency).

    SVD is more robust to rank deficiency and multicollinearity.

    Args:
        X: Design matrix of shape (n, p).
        y: Response variable of shape (n,).
        rcond: Relative condition number for rank determination.
            Singular values smaller than rcond * largest_singular_value
            are treated as zero.

    Returns:
        SVDSolveResult containing the same fields as QRSolveResult,
        plus `s` for singular values.

    Note:
        Uses Singular Value Decomposition: X = U S V^T.
        beta_hat = V S^{-1} U^T y (using pseudoinverse for rank deficiency).
        Var(beta_hat) = sigma^2 V S^{-2} V^T.

        Handles rank deficiency by identifying small singular values
        (< rcond * max(S)) and treating them as zero.

    Examples:
        >>> # Rank deficient case
        >>> X = np.array([[1, 2, 2], [1, 3, 3], [1, 4, 4]])  # col 3 = col 2
        >>> y = np.array([1.0, 2.0, 3.0])
        >>> result = svd_solve(X, y)
        >>> result.rank  # Will be 2, not 3
        2
    """
    # Convert to backend arrays, compute, convert back
    ops = get_ops()
    X_arr = ops.asarray(X)
    y_arr = ops.asarray(y)

    result = svd_solve_jax(X_arr, y_arr, rcond=rcond)

    return SVDSolveResult(
        coef=np.asarray(result.coef),
        vcov=np.asarray(result.vcov),
        sigma2=float(result.sigma2),
        fitted=np.asarray(result.fitted),
        residuals=np.asarray(result.residuals),
        df_resid=result.df_resid,
        rank=result.rank,
        s=np.asarray(result.s),
    )
