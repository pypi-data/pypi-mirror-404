"""Diagnostic statistics for linear models.

This module provides functions for computing residuals, influence measures,
and leverage statistics.
"""

import numpy as np
import polars as pl

from bossanova.ops._get_ops import get_ops

__all__ = [
    "compute_leverage",
    "compute_studentized_residuals",
    "compute_cooks_distance",
    "compute_vif",
]


def compute_leverage(
    X: np.ndarray,
    weights: np.ndarray | None = None,
    XtWX_inv: np.ndarray | None = None,
) -> np.ndarray:
    """Compute diagonal of hat matrix (leverage values).

    For the unweighted case (OLS), uses efficient QR decomposition.
    For the weighted case (GLM), can use pre-computed (X'WX)^{-1} to avoid
    redundant QR decomposition when this matrix is already available from IRLS.

    Args:
        X: Design matrix of shape (n, p).
        weights: Optional observation weights for weighted hat matrix (GLM).
        XtWX_inv: Optional pre-computed (X'WX)^{-1} of shape (p, p). When provided
            with weights, avoids QR decomposition by computing leverage directly
            as h_i = (W^{1/2} x_i)' (X'WX)^{-1} (W^{1/2} x_i). This is more
            efficient when (X'WX)^{-1} is already available (e.g., from IRLS).

    Returns:
        Diagonal of hat matrix (leverage values), shape (n,).

    Note:
        Unweighted case: H = X(X'X)^{-1} X', computed via QR as diag(H) = ||Q[i, :]||².
        Weighted case: H = W^{1/2} X (X'WX)^{-1} X' W^{1/2}.
        The sum of leverage values equals p (number of predictors).

    Examples:
        >>> X = np.array([[1, 2], [1, 3], [1, 4]])
        >>> h = compute_leverage(X)
        >>> np.sum(h)  # Should equal p (number of predictors)
        2.0

        >>> # GLM with pre-computed XtWX_inv (avoids redundant QR)
        >>> weights = np.array([1.0, 0.5, 0.8])
        >>> XtWX = X.T @ np.diag(weights) @ X
        >>> XtWX_inv = np.linalg.inv(XtWX)
        >>> h = compute_leverage(X, weights=weights, XtWX_inv=XtWX_inv)
    """
    ops = get_ops()
    xp = ops.np
    X_arr = ops.asarray(X)

    if weights is None:
        # Unweighted case (OLS)
        # QR decomposition (reduced)
        Q, _ = ops.qr(X_arr)

        # Leverage = row sums of Q²
        leverage = xp.sum(Q**2, axis=1)
    elif XtWX_inv is not None:
        # Weighted case with pre-computed (X'WX)^{-1} - optimized path
        # h_i = (W^{1/2} x_i)' (X'WX)^{-1} (W^{1/2} x_i)
        # Vectorized: h = diag(X_w @ XtWX_inv @ X_w.T) = rowsum((X_w @ XtWX_inv) * X_w)
        w_sqrt = xp.sqrt(ops.asarray(weights))
        X_weighted = w_sqrt[:, None] * X_arr
        XtWX_inv_arr = ops.asarray(XtWX_inv)

        # Efficient diagonal extraction: sum of element-wise product
        leverage = xp.sum((X_weighted @ XtWX_inv_arr) * X_weighted, axis=1)
    else:
        # Weighted case without pre-computed inverse - use QR
        # H = W^{1/2} X (X'WX)^{-1} X' W^{1/2}
        # Compute via W^{1/2} X and then QR
        w_sqrt = xp.sqrt(ops.asarray(weights))
        X_weighted = w_sqrt[:, None] * X_arr

        # QR decomposition of weighted X
        Q, _ = ops.qr(X_weighted)

        # Leverage = row sums of Q²
        leverage = xp.sum(Q**2, axis=1)

    return np.asarray(leverage)


def compute_studentized_residuals(
    residuals: np.ndarray,
    hat: np.ndarray,
    sigma: float,
) -> np.ndarray:
    """Compute internally studentized (standardized) residuals.

    Args:
        residuals: Raw residuals of shape (n,).
        hat: Leverage values (diagonal of hat matrix) of shape (n,).
        sigma: Residual standard error.

    Returns:
        Studentized residuals of shape (n,).

    Note:
        Formula: r_i / (σ * sqrt(1 - h_i)).
        Also called "internally studentized" or "standardized" residuals.
        They have approximately unit variance under model assumptions.

    Examples:
        >>> residuals = np.array([0.5, -0.3, 0.8])
        >>> hat = np.array([0.2, 0.3, 0.5])
        >>> sigma = 1.2
        >>> r_std = compute_studentized_residuals(residuals, hat, sigma)
    """
    # Handle hat=1 (perfect leverage) by returning NaN without warning
    denom = sigma * np.sqrt(1 - hat)
    return np.divide(
        residuals, denom, out=np.full_like(residuals, np.nan), where=denom != 0
    )


def compute_cooks_distance(
    residuals: np.ndarray,
    hat: np.ndarray,
    sigma: float,
    p: int,
) -> np.ndarray:
    """Compute Cook's distance for influence.

    Cook's distance measures the influence of each observation on
    the fitted coefficients.

    Args:
        residuals: Raw residuals of shape (n,).
        hat: Leverage values (diagonal of hat matrix) of shape (n,).
        sigma: Residual standard error.
        p: Number of parameters (including intercept).

    Returns:
        Cook's distances of shape (n,).

    Note:
        Cook's distance formula (matching R's cooks.distance()):
        D_i = (e_i² / (p * σ²)) * (h_i / (1 - h_i)²)
        where e_i is the raw residual, σ is sigma, h_i is leverage.

        Values > 1 are traditionally considered influential.
        More conservatively, D_i > 4/(n-p) is used.

    Examples:
        >>> D = compute_cooks_distance(residuals, hat, sigma=2.5, p=3)
        >>> influential = np.where(D > 1)[0]
    """
    # Use raw residual formula (equivalent and matches R exactly)
    # D_i = (e_i^2 / (p * sigma^2)) * (h_i / (1 - h_i)^2)
    # Handle hat=1 (perfect leverage) and sigma=0 (perfect fit) without warning
    denom = (p * sigma**2) * (1 - hat) ** 2
    numer = (residuals**2) * hat
    D = np.divide(numer, denom, out=np.full_like(residuals, np.nan), where=denom != 0)

    return np.array(D)


def compute_vif(X: np.ndarray, X_names: list[str]) -> pl.DataFrame:
    """Compute variance inflation factors.

    Args:
        X: Design matrix of shape (n, p), including intercept if present.
        X_names: Column names for design matrix.

    Returns:
        DataFrame with columns: [term, vif, ci_increase_factor]
        where ci_increase_factor = sqrt(vif).

    Note:
        VIF measures how much the variance of a coefficient is inflated
        due to multicollinearity. VIF_j = 1 / (1 - R²_j) where R²_j
        is from regressing predictor j on all other predictors.

        Excludes intercept column. Rules of thumb:
        VIF > 10: severe multicollinearity,
        VIF > 5: moderate multicollinearity,
        VIF < 5: acceptable.

    Examples:
        >>> X = np.array([[1, 2, 3], [1, 3, 4], [1, 4, 5]])
        >>> names = ['(Intercept)', 'x1', 'x2']
        >>> vif_df = compute_vif(X, names)
    """
    n, p = X.shape

    # Detect intercept column (all ones)
    is_intercept = np.all(X == X[0, :], axis=0)

    # Indices of non-intercept columns
    non_intercept_idx = np.where(~is_intercept)[0]

    if len(non_intercept_idx) == 0:
        # Only intercept, return empty DataFrame
        return pl.DataFrame({"term": [], "vif": [], "ci_increase_factor": []})

    # Extract non-intercept columns
    X_predictors = X[:, non_intercept_idx]
    predictor_names = [X_names[i] for i in non_intercept_idx]

    # If only one predictor, VIF = 1
    if X_predictors.shape[1] == 1:
        return pl.DataFrame(
            {
                "term": predictor_names,
                "vif": [1.0],
                "ci_increase_factor": [1.0],
            }
        )

    # Center predictors
    X_centered = X_predictors - np.mean(X_predictors, axis=0)

    # Compute VIF = diag(R^{-1}) where R is correlation matrix
    try:
        # Standardize centered predictors
        X_std = X_centered / np.std(X_centered, axis=0, ddof=1)
        # Correlation matrix: R = X_std' X_std / (n-1)
        R = X_std.T @ X_std / (n - 1)
        # VIF is diagonal of inverse correlation matrix
        R_inv = np.linalg.inv(R)
        vif_values = np.diag(R_inv)
    except np.linalg.LinAlgError:
        # Singular matrix, VIF undefined
        vif_values = np.full(len(predictor_names), np.inf)

    # CI increase factor is sqrt(VIF)
    ci_increase = np.sqrt(vif_values)

    return pl.DataFrame(
        {
            "term": predictor_names,
            "vif": vif_values,
            "ci_increase_factor": ci_increase,
        }
    )
