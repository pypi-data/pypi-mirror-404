"""Internal computational utilities for bossanova.

This module contains shared computational functions used by model classes.
These are internal implementation details and should not be imported directly.

Modules:
- linalg: QR and SVD solvers for ordinary least squares
- diagnostics: Leverage, Cook's D, VIF, studentized residuals
- inference: Standard errors, confidence intervals, p-values
- batching: Memory-aware batch sizing for JAX operations
- rng: Unified RNG abstraction for JAX/NumPy backends
"""

from bossanova.ops.batching import compute_batch_size, get_available_memory_gb
from bossanova.ops.diagnostics import (
    compute_cooks_distance,
    compute_leverage,
    compute_studentized_residuals,
    compute_vif,
)
from bossanova.ops.inference import (
    adjust_pvalues,
    compute_ci,
    compute_pvalue,
    compute_se_from_vcov,
    compute_t_critical,
    compute_z_critical,
    delta_method_se,
    format_pvalue_with_stars,
    parse_conf_int,
)
from bossanova.ops._get_ops import clear_ops_cache, get_ops
from bossanova.ops.linalg import (
    QRSolveResult,
    SVDSolveResult,
    qr_solve,
    qr_solve_jax,
    svd_solve,
    svd_solve_jax,
)
from bossanova.ops.rng import RNG, create_rng, get_jax_key

__all__ = [
    # Backend operations
    "get_ops",
    "clear_ops_cache",
    # linalg (public numpy API)
    "qr_solve",
    "svd_solve",
    # linalg (internal JAX API)
    "qr_solve_jax",
    "svd_solve_jax",
    "QRSolveResult",
    "SVDSolveResult",
    # diagnostics
    "compute_leverage",
    "compute_studentized_residuals",
    "compute_cooks_distance",
    "compute_vif",
    # inference
    "parse_conf_int",
    "compute_t_critical",
    "compute_z_critical",
    "compute_se_from_vcov",
    "compute_ci",
    "compute_pvalue",
    "adjust_pvalues",
    "delta_method_se",
    "format_pvalue_with_stars",
    # batching
    "get_available_memory_gb",
    "compute_batch_size",
    # rng
    "RNG",
    "create_rng",
    "get_jax_key",
]
