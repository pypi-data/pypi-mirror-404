"""JAX backend implementation.

This module provides the JAX implementation of array operations for bossanova.
It implements the ArrayOps protocol.

Note: JAX x64 config is centralized here. This is the ONLY place where
jax_enable_x64 should be set. The config is applied when this module is
first imported (via get_ops() when JAX backend is selected).
"""

from typing import Any, Callable

import jax
import jax.numpy as jnp
from jax.scipy.linalg import cho_solve, solve_triangular

# Enable float64 precision - this is the authoritative location for this config
jax.config.update("jax_enable_x64", True)


class JAXBackend:
    """JAX implementation of array operations.

    This backend uses JAX for array operations and provides JIT compilation
    and vectorization via vmap.

    Attributes:
        np: The jax.numpy module.
        jax: The jax module (for jit, vmap, etc.).
    """

    def __init__(self) -> None:
        """Initialize the JAX backend."""
        self.np = jnp
        self.jax = jax

    # =========================================================================
    # Array Creation
    # =========================================================================

    def asarray(self, x: Any, dtype: Any = None) -> jax.Array:
        """Convert input to JAX array."""
        return jnp.asarray(x, dtype=dtype)

    def zeros(self, shape: tuple[int, ...], dtype: Any = None) -> jax.Array:
        """Create array of zeros."""
        return jnp.zeros(shape, dtype=dtype or jnp.float64)

    def ones(self, shape: tuple[int, ...], dtype: Any = None) -> jax.Array:
        """Create array of ones."""
        return jnp.ones(shape, dtype=dtype or jnp.float64)

    def eye(self, n: int, dtype: Any = None) -> jax.Array:
        """Create identity matrix."""
        return jnp.eye(n, dtype=dtype or jnp.float64)

    def arange(self, start: int, stop: int | None = None, step: int = 1) -> jax.Array:
        """Create array with evenly spaced values."""
        if stop is None:
            return jnp.arange(start)
        return jnp.arange(start, stop, step)

    def full(
        self, shape: tuple[int, ...], fill_value: float, dtype: Any = None
    ) -> jax.Array:
        """Create array filled with a scalar value."""
        return jnp.full(shape, fill_value, dtype=dtype or jnp.float64)

    # =========================================================================
    # Linear Algebra
    # =========================================================================

    def cholesky(self, a: jax.Array) -> jax.Array:
        """Cholesky decomposition (lower triangular)."""
        return jnp.linalg.cholesky(a)

    def solve(self, a: jax.Array, b: jax.Array) -> jax.Array:
        """Solve linear system a @ x = b."""
        return jnp.linalg.solve(a, b)

    def solve_triangular(
        self, a: jax.Array, b: jax.Array, lower: bool = False
    ) -> jax.Array:
        """Solve triangular linear system."""
        return solve_triangular(a, b, lower=lower)

    def qr(self, a: jax.Array) -> tuple[jax.Array, jax.Array]:
        """QR decomposition."""
        return jnp.linalg.qr(a)

    def svd(
        self, a: jax.Array, full_matrices: bool = True
    ) -> tuple[jax.Array, jax.Array, jax.Array]:
        """Singular value decomposition."""
        return jnp.linalg.svd(a, full_matrices=full_matrices)

    def lstsq(
        self, a: jax.Array, b: jax.Array
    ) -> tuple[jax.Array, jax.Array, jax.Array, jax.Array]:
        """Least squares solution."""
        return jnp.linalg.lstsq(a, b)

    def inv(self, a: jax.Array) -> jax.Array:
        """Matrix inverse."""
        return jnp.linalg.inv(a)

    def det(self, a: jax.Array) -> jax.Array:
        """Matrix determinant."""
        return jnp.linalg.det(a)

    def eigh(self, a: jax.Array) -> tuple[jax.Array, jax.Array]:
        """Eigendecomposition of symmetric matrix."""
        return jnp.linalg.eigh(a)

    def norm(self, a: jax.Array, ord: Any = None, axis: int | None = None) -> jax.Array:
        """Matrix or vector norm."""
        return jnp.linalg.norm(a, ord=ord, axis=axis)

    # =========================================================================
    # Transforms
    # =========================================================================

    def jit(self, fn: Callable) -> Callable:
        """JIT-compile a function using JAX."""
        return jax.jit(fn)

    def vmap(self, fn: Callable, in_axes: int | tuple[int, ...] = 0) -> Callable:
        """Vectorize a function over a batch dimension using JAX."""
        return jax.vmap(fn, in_axes=in_axes)

    # =========================================================================
    # JAX-specific utilities (for advanced use)
    # =========================================================================

    def cho_solve(self, c_and_lower: tuple[jax.Array, bool], b: jax.Array) -> jax.Array:
        """Solve using Cholesky factor.

        Args:
            c_and_lower: Tuple of (cholesky_factor, is_lower).
            b: Right-hand side.

        Returns:
            Solution x to A @ x = b where A = L @ L.T.
        """
        return cho_solve(c_and_lower, b)

    def grad(self, fn: Callable, argnums: int = 0) -> Callable:
        """Compute gradient of a function.

        Args:
            fn: Function to differentiate.
            argnums: Which argument to differentiate with respect to.

        Returns:
            Function that computes the gradient.
        """
        return jax.grad(fn, argnums=argnums)

    def value_and_grad(self, fn: Callable, argnums: int = 0) -> Callable:
        """Compute value and gradient of a function.

        Args:
            fn: Function to differentiate.
            argnums: Which argument to differentiate with respect to.

        Returns:
            Function that returns (value, gradient).
        """
        return jax.value_and_grad(fn, argnums=argnums)
