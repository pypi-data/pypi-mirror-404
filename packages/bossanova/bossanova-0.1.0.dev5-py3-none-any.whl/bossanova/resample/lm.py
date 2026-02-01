"""Linear model resampling with hat-matrix optimization.

This module provides efficient permutation tests, bootstrap procedures,
and cross-validation for linear models. Supports both JAX (accelerated)
and NumPy (Pyodide-compatible) backends.

Performance: JAX backend uses jax.lax.map with automatic batch sizing for
2-4x speedup. NumPy backend uses Python loops for compatibility.
"""

from typing import Any, Callable, Literal

import numpy as np
import scipy.linalg as la

from bossanova._backend import get_backend
from bossanova.ops.batching import compute_batch_size
from bossanova.ops.rng import RNG
from bossanova.resample.core import (
    bootstrap_ci_basic,
    bootstrap_ci_bca,
    bootstrap_ci_percentile,
    compute_pvalues,
    generate_kfold_indices,
    generate_loo_indices,
)
from bossanova.resample.results import BootstrapResult, CVResult, PermutationResult
from bossanova.resample.utils import (
    compute_observed_statistic,
    validate_boot_type,
    validate_ci_type,
)

# Type alias for arrays (works with both JAX and NumPy)
Array = Any

__all__ = [
    "Array",
    "make_lm_coefficient_operator",
    "compute_jackknife_coefficients",
    "compute_lm_se",
    "lm_permute",
    "lm_bootstrap",
    "lm_cv",
]


# =============================================================================
# Coefficient Operator (Hat-Matrix Trick)
# =============================================================================


def make_lm_coefficient_operator(
    X: Array,
    method: Literal["cholesky", "qr"] = "cholesky",
) -> Callable[[Array], Array]:
    """Create reusable linear operator Y -> coefficients.

    Precomputes and caches the expensive factorization. Returns a function
    that maps Y -> coefficients.

    This implements the "hat-matrix trick" for efficient permutation testing:
    For fixed design matrix X, coefficients are a linear map from Y -> beta_hat:
    beta_hat = (X'X)^-1 X'y. We precompute the factorization of (X'X) once
    and reuse it for all permuted/bootstrapped Y values.

    Args:
        X: Design matrix, shape (n, p).
        method: Factorization method.
            - 'cholesky': Uses Cholesky decomposition of X'X (faster, more stable).
            - 'qr': Uses QR decomposition of X (handles rank deficiency better).

    Returns:
        Function that maps Y (shape [n] or [n, m]) to coefficients.

    Examples:
        >>> X = np.array([[1, 2], [1, 3], [1, 4]])
        >>> operator = make_lm_coefficient_operator(X)
        >>> y = np.array([5, 8, 11])
        >>> coef = operator(y)
    """
    backend = get_backend()

    if backend == "jax":
        import jax.numpy as jnp
        import jax.scipy.linalg as jsp

        X_jax = jnp.asarray(X)

        if method == "cholesky":
            XtX = X_jax.T @ X_jax
            L = jnp.linalg.cholesky(XtX)

            def apply_chol_jax(Y: Array) -> Array:
                Y_jax = jnp.asarray(Y)
                is_1d = Y_jax.ndim == 1
                if is_1d:
                    Y_jax = Y_jax[:, jnp.newaxis]

                XtY = X_jax.T @ Y_jax
                coef = jsp.cho_solve((L, True), XtY)

                if is_1d:
                    coef = jnp.squeeze(coef, axis=-1)
                return coef

            return apply_chol_jax

        elif method == "qr":
            Q, R = jnp.linalg.qr(X_jax)

            def apply_qr_jax(Y: Array) -> Array:
                Y_jax = jnp.asarray(Y)
                is_1d = Y_jax.ndim == 1
                if is_1d:
                    Y_jax = Y_jax[:, jnp.newaxis]

                QtY = Q.T @ Y_jax
                coef = jsp.solve_triangular(R, QtY, lower=False)

                if is_1d:
                    coef = jnp.squeeze(coef, axis=-1)
                return coef

            return apply_qr_jax

        else:
            raise ValueError(f"method must be 'cholesky' or 'qr', got {method}")

    else:
        # NumPy backend
        X_np = np.asarray(X)

        if method == "cholesky":
            XtX = X_np.T @ X_np
            L = la.cholesky(XtX, lower=True)

            def apply_chol_np(Y: Array) -> Array:
                Y_np = np.asarray(Y)
                is_1d = Y_np.ndim == 1
                if is_1d:
                    Y_np = Y_np[:, np.newaxis]

                XtY = X_np.T @ Y_np
                coef = la.cho_solve((L, True), XtY)

                if is_1d:
                    coef = np.squeeze(coef, axis=-1)
                return coef

            return apply_chol_np

        elif method == "qr":
            Q, R = la.qr(X_np, mode="economic")

            def apply_qr_np(Y: Array) -> Array:
                Y_np = np.asarray(Y)
                is_1d = Y_np.ndim == 1
                if is_1d:
                    Y_np = Y_np[:, np.newaxis]

                QtY = Q.T @ Y_np
                coef = la.solve_triangular(R, QtY, lower=False)

                if is_1d:
                    coef = np.squeeze(coef, axis=-1)
                return coef

            return apply_qr_np

        else:
            raise ValueError(f"method must be 'cholesky' or 'qr', got {method}")


def compute_jackknife_coefficients(
    X: Array,
    coef: Array,
    residuals: Array,
    leverage: Array,
    XtX_inv: Array,
) -> Array:
    """Compute leave-one-out coefficients via rank-one update (P1 optimization).

    Uses the Sherman-Morrison formula to compute LOO coefficients without
    re-fitting the model for each observation. This is O(n*p) instead of
    O(n*p³) for naive refitting.

    Formula: β_{-i} = β - (X'X)^{-1} x_i e_i / (1 - h_i)

    where:
    - β is the full-data coefficient vector
    - x_i is the i-th row of X
    - e_i is the i-th residual
    - h_i is the i-th leverage value

    Args:
        X: Design matrix, shape (n, p).
        coef: Fitted coefficients from full data, shape (p,).
        residuals: Residuals from full fit, shape (n,).
        leverage: Leverage values (diagonal of hat matrix), shape (n,).
        XtX_inv: Pre-computed (X'X)^{-1}, shape (p, p).

    Returns:
        Jackknife coefficients, shape (n, p), where row i is β_{-i}.

    Note:
        This is mathematically equivalent to refitting n models with one
        observation removed each time, but ~90% faster for typical problems.

    Examples:
        >>> X = np.array([[1, 2], [1, 3], [1, 4]])
        >>> coef = np.array([1.0, 2.0])
        >>> residuals = np.array([0.1, -0.2, 0.1])
        >>> leverage = np.array([0.83, 0.33, 0.83])
        >>> XtX_inv = np.linalg.inv(X.T @ X)
        >>> jack_coefs = compute_jackknife_coefficients(X, coef, residuals, leverage, XtX_inv)
    """
    backend = get_backend()

    if backend == "jax":
        import jax
        import jax.numpy as jnp

        X_jax = jnp.asarray(X)
        n = X_jax.shape[0]

        def compute_loo_coef(i: int) -> Array:
            x_i = X_jax[i]  # (p,)
            e_i = residuals[i]
            h_i = leverage[i]
            # DFBETA_i = (X'X)^{-1} x_i' e_i / (1 - h_i)
            dfbeta = (XtX_inv @ x_i) * e_i / (1 - h_i)
            return coef - dfbeta

        # vmap over all observations for efficient parallel computation
        return jax.vmap(compute_loo_coef)(jnp.arange(n))

    else:
        # NumPy backend - use Python loop
        X_np = np.asarray(X)
        coef_np = np.asarray(coef)
        residuals_np = np.asarray(residuals)
        leverage_np = np.asarray(leverage)
        XtX_inv_np = np.asarray(XtX_inv)
        n = X_np.shape[0]

        jack_coefs = []
        for i in range(n):
            x_i = X_np[i]
            e_i = residuals_np[i]
            h_i = leverage_np[i]
            dfbeta = (XtX_inv_np @ x_i) * e_i / (1 - h_i)
            jack_coefs.append(coef_np - dfbeta)

        return np.stack(jack_coefs, axis=0)


def compute_lm_se(
    X: Array,
    y: Array,
    coef: Array,
    XtX_inv: Array | None = None,
) -> Array:
    """Compute standard errors for lm coefficients.

    SE(beta_hat) = sigma_hat * sqrt(diag((X'X)^-1))
    where sigma_hat^2 = RSS / (n - p)

    Args:
        X: Design matrix, shape (n, p).
        y: Response vector, shape (n,).
        coef: Coefficient estimates, shape (p,).
        XtX_inv: Pre-computed (X'X)^{-1}, shape (p, p). If None, computed
            internally. Pass this for efficiency when calling repeatedly
            with the same X (e.g., in permutation tests).

    Returns:
        Standard errors for each coefficient, shape (p,).

    Examples:
        >>> X = np.array([[1, 2], [1, 3], [1, 4]])
        >>> y = np.array([5, 8, 11])
        >>> coef = np.array([2, 3])
        >>> se = compute_lm_se(X, y, coef)

        # For repeated calls with same X, pre-compute XtX_inv:
        >>> XtX_inv = np.linalg.inv(X.T @ X)
        >>> se = compute_lm_se(X, y, coef, XtX_inv=XtX_inv)
    """
    backend = get_backend()

    if backend == "jax":
        import jax.numpy as jnp

        X_jax = jnp.asarray(X)
        y_jax = jnp.asarray(y)
        coef_jax = jnp.asarray(coef)

        n, p = X_jax.shape

        fitted = X_jax @ coef_jax
        residuals = y_jax - fitted
        rss = jnp.sum(residuals**2)

        df_resid = n - p
        sigma2 = rss / df_resid
        sigma = jnp.sqrt(sigma2)

        # Use cached XtX_inv if provided, otherwise compute
        if XtX_inv is None:
            XtX = X_jax.T @ X_jax
            XtX_inv = jnp.linalg.inv(XtX)

        se = sigma * jnp.sqrt(jnp.diag(XtX_inv))
        return se

    else:
        # NumPy backend
        X_np = np.asarray(X)
        y_np = np.asarray(y)
        coef_np = np.asarray(coef)

        n, p = X_np.shape

        fitted = X_np @ coef_np
        residuals = y_np - fitted
        rss = np.sum(residuals**2)

        df_resid = n - p
        sigma2 = rss / df_resid
        sigma = np.sqrt(sigma2)

        # Use cached XtX_inv if provided, otherwise compute
        if XtX_inv is None:
            XtX = X_np.T @ X_np
            XtX_inv = la.inv(XtX)

        se = sigma * np.sqrt(np.diag(XtX_inv))
        return se


# =============================================================================
# Permutation Test
# =============================================================================


def lm_permute(
    X: Array,
    y: Array,
    X_names: list[str],
    n_perm: int = 999,
    seed: int | None = None,
    alternative: Literal["two-sided", "greater", "less"] = "two-sided",
    test_stat: Literal["t", "coef", "abs_coef"] = "t",
    max_mem: float | None = None,
) -> PermutationResult:
    """Efficient permutation test for lm fixed effects.

    Uses precomputed linear operator (hat-matrix trick) and batched
    processing for efficient computation.

    Args:
        X: Design matrix, shape (n, p).
        y: Response vector, shape (n,).
        X_names: Coefficient names.
        n_perm: Number of permutations.
        seed: Random seed for reproducibility.
        alternative: Alternative hypothesis type.
        test_stat: Test statistic to use:
            - 't': t-statistic (coefficient / SE).
            - 'coef': Raw coefficient.
            - 'abs_coef': Absolute coefficient.
        max_mem: Fraction of available system memory to use (0.0-1.0).
            Controls batch size for parallel computation. None defaults
            to 0.5 (50% of available memory).

    Returns:
        PermutationResult with observed stats, null distribution, and p-values.

    Examples:
        >>> X = np.array([[1, 1], [1, 2], [1, 3], [1, 4]])
        >>> y = np.array([2, 4, 5, 8])
        >>> result = lm_permute(X, y, ["Intercept", "x"], n_perm=999)
        >>> print(result.pvalues)
    """
    backend = get_backend()
    rng = RNG.from_seed(seed)

    if backend == "jax":
        return _lm_permute_jax(
            X, y, X_names, n_perm, rng, alternative, test_stat, max_mem
        )
    else:
        return _lm_permute_numpy(X, y, X_names, n_perm, rng, alternative, test_stat)


def _lm_permute_jax(
    X: Array,
    y: Array,
    X_names: list[str],
    n_perm: int,
    rng: RNG,
    alternative: Literal["two-sided", "greater", "less"],
    test_stat: Literal["t", "coef", "abs_coef"],
    max_mem: float | None,
) -> PermutationResult:
    """JAX implementation of lm_permute using jax.lax.map."""
    import jax
    import jax.numpy as jnp
    import jax.random as jr

    X_jax = jnp.asarray(X)
    y_jax = jnp.asarray(y)
    n, p = X_jax.shape
    key = rng.key

    # Build coefficient operator
    coef_operator = make_lm_coefficient_operator(X_jax, method="cholesky")

    # Pre-compute XtX_inv for SE computation
    XtX = X_jax.T @ X_jax
    XtX_inv = jnp.linalg.inv(XtX)

    # Compute observed statistics
    coef_obs = coef_operator(y_jax)
    se_obs = (
        compute_lm_se(X_jax, y_jax, coef_obs, XtX_inv=XtX_inv)
        if test_stat == "t"
        else None
    )
    observed = compute_observed_statistic(coef_obs, se_obs, test_stat)

    # Define single permutation function
    def single_permutation(subkey: Array) -> Array:
        perm_idx = jr.permutation(subkey, n)
        y_perm = y_jax[perm_idx]
        coef_perm = coef_operator(y_perm)
        se_perm = (
            compute_lm_se(X_jax, y_perm, coef_perm, XtX_inv=XtX_inv)
            if test_stat == "t"
            else None
        )
        return compute_observed_statistic(coef_perm, se_perm, test_stat)

    # Compute batch size based on memory budget
    batch_size = compute_batch_size(
        n_items=n_perm,
        bytes_per_item=p * 8,  # float64
        max_mem=max_mem,
    )

    # Generate all keys and run batched permutations
    keys = jr.split(key, n_perm)
    null_distribution = jax.lax.map(single_permutation, keys, batch_size=batch_size)

    # Compute p-values
    pvalues = compute_pvalues(observed, null_distribution, alternative=alternative)

    return PermutationResult(
        observed=observed,
        null_distribution=null_distribution,
        pvalues=pvalues,
        param_names=X_names,
        n_perm=n_perm,
        test_stat=test_stat,
        alternative=alternative,
    )


def _lm_permute_numpy(
    X: Array,
    y: Array,
    X_names: list[str],
    n_perm: int,
    rng: RNG,
    alternative: Literal["two-sided", "greater", "less"],
    test_stat: Literal["t", "coef", "abs_coef"],
) -> PermutationResult:
    """NumPy implementation of lm_permute using Python loops."""
    X_np = np.asarray(X)
    y_np = np.asarray(y)
    n, p = X_np.shape

    # Build coefficient operator
    coef_operator = make_lm_coefficient_operator(X_np, method="cholesky")

    # Pre-compute XtX_inv for SE computation
    XtX = X_np.T @ X_np
    XtX_inv = la.inv(XtX)

    # Compute observed statistics
    coef_obs = coef_operator(y_np)
    se_obs = (
        compute_lm_se(X_np, y_np, coef_obs, XtX_inv=XtX_inv)
        if test_stat == "t"
        else None
    )
    observed = compute_observed_statistic(coef_obs, se_obs, test_stat)

    # Run permutations in Python loop
    null_stats = []
    keys = rng.split(n_perm)

    for i in range(n_perm):
        perm_idx = keys[i].permutation(n)
        y_perm = y_np[perm_idx]
        coef_perm = coef_operator(y_perm)
        se_perm = (
            compute_lm_se(X_np, y_perm, coef_perm, XtX_inv=XtX_inv)
            if test_stat == "t"
            else None
        )
        null_stats.append(compute_observed_statistic(coef_perm, se_perm, test_stat))

    null_distribution = np.stack(null_stats, axis=0)

    # Compute p-values
    pvalues = compute_pvalues(observed, null_distribution, alternative=alternative)

    return PermutationResult(
        observed=observed,
        null_distribution=null_distribution,
        pvalues=pvalues,
        param_names=X_names,
        n_perm=n_perm,
        test_stat=test_stat,
        alternative=alternative,
    )


# =============================================================================
# Bootstrap
# =============================================================================


def lm_bootstrap(
    X: Array,
    y: Array,
    X_names: list[str],
    fitted: Array,
    sigma: float,
    n_boot: int = 999,
    seed: int | None = None,
    boot_type: Literal["residual", "case", "parametric"] = "residual",
    ci_type: Literal["percentile", "basic", "bca"] = "bca",
    level: float = 0.95,
    max_mem: float | None = None,
) -> BootstrapResult:
    """Bootstrap inference for lm coefficients.

    Types:
    - residual: Resample residuals, add to fitted values (assumes homoscedasticity).
    - case: Resample (X, y) pairs together (robust to heteroscedasticity).
    - parametric: Simulate from fitted model (assumes normality).

    Args:
        X: Design matrix, shape (n, p).
        y: Response vector, shape (n,).
        X_names: Coefficient names.
        fitted: Fitted values from original model, shape (n,).
        sigma: Residual standard error (σ = √(RSS/df_resid)) from original model.
        n_boot: Number of bootstrap samples.
        seed: Random seed for reproducibility.
        boot_type: Type of bootstrap.
        ci_type: Type of confidence interval ("percentile", "basic", or "bca").
        level: Confidence level.
        max_mem: Fraction of available system memory to use (0.0-1.0).
            Controls batch size for parallel computation. None defaults
            to 0.5 (50% of available memory).

    Returns:
        BootstrapResult with observed stats, bootstrap samples, and CIs.

    Examples:
        >>> X = np.array([[1, 1], [1, 2], [1, 3], [1, 4]])
        >>> y = np.array([2, 4, 5, 8])
        >>> fitted = X @ np.array([0.5, 1.9])
        >>> result = lm_bootstrap(X, y, ["Intercept", "x"], fitted, sigma=0.5)
    """
    # Validate parameters early
    validate_boot_type(boot_type)
    validate_ci_type(ci_type)

    # Dispatch to BCa-optimized version if requested
    if ci_type == "bca":
        return _lm_bootstrap_bca(
            X=X,
            y=y,
            X_names=X_names,
            fitted=fitted,
            sigma=sigma,
            n_boot=n_boot,
            seed=seed,
            boot_type=boot_type,
            level=level,
            max_mem=max_mem,
        )

    backend = get_backend()
    rng = RNG.from_seed(seed)

    if backend == "jax":
        return _lm_bootstrap_jax(
            X,
            y,
            X_names,
            fitted,
            sigma,
            n_boot,
            rng,
            boot_type,
            ci_type,
            level,
            max_mem,
        )
    else:
        return _lm_bootstrap_numpy(
            X, y, X_names, fitted, sigma, n_boot, rng, boot_type, ci_type, level
        )


def _lm_bootstrap_jax(
    X: Array,
    y: Array,
    X_names: list[str],
    fitted: Array,
    sigma: float,
    n_boot: int,
    rng: RNG,
    boot_type: Literal["residual", "case", "parametric"],
    ci_type: Literal["percentile", "basic"],
    level: float,
    max_mem: float | None,
) -> BootstrapResult:
    """JAX implementation of lm_bootstrap."""
    import jax
    import jax.numpy as jnp
    import jax.random as jr

    X_jax = jnp.asarray(X)
    y_jax = jnp.asarray(y)
    fitted_jax = jnp.asarray(fitted)
    n, p = X_jax.shape
    key = rng.key

    # Observed coefficients
    coef_operator = make_lm_coefficient_operator(X_jax, method="cholesky")
    coef_obs = coef_operator(y_jax)

    # Define single bootstrap function based on boot_type
    if boot_type == "residual":
        residuals = y_jax - fitted_jax
        residuals_centered = residuals - jnp.mean(residuals)

        def single_bootstrap(subkey: Array) -> Array:
            boot_idx = jr.choice(subkey, n, shape=(n,), replace=True)
            resid_boot = residuals_centered[boot_idx]
            y_boot = fitted_jax + resid_boot
            return coef_operator(y_boot)

    elif boot_type == "case":

        def single_bootstrap(subkey: Array) -> Array:
            boot_idx = jr.choice(subkey, n, shape=(n,), replace=True)
            X_boot = X_jax[boot_idx]
            y_boot = y_jax[boot_idx]
            coef_op_boot = make_lm_coefficient_operator(X_boot, method="cholesky")
            return coef_op_boot(y_boot)

    elif boot_type == "parametric":

        def single_bootstrap(subkey: Array) -> Array:
            errors = jr.normal(subkey, shape=(n,)) * sigma
            y_boot = fitted_jax + errors
            return coef_operator(y_boot)

    else:
        raise ValueError(
            f"boot_type must be 'residual', 'case', or 'parametric', got {boot_type}"
        )

    # Compute batch size based on memory budget
    batch_size = compute_batch_size(
        n_items=n_boot,
        bytes_per_item=p * 8,  # float64
        max_mem=max_mem,
    )

    # Generate all keys and run batched bootstrap
    keys = jr.split(key, n_boot)
    boot_samples = jax.lax.map(single_bootstrap, keys, batch_size=batch_size)

    # Compute confidence intervals
    if ci_type == "percentile":
        ci_lower, ci_upper = bootstrap_ci_percentile(boot_samples, level=level)
    elif ci_type == "basic":
        ci_lower, ci_upper = bootstrap_ci_basic(coef_obs, boot_samples, level=level)
    else:
        raise ValueError(
            f"ci_type must be 'percentile', 'basic', or 'bca', got {ci_type}"
        )

    return BootstrapResult(
        observed=coef_obs,
        boot_samples=boot_samples,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        param_names=X_names,
        n_boot=n_boot,
        ci_type=ci_type,
        level=level,
    )


def _lm_bootstrap_numpy(
    X: Array,
    y: Array,
    X_names: list[str],
    fitted: Array,
    sigma: float,
    n_boot: int,
    rng: RNG,
    boot_type: Literal["residual", "case", "parametric"],
    ci_type: Literal["percentile", "basic"],
    level: float,
) -> BootstrapResult:
    """NumPy implementation of lm_bootstrap using Python loops."""
    X_np = np.asarray(X)
    y_np = np.asarray(y)
    fitted_np = np.asarray(fitted)
    n, _ = X_np.shape

    # Observed coefficients
    coef_operator = make_lm_coefficient_operator(X_np, method="cholesky")
    coef_obs = coef_operator(y_np)

    # Run bootstrap in Python loop
    boot_samples = []
    keys = rng.split(n_boot)

    if boot_type == "residual":
        residuals = y_np - fitted_np
        residuals_centered = residuals - np.mean(residuals)

        for i in range(n_boot):
            boot_idx = keys[i].choice(n, shape=(n,), replace=True)
            resid_boot = residuals_centered[boot_idx]
            y_boot = fitted_np + resid_boot
            boot_samples.append(coef_operator(y_boot))

    elif boot_type == "case":
        p = X_np.shape[1]
        for i in range(n_boot):
            boot_idx = keys[i].choice(n, shape=(n,), replace=True)
            X_boot = X_np[boot_idx]
            y_boot = y_np[boot_idx]
            try:
                coef_op_boot = make_lm_coefficient_operator(X_boot, method="cholesky")
                boot_samples.append(coef_op_boot(y_boot))
            except np.linalg.LinAlgError:
                # Bootstrap sample created singular matrix - record as NaN
                boot_samples.append(np.full(p, np.nan))

    elif boot_type == "parametric":
        for i in range(n_boot):
            errors = keys[i].normal(shape=(n,)) * sigma
            y_boot = fitted_np + errors
            boot_samples.append(coef_operator(y_boot))

    else:
        raise ValueError(
            f"boot_type must be 'residual', 'case', or 'parametric', got {boot_type}"
        )

    boot_samples = np.stack(boot_samples, axis=0)

    # Count and warn about failures (only possible for case bootstrap)
    if boot_type == "case":
        n_failed = np.sum(np.any(np.isnan(boot_samples), axis=1))
        if n_failed > n_boot * 0.1:
            import warnings

            warnings.warn(
                f"Bootstrap: {n_failed}/{n_boot} iterations failed (singular matrix). "
                f"This can happen with small samples or high-dimensional data. "
                f"Consider using boot_type='residual' instead.",
                RuntimeWarning,
            )

    # Compute confidence intervals (excluding NaN samples from failed iterations)
    valid_mask = ~np.any(np.isnan(boot_samples), axis=1)
    boot_samples_valid = boot_samples[valid_mask]

    if ci_type == "percentile":
        ci_lower, ci_upper = bootstrap_ci_percentile(boot_samples_valid, level=level)
    elif ci_type == "basic":
        ci_lower, ci_upper = bootstrap_ci_basic(
            coef_obs, boot_samples_valid, level=level
        )
    else:
        raise ValueError(
            f"ci_type must be 'percentile', 'basic', or 'bca', got {ci_type}"
        )

    return BootstrapResult(
        observed=coef_obs,
        boot_samples=boot_samples,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        param_names=X_names,
        n_boot=n_boot,
        ci_type=ci_type,
        level=level,
    )


def _lm_bootstrap_bca(
    X: Array,
    y: Array,
    X_names: list[str],
    fitted: Array,
    sigma: float,
    n_boot: int = 999,
    seed: int | None = None,
    boot_type: Literal["residual", "case", "parametric"] = "residual",
    level: float = 0.95,
    max_mem: float | None = None,
) -> BootstrapResult:
    """BCa bootstrap with efficient jackknife computation.

    This function combines bootstrap and jackknife in an efficient manner:
    1. Generate bootstrap samples and compute boot_stats
    2. Compute jackknife statistics (leave-one-out) in parallel via vmap
    3. Use both for BCa correction

    Args:
        X: Design matrix, shape (n, p).
        y: Response vector, shape (n,).
        X_names: Coefficient names.
        fitted: Fitted values from original model, shape (n,).
        sigma: Residual standard error (σ = √(RSS/df_resid)) from original model.
        n_boot: Number of bootstrap samples.
        seed: Random seed for reproducibility.
        boot_type: Type of bootstrap.
        level: Confidence level.
        max_mem: Fraction of available system memory to use (0.0-1.0).

    Returns:
        BootstrapResult with BCa confidence intervals.
    """
    backend = get_backend()
    rng = RNG.from_seed(seed)

    if backend == "jax":
        return _lm_bootstrap_bca_jax(
            X, y, X_names, fitted, sigma, n_boot, rng, boot_type, level, max_mem
        )
    else:
        return _lm_bootstrap_bca_numpy(
            X, y, X_names, fitted, sigma, n_boot, rng, boot_type, level
        )


def _lm_bootstrap_bca_jax(
    X: Array,
    y: Array,
    X_names: list[str],
    fitted: Array,
    sigma: float,
    n_boot: int,
    rng: RNG,
    boot_type: Literal["residual", "case", "parametric"],
    level: float,
    max_mem: float | None,
) -> BootstrapResult:
    """JAX implementation of BCa bootstrap."""
    import jax
    import jax.numpy as jnp
    import jax.random as jr

    X_jax = jnp.asarray(X)
    y_jax = jnp.asarray(y)
    fitted_jax = jnp.asarray(fitted)
    n, p = X_jax.shape
    key = rng.key

    # Observed coefficients
    coef_operator = make_lm_coefficient_operator(X_jax, method="cholesky")
    coef_obs = coef_operator(y_jax)

    # Define single bootstrap function based on boot_type
    if boot_type == "residual":
        residuals = y_jax - fitted_jax
        residuals_centered = residuals - jnp.mean(residuals)

        def single_bootstrap(subkey: Array) -> Array:
            boot_idx = jr.choice(subkey, n, shape=(n,), replace=True)
            resid_boot = residuals_centered[boot_idx]
            y_boot = fitted_jax + resid_boot
            return coef_operator(y_boot)

    elif boot_type == "case":

        def single_bootstrap(subkey: Array) -> Array:
            boot_idx = jr.choice(subkey, n, shape=(n,), replace=True)
            X_boot = X_jax[boot_idx]
            y_boot = y_jax[boot_idx]
            coef_op_boot = make_lm_coefficient_operator(X_boot, method="cholesky")
            return coef_op_boot(y_boot)

    elif boot_type == "parametric":

        def single_bootstrap(subkey: Array) -> Array:
            errors = jr.normal(subkey, shape=(n,)) * sigma
            y_boot = fitted_jax + errors
            return coef_operator(y_boot)

    else:
        raise ValueError(
            f"boot_type must be 'residual', 'case', or 'parametric', got {boot_type}"
        )

    # Compute batch size based on memory budget
    batch_size = compute_batch_size(
        n_items=n_boot,
        bytes_per_item=p * 8,  # float64
        max_mem=max_mem,
    )

    # Generate all keys and run batched bootstrap
    keys = jr.split(key, n_boot)
    boot_samples = jax.lax.map(single_bootstrap, keys, batch_size=batch_size)

    # --- Jackknife statistics for BCa acceleration ---
    # Use rank-one update formula instead of O(n) model refits
    residuals_obs = y_jax - X_jax @ coef_obs

    # Compute leverage via QR decomposition: h_i = ||Q[i, :]||²
    Q, _ = jnp.linalg.qr(X_jax)
    leverage = jnp.sum(Q**2, axis=1)

    # Compute (X'X)^{-1} for rank-one update
    XtX = X_jax.T @ X_jax
    XtX_inv = jnp.linalg.inv(XtX)

    # Fast jackknife via Sherman-Morrison formula
    jackknife_stats = compute_jackknife_coefficients(
        X_jax, coef_obs, residuals_obs, leverage, XtX_inv
    )

    # --- BCa confidence intervals ---
    ci_lower, ci_upper = bootstrap_ci_bca(
        boot_stats=boot_samples,
        observed=coef_obs,
        jackknife_stats=jackknife_stats,
        level=level,
    )

    return BootstrapResult(
        observed=coef_obs,
        boot_samples=boot_samples,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        param_names=X_names,
        n_boot=n_boot,
        ci_type="bca",
        level=level,
    )


def _lm_bootstrap_bca_numpy(
    X: Array,
    y: Array,
    X_names: list[str],
    fitted: Array,
    sigma: float,
    n_boot: int,
    rng: RNG,
    boot_type: Literal["residual", "case", "parametric"],
    level: float,
) -> BootstrapResult:
    """NumPy implementation of BCa bootstrap."""
    X_np = np.asarray(X)
    y_np = np.asarray(y)
    fitted_np = np.asarray(fitted)
    n, _ = X_np.shape

    # Observed coefficients
    coef_operator = make_lm_coefficient_operator(X_np, method="cholesky")
    coef_obs = coef_operator(y_np)

    # Run bootstrap in Python loop
    boot_samples = []
    keys = rng.split(n_boot)

    if boot_type == "residual":
        residuals = y_np - fitted_np
        residuals_centered = residuals - np.mean(residuals)

        for i in range(n_boot):
            boot_idx = keys[i].choice(n, shape=(n,), replace=True)
            resid_boot = residuals_centered[boot_idx]
            y_boot = fitted_np + resid_boot
            boot_samples.append(coef_operator(y_boot))

    elif boot_type == "case":
        for i in range(n_boot):
            boot_idx = keys[i].choice(n, shape=(n,), replace=True)
            X_boot = X_np[boot_idx]
            y_boot = y_np[boot_idx]
            coef_op_boot = make_lm_coefficient_operator(X_boot, method="cholesky")
            boot_samples.append(coef_op_boot(y_boot))

    elif boot_type == "parametric":
        for i in range(n_boot):
            errors = keys[i].normal(shape=(n,)) * sigma
            y_boot = fitted_np + errors
            boot_samples.append(coef_operator(y_boot))

    else:
        raise ValueError(
            f"boot_type must be 'residual', 'case', or 'parametric', got {boot_type}"
        )

    boot_samples = np.stack(boot_samples, axis=0)

    # --- Jackknife statistics for BCa acceleration ---
    residuals_obs = y_np - X_np @ coef_obs

    # Compute leverage via QR decomposition: h_i = ||Q[i, :]||²
    Q, _ = la.qr(X_np, mode="economic")
    leverage = np.sum(Q**2, axis=1)

    # Compute (X'X)^{-1} for rank-one update
    XtX = X_np.T @ X_np
    XtX_inv = la.inv(XtX)

    # Fast jackknife via Sherman-Morrison formula
    jackknife_stats = compute_jackknife_coefficients(
        X_np, coef_obs, residuals_obs, leverage, XtX_inv
    )

    # --- BCa confidence intervals ---
    ci_lower, ci_upper = bootstrap_ci_bca(
        boot_stats=boot_samples,
        observed=coef_obs,
        jackknife_stats=jackknife_stats,
        level=level,
    )

    return BootstrapResult(
        observed=coef_obs,
        boot_samples=boot_samples,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        param_names=X_names,
        n_boot=n_boot,
        ci_type="bca",
        level=level,
    )


# =============================================================================
# Cross-Validation
# =============================================================================


def lm_cv(
    X: Array,
    y: Array,
    X_names: list[str],
    cv: int | Literal["loo"] = 5,
    seed: int | None = None,
    return_predictions: bool = False,
) -> CVResult:
    """Cross-validation for linear models.

    Uses efficient refitting via the hat-matrix operator (precomputed factorization).

    Args:
        X: Design matrix, shape (n, p).
        y: Response vector, shape (n,).
        X_names: Coefficient names.
        cv: Cross-validation strategy:
            - int: K-fold with this many splits.
            - "loo": Leave-one-out cross-validation.
        seed: Random seed for k-fold shuffling.
        return_predictions: If True, return out-of-fold predictions.

    Returns:
        CVResult with per-fold metrics (MSE, RMSE, MAE, R2).

    Examples:
        >>> X = np.array([[1, 1], [1, 2], [1, 3], [1, 4], [1, 5]])
        >>> y = np.array([2, 4, 5, 8, 10])
        >>> result = lm_cv(X, y, ["Intercept", "x"], cv=5)
        >>> print(result.mean_scores)
    """
    X_np = np.asarray(X)
    y_np = np.asarray(y)
    n, _ = X_np.shape

    rng = RNG.from_seed(seed)

    # Generate splits
    if cv == "loo":
        splits = generate_loo_indices(n)
        cv_type = "loo"
    elif isinstance(cv, int):
        splits = generate_kfold_indices(rng, n, cv, shuffle=True)
        cv_type = f"{cv}-fold"
    else:
        raise ValueError(f"cv must be int or 'loo', got {cv}")

    n_folds = len(splits)

    # Storage
    fold_scores: dict[str, list[float]] = {
        "mse": [],
        "rmse": [],
        "mae": [],
        "r2": [],
    }
    predictions_list = [] if return_predictions else None
    actuals_list = [] if return_predictions else None

    # Perform cross-validation
    for train_idx, test_idx in splits:
        X_train = X_np[train_idx]
        y_train = y_np[train_idx]
        X_test = X_np[test_idx]
        y_test = y_np[test_idx]

        # Fit on training data
        coef_operator = make_lm_coefficient_operator(X_train, method="cholesky")
        coef_fold = coef_operator(y_train)

        # Predict on test data
        y_pred = X_test @ coef_fold

        # Compute metrics
        residuals = y_test - y_pred
        mse = float(np.mean(residuals**2))
        rmse = float(np.sqrt(mse))
        mae = float(np.mean(np.abs(residuals)))

        ss_res = float(np.sum(residuals**2))
        ss_tot = float(np.sum((y_test - np.mean(y_test)) ** 2))
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        fold_scores["mse"].append(mse)
        fold_scores["rmse"].append(rmse)
        fold_scores["mae"].append(mae)
        fold_scores["r2"].append(r2)

        if return_predictions:
            assert predictions_list is not None
            assert actuals_list is not None
            predictions_list.append(np.array(y_pred))
            actuals_list.append(np.array(y_test))

    # Compute summary statistics
    mean_scores = {metric: np.mean(scores) for metric, scores in fold_scores.items()}
    std_scores = {metric: np.std(scores) for metric, scores in fold_scores.items()}

    # Concatenate predictions if requested
    predictions = None
    actuals = None
    if return_predictions and predictions_list:
        predictions = np.concatenate(predictions_list)
        actuals = np.concatenate(actuals_list)

    return CVResult(
        scores=fold_scores,
        mean_scores=mean_scores,
        std_scores=std_scores,
        n_folds=n_folds,
        cv_type=cv_type,
        predictions=predictions,
        actuals=actuals,
    )
