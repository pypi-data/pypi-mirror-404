"""NumPy backend implementation.

This module provides the NumPy/SciPy implementation of array operations
for bossanova. It implements the ArrayOps protocol.
"""

from typing import Any, Callable

import numpy as np
import scipy.linalg as la


class NumPyBackend:
    """NumPy/SciPy implementation of array operations.

    This backend uses NumPy for array operations and SciPy for linear algebra.
    JIT and vmap are no-ops (or simple loop-based implementations).

    Attributes:
        np: The numpy module.
    """

    def __init__(self) -> None:
        """Initialize the NumPy backend."""
        self.np = np

    # =========================================================================
    # Array Creation
    # =========================================================================

    def asarray(self, x: Any, dtype: Any = None) -> np.ndarray:
        """Convert input to numpy array."""
        return np.asarray(x, dtype=dtype)

    def zeros(self, shape: tuple[int, ...], dtype: Any = None) -> np.ndarray:
        """Create array of zeros."""
        return np.zeros(shape, dtype=dtype or np.float64)

    def ones(self, shape: tuple[int, ...], dtype: Any = None) -> np.ndarray:
        """Create array of ones."""
        return np.ones(shape, dtype=dtype or np.float64)

    def eye(self, n: int, dtype: Any = None) -> np.ndarray:
        """Create identity matrix."""
        return np.eye(n, dtype=dtype or np.float64)

    def arange(self, start: int, stop: int | None = None, step: int = 1) -> np.ndarray:
        """Create array with evenly spaced values."""
        if stop is None:
            return np.arange(start)
        return np.arange(start, stop, step)

    def full(
        self, shape: tuple[int, ...], fill_value: float, dtype: Any = None
    ) -> np.ndarray:
        """Create array filled with a scalar value."""
        return np.full(shape, fill_value, dtype=dtype or np.float64)

    # =========================================================================
    # Linear Algebra
    # =========================================================================

    def cholesky(self, a: np.ndarray) -> np.ndarray:
        """Cholesky decomposition (lower triangular)."""
        return la.cholesky(a, lower=True)

    def solve(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Solve linear system a @ x = b."""
        return la.solve(a, b)

    def solve_triangular(
        self, a: np.ndarray, b: np.ndarray, lower: bool = False
    ) -> np.ndarray:
        """Solve triangular linear system."""
        return la.solve_triangular(a, b, lower=lower)

    def qr(self, a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """QR decomposition (economic mode)."""
        return la.qr(a, mode="economic")

    def svd(
        self, a: np.ndarray, full_matrices: bool = True
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Singular value decomposition."""
        return la.svd(a, full_matrices=full_matrices)

    def lstsq(
        self, a: np.ndarray, b: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, int, np.ndarray]:
        """Least squares solution."""
        result = la.lstsq(a, b)
        return result  # type: ignore[return-value]

    def inv(self, a: np.ndarray) -> np.ndarray:
        """Matrix inverse."""
        return la.inv(a)

    def det(self, a: np.ndarray) -> np.floating[Any]:
        """Matrix determinant."""
        return la.det(a)

    def eigh(self, a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Eigendecomposition of symmetric matrix."""
        return la.eigh(a)

    def norm(
        self, a: np.ndarray, ord: Any = None, axis: int | None = None
    ) -> np.ndarray:
        """Matrix or vector norm."""
        return la.norm(a, ord=ord, axis=axis)

    # =========================================================================
    # Transforms (no-ops or simple implementations for NumPy)
    # =========================================================================

    def jit(self, fn: Callable) -> Callable:
        """No-op: NumPy doesn't have JIT compilation."""
        return fn

    def vmap(self, fn: Callable, in_axes: int | tuple[int, ...] = 0) -> Callable:
        """Vectorize via Python loop.

        This is a simple implementation that loops over the batch dimension
        and stacks results. It's slower than JAX's vmap but provides the
        same interface.

        Args:
            fn: Function to vectorize.
            in_axes: Axis to map over (only supports 0 or tuple of 0s/Nones).

        Returns:
            Vectorized function.
        """

        def vmapped(*args: np.ndarray) -> np.ndarray:
            # Normalize in_axes to tuple
            if isinstance(in_axes, int):
                axes = (in_axes,) * len(args)
            else:
                axes = in_axes

            # Find batch size from first mapped argument
            batch_size = None
            for arg, axis in zip(args, axes):
                if axis is not None and hasattr(arg, "shape"):
                    batch_size = arg.shape[axis]
                    break

            if batch_size is None:
                # No batched arguments, just call the function
                return fn(*args)

            # Loop over batch dimension
            results = []
            for i in range(batch_size):
                sliced_args = []
                for arg, axis in zip(args, axes):
                    if axis is None:
                        sliced_args.append(arg)
                    elif axis == 0:
                        sliced_args.append(arg[i])
                    else:
                        # General axis slicing
                        sliced_args.append(np.take(arg, i, axis=axis))
                results.append(fn(*sliced_args))

            return np.stack(results, axis=0)

        return vmapped
