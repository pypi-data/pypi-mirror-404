"""Resampling methods for statistical inference.

This module provides JAX-accelerated implementations of permutation tests,
bootstrap procedures, and cross-validation for bossanova models.

Core Functions
--------------
- generate_permutation_indices: Create permutation index arrays
- generate_bootstrap_indices: Create bootstrap sample indices
- generate_kfold_indices: Create k-fold CV splits
- generate_loo_indices: Create leave-one-out CV splits
- compute_pvalues: Calculate permutation p-values
- bootstrap_ci_percentile: Percentile bootstrap confidence intervals
- bootstrap_ci_basic: Basic (pivotal) bootstrap confidence intervals
- bootstrap_ci_bca: BCa bootstrap confidence intervals

lm-Specific Functions
---------------------
- lm_permute: Efficient permutation test for lm models
- lm_bootstrap: Bootstrap inference for lm coefficients
- lm_cv: Cross-validation for lm models
- make_lm_coefficient_operator: Create reusable Y -> coef operator
- compute_lm_se: Compute lm coefficient standard errors

glm-Specific Functions
----------------------
- glm_bootstrap: Bootstrap inference for GLM coefficients (cases or parametric)
- glm_permute: Permutation test for GLM coefficients
- simulate_response: Simulate GLM response from fitted values

Mixed Model Functions
---------------------
- glmer_bootstrap: Bootstrap inference for GLMER coefficients (parametric or case)
- lmer_bootstrap: Bootstrap inference for LMER coefficients (parametric)

Result Classes
--------------
- PermutationResult: Container for permutation test results
- BootstrapResult: Container for bootstrap results
- CVResult: Container for cross-validation results

Model Methods
-------------
The lm and glm classes provide convenient methods that call these functions:
- model.permute(): Permutation test on fitted model (lm only)
- model.bootstrap(): Bootstrap inference on fitted model
- model.cv(): Cross-validation on fitted model (lm only)

Example
-------
>>> from bossanova import lm, glm
>>> model = lm("y ~ x", data=df).fit()
>>> result = model.bootstrap(n_boot=999, ci_type="bca")
>>> print(result.summary())
>>> print(result.ci)

>>> model_glm = glm("y ~ x", data=df, family="binomial").fit()
>>> result_glm = model_glm.bootstrap(n_boot=999, boot_type="case")
"""

from bossanova.resample.core import (
    bootstrap_ci_basic,
    bootstrap_ci_bca,
    bootstrap_ci_percentile,
    compute_pvalues,
    generate_bootstrap_indices,
    generate_kfold_indices,
    generate_loo_indices,
    generate_permutation_indices,
)
from bossanova.resample.glm import (
    glm_bootstrap,
    glm_permute,
    simulate_response,
)
from bossanova.resample.lm import (
    compute_lm_se,
    lm_bootstrap,
    lm_cv,
    lm_permute,
    make_lm_coefficient_operator,
)
from bossanova.resample.mixed import (
    glmer_bootstrap,
    lmer_bootstrap,
)
from bossanova.resample.results import (
    BootstrapResult,
    CVResult,
    PermutationResult,
)

__all__ = [
    # Core functions
    "generate_permutation_indices",
    "generate_bootstrap_indices",
    "generate_kfold_indices",
    "generate_loo_indices",
    "compute_pvalues",
    "bootstrap_ci_percentile",
    "bootstrap_ci_basic",
    "bootstrap_ci_bca",
    # lm-specific functions
    "lm_permute",
    "lm_bootstrap",
    "lm_cv",
    "make_lm_coefficient_operator",
    "compute_lm_se",
    # glm-specific functions
    "glm_bootstrap",
    "glm_permute",
    "simulate_response",
    # Mixed model functions
    "glmer_bootstrap",
    "lmer_bootstrap",
    # Result classes
    "PermutationResult",
    "BootstrapResult",
    "CVResult",
]
