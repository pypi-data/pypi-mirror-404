"""Random effects formula parsing for linear mixed models.

This module provides functionality to parse R-style random effects formulas
and extract components needed for lmer/glmer fitting using the formulae library.

Key features:
    - Expand || syntax to uncorrelated random effects

Examples:
    >>> from bossanova.formula.random_effects import expand_double_verts
    >>> formula = "y ~ x + (Days||Subject)"
    >>> expanded, meta = expand_double_verts(formula)
    >>> expanded
    'y ~ x + (1|Subject) + (0+Days|Subject)'
"""

from __future__ import annotations

import re

__all__ = [
    "expand_double_verts",
]


def _parse_random_effects_spec(spec: str) -> list[str]:
    """Parse random effects specification like '1 + x + y' into ['1', 'x', 'y'].

    Args:
        spec: Random effects specification from left side of | or ||.

    Returns:
        List of term strings.

    Examples:
        >>> _parse_random_effects_spec("1 + x + y")
        ['1', 'x', 'y']
        >>> _parse_random_effects_spec("Days")
        ['Days']
        >>> _parse_random_effects_spec("0 + x")
        ['0', 'x']
    """
    if not spec or spec.strip() == "":
        return ["1"]

    spec = spec.strip()

    # Handle special case of just "1"
    if spec == "1":
        return ["1"]

    # Split by + but preserve the terms
    # Use regex to split on + but not within parentheses
    terms = [t.strip() for t in re.split(r"\s*\+\s*", spec)]

    # Filter out empty strings
    return [t for t in terms if t]


def expand_double_verts(formula: str) -> tuple[str, dict]:
    """Expand || syntax into separate uncorrelated random effects terms.

    This matches lme4's expandDoubleVerts() function. The || syntax creates
    independent (uncorrelated) random effects by expanding to separate terms.

    Args:
        formula: R-style formula string potentially containing || syntax.

    Returns:
        A tuple of:
            - Expanded formula string with || replaced by separate | terms
            - Metadata dict tracking which terms came from || expansion

    Examples:
        >>> expand_double_verts("y ~ x + (Days || Subject)")
        ('y ~ x + (1 | Subject) + (0 + Days | Subject)', {...})

        >>> expand_double_verts("y ~ x + (1 + x + y || group)")
        ('y ~ x + (1 | group) + (0 + x | group) + (0 + y | group)', {...})

    Note:
        The transformation rules are:
        - (x || g) → (1 | g) + (0 + x | g)
        - (1 + x || g) → (1 | g) + (0 + x | g)
        - (1 + x + y || g) → (1 | g) + (0 + x | g) + (0 + y | g)
        - (0 + x || g) → (0 + x | g)  [no intercept term added]
    """
    metadata = {}

    # Find all || terms using regex
    double_bar_pattern = r"\(([^)]*)\|\|([^)]*)\)"
    matches = list(re.finditer(double_bar_pattern, formula))

    if not matches:
        return formula, metadata

    # Process each || term from right to left to preserve string positions
    for match in reversed(matches):
        full_match = match.group(0)
        lhs = match.group(1).strip()  # Left side: random effects spec
        rhs = match.group(2).strip()  # Right side: grouping factor

        # Parse LHS to extract individual terms
        terms = _parse_random_effects_spec(lhs)

        # Build separate terms for each random effect
        expanded_terms = []
        has_zero = False

        # Check if intercept is explicitly excluded
        for term in terms:
            if term in ["0", "-1"]:
                has_zero = True

        # Add intercept term unless explicitly excluded
        if not has_zero:
            expanded_terms.append(f"(1 | {rhs})")

        # Add slope terms with 0 + to exclude their own intercepts
        for term in terms:
            if term not in ["1", "0", "-1"]:
                expanded_terms.append(f"(0 + {term} | {rhs})")

        # Replace the || term with expanded terms joined by +
        replacement = " + ".join(expanded_terms)
        formula = formula[: match.start()] + replacement + formula[match.end() :]

        # Track metadata for this expansion
        metadata[rhs] = {
            "original": full_match,
            "terms": expanded_terms,
            "is_uncorrelated": True,
        }

    return formula, metadata
