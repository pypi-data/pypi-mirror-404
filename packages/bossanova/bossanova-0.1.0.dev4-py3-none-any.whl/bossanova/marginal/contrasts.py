"""Contrast matrix builders for EMM comparisons.

This module provides utilities for building contrast matrices that
define comparisons between estimated marginal means. These matrices
are used by joint_tests() for ANOVA-style hypothesis testing.

Key concept: A contrast matrix C of shape (q, k) maps k EMMs to q contrasts.
When composed with the prediction matrix X_ref, we get L_emm = C @ X_ref
which maps coefficients directly to contrast estimates.

Examples:
    >>> from bossanova.marginal.contrasts import build_pairwise_contrast
    >>> C = build_pairwise_contrast(3)  # For 3-level factor
    >>> C
    array([[-1,  1,  0],
           [-1,  0,  1]])
"""

from __future__ import annotations

import numpy as np
from itertools import combinations

__all__ = [
    "build_contrast_matrix",
    "build_pairwise_contrast",
    "build_all_pairwise_contrast",
    "build_sum_to_zero_contrast",
    "compose_contrast",
    "get_contrast_labels",
]


def build_contrast_matrix(
    contrast_type: str | dict,
    levels: list,
    normalize: bool = False,
) -> np.ndarray:
    """Build a contrast matrix based on contrast type.

    Dispatcher function that builds the appropriate contrast matrix
    based on the contrast type specification.

    Args:
        contrast_type: Type of contrast:
            - "pairwise": All pairwise comparisons (k(k-1)/2 contrasts)
            - "revpairwise": Reversed pairwise comparisons
            - "trt.vs.ctrl" or "treatment": Compare each level to first level
            - dict: Custom contrasts with names as keys and weights as values
        levels: List of factor levels.
        normalize: If True, normalize custom contrasts to sum to 1/-1.

    Returns:
        Contrast matrix of shape (n_contrasts, n_levels).

    Raises:
        ValueError: If unknown contrast type.

    Examples:
        >>> build_contrast_matrix("pairwise", ["A", "B", "C"])
        array([[-1.,  1.,  0.],
               [-1.,  0.,  1.],
               [ 0., -1.,  1.]])
        >>> build_contrast_matrix("trt.vs.ctrl", ["A", "B", "C"])
        array([[-1.,  1.,  0.],
               [-1.,  0.,  1.]])
    """
    n_levels = len(levels)

    if isinstance(contrast_type, dict):
        # Custom contrasts
        contrasts = []
        for weights in contrast_type.values():
            if isinstance(weights, np.ndarray):
                c = weights.astype(float)
            else:
                c = np.array(weights, dtype=float)
            if normalize:
                # L2 normalization (same as set_contrasts)
                l2_norm = np.linalg.norm(c)
                if l2_norm > 0:
                    c = c / l2_norm
            contrasts.append(c)
        return np.array(contrasts)

    elif contrast_type == "pairwise":
        # All pairwise comparisons: B-A, C-A, C-B, ...
        return build_all_pairwise_contrast(n_levels)

    elif contrast_type == "revpairwise":
        # Reversed pairwise: A-B, A-C, B-C, ...
        return -build_all_pairwise_contrast(n_levels)

    elif contrast_type in ("trt.vs.ctrl", "treatment"):
        # Each level vs first level
        return build_pairwise_contrast(n_levels)

    else:
        raise ValueError(
            f"Unknown contrast type: {contrast_type!r}\n\n"
            "Supported types:\n"
            "  - 'pairwise': All pairwise comparisons\n"
            "  - 'revpairwise': Reversed pairwise\n"
            "  - 'trt.vs.ctrl': Each level vs first level\n"
            "  - dict: Custom contrasts {name: weights}"
        )


def build_pairwise_contrast(n_levels: int) -> np.ndarray:
    """Build (n-1) linearly independent pairwise contrasts.

    Creates "treatment-style" contrasts comparing each level to the
    first (reference) level. This produces n_levels - 1 contrasts that
    span the space of all pairwise differences.

    Args:
        n_levels: Number of EMM levels (factor levels).

    Returns:
        Contrast matrix of shape (n_levels - 1, n_levels).
        Row i compares level i+1 to level 0.

    Raises:
        ValueError: If n_levels < 1.

    Examples:
        >>> C = build_pairwise_contrast(3)
        >>> C
        array([[-1.,  1.,  0.],
               [-1.,  0.,  1.]])

        This creates 2 contrasts for 3 levels:
        - Row 0: Level 1 - Level 0 (comparing B to A)
        - Row 1: Level 2 - Level 0 (comparing C to A)

    Note:
        These (n-1) contrasts are linearly independent and sufficient
        for testing the null hypothesis that all EMMs are equal.
        This matches R's emmeans behavior for joint_tests().
    """
    if n_levels < 1:
        raise ValueError(f"n_levels must be >= 1, got {n_levels}")

    if n_levels == 1:
        # Single level - no contrasts possible
        return np.zeros((0, 1))

    # Create (n-1) x n matrix
    C = np.zeros((n_levels - 1, n_levels))

    for i in range(n_levels - 1):
        C[i, 0] = -1  # Reference level (first level)
        C[i, i + 1] = 1  # Level being compared

    return C


def build_all_pairwise_contrast(n_levels: int) -> np.ndarray:
    """Build all pairwise contrasts between EMM levels.

    Creates C(n, 2) = n*(n-1)/2 contrasts for all unique pairs.
    Unlike build_pairwise_contrast(), this includes all pairs,
    not just comparisons to the reference level.

    Args:
        n_levels: Number of EMM levels (factor levels).

    Returns:
        Contrast matrix of shape (n*(n-1)/2, n_levels).
        Each row compares two levels (level_j - level_i where j > i).

    Raises:
        ValueError: If n_levels < 1.

    Examples:
        >>> C = build_all_pairwise_contrast(3)
        >>> C
        array([[-1.,  1.,  0.],
               [-1.,  0.,  1.],
               [ 0., -1.,  1.]])

        This creates 3 contrasts for 3 levels (A, B, C):
        - Row 0: B - A
        - Row 1: C - A
        - Row 2: C - B

    Note:
        This is used for pairwise() method which reports all comparisons.
        For joint_tests(), use build_pairwise_contrast() instead.
    """
    if n_levels < 1:
        raise ValueError(f"n_levels must be >= 1, got {n_levels}")

    if n_levels == 1:
        # Single level - no contrasts possible
        return np.zeros((0, 1))

    # Number of contrasts: C(n, 2)
    n_contrasts = n_levels * (n_levels - 1) // 2

    C = np.zeros((n_contrasts, n_levels))

    # Generate all pairs (i, j) where i < j
    row = 0
    for i, j in combinations(range(n_levels), 2):
        C[row, i] = -1  # Subtract level i
        C[row, j] = 1  # Add level j
        row += 1

    return C


def build_sum_to_zero_contrast(n_levels: int) -> np.ndarray:
    """Build sum-to-zero contrasts (deviation coding).

    Creates contrasts comparing each level to the grand mean.
    This is useful for Type III SS interpretation with sum coding.

    Args:
        n_levels: Number of EMM levels.

    Returns:
        Contrast matrix of shape (n_levels - 1, n_levels).

    Examples:
        >>> C = build_sum_to_zero_contrast(3)
        >>> C
        array([[ 0.667, -0.333, -0.333],
               [-0.333,  0.667, -0.333]])
    """
    if n_levels < 1:
        raise ValueError(f"n_levels must be >= 1, got {n_levels}")

    if n_levels == 1:
        return np.zeros((0, 1))

    # Each row compares one level to the mean of all others
    C = np.zeros((n_levels - 1, n_levels))

    for i in range(n_levels - 1):
        # Level i gets coefficient (n-1)/n
        C[i, i] = (n_levels - 1) / n_levels
        # All other levels get -1/n
        for j in range(n_levels):
            if j != i:
                C[i, j] = -1 / n_levels

    return C


def compose_contrast(
    C: np.ndarray,
    X_ref: np.ndarray,
) -> np.ndarray:
    """Compose contrast matrix with prediction matrix.

    This produces a matrix L_emm that maps coefficients directly to
    contrast estimates:
        L_emm @ β = C @ (X_ref @ β) = C @ EMMs

    Args:
        C: Contrast matrix of shape (n_contrasts, n_emms).
        X_ref: Prediction matrix of shape (n_emms, n_coef).

    Returns:
        Composed contrast matrix L_emm of shape (n_contrasts, n_coef).

    Note:
        This composition is the key to joint_tests():
        - X_ref maps β → EMMs
        - C maps EMMs → contrasts
        - L_emm = C @ X_ref maps β → contrasts directly

        The F-test is then performed on H₀: L_emm @ β = 0
    """
    return C @ X_ref


def get_contrast_labels(
    levels: list[str],
    contrast_type: str = "pairwise",
) -> list[str]:
    """Generate human-readable labels for contrasts.

    Args:
        levels: List of factor level names.
        contrast_type: Type of contrast ("pairwise" or "all_pairwise").

    Returns:
        List of contrast labels like "B - A", "C - A", etc.

    Examples:
        >>> get_contrast_labels(["A", "B", "C"], "pairwise")
        ['B - A', 'C - A']
        >>> get_contrast_labels(["A", "B", "C"], "all_pairwise")
        ['B - A', 'C - A', 'C - B']
    """
    n = len(levels)

    if contrast_type == "pairwise":
        # Reference contrasts
        return [f"{levels[i + 1]} - {levels[0]}" for i in range(n - 1)]

    elif contrast_type == "all_pairwise":
        # All pairs
        return [f"{levels[j]} - {levels[i]}" for i, j in combinations(range(n), 2)]

    else:
        raise ValueError(f"Unknown contrast_type: {contrast_type}")
