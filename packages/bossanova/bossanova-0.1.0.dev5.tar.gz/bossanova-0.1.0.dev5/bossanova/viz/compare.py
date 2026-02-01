"""Multi-model comparison plots for bossanova models.

This module provides plot_compare() for visualizing coefficients across
multiple fitted models side-by-side in a forest plot.
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

__all__ = ["plot_compare"]


def plot_compare(
    models: list[BaseModel],
    *,
    names: list[str] | None = None,
    terms: list[str] | None = None,
    include_intercept: bool = False,
    sort: Literal["none", "magnitude", "alpha"] = "none",
    # FacetGrid params
    height: float = 0.5,
    aspect: float = 2.0,
    col_wrap: int | None = None,
    palette: str | None = None,
) -> sns.FacetGrid:
    """Compare coefficients across multiple fitted models.

    Creates a forest plot showing coefficient estimates and confidence intervals
    for each model, with dodged points on a shared y-axis. Useful for:

    - Coefficient stability across model specifications
    - Comparing nested models
    - Sensitivity analysis visualization

    Args:
        models: List of fitted bossanova models to compare.
        names: Labels for each model. If None, uses "Model 1", "Model 2", etc.
        terms: Terms to include. If None, uses all common terms across models.
            Terms not present in a model are shown as missing.
        include_intercept: Include intercept term (default False).
        sort: How to sort terms on y-axis.
            - "none": Original order from first model (default).
            - "magnitude": Sort by absolute value of first model's estimates.
            - "alpha": Alphabetical order.
        height: Height per term in inches (default 0.5).
        aspect: Aspect ratio (default 2.0).
        palette: Color palette name (default: BOSSANOVA_STYLE palette).

    Returns:
        Seaborn FacetGrid containing the plot.

    Raises:
        ValueError: If models list is empty.
        RuntimeError: If any model is not fitted.

    Examples:
        >>> from bossanova import lm, viz, load_dataset
        >>> mtcars = load_dataset("mtcars")
        >>> model1 = lm("mpg ~ wt + hp", data=mtcars).fit()
        >>> model2 = lm("mpg ~ wt + hp + cyl", data=mtcars).fit()
        >>> model3 = lm("mpg ~ wt * hp", data=mtcars).fit()

        >>> # Compare all three models
        >>> viz.plot_compare([model1, model2, model3],
        ...                  names=["Base", "+cyl", "Interaction"])

        >>> # Compare specific terms
        >>> viz.plot_compare([model1, model2, model3],
        ...                  terms=["wt", "hp"])

    See Also:
        plot_params: Fixed effects forest plot for a single model.
    """
    import seaborn as sns

    # Validate inputs
    if not models:
        raise ValueError("models list cannot be empty")

    for i, model in enumerate(models):
        if not model.is_fitted:
            raise RuntimeError(f"Model {i + 1} must be fitted before plotting")

    # Default names
    if names is None:
        names = [f"Model {i + 1}" for i in range(len(models))]
    elif len(names) != len(models):
        raise ValueError(
            f"Length of names ({len(names)}) must match models ({len(models)})"
        )

    style = BOSSANOVA_STYLE
    if palette is None:
        palette = style["palette"]

    n_models = len(models)

    # Extract coefficients from each model
    model_data = []
    for model in models:
        df = model.result_params

        # Filter intercept if needed
        if not include_intercept:
            df = df.filter(
                ~df["term"]
                .str.to_lowercase()
                .is_in(["intercept", "(intercept)", "const", "_cons"])
            )

        model_data.append(df)

    # Determine terms to plot
    if terms is None:
        # Use union of all terms, in order from first model
        all_terms = []
        seen = set()
        for df in model_data:
            for term in df["term"].to_list():
                if term not in seen:
                    all_terms.append(term)
                    seen.add(term)
        terms = all_terms
    else:
        # Validate specified terms exist in at least one model
        all_model_terms = set()
        for df in model_data:
            all_model_terms.update(df["term"].to_list())

        invalid = set(terms) - all_model_terms
        if invalid:
            raise ValueError(f"Terms not found in any model: {sorted(invalid)}")

    n_terms = len(terms)

    # Sort terms if requested
    if sort == "magnitude":
        first_df = model_data[0]
        term_order = {}
        for row in first_df.iter_rows(named=True):
            term_order[row["term"]] = abs(row["estimate"])
        for t in terms:
            if t not in term_order:
                term_order[t] = 0
        terms = sorted(terms, key=lambda t: term_order.get(t, 0), reverse=True)
    elif sort == "alpha":
        terms = sorted(terms)

    # Build long-format DataFrame for plotting
    rows = []
    for model_idx, (df, name) in enumerate(zip(model_data, names)):
        coef_lookup = {row["term"]: row for row in df.iter_rows(named=True)}

        for term in terms:
            if term in coef_lookup:
                row = coef_lookup[term]
                rows.append(
                    {
                        "term": term,
                        "model": name,
                        "estimate": row["estimate"],
                        "ci_lower": row.get("ci_lower", row["estimate"]),
                        "ci_upper": row.get("ci_upper", row["estimate"]),
                    }
                )

    # Build Polars DataFrame - order is preserved from DataFrame construction
    plot_df = pl.DataFrame(rows)

    # Calculate figure size
    fig_height = max(3.0, n_terms * height)

    # Build FacetGrid kwargs - pass Polars DataFrame directly
    facet_kwargs = build_facetgrid_kwargs(
        data=plot_df,
        height=fig_height,
        aspect=aspect / fig_height * 4,
        col_wrap=col_wrap,
        palette=palette,
    )

    # Create FacetGrid
    g = sns.FacetGrid(**facet_kwargs)

    # Map the comparison plot drawing
    g.map_dataframe(
        _draw_compare_panel,
        terms=terms,
        names=names,
        style=style,
        n_models=n_models,
    )

    # Add legend
    g.add_legend(title="Model")

    # Finalize
    finalize_facetgrid(g, title="Model Comparison", xlabel="Estimate", ylabel="")

    return g


def _draw_compare_panel(
    data,  # Polars or pandas DataFrame from FacetGrid
    *,
    terms: list[str],
    names: list[str],
    style: dict,
    n_models: int,
    **kwargs,
) -> None:
    """Draw model comparison forest plot on current axes."""
    import matplotlib.pyplot as plt

    ax = plt.gca()

    # Color palette
    colors = plt.cm.tab10(np.linspace(0, 1, n_models))

    # Calculate dodge offsets
    dodge = 0.15
    total_width = dodge * (n_models - 1)
    offsets = np.linspace(-total_width / 2, total_width / 2, n_models)

    # Create term -> y position mapping
    term_positions = {term: i for i, term in enumerate(terms)}
    n_terms = len(terms)

    # Convert data to arrays for cross-compatible access (works with polars/pandas)
    model_col = np.asarray(data["model"])
    term_col = list(data["term"])
    estimate_col = np.asarray(data["estimate"])
    ci_lower_col = np.asarray(data["ci_lower"])
    ci_upper_col = np.asarray(data["ci_upper"])

    # Plot each model
    for model_idx, (name, color, offset) in enumerate(zip(names, colors, offsets)):
        # Filter to current model
        mask = model_col == name
        if not mask.any():
            continue

        model_terms = [term_col[i] for i in range(len(term_col)) if mask[i]]
        model_estimates = estimate_col[mask]
        model_lowers = ci_lower_col[mask]
        model_uppers = ci_upper_col[mask]

        y_positions = np.array([term_positions[t] + offset for t in model_terms])

        # Plot error bars
        xerr = np.array(
            [model_estimates - model_lowers, model_uppers - model_estimates]
        )
        ax.errorbar(
            model_estimates,
            y_positions,
            xerr=xerr,
            fmt="o",
            markersize=6,
            capsize=style["capsize"],
            color=color,
            ecolor=color,
            elinewidth=style["line_width"],
            label=name,
        )

    # Reference line at zero
    ax.axvline(
        0.0,
        color=style["ref_line_color"],
        linestyle=style["ref_line_style"],
        linewidth=style["ref_line_width"],
        zorder=0,
    )

    # Y-axis labels
    ax.set_yticks(range(n_terms))
    ax.set_yticklabels(terms)
    ax.invert_yaxis()

    # Grid
    ax.grid(axis="x", alpha=style["grid_alpha"], linestyle=style["grid_style"])

    # Legend
    ax.legend(
        loc="lower right",
        fontsize=style["font_size"] - 1,
        framealpha=0.9,
    )
