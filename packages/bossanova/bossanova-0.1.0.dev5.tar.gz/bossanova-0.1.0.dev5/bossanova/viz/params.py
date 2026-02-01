"""Parameter forest plot for bossanova models.

This module provides plot_params() for visualizing fixed effect estimates
with confidence intervals in a forest plot style.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np

from bossanova.viz._core import (
    BOSSANOVA_STYLE,
    build_facetgrid_kwargs,
    extract_params,
    finalize_facetgrid,
    format_pvalue_annotation,
)

if TYPE_CHECKING:
    import seaborn as sns

    from bossanova.models.base import BaseModel

__all__ = ["plot_params"]


def plot_params(
    model: BaseModel,
    *,
    include_intercept: bool = False,
    effect_sizes: bool = False,
    sort: bool | Literal["ascending", "descending"] = False,
    show_values: bool = False,
    show_pvalue: bool = False,
    ref_line: float = 0.0,
    # FacetGrid params
    height: float = 0.4,
    aspect: float = 2.5,
    col_wrap: int | None = None,
    palette: str | None = None,
) -> sns.FacetGrid:
    """Plot fixed effect estimates as a forest plot.

    Creates a horizontal dot-whisker plot showing parameter estimates with
    confidence intervals. Uses Seaborn FacetGrid for consistent styling.

    Args:
        model: A fitted bossanova model (lm, glm, lmer, glmer).
        include_intercept: Include intercept term.
        effect_sizes: Plot Cohen's d instead of raw estimates.
        sort: Sort parameters by estimate magnitude.
            - False: Keep original order.
            - True or "descending": Largest to smallest.
            - "ascending": Smallest to largest.
        show_values: Annotate points with estimate values.
        show_pvalue: Add significance stars based on p-values.
        ref_line: Position of reference line (default 0.0).
        height: Height per parameter in inches (default 0.4).
        aspect: Aspect ratio (default 2.5).
        palette: Color palette name (default: BOSSANOVA_STYLE palette).

    Returns:
        Seaborn FacetGrid containing the plot.

    Raises:
        RuntimeError: If model is not fitted.

    Examples:
        >>> from bossanova import lm, viz, load_dataset
        >>> mtcars = load_dataset("mtcars")
        >>> model = lm("mpg ~ wt + hp + cyl", data=mtcars).fit()
        >>> viz.plot_params(model)  # Fixed effects forest plot
        >>> viz.plot_params(model, sort=True, show_pvalue=True)

    See Also:
        plot_ranef: Random effects caterpillar plot for mixed models.
    """
    import seaborn as sns

    if not model.is_fitted:
        raise RuntimeError("Model must be fitted before plotting parameters")

    style = BOSSANOVA_STYLE
    if palette is None:
        palette = style["palette"]

    # Extract fixed effects
    df = extract_params(
        model,
        which="fixef",
        include_intercept=include_intercept,
        effect_sizes=effect_sizes,
    )

    # Sort if requested
    if sort:
        ascending = sort == "ascending"
        df = df.sort("estimate", descending=not ascending)

    # Calculate figure size based on number of parameters
    n_params = len(df)
    fig_height = max(3.0, n_params * height)

    # Build FacetGrid kwargs - pass Polars DataFrame directly
    facet_kwargs = build_facetgrid_kwargs(
        data=df,
        height=fig_height,
        aspect=aspect / fig_height * 4,  # Adjust aspect for varying heights
        col_wrap=col_wrap,
        palette=palette,
    )

    # Create FacetGrid with pointplot-like appearance
    g = sns.FacetGrid(**facet_kwargs)

    # Map the forest plot drawing
    g.map_dataframe(
        _draw_forest_panel,
        style=style,
        show_values=show_values,
        show_pvalue=show_pvalue,
        ref_line=ref_line,
        effect_sizes=effect_sizes,
    )

    # Labels and title
    xlabel = "Cohen's d" if effect_sizes else "Estimate"
    title = "Effect Sizes (Cohen's d)" if effect_sizes else "Fixed Effects"
    finalize_facetgrid(g, title=title, xlabel=xlabel, ylabel="")

    return g


def _draw_forest_panel(
    data,  # Polars or pandas DataFrame from FacetGrid
    *,
    style: dict,
    show_values: bool,
    show_pvalue: bool,
    ref_line: float,
    effect_sizes: bool,
    **kwargs,
) -> None:
    """Draw forest plot on current axes."""
    import matplotlib.pyplot as plt

    ax = plt.gca()

    terms = list(data["term"])
    estimates = np.asarray(data["estimate"])
    n_params = len(terms)
    y_positions = np.arange(n_params)

    # Get confidence intervals if available
    ci_lower = np.asarray(data["ci_lower"]) if "ci_lower" in data.columns else None
    ci_upper = np.asarray(data["ci_upper"]) if "ci_upper" in data.columns else None
    p_values = np.asarray(data["p_value"]) if "p_value" in data.columns else None

    # Plot error bars (confidence intervals)
    if ci_lower is not None and ci_upper is not None:
        valid_ci = ~(np.isnan(ci_lower) | np.isnan(ci_upper))
        if valid_ci.any():
            xerr_lower = estimates[valid_ci] - ci_lower[valid_ci]
            xerr_upper = ci_upper[valid_ci] - estimates[valid_ci]
            ax.errorbar(
                estimates[valid_ci],
                y_positions[valid_ci],
                xerr=[xerr_lower, xerr_upper],
                fmt="none",
                ecolor=style["ref_line_color"],
                elinewidth=style["line_width"],
                capsize=style["capsize"],
                zorder=1,
            )

    # Plot point estimates
    ax.scatter(
        estimates,
        y_positions,
        s=style["point_size"],
        marker=style["point_marker"],
        edgecolors=style["point_edgecolor"],
        linewidths=style["point_linewidth"],
        zorder=2,
        c="C0",
    )

    # Add reference line
    ax.axvline(
        ref_line,
        color=style["ref_line_color"],
        linestyle=style["ref_line_style"],
        linewidth=style["ref_line_width"],
        zorder=0,
    )

    # Set y-axis labels
    ax.set_yticks(y_positions)
    ax.set_yticklabels(terms)
    ax.invert_yaxis()

    # Add value annotations
    if show_values:
        for est, y in zip(estimates, y_positions):
            ax.annotate(
                f"{est:.2f}",
                (est, y),
                xytext=(5, 0),
                textcoords="offset points",
                fontsize=style["font_size"] - 1,
                va="center",
            )

    # Add p-value stars
    if show_pvalue and p_values is not None:
        for est, y, p in zip(estimates, y_positions, p_values):
            if p is not None and not np.isnan(p):
                stars = format_pvalue_annotation(p)
                if stars:
                    ax.annotate(
                        stars,
                        (est, y),
                        xytext=(-5, 0),
                        textcoords="offset points",
                        fontsize=style["font_size"],
                        va="center",
                        ha="right",
                    )

    # Add grid
    ax.grid(axis="x", alpha=style["grid_alpha"], linestyle=style["grid_style"])
