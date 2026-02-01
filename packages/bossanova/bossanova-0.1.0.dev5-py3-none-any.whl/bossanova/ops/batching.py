"""Memory-aware batch sizing for JAX operations.

Provides utilities to compute optimal batch sizes for jax.lax.map based on
available system memory. Balances parallelism efficiency against memory
pressure and cache locality.
"""

import warnings

__all__ = ["get_available_memory_gb", "compute_batch_size"]

# Constraints tuned for resampling workloads
MIN_BATCH_SIZE: int = 64  # Below this, parallelism suffers
MAX_BATCH_SIZE: int = 8192  # Above this, cache efficiency degrades
SAFETY_MARGIN: float = 0.3  # 30% for XLA overhead, intermediates
DEFAULT_MAX_MEM: float = 0.5  # 50% of available memory


def get_available_memory_gb() -> float:
    """Query available system memory in GB.

    Attempts to detect available memory using multiple fallback strategies:
    1. JAX device stats (for GPU/TPU with memory tracking)
    2. psutil for CPU/system memory
    3. Conservative 4GB fallback with warning

    Returns:
        Available memory in GB (minimum 0.5 GB).

    Examples:
        >>> mem_gb = get_available_memory_gb()
        >>> print(f"Available: {mem_gb:.1f} GB")
    """
    # Try JAX device stats first (GPU/TPU)
    try:
        import jax

        device = jax.devices()[0]
        stats = device.memory_stats()

        if stats:
            if "bytes_limit" in stats and "bytes_in_use" in stats:
                # Best case: know both limit and current usage
                available_bytes = stats["bytes_limit"] - stats["bytes_in_use"]
                return max(available_bytes / (1024**3), 0.5)
            elif "bytes_limit" in stats:
                # Only know limit, assume 30% available conservatively
                available_bytes = stats["bytes_limit"] * 0.3
                return max(available_bytes / (1024**3), 0.5)
    except Exception:
        pass

    # CPU fallback: try psutil
    try:
        import psutil

        mem = psutil.virtual_memory()
        available_bytes = mem.available
        return max(available_bytes / (1024**3), 0.5)
    except Exception:
        pass

    # Final fallback
    warnings.warn(
        "Could not detect available memory. Using conservative default of 4.0 GB. "
        "Consider specifying max_mem explicitly.",
        UserWarning,
        stacklevel=2,
    )
    return 4.0


def compute_batch_size(
    *,
    n_items: int,
    bytes_per_item: int,
    max_mem: float | None = None,
    min_batch: int = MIN_BATCH_SIZE,
    max_batch: int = MAX_BATCH_SIZE,
) -> int:
    """Compute optimal batch size for jax.lax.map.

    Balances memory usage, parallelism efficiency, and cache locality.
    Uses a safety margin to account for XLA compilation overhead and
    intermediate arrays.

    Args:
        n_items: Total items to process (e.g., n_boot, n_perm).
        bytes_per_item: Memory per output item in bytes.
            For bootstrap/permutation with p coefficients: p * 8 (float64).
        max_mem: Fraction of available system memory to use (0.0-1.0).
            None defaults to 0.5 (50%). Values outside [0.01, 1.0] are clamped.
        min_batch: Minimum batch size for parallelism efficiency.
        max_batch: Maximum batch size for cache efficiency.

    Returns:
        Batch size clamped to [min_batch, min(max_batch, n_items)].

    Examples:
        >>> # 10000 bootstrap samples, each producing 100 float64 coefficients
        >>> batch_size = compute_batch_size(n_items=10000, bytes_per_item=100 * 8)
        >>> keys = jax.random.split(key, 10000)
        >>> boot_samples = jax.lax.map(fn, keys, batch_size=batch_size)
    """
    # Handle max_mem parameter
    if max_mem is None:
        max_mem = DEFAULT_MAX_MEM
    else:
        # Clamp to valid range
        max_mem = max(0.01, min(1.0, max_mem))

    # Get available memory and apply user fraction
    available_gb = get_available_memory_gb()
    budget_gb = available_gb * max_mem

    # Apply safety margin for XLA overhead
    usable_gb = budget_gb * (1.0 - SAFETY_MARGIN)
    usable_bytes = usable_gb * (1024**3)

    # Compute batch size from memory budget
    if bytes_per_item > 0:
        computed_size = int(usable_bytes / bytes_per_item)
    else:
        computed_size = n_items

    # Clamp to valid range
    result = max(min_batch, min(computed_size, max_batch, n_items))

    return result
