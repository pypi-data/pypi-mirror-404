"""Contrast matrix builders for categorical variable encoding.

This module provides functions to create contrast matrices for encoding
categorical variables in design matrices. These are distinct from the
EMM contrast matrices in bossanova.marginal.contrasts.

Key concept: A contrast matrix maps k categorical levels to k-1 columns
in the design matrix (assuming an intercept absorbs one degree of freedom).

Supported contrast types:
    - Treatment (dummy coding): Reference level = 0, others = one-hot
    - Sum (effects coding): Omitted level = -1s, others = one-hot
    - Poly (orthogonal polynomial): Linear, quadratic, cubic, etc. trends
    - Custom: User-specified contrast vectors converted via array_to_coding_matrix

Examples:
    >>> from bossanova.formula.contrasts import treatment_contrast, sum_contrast, poly_contrast
    >>> treatment_contrast(['A', 'B', 'C'])
    array([[0., 0.],
           [1., 0.],
           [0., 1.]])
    >>> sum_contrast(['A', 'B', 'C'])
    array([[ 1.,  0.],
           [ 0.,  1.],
           [-1., -1.]])
    >>> poly_contrast(['A', 'B', 'C'])  # Linear and quadratic trends
    array([[-0.707...,  0.408...],
           [ 0.   ..., -0.816...],
           [ 0.707...,  0.408...]])
    >>> # Custom contrast: A vs average(B, C)
    >>> array_to_coding_matrix([[-1, 0.5, 0.5]], n_levels=3)
    array([[-0.816..., ...],
           [ 0.408..., ...],
           [ 0.408..., ...]])
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

__all__ = [
    "treatment_contrast",
    "treatment_labels",
    "sum_contrast",
    "sum_labels",
    "poly_contrast",
    "poly_labels",
    "poly_numeric",
    "poly_numeric_labels",
    "array_to_coding_matrix",
    "coding_to_hypothesis",
]


def treatment_contrast(
    levels: list[str],
    reference: str | None = None,
) -> NDArray[np.float64]:
    """Build treatment (dummy) contrast matrix.

    Treatment coding sets the reference level to all zeros, and each
    other level gets a one-hot encoded row. This is the most common
    coding for regression models with an intercept.

    Args:
        levels: Ordered list of categorical level names.
        reference: Reference level name. Defaults to first level.

    Returns:
        Contrast matrix of shape (n_levels, n_levels - 1).
        Row order matches input levels order.

    Raises:
        ValueError: If levels has fewer than 2 elements or reference not in levels.

    Examples:
        >>> treatment_contrast(['A', 'B', 'C'])
        array([[0., 0.],
               [1., 0.],
               [0., 1.]])

        >>> treatment_contrast(['A', 'B', 'C'], reference='B')
        array([[1., 0.],
               [0., 0.],
               [0., 1.]])
    """
    n_levels = len(levels)
    if n_levels < 2:
        raise ValueError(f"Need at least 2 levels, got {n_levels}")

    if reference is None:
        reference = levels[0]

    if reference not in levels:
        raise ValueError(f"Reference '{reference}' not in levels: {levels}")

    ref_idx = levels.index(reference)

    # Build matrix: (n_levels, n_levels - 1)
    # Reference row is all zeros, others are one-hot
    matrix = np.zeros((n_levels, n_levels - 1), dtype=np.float64)

    col = 0
    for i in range(n_levels):
        if i != ref_idx:
            matrix[i, col] = 1.0
            col += 1

    return matrix


def treatment_labels(levels: list[str], reference: str | None = None) -> list[str]:
    """Get column labels for treatment contrast.

    Args:
        levels: Ordered list of categorical level names.
        reference: Reference level name. Defaults to first level.

    Returns:
        List of non-reference level names (column labels).
    """
    if reference is None:
        reference = levels[0]
    return [lvl for lvl in levels if lvl != reference]


def sum_contrast(
    levels: list[str],
    omit: str | None = None,
) -> NDArray[np.float64]:
    """Build sum (effects) contrast matrix.

    Sum coding sets the omitted level to all -1s, and each other level
    gets a one-hot encoded row. This centers the effects around zero,
    making coefficients interpretable as deviations from the grand mean.

    Args:
        levels: Ordered list of categorical level names.
        omit: Level to omit (gets -1s). Defaults to last level.

    Returns:
        Contrast matrix of shape (n_levels, n_levels - 1).
        Row order matches input levels order.

    Raises:
        ValueError: If levels has fewer than 2 elements or omit not in levels.

    Examples:
        >>> sum_contrast(['A', 'B', 'C'])
        array([[ 1.,  0.],
               [ 0.,  1.],
               [-1., -1.]])

        >>> sum_contrast(['A', 'B', 'C'], omit='A')
        array([[-1., -1.],
               [ 1.,  0.],
               [ 0.,  1.]])
    """
    n_levels = len(levels)
    if n_levels < 2:
        raise ValueError(f"Need at least 2 levels, got {n_levels}")

    if omit is None:
        omit = levels[-1]

    if omit not in levels:
        raise ValueError(f"Omit level '{omit}' not in levels: {levels}")

    omit_idx = levels.index(omit)

    # Build matrix: (n_levels, n_levels - 1)
    # Omitted row is all -1s, others are one-hot
    matrix = np.zeros((n_levels, n_levels - 1), dtype=np.float64)

    col = 0
    for i in range(n_levels):
        if i == omit_idx:
            matrix[i, :] = -1.0
        else:
            matrix[i, col] = 1.0
            col += 1

    return matrix


def sum_labels(levels: list[str], omit: str | None = None) -> list[str]:
    """Get column labels for sum contrast.

    Args:
        levels: Ordered list of categorical level names.
        omit: Level to omit. Defaults to last level.

    Returns:
        List of non-omitted level names (column labels).
    """
    if omit is None:
        omit = levels[-1]
    return [lvl for lvl in levels if lvl != omit]


def poly_contrast(levels: list[str]) -> NDArray[np.float64]:
    """Build orthogonal polynomial contrast matrix.

    Polynomial coding creates orthogonal contrasts representing linear,
    quadratic, cubic, etc. trends across ordered factor levels. This is
    equivalent to R's contr.poly() function.

    The contrasts are orthonormal (orthogonal and unit length), making
    them suitable for testing polynomial trends in ordered categorical
    variables.

    Args:
        levels: Ordered list of categorical level names. The order determines
            the polynomial evaluation points.

    Returns:
        Contrast matrix of shape (n_levels, n_levels - 1).
        Column 0 is linear (.L), column 1 is quadratic (.Q), etc.

    Raises:
        ValueError: If levels has fewer than 2 elements.

    Examples:
        >>> poly_contrast(['low', 'medium', 'high'])
        array([[-0.70710678,  0.40824829],
               [ 0.        , -0.81649658],
               [ 0.70710678,  0.40824829]])

        >>> poly_contrast(['A', 'B', 'C', 'D'])
        array([[-0.67082039,  0.5       , -0.2236068 ],
               [-0.2236068 , -0.5       ,  0.67082039],
               [ 0.2236068 , -0.5       , -0.67082039],
               [ 0.67082039,  0.5       ,  0.2236068 ]])

    Note:
        Level names are not used in computation - only the count and order
        matter. The polynomial is evaluated at equally-spaced points 1, 2, ..., n.
    """
    n_levels = len(levels)
    if n_levels < 2:
        raise ValueError(f"Need at least 2 levels, got {n_levels}")

    # Create Vandermonde-like matrix with centered points
    x = np.arange(1, n_levels + 1, dtype=np.float64)
    x = x - x.mean()  # center

    # Build design matrix: [1, x, x^2, x^3, ...]
    X = np.column_stack([x**i for i in range(n_levels)])

    # QR decomposition gives orthonormal basis
    Q, _ = np.linalg.qr(X)

    # Drop first column (intercept), keep remaining orthonormal columns
    result = Q[:, 1:]

    # Apply R's sign convention:
    # - Linear term: should increase (last row positive)
    # - Quadratic term: should be "U" shaped (first and last rows positive)
    # - Cubic term: should follow linear pattern (last row positive)
    # - Pattern: odd degrees follow linear, even degrees follow quadratic
    if result[-1, 0] < 0:
        result[:, 0] *= -1

    for j in range(1, result.shape[1]):
        if j % 2 == 1:  # quadratic, quartic, etc. (even polynomial degree)
            if result[0, j] < 0:
                result[:, j] *= -1
        else:  # cubic, quintic, etc. (odd polynomial degree > 1)
            if result[-1, j] < 0:
                result[:, j] *= -1

    return result


def poly_labels(levels: list[str]) -> list[str]:
    """Get column labels for polynomial contrast.

    Args:
        levels: Ordered list of categorical level names.

    Returns:
        List of polynomial degree labels: ['.L', '.Q', '.C', '^4', '^5', ...].
    """
    n_levels = len(levels)
    labels = []
    degree_names = [".L", ".Q", ".C"]  # Linear, Quadratic, Cubic

    for i in range(n_levels - 1):
        if i < len(degree_names):
            labels.append(degree_names[i])
        else:
            labels.append(f"^{i + 1}")

    return labels


def poly_numeric(
    x: NDArray[np.floating],
    degree: int,
    *,
    normalize: bool = True,
    state: dict | None = None,
) -> tuple[NDArray[np.float64], dict]:
    """Build orthogonal polynomial basis for numeric variable.

    Creates polynomial columns for a continuous variable, optionally
    orthonormalized via QR decomposition. This is equivalent to R's
    poly() function for numeric vectors.

    Args:
        x: Numeric array of observations.
        degree: Maximum polynomial degree (number of columns to create).
        normalize: If True (default), orthonormalize columns via QR decomposition.
            If False, return raw centered polynomial powers.
        state: Optional state dict from previous fit (for predictions on new data).
            If provided, uses stored parameters instead of fitting.

    Returns:
        Tuple of (matrix, state) where:
            - matrix: Array of shape (n, degree) with polynomial columns
            - state: Dict with parameters for transforming new data

    Raises:
        ValueError: If degree < 1 or degree >= n_observations.

    Examples:
        >>> x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        >>> poly, state = poly_numeric(x, degree=2)
        >>> poly.shape
        (5, 2)
        >>> # Use state for new data
        >>> x_new = np.array([2.5, 3.5])
        >>> poly_new, _ = poly_numeric(x_new, degree=2, state=state)

    Note:
        When normalize=True, columns are orthonormal and have unit length.
        When normalize=False, columns are [x-mean, (x-mean)^2, ..., (x-mean)^d].
    """
    x = np.asarray(x, dtype=np.float64).ravel()
    n = len(x)

    if degree < 1:
        raise ValueError(f"Degree must be >= 1, got {degree}")
    if degree >= n:
        raise ValueError(
            f"Degree ({degree}) must be less than number of observations ({n})"
        )

    # Fitting: compute parameters from training data
    if state is None:
        center = float(np.nanmean(x))
        x_centered = x - center

        # Build raw polynomial matrix: [x, x^2, ..., x^d]
        raw_poly = np.column_stack([x_centered ** (i + 1) for i in range(degree)])

        if normalize:
            # QR decomposition for orthonormal basis
            # Prepend intercept column to get proper orthogonalization
            with_intercept = np.column_stack([np.ones(n), raw_poly])
            Q, R = np.linalg.qr(with_intercept)
            # Drop intercept column
            result = Q[:, 1 : degree + 1].copy()

            # Apply sign convention: each column's sum should be positive
            # (or if sum is ~0, largest absolute value should be positive)
            for j in range(result.shape[1]):
                col = result[:, j]
                if np.sum(col) < 0 or (
                    abs(np.sum(col)) < 1e-10 and col[np.argmax(np.abs(col))] < 0
                ):
                    result[:, j] *= -1

            # Store transformation for new data
            # The projection from raw to orthonormal: result = raw_poly @ coefs
            # Solve: coefs = lstsq(raw_poly, result)
            coefs, _, _, _ = np.linalg.lstsq(raw_poly, result, rcond=None)

            state = {
                "center": center,
                "normalize": True,
                "coefs": coefs.tolist(),  # (degree, degree) matrix
                "degree": degree,
            }
        else:
            result = raw_poly
            state = {
                "center": center,
                "normalize": False,
                "degree": degree,
            }

        return result, state

    # Transforming: use stored parameters
    else:
        center = state["center"]
        x_centered = x - center

        # Build raw polynomial matrix
        raw_poly = np.column_stack([x_centered ** (i + 1) for i in range(degree)])

        if state.get("normalize", True):
            # Apply stored transformation
            coefs = np.array(state["coefs"])
            result = raw_poly @ coefs
        else:
            result = raw_poly

        return result, state


def poly_numeric_labels(var_name: str, degree: int) -> list[str]:
    """Get column labels for numeric polynomial.

    Args:
        var_name: Variable name.
        degree: Polynomial degree.

    Returns:
        List of column labels: ['var[poly^1]', 'var[poly^2]', ...].

    Examples:
        >>> poly_numeric_labels('x', 3)
        ['x[poly^1]', 'x[poly^2]', 'x[poly^3]']
    """
    return [f"{var_name}[poly^{i + 1}]" for i in range(degree)]


def array_to_coding_matrix(
    contrasts: NDArray[np.floating] | list[float] | list[list[float]],
    n_levels: int,
    *,
    normalize: bool = True,
) -> NDArray[np.float64]:
    """Convert user-specified contrasts to a coding matrix for design matrices.

    This function converts "human-readable" contrast specifications (where each
    row represents a hypothesis like "A vs average(B, C)") into a coding matrix
    suitable for use in regression design matrices.

    The algorithm uses QR decomposition to auto-complete under-specified
    contrasts with orthogonal contrasts, following the approach from R's
    gmodels::make.contrasts() and pymer4's con2R().

    Args:
        contrasts: User-specified contrasts as:
            - 1D array/list: Single contrast vector of length n_levels
            - 2D array/list: Multiple contrasts, shape (n_contrasts, n_levels)
            Each row sums to zero for valid contrasts.
        n_levels: Number of factor levels. Must match contrast dimensions.
        normalize: If True, normalize each contrast vector by its L2 norm
            before conversion. This puts contrasts in standard-deviation
            units similar to orthogonal polynomial contrasts.

    Returns:
        Coding matrix of shape (n_levels, n_levels - 1). Each row corresponds
        to a factor level, each column to a design matrix column.

    Raises:
        ValueError: If contrasts dimensions don't match n_levels.
        ValueError: If too many contrasts specified (must be < n_levels).
        ValueError: If contrasts are collinear (singular matrix).

    Examples:
        >>> # Single contrast: A vs average(B, C)
        >>> array_to_coding_matrix([-1, 0.5, 0.5], n_levels=3)
        array([[-0.81649658,  0.        ],
               [ 0.40824829, -0.70710678],
               [ 0.40824829,  0.70710678]])

        >>> # Multiple contrasts: A vs B, and (A,B) vs C
        >>> array_to_coding_matrix([[-1, 1, 0], [-0.5, -0.5, 1]], n_levels=3)
        array([[-0.5       , -0.28867513],
               [ 0.5       , -0.28867513],
               [ 0.        ,  0.57735027]])

    Note:
        The returned matrix has n_levels-1 columns because one degree of
        freedom is absorbed by the intercept. If you specify fewer than
        n_levels-1 contrasts, the remaining columns are auto-completed
        with orthogonal contrasts via QR decomposition.
    """
    # Convert to numpy array and ensure 2D
    arr = np.asarray(contrasts, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    elif arr.ndim > 2:
        raise ValueError(f"Contrasts must be 1D or 2D array, got {arr.ndim}D")

    n_contrasts, n_cols = arr.shape

    # Validate dimensions
    if n_cols != n_levels:
        raise ValueError(
            f"Contrast columns ({n_cols}) must match number of levels ({n_levels})"
        )

    # At most k-1 contrasts for k levels
    if n_contrasts >= n_levels:
        raise ValueError(
            f"Too many contrasts ({n_contrasts}). "
            f"Must be less than number of levels ({n_levels})."
        )

    # Optionally normalize each contrast vector
    if normalize:
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        # Avoid division by zero
        norms = np.where(norms == 0, 1, norms)
        arr = arr / norms

    # Compute pseudoinverse to get coding columns
    # Input: (n_contrasts, n_levels), Output: (n_levels, n_contrasts)
    pinv = np.linalg.pinv(arr)

    # QR decomposition with intercept prepended to find orthogonal completion
    # Prepend ones column for intercept
    augmented = np.column_stack([np.ones(n_levels), pinv])
    Q, R = np.linalg.qr(augmented, mode="complete")

    # Check rank to detect collinear contrasts
    expected_rank = n_contrasts + 1  # intercept + user contrasts
    actual_rank = np.linalg.matrix_rank(R)
    if actual_rank != expected_rank:
        raise ValueError(
            "Singular contrast matrix. Some contrasts are perfectly collinear."
        )

    # Take columns 1 to n_levels-1 from Q (skip intercept column)
    # This gives us the orthogonal basis for the contrast space
    coding_matrix = Q[:, 1:n_levels].copy()

    # Replace first n_contrasts columns with the pseudoinverse values
    # (these represent the user's specified contrasts)
    coding_matrix[:, :n_contrasts] = pinv

    return coding_matrix


def coding_to_hypothesis(coding_matrix: NDArray[np.float64]) -> NDArray[np.float64]:
    """Convert a coding matrix back to interpretable hypothesis contrasts.

    This is the inverse of array_to_coding_matrix. Given a coding matrix
    (n_levels, n_levels-1), returns the hypothesis matrix where each row
    represents the linear combination of factor levels being compared.

    Args:
        coding_matrix: Coding matrix of shape (n_levels, n_levels - 1).

    Returns:
        Hypothesis matrix of shape (n_levels - 1, n_levels). Each row
        represents a contrast hypothesis (coefficients for factor levels).

    Examples:
        >>> cm = treatment_contrast(['A', 'B', 'C'])
        >>> coding_to_hypothesis(cm)
        array([[-1.,  1.,  0.],
               [-1.,  0.,  1.]])
    """
    n_levels = coding_matrix.shape[0]

    # Prepend intercept column
    augmented = np.column_stack([np.ones(n_levels), coding_matrix])

    # Inverse gives us the hypothesis contrasts
    return np.linalg.inv(augmented)[1:, :]
