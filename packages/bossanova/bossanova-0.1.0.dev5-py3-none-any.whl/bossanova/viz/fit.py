"""Observed vs Predicted plot for bossanova models.

This module provides plot_fit() for visualizing model fit quality
via an Observed vs Predicted scatter plot with R² annotation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import polars as pl

from bossanova.viz._core import (
    BOSSANOVA_STYLE,
    finalize_facetgrid,
)

if TYPE_CHECKING:
    import seaborn as sns

    from bossanova.models.base import BaseModel

__all__ = ["plot_fit"]


def plot_fit(
    model: BaseModel,
    *,
    hue: str | None = None,
    col: str | None = None,
    row: str | None = None,
    show_identity: bool = True,
    show_regression: bool = False,
    show_r2: bool = True,
    # FacetGrid params
    height: float = 4.0,
    aspect: float = 1.0,
    col_wrap: int | None = None,
    palette: str | None = None,
) -> sns.FacetGrid:
    """Plot observed vs predicted values to assess model fit.

    Creates a scatter plot comparing observed (actual) values against
    predicted (fitted) values. A perfect model would have all points
    on the 45-degree identity line.

    This answers: "How well does the model capture the data?"

    Args:
        model: A fitted bossanova model (lm, glm, lmer, glmer).
        hue: Column name for color encoding (categorical grouping).
        col: Column name for faceting into columns.
        row: Column name for faceting into rows.
        show_identity: Show 45-degree identity line (perfect fit reference).
        show_regression: Show regression line through points (useful for
            detecting systematic bias).
        show_r2: Annotate with R² value in each panel.
        height: Height of each facet in inches.
        aspect: Aspect ratio of each facet.
        palette: Color palette name (default: BOSSANOVA_STYLE palette).

    Returns:
        Seaborn FacetGrid containing the plot.

    Raises:
        RuntimeError: If model is not fitted.

    Examples:
        >>> from bossanova import lm, viz, load_dataset
        >>> mtcars = load_dataset("mtcars")
        >>> model = lm("mpg ~ wt + hp", data=mtcars).fit()

        >>> # Basic observed vs predicted
        >>> viz.plot_fit(model)

        >>> # Facet by cylinder count
        >>> viz.plot_fit(model, hue="cyl")

        >>> # Facet into columns
        >>> model = lm("mpg ~ wt * cyl", data=mtcars).fit()
        >>> viz.plot_fit(model, col="cyl")

    See Also:
        plot_resid: Residual diagnostics (Q-Q, scale-location, leverage).
        plot_predict: Marginal predictions across predictor range.
    """
    import seaborn as sns

    if not model.is_fitted:
        raise RuntimeError("Model must be fitted before plotting")

    style = BOSSANOVA_STYLE
    if palette is None:
        palette = style["palette"]

    # Build DataFrame with observed and predicted
    plot_df = _build_fit_data(model, hue=hue, col=col, row=row)

    # Create FacetGrid using relplot - pass Polars DataFrame directly
    relplot_kwargs = {
        "data": plot_df,
        "x": "Predicted",
        "y": "Observed",
        "height": height,
        "aspect": aspect,
        "alpha": 0.6,
        "edgecolor": "white",
        "linewidth": 0.5,
    }
    if hue is not None:
        relplot_kwargs["hue"] = hue
        relplot_kwargs["palette"] = palette
    if col is not None:
        relplot_kwargs["col"] = col
    if row is not None:
        relplot_kwargs["row"] = row
    if col_wrap is not None and row is None:
        relplot_kwargs["col_wrap"] = col_wrap

    g = sns.relplot(**relplot_kwargs)

    # Add identity line and annotations to each facet
    g.map_dataframe(_add_identity_line, show=show_identity)
    g.map_dataframe(_add_regression_line, show=show_regression, style=style)

    if show_r2:
        _add_r2_annotations(g, plot_df, col=col, row=row)

    # Finalize
    finalize_facetgrid(
        g, title="Observed vs Predicted", xlabel="Predicted", ylabel="Observed"
    )

    return g


def _build_fit_data(
    model: BaseModel,
    *,
    hue: str | None = None,
    col: str | None = None,
    row: str | None = None,
) -> pl.DataFrame:
    """Build Polars DataFrame with observed, predicted, and grouping columns."""
    # Get observed and predicted
    observed = np.asarray(model._y)
    predicted = np.asarray(model.fitted)

    # Start with observed and predicted
    data = {"Observed": observed, "Predicted": predicted}

    # Add grouping columns from original data (already Polars)
    original_data = model.data

    for col_name in [hue, col, row]:
        if col_name is not None and col_name in original_data.columns:
            col_values = original_data[col_name].to_numpy()
            # Handle potential length mismatch due to missing value removal
            if len(original_data) == len(observed):
                data[col_name] = col_values
            else:
                # Use valid mask if available
                if hasattr(model, "valid_mask") and model.valid_mask is not None:
                    data[col_name] = col_values[model.valid_mask]
                else:
                    # Fallback: assume data is already filtered
                    data[col_name] = col_values[: len(observed)]

    return pl.DataFrame(data)


def _add_identity_line(data, *, show: bool = True, **kwargs) -> None:
    """Add 45-degree identity line to current axes."""
    if not show:
        return

    import matplotlib.pyplot as plt

    ax = plt.gca()

    # Get axis limits
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    # Compute line spanning both axes
    min_val = min(xlim[0], ylim[0])
    max_val = max(xlim[1], ylim[1])

    style = BOSSANOVA_STYLE
    ax.plot(
        [min_val, max_val],
        [min_val, max_val],
        color=style["ref_line_color"],
        linestyle=style["ref_line_style"],
        linewidth=style["ref_line_width"],
        zorder=0,
        label="_nolegend_",
    )

    # Reset limits (plot may have changed them)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)


def _add_regression_line(data, *, show: bool = False, style: dict, **kwargs) -> None:
    """Add regression line through observed vs predicted points."""
    if not show:
        return

    import matplotlib.pyplot as plt
    from scipy import stats

    ax = plt.gca()

    x = np.asarray(data["Predicted"])
    y = np.asarray(data["Observed"])

    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    # Plot regression line
    x_range = np.array([x.min(), x.max()])
    y_pred = intercept + slope * x_range

    ax.plot(
        x_range,
        y_pred,
        color="red",
        linewidth=style["line_width"],
        alpha=0.8,
        label="_nolegend_",
    )


def _add_r2_annotations(
    g,  # sns.FacetGrid
    plot_df: pl.DataFrame,
    *,
    col: str | None = None,
    row: str | None = None,
) -> None:
    """Add R² annotations to each panel."""
    style = BOSSANOVA_STYLE

    # Iterate over all axes
    for ax in g.axes.flat:
        if ax is None:
            continue

        # Get data for this facet
        # For simple case (no faceting), use all data
        if col is None and row is None:
            facet_data = plot_df
        else:
            # Get facet values from axis title
            title = ax.get_title()
            if not title:
                facet_data = plot_df
            else:
                # Parse facet values from title (format: "col = value" or "row = value | col = value")
                facet_data = _get_facet_data(plot_df, title)

        if len(facet_data) == 0:
            continue

        # Compute R² for this facet
        observed = np.asarray(facet_data["Observed"])
        predicted = np.asarray(facet_data["Predicted"])

        ss_res = np.sum((observed - predicted) ** 2)
        ss_tot = np.sum((observed - np.mean(observed)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Add annotation
        ax.annotate(
            f"R² = {r2:.3f}",
            xy=(0.05, 0.95),
            xycoords="axes fraction",
            ha="left",
            va="top",
            fontsize=style["font_size"],
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.8},
        )


def _get_facet_data(df: pl.DataFrame, title: str) -> pl.DataFrame:
    """Extract data for a specific facet based on title.

    Parses seaborn's facet title format: "col_name = value" or "row = val1 | col = val2"
    """
    # Parse title format
    if " | " in title:
        parts = title.split(" | ")
    else:
        parts = [title]

    result = df
    for part in parts:
        if " = " in part:
            var_name, value = part.split(" = ", 1)
            var_name = var_name.strip()
            value = value.strip()

            if var_name in result.columns:
                # Try numeric comparison first, fall back to string
                col_dtype = result[var_name].dtype
                if col_dtype in (
                    pl.Float64,
                    pl.Float32,
                    pl.Int64,
                    pl.Int32,
                    pl.Int16,
                    pl.Int8,
                ):
                    try:
                        result = result.filter(pl.col(var_name) == float(value))
                    except ValueError:
                        result = result.filter(pl.col(var_name).cast(pl.Utf8) == value)
                else:
                    result = result.filter(pl.col(var_name).cast(pl.Utf8) == value)

    return result
