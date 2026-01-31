"""Formula transformation utilities.

This module provides tools for programmatically modifying formulas
and building design matrices.

Public API:
    transform_formula: Transform formula by applying transforms and contrasts.
    expand_double_verts: Expand || syntax to separate uncorrelated random effects.
    treatment_contrast: Build treatment (dummy) contrast matrix.
    sum_contrast: Build sum (effects) contrast matrix.
    poly_contrast: Build orthogonal polynomial contrast matrix.
    encode_categorical: Encode categorical series using contrast matrix.
    ensure_enum: Convert columns to Polars Enum type.
    detect_categoricals: Detect categorical variables from formula AST.
    DesignMatrixBuilder: Build design matrices from formula + data.
    DesignMatrices: Container for design matrix results.
    build_z_simple: Build Z matrix for single grouping factor.
    build_z_nested: Build Z matrix for nested random effects.
    build_z_crossed: Build Z matrix for crossed random effects.
    build_random_effects: High-level Z matrix builder.
    RandomEffectsInfo: Container for Z matrix and metadata.
"""

from bossanova.formula.transforms import (
    Center,
    FormulaTransformer,
    Scale,
    Standardize,
    StatefulTransform,
    TransformState,
    Zscore,
    create_transform,
    transform_formula,
)
from bossanova.formula.random_effects import (
    expand_double_verts,
)
from bossanova.formula.contrasts import (
    treatment_contrast,
    treatment_labels,
    sum_contrast,
    sum_labels,
    poly_contrast,
    poly_labels,
)
from bossanova.formula.encoding import (
    encode_categorical,
    ensure_enum,
    get_levels,
    infer_levels,
    detect_categoricals,
)
from bossanova.formula.design import (
    DesignMatrixBuilder,
    DesignMatrices,
)
from bossanova.formula.z_matrix import (
    RandomEffectsInfo,
    build_random_effects,
    build_z_crossed,
    build_z_nested,
    build_z_simple,
)

__all__ = [
    "Center",
    "FormulaTransformer",
    "Scale",
    "Standardize",
    "StatefulTransform",
    "TransformState",
    "Zscore",
    "create_transform",
    "transform_formula",
    "expand_double_verts",
    "treatment_contrast",
    "treatment_labels",
    "sum_contrast",
    "sum_labels",
    "poly_contrast",
    "poly_labels",
    "encode_categorical",
    "ensure_enum",
    "get_levels",
    "infer_levels",
    "detect_categoricals",
    "DesignMatrixBuilder",
    "DesignMatrices",
    "RandomEffectsInfo",
    "build_random_effects",
    "build_z_crossed",
    "build_z_nested",
    "build_z_simple",
]
