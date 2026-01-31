"""Backend detection and switching for bossanova.

This module provides the infrastructure for switching between JAX and NumPy
backends at runtime. The backend is auto-detected on first use but can be
explicitly set before any model fitting occurs.

Examples:
    >>> import bossanova
    >>> bossanova.get_backend()
    'jax'
    >>> bossanova.set_backend("numpy")
    >>> bossanova.get_backend()
    'numpy'
"""

import sys
from contextlib import contextmanager
from typing import Literal

BackendName = Literal["jax", "numpy"]

# Global state
_backend: BackendName | None = None
_backend_locked: bool = False


def _detect_backend() -> BackendName:
    """Auto-detect the best available backend.

    Detection order:
    1. If running in Pyodide (emscripten), use numpy (JAX not available)
    2. Try to import JAX - if successful, use jax
    3. Fall back to numpy

    Returns:
        The detected backend name.
    """
    # Pyodide detection
    if sys.platform == "emscripten":
        return "numpy"

    # Try JAX
    try:
        import jax

        # Enable float64 precision - must be done before any array creation
        jax.config.update("jax_enable_x64", True)
        return "jax"
    except ImportError:
        return "numpy"


def get_backend() -> BackendName:
    """Get the current backend name.

    If no backend has been explicitly set, auto-detects the best available
    backend on first call.

    Returns:
        The current backend name ('jax' or 'numpy').

    Examples:
        >>> import bossanova
        >>> bossanova.get_backend()
        'jax'
    """
    global _backend
    if _backend is None:
        _backend = _detect_backend()
    return _backend


def set_backend(name: BackendName) -> None:
    """Set the backend to use for computations.

    Must be called before any model fitting occurs. Once a model has been
    fitted, the backend is locked and cannot be changed.

    Args:
        name: Backend name, either 'jax' or 'numpy'.

    Raises:
        RuntimeError: If called after a model has been fitted.
        ValueError: If name is not 'jax' or 'numpy'.
        ImportError: If 'jax' is requested but JAX is not installed.

    Examples:
        >>> import bossanova
        >>> bossanova.set_backend("numpy")
        >>> bossanova.get_backend()
        'numpy'
    """
    global _backend, _backend_locked
    if _backend_locked:
        raise RuntimeError(
            "Cannot change backend after models have been fitted. "
            "Call set_backend() before any model fitting."
        )
    if name not in ("jax", "numpy"):
        raise ValueError(f"Unknown backend: {name}. Use 'jax' or 'numpy'.")

    # Validate JAX availability early if requested
    if name == "jax":
        try:
            import jax

            jax.config.update("jax_enable_x64", True)
        except ImportError as e:
            raise ImportError(
                "JAX is not installed. Install it with 'pip install jax jaxlib' "
                "or use set_backend('numpy')."
            ) from e

    _backend = name


def _lock_backend() -> None:
    """Lock the backend to prevent switching after model fitting.

    This is called internally when models are fitted to ensure consistent
    behavior throughout a session.
    """
    global _backend, _backend_locked
    # Ensure backend is initialized before locking
    if _backend is None:
        _backend = _detect_backend()
    _backend_locked = True


def _is_backend_locked() -> bool:
    """Check if the backend is locked.

    Returns:
        True if backend is locked, False otherwise.
    """
    return _backend_locked


def _reset_backend() -> None:
    """Reset backend state (for testing only).

    Warning:
        This should only be used in tests. Using it in production code
        can lead to inconsistent behavior.
    """
    global _backend, _backend_locked
    _backend = None
    _backend_locked = False


@contextmanager
def backend(name: BackendName):
    """Context manager for temporary backend switching.

    This is primarily intended for testing. It temporarily switches the
    backend and restores the previous state on exit.

    Args:
        name: Backend name to use within the context.

    Context Manager:
        Yields None; restores previous backend on exit.

    Examples:
        >>> import bossanova
        >>> with bossanova.backend("numpy"):
        ...     print(bossanova.get_backend())
        'numpy'
    """
    global _backend, _backend_locked
    old_backend = _backend
    old_locked = _backend_locked

    # Temporarily switch
    _backend = name
    _backend_locked = False

    try:
        yield
    finally:
        # Restore previous state
        _backend = old_backend
        _backend_locked = old_locked
