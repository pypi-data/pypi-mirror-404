"""Z matrix (random effects design matrix) construction.

This module provides functions to build sparse Z matrices from
parsed random effects specifications. Z matrices have structure:

    Z[i, g*n_re + r] = X_re[i, r] if group[i] == g else 0

where r indexes the random effect (intercept, slopes) and g indexes
the group level.

Column Layouts:
    - Interleaved (lme4 default for correlated slopes):
      [g1_int, g1_x, g2_int, g2_x, ...]
      Each group's random effects are contiguous.
    - Blocked (lme4 for uncorrelated || syntax):
      [g1_int, g2_int, ..., g1_x, g2_x, ...]
      All intercepts first, then all slopes.

Construction is done directly in sparse COO format without dense
intermediates, enabling efficient handling of large-scale crossed
random effects (e.g., InstEval with 73k obs × 4k groups uses ~2MB
instead of ~2.4GB with dense construction).

Examples:
    >>> import numpy as np
    >>> from bossanova.formula.z_matrix import build_z_simple
    >>> group_ids = np.array([0, 0, 1, 1, 2, 2])
    >>> Z = build_z_simple(group_ids, n_groups=3)
    >>> Z.shape
    (6, 3)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

import numpy as np
import scipy.sparse as sp
from numpy.typing import NDArray

if TYPE_CHECKING:
    pass

__all__ = [
    "RandomEffectsInfo",
    "build_z_simple",
    "build_z_nested",
    "build_z_crossed",
    "build_random_effects",
]


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class RandomEffectsInfo:
    """Complete random effects specification for lmer/glmer.

    This container holds the Z matrix and all metadata needed for
    downstream operations (Lambda building, initialization, results).

    Attributes:
        Z: Sparse random effects design matrix, shape (n, q).
        group_ids_list: Group ID arrays for each factor.
        n_groups_list: Number of groups per factor.
        group_names: Names of grouping factors.
        random_names: Names of random effect terms.
        re_structure: Overall structure type
            (intercept/slope/diagonal/nested/crossed).
        re_structures_list: Per-factor structure types (for mixed).
        X_re: Random effects covariates (for slopes).
        column_labels: Z column names for output.
        term_permutation: Block ordering permutation indices.
    """

    Z: sp.csc_matrix
    group_ids_list: list[NDArray[np.intp]]
    n_groups_list: list[int]
    group_names: list[str]
    random_names: list[str]
    re_structure: str
    re_structures_list: list[str] | None = None
    X_re: NDArray[np.float64] | list[NDArray[np.float64]] | None = None
    column_labels: list[str] = field(default_factory=list)
    term_permutation: NDArray[np.intp] | None = None


# =============================================================================
# Internal Helpers
# =============================================================================


def _build_z_sparse_interleaved(
    group_ids: NDArray[np.intp],
    n_groups: int,
    X_re: NDArray[np.float64],
) -> sp.csc_matrix:
    """Build Z matrix directly in sparse format (interleaved layout).

    Constructs Z in COO format without dense intermediates. For InstEval-scale
    data (73k obs × 4k groups), this uses ~2MB instead of ~2.4GB.

    Interleaved layout: [g1_int, g1_x, g2_int, g2_x, ...]
    Column index for obs i, group g, random effect r: g * n_re + r

    Args:
        group_ids: Array of group assignments, shape (n,), values 0..n_groups-1.
        n_groups: Total number of groups.
        X_re: Random effects design matrix, shape (n, n_re).

    Returns:
        Sparse Z matrix in CSC format, shape (n, n_groups * n_re).
    """
    n = len(group_ids)
    n_re = X_re.shape[1]

    # Each observation contributes n_re non-zeros (one per random effect term)
    # Row indices: [0,0,..,0, 1,1,..,1, ..., n-1,n-1,..,n-1] (each repeated n_re times)
    rows = np.repeat(np.arange(n, dtype=np.intp), n_re)

    # Column indices for interleaved: col = group_id * n_re + re_index
    # For each obs i: [g[i]*n_re + 0, g[i]*n_re + 1, ..., g[i]*n_re + (n_re-1)]
    cols = (group_ids[:, None] * n_re + np.arange(n_re, dtype=np.intp)).ravel()

    # Data values: X_re flattened row-by-row
    data = X_re.ravel().astype(np.float64)

    return sp.csc_matrix(
        sp.coo_matrix((data, (rows, cols)), shape=(n, n_groups * n_re))
    )


def _build_z_sparse_blocked(
    group_ids: NDArray[np.intp],
    n_groups: int,
    X_re: NDArray[np.float64],
) -> sp.csc_matrix:
    """Build Z matrix directly in sparse format (blocked layout).

    Blocked layout: [g1_int, g2_int, ..., g1_x, g2_x, ...]
    Column index for obs i, group g, random effect r: r * n_groups + g

    Args:
        group_ids: Array of group assignments, shape (n,), values 0..n_groups-1.
        n_groups: Total number of groups.
        X_re: Random effects design matrix, shape (n, n_re).

    Returns:
        Sparse Z matrix in CSC format, shape (n, n_groups * n_re).
    """
    n = len(group_ids)
    n_re = X_re.shape[1]

    # Row indices: same as interleaved
    rows = np.repeat(np.arange(n, dtype=np.intp), n_re)

    # Column indices for blocked: col = re_index * n_groups + group_id
    # For each obs i: [0*n_groups + g[i], 1*n_groups + g[i], ..., (n_re-1)*n_groups + g[i]]
    cols = (np.arange(n_re, dtype=np.intp)[:, None] * n_groups + group_ids).T.ravel()

    # Data values: X_re but we need to reorder to match column order
    # For blocked, we want [X_re[i,0], X_re[i,1], ...] for each i
    # which is just X_re flattened row-by-row (same as interleaved)
    data = X_re.ravel().astype(np.float64)

    return sp.csc_matrix(
        sp.coo_matrix((data, (rows, cols)), shape=(n, n_groups * n_re))
    )


def _generate_column_labels(
    group_name: str,
    group_levels: list[str] | None,
    random_names: list[str],
    n_groups: int,
    layout: Literal["interleaved", "blocked"],
) -> list[str]:
    """Generate human-readable column labels for Z matrix.

    Args:
        group_name: Name of grouping factor (e.g., "Subject").
        group_levels: Level names, or None to use indices.
        random_names: Names of random effects (e.g., ["Intercept", "Days"]).
        n_groups: Number of groups.
        layout: Column layout.

    Returns:
        List of column labels.
    """
    if group_levels is None:
        group_levels = [str(i) for i in range(n_groups)]

    labels = []

    if layout == "interleaved":
        for g, level in enumerate(group_levels):
            for r, re_name in enumerate(random_names):
                labels.append(f"{re_name}|{group_name}[{level}]")
    else:  # blocked
        for r, re_name in enumerate(random_names):
            for g, level in enumerate(group_levels):
                labels.append(f"{re_name}|{group_name}[{level}]")

    return labels


# =============================================================================
# Core Construction Functions
# =============================================================================


def build_z_simple(
    group_ids: NDArray[np.intp],
    n_groups: int,
    X_re: NDArray[np.float64] | None = None,
    layout: Literal["interleaved", "blocked"] = "interleaved",
) -> sp.csc_matrix:
    """Build Z matrix for single grouping factor.

    Constructs Z directly in sparse COO format without dense intermediates.
    For large-scale data (e.g., InstEval with 73k obs × 4k groups), this
    uses O(n × n_re) memory instead of O(n × n_groups × n_re).

    Handles intercept-only, correlated slopes, and uncorrelated slopes
    by varying the X_re input and layout parameter.

    Args:
        group_ids: Array of group assignments, shape (n,), values 0..n_groups-1.
        n_groups: Total number of groups.
        X_re: Random effects design matrix, shape (n, n_re).
            - None or column of 1s: intercept only
            - Multiple columns: intercept + slopes
        layout: Column ordering.
            - "interleaved": [g1_int, g1_slope, g2_int, g2_slope, ...]
            - "blocked": [g1_int, g2_int, ..., g1_slope, g2_slope, ...]

    Returns:
        Sparse Z matrix in CSC format, shape (n, n_groups * n_re).

    Examples:
        >>> # Random intercept only
        >>> group_ids = np.array([0, 0, 1, 1])
        >>> Z = build_z_simple(group_ids, n_groups=2)
        >>> Z.shape
        (4, 2)

        >>> # Random intercept + slope (correlated)
        >>> X_re = np.column_stack([np.ones(4), [1, 2, 1, 2]])
        >>> Z = build_z_simple(group_ids, n_groups=2, X_re=X_re, layout="interleaved")
        >>> Z.shape
        (4, 4)

        >>> # Uncorrelated random effects
        >>> Z = build_z_simple(group_ids, n_groups=2, X_re=X_re, layout="blocked")
        >>> Z.shape
        (4, 4)
    """
    n = len(group_ids)

    # Handle intercept-only case
    if X_re is None:
        X_re = np.ones((n, 1), dtype=np.float64)
    elif X_re.ndim == 1:
        X_re = X_re.reshape(-1, 1)

    # Build Z directly in sparse format (no dense intermediates)
    if layout == "interleaved":
        return _build_z_sparse_interleaved(group_ids, n_groups, X_re)
    else:
        return _build_z_sparse_blocked(group_ids, n_groups, X_re)


def build_z_nested(
    group_ids_list: list[NDArray[np.intp]],
    n_groups_list: list[int],
    X_re_list: list[NDArray[np.float64] | None] | None = None,
) -> sp.csc_matrix:
    """Build Z matrix for nested random effects.

    Nested effects like (1|school/class) create separate random intercepts
    for each level of the hierarchy. The Z matrix is a horizontal
    concatenation of Z matrices for each level.

    Args:
        group_ids_list: List of group ID arrays, ordered [inner, ..., outer].
            For (1|school/class): [class_ids, school_ids].
        n_groups_list: Number of groups at each level.
        X_re_list: Random effects design per level, or None for intercepts.

    Returns:
        Sparse Z matrix, shape (n, sum(n_groups_i * n_re_i)).

    Examples:
        >>> # (1|school/class) with 2 schools, 4 classes total
        >>> class_ids = np.array([0, 0, 1, 1, 2, 2, 3, 3])
        >>> school_ids = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        >>> Z = build_z_nested(
        ...     group_ids_list=[class_ids, school_ids],
        ...     n_groups_list=[4, 2]
        ... )
        >>> Z.shape
        (8, 6)  # 4 class columns + 2 school columns
    """
    n_levels = len(group_ids_list)

    # Default: intercept at each level
    if X_re_list is None:
        X_re_list = [None] * n_levels

    # Build Z for each level and stack horizontally
    Z_blocks = []
    for i, (gids, n_g, xre) in enumerate(
        zip(group_ids_list, n_groups_list, X_re_list, strict=True)
    ):
        # Nested effects typically use intercept at each level
        # Layout doesn't matter for intercept-only
        Z_i = build_z_simple(gids, n_g, X_re=xre, layout="interleaved")
        Z_blocks.append(Z_i)

    return sp.hstack(Z_blocks, format="csc")


def build_z_crossed(
    group_ids_list: list[NDArray[np.intp]],
    n_groups_list: list[int],
    X_re_list: list[NDArray[np.float64] | None] | None = None,
    layouts: list[str] | None = None,
) -> sp.csc_matrix:
    """Build Z matrix for crossed random effects.

    Crossed effects like (1|subject) + (1|item) create independent
    random effects for each factor. The Z matrix is a horizontal
    concatenation of Z matrices for each factor.

    Args:
        group_ids_list: List of group ID arrays, one per factor.
        n_groups_list: Number of groups per factor.
        X_re_list: Random effects design per factor, or None for intercepts.
        layouts: Layout per factor. Default: interleaved for all.

    Returns:
        Sparse Z matrix, shape (n, sum(n_groups_i * n_re_i)).

    Examples:
        >>> # (1|subject) + (1|item) with 3 subjects, 4 items
        >>> subj_ids = np.array([0, 1, 2, 0, 1, 2])
        >>> item_ids = np.array([0, 0, 0, 1, 1, 1])
        >>> Z = build_z_crossed(
        ...     group_ids_list=[subj_ids, item_ids],
        ...     n_groups_list=[3, 4]
        ... )
        >>> Z.shape
        (6, 7)  # 3 subject + 4 item columns
    """
    n_factors = len(group_ids_list)

    # Defaults
    if X_re_list is None:
        X_re_list = [None] * n_factors
    if layouts is None:
        layouts = ["interleaved"] * n_factors

    # Build Z for each factor and stack horizontally
    Z_blocks: list[sp.csc_matrix] = []
    for i, (gids, n_g, xre) in enumerate(
        zip(group_ids_list, n_groups_list, X_re_list, strict=True)
    ):
        layout_i: Literal["interleaved", "blocked"] = (
            "interleaved" if layouts[i] == "interleaved" else "blocked"
        )
        Z_i = build_z_simple(gids, n_g, X_re=xre, layout=layout_i)
        Z_blocks.append(Z_i)

    return sp.hstack(Z_blocks, format="csc")


# =============================================================================
# High-Level Builder
# =============================================================================


def build_random_effects(
    group_ids_list: list[NDArray[np.intp]],
    n_groups_list: list[int],
    group_names: list[str],
    random_names: list[str],
    re_structure: str,
    X_re: NDArray[np.float64] | list[NDArray[np.float64]] | None = None,
    re_structures_list: list[str] | None = None,
    group_levels_list: list[list[str]] | None = None,
    term_permutation: NDArray[np.intp] | None = None,
) -> RandomEffectsInfo:
    """Build complete random effects specification.

    High-level function that constructs the Z matrix and packages
    all metadata into a RandomEffectsInfo container ready for
    lmer/glmer consumption.

    Args:
        group_ids_list: Group ID arrays for each factor.
        n_groups_list: Number of groups per factor.
        group_names: Names of grouping factors.
        random_names: Names of random effect terms.
        re_structure: Overall structure type:
            - "intercept": random intercept only
            - "slope": correlated intercept + slopes
            - "diagonal": uncorrelated intercept + slopes
            - "nested": nested hierarchy
            - "crossed": crossed factors
        X_re: Random effects covariates (for slopes).
        re_structures_list: Per-factor structure (for mixed).
        group_levels_list: Level names per factor (for labels).
        term_permutation: Block ordering permutation.

    Returns:
        RandomEffectsInfo with Z matrix and all metadata.

    Examples:
        >>> # (Days|Subject) with 18 subjects
        >>> group_ids = np.arange(180) // 10
        >>> n_groups = 18
        >>> X_re = np.column_stack([np.ones(180), np.tile(np.arange(10), 18)])
        >>> info = build_random_effects(
        ...     group_ids_list=[group_ids],
        ...     n_groups_list=[n_groups],
        ...     group_names=["Subject"],
        ...     random_names=["Intercept", "Days"],
        ...     re_structure="slope",
        ...     X_re=X_re,
        ... )
        >>> info.Z.shape
        (180, 36)  # 18 subjects * 2 RE
    """
    # Determine layout based on structure
    if re_structure == "intercept":
        # Single factor, intercept only
        Z = build_z_simple(
            group_ids_list[0],
            n_groups_list[0],
            X_re=None,
            layout="interleaved",
        )
        effective_random_names = ["Intercept"]

    elif re_structure == "slope":
        # Single factor, correlated slopes
        # Uses interleaved layout: [g1_int, g1_x, g2_int, g2_x, ...]
        # This matches our Lambda builder's block-diagonal structure
        Z = build_z_simple(
            group_ids_list[0],
            n_groups_list[0],
            X_re=X_re if not isinstance(X_re, list) else X_re[0],
            layout="interleaved",
        )
        effective_random_names = random_names

    elif re_structure == "diagonal":
        # Single factor, uncorrelated slopes (blocked)
        Z = build_z_simple(
            group_ids_list[0],
            n_groups_list[0],
            X_re=X_re if not isinstance(X_re, list) else X_re[0],
            layout="blocked",
        )
        effective_random_names = random_names

    elif re_structure == "nested":
        # Multiple levels, horizontal stack
        X_re_nested: list[NDArray[np.float64] | None] | None
        if isinstance(X_re, list):
            X_re_nested = list(X_re)  # type: ignore[arg-type]
        elif X_re is not None:
            X_re_nested = [X_re] * len(group_ids_list)
        else:
            X_re_nested = None
        Z = build_z_nested(group_ids_list, n_groups_list, X_re_nested)
        effective_random_names = random_names

    elif re_structure == "crossed":
        # Multiple factors, horizontal stack
        # Each factor may have different structure
        if re_structures_list is None:
            re_structures_list = ["intercept"] * len(group_ids_list)

        X_re_crossed: list[NDArray[np.float64] | None] | None
        if isinstance(X_re, list):
            X_re_crossed = list(X_re)  # type: ignore[arg-type]
        elif X_re is not None:
            X_re_crossed = [X_re] * len(group_ids_list)
        else:
            X_re_crossed = None
        layouts = [
            "blocked" if s == "diagonal" else "interleaved" for s in re_structures_list
        ]
        Z = build_z_crossed(group_ids_list, n_groups_list, X_re_crossed, layouts)
        effective_random_names = random_names

    else:
        raise ValueError(f"Unknown re_structure: {re_structure}")

    # Generate column labels
    column_labels = []
    if re_structure in ("intercept", "slope", "diagonal"):
        layout = "blocked" if re_structure == "diagonal" else "interleaved"
        levels = group_levels_list[0] if group_levels_list else None
        column_labels = _generate_column_labels(
            group_names[0],
            levels,
            effective_random_names,
            n_groups_list[0],
            layout,
        )
    else:
        # Nested/crossed: concatenate labels for each factor
        for i, (gname, n_g) in enumerate(zip(group_names, n_groups_list, strict=True)):
            levels = group_levels_list[i] if group_levels_list else None
            re_names_i = (
                [effective_random_names[i]]
                if i < len(effective_random_names)
                else ["Intercept"]
            )
            layout_i = (
                "blocked"
                if re_structures_list and re_structures_list[i] == "diagonal"
                else "interleaved"
            )
            column_labels.extend(
                _generate_column_labels(gname, levels, re_names_i, n_g, layout_i)
            )

    return RandomEffectsInfo(
        Z=Z,
        group_ids_list=group_ids_list,
        n_groups_list=n_groups_list,
        group_names=group_names,
        random_names=effective_random_names,
        re_structure=re_structure,
        re_structures_list=re_structures_list,
        X_re=X_re,
        column_labels=column_labels,
        term_permutation=term_permutation,
    )
