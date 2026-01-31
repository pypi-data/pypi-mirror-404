"""Parser for mee() formula specifications.

Parses specs like:
- "treatment" → single variable
- "treatment + age" → multiple variables (joint effects)
- "treatment | gender" → treatment BY gender (stratification)
- "treatment | age[30, 50]" → treatment at specific age values
- "age[mean]", "age[minmax]" → shortcuts for common values
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "ParsedSpec",
    "parse_mee_spec",
    "resolve_shortcuts",
]


@dataclass
class ParsedSpec:
    """Result of parsing a mee() specification string.

    Attributes:
        focal_vars: Variables to compute effects for (before |).
        by_vars: Stratification variables (after |), without value specs.
        at_values: Dict mapping variable names to their specified values.
            Values can be literals or shortcuts like 'mean', 'minmax'.
    """

    focal_vars: list[str] = field(default_factory=list)
    by_vars: list[str] = field(default_factory=list)
    at_values: dict[str, list[Any] | str] = field(default_factory=dict)


def parse_mee_spec(spec: str) -> ParsedSpec:
    """Parse a mee() specification string.

    Args:
        spec: Formula specification. Supports:
            - Variable names: "treatment", "age"
            - Multiple specs: "treatment + age"
            - Stratification: "treatment | gender"
            - Inline values: "age[30, 50]", "treatment[A, B]"
            - Shortcuts: "age[mean]", "age[minmax]", "age[q25, q75]"

    Returns:
        ParsedSpec with focal_vars, by_vars, and at_values.

    Raises:
        ValueError: If spec is malformed.

    Examples:
        >>> parse_mee_spec("treatment")
        ParsedSpec(focal_vars=['treatment'], by_vars=[], at_values={})

        >>> parse_mee_spec("treatment | gender")
        ParsedSpec(focal_vars=['treatment'], by_vars=['gender'], at_values={})

        >>> parse_mee_spec("treatment | age[30, 50]")
        ParsedSpec(focal_vars=['treatment'], by_vars=[], at_values={'age': [30.0, 50.0]})

        >>> parse_mee_spec("age[mean]")
        ParsedSpec(focal_vars=['age'], by_vars=[], at_values={'age': 'mean'})
    """
    spec = spec.strip()
    if not spec:
        raise ValueError("Empty specification")

    result = ParsedSpec()

    # Split on | for stratification (BY operator)
    if "|" in spec:
        parts = spec.split("|", 1)
        focal_part = parts[0].strip()
        by_part = parts[1].strip()
    else:
        focal_part = spec
        by_part = None

    # Parse focal variables (before |)
    result.focal_vars = _parse_var_list(focal_part, result.at_values)

    # Parse by variables (after |)
    if by_part:
        by_vars = _parse_var_list(by_part, result.at_values)
        # All by_vars go into result.by_vars (even those with bracket specs)
        # Variables with bracket specs will also have entries in at_values
        result.by_vars = by_vars

    return result


def _parse_var_list(part: str, at_values: dict[str, list[Any] | str]) -> list[str]:
    """Parse a '+' separated list of variables with optional [values].

    Args:
        part: String like "treatment + age[30, 50]"
        at_values: Dict to populate with value specifications.

    Returns:
        List of variable names (without brackets).
    """
    variables = []

    # Split on + for multiple variables
    terms = [t.strip() for t in part.split("+")]

    for term in terms:
        var_name, values = _parse_term(term)
        variables.append(var_name)
        if values is not None:
            at_values[var_name] = values

    return variables


def _parse_term(term: str) -> tuple[str, list[Any] | str | None]:
    """Parse a single term like 'age[30, 50]' or 'treatment'.

    Args:
        term: Single variable specification.

    Returns:
        Tuple of (variable_name, values_or_shortcut_or_None).
    """
    term = term.strip()

    # Check for bracket notation: var[values]
    match = re.match(r"^(\w+)\s*\[(.+)\]$", term)
    if not match:
        # No brackets - just a variable name
        if not re.match(r"^\w+$", term):
            raise ValueError(f"Invalid variable name: {term!r}")
        return term, None

    var_name = match.group(1)
    bracket_content = match.group(2).strip()

    # Parse bracket content
    values = _parse_bracket_content(bracket_content)
    return var_name, values


def _parse_bracket_content(content: str) -> list[Any] | str:
    """Parse the content inside brackets.

    Args:
        content: String inside brackets, e.g., "30, 50" or "mean" or "A, B"

    Returns:
        - str for shortcuts: "mean", "median", "minmax", "q25", "q75"
        - list for explicit values: [30.0, 50.0] or ["A", "B"]
    """
    content = content.strip()

    # Check for single shortcuts
    shortcuts = {"mean", "median", "minmax", "min", "max", "data"}
    if content.lower() in shortcuts:
        return content.lower()

    # Check for quantile shortcuts like "q25", "q75", "q10"
    if re.match(r"^q\d+$", content.lower()):
        return content.lower()

    # Parse as comma-separated values
    values = []
    for item in content.split(","):
        item = item.strip()
        if not item:
            continue

        # Check for quantile in list: "q25, q75"
        if re.match(r"^q\d+$", item.lower()):
            values.append(item.lower())
            continue

        # Try to parse as number
        try:
            # Try int first, then float
            if "." in item:
                values.append(float(item))
            else:
                try:
                    values.append(int(item))
                except ValueError:
                    values.append(float(item))
        except ValueError:
            # It's a string value (factor level)
            # Remove quotes if present
            if (item.startswith('"') and item.endswith('"')) or (
                item.startswith("'") and item.endswith("'")
            ):
                item = item[1:-1]
            values.append(item)

    if len(values) == 1 and isinstance(values[0], str) and values[0] in shortcuts:
        return values[0]

    return values


def resolve_shortcuts(
    at_values: dict[str, list[Any] | str],
    data: Any,  # polars DataFrame
) -> dict[str, list[Any]]:
    """Resolve shortcuts like 'mean', 'minmax' to actual values.

    Args:
        at_values: Dict with shortcuts or explicit values.
        data: DataFrame to compute statistics from.

    Returns:
        Dict with all shortcuts resolved to lists of values.
    """
    resolved = {}

    for var, values in at_values.items():
        if var not in data.columns:
            raise ValueError(f"Variable {var!r} not found in data")

        col = data[var]

        if isinstance(values, str):
            # Single shortcut
            resolved[var] = _resolve_single_shortcut(values, col)
        elif isinstance(values, list):
            # List that may contain shortcuts
            result = []
            for v in values:
                if isinstance(v, str) and (
                    v in {"mean", "median", "min", "max"} or v.startswith("q")
                ):
                    result.extend(_resolve_single_shortcut(v, col))
                else:
                    result.append(v)
            resolved[var] = result
        else:
            resolved[var] = [values]

    return resolved


def _resolve_single_shortcut(shortcut: str, col: Any) -> list[Any]:
    """Resolve a single shortcut to values.

    Args:
        shortcut: One of 'mean', 'median', 'minmax', 'min', 'max', 'qNN'.
        col: Polars Series to compute from.

    Returns:
        List of resolved values.
    """
    shortcut = shortcut.lower()

    if shortcut == "mean":
        return [float(col.mean())]
    elif shortcut == "median":
        return [float(col.median())]
    elif shortcut == "min":
        return [float(col.min())]
    elif shortcut == "max":
        return [float(col.max())]
    elif shortcut == "minmax":
        return [float(col.min()), float(col.max())]
    elif shortcut == "data":
        # Return all unique values from the column, sorted
        unique_vals = col.unique().sort().to_list()
        # Convert to appropriate Python types
        return [float(v) if isinstance(v, (int, float)) else v for v in unique_vals]
    elif shortcut.startswith("q"):
        # Quantile: q25 → 0.25, q75 → 0.75
        q = int(shortcut[1:]) / 100.0
        return [float(col.quantile(q))]
    else:
        raise ValueError(f"Unknown shortcut: {shortcut!r}")
