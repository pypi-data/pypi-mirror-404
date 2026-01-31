"""Core resampling utilities.

This module provides index generation functions, p-value computation,
and confidence interval methods for resampling-based inference.

All index generation functions use the unified RNG abstraction for
backend-agnostic random number generation (works with JAX and NumPy).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np

# Conditional JAX import for Pyodide compatibility
# Must configure x64 before any JAX array operations
try:
    import jax

    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp
except ImportError:
    import numpy as jnp  # type: ignore[no-redef]

from scipy import stats as sp_stats

if TYPE_CHECKING:
    from numpy.typing import ArrayLike

    from bossanova.ops.rng import RNG

__all__ = [
    "generate_permutation_indices",
    "generate_bootstrap_indices",
    "generate_kfold_indices",
    "generate_loo_indices",
    "compute_pvalues",
    "bootstrap_ci_percentile",
    "bootstrap_ci_basic",
    "BCa_MIN_NBOOT",
    "bootstrap_ci_bca",
]


# =============================================================================
# Index Generation (unified, backend-agnostic)
# =============================================================================


def generate_permutation_indices(rng: "RNG", n: int, n_perm: int) -> np.ndarray:
    """Generate n_perm permutation index arrays.

    Args:
        rng: RNG object (from bossanova.ops.rng).
        n: Length of each permutation.
        n_perm: Number of permutations to generate.

    Returns:
        Shape [n_perm, n], where each row is a permutation of [0, 1, ..., n-1].

    Examples:
        >>> from bossanova.ops.rng import RNG
        >>> rng = RNG.from_seed(42)
        >>> indices = generate_permutation_indices(rng, n=5, n_perm=3)
        >>> indices.shape
        (3, 5)
    """
    keys = rng.split(n_perm)
    return np.stack([np.asarray(k.permutation(n)) for k in keys])


def generate_bootstrap_indices(rng: "RNG", n: int, n_boot: int) -> np.ndarray:
    """Generate n_boot bootstrap index arrays (with replacement).

    Args:
        rng: RNG object (from bossanova.ops.rng).
        n: Size of each bootstrap sample.
        n_boot: Number of bootstrap samples to generate.

    Returns:
        Shape [n_boot, n], where each row contains indices sampled with replacement.

    Examples:
        >>> from bossanova.ops.rng import RNG
        >>> rng = RNG.from_seed(42)
        >>> indices = generate_bootstrap_indices(rng, n=5, n_boot=3)
        >>> indices.shape
        (3, 5)
    """
    keys = rng.split(n_boot)
    return np.stack([np.asarray(k.choice(n, (n,), replace=True)) for k in keys])


def generate_kfold_indices(
    rng: "RNG",
    n: int,
    k: int,
    shuffle: bool = True,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Generate k-fold cross-validation train/test index splits.

    Args:
        rng: RNG object (from bossanova.ops.rng). Used if shuffle=True.
        n: Total number of observations.
        k: Number of folds.
        shuffle: Whether to shuffle indices before splitting.

    Returns:
        List of k tuples (train_indices, test_indices).

    Examples:
        >>> from bossanova.ops.rng import RNG
        >>> rng = RNG.from_seed(42)
        >>> splits = generate_kfold_indices(rng, n=10, k=5)
        >>> len(splits)
        5
        >>> train, test = splits[0]
        >>> len(train) + len(test)
        10
    """
    indices = np.arange(n)

    if shuffle:
        perm = np.asarray(rng.permutation(n))
        indices = indices[perm]

    # Compute fold sizes (handle n not divisible by k)
    fold_sizes = np.full(k, n // k, dtype=int)
    fold_sizes[: n % k] += 1

    # Create splits
    splits = []
    current = 0
    for fold_size in fold_sizes:
        test_indices = indices[current : current + fold_size]
        train_indices = np.concatenate(
            [
                indices[:current],
                indices[current + fold_size :],
            ]
        )
        splits.append((train_indices, test_indices))
        current += fold_size

    return splits


def generate_loo_indices(n: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """Generate leave-one-out cross-validation train/test index splits.

    Args:
        n: Total number of observations.

    Returns:
        List of n tuples (train_indices, test_indices), where each test set
        contains exactly one observation.

    Examples:
        >>> splits = generate_loo_indices(n=5)
        >>> len(splits)
        5
        >>> train, test = splits[0]
        >>> len(test)
        1
    """
    indices = np.arange(n)
    splits = []

    for i in range(n):
        test_indices = np.array([i])
        train_indices = np.concatenate([indices[:i], indices[i + 1 :]])
        splits.append((train_indices, test_indices))

    return splits


# =============================================================================
# P-Value Computation
# =============================================================================


def compute_pvalues(
    observed_stats: "ArrayLike",
    null_stats: "ArrayLike",
    alternative: Literal["two-sided", "greater", "less"] = "two-sided",
) -> np.ndarray:
    """Compute permutation p-values.

    Uses formula: p = (1 + sum(|T_null| >= |T_obs|)) / (B + 1)
    where B is the number of null samples.

    Args:
        observed_stats: Observed test statistics, shape [n_params] or scalar.
        null_stats: Null distribution statistics, shape [n_perm, n_params] or [n_perm].
        alternative: Type of test: "two-sided", "greater", or "less".

    Returns:
        P-values for each parameter.

    Examples:
        >>> observed = jnp.array([2.5, -1.0])
        >>> null = jnp.array([[0.1, 0.2], [-0.3, 0.5], [0.8, -0.1]])
        >>> pvals = compute_pvalues(observed, null, alternative="two-sided")
    """
    observed_stats = jnp.atleast_1d(observed_stats)
    null_stats = jnp.asarray(null_stats)

    if null_stats.ndim == 1:
        null_stats = null_stats[:, jnp.newaxis]

    n_perm = null_stats.shape[0]

    if alternative == "two-sided":
        abs_obs = jnp.abs(observed_stats)
        abs_null = jnp.abs(null_stats)
        count = jnp.sum(abs_null >= abs_obs, axis=0)
    elif alternative == "greater":
        count = jnp.sum(null_stats >= observed_stats, axis=0)
    elif alternative == "less":
        count = jnp.sum(null_stats <= observed_stats, axis=0)
    else:
        raise ValueError(
            f"alternative must be 'two-sided', 'greater', or 'less', got {alternative}"
        )

    pvalues = (1 + count) / (n_perm + 1)

    if observed_stats.shape[0] == 1:
        return pvalues[0]

    return pvalues


# =============================================================================
# Confidence Interval Methods
# =============================================================================


def bootstrap_ci_percentile(
    boot_stats: "ArrayLike",
    level: float = 0.95,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute percentile bootstrap confidence intervals.

    Args:
        boot_stats: Bootstrap statistics, shape [n_boot] or [n_boot, n_params].
        level: Confidence level (e.g., 0.95 for 95% CI).

    Returns:
        Tuple of (lower, upper) confidence bounds.

    Examples:
        >>> boot_stats = jnp.array([[1.0, 2.0], [1.5, 2.5], [0.8, 1.8]])
        >>> lower, upper = bootstrap_ci_percentile(boot_stats, level=0.95)
    """
    if boot_stats.ndim == 1:
        boot_stats = boot_stats[:, jnp.newaxis]
        squeeze_output = True
    else:
        squeeze_output = False

    alpha = 1 - level
    lower_percentile = 100 * alpha / 2
    upper_percentile = 100 * (1 - alpha / 2)

    lower = jnp.percentile(boot_stats, lower_percentile, axis=0)
    upper = jnp.percentile(boot_stats, upper_percentile, axis=0)

    if squeeze_output:
        lower = jnp.squeeze(lower)
        upper = jnp.squeeze(upper)

    return lower, upper


def bootstrap_ci_basic(
    observed: "ArrayLike",
    boot_stats: "ArrayLike",
    level: float = 0.95,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute basic (pivotal) bootstrap confidence intervals.

    The basic bootstrap CI is: [2*theta_hat - q_upper, 2*theta_hat - q_lower]
    where q_lower and q_upper are the quantiles of the bootstrap distribution.

    Args:
        observed: Observed statistic, shape [n_params] or scalar.
        boot_stats: Bootstrap statistics, shape [n_boot] or [n_boot, n_params].
        level: Confidence level (e.g., 0.95 for 95% CI).

    Returns:
        Tuple of (lower, upper) confidence bounds.

    Examples:
        >>> observed = jnp.array([1.0, 2.0])
        >>> boot_stats = jnp.array([[1.1, 2.1], [0.9, 1.9], [1.2, 2.2]])
        >>> lower, upper = bootstrap_ci_basic(observed, boot_stats, level=0.95)
    """
    observed = jnp.atleast_1d(observed)

    if boot_stats.ndim == 1:
        boot_stats = boot_stats[:, jnp.newaxis]
        squeeze_output = True
    else:
        squeeze_output = False

    alpha = 1 - level
    lower_percentile = 100 * alpha / 2
    upper_percentile = 100 * (1 - alpha / 2)

    boot_lower = jnp.percentile(boot_stats, lower_percentile, axis=0)
    boot_upper = jnp.percentile(boot_stats, upper_percentile, axis=0)

    # Basic CI: [2*observed - upper, 2*observed - lower]
    ci_lower = 2 * observed - boot_upper
    ci_upper = 2 * observed - boot_lower

    if squeeze_output:
        ci_lower = jnp.squeeze(ci_lower)
        ci_upper = jnp.squeeze(ci_upper)

    return ci_lower, ci_upper


BCa_MIN_NBOOT = 50  # Minimum bootstrap samples for reliable BCa intervals


def bootstrap_ci_bca(
    boot_stats: "ArrayLike",
    observed: "ArrayLike",
    jackknife_stats: "ArrayLike | None" = None,
    level: float = 0.95,
) -> tuple[np.ndarray, np.ndarray]:
    """BCa (bias-corrected and accelerated) bootstrap confidence intervals.

    BCa intervals adjust for bias and skewness in the bootstrap distribution,
    providing second-order accuracy. This is R's gold standard method.

    Args:
        boot_stats: Bootstrap statistics, shape [n_boot, n_params].
        observed: Observed statistic from original data, shape [n_params].
        jackknife_stats: Jackknife statistics for acceleration, shape [n, n_params].
            If None, uses a=0 (bias-corrected percentile only, no acceleration).
        level: Confidence level (default 0.95).

    Returns:
        Tuple of (lower, upper) confidence bounds.

    Raises:
        ValueError: If n_boot < BCa_MIN_NBOOT (50). BCa requires sufficient
            bootstrap samples to reliably estimate bias and acceleration.

    References:
        Efron, B. (1987). Better Bootstrap Confidence Intervals.
        DiCiccio, T. J., & Efron, B. (1996). Bootstrap confidence intervals.
    """
    boot_stats = jnp.atleast_2d(boot_stats)
    if boot_stats.shape[0] == 1:
        boot_stats = boot_stats.T  # Ensure [n_boot, n_params]

    n_boot = boot_stats.shape[0]
    if n_boot < BCa_MIN_NBOOT:
        raise ValueError(
            f"BCa confidence intervals require at least {BCa_MIN_NBOOT} bootstrap "
            f"samples, got n_boot={n_boot}. Use ci_type='percentile' for small "
            f"n_boot, or increase n_boot for BCa."
        )

    observed = jnp.atleast_1d(observed)
    alpha = 1 - level
    n_params = len(observed)

    # 1. Bias correction factor z0
    # z0 = Phi^-1(#{theta* < theta_hat}/B)
    # Note: jnp.mean on boolean array returns float32 even with x64 enabled,
    # so we must cast to float64 to preserve precision for clipping
    prop_less = jnp.mean(boot_stats < observed, axis=0).astype(jnp.float64)
    # Clip to avoid ppf(0) = -inf or ppf(1) = inf
    prop_less = jnp.clip(prop_less, 1e-10, 1 - 1e-10)
    z0 = sp_stats.norm.ppf(np.array(prop_less))

    # 2. Acceleration factor a
    if jackknife_stats is not None:
        jack_mean = jnp.mean(jackknife_stats, axis=0)
        diff = jack_mean - jackknife_stats
        numerator = jnp.sum(diff**3, axis=0)
        denominator = 6 * (jnp.sum(diff**2, axis=0) ** 1.5)
        # Small epsilon to avoid division by zero
        a = np.array(numerator / (denominator + 1e-10))
    else:
        a = np.zeros(n_params)

    # 3. Adjusted percentiles
    z_alpha_lower = sp_stats.norm.ppf(alpha / 2)
    z_alpha_upper = sp_stats.norm.ppf(1 - alpha / 2)

    def bca_percentile(z_alpha: float, z0_arr: np.ndarray, a_arr: np.ndarray):
        numerator = z0_arr + z_alpha
        denominator = 1 - a_arr * numerator
        # Protect against division by zero (can happen with small n_boot)
        # Use np.divide with out and where to avoid computing invalid values
        ratio = np.zeros_like(numerator)
        valid_mask = np.abs(denominator) >= 1e-10
        np.divide(numerator, denominator, out=ratio, where=valid_mask)
        adjusted = z0_arr + ratio
        return sp_stats.norm.cdf(adjusted)

    alpha1 = bca_percentile(z_alpha_lower, z0, a)
    alpha2 = bca_percentile(z_alpha_upper, z0, a)

    # Clip to valid percentile range
    alpha1 = np.clip(alpha1, 0.005, 0.995)
    alpha2 = np.clip(alpha2, 0.005, 0.995)

    # 4. Extract BCa intervals
    ci_lower = jnp.array(
        [jnp.percentile(boot_stats[:, i], 100 * alpha1[i]) for i in range(n_params)]
    )
    ci_upper = jnp.array(
        [jnp.percentile(boot_stats[:, i], 100 * alpha2[i]) for i in range(n_params)]
    )

    return ci_lower, ci_upper
