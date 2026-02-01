"""Internal utilities for bossanova.

This module contains shared helper functions used across the package.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    import pandas as pd


def remove_predictor_from_formula(formula: str, predictor: str) -> str:
    """Remove a predictor term from a formula string.

    Handles various predictor formats including raw names, factor(), C(), c().

    Args:
        formula: R-style formula string (e.g., "y ~ x1 + x2").
        predictor: Name of predictor to remove.

    Returns:
        Modified formula with predictor removed, or original if removal fails.

    Examples:
        >>> remove_predictor_from_formula("y ~ a + b + c", "b")
        'y ~ a + c'
        >>> remove_predictor_from_formula("y ~ factor(a) + b", "a")
        'y ~ b'
    """
    parts = formula.split("~")
    if len(parts) != 2:
        return formula

    lhs, rhs = parts[0].strip(), parts[1].strip()

    # Patterns to match: factor(pred), C(pred), c(pred), or raw pred
    patterns = [
        rf"\bfactor\({re.escape(predictor)}\)",
        rf"\bC\({re.escape(predictor)}\)",
        rf"\bc\({re.escape(predictor)}\)",
        rf"\b{re.escape(predictor)}\b",
    ]

    new_rhs = rhs
    for pattern in patterns:
        # Remove " + term" or "term + "
        new_rhs = re.sub(rf"\s*\+\s*{pattern}", "", new_rhs)
        new_rhs = re.sub(rf"{pattern}\s*\+\s*", "", new_rhs)
        # Remove standalone term
        new_rhs = re.sub(pattern, "", new_rhs)

    # Clean up whitespace and extra + signs
    new_rhs = re.sub(r"\s+", " ", new_rhs).strip()
    new_rhs = re.sub(r"\+\s*\+", "+", new_rhs)
    new_rhs = new_rhs.strip("+ ")

    # If nothing changed, return original
    if new_rhs == rhs:
        return formula

    # If RHS is empty after removal, use intercept-only model
    if not new_rhs:
        return f"{lhs} ~ 1"

    return f"{lhs} ~ {new_rhs}"


def coerce_dataframe(data: pl.DataFrame | pd.DataFrame) -> pl.DataFrame:
    """Convert pandas DataFrame to polars if needed.

    Args:
        data: Input DataFrame (polars or pandas).

    Returns:
        Polars DataFrame.

    Raises:
        TypeError: If data is not a polars or pandas DataFrame.
    """
    if isinstance(data, pl.DataFrame):
        return data

    # Lazy import to avoid requiring pandas
    import pandas as pd_module

    if isinstance(data, pd_module.DataFrame):
        return pl.from_pandas(data)

    raise TypeError(f"data must be DataFrame, got {type(data)}")
