"""Backend accessor for array operations.

This module provides the get_ops() function that returns the appropriate
backend instance based on the current backend setting.
"""

from typing import TYPE_CHECKING

from bossanova._backend import get_backend

if TYPE_CHECKING:
    from bossanova.ops._array_ops import ArrayOps

# Cache for backend instances (created once per backend)
_ops_cache: dict[str, "ArrayOps"] = {}


def get_ops() -> "ArrayOps":
    """Get array operations for the current backend.

    Returns the appropriate backend instance (NumPyBackend or JAXBackend)
    based on the current backend setting. The instance is cached so that
    repeated calls return the same object.

    Returns:
        ArrayOps instance for the current backend.

    Examples:
        >>> from bossanova.ops import get_ops
        >>> ops = get_ops()
        >>> X = ops.asarray([[1, 2], [3, 4]])
        >>> L = ops.cholesky(X @ X.T)
    """
    backend = get_backend()

    if backend not in _ops_cache:
        if backend == "jax":
            from bossanova.ops._jax_backend import JAXBackend

            _ops_cache[backend] = JAXBackend()
        else:
            from bossanova.ops._numpy_backend import NumPyBackend

            _ops_cache[backend] = NumPyBackend()

    return _ops_cache[backend]


def clear_ops_cache() -> None:
    """Clear the backend operations cache.

    This is primarily for testing purposes. Clears the cached backend
    instances so that the next call to get_ops() creates a fresh instance.

    Warning:
        This should only be used in tests. Using it in production code
        can lead to inconsistent behavior.
    """
    global _ops_cache
    _ops_cache = {}
