"""Relationship visualization for bossanova models.

This module provides plot_relationships() for visualizing pairwise relationships
between the response variable and predictors via scatter plot matrix.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import polars as pl

from bossanova.viz._core import BOSSANOVA_STYLE
from bossanova.viz.design import _parse_column_type
from bossanova.viz.vif import _compute_vif

if TYPE_CHECKING:
    import seaborn as sns

    from bossanova.models.base import BaseModel

__all__ = ["plot_relationships"]


# =============================================================================
# Main Plot Function
# =============================================================================


def plot_relationships(
    model: BaseModel,
    *,
    show_vif: bool = True,
    # PairGrid params
    height: float = 1.5,
    aspect: float = 1.0,
    palette: str | None = None,
) -> sns.PairGrid:
    """Plot pairwise relationships between response and predictors.

    Creates a scatter plot matrix showing:
    - Response variable (y) in the first row/column
    - All predictor variables from the design matrix
    - Diagonal shows distributions (KDE) colored by variable type
    - Off-diagonal shows pairwise scatter plots
    - VIF statistics for multicollinearity assessment (optional)

    Works on unfitted models since the design matrix is built at initialization.

    Args:
        model: A bossanova model (lm, glm, lmer, glmer). Can be fitted or unfitted.
        show_vif: Whether to display VIF statistics above the plot.
        height: Height of each facet in inches.
        aspect: Aspect ratio of each facet.
        palette: Color palette name (default: BOSSANOVA_STYLE palette).

    Returns:
        Seaborn PairGrid containing the plot.

    Note:
        This function returns a PairGrid. To access the underlying Figure,
        use `g.figure`. Migration from previous API:
        `fig = model.plot_relationships()` → `g = model.plot_relationships(); fig = g.figure`

    Examples:
        >>> from bossanova import lm, load_dataset
        >>> cars = load_dataset("mtcars")
        >>> model = lm("mpg ~ wt + hp + disp", data=cars)
        >>> model.plot_relationships()  # Shows y and all predictors
    """
    import seaborn as sns
    from matplotlib.patches import Patch

    style = BOSSANOVA_STYLE
    if palette is None:
        palette = style["palette"]

    # Get design matrix and response
    X = model._X
    X_names = model._X_names
    y = model._y
    y_name = model._y_name

    # Find non-intercept columns
    non_intercept_idx = [i for i, name in enumerate(X_names) if name != "Intercept"]
    X_pred = X[:, non_intercept_idx]
    pred_names = [X_names[i] for i in non_intercept_idx]

    n_predictors = len(pred_names)

    if n_predictors == 0:
        raise ValueError("Model has no predictors (only intercept)")

    # Get column types for predictors
    col_types = [_parse_column_type(name) for name in pred_names]

    # Color scheme matching plot_design
    type_colors = {
        "response": "#5C6BC0",  # Indigo for response variable
        "constant": "#9E9E9E",  # Medium gray
        "continuous": "#78909C",  # Blue-gray
        "factor": "#A1887F",  # Warm gray/taupe
    }
    type_labels = {
        "response": "Response",
        "constant": "Constant",
        "continuous": "Continuous",
        "factor": "Factor",
    }

    # Build VIF info text if requested
    vif_text = ""
    if show_vif and n_predictors >= 2:
        vif_values = _compute_vif(X, X_names)
        vif_lines = []
        for name in pred_names:
            vif = vif_values.get(name, 1.0)
            ci_increase = np.sqrt(vif)
            if np.isinf(vif):
                vif_lines.append(f"{name}: VIF=∞")
            else:
                vif_lines.append(f"{name}: VIF={vif:.1f}, CI inc: {ci_increase:.1f}x")
        vif_text = "\n".join(vif_lines)

    # Create Polars DataFrame with y first, then predictors
    all_names = [y_name] + pred_names
    all_types = ["response"] + col_types

    data_dict = {y_name: y}
    for i, name in enumerate(pred_names):
        data_dict[name] = X_pred[:, i]

    df = pl.DataFrame(data_dict)

    n_vars = len(all_names)

    # Create PairGrid (supports Polars directly)
    grid = sns.PairGrid(
        df,
        height=height,
        aspect=aspect,
    )

    # Map scatter plots to off-diagonal
    grid.map_offdiag(
        sns.scatterplot,
        alpha=0.5,
        s=20,
        edgecolor="none",
        color="#888888",
    )

    # Map KDE plots to diagonal
    grid.map_diag(sns.kdeplot, fill=True, alpha=0.7, linewidth=1.5, color="#888888")

    # Color diagonal KDE plots by variable type and remove spines
    for i, (name, vtype) in enumerate(zip(all_names, all_types)):
        color = type_colors[vtype]
        ax_diag = grid.diag_axes[i]
        ax_diag.clear()

        # Get data for this variable
        col_data = np.asarray(df[name])

        sns.kdeplot(
            col_data, ax=ax_diag, color=color, fill=True, alpha=0.7, linewidth=1.5
        )
        ax_diag.set_ylabel("")
        ax_diag.set_xlabel("")
        ax_diag.set_yticks([])
        # Remove spines from diagonal plots
        for spine in ax_diag.spines.values():
            spine.set_visible(False)

    # Style adjustments to match bossanova aesthetic
    for ax in grid.axes.flatten():
        if ax is not None:
            ax.tick_params(labelsize=style["font_size"] - 2)
            # Keep spines on off-diagonal plots but make them subtle
            if ax not in grid.diag_axes:
                for spine in ax.spines.values():
                    spine.set_color("#cccccc")

    # Add legend for variable types (only those present)
    present_types = set(all_types)
    legend_elements = [
        Patch(facecolor=type_colors[t], label=type_labels[t], alpha=0.7)
        for t in ["response", "constant", "continuous", "factor"]
        if t in present_types
    ]
    grid.figure.legend(
        handles=legend_elements,
        loc="upper right",
        bbox_to_anchor=(0.98, 0.98),
        fontsize=style["font_size"] - 1,
        title="Type",
        title_fontsize=style["font_size"] - 1,
    )

    # Add main title at top
    grid.figure.suptitle(
        "Variable Relationships",
        fontsize=style["title_size"],
        y=1.02,
    )

    # Add VIF info below title (left-aligned, closer to title)
    if vif_text:
        grid.figure.text(
            0.02,
            0.99,
            vif_text,
            ha="left",
            va="top",
            fontsize=style["font_size"] - 1,
            color="#666666",
            transform=grid.figure.transFigure,
        )

    grid.figure.tight_layout()
    grid.figure.subplots_adjust(top=0.88 - n_vars * 0.01)

    return grid
