"""Design matrix construction from formula strings.

This module provides the core infrastructure for building design matrices
from R-style formula strings and Polars DataFrames.

Examples:
    >>> import polars as pl
    >>> from bossanova.formula.design import DesignMatrixBuilder
    >>>
    >>> df = pl.DataFrame({
    ...     'y': [1.0, 2.0, 3.0, 4.0],
    ...     'x': [1.0, 2.0, 3.0, 4.0],
    ...     'group': ['A', 'B', 'A', 'B'],
    ... })
    >>> builder = DesignMatrixBuilder('y ~ x + group', df)
    >>> result = builder.build()
    >>> result.X.shape
    (4, 3)  # Intercept, x, group[B]
    >>> result.X_labels
    ['Intercept', 'x', 'group[B]']
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
import polars as pl
from numpy.typing import NDArray

from bossanova._parser import Parser, Scanner
from bossanova._parser.expr import (
    Binary,
    Call,
    Grouping,
    Literal,
    QuotedName,
    Unary,
    Variable,
)
from bossanova.formula.contrasts import (
    poly_contrast,
    poly_labels,
    poly_numeric,
    poly_numeric_labels,
    sum_contrast,
    treatment_contrast,
)
from bossanova.formula.encoding import (
    detect_categoricals,
    encode_categorical,
    ensure_enum,
    get_levels,
)
from bossanova.formula.transforms import (
    STATEFUL_TRANSFORMS,
    StatefulTransform,
    create_transform,
)
from bossanova.formula.random_effects import expand_double_verts
from bossanova.formula.z_matrix import RandomEffectsInfo, build_random_effects

__all__ = [
    "DesignMatrices",
    "DesignMatrixBuilder",
]


def _full_rank_contrast(levels: list[str]) -> NDArray[np.float64]:
    """Build full-rank identity contrast matrix (all levels encoded).

    Used when a categorical variable spans the intercept (no intercept in model).

    Args:
        levels: Ordered list of categorical level names.

    Returns:
        Identity matrix of shape (n_levels, n_levels).
    """
    return np.eye(len(levels), dtype=np.float64)


def _variable_not_found_error(name: str, data_columns: list[str]) -> ValueError:
    """Create informative error for missing variable.

    Args:
        name: Variable name that was not found.
        data_columns: List of available column names in the data.

    Returns:
        ValueError with helpful message including available columns
        and "did you mean?" suggestions.
    """
    # Find similar column names (simple substring matching)
    name_lower = name.lower()
    similar = [
        col
        for col in data_columns
        if name_lower in col.lower() or col.lower() in name_lower
    ]

    msg = f'Variable "{name}" not found in data.\n\n'
    if len(data_columns) <= 10:
        msg += f"Available columns: {', '.join(data_columns)}"
    else:
        msg += f"Available columns: {', '.join(data_columns[:10])} ... and {len(data_columns) - 10} more"

    if similar:
        suggestions = ", ".join(f'"{s}"' for s in similar[:3])
        msg += f"\n\nDid you mean: {suggestions}?"

    return ValueError(msg)


def _extract_group_info(group_series: pl.Series) -> tuple[list, NDArray[np.intp]]:
    """Extract group levels and integer IDs from a grouping factor series.

    Handles Enum, Categorical, and plain string columns consistently.
    For Enum types, uses the fixed categories from the dtype.
    For other types, sorts unique values to ensure reproducible ordering.

    Args:
        group_series: Polars Series containing group labels.

    Returns:
        Tuple of (levels, group_ids) where:
            - levels: List of unique group level names in sorted order
            - group_ids: Integer array mapping each observation to its group index
    """
    if isinstance(group_series.dtype, pl.Enum):
        # Enum has fixed categories in dtype
        levels = list(group_series.dtype.categories)  # type: ignore
    elif isinstance(group_series.dtype, pl.Categorical):
        # Categorical has dynamic categories - get from data
        levels = sorted(group_series.unique().to_list())
    else:
        levels = sorted(group_series.unique().to_list())

    group_values = group_series.to_list()
    level_to_idx = {lvl: i for i, lvl in enumerate(levels)}
    group_ids = np.array([level_to_idx[v] for v in group_values], dtype=np.intp)

    return levels, group_ids


if TYPE_CHECKING:
    pass


@dataclass
class DesignMatrices:
    """Container for design matrices built from a formula.

    Attributes:
        X: Fixed effects design matrix of shape (n_obs, n_features).
        X_labels: Column names for X matrix.
        y: Response vector of shape (n_obs,), or None if no response in formula.
        y_label: Name of response variable.
        factors: Dict mapping factor names to their level orderings.
        contrast_matrices: Dict mapping factor names to contrast matrices used.
        contrast_types: Dict mapping factor names to contrast type strings
            ("treatment", "sum", "poly"). Used for introspection.
        transform_state: Dict storing state for stateful transforms (center, scale).
            Used for evaluate_new_data to apply same transformations.
        n_obs: Number of observations.
    """

    X: NDArray[np.float64]
    X_labels: list[str]
    y: NDArray[np.float64] | None = None
    y_label: str | None = None
    factors: dict[str, list[str]] = field(default_factory=dict)
    contrast_matrices: dict[str, NDArray[np.float64]] = field(default_factory=dict)
    contrast_types: dict[str, str] = field(default_factory=dict)
    transform_state: dict[str, dict] = field(default_factory=dict)

    @property
    def n_obs(self) -> int:
        """Number of observations."""
        return self.X.shape[0]

    @property
    def n_features(self) -> int:
        """Number of features (columns in X)."""
        return self.X.shape[1]

    def __repr__(self) -> str:
        parts = [
            f"DesignMatrices(n_obs={self.n_obs}, n_features={self.n_features})",
            f"  X_labels: {self.X_labels}",
        ]
        if self.y is not None:
            parts.append(f"  y_label: {self.y_label}")
        if self.factors:
            parts.append(f"  factors: {list(self.factors.keys())}")
        return "\n".join(parts)


class DesignMatrixBuilder:
    """Build design matrices from formula strings and data.

    This class parses R-style formulas and constructs numpy design matrices
    suitable for regression models. It handles:

    - Intercept (added by default, suppress with '0' or '-1')
    - Numeric predictors (passed through as-is)
    - Categorical predictors (encoded with treatment contrasts by default)
    - Response variable (left side of ~)

    Args:
        formula: R-style formula string (e.g., 'y ~ x + group').
        data: Polars DataFrame containing the variables.
        factors: Optional dict mapping column names to level orderings.
            If provided, these orderings are used for categorical encoding.
            Otherwise, levels are inferred from data (sorted unique values).

    Examples:
        >>> import polars as pl
        >>> df = pl.DataFrame({
        ...     'y': [1.0, 2.0, 3.0],
        ...     'x': [1.0, 2.0, 3.0],
        ...     'group': ['A', 'B', 'A'],
        ... })
        >>> builder = DesignMatrixBuilder('y ~ x + group', df)
        >>> result = builder.build()
        >>> result.X_labels
        ['Intercept', 'x', 'group[B]']
    """

    def __init__(
        self,
        formula: str,
        data: pl.DataFrame,
        factors: dict[str, list[str]] | None = None,
        custom_contrasts: dict[str, NDArray[np.float64]] | None = None,
    ) -> None:
        # Expand || syntax to separate uncorrelated terms before parsing
        # E.g., (1 + x || group) -> (1 | group) + (0 + x | group)
        expanded_formula, self._uncorr_metadata = expand_double_verts(formula)

        self.formula = formula  # Keep original for display
        self._expanded_formula = expanded_formula  # Use for parsing
        self.data = data
        self._user_factors = factors or {}
        self._custom_contrasts = custom_contrasts or {}

        # Parsing state
        self._ast: object = None
        self._response_name: str | None = None
        self._rhs_terms: list[object] = []
        self._re_terms: list[Binary] = []  # Random effect terms (Binary with PIPE)
        self._has_intercept: bool = True

        # Encoding state (populated during build)
        self._factors: dict[str, list[str]] = {}
        self._contrast_matrices: dict[str, NDArray[np.float64]] = {}
        self._contrast_types: dict[str, str] = {}
        self._transform_state: dict[str, dict] = {}
        self._transforms: dict[str, StatefulTransform] = {}

        # Track whether intercept degree of freedom has been absorbed
        # This affects whether categoricals use full or reduced encoding
        self._intercept_absorbed: bool = False

        self._parse()

    def _parse(self) -> None:
        """Parse formula string into AST and extract structure."""
        # Validate formula type
        if not isinstance(self._expanded_formula, str):
            raise TypeError(
                f"Formula must be a string, got {type(self._expanded_formula).__name__}"
            )
        # Validate formula is not empty
        if not self._expanded_formula or not self._expanded_formula.strip():
            raise ValueError("Formula cannot be empty. Example: 'y ~ x1 + x2'")

        # Use expanded formula (|| already converted to separate | terms)
        tokens = Scanner(self._expanded_formula).scan()
        self._ast = Parser(tokens, self._expanded_formula).parse()

        # Check for response ~ predictors structure
        if isinstance(self._ast, Binary) and self._ast.operator.kind == "TILDE":
            self._response_name = self._extract_name(self._ast.left)
            self._extract_rhs_terms(self._ast.right)
        else:
            # No response, entire formula is RHS
            self._extract_rhs_terms(self._ast)

    def _extract_name(self, node: object) -> str | None:
        """Extract variable name or literal value from AST node."""
        if isinstance(node, Variable):
            return node.name.lexeme
        if isinstance(node, QuotedName):
            return node.expression.lexeme
        if isinstance(node, Literal):
            # Return string representation of literal value (for 0, 1 checks)
            return str(node.value)
        return None

    def _extract_contrast_type(self, node: object) -> str | None:
        """Extract contrast type from AST node.

        Handles:
        - Variable nodes: Sum, Treatment, Poly
        - Call nodes: Treatment(reference='B'), Sum(), Poly()

        Returns:
            Lowercase contrast type string ("sum", "treatment", "poly") or None.
        """
        valid_contrasts = ("sum", "treatment", "poly")

        # Handle Variable: factor(x, Sum) -> "sum"
        if isinstance(node, Variable):
            name = node.name.lexeme.lower()
            if name in valid_contrasts:
                return name
            return None

        # Handle Call: factor(x, Treatment(reference='B')) -> "treatment"
        if isinstance(node, Call):
            if isinstance(node.callee, Variable):
                name = node.callee.name.lexeme.lower()
                if name in valid_contrasts:
                    return name
            return None

        return None

    def _extract_rhs_terms(self, node: object) -> None:
        """Extract terms from RHS of formula, handling + and - operators.

        Random effect terms (containing PIPE operator) are collected separately
        in self._re_terms for processing by build_random_effects().
        """
        if isinstance(node, Binary):
            if node.operator.kind == "PLUS":
                self._extract_rhs_terms(node.left)
                self._extract_rhs_terms(node.right)
            elif node.operator.kind == "MINUS":
                self._extract_rhs_terms(node.left)
                # Check if subtracting intercept
                right_name = self._extract_name(node.right)
                if right_name == "1":
                    self._has_intercept = False
                # Otherwise ignore subtracted terms for now
            elif node.operator.kind == "PIPE":
                # Random effect term: collect separately
                self._re_terms.append(node)
            else:
                # Other operators (*, :) - treat whole thing as a term
                self._rhs_terms.append(node)
        elif isinstance(node, Unary):
            if node.operator.kind == "MINUS":
                # -1 or -0 removes intercept
                right_name = self._extract_name(node.right)
                if right_name in ("0", "1"):
                    self._has_intercept = False
            elif node.operator.kind == "PLUS":
                self._extract_rhs_terms(node.right)
        elif isinstance(node, Literal):
            # Literal 0 or 1 controls intercept
            if node.value in (0, 1, "0", "1"):
                if node.value in (0, "0"):
                    self._has_intercept = False
                # value of 1 means keep intercept (default)
            else:
                self._rhs_terms.append(node)
        elif isinstance(node, Grouping):
            # Check if grouping contains a random effect (PIPE)
            if self._contains_pipe(node.expression):
                self._extract_rhs_terms(node.expression)
            else:
                self._extract_rhs_terms(node.expression)
        else:
            # Variable, Call, etc. - it's a term
            self._rhs_terms.append(node)

    def _contains_pipe(self, node: object) -> bool:
        """Check if an AST node contains a PIPE operator (random effect)."""
        if isinstance(node, Binary):
            if node.operator.kind == "PIPE":
                return True
            return self._contains_pipe(node.left) or self._contains_pipe(node.right)
        if isinstance(node, Grouping):
            return self._contains_pipe(node.expression)
        return False

    def build(self) -> DesignMatrices:
        """Build the design matrices.

        Returns:
            DesignMatrices containing X, y, and metadata.

        Raises:
            ValueError: If response variable not found in data.
            ValueError: If predictor variable not found in data.
        """
        n_obs = len(self.data)

        # Detect categoricals from formula and data
        detected_cats = detect_categoricals(self._ast, self.data)
        # Merge with user-provided factors (user takes precedence)
        self._factors = {**detected_cats, **self._user_factors}

        # Ensure categorical columns are Enum type
        if self._factors:
            self.data = ensure_enum(self.data, self._factors)

        # Build response vector
        y: NDArray[np.float64] | None = None
        if self._response_name is not None:
            if self._response_name not in self.data.columns:
                raise ValueError(
                    f"Response variable '{self._response_name}' not in data"
                )
            y = self.data[self._response_name].to_numpy().astype(np.float64)

        # Build design matrix columns
        columns: list[NDArray[np.float64]] = []
        labels: list[str] = []

        # Add intercept and track absorption
        if self._has_intercept:
            columns.append(np.ones(n_obs, dtype=np.float64))
            labels.append("Intercept")
            self._intercept_absorbed = True
        else:
            # No intercept - first categorical will absorb the df
            self._intercept_absorbed = False

        # Evaluate each term
        for term in self._rhs_terms:
            col_data, col_labels = self._evaluate_term(term)
            if col_data.ndim == 1:
                columns.append(col_data)
            else:
                # Multiple columns (e.g., from categorical)
                for i in range(col_data.shape[1]):
                    columns.append(col_data[:, i])
            labels.extend(col_labels)

        # Stack into matrix
        if columns:
            X = np.column_stack(columns)
        else:
            # No predictors, just intercept-only model with no intercept = empty
            X = np.empty((n_obs, 0), dtype=np.float64)

        return DesignMatrices(
            X=X,
            X_labels=labels,
            y=y,
            y_label=self._response_name,
            factors=self._factors,
            contrast_matrices=self._contrast_matrices,
            contrast_types=self._contrast_types,
            transform_state=self._transform_state,
        )

    def build_re(self) -> RandomEffectsInfo | None:
        """Build random effects design matrix (Z) from parsed RE terms.

        Processes random effect terms like (1 + x | group) that were
        collected during parsing. Constructs the sparse Z matrix and
        all metadata needed for lmer/glmer.

        Returns:
            RandomEffectsInfo containing Z matrix and metadata, or None
            if no random effects in formula.

        Raises:
            ValueError: If grouping variable not found in data.
            NotImplementedError: For unsupported RE structures.

        Examples:
            >>> builder = DesignMatrixBuilder('y ~ x + (Days | Subject)', df)
            >>> dm = builder.build()
            >>> re_info = builder.build_re()
            >>> re_info.Z.shape
            (180, 36)  # 18 subjects * 2 RE (intercept + Days)
        """
        if not self._re_terms:
            return None

        # First pass: collect all RE term info
        re_term_infos = []
        for term in self._re_terms:
            info = self._parse_re_term(term)
            re_term_infos.append(info)

        # Check for nested effects (a/b syntax)
        has_nested = any(info.get("is_nested", False) for info in re_term_infos)
        if has_nested:
            # Handle nested effects
            if len(re_term_infos) > 1:
                # Multiple RE terms with at least one nested - complex case
                # For now, handle single nested term case
                raise NotImplementedError(
                    "Multiple RE terms with nested effects not yet supported"
                )
            return self._build_re_nested(re_term_infos[0])

        # Group terms by grouping factor to detect crossed vs simple
        factors_seen: dict[str, list[dict]] = {}
        for info in re_term_infos:
            factor = info["group_name"]
            if factor not in factors_seen:
                factors_seen[factor] = []
            factors_seen[factor].append(info)

        # Determine overall structure
        if len(factors_seen) == 1:
            # Single grouping factor - simple or diagonal
            factor_name = list(factors_seen.keys())[0]
            terms_for_factor = factors_seen[factor_name]
            return self._build_re_simple(factor_name, terms_for_factor)
        else:
            # Multiple grouping factors - crossed effects
            return self._build_re_crossed(factors_seen)

    def _parse_re_term(self, term: Binary) -> dict:
        """Parse a single random effect term into components.

        Args:
            term: Binary AST node with PIPE operator.
                Format: Binary(left=re_expr, operator=PIPE, right=group_factor)

        Returns:
            Dict with keys:
                - group_name: Name of grouping factor (or list for nested)
                - re_vars: List of random effect variable names
                - has_intercept: Whether intercept is included
                - X_re: Random effects design matrix (n, n_re)
                - is_nested: True if nested effects (a/b syntax)
                - nested_levels: List of nested level names if is_nested
        """
        # Check if term.right is nested (contains SLASH operator)
        if isinstance(term.right, Binary) and term.right.operator.kind == "SLASH":
            # Nested effects: (1|a/b) or (1|a/b/c)
            nested_levels = self._extract_nested_levels(term.right)
            # Validate all levels exist
            for level in nested_levels:
                if level not in self.data.columns:
                    raise _variable_not_found_error(level, self.data.columns)
            # Parse left side for RE expression
            re_vars, has_intercept = self._parse_re_expr(term.left)
            # Build X_re
            n_obs = len(self.data)
            X_re_cols = []
            random_names = []
            if has_intercept:
                X_re_cols.append(np.ones(n_obs, dtype=np.float64))
                random_names.append("Intercept")
            for var in re_vars:
                if var not in self.data.columns:
                    raise ValueError(
                        f"Random slope variable '{var}' not found in data."
                    )
                X_re_cols.append(self.data[var].to_numpy().astype(np.float64))
                random_names.append(var)
            X_re = np.column_stack(X_re_cols) if X_re_cols else None
            return {
                "group_name": nested_levels[0],  # Outer level for compatibility
                "nested_levels": nested_levels,
                "is_nested": True,
                "re_vars": re_vars,
                "has_intercept": has_intercept,
                "X_re": X_re,
                "random_names": random_names,
            }

        # Simple grouping factor (not nested)
        group_name = self._extract_name(term.right)
        if group_name is None:
            raise ValueError(f"Could not extract grouping factor from: {term}")

        if group_name not in self.data.columns:
            raise _variable_not_found_error(group_name, self.data.columns)

        # term.left is the random effects expression (1, 1 + x, 0 + x, etc.)
        re_vars, has_intercept = self._parse_re_expr(term.left)

        # Build X_re matrix
        n_obs = len(self.data)
        X_re_cols = []
        random_names = []

        if has_intercept:
            X_re_cols.append(np.ones(n_obs, dtype=np.float64))
            random_names.append("Intercept")

        for var in re_vars:
            if var not in self.data.columns:
                raise ValueError(
                    f"Random slope variable '{var}' not found in data. "
                    f"For formula with ({var}|{group_name}), '{var}' must be in data."
                )
            X_re_cols.append(self.data[var].to_numpy().astype(np.float64))
            random_names.append(var)

        if X_re_cols:
            X_re = np.column_stack(X_re_cols)
        else:
            # Edge case: no intercept, no slopes (shouldn't happen)
            raise ValueError("Random effect term has no intercept and no slopes")

        return {
            "group_name": group_name,
            "re_vars": re_vars,
            "has_intercept": has_intercept,
            "X_re": X_re,
            "random_names": random_names,
            "is_nested": False,
        }

    def _extract_nested_levels(self, node: Binary) -> list[str]:
        """Extract nested grouping levels from a/b/c syntax.

        For (1|a/b/c), returns ["a", "b", "c"] (outer to inner).
        """
        levels = []

        def extract(n):
            if isinstance(n, Binary) and n.operator.kind == "SLASH":
                extract(n.left)
                extract(n.right)
            else:
                name = self._extract_name(n)
                if name:
                    levels.append(name)

        extract(node)
        return levels

    def _parse_re_expr(self, expr: object) -> tuple[list[str], bool]:
        """Parse the left side of a random effect term.

        Handles expressions like:
            - 1           -> ([], True)  - intercept only
            - x           -> (['x'], True)  - intercept + slope (implicit)
            - 1 + x       -> (['x'], True)  - intercept + slope
            - 0 + x       -> (['x'], False) - slope only
            - 1 + x + z   -> (['x', 'z'], True)  - intercept + multiple slopes

        Args:
            expr: AST node for the RE expression.

        Returns:
            Tuple of (list of slope variable names, has_intercept bool).
        """
        vars_found: list[str] = []
        has_intercept = True  # Default: include intercept

        def traverse(node: object) -> None:
            nonlocal has_intercept

            if isinstance(node, Literal):
                if node.value in (0, "0"):
                    has_intercept = False
                # value of 1 means intercept (already default True)

            elif isinstance(node, Variable):
                vars_found.append(node.name.lexeme)

            elif isinstance(node, QuotedName):
                vars_found.append(node.expression.lexeme)

            elif isinstance(node, Binary):
                if node.operator.kind == "PLUS":
                    traverse(node.left)
                    traverse(node.right)
                elif node.operator.kind == "MINUS":
                    traverse(node.left)
                    # Check if subtracting 1 (removes intercept)
                    if isinstance(node.right, Literal) and node.right.value in (1, "1"):
                        has_intercept = False
                else:
                    # Colon or star in RE expression (interactions)
                    raise NotImplementedError(
                        f"Interaction terms in random effects ({node.operator.kind}) "
                        "not yet supported"
                    )

            elif isinstance(node, Grouping):
                traverse(node.expression)

            elif isinstance(node, Unary):
                if node.operator.kind == "MINUS":
                    name = self._extract_name(node.right)
                    if name in ("0", "1"):
                        has_intercept = False
                elif node.operator.kind == "PLUS":
                    traverse(node.right)

        traverse(expr)
        return vars_found, has_intercept

    def _build_re_simple(
        self, factor_name: str, terms: list[dict]
    ) -> RandomEffectsInfo:
        """Build random effects for single grouping factor.

        Args:
            factor_name: Name of the grouping factor.
            terms: List of parsed RE term dicts for this factor.

        Returns:
            RandomEffectsInfo with Z matrix and metadata.
        """
        # Get group IDs
        group_series = self.data[factor_name]
        levels, group_ids = _extract_group_info(group_series)
        n_groups = len(levels)

        if len(terms) == 1:
            # Single term: use directly
            info = terms[0]
            X_re = info["X_re"]
            random_names = info["random_names"]

            # Determine structure based on content, not just count
            if len(random_names) == 1 and random_names[0] == "Intercept":
                re_structure = "intercept"
            elif len(random_names) == 1:
                # Single slope only (e.g., 0+x|group)
                re_structure = "slope"  # Use slope to preserve X_re
            else:
                # Multiple REs (intercept + slopes)
                re_structure = "slope"
        else:
            # Multiple terms for same factor: likely || expansion (uncorrelated)
            # Stack X_re matrices horizontally and use diagonal structure
            X_re_list = [t["X_re"] for t in terms]
            random_names = []
            for t in terms:
                random_names.extend(t["random_names"])
            # For uncorrelated slopes, we use blocked layout
            re_structure = "diagonal"

            # Build Z for each term separately and hstack
            from bossanova.formula.z_matrix import build_z_simple
            import scipy.sparse as sp

            Z_blocks = []
            for t in terms:
                Z_i = build_z_simple(
                    group_ids, n_groups, X_re=t["X_re"], layout="blocked"
                )
                Z_blocks.append(Z_i)

            Z = sp.hstack(Z_blocks, format="csc")

            return RandomEffectsInfo(
                Z=Z,
                group_ids_list=[group_ids],
                n_groups_list=[n_groups],
                group_names=[factor_name],
                random_names=random_names,
                re_structure=re_structure,
                X_re=X_re_list,
                column_labels=self._generate_re_labels(
                    [factor_name], [levels], [random_names], "blocked"
                ),
            )

        # Single term case: use build_random_effects
        return build_random_effects(
            group_ids_list=[group_ids],
            n_groups_list=[n_groups],
            group_names=[factor_name],
            random_names=random_names,
            re_structure=re_structure,
            X_re=X_re,
            group_levels_list=[levels],
        )

    def _build_re_crossed(self, factors: dict[str, list[dict]]) -> RandomEffectsInfo:
        """Build random effects for crossed (multiple) grouping factors.

        Args:
            factors: Dict mapping factor names to their parsed RE term lists.

        Returns:
            RandomEffectsInfo with horizontally stacked Z matrices.
        """
        import scipy.sparse as sp
        from bossanova.formula.z_matrix import build_z_simple

        group_ids_list = []
        n_groups_list = []
        group_names = []
        group_levels_list = []
        all_random_names = []
        Z_blocks = []
        re_structures = []

        for factor_name, terms in factors.items():
            # Get group IDs for this factor
            group_series = self.data[factor_name]
            levels, group_ids = _extract_group_info(group_series)
            n_groups = len(levels)

            group_ids_list.append(group_ids)
            n_groups_list.append(n_groups)
            group_names.append(factor_name)
            group_levels_list.append(levels)

            # Build Z for this factor's terms
            if len(terms) == 1:
                info = terms[0]
                X_re = info["X_re"]
                random_names = info["random_names"]
                layout = "interleaved"
                re_struct = "slope" if len(random_names) > 1 else "intercept"
            else:
                # Multiple terms: diagonal (uncorrelated)
                random_names = []
                for t in terms:
                    random_names.extend(t["random_names"])
                layout = "blocked"
                re_struct = "diagonal"
                # Build each term's Z separately
                for t in terms:
                    Z_i = build_z_simple(
                        group_ids, n_groups, X_re=t["X_re"], layout="blocked"
                    )
                    Z_blocks.append(Z_i)
                all_random_names.extend(random_names)
                re_structures.append(re_struct)
                continue

            Z_i = build_z_simple(group_ids, n_groups, X_re=X_re, layout=layout)
            Z_blocks.append(Z_i)
            all_random_names.extend(random_names)
            re_structures.append(re_struct)

        # Compute term permutation: sort by n_groups descending (largest first)
        # This optimizes Cholesky factorization by putting larger blocks first
        n_factors = len(n_groups_list)
        if n_factors > 1:
            # argsort gives ascending order, so negate n_groups for descending
            perm = np.argsort([-n for n in n_groups_list])
            term_permutation = np.array(perm, dtype=np.intp)

            # Apply permutation to all lists
            group_ids_list = [group_ids_list[i] for i in perm]
            n_groups_list = [n_groups_list[i] for i in perm]
            group_names = [group_names[i] for i in perm]
            group_levels_list = [group_levels_list[i] for i in perm]
            Z_blocks = [Z_blocks[i] for i in perm]
            re_structures = [re_structures[i] for i in perm]
        else:
            term_permutation = None

        # Stack all Z blocks horizontally
        Z = sp.hstack(Z_blocks, format="csc")

        return RandomEffectsInfo(
            Z=Z,
            group_ids_list=group_ids_list,
            n_groups_list=n_groups_list,
            group_names=group_names,
            random_names=all_random_names,
            re_structure="crossed",
            re_structures_list=re_structures,
            column_labels=self._generate_re_labels_crossed(
                group_names, group_levels_list, factors
            ),
            term_permutation=term_permutation,
        )

    def _build_re_nested(self, info: dict) -> RandomEffectsInfo:
        """Build random effects for nested grouping factors (a/b syntax).

        For (1|a/b), creates Z blocks for each nesting level:
        - One block for outer factor 'a'
        - One block for inner factor 'a:b' (unique combinations)

        Args:
            info: Parsed RE term dict with nested_levels key.

        Returns:
            RandomEffectsInfo with horizontally stacked Z matrices.
        """
        import scipy.sparse as sp
        from bossanova.formula.z_matrix import build_z_simple

        nested_levels = info["nested_levels"]
        X_re = info["X_re"]
        random_names = info["random_names"]

        group_ids_list = []
        n_groups_list = []
        group_names_out = []
        group_levels_list = []
        Z_blocks = []

        # For each nesting level, create a grouping
        # lme4 orders from innermost to outermost for optimization
        for depth in range(len(nested_levels)):
            if depth == 0:
                # Outermost level: use as-is
                level_name = nested_levels[0]
                group_series = self.data[level_name]
            else:
                # Inner levels: combine with outer levels
                # e.g., for a/b/c at depth 2, use a:b:c
                cols = nested_levels[: depth + 1]
                level_name = ":".join(cols)
                # Create combined grouping as string (for hashability)
                # Concatenate columns with ":" separator
                group_series = self.data.select(
                    pl.concat_str(
                        [pl.col(c).cast(str) for c in cols], separator=":"
                    ).alias("__nested_combo__")
                ).get_column("__nested_combo__")

            levels, group_ids = _extract_group_info(group_series)
            n_groups = len(levels)

            group_ids_list.append(group_ids)
            n_groups_list.append(n_groups)
            group_names_out.append(level_name)
            group_levels_list.append([str(lvl) for lvl in levels])

            # Build Z for this level
            Z_i = build_z_simple(group_ids, n_groups, X_re=X_re, layout="interleaved")
            Z_blocks.append(Z_i)

        # lme4 orders innermost first for Cholesky efficiency
        # Reverse order: innermost first
        group_ids_list = group_ids_list[::-1]
        n_groups_list = n_groups_list[::-1]
        group_names_out = group_names_out[::-1]
        group_levels_list = group_levels_list[::-1]
        Z_blocks = Z_blocks[::-1]

        # Stack all Z blocks horizontally
        Z = sp.hstack(Z_blocks, format="csc")

        # Determine structure
        re_structure = "nested"

        # Generate column labels
        column_labels = self._generate_re_labels(
            group_names_out,
            group_levels_list,
            [random_names] * len(group_names_out),
            "interleaved",
        )

        return RandomEffectsInfo(
            Z=Z,
            group_ids_list=group_ids_list,
            n_groups_list=n_groups_list,
            group_names=group_names_out,
            random_names=random_names,
            re_structure=re_structure,
            re_structures_list=["intercept"] * len(group_names_out),
            X_re=X_re,
            column_labels=column_labels,
        )

    def _generate_re_labels(
        self,
        group_names: list[str],
        levels_list: list[list[str]],
        random_names_list: list[list[str]],
        layout: str,
    ) -> list[str]:
        """Generate column labels for Z matrix."""
        labels = []
        for gname, levels, rnames in zip(
            group_names, levels_list, random_names_list, strict=True
        ):
            if layout == "interleaved":
                for level in levels:
                    for rname in rnames:
                        labels.append(f"{rname}|{gname}[{level}]")
            else:  # blocked
                for rname in rnames:
                    for level in levels:
                        labels.append(f"{rname}|{gname}[{level}]")
        return labels

    def _generate_re_labels_crossed(
        self,
        group_names: list[str],
        levels_list: list[list[str]],
        factors: dict[str, list[dict]],
    ) -> list[str]:
        """Generate column labels for crossed RE Z matrix."""
        labels = []
        for gname, levels in zip(group_names, levels_list, strict=True):
            terms = factors[gname]
            for t in terms:
                rnames = t["random_names"]
                for rname in rnames:
                    for level in levels:
                        labels.append(f"{rname}|{gname}[{level}]")
        return labels

    @property
    def has_random_effects(self) -> bool:
        """Check if formula contains random effects."""
        return len(self._re_terms) > 0

    def _evaluate_term(self, term: object) -> tuple[NDArray[np.float64], list[str]]:
        """Evaluate a single term to array and labels.

        Args:
            term: AST node representing the term.

        Returns:
            Tuple of (data array, list of column labels).
        """
        if isinstance(term, Variable):
            return self._evaluate_variable(term.name.lexeme)

        if isinstance(term, QuotedName):
            return self._evaluate_variable(term.expression.lexeme)

        if isinstance(term, Call):
            return self._evaluate_call(term)

        if isinstance(term, Grouping):
            return self._evaluate_term(term.expression)

        if isinstance(term, Binary):
            # Interaction or other binary op - defer to separate task
            # For now, just evaluate as interaction if it's :
            if term.operator.kind == "COLON":
                return self._evaluate_interaction(term)
            # * operator includes main effects + interaction
            if term.operator.kind == "STAR":
                return self._evaluate_star(term)
            # ** power operator for I(x**2) polynomial syntax
            if term.operator.kind == "STAR_STAR":
                left_data, left_labels = self._evaluate_term(term.left)
                right_data, _ = self._evaluate_term(term.right)
                # Right side should be a constant (exponent)
                if right_data.ndim > 0 and len(np.unique(right_data)) == 1:
                    exponent = right_data[0]
                else:
                    exponent = right_data
                result = np.power(left_data, exponent)
                # Generate label like "x**2"
                base_label = left_labels[0] if left_labels else "x"
                exp_label = int(exponent) if float(exponent).is_integer() else exponent
                labels = [f"{base_label}**{exp_label}"]
                return result, labels
            raise ValueError(
                f"Unsupported binary operator in term: {term.operator.kind}"
            )

        if isinstance(term, Literal):
            # Numeric literal as a term (unusual but valid)
            n_obs = len(self.data)
            val = float(term.value) if isinstance(term.value, (int, float)) else 0.0
            return np.full(n_obs, val, dtype=np.float64), [str(term.value)]

        raise ValueError(f"Unsupported term type: {type(term)}")

    def _evaluate_variable(self, name: str) -> tuple[NDArray[np.float64], list[str]]:
        """Evaluate a simple variable reference.

        Args:
            name: Column name.

        Returns:
            Tuple of (data array, labels).
        """
        if name not in self.data.columns:
            raise _variable_not_found_error(name, self.data.columns)

        series = self.data[name]
        dtype = series.dtype

        # Check if categorical
        if isinstance(dtype, (pl.Enum, pl.Categorical)) or name in self._factors:
            return self._evaluate_categorical(name, series)

        # Numeric
        return series.to_numpy().astype(np.float64), [name]

    def _evaluate_categorical(
        self,
        name: str,
        series: pl.Series,
        spans_intercept: bool | None = None,
        contrast_type: str | None = None,
    ) -> tuple[NDArray[np.float64], list[str]]:
        """Evaluate a categorical variable with contrast encoding.

        Args:
            name: Variable name.
            series: Polars series with categorical data.
            spans_intercept: Whether this categorical should span the intercept
                (use full encoding). If None, determined automatically based on
                whether intercept has been absorbed by a previous term.
            contrast_type: Type of contrast to use ("treatment", "sum", etc.).
                If None, defaults to "treatment".

        Returns:
            Tuple of (encoded array, labels).
        """
        # Get levels
        if name in self._factors:
            levels = self._factors[name]
        else:
            levels = get_levels(series)
            self._factors[name] = levels

        # Determine if this categorical spans the intercept
        if spans_intercept is None:
            spans_intercept = not self._intercept_absorbed

        # Build contrast matrix
        if spans_intercept:
            # Full rank encoding (all levels)
            contrast = _full_rank_contrast(levels)
            labels = [f"{name}[{lvl}]" for lvl in levels]
            # This categorical absorbs the intercept df
            self._intercept_absorbed = True
            # Full rank has no standard contrast type
            actual_contrast_type = "full"
        elif name in self._custom_contrasts:
            # Use custom contrast matrix provided by user
            contrast = self._custom_contrasts[name]
            actual_contrast_type = "custom"
            # Generate generic column labels for custom contrasts
            n_cols = contrast.shape[1]
            labels = [f"{name}[c{i + 1}]" for i in range(n_cols)]
        else:
            # Reduced encoding with specified contrast type
            if contrast_type == "sum":
                contrast = sum_contrast(levels)
                # Sum contrast: last level is omitted (encoded as -1s)
                ref_level = levels[-1]
                actual_contrast_type = "sum"
                labels = [f"{name}[{lvl}]" for lvl in levels if lvl != ref_level]
            elif contrast_type == "poly":
                contrast = poly_contrast(levels)
                # Poly contrast: orthogonal polynomial columns (.L, .Q, .C, ...)
                actual_contrast_type = "poly"
                labels = [f"{name}{suffix}" for suffix in poly_labels(levels)]
            else:
                # Default: treatment contrast (first level is reference)
                contrast = treatment_contrast(levels)
                ref_level = levels[0]
                actual_contrast_type = "treatment"
                labels = [f"{name}[{lvl}]" for lvl in levels if lvl != ref_level]

        self._contrast_matrices[name] = contrast
        self._contrast_types[name] = actual_contrast_type

        # Encode
        encoded = encode_categorical(series, contrast)

        return encoded, labels

    def _evaluate_call(self, call: Call) -> tuple[NDArray[np.float64], list[str]]:
        """Evaluate a function call term.

        Handles:
        - factor(), T(), S(): Categorical markers
        - center(), scale(), standardize(), zscore(): Stateful transforms
        - I(): Identity function
        - log(), log10(), sqrt(): Math transforms

        Args:
            call: Call AST node.

        Returns:
            Tuple of (data array, labels).
        """
        if not isinstance(call.callee, Variable):
            raise ValueError(f"Unsupported callee type: {type(call.callee)}")

        func_name = call.callee.name.lexeme

        # Categorical markers factor(x), factor(x, Sum), T(x), S(x)
        if func_name in ("factor", "T", "S"):
            if not call.args:
                raise ValueError(f"{func_name}() requires at least one argument")
            first_arg = call.args[0]
            var_name = self._extract_name(first_arg)
            if var_name is None:
                raise ValueError(f"First argument to {func_name}() must be a variable")
            if var_name not in self.data.columns:
                raise _variable_not_found_error(var_name, self.data.columns)
            series = self.data[var_name]
            # Extract contrast type from second argument if present
            contrast_type = None
            if len(call.args) > 1:
                contrast_type = self._extract_contrast_type(call.args[1])
            return self._evaluate_categorical(
                var_name, series, spans_intercept=None, contrast_type=contrast_type
            )

        # Identity function I() - evaluate inner expression
        if func_name == "I":
            if not call.args:
                raise ValueError("I() requires an argument")
            return self._evaluate_term(call.args[0])

        # Stateful transforms: center, scale, standardize, zscore
        if func_name in STATEFUL_TRANSFORMS:
            if not call.args:
                raise ValueError(f"{func_name}() requires an argument")
            return self._evaluate_stateful_transform(func_name, call.args[0])

        # Math transforms: log, log10, sqrt
        if func_name in ("log", "log10", "sqrt"):
            if not call.args:
                raise ValueError(f"{func_name}() requires an argument")
            return self._evaluate_math_transform(func_name, call.args[0])

        # Polynomial transform: poly(x, degree) or poly(x, degree, normalize=True/False)
        if func_name == "poly":
            if len(call.args) < 2:
                raise ValueError(
                    "poly() requires two arguments: poly(variable, degree)"
                )
            return self._evaluate_poly(call)

        # Unknown function
        raise ValueError(
            f"Unknown function '{func_name}'. "
            f"Supported: factor, T, S, I, center, scale, standardize, zscore, log, log10, sqrt, poly"
        )

    def _evaluate_stateful_transform(
        self, func_name: str, arg: object
    ) -> tuple[NDArray[np.float64], list[str]]:
        """Evaluate a stateful transform like center(), scale().

        Creates a transform instance, fits it to the data, and stores
        the state for later use with new_data.

        Args:
            func_name: Transform name (center, scale, standardize, zscore).
            arg: AST node for the argument (usually a Variable).

        Returns:
            Tuple of (transformed data array, labels).
        """
        var_name = self._extract_name(arg)
        if var_name is None:
            raise ValueError(f"{func_name}() argument must be a variable")

        if var_name not in self.data.columns:
            raise _variable_not_found_error(var_name, self.data.columns)

        # Get raw data
        raw_data = self.data[var_name].to_numpy().astype(np.float64)

        # Create transform key for storing state
        transform_key = f"{func_name}({var_name})"

        # Create and fit transform
        transform = create_transform(func_name)
        transformed = transform.fit_transform(raw_data)

        # Store transform instance and state
        self._transforms[transform_key] = transform
        self._transform_state[transform_key] = {
            "type": func_name,
            "variable": var_name,
            "params": transform.state.params,
        }

        label = f"{func_name}({var_name})"
        return transformed.reshape(-1, 1), [label]

    def _evaluate_math_transform(
        self, func_name: str, arg: object
    ) -> tuple[NDArray[np.float64], list[str]]:
        """Evaluate a math transform like log(), sqrt().

        These are stateless - they just apply a numpy function.

        Args:
            func_name: Transform name (log, log10, sqrt).
            arg: AST node for the argument (usually a Variable).

        Returns:
            Tuple of (transformed data array, labels).
        """
        var_name = self._extract_name(arg)
        if var_name is None:
            raise ValueError(f"{func_name}() argument must be a variable")

        if var_name not in self.data.columns:
            raise _variable_not_found_error(var_name, self.data.columns)

        # Get raw data
        raw_data = self.data[var_name].to_numpy().astype(np.float64)

        # Apply math function
        if func_name == "log":
            transformed = np.log(raw_data)
        elif func_name == "log10":
            transformed = np.log10(raw_data)
        elif func_name == "sqrt":
            transformed = np.sqrt(raw_data)
        else:
            raise ValueError(f"Unknown math transform: {func_name}")

        # Track in transform_state for _orig column creation
        # Math transforms are stateless, so params is empty
        transform_key = f"{func_name}({var_name})"
        self._transform_state[transform_key] = {
            "type": func_name,
            "variable": var_name,
            "params": {},
        }

        label = f"{func_name}({var_name})"
        return transformed.reshape(-1, 1), [label]

    def _evaluate_poly(self, call: Call) -> tuple[NDArray[np.float64], list[str]]:
        """Evaluate a polynomial transform: poly(x, degree) or poly(x, degree, normalize).

        Creates orthogonal polynomial basis columns for a numeric variable.

        Args:
            call: Call AST node with poly function call.

        Returns:
            Tuple of (polynomial matrix, column labels).
        """
        # Extract variable name from first argument
        var_name = self._extract_name(call.args[0])
        if var_name is None:
            raise ValueError("poly() first argument must be a variable name")

        if var_name not in self.data.columns:
            raise _variable_not_found_error(var_name, self.data.columns)

        # Extract degree from second argument (must be a literal integer)
        degree_arg = call.args[1]
        if isinstance(degree_arg, Literal):
            degree = int(degree_arg.value)
        else:
            raise ValueError(
                "poly() second argument (degree) must be an integer literal"
            )

        if degree < 1:
            raise ValueError(f"poly() degree must be >= 1, got {degree}")

        # Extract normalize from third argument if present (default True)
        normalize = True
        if len(call.args) > 2:
            norm_arg = call.args[2]
            if isinstance(norm_arg, Literal):
                normalize = bool(norm_arg.value)
            elif isinstance(norm_arg, Variable):
                # Handle normalize=True or normalize=False as keyword-style
                lexeme = norm_arg.name.lexeme.lower()
                if lexeme == "true":
                    normalize = True
                elif lexeme == "false":
                    normalize = False
                else:
                    raise ValueError(
                        f"poly() third argument must be True or False, got {lexeme}"
                    )
            else:
                raise ValueError(
                    "poly() third argument (normalize) must be True or False"
                )

        # Get raw data
        raw_data = self.data[var_name].to_numpy().astype(np.float64)

        # Apply polynomial transformation
        poly_matrix, state = poly_numeric(raw_data, degree, normalize=normalize)

        # Generate column labels: x[poly^1], x[poly^2], etc.
        labels = poly_numeric_labels(var_name, degree)

        # Store state for new_data predictions
        transform_key = f"poly({var_name}, {degree})"
        self._transform_state[transform_key] = {
            "type": "poly",
            "variable": var_name,
            "degree": degree,
            "normalize": normalize,
            "params": state,
        }

        return poly_matrix, labels

    def _evaluate_interaction(
        self, term: Binary, is_toplevel: bool = True
    ) -> tuple[NDArray[np.float64], list[str]]:
        """Evaluate an interaction term (a:b).

        Args:
            term: Binary AST node with COLON operator.
            is_toplevel: Whether this is a top-level interaction term (not nested
                in a * expansion). Affects spans_intercept tracking.

        Returns:
            Tuple of (interaction array, labels).
        """
        # For interactions, we need to track spans_intercept carefully
        # If no intercept has been absorbed, BOTH components should span
        # (this gives full factorial encoding)
        left_spans = not self._intercept_absorbed if is_toplevel else False
        right_spans = not self._intercept_absorbed if is_toplevel else False

        # Evaluate components with explicit spans_intercept control
        left_data, left_labels = self._evaluate_term_for_interaction(
            term.left, spans_intercept=left_spans
        )
        right_data, right_labels = self._evaluate_term_for_interaction(
            term.right, spans_intercept=right_spans
        )

        # Mark intercept as absorbed if either component spanned
        if left_spans or right_spans:
            self._intercept_absorbed = True

        # Ensure 2D
        if left_data.ndim == 1:
            left_data = left_data.reshape(-1, 1)
        if right_data.ndim == 1:
            right_data = right_data.reshape(-1, 1)

        # Compute all pairwise products
        n_left = left_data.shape[1]
        n_right = right_data.shape[1]
        n_obs = left_data.shape[0]

        result_cols = []
        result_labels = []

        for i in range(n_left):
            for j in range(n_right):
                result_cols.append(left_data[:, i] * right_data[:, j])
                result_labels.append(f"{left_labels[i]}:{right_labels[j]}")

        if result_cols:
            result = np.column_stack(result_cols)
        else:
            result = np.empty((n_obs, 0), dtype=np.float64)

        return result, result_labels

    def _evaluate_term_for_interaction(
        self, term: object, spans_intercept: bool
    ) -> tuple[NDArray[np.float64], list[str]]:
        """Evaluate a term as part of an interaction with explicit spans_intercept.

        This is a helper for _evaluate_interaction that allows explicit control
        over categorical encoding.

        Args:
            term: AST node representing the term.
            spans_intercept: Whether categorical terms should use full encoding.

        Returns:
            Tuple of (data array, list of column labels).
        """
        if isinstance(term, Variable):
            name = term.name.lexeme
            if name not in self.data.columns:
                raise _variable_not_found_error(name, self.data.columns)
            series = self.data[name]
            dtype = series.dtype
            if isinstance(dtype, (pl.Enum, pl.Categorical)) or name in self._factors:
                return self._evaluate_categorical(
                    name, series, spans_intercept=spans_intercept
                )
            return series.to_numpy().astype(np.float64), [name]

        if isinstance(term, QuotedName):
            name = term.expression.lexeme
            if name not in self.data.columns:
                raise _variable_not_found_error(name, self.data.columns)
            series = self.data[name]
            dtype = series.dtype
            if isinstance(dtype, (pl.Enum, pl.Categorical)) or name in self._factors:
                return self._evaluate_categorical(
                    name, series, spans_intercept=spans_intercept
                )
            return series.to_numpy().astype(np.float64), [name]

        if isinstance(term, Call):
            # For calls like factor(x) or factor(x, Sum), evaluate with contrast
            if isinstance(term.callee, Variable):
                func_name = term.callee.name.lexeme
                if func_name in ("factor", "T", "S") and term.args:
                    first_arg = term.args[0]
                    var_name = self._extract_name(first_arg)
                    if var_name and var_name in self.data.columns:
                        series = self.data[var_name]
                        # Extract contrast type from second argument if present
                        contrast_type = None
                        if len(term.args) > 1:
                            second_arg = term.args[1]
                            contrast_type = self._extract_contrast_type(second_arg)
                        return self._evaluate_categorical(
                            var_name,
                            series,
                            spans_intercept=spans_intercept,
                            contrast_type=contrast_type,
                        )
            # Fall through to regular evaluation
            return self._evaluate_call(term)

        if isinstance(term, Grouping):
            return self._evaluate_term_for_interaction(term.expression, spans_intercept)

        if isinstance(term, Binary) and term.operator.kind == "COLON":
            # Nested interaction - propagate spans_intercept to both sides
            return self._evaluate_nested_interaction(term, spans_intercept)

        # For other terms, use regular evaluation
        return self._evaluate_term(term)

    def _evaluate_nested_interaction(
        self, term: Binary, spans_intercept: bool
    ) -> tuple[NDArray[np.float64], list[str]]:
        """Evaluate a nested interaction with propagated spans_intercept.

        Args:
            term: Binary AST node with COLON operator.
            spans_intercept: Whether categorical components should use full encoding.

        Returns:
            Tuple of (interaction array, labels).
        """
        # Recursively evaluate both sides with the same spans_intercept
        left_data, left_labels = self._evaluate_term_for_interaction(
            term.left, spans_intercept=spans_intercept
        )
        right_data, right_labels = self._evaluate_term_for_interaction(
            term.right, spans_intercept=spans_intercept
        )

        # Ensure 2D
        if left_data.ndim == 1:
            left_data = left_data.reshape(-1, 1)
        if right_data.ndim == 1:
            right_data = right_data.reshape(-1, 1)

        # Compute all pairwise products
        n_left = left_data.shape[1]
        n_right = right_data.shape[1]
        n_obs = left_data.shape[0]

        result_cols = []
        result_labels = []

        for i in range(n_left):
            for j in range(n_right):
                result_cols.append(left_data[:, i] * right_data[:, j])
                result_labels.append(f"{left_labels[i]}:{right_labels[j]}")

        if result_cols:
            result = np.column_stack(result_cols)
        else:
            result = np.empty((n_obs, 0), dtype=np.float64)

        return result, result_labels

    def _evaluate_star(self, term: Binary) -> tuple[NDArray[np.float64], list[str]]:
        """Evaluate a * term (main effects + interaction).

        a * b expands to a + b + a:b

        Args:
            term: Binary AST node with STAR operator.

        Returns:
            Tuple of (combined array, labels).
        """
        # Get main effects (these will absorb intercept if needed)
        left_data, left_labels = self._evaluate_term(term.left)
        right_data, right_labels = self._evaluate_term(term.right)

        # Get interaction (main effects already absorbed intercept, so reduced encoding)
        int_data, int_labels = self._evaluate_interaction(term, is_toplevel=False)

        # Combine
        all_cols = []
        all_labels = []

        # Add left main effect
        if left_data.ndim == 1:
            all_cols.append(left_data)
        else:
            for i in range(left_data.shape[1]):
                all_cols.append(left_data[:, i])
        all_labels.extend(left_labels)

        # Add right main effect
        if right_data.ndim == 1:
            all_cols.append(right_data)
        else:
            for i in range(right_data.shape[1]):
                all_cols.append(right_data[:, i])
        all_labels.extend(right_labels)

        # Add interaction
        if int_data.ndim == 1:
            all_cols.append(int_data)
        else:
            for i in range(int_data.shape[1]):
                all_cols.append(int_data[:, i])
        all_labels.extend(int_labels)

        if all_cols:
            result = np.column_stack(all_cols)
        else:
            result = np.empty((len(self.data), 0), dtype=np.float64)

        return result, all_labels

    def evaluate_new_data(
        self,
        data: pl.DataFrame,
        *,
        on_unseen_level: str = "error",
    ) -> NDArray[np.float64]:
        """Evaluate new data using stored encodings and transforms.

        Applies the same transformations learned during build() to new data.
        This is used for predictions on new observations.

        Args:
            data: New data as Polars DataFrame. Must contain all predictor
                columns used in the formula.
            on_unseen_level: How to handle unseen categorical levels.
                - "error": Raise ValueError (default)
                - "warn": Warn and encode as zeros
                - "ignore": Silently encode as zeros

        Returns:
            Design matrix for new data, shape (n_new, n_features).
            Column order matches self.build().X_labels.

        Raises:
            ValueError: If required columns are missing from data.
            ValueError: If on_unseen_level="error" and unseen levels found.
            RuntimeError: If build() has not been called yet.

        Examples:
            >>> builder = DesignMatrixBuilder('y ~ center(x) + group', train_df)
            >>> dm = builder.build()  # Fits transforms, stores levels
            >>> X_new = builder.evaluate_new_data(test_df)
        """
        # Validate build() was called
        if not self._factors and not self._contrast_matrices and not self._transforms:
            # Check if we have any terms that would populate these
            has_cats = any(
                name in self._factors
                or isinstance(self.data[name].dtype, (pl.Enum, pl.Categorical))
                for name in self.data.columns
                if name
                in [
                    self._extract_name(t) for t in self._rhs_terms if hasattr(t, "name")
                ]
            )
            has_transforms = bool(self._transform_state)
            if not has_cats and not has_transforms:
                # Simple numeric model - that's fine
                pass

        n_obs = len(data)
        columns: list[NDArray[np.float64]] = []

        # Add intercept if model has one
        if self._has_intercept:
            columns.append(np.ones(n_obs, dtype=np.float64))

        # Evaluate each term with new data
        for term in self._rhs_terms:
            col_data = self._evaluate_term_new_data(term, data, on_unseen_level)
            if col_data.ndim == 1:
                columns.append(col_data)
            else:
                for i in range(col_data.shape[1]):
                    columns.append(col_data[:, i])

        if columns:
            return np.column_stack(columns)
        else:
            return np.empty((n_obs, 0), dtype=np.float64)

    def _evaluate_term_new_data(
        self,
        term: object,
        data: pl.DataFrame,
        on_unseen_level: str,
    ) -> NDArray[np.float64]:
        """Evaluate a term on new data using stored state.

        Args:
            term: AST node representing the term.
            data: New data DataFrame.
            on_unseen_level: How to handle unseen categorical levels.

        Returns:
            Evaluated data array.
        """
        if isinstance(term, Variable):
            return self._evaluate_variable_new_data(
                term.name.lexeme, data, on_unseen_level
            )

        if isinstance(term, QuotedName):
            return self._evaluate_variable_new_data(
                term.expression.lexeme, data, on_unseen_level
            )

        if isinstance(term, Call):
            return self._evaluate_call_new_data(term, data, on_unseen_level)

        if isinstance(term, Grouping):
            return self._evaluate_term_new_data(term.expression, data, on_unseen_level)

        if isinstance(term, Binary):
            if term.operator.kind == "COLON":
                return self._evaluate_interaction_new_data(term, data, on_unseen_level)
            if term.operator.kind == "STAR":
                return self._evaluate_star_new_data(term, data, on_unseen_level)
            raise ValueError(f"Unsupported binary operator: {term.operator.kind}")

        if isinstance(term, Literal):
            n_obs = len(data)
            val = float(term.value) if isinstance(term.value, (int, float)) else 0.0
            return np.full(n_obs, val, dtype=np.float64)

        raise ValueError(f"Unsupported term type: {type(term)}")

    def _evaluate_variable_new_data(
        self,
        name: str,
        data: pl.DataFrame,
        on_unseen_level: str,
    ) -> NDArray[np.float64]:
        """Evaluate a variable on new data.

        Args:
            name: Column name.
            data: New data DataFrame.
            on_unseen_level: How to handle unseen categorical levels.

        Returns:
            Evaluated data array.
        """
        if name not in data.columns:
            raise ValueError(f"Variable '{name}' not found in new data")

        series = data[name]

        # Check if this was treated as categorical during build
        if name in self._factors:
            return self._evaluate_categorical_new_data(name, series, on_unseen_level)

        # Numeric
        return series.to_numpy().astype(np.float64)

    def _evaluate_categorical_new_data(
        self,
        name: str,
        series: pl.Series,
        on_unseen_level: str,
    ) -> NDArray[np.float64]:
        """Evaluate categorical on new data using stored levels and contrast.

        Args:
            name: Variable name.
            series: New data series.
            on_unseen_level: How to handle unseen levels.

        Returns:
            Encoded array using stored contrast matrix.
        """
        import warnings

        stored_levels = self._factors[name]
        contrast = self._contrast_matrices[name]

        # Check for unseen levels
        # Convert to strings for comparison since stored_levels are always strings
        new_values = [str(v) for v in series.unique().to_list()]
        unseen = set(new_values) - set(stored_levels)

        if unseen:
            msg = f"Unseen levels {unseen} for variable '{name}'"
            if on_unseen_level == "error":
                raise ValueError(msg)
            elif on_unseen_level == "warn":
                warnings.warn(msg, UserWarning, stacklevel=4)
            # For both "warn" and "ignore", we'll encode unseen as zeros

        # Encode using stored levels
        n_obs = len(series)
        n_cols = contrast.shape[1]

        # Convert to stored enum ordering
        # Convert values to strings to match stored_levels format
        values = [str(v) for v in series.to_list()]
        result = np.zeros((n_obs, n_cols), dtype=np.float64)

        for i, val in enumerate(values):
            if val in stored_levels:
                level_idx = stored_levels.index(val)
                result[i, :] = contrast[level_idx, :]
            # else: unseen level, leave as zeros

        return result

    def _evaluate_call_new_data(
        self,
        call: Call,
        data: pl.DataFrame,
        on_unseen_level: str,
    ) -> NDArray[np.float64]:
        """Evaluate a function call on new data.

        Args:
            call: Call AST node.
            data: New data DataFrame.
            on_unseen_level: How to handle unseen categorical levels.

        Returns:
            Evaluated data array.
        """
        if not isinstance(call.callee, Variable):
            raise ValueError(f"Unsupported callee type: {type(call.callee)}")

        func_name = call.callee.name.lexeme

        # Categorical markers
        if func_name in ("factor", "T", "S"):
            var_name = self._extract_name(call.args[0])
            if var_name is None:
                raise ValueError(f"Could not extract variable name from {call.args[0]}")
            return self._evaluate_variable_new_data(var_name, data, on_unseen_level)

        # Identity function
        if func_name == "I":
            return self._evaluate_term_new_data(call.args[0], data, on_unseen_level)

        # Stateful transforms - use stored transform
        if func_name in STATEFUL_TRANSFORMS:
            var_name = self._extract_name(call.args[0])
            if var_name is None:
                raise ValueError(f"Could not extract variable name from {call.args[0]}")
            transform_key = f"{func_name}({var_name})"

            if transform_key not in self._transforms:
                raise RuntimeError(
                    f"Transform '{transform_key}' not found. Was build() called?"
                )

            if var_name not in data.columns:
                raise ValueError(f"Variable '{var_name}' not found in new data")

            raw_data = data[var_name].to_numpy().astype(np.float64)
            transform = self._transforms[transform_key]
            return transform.transform(raw_data).reshape(-1, 1)

        # Math transforms - stateless, just apply
        if func_name in ("log", "log10", "sqrt"):
            var_name = self._extract_name(call.args[0])

            if var_name not in data.columns:
                raise ValueError(f"Variable '{var_name}' not found in new data")

            raw_data = data[var_name].to_numpy().astype(np.float64)

            if func_name == "log":
                return np.log(raw_data).reshape(-1, 1)
            elif func_name == "log10":
                return np.log10(raw_data).reshape(-1, 1)
            elif func_name == "sqrt":
                return np.sqrt(raw_data).reshape(-1, 1)

        # Polynomial transform - use stored state
        if func_name == "poly":
            var_name = self._extract_name(call.args[0])
            if var_name is None:
                raise ValueError("poly() first argument must be a variable name")

            # Extract degree from second argument
            degree_arg = call.args[1]
            if isinstance(degree_arg, Literal):
                degree = int(degree_arg.value)
            else:
                raise ValueError("poly() second argument (degree) must be an integer")

            transform_key = f"poly({var_name}, {degree})"

            if transform_key not in self._transform_state:
                raise RuntimeError(
                    f"Polynomial transform '{transform_key}' not found. Was build() called?"
                )

            if var_name not in data.columns:
                raise ValueError(f"Variable '{var_name}' not found in new data")

            # Get stored state and apply transformation
            stored = self._transform_state[transform_key]
            raw_data = data[var_name].to_numpy().astype(np.float64)

            # Apply poly_numeric with stored state
            poly_matrix, _ = poly_numeric(
                raw_data,
                degree=stored["degree"],
                normalize=stored["normalize"],
                state=stored["params"],
            )
            return poly_matrix

        raise ValueError(f"Unknown function: {func_name}")

    def _evaluate_interaction_new_data(
        self,
        term: Binary,
        data: pl.DataFrame,
        on_unseen_level: str,
    ) -> NDArray[np.float64]:
        """Evaluate interaction term on new data.

        Args:
            term: Binary AST node with COLON operator.
            data: New data DataFrame.
            on_unseen_level: How to handle unseen categorical levels.

        Returns:
            Interaction data array.
        """
        left_data = self._evaluate_term_new_data(term.left, data, on_unseen_level)
        right_data = self._evaluate_term_new_data(term.right, data, on_unseen_level)

        # Ensure 2D
        if left_data.ndim == 1:
            left_data = left_data.reshape(-1, 1)
        if right_data.ndim == 1:
            right_data = right_data.reshape(-1, 1)

        # Compute pairwise products
        n_left = left_data.shape[1]
        n_right = right_data.shape[1]
        n_obs = left_data.shape[0]

        result_cols = []
        for i in range(n_left):
            for j in range(n_right):
                result_cols.append(left_data[:, i] * right_data[:, j])

        if result_cols:
            return np.column_stack(result_cols)
        else:
            return np.empty((n_obs, 0), dtype=np.float64)

    def _evaluate_star_new_data(
        self,
        term: Binary,
        data: pl.DataFrame,
        on_unseen_level: str,
    ) -> NDArray[np.float64]:
        """Evaluate star term (a * b = a + b + a:b) on new data.

        Args:
            term: Binary AST node with STAR operator.
            data: New data DataFrame.
            on_unseen_level: How to handle unseen categorical levels.

        Returns:
            Combined data array.
        """
        left_data = self._evaluate_term_new_data(term.left, data, on_unseen_level)
        right_data = self._evaluate_term_new_data(term.right, data, on_unseen_level)
        int_data = self._evaluate_interaction_new_data(term, data, on_unseen_level)

        all_cols = []

        # Left main effect
        if left_data.ndim == 1:
            all_cols.append(left_data)
        else:
            for i in range(left_data.shape[1]):
                all_cols.append(left_data[:, i])

        # Right main effect
        if right_data.ndim == 1:
            all_cols.append(right_data)
        else:
            for i in range(right_data.shape[1]):
                all_cols.append(right_data[:, i])

        # Interaction
        if int_data.ndim == 1:
            all_cols.append(int_data)
        else:
            for i in range(int_data.shape[1]):
                all_cols.append(int_data[:, i])

        if all_cols:
            return np.column_stack(all_cols)
        else:
            return np.empty((len(data), 0), dtype=np.float64)
