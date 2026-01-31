"""Unified RNG abstraction for JAX and NumPy backends.

This module provides a unified interface for random number generation that works
with both JAX's functional RNG (explicit keys) and NumPy's stateful RNG.

Key design goals:
1. JAX compatibility: Preserve functional key-splitting semantics
2. NumPy compatibility: Simulate key-splitting with spawned generators
3. JIT safety: JAX operations remain JIT-compatible
4. Consistent API: Same interface regardless of backend

Usage:
    # From seed (recommended for reproducibility)
    rng = RNG.from_seed(42)

    # Split for parallel operations
    keys = rng.split(n=10)  # Returns list of 10 RNG objects

    # Or split into two (common pattern)
    rng1, rng2 = rng.split()

    # Generate random values (use .key for JAX backend)
    values = jax.random.normal(rng.key, shape=(100,))  # JAX
    values = rng.normal(shape=(100,))  # Backend-agnostic helper
"""

from __future__ import annotations

from typing import Any

import numpy as np

from bossanova._backend import get_backend

__all__ = [
    "RNG",
    "create_rng",
    "get_jax_key",
]


class RNG:
    """Unified RNG wrapper for JAX and NumPy backends.

    This class wraps either a JAX PRNGKey or a NumPy Generator, providing
    a consistent interface for random number generation across backends.

    The key insight is that JAX uses functional RNG (immutable keys that
    are split to produce new keys), while NumPy uses stateful RNG (mutable
    generators). This class bridges the gap by:

    - JAX backend: Wraps a PRNGKey, split() returns new RNG objects with split keys
    - NumPy backend: Wraps a Generator, split() returns new RNG objects with
      spawned generators (using SeedSequence.spawn)

    Attributes:
        key: The underlying random state. For JAX backend, this is a PRNGKey
            that can be passed directly to jax.random functions. For NumPy
            backend, this is a Generator (but prefer using the helper methods).

    Examples:
        >>> rng = RNG.from_seed(42)
        >>> rng1, rng2 = rng.split()
        >>> values = rng1.normal(shape=(100,))
    """

    __slots__ = ("_key", "_backend")

    def __init__(self, key: Any, backend: str | None = None):
        """Initialize RNG with an existing key/generator.

        Args:
            key: JAX PRNGKey or NumPy Generator.
            backend: Backend name ("jax" or "numpy"). If None, auto-detects.
        """
        self._key = key
        self._backend = backend or get_backend()

    @classmethod
    def from_seed(cls, seed: int | None = None) -> RNG:
        """Create RNG from integer seed.

        Args:
            seed: Integer seed for reproducibility. If None, uses random seed.

        Returns:
            New RNG instance.

        Examples:
            >>> rng = RNG.from_seed(42)
            >>> rng.split(n=3)  # Returns list of 3 RNGs
        """
        backend = get_backend()

        if seed is None:
            seed = int(np.random.default_rng().integers(0, 2**31))

        if backend == "jax":
            import jax.random as jr

            key = jr.PRNGKey(seed)
        else:
            # NumPy: use Generator with SeedSequence for proper spawning
            key = np.random.default_rng(seed)

        return cls(key, backend)

    @property
    def key(self) -> Any:
        """Get the underlying key/generator.

        For JAX backend, returns a PRNGKey suitable for jax.random functions.
        For NumPy backend, returns a Generator.

        Examples:
            >>> rng = RNG.from_seed(42)
            >>> # JAX usage
            >>> values = jax.random.normal(rng.key, shape=(100,))
        """
        return self._key

    def split(self, n: int = 2) -> list[RNG]:
        """Split RNG into n independent RNGs.

        This is the key operation for parallel random number generation.
        Each returned RNG is independent and can be used in parallel.

        Args:
            n: Number of RNGs to create (default: 2).

        Returns:
            List of n independent RNG objects.

        Examples:
            >>> rng = RNG.from_seed(42)
            >>> rng1, rng2 = rng.split()
            >>> keys = rng.split(n=10)  # For parallel operations
        """
        if self._backend == "jax":
            import jax.random as jr

            keys = jr.split(self._key, n)
            return [RNG(keys[i], self._backend) for i in range(n)]
        else:
            # NumPy: spawn child generators
            # Use bit_generator.spawn for proper independence
            children = self._key.bit_generator.spawn(n)
            return [RNG(np.random.Generator(bg), self._backend) for bg in children]

    def split_one(self) -> tuple[RNG, RNG]:
        """Split into two RNGs, returning (new_self, child).

        Common pattern: advance self and get one child for use.

        Returns:
            Tuple of (new_self, child) RNGs.

        Examples:
            >>> rng = RNG.from_seed(42)
            >>> rng, child = rng.split_one()
            >>> values = child.normal(shape=(100,))
        """
        rngs = self.split(2)
        return rngs[0], rngs[1]

    # =========================================================================
    # Backend-agnostic random value generation
    # =========================================================================

    def normal(self, shape: tuple[int, ...]) -> Any:
        """Generate standard normal random values.

        Args:
            shape: Shape of output array.

        Returns:
            Array of shape `shape` with N(0, 1) values.
        """
        if self._backend == "jax":
            import jax.random as jr

            return jr.normal(self._key, shape=shape)
        else:
            return self._key.standard_normal(shape)

    def uniform(
        self, shape: tuple[int, ...], minval: float = 0.0, maxval: float = 1.0
    ) -> Any:
        """Generate uniform random values.

        Args:
            shape: Shape of output array.
            minval: Minimum value (inclusive).
            maxval: Maximum value (exclusive).

        Returns:
            Array of shape `shape` with U(minval, maxval) values.
        """
        if self._backend == "jax":
            import jax.random as jr

            return jr.uniform(self._key, shape=shape, minval=minval, maxval=maxval)
        else:
            return self._key.uniform(minval, maxval, shape)

    def permutation(self, n: int) -> Any:
        """Generate random permutation of [0, 1, ..., n-1].

        Args:
            n: Length of permutation.

        Returns:
            Array of shape (n,) containing a random permutation.
        """
        if self._backend == "jax":
            import jax.random as jr

            return jr.permutation(self._key, n)
        else:
            return self._key.permutation(n)

    def choice(self, n: int, shape: tuple[int, ...], replace: bool = True) -> Any:
        """Random choice from [0, 1, ..., n-1].

        Args:
            n: Upper bound (exclusive) for choices.
            shape: Shape of output array.
            replace: Whether to sample with replacement.

        Returns:
            Array of shape `shape` with random integers in [0, n).
        """
        if self._backend == "jax":
            import jax.random as jr

            return jr.choice(self._key, n, shape=shape, replace=replace)
        else:
            return self._key.choice(n, size=shape, replace=replace)

    def bernoulli(self, p: float, shape: tuple[int, ...]) -> Any:
        """Generate Bernoulli random values.

        Args:
            p: Probability of True/1.
            shape: Shape of output array.

        Returns:
            Boolean array of shape `shape` (JAX) or int array 0/1 (NumPy).
        """
        if self._backend == "jax":
            import jax.random as jr

            return jr.bernoulli(self._key, p=p, shape=shape)
        else:
            return self._key.binomial(1, p, size=shape)

    def poisson(self, lam: Any) -> Any:
        """Generate Poisson random values.

        Args:
            lam: Rate parameter (can be scalar or array).

        Returns:
            Array of same shape as `lam` with Poisson samples.
        """
        if self._backend == "jax":
            import jax.random as jr

            return jr.poisson(self._key, lam)
        else:
            return self._key.poisson(lam)


# =============================================================================
# Convenience functions for common patterns
# =============================================================================


def create_rng(seed: int | None = None) -> RNG:
    """Create RNG from seed (convenience function).

    Args:
        seed: Integer seed. If None, uses random seed.

    Returns:
        New RNG instance.

    Examples:
        >>> rng = create_rng(42)
        >>> values = rng.normal(shape=(100,))
    """
    return RNG.from_seed(seed)


def get_jax_key(rng: RNG | int | None) -> Any:
    """Get JAX PRNGKey from RNG, seed, or None.

    Convenience function for code that needs a raw JAX key but wants
    to accept flexible inputs.

    Args:
        rng: RNG object, integer seed, or None.

    Returns:
        JAX PRNGKey.

    Raises:
        RuntimeError: If called with NumPy backend.

    Examples:
        >>> key = get_jax_key(42)  # From seed
        >>> key = get_jax_key(rng)  # From RNG object
    """
    import jax.random as jr

    if rng is None:
        seed = int(np.random.default_rng().integers(0, 2**31))
        return jr.PRNGKey(seed)
    elif isinstance(rng, int):
        return jr.PRNGKey(rng)
    elif isinstance(rng, RNG):
        if rng._backend != "jax":
            raise RuntimeError("get_jax_key requires JAX backend")
        return rng.key
    else:
        # Assume it's already a PRNGKey
        return rng
