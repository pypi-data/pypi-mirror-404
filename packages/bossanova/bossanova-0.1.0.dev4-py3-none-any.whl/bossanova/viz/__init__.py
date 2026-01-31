"""Visualization module for bossanova models.

This module provides plotting functions for model exploration and diagnostics.
All functions follow the functional core pattern - they take a model as input
and return matplotlib Figure or Axes objects.

Available Functions:
    plot_params: Forest plot of parameter estimates (fixed/random effects)
    plot_resid: Residual diagnostic grid (4 panels)
    plot_predict: Marginal predictions across predictor range
    plot_mee: Marginal effects/means visualization
    plot_fit: Composite diagnostic panel
    plot_compare: Multi-model coefficient comparison
    plot_dag: Causal DAG visualization
    plot_lattice: Model lattice (Hasse diagram) visualization
    plot_cognition: Combined DAG + lattice visualization

Examples:
    >>> from bossanova import lm, viz
    >>> model = lm("mpg ~ wt + hp", data=mtcars).fit()
    >>> viz.plot_params(model)
    >>> viz.plot_resid(model)

    # Or using model methods (convenience wrappers)
    >>> model.plot_params()
    >>> model.plot_resid()

    # Pre-estimation visualization via grammar API
    >>> from bossanova.grammar import model, assuming, viz
    >>> model("y ~ x1 + x2") | assuming() | viz()
"""

from bossanova.viz._core import (
    BOSSANOVA_STYLE,
    compute_figsize,
    compute_grid_figsize,
    extract_params,
    extract_residuals,
)

# Plot functions (post-estimation)
from bossanova.viz.params import plot_params
from bossanova.viz.ranef import plot_ranef
from bossanova.viz.resid import plot_resid
from bossanova.viz.predict import plot_predict
from bossanova.viz.fit import plot_fit
from bossanova.viz.mem import plot_mee
from bossanova.viz.compare import plot_compare

# Plot functions (pre-estimation / model cognition)
from bossanova.viz.dag import plot_dag
from bossanova.viz.lattice import plot_lattice
from bossanova.viz.cognition import plot_cognition
from bossanova.viz.design import plot_design
from bossanova.viz.vif import plot_vif
from bossanova.viz.relationships import plot_relationships

__all__ = [
    # Core utilities
    "BOSSANOVA_STYLE",
    "compute_figsize",
    "compute_grid_figsize",
    "extract_params",
    "extract_residuals",
    # Plot functions (post-estimation)
    "plot_params",
    "plot_ranef",
    "plot_resid",
    "plot_predict",
    "plot_fit",
    "plot_mee",
    "plot_compare",
    # Plot functions (pre-estimation / model cognition)
    "plot_dag",
    "plot_lattice",
    "plot_cognition",
    "plot_design",
    "plot_vif",
    "plot_relationships",
]
