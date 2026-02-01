"""Simulation utilities for parameter recovery and Monte Carlo studies.

This module provides data generating process (DGP) functions for creating
synthetic datasets with known true parameters, enabling:

- Parameter recovery validation (bias, RMSE)
- Coverage probability testing (CI calibration)
- Type I/II error rate validation
- Power analysis

Examples:
    >>> from bossanova.simulation import generate_lm_data, monte_carlo
    >>> from bossanova import lm
    >>>
    >>> # Run Monte Carlo study
    >>> result = monte_carlo(
    ...     dgp_fn=generate_lm_data,
    ...     dgp_params={"n": 100, "beta": [1.0, 2.0], "sigma": 1.0},
    ...     fit_fn=lambda d: lm("y ~ x1", data=d).fit(),
    ...     n_sims=500,
    ... )
    >>> result.bias("x1")      # Should be ~0
    >>> result.coverage("x1")  # Should be ~0.95
"""

from bossanova.simulation.dgp import (
    generate_glm_data,
    generate_glmer_data,
    generate_lm_data,
    generate_lmer_data,
)
from bossanova.simulation.harness import MonteCarloResult, monte_carlo
from bossanova.simulation.metrics import (
    bias,
    coverage,
    empirical_se,
    mean_se,
    rejection_rate,
    rmse,
    se_ratio,
)

__all__ = [
    # DGP generators
    "generate_lm_data",
    "generate_glm_data",
    "generate_lmer_data",
    "generate_glmer_data",
    # Monte Carlo harness
    "monte_carlo",
    "MonteCarloResult",
    # Metrics
    "bias",
    "rmse",
    "mean_se",
    "empirical_se",
    "coverage",
    "rejection_rate",
    "se_ratio",
]
