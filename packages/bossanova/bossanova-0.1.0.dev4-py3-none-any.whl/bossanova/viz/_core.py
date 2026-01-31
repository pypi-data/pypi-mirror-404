"""Core utilities for bossanova visualization.

This module provides shared infrastructure for all plot functions:
- Figure sizing based on number of items
- Consistent styling defaults
- Model data extraction utilities
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import polars as pl

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from bossanova.models.base import BaseModel


# =============================================================================
# Styling Constants
# =============================================================================

BOSSANOVA_STYLE: dict[str, Any] = {
    # Point/marker settings
    "point_size": 80,
    "point_marker": "o",
    "point_edgecolor": "white",
    "point_linewidth": 0.5,
    # Line/whisker settings
    "line_width": 1.5,
    "capsize": 0,
    # Confidence band settings
    "ci_alpha": 0.3,
    # Reference line settings
    "ref_line_color": "#888888",
    "ref_line_style": "--",
    "ref_line_width": 1.0,
    # Font settings
    "font_size": 10,
    "title_size": 12,
    "label_size": 10,
    # Color palette
    "palette": "tab10",
    # Grid settings
    "grid_alpha": 0.3,
    "grid_style": "-",
}


# =============================================================================
# Sizing Utilities
# =============================================================================


def compute_figsize(
    n_items: int,
    orientation: Literal["horizontal", "vertical"] = "horizontal",
    item_size: float = 0.4,
    min_size: float = 3.0,
    max_size: float = 12.0,
    base_width: float = 8.0,
) -> tuple[float, float]:
    """Compute figure size based on number of items.

    Creates readable plots for 15-20 parameters by default.
    Clamps dimensions to prevent too-small or too-large figures.

    Args:
        n_items: Number of items (parameters, groups, etc.) to display.
        orientation: Plot orientation.
            - "horizontal": Items on y-axis (forest plot style).
            - "vertical": Items on x-axis (bar chart style).
        item_size: Inches per item. Default 0.4 works well for forest plots.
        min_size: Minimum dimension in inches.
        max_size: Maximum dimension in inches.
        base_width: Base width for horizontal orientation (height for vertical).

    Returns:
        Tuple of (width, height) in inches.

    Examples:
        >>> compute_figsize(15)  # 15 parameters
        (8.0, 6.0)
        >>> compute_figsize(30)  # Clamped to max
        (8.0, 12.0)
    """
    computed = np.clip(n_items * item_size, min_size, max_size)

    if orientation == "horizontal":
        return (base_width, computed)
    return (computed, base_width)


def compute_grid_figsize(
    n_rows: int,
    n_cols: int,
    cell_width: float = 4.0,
    cell_height: float = 3.5,
) -> tuple[float, float]:
    """Compute figure size for grid/subplot layouts.

    Args:
        n_rows: Number of subplot rows.
        n_cols: Number of subplot columns.
        cell_width: Width per cell in inches.
        cell_height: Height per cell in inches.

    Returns:
        Tuple of (width, height) in inches.

    Examples:
        >>> compute_grid_figsize(2, 2)  # 2x2 diagnostic grid
        (8.0, 7.0)
    """
    return (n_cols * cell_width, n_rows * cell_height)


# =============================================================================
# Model Data Extraction
# =============================================================================


def extract_params(
    model: BaseModel,
    which: Literal["fixef", "ranef", "all"] = "fixef",
    include_intercept: bool = False,
    effect_sizes: bool = False,
    group: str | None = None,
    term: str | None = None,
) -> pl.DataFrame:
    """Extract parameter estimates from a fitted model.

    Returns a standardized DataFrame suitable for forest plot visualization.

    Args:
        model: Fitted bossanova model (lm, glm, lmer, glmer).
        which: Which parameters to extract.
            - "fixef": Fixed effects only (default).
            - "ranef": Random effects (lmer/glmer only).
            - "all": Both fixed and random effects.
        include_intercept: Include intercept term for fixed effects.
        effect_sizes: Return effect sizes (Cohen's d) instead of raw estimates.
        group: For ranef, which grouping factor (None = all).
        term: For ranef, which RE term (None = all).

    Returns:
        DataFrame with columns:
            - term: Parameter name
            - estimate: Point estimate
            - se: Standard error
            - ci_lower: Lower confidence bound
            - ci_upper: Upper confidence bound
            - p_value: P-value (if available)
            - group_factor: Grouping factor name (for ranef)
            - re_term: Random effect term name (for ranef)

    Raises:
        RuntimeError: If model is not fitted.
        TypeError: If which="ranef" but model has no random effects.
    """
    # Check model is fitted
    if not model.is_fitted:
        raise RuntimeError("Model must be fitted before extracting parameters")

    if which == "fixef":
        return _extract_fixef(model, include_intercept, effect_sizes)
    elif which == "ranef":
        return _extract_ranef(model, group, term)
    elif which == "all":
        fixef_df = _extract_fixef(model, include_intercept, effect_sizes)
        ranef_df = _extract_ranef(model, group, term)
        # Add type column for stacking
        fixef_df = fixef_df.with_columns(pl.lit("fixef").alias("param_type"))
        ranef_df = ranef_df.with_columns(pl.lit("ranef").alias("param_type"))
        # Align schemas before concat
        return pl.concat([fixef_df, ranef_df], how="diagonal")
    else:
        raise ValueError(f"which must be 'fixef', 'ranef', or 'all', got {which!r}")


def _extract_fixef(
    model: BaseModel,
    include_intercept: bool = False,
    effect_sizes: bool = False,
) -> pl.DataFrame:
    """Extract fixed effects from model."""
    if effect_sizes:
        # Use result_params.to_effect_size() method
        df = model.result_params.to_effect_size(include_intercept=include_intercept)
        # Rename columns to standard schema for plotting
        # to_effect_size returns: term, estimate, ..., d, d_lower, d_upper, ...
        # We want: term, estimate (= d), ci_lower, ci_upper
        return df.select(
            pl.col("term"),
            pl.col("d").alias("estimate"),
            pl.col("se")
            if "se" in df.columns
            else pl.lit(None).cast(pl.Float64).alias("se"),
            pl.col("d_lower").alias("ci_lower"),
            pl.col("d_upper").alias("ci_upper"),
            pl.col("p_value")
            if "p_value" in df.columns
            else pl.lit(None).cast(pl.Float64).alias("p_value"),
        )

    # Get result_params table
    df = model.result_params

    # Filter intercept if needed
    if not include_intercept:
        # Match various intercept naming conventions
        df = df.filter(
            ~pl.col("term")
            .str.to_lowercase()
            .is_in(["intercept", "(intercept)", "const", "_cons"])
        )

    # Select standard columns (handle different model schemas)
    cols = df.columns
    result_cols = [pl.col("term"), pl.col("estimate")]

    if "se" in cols:
        result_cols.append(pl.col("se"))
    else:
        result_cols.append(pl.lit(None).cast(pl.Float64).alias("se"))

    if "ci_lower" in cols:
        result_cols.append(pl.col("ci_lower"))
    else:
        result_cols.append(pl.lit(None).cast(pl.Float64).alias("ci_lower"))

    if "ci_upper" in cols:
        result_cols.append(pl.col("ci_upper"))
    else:
        result_cols.append(pl.lit(None).cast(pl.Float64).alias("ci_upper"))

    if "p_value" in cols:
        result_cols.append(pl.col("p_value"))
    else:
        result_cols.append(pl.lit(None).cast(pl.Float64).alias("p_value"))

    return df.select(result_cols)


def _extract_ranef(
    model: BaseModel,
    group: str | None = None,
    term: str | None = None,
) -> pl.DataFrame:
    """Extract random effects from mixed model."""
    # Check model has random effects
    if not hasattr(model, "varying"):
        raise TypeError(
            f"{type(model).__name__} has no varying effects. Use which='params' instead."
        )

    # Get varying effects DataFrame
    ranef_df = model.varying

    # Filter by group if specified
    if group is not None:
        if "group_factor" in ranef_df.columns:
            ranef_df = ranef_df.filter(pl.col("group_factor") == group)
        elif group not in ranef_df.columns:
            raise ValueError(
                f"Group factor '{group}' not found. Available: {ranef_df.columns}"
            )

    # Filter by term if specified
    if term is not None:
        if "re_term" in ranef_df.columns:
            ranef_df = ranef_df.filter(pl.col("re_term") == term)

    # Standardize column names for plotting
    # ranef typically has: group_id, group_factor, Intercept, slope_name, etc.
    # We need to reshape to long format: term, estimate, ...

    # Check if already in long format
    if "estimate" in ranef_df.columns:
        return ranef_df

    # Otherwise, reshape from wide to long
    # Identify RE columns (not group_id, group_factor)
    group_cols = ["group_id", "group_factor"]
    re_cols = [c for c in ranef_df.columns if c not in group_cols]

    if not re_cols:
        raise ValueError("No random effect columns found in ranef DataFrame")

    # Melt to long format
    # Create term column from group_id and RE name
    rows = []
    for row in ranef_df.iter_rows(named=True):
        group_id = row.get("group_id", "")
        group_factor = row.get("group_factor", "")
        for re_col in re_cols:
            rows.append(
                {
                    "term": f"{group_id}",
                    "estimate": row[re_col],
                    "se": None,  # BLUP SEs require conditional vcov (see: washington-ckyb)
                    "ci_lower": None,
                    "ci_upper": None,
                    "p_value": None,
                    "group_factor": group_factor,
                    "re_term": re_col,
                }
            )

    return pl.DataFrame(rows)


def extract_residuals(
    model: BaseModel,
    residual_type: str | None = None,
) -> dict[str, np.ndarray]:
    """Extract residual diagnostics from a fitted model.

    Args:
        model: Fitted bossanova model.
        residual_type: Type of residuals. If None, uses model default.
            - "response": Raw residuals (y - fitted)
            - "pearson": Pearson residuals
            - "deviance": Deviance residuals (GLM)

    Returns:
        Dictionary with:
            - fitted: Fitted values
            - residuals: Residual values
            - std_resid: Standardized residuals
            - leverage: Hat/leverage values
            - cooksd: Cook's distance

    Raises:
        RuntimeError: If model is not fitted.
    """
    if not model.is_fitted:
        raise RuntimeError("Model must be fitted before extracting residuals")

    # Default residual type based on model
    if residual_type is None:
        if hasattr(model, "_family"):
            # GLM/GLMER: use deviance residuals
            residual_type = "deviance"
        else:
            # LM/LMER: use response residuals
            residual_type = "response"

    # Extract from model - try augmented data columns first, then model attributes
    data = model.data

    # Get fitted values
    if "fitted" in data.columns:
        fitted = data["fitted"].to_numpy()
    elif hasattr(model, "fitted"):
        fitted = np.asarray(model.fitted)
    else:
        raise ValueError("Model has no fitted values available")

    result = {"fitted": fitted}

    # Get residuals (type-specific for GLM)
    if residual_type == "response":
        if "resid" in data.columns:
            result["residuals"] = data["resid"].to_numpy()
        elif hasattr(model, "residuals"):
            result["residuals"] = np.asarray(model.residuals)
        else:
            # Compute from y and fitted
            y_col = model._formula.split("~")[0].strip()
            y = data[y_col].to_numpy()
            result["residuals"] = y - fitted
    elif residual_type == "pearson" and "pearson_resid" in data.columns:
        result["residuals"] = data["pearson_resid"].to_numpy()
    elif residual_type == "deviance" and "deviance_resid" in data.columns:
        result["residuals"] = data["deviance_resid"].to_numpy()
    else:
        # Fallback to response residuals
        if "resid" in data.columns:
            result["residuals"] = data["resid"].to_numpy()
        elif hasattr(model, "residuals"):
            result["residuals"] = np.asarray(model.residuals)
        else:
            y_col = model._formula.split("~")[0].strip()
            y = data[y_col].to_numpy()
            result["residuals"] = y - fitted

    # Standardized residuals
    if "std_resid" in data.columns:
        result["std_resid"] = data["std_resid"].to_numpy()
    else:
        # Compute if not available
        resid = result["residuals"]
        std = np.std(resid)
        result["std_resid"] = resid / std if std > 0 else resid

    n = len(result["fitted"])

    # Leverage
    if "hat" in data.columns:
        result["leverage"] = data["hat"].to_numpy()
    else:
        result["leverage"] = np.zeros(n)

    # Cook's distance
    if "cooksd" in data.columns:
        result["cooksd"] = data["cooksd"].to_numpy()
    else:
        result["cooksd"] = np.zeros(n)

    return result


# =============================================================================
# Plot Helpers
# =============================================================================


def setup_ax(
    ax: Axes | None,
    figsize: tuple[float, float] | None = None,
) -> tuple[Figure, Axes]:
    """Set up matplotlib axes, creating figure if needed.

    Args:
        ax: Existing axes or None to create new figure.
        figsize: Figure size if creating new figure.

    Returns:
        Tuple of (figure, axes).
    """
    import matplotlib.pyplot as plt

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    return fig, ax


def add_ref_line(
    ax: Axes,
    value: float = 0.0,
    orientation: Literal["horizontal", "vertical"] = "vertical",
) -> None:
    """Add reference line to axes.

    Args:
        ax: Matplotlib axes.
        value: Position of reference line.
        orientation: Line orientation.
    """
    style = BOSSANOVA_STYLE

    if orientation == "vertical":
        ax.axvline(
            value,
            color=style["ref_line_color"],
            linestyle=style["ref_line_style"],
            linewidth=style["ref_line_width"],
            zorder=0,
        )
    else:
        ax.axhline(
            value,
            color=style["ref_line_color"],
            linestyle=style["ref_line_style"],
            linewidth=style["ref_line_width"],
            zorder=0,
        )


def format_pvalue_annotation(p: float) -> str:
    """Format p-value for plot annotation.

    Args:
        p: P-value.

    Returns:
        Formatted string with significance stars.
    """
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    elif p < 0.1:
        return "."
    return ""


# =============================================================================
# FacetGrid Helpers
# =============================================================================


def build_facetgrid_kwargs(
    data: pl.DataFrame,
    height: float,
    aspect: float,
    col_wrap: int | None = None,
    hue: str | None = None,
    col: str | None = None,
    row: str | None = None,
    palette: str | None = None,
    sharex: bool = True,
    sharey: bool = True,
) -> dict[str, Any]:
    """Build standardized kwargs dict for FacetGrid/relplot/catplot.

    Creates a kwargs dictionary with consistent parameter handling for
    seaborn grid-based plotting functions.

    Args:
        data: Polars DataFrame to plot (passed directly to seaborn).
        height: Height of each facet in inches.
        aspect: Aspect ratio of each facet (width = height * aspect).
        col_wrap: Wrap column facets after this many columns. Ignored if row is set.
        hue: Variable name for color grouping.
        col: Variable name for column faceting.
        row: Variable name for row faceting.
        palette: Color palette name (uses BOSSANOVA_STYLE default if hue set but no palette).
        sharex: Share x-axis across facets.
        sharey: Share y-axis across facets.

    Returns:
        Dictionary of kwargs ready for sns.FacetGrid, relplot, or catplot.

    Examples:
        >>> kwargs = build_facetgrid_kwargs(df, height=4.0, aspect=1.2, col="group")
        >>> g = sns.FacetGrid(**kwargs)
    """
    kwargs: dict[str, Any] = {
        "data": data,
        "height": height,
        "aspect": aspect,
        "sharex": sharex,
        "sharey": sharey,
    }

    if col is not None:
        kwargs["col"] = col
    if row is not None:
        kwargs["row"] = row
    if col_wrap is not None and row is None:
        kwargs["col_wrap"] = col_wrap
    if hue is not None:
        kwargs["hue"] = hue
        kwargs["palette"] = palette or BOSSANOVA_STYLE["palette"]

    return kwargs


def finalize_facetgrid(
    g: Any,  # sns.FacetGrid or sns.PairGrid
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
) -> Any:
    """Apply standard styling and layout to a FacetGrid.

    Applies consistent bossanova styling: despine, tight_layout, and title.

    Args:
        g: Seaborn FacetGrid or PairGrid object.
        title: Optional title to add above the plot.
        xlabel: Optional x-axis label.
        ylabel: Optional y-axis label.

    Returns:
        The same FacetGrid/PairGrid object (for chaining).

    Examples:
        >>> g = sns.FacetGrid(df, col="group")
        >>> g.map_dataframe(my_plot_func)
        >>> finalize_facetgrid(g, title="My Plot", xlabel="X", ylabel="Y")
    """
    import seaborn as sns

    style = BOSSANOVA_STYLE

    if xlabel or ylabel:
        g.set_axis_labels(xlabel or "", ylabel or "")

    if title:
        g.figure.suptitle(title, y=1.02, fontsize=style["title_size"])

    sns.despine()
    g.tight_layout()

    return g
