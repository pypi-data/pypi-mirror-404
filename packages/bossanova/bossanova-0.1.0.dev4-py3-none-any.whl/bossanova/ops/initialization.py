"""Moment-based initialization for LMM variance components.

Implements starting value strategies for theta parameters, following lme4's
variance decomposition approach. Good starting values dramatically reduce
convergence time for complex mixed models.

The moment-based method estimates variance components from the data:
1. Remove fixed effects via OLS
2. Compute group-level statistics (means, slopes)
3. Estimate variance components empirically
4. Convert to theta (Cholesky parameterization on relative scale)

Reference:
    lme4/R/modular.R lines 567-577 (mkLmerDevfun)
"""

import numpy as np
import scipy.sparse as sp

__all__ = [
    "compute_moment_init",
]


def compute_moment_init(
    X: np.ndarray,
    Z: sp.csc_matrix,
    y: np.ndarray,
    group_ids_list: list[np.ndarray],
    n_groups_list: list[int],
    re_structure: str,
    X_re: np.ndarray | None = None,
    metadata: dict | None = None,
) -> np.ndarray:
    """Compute moment-based starting values for theta.

    Dispatches to appropriate initializer based on re_structure.

    Args:
        X: Fixed effects design matrix, shape (n, p).
        Z: Random effects design matrix, shape (n, q), scipy sparse.
        y: Response vector, shape (n,).
        group_ids_list: List of group ID arrays (one per grouping factor).
            For simple models: single array of shape (n,) with values 0 to n_groups-1
            For crossed/nested: multiple arrays
        n_groups_list: Number of groups per grouping factor.
        re_structure: Random effects structure type.
            Options: "intercept", "slope", "diagonal", "crossed", "nested", "mixed"
        X_re: Random effects design matrix, shape (n, r).
            For slopes: typically (n, 2) with columns [ones, predictor]
            Not needed for intercept-only models.
        metadata: Optional metadata dict with structure information.
            For crossed/nested/mixed, should contain 're_structures_list'
            specifying each factor's structure (e.g., ['slope', 'intercept']).

    Returns:
        Initial theta values, shape varies by structure:
        - Intercept: (1,) or (n_factors,) for crossed/nested
        - Slope: (3,) for 2x2 Cholesky
        - Diagonal: (k,) for k RE per group
        - Crossed/nested with mixed: concatenation per factor

    Examples:
        >>> import numpy as np
        >>> import scipy.sparse as sp
        >>> # Simple random intercept
        >>> X = np.random.randn(100, 2)
        >>> Z = sp.random(100, 10, density=0.1, format='csc')
        >>> y = np.random.randn(100)
        >>> group_ids = [np.repeat(np.arange(10), 10)]
        >>> theta = compute_moment_init(X, Z, y, group_ids, [10], "intercept")
        >>> theta.shape
        (1,)

    Notes:
        - Uses lme4's variance decomposition when possible
        - Falls back to conservative defaults if estimation fails
        - Returns theta on relative scale (τ/σ)
    """
    if metadata is None:
        metadata = {}
    if re_structure == "intercept":
        # For crossed/nested intercepts: compute theta for each factor
        if len(n_groups_list) > 1:
            # Multiple factors (crossed or nested) - one theta per factor
            theta_list = []
            for i, (group_ids, n_groups) in enumerate(
                zip(group_ids_list, n_groups_list, strict=True)
            ):
                theta_i = _compute_moment_init_intercept(X, group_ids, y, n_groups)
                theta_list.append(theta_i[0])
            return np.array(theta_list)
        else:
            # Single factor
            return _compute_moment_init_intercept(
                X, group_ids_list[0], y, n_groups_list[0]
            )

    elif re_structure == "slope":
        if X_re is None:
            raise ValueError("Slope models require X_re")
        return _compute_moment_init_slope(
            X, group_ids_list[0], X_re, y, n_groups_list[0]
        )

    elif re_structure == "diagonal":
        if X_re is None:
            raise ValueError("Diagonal models require X_re")
        # For diagonal: each RE gets independent variance
        # X_re is a list of arrays (one per independent term)
        # Use simple heuristic initialization: one theta per term
        if isinstance(X_re, list):
            k = len(X_re)  # Number of independent RE terms
        else:
            k = X_re.shape[1]  # Fallback if single array
        return np.ones(k) * 0.5

    elif re_structure in ("crossed", "nested", "mixed"):
        # Crossed/nested/mixed: compute theta for each factor based on its structure
        re_structures_list = metadata.get("re_structures_list", None)

        if re_structures_list is None:
            # Fallback: assume all intercepts (one theta per factor)
            n_factors = len(n_groups_list)
            return np.ones(n_factors) * 0.5

        # Compute theta for each factor based on its structure
        theta_list = []
        for factor_structure in re_structures_list:
            if factor_structure == "intercept":
                # Single variance parameter
                theta_list.append(0.5)
            elif factor_structure == "slope":
                # 2x2 Cholesky: [L00, L10, L11] = 3 params
                # Use heuristic: diagonal=0.5, off-diagonal=0
                theta_list.extend([0.5, 0.0, 0.5])
            elif factor_structure == "diagonal":
                # For diagonal, we'd need to know k (number of RE terms)
                # Default to 2 terms (intercept + slope, uncorrelated)
                theta_list.extend([0.5, 0.5])
            else:
                raise ValueError(f"Unknown factor structure: {factor_structure}")

        return np.array(theta_list)

    else:
        raise ValueError(f"Unknown re_structure: {re_structure}")


def _compute_moment_init_intercept(
    X: np.ndarray, group_ids: np.ndarray, y: np.ndarray, n_groups: int
) -> np.ndarray:
    """Compute moment-based starting value for random intercept model.

    Uses lme4's variance decomposition (modular.R:567-577):
    1. v = var(ave(y, f)) - variance of group means
    2. v_e = var(y) - v - residual variance
    3. theta = sqrt(v / v_e) - relative scale

    Args:
        X: Fixed effects design matrix, shape (n, p).
        group_ids: Group assignments, shape (n,), values 0 to n_groups-1.
        y: Response vector, shape (n,).
        n_groups: Number of groups.

    Returns:
        theta_init, shape (1,), with tau/sigma starting value.

    Examples:
        >>> X = np.random.randn(100, 2)
        >>> group_ids = np.repeat(np.arange(10), 10)
        >>> y = np.random.randn(100)
        >>> theta = _compute_moment_init_intercept(X, group_ids, y, 10)
        >>> theta.shape
        (1,)
        >>> theta[0] > 0
        True

    Notes:
        - Removes fixed effects via OLS before variance decomposition
        - Falls back to theta=1.0 if residual variance is non-positive
        - Clips theta to minimum 1e-3 for numerical stability
    """
    # Remove fixed effects
    try:
        beta_ols = np.linalg.lstsq(X, y, rcond=None)[0]
        y_work = y - X @ beta_ols
    except np.linalg.LinAlgError:
        y_work = y

    # Compute group means replicated across observations (vectorized)
    # Using numpy bincount for O(1) vectorized operation instead of O(n_groups) loop
    counts = np.bincount(group_ids, minlength=n_groups)
    sums = np.bincount(group_ids, weights=y_work, minlength=n_groups)
    # Safe division: avoid divide by zero for empty groups
    means = np.where(counts > 0, sums / counts, 0.0)
    group_means_replicated = means[group_ids]

    # Variance of group means (lme4's v)
    v = np.var(group_means_replicated, ddof=1)

    # Residual variance (lme4's v_e)
    var_y = np.var(y_work, ddof=1)
    v_e = var_y - v

    # Check if residual variance is positive
    if not np.isnan(v_e) and v_e > 0:
        v_rel = v / v_e
        if v_rel > 0 and np.isfinite(v_rel):
            theta = np.sqrt(v_rel)
            theta = max(theta, 1e-3)  # Minimum threshold
        else:
            theta = 1.0
    else:
        theta = 1.0

    # Final sanity check
    if not np.isfinite(theta) or theta <= 0:
        theta = 1.0

    return np.array([theta])


def _compute_moment_init_slope(
    X: np.ndarray,
    group_ids: np.ndarray,
    X_re: np.ndarray,
    y: np.ndarray,
    n_groups: int,
) -> np.ndarray:
    """Compute moment-based starting values for random slope model.

    Fits group-specific models to estimate variance components for
    intercept, slope, and their correlation.

    Args:
        X: Fixed effects design matrix, shape (n, p).
        group_ids: Group assignments, shape (n,), values 0 to n_groups-1.
        X_re: Random effects predictors, shape (n, r).
            Typically (n, 2) with [ones, slope_predictor].
        y: Response vector, shape (n,).
        n_groups: Number of groups.

    Returns:
        theta_init, shape (3,) with [L00, L10, L11] on relative scale.

    Examples:
        >>> X = np.random.randn(100, 2)
        >>> group_ids = np.repeat(np.arange(10), 10)
        >>> X_re = np.column_stack([np.ones(100), np.random.randn(100)])
        >>> y = np.random.randn(100)
        >>> theta = _compute_moment_init_slope(X, group_ids, X_re, y, 10)
        >>> theta.shape
        (3,)

    Notes:
        - Fits OLS within each group
        - Estimates empirical covariance of group-level parameters
        - Converts to Cholesky parameterization
        - Scales by residual SD to get relative scale
    """
    r = X_re.shape[1]  # Number of RE per group

    # Remove fixed effects
    try:
        beta_ols = np.linalg.lstsq(X, y, rcond=None)[0]
        residuals = y - X @ beta_ols
    except np.linalg.LinAlgError:
        residuals = y

    # Fit group-specific models
    group_params = []  # List of parameter vectors per group

    for g in range(n_groups):
        mask = group_ids == g
        n_obs_g = np.sum(mask)

        if n_obs_g < r:
            # Not enough observations for this group
            continue

        y_g = residuals[mask]
        X_g = X_re[mask, :]

        # Fit: y_g ~ X_g
        try:
            params_g = np.linalg.lstsq(X_g, y_g, rcond=None)[0]
            group_params.append(params_g)
        except np.linalg.LinAlgError:
            continue

    # Check if we have enough groups
    if len(group_params) < 2:
        # Fallback: diagonal initialization
        theta_dim = r * (r + 1) // 2
        theta_init = np.zeros(theta_dim)
        idx = 0
        for i in range(r):
            theta_init[idx + i] = 1.0  # Diagonal = 1.0
            idx += i + 1
        return theta_init

    group_params = np.array(group_params)  # Shape: (n_valid_groups, r)

    # Compute empirical covariance
    Sigma = np.cov(group_params.T)  # Shape: (r, r) or scalar if r=1

    # Handle r=1 case where np.cov returns a scalar
    if r == 1:
        Sigma = np.atleast_2d(Sigma)  # Convert scalar to (1, 1) array

    # Ensure PSD
    min_var = 1e-6
    for i in range(r):
        Sigma[i, i] = max(Sigma[i, i], min_var)

    # Cholesky decomposition
    try:
        L = np.linalg.cholesky(Sigma)  # Lower triangular
    except np.linalg.LinAlgError:
        # Fallback: diagonal
        L = np.diag(np.sqrt(np.maximum(np.diag(Sigma), min_var)))

    # Estimate residual SD for scaling
    try:
        beta_ols = np.linalg.lstsq(X, y, rcond=None)[0]
        residuals = y - X @ beta_ols
        sigma_est = np.std(residuals)
    except (np.linalg.LinAlgError, ValueError):
        sigma_est = 1.0

    sigma_est = max(sigma_est, 1e-6)

    # Scale to relative scale (L_rel = L / sigma)
    L_rel = L / sigma_est

    # Ensure positive diagonals
    for i in range(r):
        L_rel[i, i] = max(L_rel[i, i], 1e-3)

    # Extract lower triangle
    theta = []
    for col in range(r):
        for row in range(col, r):
            theta.append(L_rel[row, col])

    theta = np.array(theta)

    # Final check
    if not np.all(np.isfinite(theta)):
        # Ultimate fallback
        theta_dim = r * (r + 1) // 2
        theta_init = np.zeros(theta_dim)
        idx = 0
        for i in range(r):
            theta_init[idx + i] = 1.0
            idx += i + 1
        return theta_init

    return theta
