"""Sandwich (heteroscedasticity-consistent) covariance matrix estimators.

This module implements HC0-HC3 sandwich estimators for robust standard errors
when homoscedasticity cannot be assumed.

For linear models (lm):
    The sandwich corrects for arbitrary heteroscedasticity in the errors.

For generalized linear models (glm):
    The sandwich corrects for misspecification of the variance function.
    This is useful when overdispersion or other variance misspecification
    is suspected but you still want to use GLM point estimates.

References:
    - White, H. (1980). A Heteroskedasticity-Consistent Covariance Matrix
      Estimator and a Direct Test for Heteroskedasticity. Econometrica, 48(4), 817-838.
    - MacKinnon, J. G., & White, H. (1985). Some heteroskedasticity-consistent
      covariance matrix estimators with improved finite sample properties.
      Journal of Econometrics, 29(3), 305-325.
    - Zeileis, A. (2006). Object-oriented Computation of Sandwich Estimators.
      Journal of Statistical Software, 16(9), 1-16.

Examples:
    >>> from bossanova import lm, glm, load_dataset
    >>> df = load_dataset("credit")
    >>> # OLS with HC3 robust standard errors
    >>> model = lm("Balance ~ Income", data=df).fit().infer(errors="hetero")
    >>> # GLM with robust standard errors
    >>> model = glm("Default ~ Income", data=df, family="binomial").fit().infer(errors="hetero")
"""

from __future__ import annotations

__all__ = ["compute_hc_vcov", "compute_glm_hc_vcov"]

import numpy as np
from numpy.typing import NDArray


def compute_hc_vcov(
    X: NDArray[np.float64],
    residuals: NDArray[np.float64],
    XtX_inv: NDArray[np.float64],
    hc_type: str = "HC3",
) -> NDArray[np.float64]:
    """Compute heteroscedasticity-consistent covariance matrix.

    Implements the sandwich estimator: (X'X)^{-1} X' Ω X (X'X)^{-1}
    where Ω is a diagonal matrix of squared (possibly adjusted) residuals.

    Args:
        X: Design matrix, shape (n, p).
        residuals: OLS residuals, shape (n,).
        XtX_inv: (X'X)^{-1} from OLS, shape (p, p).
        hc_type: Type of HC estimator:
            - "HC0": White's original (no adjustment) - σ̂²ᵢ = e²ᵢ
            - "HC1": df correction - σ̂²ᵢ = e²ᵢ × n/(n-p)
            - "HC2": Leverage adjustment - σ̂²ᵢ = e²ᵢ / (1 - hᵢᵢ)
            - "HC3": Squared leverage (default, most conservative) - σ̂²ᵢ = e²ᵢ / (1 - hᵢᵢ)²

    Returns:
        Heteroscedasticity-consistent covariance matrix, shape (p, p).

    Raises:
        ValueError: If hc_type is not one of HC0, HC1, HC2, HC3.

    Notes:
        HC3 is recommended for small to medium samples as it's most robust
        to leverage points and provides better coverage in finite samples.

        The leverage (hat matrix diagonal) hᵢᵢ = xᵢ'(X'X)⁻¹xᵢ measures
        how much observation i influences its own prediction.

    Examples:
        >>> import numpy as np
        >>> n, p = 100, 3
        >>> X = np.random.randn(n, p)
        >>> y = X @ np.array([1, 2, 3]) + np.random.randn(n)
        >>> XtX_inv = np.linalg.inv(X.T @ X)
        >>> beta = XtX_inv @ X.T @ y
        >>> residuals = y - X @ beta
        >>> vcov_hc3 = compute_hc_vcov(X, residuals, XtX_inv, "HC3")
    """
    n, p = X.shape
    residuals = np.asarray(residuals, dtype=np.float64).ravel()

    if len(residuals) != n:
        raise ValueError(f"residuals length ({len(residuals)}) must match X rows ({n})")

    # Compute leverage (hat matrix diagonal): hᵢᵢ = xᵢ'(X'X)⁻¹xᵢ
    # Efficient computation: sum of element-wise products per row
    leverage = np.sum((X @ XtX_inv) * X, axis=1)

    # Compute omega (diagonal weights) based on HC type
    if hc_type == "HC0":
        # White's original: no adjustment
        omega = residuals**2
    elif hc_type == "HC1":
        # df correction: inflate by n/(n-p)
        omega = residuals**2 * (n / (n - p))
    elif hc_type == "HC2":
        # Leverage adjustment: divide by (1 - hᵢᵢ)
        omega = residuals**2 / (1 - leverage)
    elif hc_type == "HC3":
        # Squared leverage: divide by (1 - hᵢᵢ)²
        omega = residuals**2 / (1 - leverage) ** 2
    else:
        raise ValueError(
            f"Unknown hc_type: {hc_type!r}. Use 'HC0', 'HC1', 'HC2', or 'HC3'."
        )

    # Sandwich formula: (X'X)⁻¹ X' Ω X (X'X)⁻¹
    # where Ω = diag(omega)
    # Efficient: X' Ω X = X' (X ⊙ ω) where ⊙ is column-wise multiplication
    meat = X.T @ (X * omega[:, np.newaxis])  # X' Ω X
    vcov = XtX_inv @ meat @ XtX_inv

    return vcov


def compute_glm_hc_vcov(
    X: NDArray[np.float64],
    residuals: NDArray[np.float64],
    irls_weights: NDArray[np.float64],
    XtWX_inv: NDArray[np.float64],
    hc_type: str = "HC0",
) -> NDArray[np.float64]:
    """Compute heteroscedasticity-consistent covariance matrix for GLM.

    Implements the sandwich estimator for generalized linear models:
        (X'WX)^{-1} X'W Ω W X (X'WX)^{-1}

    where W are the IRLS weights and Ω accounts for variance misspecification.

    This is robust to misspecification of the GLM variance function (e.g.,
    overdispersion in Poisson or binomial models).

    Args:
        X: Design matrix, shape (n, p).
        residuals: Response residuals (y - μ), shape (n,).
        irls_weights: IRLS weights from GLM fit, shape (n,).
        XtWX_inv: (X'WX)^{-1} from GLM fit, shape (p, p).
        hc_type: Type of HC estimator:
            - "HC0": No small-sample adjustment (default for GLM)
            - "HC1": df correction

    Returns:
        Heteroscedasticity-consistent covariance matrix, shape (p, p).

    Notes:
        For GLM, HC0 is typically used as the default since the leverage
        adjustment in HC2/HC3 is less well-defined for weighted regression.

        The sandwich estimator protects against:
        - Overdispersion (Var(Y) > V(μ))
        - Underdispersion (Var(Y) < V(μ))
        - General variance misspecification

    Examples:
        >>> # After fitting a GLM
        >>> vcov_robust = compute_glm_hc_vcov(
        ...     model._X, model._residuals, model._irls_weights, model._XtWX_inv
        ... )
    """
    n, p = X.shape
    residuals = np.asarray(residuals, dtype=np.float64).ravel()
    irls_weights = np.asarray(irls_weights, dtype=np.float64).ravel()

    if len(residuals) != n:
        raise ValueError(f"residuals length ({len(residuals)}) must match X rows ({n})")
    if len(irls_weights) != n:
        raise ValueError(
            f"irls_weights length ({len(irls_weights)}) must match X rows ({n})"
        )

    # For GLM, the "score" contribution from observation i is:
    # s_i = w_i * (y_i - μ_i) * x_i
    # The meat of the sandwich is: Σ s_i s_i' = X' diag(w²e²) X
    #
    # We use squared weighted residuals as the omega
    omega = (irls_weights * residuals) ** 2

    # Apply HC correction if requested
    if hc_type == "HC0":
        # No adjustment
        pass
    elif hc_type == "HC1":
        # df correction
        omega = omega * (n / (n - p))
    else:
        raise ValueError(f"Unknown hc_type for GLM: {hc_type!r}. Use 'HC0' or 'HC1'.")

    # Sandwich formula: (X'WX)⁻¹ × Meat × (X'WX)⁻¹
    # where Meat = X' diag(ω) X
    meat = X.T @ (X * omega[:, np.newaxis])
    vcov = XtWX_inv @ meat @ XtWX_inv

    return vcov
