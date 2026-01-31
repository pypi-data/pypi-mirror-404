"""Shared utilities for resampling operations.

This module provides helper functions that abstract common patterns
in permutation tests and bootstrap procedures, reducing duplication
between JAX and NumPy implementations.
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np

from bossanova._backend import get_backend

# Type alias for arrays (works with both JAX and NumPy)
Array = Any

__all__ = [
    "Array",
    "compute_observed_statistic",
    "compute_permuted_statistic",
    "compute_bootstrap_statistic",
    "stack_results",
    "validate_boot_type",
    "validate_ci_type",
]


def compute_observed_statistic(
    coef: Array,
    se: Array | None,
    test_stat: Literal["t", "coef", "abs_coef"],
) -> Array:
    """Compute observed test statistic from coefficients.

    Args:
        coef: Coefficient estimates, shape (p,).
        se: Standard errors, shape (p,). Required if test_stat="t".
        test_stat: Type of test statistic.

    Returns:
        Observed statistic, shape (p,).

    Raises:
        ValueError: If test_stat is invalid.
    """
    backend = get_backend()

    if test_stat == "t":
        if se is None:
            raise ValueError("se required for test_stat='t'")
        return coef / se
    elif test_stat == "coef":
        return coef
    elif test_stat == "abs_coef":
        if backend == "jax":
            import jax.numpy as jnp

            return jnp.abs(coef)
        else:
            return np.abs(coef)
    else:
        raise ValueError(
            f"test_stat must be 't', 'coef', or 'abs_coef', got {test_stat}"
        )


def compute_permuted_statistic(
    coef: Array,
    se: Array | None,
    test_stat: Literal["t", "coef", "abs_coef"],
) -> Array:
    """Compute permuted test statistic (same logic as observed).

    This is a separate function for clarity in the calling code,
    but the logic is identical to compute_observed_statistic.
    """
    return compute_observed_statistic(coef, se, test_stat)


def compute_bootstrap_statistic(
    y_boot: Array,
    fitted: Array,
    residuals_centered: Array,
    sigma: float,
    boot_type: Literal["residual", "case", "parametric"],
    boot_idx: Array,
    rng_key: Any,
) -> Array:
    """Compute bootstrapped y values based on bootstrap type.

    Args:
        y_boot: Not used, kept for signature compatibility.
        fitted: Fitted values from original model.
        residuals_centered: Centered residuals (y - fitted - mean(y - fitted)).
        sigma: Residual standard error.
        boot_type: Type of bootstrap.
        boot_idx: Bootstrap indices for case/residual resampling.
        rng_key: RNG key for parametric bootstrap.

    Returns:
        Bootstrapped y values.

    Note:
        For case bootstrap, X must also be resampled at the call site.
    """
    backend = get_backend()
    n = len(fitted)

    if boot_type == "residual":
        if backend == "jax":
            import jax.numpy as jnp

            resid_boot = jnp.asarray(residuals_centered)[boot_idx]
            return jnp.asarray(fitted) + resid_boot
        else:
            resid_boot = np.asarray(residuals_centered)[boot_idx]
            return np.asarray(fitted) + resid_boot

    elif boot_type == "parametric":
        if backend == "jax":
            import jax.numpy as jnp
            import jax.random as jr

            errors = jr.normal(rng_key, shape=(n,)) * sigma
            return jnp.asarray(fitted) + errors
        else:
            # rng_key is an RNG object for NumPy
            errors = rng_key.normal(shape=(n,)) * sigma
            return np.asarray(fitted) + errors

    else:
        raise ValueError(
            f"boot_type must be 'residual', 'case', or 'parametric', got {boot_type}"
        )


def stack_results(results: list[Array]) -> Array:
    """Stack list of arrays into a single array.

    Uses the appropriate backend for stacking.

    Args:
        results: List of arrays to stack.

    Returns:
        Stacked array with shape (len(results), *results[0].shape).
    """
    backend = get_backend()

    if backend == "jax":
        import jax.numpy as jnp

        return jnp.stack(results, axis=0)
    else:
        return np.stack(results, axis=0)


def validate_boot_type(
    boot_type: str,
    valid_types: tuple[str, ...] = ("residual", "case", "parametric"),
) -> None:
    """Validate bootstrap type parameter.

    Args:
        boot_type: Bootstrap type to validate.
        valid_types: Tuple of valid bootstrap types.

    Raises:
        ValueError: If boot_type is not valid.
    """
    if boot_type not in valid_types:
        valid_str = ", ".join(f"'{t}'" for t in valid_types)
        raise ValueError(f"boot_type must be {valid_str}, got {boot_type}")


def validate_ci_type(
    ci_type: str,
    valid_types: tuple[str, ...] = ("percentile", "basic", "bca"),
) -> None:
    """Validate confidence interval type parameter.

    Args:
        ci_type: CI type to validate.
        valid_types: Tuple of valid CI types.

    Raises:
        ValueError: If ci_type is not valid.
    """
    if ci_type not in valid_types:
        valid_str = ", ".join(f"'{t}'" for t in valid_types)
        raise ValueError(f"ci_type must be {valid_str}, got {ci_type}")
