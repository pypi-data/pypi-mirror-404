"""Marginal means visualization for bossanova models.

This module provides plot_mee() for visualizing marginal estimated effects
(MEEs) from model.mee() output.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np
import polars as pl

from bossanova.viz._core import BOSSANOVA_STYLE

if TYPE_CHECKING:
    import seaborn as sns

    from bossanova.models.base import BaseModel

__all__ = ["plot_mee"]


def plot_mee(
    model: BaseModel,
    specs: str,
    *,
    hue: str | None = None,
    col: str | None = None,
    row: str | None = None,
    at: dict | None = None,
    units: Literal["link", "data"] = "data",
    contrasts: str | None = None,
    conf_int: float = 0.95,
    height: float = 4.0,
    aspect: float = 1.2,
    palette: str | None = None,
) -> sns.FacetGrid:
    """Plot marginal estimated effects.

    Visualizes MEEs from model.mee() as points with confidence interval
    error bars. Supports grouping via `hue=` and faceting via `col=`/`row=`.

    Args:
        model: A fitted bossanova model (lm, glm, lmer, glmer).
        specs: Factor(s) to compute MEEs for, e.g., "cyl" or "cyl:am".
        hue: Color encoding variable for grouping (dodged on same plot).
        col: Column faceting variable.
        row: Row faceting variable.
        at: Dictionary of covariate values to hold fixed.
            E.g., `at={"hp": 150}` computes MEEs at hp=150.
        units: Units for predictions.
            - "data": Back-transformed scale (default).
            - "link": Link scale (GLM/GLMER).
        contrasts: Type of contrasts to compute and annotate.
            - None: No contrasts (default).
            - "pairwise": All pairwise comparisons.
            - "revpairwise": Reversed pairwise.
            Adds significance stars (*, **, ***) above compared pairs.
        conf_int: Confidence level (default 0.95).
        height: Height of each facet in inches.
        aspect: Aspect ratio of each facet.
        palette: Color palette name (default: BOSSANOVA_STYLE palette).

    Returns:
        Seaborn FacetGrid containing the plot.

    Raises:
        RuntimeError: If model is not fitted.
        AttributeError: If model doesn't have mee method.

    Examples:
        >>> from bossanova import lm, viz, load_dataset
        >>> mtcars = load_dataset("mtcars")
        >>> model = lm("mpg ~ factor(cyl) + hp", data=mtcars).fit()
        >>> viz.plot_mee(model, "cyl")  # MEEs for each cyl level

        >>> # With hue grouping
        >>> model = lm("mpg ~ factor(cyl) + factor(am)", data=mtcars).fit()
        >>> viz.plot_mee(model, "cyl", hue="am")

        >>> # With contrasts
        >>> viz.plot_mee(model, "cyl", contrasts="pairwise")

    See Also:
        plot_predict: Marginal predictions across predictor range.
        plot_params: Fixed effects forest plot.
    """
    import seaborn as sns

    if not model.is_fitted:
        raise RuntimeError("Model must be fitted before plotting MEEs")

    if not hasattr(model, "mee"):
        raise AttributeError(f"{type(model).__name__} does not have mee method")

    style = BOSSANOVA_STYLE
    if palette is None:
        palette = style["palette"]

    # Build spec string with optional stratification via | operator
    full_specs = f"{specs} | {hue}" if hue else specs

    # Get MEEs from model using new .mee().infer() pattern
    model.mee(full_specs, at=at, units=units).infer(conf_int=conf_int)
    emm_df = model.result_mee.to_dataframe()

    # Handle hue case - add _hue_level column for plotting
    if hue is not None and hue in emm_df.columns:
        emm_df = emm_df.with_columns(pl.col(hue).alias("_hue_level"))

    # Get contrasts if requested
    contrasts_df = None
    if contrasts is not None:
        model.mee(specs, contrasts=contrasts).infer(conf_int=conf_int)
        contrasts_df = model.result_mee.to_dataframe()

    # Determine x-axis categories
    primary_factor = specs.split(":")[0].strip()

    # New mee() format uses "term" and "level" columns
    if "level" in emm_df.columns:
        categories = emm_df["level"].unique().to_list()
        primary_factor = "level"
    elif primary_factor in emm_df.columns:
        categories = emm_df[primary_factor].unique().to_list()
    else:
        # Try to find the factor column
        non_stat_cols = [
            c
            for c in emm_df.columns
            if c
            not in [
                "estimate",
                "se",
                "df",
                "t_value",
                "p_value",
                "ci_lower",
                "ci_upper",
                "term",
                "level",
                "_hue_level",
            ]
        ]
        if non_stat_cols:
            primary_factor = non_stat_cols[0]
            categories = emm_df[primary_factor].unique().to_list()
        else:
            raise ValueError("Could not identify factor column in MEE output")

    # Pass Polars DataFrame directly to Seaborn
    plot_df = emm_df

    # Add faceting columns if specified
    if col is not None and col not in plot_df.columns:
        raise ValueError(f"Column '{col}' not found in data")
    if row is not None and row not in plot_df.columns:
        raise ValueError(f"Row '{row}' not found in data")

    # Create FacetGrid
    facet_kwargs = {
        "data": plot_df,
        "height": height,
        "aspect": aspect,
    }
    if col is not None:
        facet_kwargs["col"] = col
    if row is not None:
        facet_kwargs["row"] = row

    g = sns.FacetGrid(**facet_kwargs)

    # Map the MEE plot drawing
    g.map_dataframe(
        _draw_mee_panel,
        primary_factor=primary_factor,
        categories=categories,
        hue=hue,
        style=style,
        palette=palette,
    )

    # Add contrast annotations if requested
    if contrasts_df is not None:
        g.map_dataframe(
            _add_contrast_annotations,
            contrasts_df=contrasts_df,
            categories=categories,
            style=style,
        )

    # Labels
    g.set_axis_labels(primary_factor, "Estimated Marginal Mean")

    title = f"Estimated Marginal Means: {specs}"
    if hue:
        title += f" by {hue}"
    g.figure.suptitle(title, y=1.02, fontsize=style["title_size"])

    # Add legend if using hue
    if hue is not None and "_hue_level" in plot_df.columns:
        g.add_legend(title=hue)

    # Clean up
    sns.despine()
    g.tight_layout()

    return g


def _draw_mee_panel(
    data,  # Polars or pandas DataFrame from FacetGrid
    *,
    primary_factor: str,
    categories: list,
    hue: str | None,
    style: dict,
    palette: str,
    **kwargs,
) -> None:
    """Draw MEE points and error bars on current axes."""
    import matplotlib.pyplot as plt

    ax = plt.gca()
    x_positions = np.arange(len(categories))

    if hue is not None and "_hue_level" in data.columns:
        _plot_with_hue(ax, data, primary_factor, categories, x_positions, hue, style)
    else:
        _plot_simple(ax, data, primary_factor, categories, x_positions, style)


def _plot_simple(
    ax,
    data,  # Polars or pandas DataFrame from FacetGrid
    factor: str,
    categories: list,
    x_positions: np.ndarray,
    style: dict,
) -> None:
    """Plot EMMs without grouping - simple points + error bars."""
    # Extract columns as arrays for cross-compatible access
    factor_col = np.asarray(data[factor])
    estimate_col = np.asarray(data["estimate"])
    ci_lower_col = np.asarray(data["ci_lower"])
    ci_upper_col = np.asarray(data["ci_upper"])

    emmeans = []
    ci_lowers = []
    ci_uppers = []

    for cat in categories:
        # Find matching row
        mask = factor_col == cat
        if mask.any():
            idx = np.where(mask)[0][0]
            emmeans.append(estimate_col[idx])
            ci_lowers.append(ci_lower_col[idx])
            ci_uppers.append(ci_upper_col[idx])
        else:
            emmeans.append(np.nan)
            ci_lowers.append(np.nan)
            ci_uppers.append(np.nan)

    emmeans = np.array(emmeans)
    ci_lowers = np.array(ci_lowers)
    ci_uppers = np.array(ci_uppers)

    # Plot error bars
    yerr = [emmeans - ci_lowers, ci_uppers - emmeans]
    ax.errorbar(
        x_positions,
        emmeans,
        yerr=yerr,
        fmt="o",
        markersize=8,
        capsize=5,
        color="C0",
        ecolor=style["ref_line_color"],
        elinewidth=style["line_width"],
    )

    ax.set_xticks(x_positions)
    ax.set_xticklabels([str(c) for c in categories])


def _plot_with_hue(
    ax,
    data,  # Polars or pandas DataFrame from FacetGrid
    factor: str,
    categories: list,
    x_positions: np.ndarray,
    hue: str,
    style: dict,
) -> None:
    """Plot EMMs with hue grouping - dodged points + error bars."""
    import matplotlib.pyplot as plt

    # Extract columns as arrays for cross-compatible access
    hue_col = np.asarray(data["_hue_level"])
    factor_col = np.asarray(data[factor])
    estimate_col = np.asarray(data["estimate"])
    ci_lower_col = np.asarray(data["ci_lower"])
    ci_upper_col = np.asarray(data["ci_upper"])

    hue_levels = sorted(set(hue_col))
    n_groups = len(hue_levels)
    colors = plt.cm.tab10(np.linspace(0, 1, n_groups))

    # Calculate dodge offsets
    dodge = 0.2
    total_width = dodge * (n_groups - 1)
    offsets = np.linspace(-total_width / 2, total_width / 2, n_groups)

    for i, hue_level in enumerate(hue_levels):
        hue_mask = hue_col == hue_level

        emmeans = []
        ci_lowers = []
        ci_uppers = []

        for cat in categories:
            # Find row matching both hue level and category
            mask = hue_mask & (factor_col == cat)
            if mask.any():
                idx = np.where(mask)[0][0]
                emmeans.append(estimate_col[idx])
                ci_lowers.append(ci_lower_col[idx])
                ci_uppers.append(ci_upper_col[idx])
            else:
                emmeans.append(np.nan)
                ci_lowers.append(np.nan)
                ci_uppers.append(np.nan)

        emmeans = np.array(emmeans)
        ci_lowers = np.array(ci_lowers)
        ci_uppers = np.array(ci_uppers)

        yerr = [emmeans - ci_lowers, ci_uppers - emmeans]
        ax.errorbar(
            x_positions + offsets[i],
            emmeans,
            yerr=yerr,
            fmt="o",
            markersize=8,
            capsize=4,
            color=colors[i],
            ecolor=colors[i],
            elinewidth=style["line_width"],
            label=f"{hue}={hue_level}",
        )

    ax.set_xticks(x_positions)
    ax.set_xticklabels([str(c) for c in categories])
    ax.legend(title=hue, fontsize=style["font_size"] - 1)


def _add_contrast_annotations(
    data,  # Polars or pandas DataFrame from FacetGrid (unused here)
    *,
    contrasts_df,
    categories: list,
    style: dict,
    **kwargs,
) -> None:
    """Add significance stars above compared pairs."""
    import matplotlib.pyplot as plt

    ax = plt.gca()

    # Get y-axis limits for positioning
    y_min, y_max = ax.get_ylim()
    y_range = y_max - y_min

    annotation_height = y_max + 0.05 * y_range
    height_increment = 0.08 * y_range

    for i, row in enumerate(contrasts_df.iter_rows(named=True)):
        contrast_name = row["contrast"]
        p_value = row["p_value"]

        # Determine significance stars
        if p_value < 0.001:
            stars = "***"
        elif p_value < 0.01:
            stars = "**"
        elif p_value < 0.05:
            stars = "*"
        else:
            continue  # Don't annotate non-significant

        # Parse contrast name (e.g., "6 - 4" or "8 - 4")
        parts = contrast_name.split(" - ")
        if len(parts) != 2:
            continue

        try:
            level1, level2 = parts[0].strip(), parts[1].strip()
            x1 = _find_category_index(categories, level1)
            x2 = _find_category_index(categories, level2)

            if x1 is None or x2 is None:
                continue

            # Draw bracket and stars
            y = annotation_height + i * height_increment
            ax.plot(
                [x1, x1, x2, x2],
                [y - 0.02 * y_range, y, y, y - 0.02 * y_range],
                color="black",
                linewidth=1,
            )
            ax.text(
                (x1 + x2) / 2,
                y + 0.01 * y_range,
                stars,
                ha="center",
                va="bottom",
                fontsize=style["font_size"],
            )

        except (ValueError, IndexError):
            continue

    # Adjust y-axis to accommodate annotations
    if len(contrasts_df) > 0:
        new_y_max = (
            annotation_height + len(contrasts_df) * height_increment + 0.05 * y_range
        )
        ax.set_ylim(y_min, new_y_max)


def _find_category_index(categories: list, value: str) -> int | None:
    """Find index of a category, handling type conversion."""
    for i, cat in enumerate(categories):
        if str(cat) == value:
            return i
        try:
            if int(cat) == int(value):
                return i
        except (ValueError, TypeError):
            pass
    return None
