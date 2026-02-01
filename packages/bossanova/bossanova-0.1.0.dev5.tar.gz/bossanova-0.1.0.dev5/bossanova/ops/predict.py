"""Prediction utilities with NA handling.

Shared utilities for making predictions on new data while properly
handling missing values. Used by lm, glm, ridge, lmer, glmer predict() methods.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

__all__ = [
    "get_valid_rows",
    "init_na_array",
    "fill_valid",
]


def get_valid_rows(X: NDArray) -> tuple[NDArray[np.bool_], NDArray, int]:
    """Identify valid (non-NA) rows in a design matrix.

    Args:
        X: Design matrix of shape (n, p), may contain NaN values.

    Returns:
        Tuple of (valid_mask, X_valid, n) where:
        - valid_mask: Boolean array of shape (n,), True for rows without NaN
        - X_valid: Design matrix with only valid rows, shape (n_valid, p)
        - n: Total number of rows

    Examples:
        >>> X = np.array([[1, 2], [np.nan, 3], [4, 5]])
        >>> valid_mask, X_valid, n = get_valid_rows(X)
        >>> valid_mask
        array([ True, False,  True])
        >>> X_valid
        array([[1., 2.], [4., 5.]])
    """
    n = X.shape[0]
    valid_mask = ~np.any(np.isnan(X), axis=1)
    X_valid = X[valid_mask] if np.any(valid_mask) else np.empty((0, X.shape[1]))
    return valid_mask, X_valid, n


def init_na_array(n: int, dtype: type = np.float64) -> NDArray:
    """Create an array of NaN values.

    Args:
        n: Length of array.
        dtype: Data type (default float64).

    Returns:
        Array of NaN values with shape (n,).
    """
    return np.full(n, np.nan, dtype=dtype)


def fill_valid(
    result: NDArray,
    valid_mask: NDArray[np.bool_],
    values: NDArray,
) -> NDArray:
    """Fill valid positions in result array with computed values.

    Args:
        result: Array to fill (modified in place), shape (n,).
        valid_mask: Boolean mask indicating valid positions, shape (n,).
        values: Values to insert at valid positions, shape (n_valid,).

    Returns:
        The result array (same object, modified in place).

    Examples:
        >>> result = np.full(3, np.nan)
        >>> valid_mask = np.array([True, False, True])
        >>> values = np.array([10.0, 20.0])
        >>> fill_valid(result, valid_mask, values)
        array([10., nan, 20.])
    """
    if len(values) > 0:
        result[valid_mask] = values
    return result
