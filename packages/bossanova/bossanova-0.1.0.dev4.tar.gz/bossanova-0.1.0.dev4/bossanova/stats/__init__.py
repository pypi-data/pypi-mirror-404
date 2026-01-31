"""Statistical utilities for inference and p-value adjustments."""

from bossanova.stats.compare import compare
from bossanova.stats.lrt import lrt
from bossanova.stats.sandwich import compute_glm_hc_vcov, compute_hc_vcov
from bossanova.stats.satterthwaite import (
    compute_gradient_richardson,
    compute_hessian_numerical,
    compute_hessian_richardson,
    compute_jacobian_numerical,
    compute_jacobian_richardson,
    compute_satterthwaite_summary_table,
    satterthwaite_df,
    satterthwaite_df_for_contrasts,
    satterthwaite_t_test,
)
from bossanova.stats.welch import (
    CellInfo,
    compute_cell_info,
    compute_welch_se,
    extract_factors_from_formula,
    welch_satterthwaite_df,
)

__all__ = [
    # compare & lrt
    "compare",
    "lrt",
    # sandwich (HC) estimators
    "compute_hc_vcov",
    "compute_glm_hc_vcov",
    # satterthwaite (for mixed models)
    "compute_gradient_richardson",
    "compute_hessian_richardson",
    "compute_jacobian_richardson",
    "compute_hessian_numerical",
    "compute_jacobian_numerical",
    "satterthwaite_df",
    "satterthwaite_df_for_contrasts",
    "satterthwaite_t_test",
    "compute_satterthwaite_summary_table",
    # welch (unequal variance)
    "welch_satterthwaite_df",
    "CellInfo",
    "extract_factors_from_formula",
    "compute_cell_info",
    "compute_welch_se",
]
