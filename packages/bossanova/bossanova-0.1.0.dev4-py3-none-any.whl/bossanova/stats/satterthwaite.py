"""Satterthwaite degrees of freedom approximation for linear mixed models.

This module implements the Satterthwaite method for computing approximate
denominator degrees of freedom for t-tests of fixed effects in linear mixed models.

The key insight is to match moments of the variance estimator to a scaled chi-squared
distribution, allowing approximate inference when exact degrees of freedom are unavailable.

Mathematical Background
-----------------------
For a t-statistic t = β̂_j / SE(β̂_j), the denominator degrees of freedom is:

    df_j = 2 * (SE(β̂_j)²)² / Var(SE(β̂_j)²)

Where Var(SE(β̂_j)²) is computed via delta method:

    Var(Vcov[j,j]) ≈ g' · H⁻¹ · g

    g = ∂Vcov[j,j]/∂θ  (Jacobian row)
    H = ∂²deviance/∂θ²  (Hessian of deviance)

Numerical Methods
-----------------
This module provides two approaches for computing derivatives:

1. **Richardson extrapolation** - Uses iterative refinement of finite differences
   to achieve O(h^8) accuracy. Matches R's numDeriv package exactly.

2. **Central finite differences** - Standard O(h^2) method, simpler but less accurate.

References
----------
- Satterthwaite, F.E. (1946). An approximate distribution of estimates of variance
  components. Biometrics Bulletin, 2(6), 110-114.

- Fai, A.H. & Cornelius, P.L. (1996). Approximate F-tests of multiple degree of
  freedom hypotheses in generalized least squares analyses. Journal of Statistical
  Computation and Simulation, 54(4), 363-378.

- Gilbert, P. and Varadhan, R. (2019). numDeriv: Accurate Numerical Derivatives.
  R package version 2016.8-1.1.
"""

import warnings
from typing import Callable

import numpy as np
from scipy.stats import t as t_dist

__all__ = [
    "compute_gradient_richardson",
    "compute_jacobian_richardson",
    "compute_hessian_richardson",
    "compute_hessian_numerical",
    "compute_jacobian_numerical",
    "satterthwaite_df",
    "satterthwaite_df_for_contrasts",
    "satterthwaite_t_test",
    "compute_satterthwaite_summary_table",
]

# =============================================================================
# Numerical Differentiation - Richardson Extrapolation
# =============================================================================


def compute_gradient_richardson(
    func: Callable[[np.ndarray], float],
    x: np.ndarray,
    d: float = 1e-4,
    eps: float = 1e-4,
    r: int = 4,
    v: int = 2,
    zero_tol: float | None = None,
) -> np.ndarray:
    """Compute gradient using Richardson extrapolation.

    Matches numDeriv::grad() behavior exactly by using Richardson extrapolation
    to achieve high-order accuracy (O(h^(2r))) in numerical differentiation.

    The algorithm:
    1. Computes r gradient approximations using central differences with
       step sizes h, h/v, h/v², ..., h/v^(r-1)
    2. Applies Richardson extrapolation recursively to cancel truncation errors
    3. Returns the final extrapolated estimate

    Richardson extrapolation formula:
        A_{k,m} = (v^(2m) * A_{k+1,m-1} - A_{k,m-1}) / (v^(2m) - 1)

    where A_{k,0} is the k-th central difference approximation.

    Step size formula:
        h[i] = |d * x[i]| + eps * I(|x[i]| < zero_tol)

    This ensures:
    - Relative step for large parameters: h ≈ d * |x|
    - Absolute step for small parameters: h = eps

    Args:
        func: Scalar function R^n -> R to differentiate.
        x: Point at which to compute gradient, shape (n,).
        d: Relative step size multiplier (default 1e-4).
        eps: Absolute step size for small x values (default 1e-4).
        r: Number of Richardson iterations (default 4 gives O(h^8) accuracy).
        v: Step reduction factor between iterations (default 2).
        zero_tol: Threshold for "small" x values. If None, computed as
                  sqrt(machine_eps / 7e-7) ≈ 5.6e-5.

    Returns:
        Gradient vector of shape (n,).

    Notes:
        - With default r=4, achieves O(h^8) accuracy vs O(h^2) for simple central differences
        - Requires 2*r*n function evaluations (vs 2*n for simple central differences)
        - Matches numDeriv's default parameters exactly for lmerTest compatibility

    Examples:
        >>> def rosenbrock(x):
        ...     return (1 - x[0])**2 + 100 * (x[1] - x[0]**2)**2
        >>> x = np.array([1.0, 1.0])
        >>> grad = compute_gradient_richardson(rosenbrock, x)
    """
    n = len(x)
    x = np.asarray(x, dtype=np.float64)

    # Compute zero_tol if not provided (matches numDeriv)
    if zero_tol is None:
        zero_tol = np.sqrt(np.finfo(float).eps / 7e-7)

    # Compute step sizes for each dimension (matches numDeriv formula)
    h = np.abs(d * x) + eps * (np.abs(x) < zero_tol)

    # Storage for Richardson approximations
    # a[k, i] = k-th approximation for derivative of dimension i
    a = np.zeros((r, n), dtype=np.float64)

    # Compute r central difference approximations with decreasing step sizes
    for k in range(r):
        for i in range(n):
            # Central difference: (f(x+h) - f(x-h)) / (2h)
            x_plus = x.copy()
            x_minus = x.copy()
            x_plus[i] += h[i]
            x_minus[i] -= h[i]
            a[k, i] = (float(func(x_plus)) - float(func(x_minus))) / (2.0 * h[i])

        # Reduce step size for next iteration
        if k < r - 1:
            h = h / v

    # Apply Richardson extrapolation
    # For each refinement level m, combine approximations to cancel O(h^(2m)) error
    for m in range(1, r):
        coeff = v ** (2 * m)  # For central differences, error is in h^2, h^4, h^6, ...
        for k in range(r - m):
            # Richardson formula: higher-order estimate from two lower-order estimates
            a[k, :] = (coeff * a[k + 1, :] - a[k, :]) / (coeff - 1.0)

    # Return the final extrapolated gradient (a[0, :] has highest accuracy)
    return a[0, :]


def compute_jacobian_richardson(
    func: Callable[[np.ndarray], np.ndarray],
    x: np.ndarray,
    d: float = 1e-4,
    eps: float = 1e-4,
    r: int = 4,
    v: int = 2,
    zero_tol: float | None = None,
) -> np.ndarray:
    """Compute Jacobian using Richardson extrapolation.

    Matches numDeriv::jacobian() behavior exactly. For a vector-valued function
    f: R^n -> R^m, computes the Jacobian matrix J where J[i,j] = ∂f_i/∂x_j.

    Uses Richardson extrapolation on each column (partial derivatives w.r.t. each
    input variable) to achieve high-order accuracy.

    Args:
        func: Vector function R^n -> R^m to differentiate.
              Returns array of shape (m,) or multi-dimensional (*out_shape,).
        x: Point at which to compute Jacobian, shape (n,).
        d: Relative step size multiplier (default 1e-4).
        eps: Absolute step size for small x values (default 1e-4).
        r: Number of Richardson iterations (default 4).
        v: Step reduction factor (default 2).
        zero_tol: Threshold for small x values (default sqrt(eps/7e-7)).

    Returns:
        Jacobian array of shape (*out_shape, n) where out_shape = func(x).shape.
        For matrix-valued functions (e.g., Vcov matrix), returns shape (p, p, n).

    Notes:
        - Each column of the Jacobian is computed using Richardson extrapolation
        - For func: R^n -> R^(p×p), returns array of shape (p, p, n)
        - Matches numDeriv's row-major flattening convention
        - Requires 2*r*n function evaluations

    Examples:
        For Vcov(beta): R^k -> R^(p×p), the Jacobian has shape (p, p, k)
        where Jac[i, j, l] = ∂Vcov[i,j]/∂varpar[l]
    """
    n = len(x)
    x = np.asarray(x, dtype=np.float64)

    # Get output shape
    f0 = np.asarray(func(x), dtype=np.float64)
    out_shape = f0.shape

    # Compute zero_tol if not provided
    if zero_tol is None:
        zero_tol = np.sqrt(np.finfo(float).eps / 7e-7)

    # Compute step sizes
    h = np.abs(d * x) + eps * (np.abs(x) < zero_tol)

    # Storage for Jacobian: shape (*out_shape, n)
    jac = np.zeros((*out_shape, n), dtype=np.float64)

    # Compute each column of Jacobian (partial derivatives w.r.t. x[i])
    for i in range(n):
        # Storage for Richardson approximations for this column
        a = np.zeros((r, *out_shape), dtype=np.float64)

        # Current step size for this dimension
        h_curr = h[i]

        # Compute r central difference approximations
        for k in range(r):
            x_plus = x.copy()
            x_minus = x.copy()
            x_plus[i] += h_curr
            x_minus[i] -= h_curr

            f_plus = np.asarray(func(x_plus), dtype=np.float64)
            f_minus = np.asarray(func(x_minus), dtype=np.float64)

            a[k] = (f_plus - f_minus) / (2.0 * h_curr)

            # Reduce step size for next iteration
            if k < r - 1:
                h_curr = h_curr / v

        # Apply Richardson extrapolation
        for m in range(1, r):
            coeff = v ** (2 * m)
            for k in range(r - m):
                a[k] = (coeff * a[k + 1] - a[k]) / (coeff - 1.0)

        # Store final extrapolated result for this column
        jac[..., i] = a[0]

    return jac


def compute_hessian_richardson(
    func: Callable[[np.ndarray], float],
    x: np.ndarray,
    d: float = 1e-4,
    eps: float = 1e-4,
    r: int = 4,
    v: int = 2,
    zero_tol: float | None = None,
) -> np.ndarray:
    """Compute Hessian using Richardson extrapolation with genD method.

    Matches numDeriv::hessian() behavior exactly by using the same two-step
    approach as numDeriv's genD() function:

    1. First computes diagonal Hessian elements H[i,i] using Richardson extrapolation
    2. Then computes off-diagonal elements H[i,j] using a modified mixed partial
       formula that subtracts the diagonal contributions:

       H[i,j] = (f(x+h_i+h_j) - 2*f(x) + f(x-h_i-h_j)
                 - H[i,i]*h_i² - H[j,j]*h_j²) / (2*h_i*h_j)

    This formula is more stable than the standard 4-point mixed partial formula
    and better isolates the cross-derivative term from numerical noise.

    Args:
        func: Scalar function R^n -> R to differentiate.
        x: Point at which to compute Hessian, shape (n,).
        d: Relative step size multiplier (default 1e-4).
        eps: Absolute step size for small x values (default 1e-4).
        r: Number of Richardson iterations (default 4).
        v: Step reduction factor (default 2).
        zero_tol: Threshold for small x values (default sqrt(eps/7e-7)).

    Returns:
        Hessian matrix of shape (n, n).

    Notes:
        - Uses genD method exactly as in numDeriv R package
        - Diagonal elements computed with Richardson extrapolation
        - Off-diagonal elements use diagonal-subtracted formula
        - More accurate than simple finite differences for smooth functions
        - Requires 1 + r*n + (n*(n-1)/2)*2 function evaluations
        - Essential for matching lmerTest's Satterthwaite df computation

    The diagonal-subtracted formula works because:
        f(x+h_i+h_j) ≈ f(x) + h_i*f_i + h_j*f_j
                       + 0.5*h_i²*f_ii + 0.5*h_j²*f_jj + h_i*h_j*f_ij + ...

    Taking f(x+h_i+h_j) - 2*f(x) + f(x-h_i-h_j) gives:
        h_i²*f_ii + h_j²*f_jj + 2*h_i*h_j*f_ij + O(h^4)

    Subtracting the known diagonal terms H[i,i]*h_i² + H[j,j]*h_j² and
    dividing by 2*h_i*h_j isolates f_ij with O(h²) accuracy.
    """
    n = len(x)
    x = np.asarray(x, dtype=np.float64)

    # Compute zero_tol if not provided
    if zero_tol is None:
        zero_tol = np.sqrt(np.finfo(float).eps / 7e-7)

    # Compute step sizes
    h = np.abs(d * x) + eps * (np.abs(x) < zero_tol)

    # Function value at x (needed for off-diagonal formula)
    f0 = float(func(x))

    # Initialize Hessian
    H = np.zeros((n, n), dtype=np.float64)

    # STEP 1: Compute diagonal elements using Richardson extrapolation
    for i in range(n):
        # Storage for Richardson approximations
        a = np.zeros(r, dtype=np.float64)

        # Current step size
        h_curr = h[i]

        # Compute r approximations using central differences for second derivative
        for k in range(r):
            x_plus = x.copy()
            x_minus = x.copy()
            x_plus[i] += h_curr
            x_minus[i] -= h_curr

            # Second derivative: (f(x+h) - 2*f(x) + f(x-h)) / h²
            a[k] = (float(func(x_plus)) - 2.0 * f0 + float(func(x_minus))) / (h_curr**2)

            # Reduce step size for next iteration
            if k < r - 1:
                h_curr = h_curr / v

        # Apply Richardson extrapolation
        for m in range(1, r):
            coeff = v ** (2 * m)
            for k in range(r - m):
                a[k] = (coeff * a[k + 1] - a[k]) / (coeff - 1.0)

        # Store diagonal element
        H[i, i] = a[0]

    # STEP 2: Compute off-diagonal elements using diagonal-subtracted formula
    # This is the key difference from standard finite differences!
    for i in range(n):
        for j in range(i + 1, n):
            # Storage for Richardson approximations
            a = np.zeros(r, dtype=np.float64)

            # Current step sizes
            h_i_curr = h[i]
            h_j_curr = h[j]

            # Compute r approximations
            for k in range(r):
                # Evaluate at x + h_i + h_j and x - h_i - h_j
                x_pp = x.copy()
                x_pp[i] += h_i_curr
                x_pp[j] += h_j_curr

                x_mm = x.copy()
                x_mm[i] -= h_i_curr
                x_mm[j] -= h_j_curr

                # Diagonal-subtracted formula (matches numDeriv genD)
                # This isolates the mixed partial by removing diagonal contributions
                numerator = (
                    float(func(x_pp))
                    - 2.0 * f0
                    + float(func(x_mm))
                    - H[i, i] * h_i_curr**2
                    - H[j, j] * h_j_curr**2
                )
                a[k] = numerator / (2.0 * h_i_curr * h_j_curr)

                # Reduce step sizes for next iteration
                if k < r - 1:
                    h_i_curr = h_i_curr / v
                    h_j_curr = h_j_curr / v

            # Apply Richardson extrapolation
            for m in range(1, r):
                coeff = v ** (2 * m)
                for k in range(r - m):
                    a[k] = (coeff * a[k + 1] - a[k]) / (coeff - 1.0)

            # Store off-diagonal element (symmetry)
            H[i, j] = a[0]
            H[j, i] = a[0]

    return H


# =============================================================================
# Numerical Differentiation - Simple Finite Differences
# =============================================================================


def compute_hessian_numerical(
    func: Callable[[np.ndarray], float],
    x: np.ndarray,
    step_size: float | np.ndarray | None = None,
) -> np.ndarray:
    """Compute Hessian using central finite differences.

    Uses 2nd-order accurate central differences:
    - Diagonal: H[i,i] ≈ (f(x+h) - 2*f(x) + f(x-h)) / h^2
    - Off-diagonal: H[i,j] ≈ (f(x+h_i+h_j) - f(x+h_i-h_j) - f(x-h_i+h_j) + f(x-h_i-h_j)) / (4*h_i*h_j)

    This is a simpler alternative to Richardson extrapolation, trading accuracy
    for simplicity. For production use, prefer compute_hessian_richardson().

    Args:
        func: Function R^n -> R to differentiate (deviance function).
        x: Point at which to compute Hessian.
        step_size: Step size(s) for finite differences. Can be:
                  - None: Adaptive step size (0.01 * max(|x|, 0.1))
                  - Scalar: Same step size for all dimensions
                  - Array: Per-dimension step sizes

    Returns:
        Hessian matrix of shape (n, n).

    Notes:
        - More accurate than forward differences but less than Richardson
        - Requires O(n^2) function evaluations
        - Pragmatic step size balances truncation O(h^2) with roundoff O(eps*f/h^2)
    """
    n = len(x)
    x = np.asarray(x, dtype=np.float64)

    # Adaptive step size for central differences
    # For Hessian computation, we use a pragmatic approach:
    # h_i = scale_i * h_base where scale_i depends on parameter magnitude
    # and h_base is chosen for numerical stability with typical deviance functions
    #
    # Note: Optimal h for second derivatives is O(f^(1/4) * eps^(1/4)) but this
    # requires knowing function scale. We use a conservative fixed value that
    # works well for log-likelihood/deviance functions (~O(100-1000))
    if step_size is None:
        # Base step size for parameters O(1)
        # This balances truncation O(h^2) with roundoff O(eps*f/h^2)
        # For f~1000, eps~1e-16: optimal h ~ (1e-16*1000)^(1/4) ~ 0.003
        h_base = 0.01
        # Scale by parameter magnitude, with floor to handle small values
        step_size = h_base * np.maximum(np.abs(x), 0.1)
    elif np.isscalar(step_size):
        step_size = np.full(n, step_size, dtype=np.float64)
    else:
        step_size = np.asarray(step_size, dtype=np.float64)

    H = np.zeros((n, n), dtype=np.float64)
    f0 = float(func(x))

    # Diagonal elements: second derivative using central differences
    for i in range(n):
        h = step_size[i]
        x_plus = x.copy()
        x_minus = x.copy()
        x_plus[i] += h
        x_minus[i] -= h
        H[i, i] = (float(func(x_plus)) - 2 * f0 + float(func(x_minus))) / (h**2)

    # Off-diagonal elements: mixed partial derivatives using central differences
    for i in range(n):
        for j in range(i + 1, n):
            hi, hj = step_size[i], step_size[j]
            x_pp = x.copy()
            x_pp[i] += hi
            x_pp[j] += hj
            x_pm = x.copy()
            x_pm[i] += hi
            x_pm[j] -= hj
            x_mp = x.copy()
            x_mp[i] -= hi
            x_mp[j] += hj
            x_mm = x.copy()
            x_mm[i] -= hi
            x_mm[j] -= hj
            H[i, j] = (
                float(func(x_pp))
                - float(func(x_pm))
                - float(func(x_mp))
                + float(func(x_mm))
            ) / (4 * hi * hj)
            H[j, i] = H[i, j]  # Symmetry

    return H


def compute_jacobian_numerical(
    func: Callable[[np.ndarray], np.ndarray],
    x: np.ndarray,
    step_size: float | np.ndarray | None = None,
) -> np.ndarray:
    """Compute Jacobian using central finite differences.

    For func: R^n -> R^(p×p) (returning Vcov matrix), computes the derivative
    of each output element w.r.t. each input parameter.

    This is a simpler alternative to Richardson extrapolation. For production
    use, prefer compute_jacobian_richardson().

    Args:
        func: Function R^n -> R^(p×p) to differentiate (Vcov(beta) function).
        x: Point at which to compute Jacobian.
        step_size: Step size(s) for finite differences. Can be:
                  - None: Adaptive step size (0.001 * max(|x|, 0.1))
                  - Scalar: Same step size for all dimensions
                  - Array: Per-dimension step sizes

    Returns:
        Jacobian array of shape (*out_shape, n) where out_shape = func(x).shape.
        For Vcov(beta), this is (p, p, n).

    Notes:
        - Uses central differences for 2nd-order accuracy
        - Requires O(n) function evaluations
        - Step size balances truncation O(h^2) with roundoff O(eps*f/h)
    """
    n = len(x)
    x = np.asarray(x, dtype=np.float64)

    # Get output shape from f(x)
    f0 = np.asarray(func(x), dtype=np.float64)
    out_shape = f0.shape

    # Step size for central differences (first derivatives)
    # For Jacobian: truncation O(h^2), roundoff O(eps*f/h)
    # Similar pragmatic approach as Hessian but with smaller base step
    if step_size is None:
        h_base = 0.001  # Smaller than Hessian since first derivative is better behaved
        step_size = h_base * np.maximum(np.abs(x), 0.1)
    elif np.isscalar(step_size):
        step_size = np.full(n, step_size, dtype=np.float64)
    else:
        step_size = np.asarray(step_size, dtype=np.float64)

    # Jacobian: shape (*out_shape, n)
    jac = np.zeros((*out_shape, n), dtype=np.float64)

    # Central differences for each input dimension
    for i in range(n):
        h = step_size[i]
        x_plus = x.copy()
        x_minus = x.copy()
        x_plus[i] += h
        x_minus[i] -= h
        f_plus = np.asarray(func(x_plus), dtype=np.float64)
        f_minus = np.asarray(func(x_minus), dtype=np.float64)
        jac[..., i] = (f_plus - f_minus) / (2 * h)

    return jac


# =============================================================================
# Satterthwaite Degrees of Freedom
# =============================================================================


def satterthwaite_df(
    vcov_beta: np.ndarray,
    jacobian_vcov: np.ndarray,
    hessian_deviance: np.ndarray,
    min_df: float = 1.0,
    max_df: float = 1e6,
    tol: float = 1e-8,
) -> np.ndarray:
    """Compute Satterthwaite degrees of freedom for each fixed effect.

    Implements the Satterthwaite approximation for denominator degrees of freedom:

        df_j = 2 * (SE(β̂_j)²)² / Var(SE(β̂_j)²)

    Where Var(SE(β̂_j)²) is computed via the delta method using the Jacobian
    of Vcov(beta) w.r.t. variance parameters and the inverse Hessian of the
    deviance function.

    Args:
        vcov_beta: Variance-covariance matrix of fixed effects, shape (p, p).
        jacobian_vcov: Jacobian of Vcov(beta) w.r.t. variance parameters,
                       shape (p, p, k) where k = number of variance parameters.
        hessian_deviance: Hessian of deviance w.r.t. variance parameters,
                          shape (k, k).
        min_df: Minimum allowable df (default 1.0).
        max_df: Maximum allowable df (default 1e6).
        tol: Tolerance for determining positive eigenvalues in Hessian.

    Returns:
        Array of degrees of freedom for each fixed effect, shape (p,).

    Notes:
        - Uses Moore-Penrose pseudo-inverse for the Hessian to handle
          negative or near-zero eigenvalues (convergence issues)
        - Warns when negative eigenvalues are detected
        - Clips df to [min_df, max_df] range for numerical stability
        - Returns max_df when variance of variance is near zero

    Examples:
        >>> # After fitting lmer model and computing Hessian/Jacobian
        >>> df = satterthwaite_df(vcov_beta, jac, hess)
        >>> # df[0] is the denominator df for testing beta[0]
    """
    p = vcov_beta.shape[0]
    k = jacobian_vcov.shape[2]

    # Compute vcov_varpar = 2 * H^{-1} using Moore-Penrose pseudo-inverse
    # Only use positive eigenvalues (lmerTest approach)
    eig_vals, eig_vecs = np.linalg.eigh(hessian_deviance)

    # Check for negative eigenvalues (convergence issues)
    neg = eig_vals < -tol
    zero = (eig_vals > -tol) & (eig_vals < tol)
    pos = eig_vals > tol

    if np.sum(neg) > 0:
        # Warn about negative eigenvalues
        neg_count = int(np.sum(neg))
        eval_chr = "eigenvalues" if neg_count > 1 else "eigenvalue"
        warnings.warn(
            f"Model failed to converge with {neg_count} negative {eval_chr}. "
            f"Using Moore-Penrose pseudo-inverse for numerical stability.",
            UserWarning,
        )

    if np.sum(zero) > 0:
        # Warn about near-zero eigenvalues
        zero_count = int(np.sum(zero))
        eval_chr = "eigenvalues" if zero_count > 1 else "eigenvalue"
        warnings.warn(
            f"Model may not have converged with {zero_count} {eval_chr} close to zero. "
            f"Using Moore-Penrose pseudo-inverse for numerical stability.",
            UserWarning,
        )

    # Compute vcov_varpar = 2 * H^{-1}
    q = int(np.sum(pos))
    if q > 0:
        # Moore-Penrose: H^{-1} = V * D^{-1} * V^T where D contains only positive eigenvalues
        eig_vecs_pos = eig_vecs[:, pos]
        eig_vals_pos = eig_vals[pos]
        # Compute: V * diag(1/eigenvals) * V^T
        H_inv = eig_vecs_pos @ np.diag(1.0 / eig_vals_pos) @ eig_vecs_pos.T
        vcov_varpar = 2.0 * H_inv
    else:
        # All eigenvalues are negative/zero - use small regularization
        warnings.warn(
            "All Hessian eigenvalues are non-positive. "
            "Using regularized pseudo-inverse.",
            UserWarning,
        )
        # Add small regularization and use pinv as last resort
        vcov_varpar = 2.0 * np.linalg.pinv(hessian_deviance + np.eye(k) * 1e-6)

    # Compute df for each coefficient
    dfs = np.zeros(p, dtype=np.float64)

    for j in range(p):
        # Extract variance of j-th coefficient: var_j = Vcov(beta)[j, j]
        var_j = vcov_beta[j, j]
        var_j = np.abs(var_j)  # Ensure non-negative

        # Extract gradient of var_j w.r.t. variance parameters: g = Jac[j, j, :]
        grad_var_j = jacobian_vcov[j, j, :]

        # Compute variance of var_j using delta method:
        # Var(var_j) = g' * Vcov(varpar) * g
        var_of_var = grad_var_j @ vcov_varpar @ grad_var_j
        var_of_var = np.abs(var_of_var)  # Ensure non-negative

        # Check for numerical issues in denominator
        if var_of_var < 1e-10:
            # Denominator too small - use large df as fallback
            warnings.warn(
                f"Var(var_contrast) is near zero ({var_of_var:.2e}) for coefficient {j}. "
                f"Using maximum df={max_df}.",
                UserWarning,
            )
            dfs[j] = max_df
        else:
            # Satterthwaite formula: df = 2 * var^2 / Var(var)
            df_j = 2.0 * var_j**2 / var_of_var

            # Clip to reasonable range
            dfs[j] = np.clip(df_j, min_df, max_df)

    return dfs


def satterthwaite_df_for_contrasts(
    L: np.ndarray,
    vcov_beta: np.ndarray,
    vcov_varpar: np.ndarray,
    jac_list: list[np.ndarray],
    min_df: float = 1.0,
    max_df: float = 1e6,
) -> np.ndarray:
    """Compute Satterthwaite degrees of freedom for arbitrary contrasts.

    This generalizes `satterthwaite_df()` to handle arbitrary linear contrasts
    L @ β, not just individual coefficients. This is needed for emmeans where
    each EMM is a linear combination of coefficients.

    The Satterthwaite formula for contrast L is:

        df = 2 * var_contrast² / Var(var_contrast)

    Where:
        var_contrast = L @ Vcov(β) @ L.T
        grad[i] = L @ Jac_i @ L.T  (gradient w.r.t. variance parameter i)
        Var(var_contrast) = grad @ Vcov(varpar) @ grad

    Args:
        L: Contrast matrix, shape (n_contrasts, n_coef). Each row is a contrast.
            For a single contrast, shape can be (n_coef,).
        vcov_beta: Variance-covariance matrix of fixed effects, shape (p, p).
        vcov_varpar: Variance-covariance matrix of variance parameters, shape (k, k).
            This is 2 * H^{-1} where H is the Hessian of deviance.
        jac_list: List of k Jacobian matrices, each shape (p, p).
            jac_list[i] = ∂Vcov(β)/∂varpar_i.
        min_df: Minimum allowable df (default 1.0).
        max_df: Maximum allowable df (default 1e6).

    Returns:
        Array of degrees of freedom for each contrast, shape (n_contrasts,).
        For a single contrast (1D input), returns a scalar float.

    Examples:
        >>> # Compute df for EMMs where X_ref is the prediction matrix
        >>> df = satterthwaite_df_for_contrasts(
        ...     X_ref, vcov_beta, vcov_varpar, jac_list
        ... )
        >>> # df[i] is the denominator df for EMM i
    """
    # Handle 1D input (single contrast)
    L = np.atleast_2d(L)
    n_contrasts = L.shape[0]
    k = len(jac_list)

    dfs = np.zeros(n_contrasts, dtype=np.float64)

    for i in range(n_contrasts):
        Li = L[i, :]

        # Compute variance of contrast: var_contrast = L @ Vcov(β) @ L
        var_contrast = Li @ vcov_beta @ Li
        var_contrast = np.abs(var_contrast)  # Ensure non-negative

        # Compute gradient of var_contrast w.r.t. variance parameters
        # grad[j] = L @ Jac_j @ L
        grad_var_contrast = np.array([Li @ jac_list[j] @ Li for j in range(k)])

        # Compute variance of var_contrast using delta method:
        # Var(var_contrast) = grad @ Vcov(varpar) @ grad
        var_of_var = grad_var_contrast @ vcov_varpar @ grad_var_contrast
        var_of_var = np.abs(var_of_var)  # Ensure non-negative

        # Check for numerical issues in denominator
        if var_of_var < 1e-10:
            # Denominator too small - use large df as fallback
            dfs[i] = max_df
        else:
            # Satterthwaite formula: df = 2 * var^2 / Var(var)
            df_i = 2.0 * var_contrast**2 / var_of_var
            # Clip to reasonable range
            dfs[i] = np.clip(df_i, min_df, max_df)

    # Return scalar for single contrast input
    if n_contrasts == 1:
        return float(dfs[0])
    return dfs


def satterthwaite_t_test(
    beta: np.ndarray,
    se: np.ndarray,
    df: np.ndarray,
    conf_level: float = 0.95,
) -> dict[str, np.ndarray]:
    """Compute t-statistics, p-values, and confidence intervals.

    Uses Satterthwaite degrees of freedom for each coefficient to compute
    t-test statistics and p-values.

    Args:
        beta: Coefficient estimates, shape (p,).
        se: Standard errors, shape (p,).
        df: Satterthwaite degrees of freedom for each coefficient, shape (p,).
        conf_level: Confidence level for intervals (default 0.95 for 95% CI).

    Returns:
        Dictionary with:
        - 'statistic': t-statistics, shape (p,)
        - 'p_value': Two-tailed p-values, shape (p,)
        - 'ci_lower': Lower confidence bounds, shape (p,)
        - 'ci_upper': Upper confidence bounds, shape (p,)

    Examples:
        >>> # After computing df from satterthwaite_df()
        >>> se = np.sqrt(np.diag(vcov_beta))
        >>> results = satterthwaite_t_test(beta, se, df)
        >>> print(results['p_value'])  # Two-tailed p-values
    """
    p = len(beta)

    # Compute t-statistics
    t_stats = beta / se

    # Compute p-values (two-tailed)
    p_values = np.array(
        [2.0 * t_dist.sf(np.abs(t_stats[i]), df=df[i]) for i in range(p)]
    )

    # Compute confidence intervals
    alpha = 1.0 - conf_level
    t_crit = np.array([t_dist.ppf(1 - alpha / 2, df=df[i]) for i in range(p)])
    ci_lower = beta - t_crit * se
    ci_upper = beta + t_crit * se

    return {
        "statistic": t_stats,
        "p_value": p_values,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
    }


def compute_satterthwaite_summary_table(
    beta: np.ndarray,
    beta_names: list[str],
    vcov_beta: np.ndarray,
    vcov_varpar: np.ndarray,
    jac_list: list[np.ndarray],
) -> dict[str, list]:
    """Compute full coefficient table with Satterthwaite df and p-values.

    Computes t-statistics, degrees of freedom, and p-values for all
    fixed effects using Satterthwaite's approximation.

    This is a convenience function that combines `satterthwaite_df()`
    and `satterthwaite_t_test()` into a single summary table.

    Args:
        beta: Fixed effects estimates, shape (p,).
        beta_names: Names of fixed effects.
        vcov_beta: Variance-covariance matrix of beta, shape (p, p).
        vcov_varpar: Variance-covariance matrix of variance parameters.
        jac_list: List of Jacobian matrices, each shape (p, p).

    Returns:
        Dictionary with keys:
        - 'Parameter': List of parameter names
        - 'Estimate': Coefficient estimates
        - 'Std. Error': Standard errors
        - 'df': Satterthwaite degrees of freedom
        - 't value': t-statistics
        - 'Pr(>|t|)': Two-tailed p-values

    Notes:
        - Computes one t-test per fixed effect
        - Uses standard t-distribution for p-values
        - All computations vectorized for efficiency

    Examples:
        >>> # After fitting lmer and computing Hessian/Jacobian
        >>> table = compute_satterthwaite_summary_table(
        ...     beta, beta_names, vcov_beta, vcov_varpar, jac_list
        ... )
        >>> import pandas as pd
        >>> df = pd.DataFrame(table)
        >>> print(df)
    """
    p = len(beta)

    # Storage for results
    estimates = []
    std_errors = []
    dfs = []
    t_stats = []
    p_values = []

    # Compute for each coefficient
    for i in range(p):
        # Contrast vector: picks out i-th coefficient
        L = np.zeros(p)
        L[i] = 1.0

        # Compute variance of contrast: var_contrast = L' * Vcov(beta) * L
        var_contrast = L @ vcov_beta @ L
        var_contrast = np.abs(var_contrast)
        se = np.sqrt(var_contrast)

        # Compute gradient of var_contrast w.r.t. variance parameters
        # g_i = L' * Jac_i * L
        k = len(jac_list)
        grad_var_contrast = np.array([L @ jac_list[j] @ L for j in range(k)])

        # Compute variance of var_contrast using delta method:
        # Var(var_contrast) = grad' * Vcov(varpar) * grad
        var_of_var = grad_var_contrast @ vcov_varpar @ grad_var_contrast
        var_of_var = np.abs(var_of_var)

        # Check for numerical issues in denominator
        tol = 1e-10
        if var_of_var < tol:
            # Denominator too small - use large df as fallback
            warnings.warn(
                f"Var(var_contrast) is near zero ({var_of_var:.2e}). "
                f"Using maximum df=1e6 for this contrast.",
                UserWarning,
            )
            ddf = 1e6
        else:
            # Satterthwaite formula: ddf = 2 * var^2 / Var(var)
            ddf = 2.0 * var_contrast**2 / var_of_var

            # Clip to reasonable range
            ddf = np.clip(ddf, 1.0, 1e6)

        # Compute t-statistic
        estimate = beta[i]
        t_stat = estimate / se

        # Compute two-tailed p-value
        p_value = 2.0 * t_dist.sf(np.abs(float(t_stat)), df=float(ddf))

        # Store results
        estimates.append(float(estimate))
        std_errors.append(float(se))
        dfs.append(float(ddf))
        t_stats.append(float(t_stat))
        p_values.append(float(p_value))

    return {
        "Parameter": beta_names,
        "Estimate": estimates,
        "Std. Error": std_errors,
        "df": dfs,
        "t value": t_stats,
        "Pr(>|t|)": p_values,
    }
