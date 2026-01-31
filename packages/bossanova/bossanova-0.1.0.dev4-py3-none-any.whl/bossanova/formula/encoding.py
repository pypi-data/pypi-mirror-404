"""Categorical variable encoding using Polars Enum.

This module provides utilities for encoding categorical variables using
Polars Enum types. The key insight is that Polars Enum + .to_physical()
provides a clean replacement for pandas Categorical + .codes:

- Enum has explicit, immutable level ordering
- .to_physical() returns uint8/uint32 integer codes
- First level in Enum = code 0 = reference level for treatment contrasts

Examples:
    >>> import polars as pl
    >>> from bossanova.formula.encoding import ensure_enum, encode_categorical
    >>> from bossanova.formula.contrasts import treatment_contrast
    >>>
    >>> df = pl.DataFrame({'group': ['B', 'A', 'C', 'A', 'B']})
    >>> df = ensure_enum(df, {'group': ['A', 'B', 'C']})
    >>> contrast = treatment_contrast(['A', 'B', 'C'])
    >>> encoded = encode_categorical(df['group'], contrast)
    >>> encoded
    array([[1., 0.],
           [0., 0.],
           [0., 1.],
           [0., 0.],
           [1., 0.]])
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import polars as pl
from numpy.typing import NDArray

if TYPE_CHECKING:
    from bossanova._parser.expr import Binary, Call, Variable

__all__ = [
    "encode_categorical",
    "ensure_enum",
    "get_levels",
    "infer_levels",
    "detect_categoricals",
]


def encode_categorical(
    series: pl.Series,
    contrast: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Encode a categorical series using a contrast matrix.

    Takes a Polars series (must be Enum or Categorical type) and applies
    contrast encoding by indexing into the contrast matrix with the
    integer codes.

    Args:
        series: Polars series with Enum or Categorical dtype.
        contrast: Contrast matrix of shape (n_levels, n_columns).
            Row order must match the series' category order.

    Returns:
        Encoded array of shape (n_obs, n_columns).

    Raises:
        ValueError: If series is not categorical or has wrong number of levels.

    Examples:
        >>> import polars as pl
        >>> from bossanova.formula.contrasts import treatment_contrast
        >>> series = pl.Series('x', ['B', 'A', 'C']).cast(pl.Enum(['A', 'B', 'C']))
        >>> contrast = treatment_contrast(['A', 'B', 'C'])
        >>> encode_categorical(series, contrast)
        array([[1., 0.],
               [0., 0.],
               [0., 1.]])
    """
    # Validate dtype
    if not isinstance(series.dtype, (pl.Enum, pl.Categorical)):
        raise ValueError(f"Series must be Enum or Categorical, got {series.dtype}")

    # Get integer codes via to_physical()
    codes = series.to_physical().to_numpy()

    # Validate level count matches contrast matrix
    n_levels = contrast.shape[0]
    max_code = codes.max() if len(codes) > 0 else 0
    if max_code >= n_levels:
        raise ValueError(
            f"Series has codes up to {max_code} but contrast has only {n_levels} levels"
        )

    # Fancy indexing: select rows from contrast matrix
    return contrast[codes]


def ensure_enum(
    data: pl.DataFrame,
    factors: dict[str, list[str]],
) -> pl.DataFrame:
    """Convert columns to Enum type with specified level ordering.

    This function converts string/categorical columns to Polars Enum type,
    ensuring consistent level ordering. If a column is already an Enum with
    matching levels, it is left unchanged.

    Args:
        data: DataFrame to modify.
        factors: Dict mapping column names to ordered level lists.
            Level order determines reference category (first = reference).

    Returns:
        DataFrame with specified columns converted to Enum type.

    Raises:
        ValueError: If a column contains values not in the specified levels.

    Examples:
        >>> import polars as pl
        >>> df = pl.DataFrame({'group': ['B', 'A', 'C', 'A', 'B']})
        >>> df = ensure_enum(df, {'group': ['A', 'B', 'C']})
        >>> df['group'].dtype
        Enum(categories=['A', 'B', 'C'])
    """
    if not factors:
        return data

    expressions = []
    for col_name, levels in factors.items():
        if col_name not in data.columns:
            raise ValueError(f"Column '{col_name}' not found in DataFrame")

        # Cast to String first (handles existing categoricals), then to Enum
        expr = pl.col(col_name).cast(pl.String).cast(pl.Enum(levels))
        expressions.append(expr)

    return data.with_columns(*expressions)


def get_levels(series: pl.Series) -> list[str]:
    """Get the level ordering from an Enum or Categorical series.

    Args:
        series: Polars series with Enum or Categorical dtype.

    Returns:
        List of category levels in their defined order.

    Raises:
        ValueError: If series is not categorical.

    Examples:
        >>> import polars as pl
        >>> s = pl.Series('x', ['B', 'A']).cast(pl.Enum(['A', 'B', 'C']))
        >>> get_levels(s)
        ['A', 'B', 'C']
    """
    dtype = series.dtype
    if isinstance(dtype, pl.Enum):
        return list(dtype.categories)
    elif isinstance(dtype, pl.Categorical):
        # For Categorical, get unique values sorted
        return series.unique().sort().cast(pl.String).to_list()
    else:
        raise ValueError(f"Series must be Enum or Categorical, got {dtype}")


def infer_levels(series: pl.Series) -> list[str]:
    """Infer level ordering from a non-categorical series.

    For string columns that haven't been converted to Enum yet,
    infers levels by getting unique values and sorting them.

    Args:
        series: Polars series (any string-like type).

    Returns:
        List of unique values, sorted alphabetically.

    Examples:
        >>> import polars as pl
        >>> s = pl.Series('x', ['B', 'A', 'C', 'A'])
        >>> infer_levels(s)
        ['A', 'B', 'C']
    """
    return series.cast(pl.String).unique().sort().to_list()


def detect_categoricals(
    ast: Binary | Call | Variable | object,
    data: pl.DataFrame,
) -> dict[str, list[str]]:
    """Detect categorical variables from a formula AST.

    Walks the AST to find:
    1. Explicit categorical markers: factor(x), T(x), S(x)
    2. String columns referenced in the formula

    For explicit markers, extracts level information if provided.
    For implicit string columns, infers levels from data.

    Args:
        ast: Parsed formula AST (from bossanova._parser).
        data: DataFrame to check column types against.

    Returns:
        Dict mapping column names to ordered level lists.

    Examples:
        >>> from bossanova._parser import Scanner, Parser
        >>> import polars as pl
        >>> tokens = Scanner('y ~ factor(group) + age').scan()
        >>> ast = Parser(tokens).parse()
        >>> df = pl.DataFrame({'y': [1, 2], 'group': ['A', 'B'], 'age': [30, 40]})
        >>> detect_categoricals(ast, df)
        {'group': ['A', 'B']}
    """
    # Import AST types here to avoid circular imports
    from bossanova._parser.expr import (
        Assign,
        Binary,
        Call,
        Grouping,
        Literal,
        QuotedName,
        Unary,
        Variable,
    )

    categoricals: dict[str, list[str]] = {}

    def _walk(node: object) -> None:
        """Recursively walk AST nodes."""
        if isinstance(node, Binary):
            _walk(node.left)
            _walk(node.right)

        elif isinstance(node, Unary):
            _walk(node.right)

        elif isinstance(node, Call):
            callee = node.callee
            if isinstance(callee, Variable):
                func_name = callee.name.lexeme
                # factor(), T(), S() are categorical markers
                if func_name in ("factor", "T", "S"):
                    if node.args:
                        first_arg = node.args[0]
                        col_name: str | None = None

                        if isinstance(first_arg, Variable):
                            col_name = first_arg.name.lexeme
                        elif isinstance(first_arg, QuotedName):
                            col_name = first_arg.expression.lexeme

                        if col_name and col_name in data.columns:
                            # Check for explicit levels in later args
                            levels = _extract_levels(node.args[1:])
                            if levels is None:
                                # Infer from data
                                levels = infer_levels(data[col_name])
                            categoricals[col_name] = levels

            # Walk all arguments
            for arg in node.args:
                _walk(arg)

        elif isinstance(node, Variable):
            col_name = node.name.lexeme
            if col_name in data.columns:
                dtype = data[col_name].dtype
                # Auto-detect string/categorical columns
                if dtype == pl.String or isinstance(dtype, (pl.Enum, pl.Categorical)):
                    if col_name not in categoricals:
                        if isinstance(dtype, pl.Enum):
                            categoricals[col_name] = get_levels(data[col_name])
                        else:
                            categoricals[col_name] = infer_levels(data[col_name])

        elif isinstance(node, Grouping):
            _walk(node.expression)

        elif isinstance(node, Assign):
            _walk(node.value)

        elif isinstance(node, (Literal, QuotedName)):
            pass  # Leaf nodes

    def _extract_levels(args: list[object]) -> list[str] | None:
        """Extract explicit level list from function arguments."""
        for arg in args:
            if isinstance(arg, Assign):
                if isinstance(arg.name, Variable) and arg.name.name.lexeme == "levels":
                    # levels=[...] argument
                    return _literal_to_list(arg.value)
        return None

    def _literal_to_list(node: object) -> list[str] | None:
        """Convert a Literal containing a list to Python list."""
        if isinstance(node, Literal) and isinstance(node.value, (list, tuple)):
            return [str(v) for v in node.value]
        return None

    _walk(ast)
    return categoricals
