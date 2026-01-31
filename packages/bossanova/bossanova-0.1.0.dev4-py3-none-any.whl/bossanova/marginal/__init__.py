"""Marginal estimation module for EMMs and joint tests.

This module provides the computational infrastructure for:
- Estimated marginal means (EMMs)
- Joint tests of EMM contrasts (ANOVA via emmeans approach)
- Reference grid construction
- Contrast matrix builders

The functions here are model-agnostic pure functions. Model-specific
logic (F vs chi-square, Satterthwaite df) lives in joint_tests.py.

Examples:
    >>> from bossanova.marginal import build_reference_grid, compute_emm
    >>> grid = build_reference_grid(data, factors=["group"])
    >>> result = compute_emm(dm, grid, coef, vcov, df_resid)

    >>> from bossanova.marginal import joint_tests
    >>> result = joint_tests(model)  # EMM-based ANOVA
"""

from bossanova.marginal.grid import build_reference_grid
from bossanova.marginal.emm import (
    EMMResult,
    EMMContrastResult,
    compute_emm,
    parse_emmeans_formula,
    format_emm_table,
    format_contrast_table,
)
from bossanova.marginal.contrasts import (
    build_pairwise_contrast,
    build_all_pairwise_contrast,
    build_sum_to_zero_contrast,
    compose_contrast,
)
from bossanova.marginal.hypothesis import (
    compute_f_test,
    compute_chi2_test,
    compute_t_test,
    TTestResult,
    compute_contrast_variance,
    compute_wald_statistic,
)
from bossanova.marginal.joint_tests import joint_tests
from bossanova.marginal.slopes import (
    SlopeResult,
    compute_slopes,
    compute_slopes_by_group,
    average_slopes,
)

__all__ = [
    # Grid construction
    "build_reference_grid",
    # EMM computation
    "EMMResult",
    "EMMContrastResult",
    "compute_emm",
    "parse_emmeans_formula",
    "format_emm_table",
    "format_contrast_table",
    # Contrast matrices
    "build_pairwise_contrast",
    "build_all_pairwise_contrast",
    "build_sum_to_zero_contrast",
    "compose_contrast",
    # Statistical tests
    "compute_f_test",
    "compute_chi2_test",
    "compute_t_test",
    "TTestResult",
    "compute_contrast_variance",
    "compute_wald_statistic",
    # Joint tests (ANOVA)
    "joint_tests",
    # Slopes (marginal effects)
    "SlopeResult",
    "compute_slopes",
    "compute_slopes_by_group",
    "average_slopes",
]
