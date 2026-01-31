"""Result schemas and builders for bossanova models.

This module provides:
- Dataclass schemas defining the structure of result DataFrames
- Builder functions that construct DataFrames from schemas

Usage:
    from bossanova.results import LMResultFit, build_result_params

    schema = LMResultFit(
        term=["Intercept", "x"],
        estimate=[1.0, 2.0],
        ...
    )
    df = build_result_params(schema)
"""

from bossanova.results.schemas import (
    # Base schemas
    BaseResultFit,
    BaseResultFitDiagnostics,
    # lm schemas
    LMResultFit,
    LMResultFitDiagnostics,
    # glm schemas
    GLMResultFit,
    GLMResultFitDiagnostics,
    # lmer schemas
    LMerResultFit,
    LMerResultFitDiagnostics,
    # ridge schemas
    RidgeResultFit,
    RidgeResultFitDiagnostics,
    # Bootstrap/permutation schemas
    BootResultFit,
    PermResultFit,
)

from bossanova.results.builders import (
    build_result_params,
    build_result_model,
    build_boot_result_params,
    build_perm_result_params,
    # glm builders
    build_glm_result_params,
    build_glm_result_model,
    # lmer builders
    build_lmer_result_params,
    build_lmer_result_model,
    build_ranef_dataframe,
    theta_to_variance_components,
    # ridge builders
    build_ridge_result_params,
    build_ridge_result_model,
)

from bossanova.results.wrappers import ResultFit

__all__ = [
    # Wrapper
    "ResultFit",
    # Schemas
    "BaseResultFit",
    "BaseResultFitDiagnostics",
    "LMResultFit",
    "LMResultFitDiagnostics",
    "GLMResultFit",
    "GLMResultFitDiagnostics",
    "LMerResultFit",
    "LMerResultFitDiagnostics",
    "RidgeResultFit",
    "RidgeResultFitDiagnostics",
    "BootResultFit",
    "PermResultFit",
    # Builders
    "build_result_params",
    "build_result_model",
    "build_boot_result_params",
    "build_perm_result_params",
    "build_glm_result_params",
    "build_glm_result_model",
    "build_lmer_result_params",
    "build_lmer_result_model",
    "build_ranef_dataframe",
    "theta_to_variance_components",
    "build_ridge_result_params",
    "build_ridge_result_model",
]
