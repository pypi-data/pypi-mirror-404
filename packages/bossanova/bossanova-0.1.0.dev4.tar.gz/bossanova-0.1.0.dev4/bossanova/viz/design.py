"""Design matrix visualization for bossanova models.

This module provides plot_design() for pedagogical visualization of the
design matrix structure. Works on both fitted and unfitted models since
the design matrix is constructed during initialization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np

from bossanova.viz._core import BOSSANOVA_STYLE, setup_ax

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from bossanova.models.base import BaseModel

__all__ = ["plot_design"]


# =============================================================================
# Column Type Detection
# =============================================================================


def _parse_column_type(
    name: str,
) -> Literal["constant", "continuous", "factor"]:
    """Infer the type of a design matrix column from its name.

    Detection rules:
    - "Intercept" -> constant
    - Contains "[" and "]" -> factor (categorical dummy or interaction with categorical)
    - Otherwise -> continuous (including continuous × continuous interactions)

    Args:
        name: Column name from the design matrix.

    Returns:
        Column type as a string literal.
    """
    if name == "Intercept":
        return "constant"
    # Brackets indicate categorical variable (e.g., "cyl[6]" or "cyl[6]:wt")
    if "[" in name and "]" in name:
        return "factor"
    # Everything else is continuous (including "wt:hp" interactions)
    return "continuous"


def _group_columns_by_term(X_names: list[str]) -> dict[str, list[int]]:
    """Group design matrix columns by their parent term.

    For example, a factor with 3 levels produces multiple columns like
    "cyl[6]", "cyl[8]" which all belong to term "cyl".

    Args:
        X_names: Column names from the design matrix.

    Returns:
        Dictionary mapping term names to lists of column indices.
    """
    groups: dict[str, list[int]] = {}

    for i, name in enumerate(X_names):
        # Extract base term name
        if name == "Intercept":
            term = "Intercept"
        elif "[" in name and "]" in name:
            # Categorical: "cyl[6]" -> "cyl"
            # Interaction with categorical: "cyl[6]:wt" -> "cyl:wt"
            parts = []
            for part in name.split(":"):
                if "[" in part:
                    parts.append(part.split("[")[0])
                else:
                    parts.append(part)
            term = ":".join(parts)
        elif ":" in name:
            # Continuous interaction: keep as-is
            term = name
        else:
            # Continuous or transformed: use full name as term
            term = name

        if term not in groups:
            groups[term] = []
        groups[term].append(i)

    return groups


def _get_contrast_info(model: BaseModel) -> dict[str, str]:
    """Extract contrast/reference level info from model.

    Args:
        model: A bossanova model (fitted or unfitted).

    Returns:
        Dictionary mapping factor names to reference info strings.
        E.g., {"cyl": "Ref: 4", "am": "Ref: 0"}
    """
    info: dict[str, str] = {}

    # Get factors and their levels
    if not hasattr(model, "_dm") or model._dm is None:
        return info

    dm = model._dm

    for factor, levels in dm.factors.items():
        contrast_type = dm.contrast_types.get(factor, "treatment")

        if contrast_type in ("treatment", "Treatment"):
            # Reference level is the first one
            info[factor] = f"Ref: {levels[0]}"
        elif contrast_type in ("sum", "Sum"):
            # Last level is the reference
            info[factor] = f"Sum (Ref: {levels[-1]})"
        elif contrast_type in ("poly", "Poly"):
            # Polynomial contrast - no single reference
            info[factor] = "Poly"

    return info


# =============================================================================
# Main Plot Function
# =============================================================================


def plot_design(
    model: BaseModel,
    *,
    max_rows: int | None = 20,
    annotate_terms: bool = True,
    show_contrast_info: bool = True,
    cmap: str | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
) -> Figure | Axes:
    """Plot design matrix as an annotated heatmap.

    Visualizes the structure of the model's design matrix with:
    - Color-coded cells by value (sequential or diverging colormap)
    - Column grouping annotations showing which columns belong to each term
    - Reference level annotations for categorical variables

    Works on unfitted models since the design matrix is built at initialization.

    Args:
        model: A bossanova model (lm, glm, lmer, glmer). Can be fitted or unfitted.
        max_rows: Maximum number of rows to display. If None, shows all rows.
            Large datasets are subsampled evenly for readability.
        annotate_terms: Show term grouping brackets above the heatmap.
        show_contrast_info: Show reference level annotations for categorical terms.
        cmap: Matplotlib colormap name. If None (default), auto-selects based on
            data: "magma" for non-negative data, "coolwarm" for signed data.
        figsize: Figure size as (width, height). Auto-computed if None.
        ax: Existing matplotlib Axes to plot on. Creates new figure if None.

    Returns:
        Figure if creating new figure, Axes if ax was provided.

    Examples:
        >>> from bossanova import lm, load_dataset
        >>> cars = load_dataset("mtcars")
        >>> model = lm("mpg ~ factor(cyl) + wt + wt:cyl", data=cars)
        >>> # Works before fitting
        >>> model.plot_design()
        >>> # Also works after fitting
        >>> model.fit().plot_design()
    """
    import matplotlib.pyplot as plt

    # Get design matrix
    X = model._X
    X_names = model._X_names

    n_obs, n_cols = X.shape

    # Subsample rows if too many
    if max_rows is not None and n_obs > max_rows:
        # Even sampling across the dataset
        indices = np.linspace(0, n_obs - 1, max_rows, dtype=int)
        X_plot = X[indices]
        row_labels = [f"row {i}" for i in indices]
    else:
        X_plot = X
        row_labels = [f"row {i}" for i in range(n_obs)]

    n_rows_display = X_plot.shape[0]

    # Compute figure size
    if figsize is None:
        # Width based on columns, height based on rows
        width = max(6, min(14, 1.0 + n_cols * 0.8))
        height = max(4, min(10, 1.5 + n_rows_display * 0.25))
        figsize = (width, height)

    # Set up axes
    user_provided_ax = ax is not None
    fig, ax = setup_ax(ax, figsize=figsize)
    style = BOSSANOVA_STYLE

    # Determine color limits and colormap - adapt to data range
    data_min = np.nanmin(X_plot)
    data_max = np.nanmax(X_plot)
    has_negative = data_min < 0
    has_positive = data_max > 0

    if has_negative and has_positive:
        # Mixed signs: use symmetric diverging range and colormap
        abs_max = max(abs(data_min), abs(data_max))
        vmin, vmax = -abs_max, abs_max
        auto_cmap = "coolwarm"
    elif has_negative:
        # All non-positive: use actual range, sequential colormap (reversed)
        vmin, vmax = data_min, 0
        auto_cmap = "magma_r"
    else:
        # All non-negative: use actual range, sequential colormap
        vmin, vmax = 0, data_max if data_max > 0 else 1
        auto_cmap = "magma"

    # Use user-provided cmap or auto-selected
    cmap = cmap if cmap is not None else auto_cmap

    # Column type colors (muted palette) and hatches for distinction
    col_types = [_parse_column_type(name) for name in X_names]
    type_colors = {
        "constant": "#9E9E9E",  # Medium gray
        "continuous": "#78909C",  # Blue-gray
        "factor": "#A1887F",  # Warm gray/taupe
    }
    type_hatches = {
        "constant": "",  # Solid (no hatch)
        "continuous": "//",  # Diagonal lines
        "factor": "xx",  # Cross-hatch
    }

    # Plot heatmap
    im = ax.imshow(
        X_plot,
        aspect="auto",
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        interpolation="nearest",
    )

    # Add colorbar (narrow, with rotated label)
    cbar = fig.colorbar(im, ax=ax, shrink=0.6, pad=0.02, aspect=30)
    cbar.ax.tick_params(labelsize=style["font_size"] - 1)
    cbar.set_label("Value", rotation=270, labelpad=15, fontsize=style["font_size"])

    # Add faint horizontal lines between rows for clarity
    for row in range(n_rows_display + 1):
        ax.axhline(y=row - 0.5, color="white", linewidth=0.5, alpha=0.6)

    # Add thin colored strip above heatmap for predictor types
    strip_height = 0.4  # Height of the colored strip in data units
    for i, ctype in enumerate(col_types):
        rect = plt.Rectangle(
            (i - 0.5, -0.5 - strip_height),  # Position above the heatmap
            1,
            strip_height,
            facecolor=type_colors[ctype],
            edgecolor="white",
            linewidth=0.5,
            hatch=type_hatches[ctype],
            clip_on=False,
        )
        ax.add_patch(rect)

    # Remove x-axis tick labels (term annotations provide the labels)
    ax.set_xticks([])
    ax.set_xticklabels([])

    ax.set_yticks(np.arange(n_rows_display))
    ax.set_yticklabels(row_labels, fontsize=style["font_size"] - 1)

    # Add term grouping annotations above the color strip
    if annotate_terms:
        term_groups = _group_columns_by_term(X_names)
        contrast_info = _get_contrast_info(model) if show_contrast_info else {}

        # Position for term labels (above color strip and column labels)
        y_label = -0.5 - strip_height - 0.3  # Just above the color strip

        for term, col_indices in term_groups.items():
            if len(col_indices) == 0:
                continue

            # Get x position for the term label (center of its columns)
            x_start = min(col_indices)
            x_end = max(col_indices)
            x_center = (x_start + x_end) / 2

            # Build label with optional contrast info
            label = term
            base_term = term.split(":")[0] if ":" in term else term
            if base_term in contrast_info:
                label = f"{term}\n({contrast_info[base_term]})"

            # Add bracket/span if term has multiple columns
            if len(col_indices) > 1:
                # Draw bracket line
                bracket_y = -0.5 - strip_height - 0.15
                ax.plot(
                    [x_start - 0.3, x_end + 0.3],
                    [bracket_y, bracket_y],
                    color="#666666",
                    lw=1.5,
                    clip_on=False,
                )
                # Add vertical ticks at ends
                tick_height = 0.1
                ax.plot(
                    [x_start - 0.3, x_start - 0.3],
                    [bracket_y, bracket_y + tick_height],
                    color="#666666",
                    lw=1.5,
                    clip_on=False,
                )
                ax.plot(
                    [x_end + 0.3, x_end + 0.3],
                    [bracket_y, bracket_y + tick_height],
                    color="#666666",
                    lw=1.5,
                    clip_on=False,
                )
                y_label_this = bracket_y - 0.15
            else:
                y_label_this = y_label

            # Add term label
            ax.text(
                x_center,
                y_label_this,
                label,
                ha="center",
                va="bottom",
                fontsize=style["font_size"] - 1,
                clip_on=False,
            )

    # Add title with formula
    title = f"{model._formula}"
    if len(title) > 60:
        # Truncate long formulas
        title = f"{model._formula[:55]}..."
    ax.set_title(title, fontsize=style["title_size"], pad=40 if annotate_terms else 10)

    # Add legend for predictor types (only those present in the design matrix)
    from matplotlib.patches import Patch

    type_labels = {
        "constant": "Constant",
        "continuous": "Continuous",
        "factor": "Factor",
    }
    # Only include types that are actually present
    present_types = set(col_types)
    legend_elements = [
        Patch(
            facecolor=color,
            edgecolor="#666666",
            hatch=type_hatches[ctype],
            label=type_labels[ctype],
        )
        for ctype, color in type_colors.items()
        if ctype in present_types
    ]
    ax.legend(
        handles=legend_elements,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        fontsize=style["font_size"] - 1,
        title="Predictor Type",
        title_fontsize=style["font_size"],
        handleheight=1.5,
        handlelength=2.0,
    )

    # Add observation count below heatmap
    obs_text = f"N = {n_obs}"

    # For mixed models, add group counts
    if hasattr(model, "_group_names") and hasattr(model, "_n_groups_list"):
        group_names = model._group_names
        n_groups_list = model._n_groups_list
        if group_names and n_groups_list:
            group_counts = [
                f"{name}: {n}" for name, n in zip(group_names, n_groups_list)
            ]
            obs_text += f"  |  Groups: {', '.join(group_counts)}"

    ax.text(
        0.5,
        -0.02,
        obs_text,
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=style["font_size"] - 1,
        color="#666666",
    )

    fig.tight_layout()

    return ax if user_provided_ax else fig
