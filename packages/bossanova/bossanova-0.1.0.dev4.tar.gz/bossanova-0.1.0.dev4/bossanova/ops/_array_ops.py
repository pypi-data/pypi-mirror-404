"""Array operations protocol for backend abstraction.

This module defines the interface that both NumPy and JAX backends must
implement. Using a Protocol allows for static type checking while maintaining
flexibility in implementation.
"""

from typing import Any, Callable, Protocol, TypeVar

# Generic array type - could be np.ndarray or jax.Array
Array = TypeVar("Array")


class ArrayOps(Protocol):
    """Protocol for array operations across backends.

    This defines the interface that both NumPyBackend and JAXBackend must
    implement. All linear algebra and array manipulation needed by bossanova
    should go through this interface.

    Attributes:
        np: The numpy-like module (numpy or jax.numpy).
    """

    np: Any  # numpy or jax.numpy module

    # =========================================================================
    # Array Creation
    # =========================================================================

    def asarray(self, x: Any, dtype: Any = None) -> Array:
        """Convert input to array.

        Args:
            x: Input data (list, tuple, ndarray, etc.).
            dtype: Desired data type.

        Returns:
            Array of the appropriate backend type.
        """
        ...

    def zeros(self, shape: tuple[int, ...], dtype: Any = None) -> Array:
        """Create array of zeros.

        Args:
            shape: Shape of the array.
            dtype: Data type (defaults to float64).

        Returns:
            Array of zeros.
        """
        ...

    def ones(self, shape: tuple[int, ...], dtype: Any = None) -> Array:
        """Create array of ones.

        Args:
            shape: Shape of the array.
            dtype: Data type (defaults to float64).

        Returns:
            Array of ones.
        """
        ...

    def eye(self, n: int, dtype: Any = None) -> Array:
        """Create identity matrix.

        Args:
            n: Size of the identity matrix.
            dtype: Data type (defaults to float64).

        Returns:
            Identity matrix of shape (n, n).
        """
        ...

    def arange(self, start: int, stop: int | None = None, step: int = 1) -> Array:
        """Create array with evenly spaced values.

        Args:
            start: Start value (or stop if stop is None).
            stop: Stop value (exclusive).
            step: Step size.

        Returns:
            Array of evenly spaced values.
        """
        ...

    def full(
        self, shape: tuple[int, ...], fill_value: float, dtype: Any = None
    ) -> Array:
        """Create array filled with a scalar value.

        Args:
            shape: Shape of the array.
            fill_value: Value to fill the array with.
            dtype: Data type (defaults to float64).

        Returns:
            Array filled with fill_value.
        """
        ...

    # =========================================================================
    # Linear Algebra
    # =========================================================================

    def cholesky(self, a: Array) -> Array:
        """Cholesky decomposition.

        Args:
            a: Symmetric positive-definite matrix.

        Returns:
            Lower triangular Cholesky factor L such that a = L @ L.T.
        """
        ...

    def solve(self, a: Array, b: Array) -> Array:
        """Solve linear system a @ x = b.

        Args:
            a: Coefficient matrix.
            b: Right-hand side.

        Returns:
            Solution x.
        """
        ...

    def solve_triangular(self, a: Array, b: Array, lower: bool = False) -> Array:
        """Solve triangular linear system.

        Args:
            a: Triangular coefficient matrix.
            b: Right-hand side.
            lower: If True, a is lower triangular.

        Returns:
            Solution x.
        """
        ...

    def qr(self, a: Array) -> tuple[Array, Array]:
        """QR decomposition.

        Args:
            a: Matrix to decompose.

        Returns:
            Tuple (Q, R) where Q is orthogonal and R is upper triangular.
        """
        ...

    def svd(self, a: Array, full_matrices: bool = True) -> tuple[Array, Array, Array]:
        """Singular value decomposition.

        Args:
            a: Matrix to decompose.
            full_matrices: If True, return full U and Vt matrices.

        Returns:
            Tuple (U, s, Vt) such that a = U @ diag(s) @ Vt.
        """
        ...

    def lstsq(self, a: Array, b: Array) -> tuple[Array, Any, Any, Any]:
        """Least squares solution.

        Args:
            a: Coefficient matrix.
            b: Right-hand side.

        Returns:
            Tuple (solution, residuals, rank, singular_values).
        """
        ...

    def inv(self, a: Array) -> Array:
        """Matrix inverse.

        Args:
            a: Square matrix.

        Returns:
            Inverse of a.
        """
        ...

    def det(self, a: Array) -> Array:
        """Matrix determinant.

        Args:
            a: Square matrix.

        Returns:
            Determinant of a.
        """
        ...

    def eigh(self, a: Array) -> tuple[Array, Array]:
        """Eigendecomposition of symmetric matrix.

        Args:
            a: Symmetric matrix.

        Returns:
            Tuple (eigenvalues, eigenvectors).
        """
        ...

    def norm(self, a: Array, ord: Any = None, axis: int | None = None) -> Array:
        """Matrix or vector norm.

        Args:
            a: Input array.
            ord: Order of the norm.
            axis: Axis along which to compute.

        Returns:
            Norm of the array.
        """
        ...

    # =========================================================================
    # Transforms (JIT, vmap)
    # =========================================================================

    def jit(self, fn: Callable) -> Callable:
        """JIT-compile a function.

        For NumPy backend, this is a no-op (returns the function unchanged).
        For JAX backend, this wraps the function with jax.jit.

        Args:
            fn: Function to compile.

        Returns:
            JIT-compiled function (or original for NumPy).
        """
        ...

    def vmap(self, fn: Callable, in_axes: int | tuple[int, ...] = 0) -> Callable:
        """Vectorize a function over a batch dimension.

        For NumPy backend, this uses a Python loop with np.stack.
        For JAX backend, this uses jax.vmap.

        Args:
            fn: Function to vectorize.
            in_axes: Axis to map over for each input.

        Returns:
            Vectorized function.
        """
        ...
