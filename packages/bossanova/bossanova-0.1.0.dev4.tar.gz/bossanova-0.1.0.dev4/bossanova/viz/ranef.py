"""Random effects caterpillar plot for bossanova mixed models.

This module provides plot_ranef() for visualizing random effect estimates
(BLUPs) with optional confidence intervals in a caterpillar plot style.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np
import polars as pl

from bossanova.viz._core import (
    BOSSANOVA_STYLE,
    build_facetgrid_kwargs,
    finalize_facetgrid,
)

if TYPE_CHECKING:
    import seaborn as sns

    from bossanova.models.base import BaseModel

__all__ = ["plot_ranef"]


def plot_ranef(
    model: BaseModel,
    *,
    group: str | None = None,
    term: str | None = None,
    col: str | None = None,
    show: int | list[str] | Literal["all", "top", "bottom", "quartile"] = "all",
    sort: bool | Literal["ascending", "descending"] = False,
    show_values: bool = False,
    ref_line: float = 0.0,
    # FacetGrid params
    height: float = 4.0,
    aspect: float = 1.0,
    col_wrap: int | None = None,
    palette: str | None = None,
) -> sns.FacetGrid:
    """Plot random effects as a caterpillar plot.

    Creates a horizontal dot-whisker plot showing random effect estimates
    (BLUPs) for each group level. Supports faceting by random effect term.

    Args:
        model: A fitted mixed-effects model (lmer, glmer).
        group: Which grouping factor to show. None shows first grouping factor.
        term: Which random effect term to show (e.g., "Intercept", "Days").
            None shows all terms with faceting.
        col: Column faceting variable. If None and multiple RE terms exist,
            facets by term.
        show: Which group levels to display.
            - "all": Show all levels (default).
            - int: First N levels in model order.
            - list[str]: Specific level names.
            - "top": Top quartile by magnitude.
            - "bottom": Bottom quartile by magnitude.
            - "quartile": Top + bottom quartiles (most extreme).
        sort: Sort levels by estimate magnitude.
            - False: Keep original order.
            - True or "descending": Largest to smallest.
            - "ascending": Smallest to largest.
        show_values: Annotate points with estimate values.
        ref_line: Position of reference line (default 0.0).
        height: Height of each facet in inches.
        aspect: Aspect ratio of each facet.
        palette: Color palette name (default: BOSSANOVA_STYLE palette).

    Returns:
        Seaborn FacetGrid containing the plot.

    Raises:
        RuntimeError: If model is not fitted.
        TypeError: If model has no random effects.
        ValueError: If specified group or term not found.

    Examples:
        >>> from bossanova import lmer, viz, load_dataset
        >>> sleep = load_dataset("sleep")
        >>> model = lmer("Reaction ~ Days + (Days|Subject)", data=sleep).fit()

        >>> # All RE terms, faceted
        >>> viz.plot_ranef(model)

        >>> # Just intercepts
        >>> viz.plot_ranef(model, term="Intercept")

        >>> # Extreme levels only
        >>> viz.plot_ranef(model, show="quartile", sort=True)

    See Also:
        plot_params: Fixed effects forest plot.
        plot_predict: Marginal predictions with BLUPs overlay.
    """
    import seaborn as sns

    if not model.is_fitted:
        raise RuntimeError("Model must be fitted before plotting random effects")

    if not hasattr(model, "varying"):
        raise TypeError(
            f"{type(model).__name__} has no varying effects. "
            "Use plot_params() for fixed effects."
        )

    style = BOSSANOVA_STYLE
    if palette is None:
        palette = style["palette"]

    # Get varying effects DataFrame
    ranef_df = model.varying

    # Filter by group if specified
    if group is not None:
        if "group" in ranef_df.columns:
            ranef_df = ranef_df.filter(pl.col("group") == group)
        else:
            raise ValueError(f"Group column not found. Available: {ranef_df.columns}")

    # Identify RE term columns (not group/level metadata)
    meta_cols = ["group", "level"]
    re_terms = [c for c in ranef_df.columns if c not in meta_cols]

    if not re_terms:
        raise ValueError("No random effect terms found in model")

    # Filter to specific term if requested
    if term is not None:
        if term not in re_terms:
            raise ValueError(f"Term '{term}' not found. Available: {re_terms}")
        re_terms = [term]

    # Get levels and apply show filter
    levels = ranef_df["level"].to_list()
    levels = _filter_levels(ranef_df, levels, re_terms, show)

    # Filter dataframe to selected levels
    ranef_df = ranef_df.filter(pl.col("level").is_in(levels))

    # Sort levels if requested
    if sort:
        first_term = re_terms[0]
        if sort == "ascending":
            ranef_df = ranef_df.sort(first_term)
        else:
            ranef_df = ranef_df.sort(first_term, descending=True)
        levels = ranef_df["level"].to_list()

    # Reshape to long format for FacetGrid
    # Create: level, term, estimate columns
    rows = []
    for row in ranef_df.iter_rows(named=True):
        level = row["level"]
        for re_term in re_terms:
            rows.append(
                {
                    "level": level,
                    "term": re_term,
                    "estimate": row[re_term],
                }
            )

    # Build Polars DataFrame - order is preserved from DataFrame construction
    plot_df = pl.DataFrame(rows)

    # Determine faceting
    n_terms = len(re_terms)
    facet_col = "term" if n_terms > 1 and col is None else col

    # Build FacetGrid kwargs - pass Polars DataFrame directly
    facet_kwargs = build_facetgrid_kwargs(
        data=plot_df,
        height=height,
        aspect=aspect,
        col=facet_col,
        col_wrap=col_wrap,
        palette=palette,
        sharex=False,
        sharey=True,
    )

    # Create FacetGrid
    g = sns.FacetGrid(**facet_kwargs)

    # Map the caterpillar plot drawing
    g.map_dataframe(
        _draw_caterpillar_panel,
        style=style,
        show_values=show_values,
        ref_line=ref_line,
    )

    # Finalize
    finalize_facetgrid(g, title="Random Effects", xlabel="Estimate", ylabel="")

    return g


def _draw_caterpillar_panel(
    data,  # Polars or pandas DataFrame from FacetGrid
    *,
    style: dict,
    show_values: bool,
    ref_line: float,
    **kwargs,
) -> None:
    """Draw caterpillar plot on current axes."""
    import matplotlib.pyplot as plt

    ax = plt.gca()

    levels = list(data["level"])
    estimates = np.asarray(data["estimate"])
    n_levels = len(levels)
    y_positions = np.arange(n_levels)

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
    ax.set_yticklabels(levels)
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

    # Add grid
    ax.grid(axis="x", alpha=style["grid_alpha"], linestyle=style["grid_style"])


def _filter_levels(
    ranef_df: pl.DataFrame,
    levels: list[str],
    re_terms: list[str],
    show: int | list[str] | str,
) -> list[str]:
    """Filter levels based on show parameter."""
    if show == "all":
        return levels

    if isinstance(show, int):
        return levels[:show]

    if isinstance(show, list):
        # Filter to specified levels
        return [lv for lv in levels if lv in show]

    # Quartile-based filtering
    # Compute magnitude as sum of |estimates| across all terms
    magnitudes = np.zeros(len(levels))
    for re_term in re_terms:
        magnitudes += np.abs(ranef_df[re_term].to_numpy())

    n_quartile = max(1, len(levels) // 4)
    sorted_indices = np.argsort(magnitudes)

    if show == "top":
        # Top quartile (highest magnitude)
        selected_indices = sorted_indices[-n_quartile:]
    elif show == "bottom":
        # Bottom quartile (lowest magnitude)
        selected_indices = sorted_indices[:n_quartile]
    elif show == "quartile":
        # Top + bottom quartiles
        selected_indices = np.concatenate(
            [sorted_indices[:n_quartile], sorted_indices[-n_quartile:]]
        )
    else:
        raise ValueError(
            f"Invalid show value: {show}. "
            "Use 'all', int, list of levels, 'top', 'bottom', or 'quartile'."
        )

    return [levels[i] for i in sorted(selected_indices)]
