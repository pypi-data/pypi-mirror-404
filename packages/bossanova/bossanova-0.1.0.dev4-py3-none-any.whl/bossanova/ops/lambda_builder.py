"""Lambda matrix construction from theta parameters.

Lambda is the Cholesky-like factor of the random effects covariance matrix.
It is block-diagonal, with blocks corresponding to grouping factors.

Theta Parameterization (lme4-compatible):
-----------------------------------------
Theta contains elements of the lower triangular Cholesky factor L, where
the random effects covariance is Σ = σ² * Λ * Λ' and Λ is built from theta.

Theta is on the **relative scale** (divided by σ), following lme4's convention.

Examples:
- Random intercept (1|group): theta = [τ/σ], dim = 1
- Correlated slopes (1+x|group): theta = [L₀₀/σ, L₁₀/σ, L₁₁/σ], dim = 3
- Uncorrelated slopes (1+x||group): theta = [L₀₀/σ, L₁₁/σ], dim = 2
- Nested (1|school/class): theta = [τ₁/σ, τ₂/σ], dim = 2
- Crossed (1|subject) + (1|item): theta = [τ₁/σ, τ₂/σ], dim = 2

During optimization, theta is constrained:
- Diagonal elements: θ ≥ 0 (ensures PSD)
- Off-diagonal elements: -∞ < θ < ∞

Performance Note:
-----------------
For repeated Lambda construction with varying theta (optimization), use
LambdaTemplate to cache the sparsity pattern and only update values.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import scipy.sparse as sp

if TYPE_CHECKING:
    pass

__all__ = [
    "LambdaTemplate",
    "PatternTemplate",
    "build_lambda_template",
    "update_lambda_from_template",
    "theta_to_cholesky_block",
    "cholesky_block_to_theta",
    "theta_to_variance_params",
    "build_lambda_sparse",
    "build_pattern_template",
    "compute_zl_preserve_pattern",
    "compute_s22_preserve_pattern",
]


@dataclass
class LambdaTemplate:
    """Template for efficient Lambda matrix updates during optimization.

    Caches the sparsity pattern of Lambda so that repeated calls only
    update the data values, avoiding reconstruction of indices.

    Attributes:
        template: Sparse CSC matrix with correct structure but placeholder values.
        theta_to_data_map: List mapping theta indices to positions in template.data.
            Each element is an int64 array of indices into template.data.
        re_structure: The random effects structure type.
        n_groups_list: Number of groups per factor.
    """

    template: sp.csc_matrix
    theta_to_data_map: list[np.ndarray]  # List of int arrays, not object array
    re_structure: str
    n_groups_list: list[int]


@dataclass
class PatternTemplate:
    """Template for preserving sparsity patterns across theta evaluations.

    This is critical for cross-theta Cholesky caching. When theta has boundary
    values (θ=0), the resulting matrices would normally have fewer non-zeros.
    This template ensures the sparsity pattern remains constant by storing
    explicit zeros where needed.

    Used to match lme4's behavior where the sparsity pattern is fixed at
    initialization and never changes during optimization.

    Attributes:
        ZL_pattern: Sparsity pattern of Z @ Lambda (computed with theta=ones).
        S22_pattern: Sparsity pattern of ZL' @ ZL + I (computed with theta=ones).
        Z: Reference to the original Z matrix for value computation.
        lambda_template: Reference to the LambdaTemplate.
    """

    ZL_pattern: sp.csc_matrix
    S22_pattern: sp.csc_matrix
    Z: sp.csc_matrix
    lambda_template: "LambdaTemplate"


def build_lambda_template(
    n_groups_list: list[int],
    re_structure: str,
    metadata: dict | None = None,
) -> LambdaTemplate:
    """Build a Lambda template for efficient repeated updates.

    Creates a sparse matrix template with the correct sparsity pattern,
    plus a mapping from theta indices to data array positions.

    Args:
        n_groups_list: Number of groups per grouping factor.
        re_structure: Random effects structure type.
        metadata: Optional metadata dict with structure information.

    Returns:
        LambdaTemplate with template matrix and theta-to-data mapping.

    Examples:
        >>> # Create template for random intercept model
        >>> template = build_lambda_template([18], "intercept")
        >>> template.template.shape
        (18, 18)

        >>> # Update with new theta values
        >>> Lambda = update_lambda_from_template(template, np.array([1.5]))
        >>> Lambda.data[0]
        1.5

    Notes:
        - Template is built once per model, reused during optimization
        - theta_to_data_map[i] gives indices in template.data for theta[i]
    """
    if metadata is None:
        metadata = {}

    if re_structure == "intercept":
        if len(n_groups_list) == 1:
            # Simple intercept: diagonal matrix
            n_groups = n_groups_list[0]
            template = sp.diags(
                [1.0], offsets=0, shape=(n_groups, n_groups), format="csc"
            )
            # theta[0] maps to all diagonal positions
            theta_to_data_map = [np.arange(n_groups, dtype=np.int64)]
        else:
            # Multiple factors: block diagonal of diagonals
            blocks = []
            theta_to_data_map = []
            offset = 0
            for n_groups in n_groups_list:
                block = sp.diags(
                    [1.0], offsets=0, shape=(n_groups, n_groups), format="csc"
                )
                blocks.append(block)
                theta_to_data_map.append(
                    np.arange(offset, offset + n_groups, dtype=np.int64)
                )
                offset += n_groups
            template = sp.block_diag(blocks, format="csc")

    elif re_structure == "diagonal":
        # Uncorrelated slopes: blocked diagonal
        n_groups = n_groups_list[0]
        k = _infer_diagonal_dim(metadata)
        q = n_groups * k

        template = sp.diags([1.0] * q, offsets=0, shape=(q, q), format="csc")

        # theta[i] maps to positions [i*n_groups, ..., (i+1)*n_groups - 1]
        theta_to_data_map = [
            np.arange(i * n_groups, (i + 1) * n_groups, dtype=np.int64)
            for i in range(k)
        ]

    elif re_structure == "slope":
        # Correlated slopes: block diagonal of Cholesky blocks
        dim = _infer_slope_dim(metadata)
        n_groups = n_groups_list[0]
        n_theta = dim * (dim + 1) // 2

        # Build single block template
        L_template = np.zeros((dim, dim))
        idx = 0
        for col in range(dim):
            for row in range(col, dim):
                L_template[row, col] = 1.0
                idx += 1

        block_sparse = sp.csc_matrix(L_template)
        blocks = [block_sparse.copy() for _ in range(n_groups)]
        template = sp.block_diag(blocks, format="csc")

        # Build theta-to-data mapping
        # For each theta element, find which positions in template.data it affects
        theta_to_data_map = []
        nnz_per_block = block_sparse.nnz

        for theta_idx in range(n_theta):
            # Find position of this theta in a single block
            block_data_idx = theta_idx  # Since we fill column-major in lower triangle
            # This theta affects all blocks at the same position
            positions = np.array(
                [g * nnz_per_block + block_data_idx for g in range(n_groups)],
                dtype=np.int64,
            )
            theta_to_data_map.append(positions)

    else:
        # Template caching is a performance optimization for simple structures.
        # Nested/crossed/mixed structures use build_lambda_sparse() directly,
        # which handles ALL random effect structures correctly.
        # This NotImplementedError only affects callers requesting a template,
        # not the core fitting algorithms (which use build_lambda_sparse).
        theta_to_data_map = None
        template = None

    if template is None:
        raise NotImplementedError(
            f"Lambda template caching not implemented for re_structure='{re_structure}'. "
            f"Use build_lambda_sparse() for full support of all RE structures."
        )

    return LambdaTemplate(
        template=template,
        theta_to_data_map=theta_to_data_map,
        re_structure=re_structure,
        n_groups_list=n_groups_list,
    )


def update_lambda_from_template(
    template: LambdaTemplate,
    theta: np.ndarray,
) -> sp.csc_matrix:
    """Update Lambda matrix from template using new theta values.

    Efficiently updates only the data values without rebuilding structure.

    Args:
        template: LambdaTemplate created by build_lambda_template.
        theta: New theta values.

    Returns:
        Updated sparse Lambda matrix in CSC format.

    Examples:
        >>> template = build_lambda_template([18], "intercept")
        >>> Lambda = update_lambda_from_template(template, np.array([1.5]))
        >>> Lambda[0, 0]
        1.5

    Notes:
        - Much faster than build_lambda_sparse for repeated calls
        - Modifies template.data in place for maximum efficiency
    """
    # Copy the template (to avoid modifying the original)
    Lambda = template.template.copy()

    # Update data values based on mapping
    for theta_idx, data_indices in enumerate(template.theta_to_data_map):
        Lambda.data[data_indices] = theta[theta_idx]

    return Lambda


def _infer_diagonal_dim(metadata: dict) -> int:
    """Infer dimension for diagonal structure from metadata."""
    if "re_terms" in metadata:
        return len(metadata["re_terms"])
    if "random_names" in metadata:
        return len(metadata["random_names"])
    return 2  # Default: intercept + slope


def _infer_slope_dim(metadata: dict) -> int:
    """Infer dimension for slope structure from metadata."""
    if "re_terms" in metadata:
        return len(metadata["re_terms"])
    if "random_names" in metadata:
        return len(metadata["random_names"])
    return 2  # Default: intercept + slope


def theta_to_cholesky_block(theta: np.ndarray, dim: int) -> np.ndarray:
    """Convert theta vector to lower-triangular Cholesky block.

    Args:
        theta: Cholesky factor elements (lower triangle, column-major).
            For 2×2: [L₀₀, L₁₀, L₁₁], length = 3
            For 3×3: [L₀₀, L₁₀, L₁₁, L₂₀, L₂₁, L₂₂], length = 6
        dim: Dimension of the Cholesky block (2, 3, etc.).

    Returns:
        Lower triangular Cholesky block, shape (dim, dim).

    Examples:
        >>> theta = np.array([1.5, 0.3, 1.2])
        >>> L = theta_to_cholesky_block(theta, 2)
        >>> L
        array([[1.5, 0. ],
               [0.3, 1.2]])

    Notes:
        - Fills lower triangle column-by-column (Fortran order)
        - Diagonal elements should be positive for valid Cholesky
    """
    # Verify theta length
    expected_len = dim * (dim + 1) // 2
    if len(theta) != expected_len:
        raise ValueError(
            f"theta length ({len(theta)}) does not match expected "
            f"length ({expected_len}) for dim={dim}"
        )

    # Build lower triangular matrix
    L = np.zeros((dim, dim))
    idx = 0
    for col in range(dim):
        for row in range(col, dim):
            L[row, col] = theta[idx]
            idx += 1

    return L


def cholesky_block_to_theta(L: np.ndarray) -> np.ndarray:
    """Convert lower-triangular Cholesky block to theta vector.

    Args:
        L: Lower triangular Cholesky block, shape (dim, dim).

    Returns:
        Theta vector (lower triangle elements, column-major).

    Examples:
        >>> L = np.array([[1.5, 0.0], [0.3, 1.2]])
        >>> theta = cholesky_block_to_theta(L)
        >>> theta
        array([1.5, 0.3, 1.2])

    Notes:
        - Extracts lower triangle column-by-column
        - Inverse of theta_to_cholesky_block
    """
    dim = L.shape[0]
    theta = []

    for col in range(dim):
        for row in range(col, dim):
            theta.append(L[row, col])

    return np.array(theta)


def theta_to_variance_params(
    theta: np.ndarray, is_diagonal: bool = False
) -> tuple[np.ndarray, np.ndarray]:
    """Convert theta (Cholesky elements) to variance parameters.

    Computes standard deviations and correlations from Cholesky factor.

    Args:
        theta: Cholesky factor elements (lower triangle, column-major).
            For intercept: [L₀₀], length = 1
            For slopes (2D): [L₀₀, L₁₀, L₁₁], length = 3
            For diagonal (2D): [L₀₀, L₁₁], length = 2
        is_diagonal: If True, theta contains only diagonal elements (|| syntax).

    Returns:
        Tuple of (standard_deviations, correlations):
        - standard_deviations: sqrt(diag(Σ)), shape (n,)
        - correlations: off-diagonal correlations, shape (n*(n-1)/2,)

    Examples:
        >>> # Correlated slopes
        >>> theta = np.array([1.5, 0.3, 1.2])
        >>> sds, rhos = theta_to_variance_params(theta)
        >>> sds  # sqrt(diag(L @ L.T))
        array([1.5       , 1.23693169])
        >>> rhos  # correlation between intercept and slope
        array([0.24253563])

        >>> # Uncorrelated slopes
        >>> theta = np.array([1.5, 1.2])
        >>> sds, rhos = theta_to_variance_params(theta, is_diagonal=True)
        >>> sds
        array([1.5, 1.2])
        >>> rhos  # empty for diagonal structure
        array([])

    Notes:
        - For diagonal structures, SDs are just theta values
        - For full structures, computes Σ = L @ L.T then extracts params
    """
    n_theta = len(theta)

    # Simple intercept: single parameter
    if n_theta == 1:
        return theta, np.array([])

    # Diagonal structure: no correlations
    if is_diagonal:
        return theta, np.array([])

    # Full structure: compute from Cholesky
    # Determine dimension: n*(n+1)/2 = n_theta => n = (-1 + sqrt(1 + 8*n_theta)) / 2
    dim = int((-1 + np.sqrt(1 + 8 * n_theta)) / 2)

    if dim * (dim + 1) // 2 != n_theta:
        raise ValueError(
            f"Invalid theta length {n_theta}. Must be triangular number (1, 3, 6, ...)"
        )

    # Reconstruct Cholesky block
    L = theta_to_cholesky_block(theta, dim)

    # Compute covariance: Σ = L @ L.T
    Sigma = L @ L.T

    # Extract standard deviations
    sds = np.sqrt(np.diag(Sigma))

    # Extract correlations (lower triangle, excluding diagonal)
    rhos = []
    for i in range(dim):
        for j in range(i):
            denom = sds[i] * sds[j]
            if denom > 0:
                rho = Sigma[i, j] / denom
            else:
                rho = 0.0
            rhos.append(rho)

    return sds, np.array(rhos)


def build_lambda_sparse(
    theta: np.ndarray,
    n_groups_list: list[int],
    re_structure: str,
    metadata: dict | None = None,
) -> sp.csc_matrix:
    """Build sparse block-diagonal Lambda matrix from theta.

    Lambda is constructed based on the random effects structure:
    - Intercept: Diagonal with theta[i] repeated
    - Diagonal: Block-diagonal with diagonal blocks
    - Slope: Block-diagonal with full Cholesky blocks
    - Nested/Crossed: Concatenated blocks per grouping factor

    Args:
        theta: Cholesky factor elements (lower triangle, column-major).
        n_groups_list: Number of groups per grouping factor.
            For simple models: [n_groups]
            For nested/crossed: [n_groups_factor1, n_groups_factor2, ...]
        re_structure: Random effects structure type.
            Options: "intercept", "slope", "diagonal", "nested", "crossed", "mixed"
        metadata: Optional metadata dict with structure information.
            May contain 're_structures_list' for mixed models.

    Returns:
        Sparse block-diagonal Lambda matrix, CSC format.

    Examples:
        >>> # Random intercept: (1|group)
        >>> theta = np.array([1.5])
        >>> Lambda = build_lambda_sparse(theta, [10], "intercept")
        >>> Lambda.shape
        (10, 10)

        >>> # Correlated slopes: (1+x|group)
        >>> theta = np.array([1.5, 0.3, 1.2])  # [L00, L10, L11]
        >>> Lambda = build_lambda_sparse(theta, [18], "slope")
        >>> Lambda.shape
        (36, 36)  # 18 groups × 2 RE per group

        >>> # Uncorrelated slopes: (1+x||group)
        >>> theta = np.array([1.5, 1.2])  # [L00, L11]
        >>> Lambda = build_lambda_sparse(theta, [18], "diagonal")
        >>> Lambda.shape
        (36, 36)

    Notes:
        - Returns CSC format for compatibility with CHOLMOD
        - Blocks are arranged per lme4's conventions
        - For diagonal structures, uses blocked layout (all intercepts, then slopes)
    """
    if metadata is None:
        metadata = {}

    if re_structure == "intercept":
        # Diagonal Lambda with repeated theta values
        if len(n_groups_list) == 1:
            # Simple intercept: (1|group)
            tau = theta[0]
            n_groups = n_groups_list[0]
            return sp.diags([tau], offsets=0, shape=(n_groups, n_groups), format="csc")
        else:
            # Multiple factors (crossed/nested intercepts)
            # theta = [tau1, tau2, ...]
            blocks = []
            for i, (tau, n_groups) in enumerate(zip(theta, n_groups_list)):
                block = sp.diags(
                    [tau], offsets=0, shape=(n_groups, n_groups), format="csc"
                )
                blocks.append(block)
            return sp.block_diag(blocks, format="csc")

    elif re_structure == "diagonal":
        # Uncorrelated slopes: blocked diagonal structure
        # theta = [L00, L11, L22, ...] for k RE per group
        # Layout: [group1_re1, group2_re1, ..., group1_re2, group2_re2, ...]
        n_groups = n_groups_list[0]
        k = len(theta)  # Number of RE per group
        q = n_groups * k

        # Build diagonal with blocked structure
        diag_values = []
        for tau in theta:
            diag_values.extend([tau] * n_groups)

        return sp.diags(diag_values, offsets=0, shape=(q, q), format="csc")

    elif re_structure == "slope":
        # Correlated slopes: block-diagonal with Cholesky blocks
        # theta = [L00, L10, L11, ...] (lower triangle)
        n_theta = len(theta)
        dim = int((-1 + np.sqrt(1 + 8 * n_theta)) / 2)

        if dim * (dim + 1) // 2 != n_theta:
            raise ValueError(
                f"Invalid theta length {n_theta} for slope structure. "
                f"Must be triangular number (3, 6, 10, ...)"
            )

        # Build Cholesky block
        L = theta_to_cholesky_block(theta, dim)

        # Repeat block for each group
        n_groups = n_groups_list[0]
        block_sparse = sp.csc_matrix(L)
        blocks = [block_sparse for _ in range(n_groups)]

        return sp.block_diag(blocks, format="csc")

    elif re_structure in ("nested", "crossed"):
        # Each grouping factor gets its own block
        # For intercepts: one diagonal block per factor
        # For slopes: multiple Cholesky blocks per factor
        re_structures_list = metadata.get("re_structures_list", None)

        if re_structures_list is None:
            # Default: assume all intercepts
            re_structures_list = ["intercept"] * len(n_groups_list)

        blocks = []
        theta_offset = 0

        for factor_idx, (n_groups, factor_structure) in enumerate(
            zip(n_groups_list, re_structures_list)
        ):
            if factor_structure == "intercept":
                # Single variance parameter
                tau = theta[theta_offset]
                block = sp.diags(
                    [tau], offsets=0, shape=(n_groups, n_groups), format="csc"
                )
                theta_offset += 1

            elif factor_structure == "slope":
                # Cholesky block (typically 2×2)
                # For now, assume 2D (intercept + slope)
                n_params = 3  # [L00, L10, L11]
                theta_factor = theta[theta_offset : theta_offset + n_params]
                L = theta_to_cholesky_block(theta_factor, 2)

                # Repeat for each group in this factor
                block_sparse = sp.csc_matrix(L)
                factor_blocks = [block_sparse for _ in range(n_groups)]
                block = sp.block_diag(factor_blocks, format="csc")
                theta_offset += n_params

            else:
                raise ValueError(f"Unknown factor structure: {factor_structure}")

            blocks.append(block)

        return sp.block_diag(blocks, format="csc")

    elif re_structure == "mixed":
        # Mixed structures require per-factor metadata
        re_structures_list = metadata.get("re_structures_list", None)
        if re_structures_list is None:
            raise ValueError(
                "Mixed structure requires 're_structures_list' in metadata"
            )

        blocks = []
        theta_offset = 0

        for factor_idx, (n_groups, factor_structure) in enumerate(
            zip(n_groups_list, re_structures_list)
        ):
            if factor_structure == "intercept":
                tau = theta[theta_offset]
                block = sp.diags(
                    [tau], offsets=0, shape=(n_groups, n_groups), format="csc"
                )
                theta_offset += 1

            elif factor_structure == "slope":
                n_params = 3  # Assume 2D slopes
                theta_factor = theta[theta_offset : theta_offset + n_params]
                L = theta_to_cholesky_block(theta_factor, 2)

                block_sparse = sp.csc_matrix(L)
                factor_blocks = [block_sparse for _ in range(n_groups)]
                block = sp.block_diag(factor_blocks, format="csc")
                theta_offset += n_params

            else:
                raise ValueError(f"Unknown factor structure: {factor_structure}")

            blocks.append(block)

        return sp.block_diag(blocks, format="csc")

    else:
        raise ValueError(f"Unknown re_structure: {re_structure}")


def build_pattern_template(
    Z: sp.csc_matrix,
    lambda_template: LambdaTemplate,
) -> PatternTemplate:
    """Build pattern template for cross-theta Cholesky caching.

    Computes the "maximal" sparsity patterns of ZL and S22 using theta=ones.
    These patterns are used to ensure consistent sparsity across all theta
    evaluations, even when theta components are zero (boundary conditions).

    This matches lme4's approach where the sparsity pattern is fixed at
    model initialization and never changes during optimization.

    Args:
        Z: Random effects design matrix (n, q), scipy sparse CSC.
        lambda_template: LambdaTemplate with pattern information.

    Returns:
        PatternTemplate with ZL and S22 patterns.

    Examples:
        >>> Z = sp.random(100, 50, density=0.1, format='csc')
        >>> lambda_tpl = build_lambda_template([50], "intercept")
        >>> pattern_tpl = build_pattern_template(Z, lambda_tpl)
        >>> # Now use pattern_tpl for pattern-preserved computations
    """
    if not sp.isspmatrix_csc(Z):
        Z = Z.tocsc()

    # Build Lambda with theta=ones to get maximal pattern
    n_theta = len(lambda_template.theta_to_data_map)
    theta_ones = np.ones(n_theta)
    Lambda_max = update_lambda_from_template(lambda_template, theta_ones)

    # Compute ZL pattern (maximal, with theta=ones)
    ZL_pattern = Z @ Lambda_max
    if not sp.isspmatrix_csc(ZL_pattern):
        ZL_pattern = ZL_pattern.tocsc()

    # Compute S22 pattern: ZL' @ ZL + I (without weights, pattern only)
    S22_pattern = ZL_pattern.T @ ZL_pattern
    S22_pattern = S22_pattern + sp.eye(S22_pattern.shape[0], format="csc")
    if not sp.isspmatrix_csc(S22_pattern):
        S22_pattern = S22_pattern.tocsc()

    return PatternTemplate(
        ZL_pattern=ZL_pattern,
        S22_pattern=S22_pattern,
        Z=Z,
        lambda_template=lambda_template,
    )


def compute_zl_preserve_pattern(
    Z: sp.csc_matrix,
    Lambda: sp.csc_matrix,
    ZL_pattern: sp.csc_matrix,
) -> sp.csc_matrix:
    """Compute Z @ Lambda while preserving the sparsity pattern of ZL_pattern.

    When theta has zeros (boundary), scipy's Z @ Lambda prunes explicit zeros,
    changing the sparsity pattern. This function ensures the result always has
    the same pattern as ZL_pattern by adding explicit zeros where needed.

    This is critical for CHOLMOD caching: the factorization reuses the symbolic
    analysis, which depends on having a consistent sparsity pattern.

    Args:
        Z: Random effects design matrix (n, q).
        Lambda: Current Lambda matrix (may have zeros from boundary theta).
        ZL_pattern: The "maximal" ZL pattern from build_pattern_template.

    Returns:
        ZL with ZL_pattern's sparsity structure but current values.

    Notes:
        - Pattern positions not in Z @ Lambda are filled with explicit zeros.
        - This matches lme4's updateLamtUt() which preserves pattern via manual iteration.
    """
    # Compute actual ZL values
    ZL_values = Z @ Lambda
    if not sp.isspmatrix_csc(ZL_values):
        ZL_values = ZL_values.tocsc()

    # If patterns match, we're done
    if ZL_values.nnz == ZL_pattern.nnz:
        return ZL_values

    # Create result with pattern's structure
    # Start with zeros in pattern's positions
    result_data = np.zeros(ZL_pattern.nnz, dtype=np.float64)

    # Copy values from ZL_values where they exist in pattern
    # We need to map from ZL_values positions to ZL_pattern positions
    n_cols = ZL_pattern.shape[1]

    for col in range(n_cols):
        # Pattern column range
        pat_start = ZL_pattern.indptr[col]
        pat_end = ZL_pattern.indptr[col + 1]
        pat_rows = ZL_pattern.indices[pat_start:pat_end]

        # Values column range
        val_start = ZL_values.indptr[col]
        val_end = ZL_values.indptr[col + 1]
        val_rows = ZL_values.indices[val_start:val_end]
        val_data = ZL_values.data[val_start:val_end]

        # For each row in pattern, find if it exists in values
        # Use searchsorted for efficiency (rows are sorted in CSC)
        for i, pat_row in enumerate(pat_rows):
            idx = np.searchsorted(val_rows, pat_row)
            if idx < len(val_rows) and val_rows[idx] == pat_row:
                result_data[pat_start + i] = val_data[idx]
            # else: stays 0 (explicit zero)

    result = sp.csc_matrix(
        (result_data, ZL_pattern.indices.copy(), ZL_pattern.indptr.copy()),
        shape=ZL_pattern.shape,
    )
    return result


def compute_s22_preserve_pattern(
    ZL: sp.csc_matrix,
    W: sp.csc_matrix,
    S22_pattern: sp.csc_matrix,
) -> sp.csc_matrix:
    """Compute ZL' @ W @ ZL + I while preserving S22_pattern's sparsity.

    Similar to compute_zl_preserve_pattern, this ensures S22 always has
    the same sparsity pattern regardless of theta values.

    Args:
        ZL: Pattern-preserved ZL matrix from compute_zl_preserve_pattern.
        W: Diagonal weight matrix.
        S22_pattern: The "maximal" S22 pattern from build_pattern_template.

    Returns:
        S22 with S22_pattern's sparsity structure but current values.
    """
    # Compute actual S22 values
    S22_values = ZL.T @ W @ ZL
    q = S22_values.shape[0]
    S22_values = S22_values + sp.eye(q, format="csc")
    if not sp.isspmatrix_csc(S22_values):
        S22_values = S22_values.tocsc()

    # If patterns match, we're done
    if S22_values.nnz == S22_pattern.nnz:
        return S22_values

    # Create result with pattern's structure
    result_data = np.zeros(S22_pattern.nnz, dtype=np.float64)

    n_cols = S22_pattern.shape[1]

    for col in range(n_cols):
        # Pattern column range
        pat_start = S22_pattern.indptr[col]
        pat_end = S22_pattern.indptr[col + 1]
        pat_rows = S22_pattern.indices[pat_start:pat_end]

        # Values column range
        val_start = S22_values.indptr[col]
        val_end = S22_values.indptr[col + 1]
        val_rows = S22_values.indices[val_start:val_end]
        val_data = S22_values.data[val_start:val_end]

        # For each row in pattern, find if it exists in values
        for i, pat_row in enumerate(pat_rows):
            idx = np.searchsorted(val_rows, pat_row)
            if idx < len(val_rows) and val_rows[idx] == pat_row:
                result_data[pat_start + i] = val_data[idx]
            # else: stays 0 (explicit zero for off-diag, but diag has +I)

    result = sp.csc_matrix(
        (result_data, S22_pattern.indices.copy(), S22_pattern.indptr.copy()),
        shape=S22_pattern.shape,
    )
    return result
