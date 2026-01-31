"""Formula transformation utilities.

This module provides tools for programmatically modifying formulas
to add transforms (center, scale, log) and contrasts (Sum, Treatment).
Uses the vendored parser AST for reliable transformation of any valid formula syntax.

Stateful Transforms:
    center(x): x - mean(x) — subtract mean only
    scale(x): x / std(x) — divide by std only (no mean subtraction)
    standardize(x): (x - mean(x)) / std(x) — full z-score
    zscore(x): alias for standardize(x)

These transforms capture parameters from training data and reuse them
for predictions on new data.

Examples:
    >>> from bossanova.formula import transform_formula
    >>> transform_formula("y ~ x1 * x2", transforms={"x1": "center", "x2": "scale"})
    'y ~ center(x1) * scale(x2)'
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from bossanova._parser import (
    Scanner,
    Parser,
    Variable,
    Call,
    Binary,
    Grouping,
    Literal,
    QuotedName,
    Token,
)

__all__ = [
    "TransformState",
    "StatefulTransform",
    "Center",
    "Scale",
    "Standardize",
    "Zscore",
    "STATEFUL_TRANSFORMS",
    "create_transform",
    "TRANSFORM_MAP",
    "CONTRAST_MAP",
    "VALID_TRANSFORMS",
    "VALID_CONTRASTS",
    "ContrastSpec",
    "FormulaTransformer",
    "transform_formula",
]


# =============================================================================
# Stateful Transform Classes
# =============================================================================


@dataclass
class TransformState:
    """Container for captured transform parameters.

    Attributes:
        name: Transform name (center, scale, standardize).
        params: Dictionary of learned parameters (mean, std).
    """

    name: str
    params: dict[str, float]


class StatefulTransform:
    """Base class for stateful transforms.

    Stateful transforms capture parameters from training data and
    reuse them when transforming new data for predictions.
    """

    name: str = "base"

    def __init__(self) -> None:
        self._fitted = False
        self._params: dict[str, float] = {}

    @property
    def fitted(self) -> bool:
        """Whether transform has been fitted to data."""
        return self._fitted

    @property
    def state(self) -> TransformState:
        """Get current transform state."""
        return TransformState(name=self.name, params=self._params.copy())

    def fit(self, x: NDArray[np.floating[Any]]) -> None:
        """Compute and store parameters from training data.

        Args:
            x: Training data array.
        """
        raise NotImplementedError

    def transform(self, x: NDArray[np.floating[Any]]) -> NDArray[np.floating[Any]]:
        """Transform data using stored parameters.

        Args:
            x: Data to transform.

        Returns:
            Transformed data.

        Raises:
            RuntimeError: If transform has not been fitted.
        """
        raise NotImplementedError

    def fit_transform(self, x: NDArray[np.floating[Any]]) -> NDArray[np.floating[Any]]:
        """Fit to data and transform in one step.

        Args:
            x: Training data to fit and transform.

        Returns:
            Transformed training data.
        """
        self.fit(x)
        return self.transform(x)

    def __call__(self, x: NDArray[np.floating[Any]]) -> NDArray[np.floating[Any]]:
        """Apply transform, fitting if not already fitted.

        This allows the transform to be used as a callable in formulas.
        First call fits the transform; subsequent calls reuse parameters.

        Args:
            x: Data to transform.

        Returns:
            Transformed data.
        """
        if not self._fitted:
            return self.fit_transform(x)
        return self.transform(x)


class Center(StatefulTransform):
    """Mean-centering transform: x - mean(x).

    Subtracts the mean computed from training data.

    Examples:
        >>> transform = Center()
        >>> train = np.array([10.0, 20.0, 30.0])
        >>> transform.fit_transform(train)  # mean=20
        array([-10.,   0.,  10.])
        >>> new = np.array([25.0, 35.0])
        >>> transform.transform(new)  # uses mean=20 from training
        array([ 5., 15.])
    """

    name = "center"

    def fit(self, x: NDArray[np.floating[Any]]) -> None:
        """Compute mean from training data."""
        self._params["mean"] = float(np.nanmean(x))
        self._fitted = True

    def transform(self, x: NDArray[np.floating[Any]]) -> NDArray[np.floating[Any]]:
        """Subtract training mean from data."""
        if not self._fitted:
            raise RuntimeError("Transform not fitted. Call fit() first.")
        return x - self._params["mean"]


class Scale(StatefulTransform):
    """Scaling transform: x / std(x).

    Divides by the standard deviation computed from training data.
    Does NOT subtract the mean (use Standardize for z-scores).

    Examples:
        >>> transform = Scale()
        >>> train = np.array([0.0, 10.0, 20.0])
        >>> transform.fit_transform(train)  # std=10
        array([0., 1., 2.])
        >>> new = np.array([5.0, 15.0])
        >>> transform.transform(new)  # uses std=10 from training
        array([0.5, 1.5])
    """

    name = "scale"

    def fit(self, x: NDArray[np.floating[Any]]) -> None:
        """Compute std from training data."""
        std = float(np.nanstd(x, ddof=1))  # Sample std
        if std == 0:
            std = 1.0  # Avoid division by zero
        self._params["std"] = std
        self._fitted = True

    def transform(self, x: NDArray[np.floating[Any]]) -> NDArray[np.floating[Any]]:
        """Divide data by training std."""
        if not self._fitted:
            raise RuntimeError("Transform not fitted. Call fit() first.")
        return x / self._params["std"]


class Standardize(StatefulTransform):
    """Standardization transform: (x - mean(x)) / std(x).

    Computes z-scores using mean and std from training data.
    Alias: zscore()

    Examples:
        >>> transform = Standardize()
        >>> train = np.array([10.0, 20.0, 30.0])
        >>> transform.fit_transform(train)  # mean=20, std=10
        array([-1.,  0.,  1.])
        >>> new = np.array([25.0, 35.0])
        >>> transform.transform(new)  # uses training mean/std
        array([0.5, 1.5])
    """

    name = "standardize"

    def fit(self, x: NDArray[np.floating[Any]]) -> None:
        """Compute mean and std from training data."""
        self._params["mean"] = float(np.nanmean(x))
        std = float(np.nanstd(x, ddof=1))  # Sample std
        if std == 0:
            std = 1.0  # Avoid division by zero
        self._params["std"] = std
        self._fitted = True

    def transform(self, x: NDArray[np.floating[Any]]) -> NDArray[np.floating[Any]]:
        """Apply z-score using training mean and std."""
        if not self._fitted:
            raise RuntimeError("Transform not fitted. Call fit() first.")
        return (x - self._params["mean"]) / self._params["std"]


# Alias for Standardize
Zscore = Standardize


# Registry of stateful transform classes
STATEFUL_TRANSFORMS: dict[str, type[StatefulTransform]] = {
    "center": Center,
    "scale": Scale,
    "standardize": Standardize,
    "zscore": Standardize,  # Alias
}


def create_transform(name: str) -> StatefulTransform:
    """Create a stateful transform instance by name.

    Args:
        name: Transform name (center, scale, standardize, zscore).

    Returns:
        New transform instance.

    Raises:
        ValueError: If transform name is unknown.

    Examples:
        >>> transform = create_transform("center")
        >>> transform.fit_transform(np.array([1.0, 2.0, 3.0]))
        array([-1.,  0.,  1.])
    """
    if name not in STATEFUL_TRANSFORMS:
        raise ValueError(
            f"Unknown transform '{name}'. "
            f"Valid transforms: {sorted(STATEFUL_TRANSFORMS.keys())}"
        )
    return STATEFUL_TRANSFORMS[name]()


# =============================================================================
# Formula Transform Mapping
# =============================================================================

# Mapping from our names to formulae syntax
TRANSFORM_MAP: dict[str, str] = {
    "center": "center",
    "scale": "scale",
    "standardize": "standardize",
    "zscore": "zscore",
    "log": "log",
    "log10": "log10",
    "sqrt": "sqrt",
}

CONTRAST_MAP: dict[str, str] = {
    "treatment": "Treatment",
    "sum": "Sum",
    "poly": "Poly",
}

# Valid transform and contrast types for validation
VALID_TRANSFORMS = frozenset(TRANSFORM_MAP.keys())
VALID_CONTRASTS = frozenset(CONTRAST_MAP.keys())

# Type alias for contrast specification
# Can be: "sum", "treatment", or ("treatment", "reference_level")
ContrastSpec = str | tuple[str, str]


def _ast_to_string(node) -> str:
    """Convert AST node back to formula string.

    The formulae library's AST __str__ produces debug output, not valid
    formula strings. This function walks the AST and reconstructs a
    parseable formula string.

    Args:
        node: AST node from formulae parser.

    Returns:
        Valid formula string representation of the AST.
    """
    if isinstance(node, Variable):
        return node.name.lexeme
    elif isinstance(node, Literal):
        # String literals need quotes
        if isinstance(node.value, str):
            return f"'{node.value}'"
        return str(node.value)
    elif isinstance(node, QuotedName):
        # Preserve backticks for quoted names
        return f"`{node.name.lexeme}`"
    elif isinstance(node, Binary):
        left_str = _ast_to_string(node.left)
        right_str = _ast_to_string(node.right)
        op = node.operator.lexeme
        # Handle keyword arguments (no spaces around =)
        if op == "=":
            return f"{left_str}={right_str}"
        return f"{left_str} {op} {right_str}"
    elif isinstance(node, Grouping):
        inner = _ast_to_string(node.expression)
        return f"({inner})"
    elif isinstance(node, Call):
        callee = _ast_to_string(node.callee)
        args = ", ".join(_ast_to_string(arg) for arg in node.args)
        return f"{callee}({args})"
    else:
        # Fallback - try str representation
        return str(node)


class FormulaTransformer:
    """Transform formula AST by wrapping variables in functions.

    This class parses a formula string into an AST, transforms specified
    variables by wrapping them in function calls, and reconstructs the
    formula string.

    Args:
        transforms: Mapping of variable names to transform types.
            Valid types: "center", "scale", "log", "log10", "sqrt".
        contrasts: Mapping of variable names to contrast specifications.
            Each value can be:
            - String: "treatment" or "sum" (uses default reference)
            - Tuple: ("treatment", "reference_level") for explicit reference

    Examples:
        >>> transformer = FormulaTransformer(
        ...     transforms={"x1": "center", "x2": "scale"},
        ...     contrasts={"group": "sum"}
        ... )
        >>> transformer.transform("y ~ x1 * x2 + group")
        'y ~ center(x1) * scale(x2) + factor(group, Sum)'

        >>> # With explicit reference level
        >>> transformer = FormulaTransformer(
        ...     contrasts={"group": ("treatment", "control")}
        ... )
        >>> transformer.transform("y ~ group")
        "y ~ factor(group, Treatment(reference='control'))"
    """

    def __init__(
        self,
        transforms: dict[str, str] | None = None,
        contrasts: dict[str, ContrastSpec] | None = None,
    ):
        """Initialize transformer with transform and contrast specifications.

        Args:
            transforms: Variable name to transform type mapping.
            contrasts: Variable name to contrast spec mapping. Each value
                can be a string ("sum", "treatment") or tuple
                ("treatment", "reference_level").
        """
        self.transforms = transforms or {}
        self.contrasts = contrasts or {}

        # Validate transform types
        for var, transform in self.transforms.items():
            if transform not in VALID_TRANSFORMS:
                raise ValueError(
                    f"Unknown transform '{transform}' for variable '{var}'. "
                    f"Valid transforms: {sorted(VALID_TRANSFORMS)}"
                )

        # Validate and normalize contrast types
        for var, contrast in self.contrasts.items():
            contrast_type = contrast[0] if isinstance(contrast, tuple) else contrast
            if contrast_type not in VALID_CONTRASTS:
                raise ValueError(
                    f"Unknown contrast '{contrast_type}' for variable '{var}'. "
                    f"Valid contrasts: {sorted(VALID_CONTRASTS)}"
                )

    def transform(self, formula: str) -> str:
        """Transform formula string, returning new formula string.

        Args:
            formula: Original formula string (e.g., "y ~ x1 + x2").

        Returns:
            Transformed formula string with functions applied.
        """
        tokens = Scanner(formula).scan()
        ast = Parser(tokens, formula).parse()
        new_ast = self._visit(ast)
        return _ast_to_string(new_ast)

    def _visit(self, node):
        """Recursively visit and transform AST nodes.

        Args:
            node: AST node to visit.

        Returns:
            Transformed AST node (or original if no transformation needed).
        """
        if isinstance(node, Variable):
            return self._transform_variable(node)
        elif isinstance(node, Binary):
            return Binary(
                left=self._visit(node.left),
                operator=node.operator,
                right=self._visit(node.right),
            )
        elif isinstance(node, Call):
            # Don't transform inside existing function calls
            # (e.g., if user already wrote center(x), leave it alone)
            return node
        elif isinstance(node, Grouping):
            return Grouping(self._visit(node.expression))
        elif isinstance(node, (Literal, QuotedName)):
            # Leave literals and quoted names unchanged
            return node
        else:
            # Unknown node type - return as-is
            return node

    def _transform_variable(self, node: Variable) -> Variable | Call:
        """Apply transform or contrast to a variable.

        Args:
            node: Variable AST node.

        Returns:
            Original variable or Call node wrapping the variable.
        """
        var_name = node.name.lexeme

        # Check for transform (takes priority over contrast)
        if var_name in self.transforms:
            func_name = TRANSFORM_MAP[self.transforms[var_name]]
            return self._wrap_in_call(node, func_name)

        # Check for contrast
        if var_name in self.contrasts:
            contrast_spec = self.contrasts[var_name]
            if isinstance(contrast_spec, tuple):
                contrast_type = CONTRAST_MAP[contrast_spec[0]]
                reference = contrast_spec[1]
            else:
                contrast_type = CONTRAST_MAP[contrast_spec]
                reference = None
            return self._wrap_in_contrast(node, contrast_type, reference)

        return node

    def _wrap_in_call(self, var_node: Variable, func_name: str) -> Call:
        """Wrap variable in function call: x -> func(x).

        Args:
            var_node: Variable AST node.
            func_name: Function name to wrap with.

        Returns:
            Call AST node representing func(var).
        """
        func_token = Token("IDENTIFIER", func_name)
        return Call(
            callee=Variable(func_token),
            args=[var_node],
        )

    def _wrap_in_contrast(
        self, var_node: Variable, contrast_type: str, reference: str | None = None
    ) -> Call:
        """Wrap variable in contrast: x -> factor(x, ContrastType).

        Args:
            var_node: Variable AST node.
            contrast_type: Contrast type name (e.g., "Sum", "Treatment").
            reference: Optional reference level for Treatment contrasts.

        Returns:
            Call AST node representing factor(var, ContrastType) or
            factor(var, Treatment(reference='level')).
        """
        factor_token = Token("IDENTIFIER", "factor")

        if reference is not None:
            # Build: Treatment(reference='level')
            contrast_token = Token("IDENTIFIER", contrast_type)
            ref_token = Token("IDENTIFIER", "reference")
            # Build Treatment(reference='level') as a Call node
            treatment_call = Call(
                callee=Variable(contrast_token),
                args=[
                    Binary(
                        left=Variable(ref_token),
                        operator=Token("EQUAL", "="),
                        right=Literal(reference),
                    )
                ],
            )
            return Call(
                callee=Variable(factor_token),
                args=[var_node, treatment_call],
            )
        else:
            contrast_token = Token("IDENTIFIER", contrast_type)
            return Call(
                callee=Variable(factor_token),
                args=[var_node, Variable(contrast_token)],
            )


def transform_formula(
    formula: str,
    transforms: dict[str, str] | None = None,
    contrasts: dict[str, ContrastSpec] | None = None,
) -> str:
    """Transform formula by applying transforms and contrasts.

    Convenience function wrapping FormulaTransformer.

    Args:
        formula: Original formula string.
        transforms: Variable name to transform type mapping.
            Valid types: "center", "scale", "log", "log10", "sqrt".
        contrasts: Variable name to contrast spec mapping. Each value
            can be a string ("sum", "treatment") or tuple
            ("treatment", "reference_level") for explicit reference.

    Returns:
        Transformed formula string.

    Examples:
        >>> transform_formula("y ~ x1 + x2", transforms={"x1": "center"})
        'y ~ center(x1) + x2'

        >>> transform_formula(
        ...     "y ~ x * group",
        ...     transforms={"x": "scale"},
        ...     contrasts={"group": "sum"}
        ... )
        'y ~ scale(x) * factor(group, Sum)'

        >>> # With explicit reference level
        >>> transform_formula(
        ...     "y ~ group",
        ...     contrasts={"group": ("treatment", "control")}
        ... )
        "y ~ factor(group, Treatment(reference='control'))"
    """
    transformer = FormulaTransformer(transforms, contrasts)
    return transformer.transform(formula)
