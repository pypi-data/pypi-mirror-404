"""Global configuration for bossanova.

This module provides package-wide configuration settings that can be modified
at runtime. Currently manages singular tolerance for mixed models.
"""

# Default singular tolerance matches lme4's default (utilities.R:924-928)
_SINGULAR_TOLERANCE: float = 1e-4


def get_singular_tolerance() -> float:
    """Get the current singular tolerance for mixed models.

    The singular tolerance is used by `isSingular()` to determine if a mixed
    model fit is singular (has variance components at or near zero).

    Returns:
        The current singular tolerance threshold.

    Examples:
        >>> from bossanova import get_singular_tolerance
        >>> get_singular_tolerance()
        0.0001
    """
    return _SINGULAR_TOLERANCE


def set_singular_tolerance(tol: float) -> None:
    """Set the global singular tolerance for mixed models.

    The singular tolerance is used by `isSingular()` to determine if a mixed
    model fit is singular. Values below this threshold are considered
    effectively zero.

    Args:
        tol: New tolerance threshold. Must be positive.

    Raises:
        ValueError: If tol is not positive.

    Examples:
        >>> from bossanova import set_singular_tolerance
        >>> set_singular_tolerance(1e-6)  # More strict threshold
    """
    global _SINGULAR_TOLERANCE
    if tol <= 0:
        raise ValueError(f"Tolerance must be positive, got {tol}")
    _SINGULAR_TOLERANCE = tol
