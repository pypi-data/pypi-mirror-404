"""Sparse linear algebra with backend abstraction.

This module provides a unified interface for sparse matrix factorization
and solving that works with both:
- CHOLMOD (sksparse): Fast specialized Cholesky for SPD matrices (JAX backend)
- splu (scipy): General sparse LU factorization (NumPy/Pyodide backend)

Key operations:
1. Factor a sparse SPD matrix A
2. Solve A @ x = b using the factorization
3. Compute log|A| (log-determinant)
4. Efficient re-factorization with cached symbolic analysis

Usage:
    from bossanova.ops.sparse_solver import sparse_cholesky, sparse_analyze

    # Full factorization (symbolic + numeric)
    factor = sparse_cholesky(A)
    x = factor.solve(b)
    logdet = factor.logdet()

    # Efficient caching for repeated factorizations (same sparsity pattern):
    # 1. Symbolic analysis once (expensive)
    factor = sparse_analyze(A)

    # 2. Numeric factorization (cheap, reuses symbolic)
    for A_new in matrices_with_same_pattern:
        factor.cholesky_inplace(A_new)
        x = factor.solve(b)

This caching pattern is critical for mixed model bootstrap performance,
achieving parity with R's lme4/bootMer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np
import scipy.sparse as sp

from bossanova._backend import get_backend

if TYPE_CHECKING:
    from typing import Any

__all__ = [
    "SparseFactorization",
    "CHOLMODFactorization",
    "SPLUFactorization",
    "sparse_cholesky",
    "sparse_analyze",
    "clear_sparse_solver_cache",
]


class SparseFactorization(ABC):
    """Abstract base class for sparse matrix factorization.

    Wraps either CHOLMOD or splu to provide a unified interface.

    Methods:
        solve: Solve A @ x = b
        logdet: Compute log-determinant log|A|
        cholesky_inplace: Update factorization with new values (same sparsity)
    """

    @abstractmethod
    def solve(self, b: np.ndarray) -> np.ndarray:
        """Solve A @ x = b.

        Args:
            b: Right-hand side vector or matrix.

        Returns:
            Solution x.
        """

    @abstractmethod
    def logdet(self) -> float:
        """Compute log-determinant of the factored matrix.

        Returns:
            log|A|
        """

    @abstractmethod
    def cholesky_inplace(self, A: sp.spmatrix) -> None:
        """Update factorization with new matrix values (same sparsity pattern).

        This enables efficient re-factorization when only the values change
        but the sparsity pattern remains constant. The expensive symbolic
        analysis is reused, only numeric factorization is performed.

        Args:
            A: Sparse SPD matrix with same sparsity pattern as original.

        Raises:
            ValueError: If sparsity pattern differs from original.
        """

    def __call__(self, b: np.ndarray) -> np.ndarray:
        """Solve A @ x = b (CHOLMOD-compatible calling convention).

        Args:
            b: Right-hand side.

        Returns:
            Solution x.
        """
        return self.solve(b)


class CHOLMODFactorization(SparseFactorization):
    """Wrapper around CHOLMOD sparse Cholesky factorization.

    CHOLMOD provides optimized sparse Cholesky factorization for
    symmetric positive definite matrices.

    Attributes:
        _factor: The underlying CHOLMOD Factor object.
    """

    __slots__ = ("_factor",)

    def __init__(self, factor: "Any"):
        """Initialize with CHOLMOD factor.

        Args:
            factor: sksparse.cholmod.Factor object.
        """
        self._factor = factor

    def solve(self, b: np.ndarray) -> np.ndarray:
        """Solve A @ x = b using Cholesky factor.

        Args:
            b: Right-hand side.

        Returns:
            Solution x.
        """
        return self._factor(b)

    def logdet(self) -> float:
        """Compute log-determinant via Cholesky.

        For SPD matrix A with Cholesky factor L (A = L @ L.T):
            log|A| = log|L|² = 2 * log|L| = 2 * sum(log(diag(L)))

        CHOLMOD's logdet() returns this directly.

        Returns:
            log|A|
        """
        return float(self._factor.logdet())

    def cholesky_inplace(self, A: sp.spmatrix) -> None:
        """Update factorization with new values (same sparsity pattern).

        Reuses the symbolic analysis (fill-reducing permutation) from the
        original factorization. Only performs numeric factorization with
        the new values. This is much faster than a full cholesky() call.

        Args:
            A: Sparse SPD matrix with same sparsity pattern as original.

        Raises:
            CholmodError: If sparsity pattern differs or matrix is not SPD.
        """
        if not sp.isspmatrix_csc(A):
            A = A.tocsc()
        self._factor.cholesky_inplace(A)


class SPLUFactorization(SparseFactorization):
    """Wrapper around scipy.sparse.linalg.splu factorization.

    splu provides general sparse LU factorization. For SPD matrices,
    it's less efficient than Cholesky but works in environments
    where CHOLMOD isn't available (e.g., Pyodide).

    Attributes:
        _lu: The underlying SuperLU object from splu.
        _n: Matrix dimension.
    """

    __slots__ = ("_lu", "_n")

    def __init__(self, lu: "Any", n: int):
        """Initialize with splu result.

        Args:
            lu: scipy.sparse.linalg.SuperLU object.
            n: Matrix dimension.
        """
        self._lu = lu
        self._n = n

    def solve(self, b: np.ndarray) -> np.ndarray:
        """Solve A @ x = b using LU factorization.

        Args:
            b: Right-hand side (1D or 2D array).

        Returns:
            Solution x.
        """
        # Ensure b is NumPy (not JAX) for splu compatibility
        return self._lu.solve(np.asarray(b))

    def logdet(self) -> float:
        """Compute log-determinant from LU decomposition.

        For LU factorization with pivoting: A = P @ L @ U
        where P is permutation, L is lower triangular, U is upper triangular.

        For SPD matrices, |A| > 0 so:
            log|A| = log|L| + log|U|

        Since L has unit diagonal: log|L| = 0
        So: log|A| = sum(log(|diag(U)|))

        Note: For general (non-SPD) matrices, the sign from permutation P
        and negative diagonal elements would need to be tracked. For SPD
        matrices used in mixed models, this is not needed.

        Returns:
            log|A| (assumes A is SPD so determinant is positive)
        """
        diag_U = self._lu.U.diagonal()

        # For SPD matrices, all diagonal elements should be positive
        # Use abs() for numerical robustness (small negative values from roundoff)
        return float(np.sum(np.log(np.abs(diag_U))))

    def cholesky_inplace(self, A: sp.spmatrix) -> None:
        """Update factorization with new values.

        Note: scipy.sparse.linalg.splu does not support in-place updates,
        so this performs a full re-factorization. No performance benefit
        in the NumPy/Pyodide backend, but provides API consistency.

        Args:
            A: Sparse SPD matrix (sparsity pattern should match original).
        """
        from scipy.sparse.linalg import splu

        if not sp.isspmatrix_csc(A):
            A = A.tocsc()
        # Cast to csc_matrix for type checker (tocsc() returns csc_matrix)
        A_csc: sp.csc_matrix = A  # type: ignore[assignment]

        # Ensure data arrays are NumPy (not JAX)
        A_numpy = sp.csc_matrix(
            (np.asarray(A_csc.data), A_csc.indices, A_csc.indptr), shape=A_csc.shape
        )
        self._lu = splu(A_numpy)


def sparse_cholesky(A: sp.spmatrix) -> SparseFactorization:
    """Factor a sparse symmetric positive definite matrix.

    Uses CHOLMOD if available (fast specialized Cholesky) or
    splu as fallback (general LU, works in Pyodide and when sksparse
    is not installed).

    Args:
        A: Sparse SPD matrix in CSC format. Will be converted if needed.

    Returns:
        SparseFactorization object with solve() and logdet() methods.

    Examples:
        >>> import scipy.sparse as sp
        >>> A = sp.eye(100, format='csc') + sp.random(100, 100, density=0.1)
        >>> A = A @ A.T  # Make SPD
        >>> factor = sparse_cholesky(A)
        >>> x = factor.solve(b)
        >>> logdet = factor.logdet()
    """
    # Ensure CSC format (required by both CHOLMOD and splu)
    if not sp.isspmatrix_csc(A):
        A = A.tocsc()
    # Cast to csc_matrix for type checker (tocsc() returns csc_matrix)
    A_csc: sp.csc_matrix = A  # type: ignore[assignment]

    backend = get_backend()

    if backend == "jax":
        # Try CHOLMOD for JAX backend (faster for SPD matrices)
        try:
            from sksparse.cholmod import cholesky

            factor = cholesky(A_csc)
            return CHOLMODFactorization(factor)
        except ImportError:
            # Fall back to splu if sksparse not installed
            pass

    # Use splu for NumPy backend or as fallback
    from scipy.sparse.linalg import splu

    # Ensure data arrays are NumPy (not JAX) for splu compatibility
    A_numpy = sp.csc_matrix(
        (np.asarray(A_csc.data), A_csc.indices, A_csc.indptr), shape=A_csc.shape
    )
    lu = splu(A_numpy)
    return SPLUFactorization(lu, A_csc.shape[0])


def sparse_analyze(A: sp.spmatrix) -> SparseFactorization:
    """Perform symbolic Cholesky analysis only (no numeric factorization).

    This computes the fill-reducing permutation based on the sparsity pattern
    of A, but does NOT perform the actual numeric factorization. Use this to
    pre-compute the symbolic analysis, then call factor.cholesky_inplace(A)
    for efficient numeric factorization.

    This is the key to achieving parity with R's lme4/bootMer performance:
    - Symbolic analysis: O(nnz) to O(nnz^1.5), depends only on sparsity pattern
    - Numeric factorization: O(nnz), uses the values

    For mixed model bootstrap, the sparsity pattern is constant across all
    iterations, so symbolic analysis needs to be done only once.

    Args:
        A: Sparse SPD matrix in CSC format. Only the sparsity pattern is used;
           the actual values are ignored.

    Returns:
        SparseFactorization object ready for cholesky_inplace() calls.

    Examples:
        >>> # Pre-compute symbolic analysis once
        >>> factor = sparse_analyze(A)
        >>>
        >>> # Efficient numeric factorization (reuses symbolic)
        >>> for A_new in matrices_with_same_pattern:
        ...     factor.cholesky_inplace(A_new)
        ...     x = factor.solve(b)

    Note:
        For the NumPy/Pyodide backend (splu), this falls back to full
        factorization since splu doesn't support separate symbolic analysis.
        The API is consistent, but there's no performance benefit.
    """
    # Ensure CSC format
    if not sp.isspmatrix_csc(A):
        A = A.tocsc()
    # Cast to csc_matrix for type checker (tocsc() returns csc_matrix)
    A_csc: sp.csc_matrix = A  # type: ignore[assignment]

    backend = get_backend()

    if backend == "jax":
        # Try CHOLMOD analyze (symbolic-only)
        try:
            from sksparse.cholmod import analyze

            factor = analyze(A_csc)
            return CHOLMODFactorization(factor)
        except ImportError:
            # Fall back to splu if sksparse not installed
            pass

    # Use splu for NumPy backend or as fallback
    # Note: splu doesn't support separate symbolic analysis, so we do full factorization
    from scipy.sparse.linalg import splu

    A_numpy = sp.csc_matrix(
        (np.asarray(A_csc.data), A_csc.indices, A_csc.indptr), shape=A_csc.shape
    )
    lu = splu(A_numpy)
    return SPLUFactorization(lu, A_csc.shape[0])


def clear_sparse_solver_cache() -> None:
    """Clear any cached sparse solver objects.

    Currently a no-op, but provided for API consistency with other
    ops modules that have caching.
    """
    pass
