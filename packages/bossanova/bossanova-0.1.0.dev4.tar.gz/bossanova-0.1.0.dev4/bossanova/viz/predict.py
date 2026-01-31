"""Prediction plots for bossanova models.

This module provides plot_predict() for visualizing marginal predictions
across the range of a predictor variable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np
import polars as pl

from bossanova.viz._core import BOSSANOVA_STYLE

if TYPE_CHECKING:
    import seaborn as sns

    from bossanova.models.base import BaseModel

__all__ = ["plot_predict"]


def plot_predict(
    model: BaseModel,
    term: str,
    *,
    hue: str | None = None,
    col: str | None = None,
    row: str | None = None,
    at: dict | None = None,
    units: Literal["link", "data"] = "data",
    n_points: int = 50,
    interval: Literal["confidence", "prediction"] | None = "confidence",
    conf_int: float = 0.95,
    show_data: bool = False,
    show_rug: bool = False,
    show_blups: bool = False,
    groups: list[str] | None = None,
    # FacetGrid params
    height: float = 4.0,
    aspect: float = 1.2,
    col_wrap: int | None = None,
    palette: str | None = None,
) -> sns.FacetGrid:
    """Plot marginal predictions across a predictor's range.

    Creates a visualization of model predictions varying one predictor while
    holding others at reference values (means for continuous, reference level
    for categorical).

    Args:
        model: A fitted bossanova model (lm, glm, lmer, glmer).
        term: The predictor variable to vary. Can be continuous or categorical.
        hue: Column name for color encoding (creates separate lines per level).
        col: Column name for faceting into columns.
        row: Column name for faceting into rows.
        at: Dictionary of predictor values to hold fixed.
            E.g., `at={"age": 30}` holds age at 30.
        units: Units for predictions.
            - "data": Back-transformed predictions (default).
            - "link": Predictions on link scale (GLM/GLMER).
        n_points: Number of points for continuous predictors.
        interval: Type of interval to show.
            - "confidence": Confidence interval for mean prediction.
            - "prediction": Prediction interval (wider, includes residual var).
            - None: No interval.
        conf_int: Confidence level (default 0.95).
        show_data: Overlay actual data points on the plot.
        show_rug: Add rug plot showing observed data distribution.
        show_blups: For mixed models, show group-specific BLUP lines in addition
            to the population-average fixed effects line.
        groups: For mixed models with show_blups=True, which group levels to show.
            If None, shows all groups (can be crowded for many groups).
        height: Height of each facet in inches.
        aspect: Aspect ratio of each facet.
        palette: Color palette name (default: BOSSANOVA_STYLE palette).

    Returns:
        Seaborn FacetGrid containing the plot.

    Raises:
        RuntimeError: If model is not fitted.
        ValueError: If term is not in the model.

    Examples:
        >>> from bossanova import lm, viz, load_dataset
        >>> mtcars = load_dataset("mtcars")
        >>> model = lm("mpg ~ wt + hp", data=mtcars).fit()
        >>> viz.plot_predict(model, "wt")  # Predictions across wt range

        >>> # Interaction visualization with hue
        >>> model = lm("mpg ~ wt * cyl", data=mtcars).fit()
        >>> viz.plot_predict(model, "wt", hue="cyl")

        >>> # Mixed model with BLUPs
        >>> from bossanova import lmer
        >>> sleep = load_dataset("sleep")
        >>> model = lmer("Reaction ~ Days + (Days|Subject)", data=sleep).fit()
        >>> viz.plot_predict(model, "Days", show_blups=True)

    See Also:
        plot_fit: Observed vs Predicted scatter plot.
        plot_mee: Marginal effects/means visualization.
    """
    import seaborn as sns

    if not model.is_fitted:
        raise RuntimeError("Model must be fitted before plotting predictions")

    style = BOSSANOVA_STYLE
    if palette is None:
        palette = style["palette"]

    # Get original data
    data = model.data

    # Check term exists
    if term not in data.columns:
        raise ValueError(f"Term '{term}' not found in data columns")

    # Determine if term is continuous or categorical
    is_categorical = _is_categorical(data, term)

    # Build prediction data
    plot_df = _build_prediction_data(
        model=model,
        data=data,
        term=term,
        hue=hue,
        col=col,
        row=row,
        at=at,
        n_points=n_points,
        is_categorical=is_categorical,
        pred_type=units,
        interval=interval,
        conf_int=conf_int,
        show_blups=show_blups,
        groups=groups,
    )

    # Create the plot
    if is_categorical:
        g = _plot_categorical(
            plot_df, term, hue, col, row, height, aspect, palette, style
        )
    else:
        g = _plot_continuous(
            plot_df, term, hue, col, row, height, aspect, palette, style, show_blups
        )

    # Add data points if requested
    if show_data:
        g.map_dataframe(_add_data_layer, model=model, term=term, hue=hue, style=style)

    # Add rug if requested
    if show_rug and not is_categorical:
        g.map_dataframe(_add_rug_layer, model=model, term=term)

    # Labels and title
    ylabel = "Predicted" if units == "data" else "Linear Predictor"
    g.set_axis_labels(term, ylabel)

    title = f"Marginal Predictions: {term}"
    g.figure.suptitle(title, y=1.02, fontsize=style["title_size"])

    # Clean up
    sns.despine()
    g.tight_layout()

    return g


def _is_categorical(data: pl.DataFrame, term: str) -> bool:
    """Check if a term is categorical."""
    dtype = data[term].dtype
    return dtype in (pl.Categorical, pl.Utf8, pl.String) or data[term].n_unique() < 10


def _is_mixed_model(model: BaseModel) -> bool:
    """Check if model is a mixed-effects model (lmer/glmer)."""
    model_class = type(model).__name__.lower()
    return model_class in ("lmer", "glmer")


def _get_grouping_factors(model: BaseModel) -> list[str]:
    """Get grouping factor column names for mixed models."""
    if not _is_mixed_model(model):
        return []
    return list(getattr(model, "_group_names", []))


def _build_prediction_data(
    model: BaseModel,
    data: pl.DataFrame,
    term: str,
    hue: str | None,
    col: str | None,
    row: str | None,
    at: dict | None,
    n_points: int,
    is_categorical: bool,
    pred_type: str,
    interval: str | None,
    conf_int: float,
    show_blups: bool,
    groups: list[str] | None,
) -> pl.DataFrame:
    """Build prediction DataFrame with fitted values and intervals."""
    response_col = model._formula.split("~")[0].strip()
    grouping_factors = _get_grouping_factors(model)
    is_mixed = _is_mixed_model(model)

    # Build base prediction grid
    grid_data = {}

    for col_name in data.columns:
        if col_name == response_col:
            continue

        # Handle grouping factors for mixed models
        if col_name in grouping_factors:
            if show_blups and is_mixed:
                # Include grouping factor in grid for BLUP predictions
                all_levels = data[col_name].unique().sort().to_list()
                if groups is not None:
                    # Filter to requested groups
                    grid_data[col_name] = [g for g in all_levels if g in groups]
                else:
                    grid_data[col_name] = all_levels
            continue  # Skip if not showing BLUPs

        if col_name == term:
            # Vary this term
            if is_categorical:
                grid_data[col_name] = data[col_name].unique().sort().to_list()
            else:
                col_data = data[col_name].to_numpy()
                # Use nanmin/nanmax to handle columns with missing values
                grid_data[col_name] = list(
                    np.linspace(np.nanmin(col_data), np.nanmax(col_data), n_points)
                )
        elif at and col_name in at:
            grid_data[col_name] = [at[col_name]]
        elif col_name in [hue, col, row] and col_name is not None:
            # Vary grouping variables
            grid_data[col_name] = data[col_name].unique().sort().to_list()
        else:
            # Use reference value
            dtype = data[col_name].dtype
            if dtype in (pl.Categorical, pl.Utf8, pl.String):
                grid_data[col_name] = [data[col_name].unique().sort().to_list()[0]]
            else:
                grid_data[col_name] = [float(data[col_name].mean())]

    # Create Cartesian product grid
    from itertools import product

    keys = list(grid_data.keys())
    values = [grid_data[k] for k in keys]
    rows = [dict(zip(keys, combo)) for combo in product(*values)]
    pred_grid = pl.DataFrame(rows)

    # Get predictions
    predict_kwargs = {"type": pred_type}

    if is_mixed:
        if show_blups:
            # Include varying effects for BLUP predictions
            predict_kwargs["varying"] = "include"
        else:
            # Population-level only
            predict_kwargs["varying"] = "exclude"

    preds = model.predict(pred_grid, **predict_kwargs)
    preds_array = np.asarray(preds).ravel()  # Ensure 1D array
    result_df = pred_grid.with_columns(pl.Series("fit", preds_array))

    # Get intervals if requested
    if interval:
        try:
            interval_kwargs = {
                **predict_kwargs,
                "interval": interval,
                "conf_int": conf_int,
            }
            pred_df = model.predict(pred_grid, **interval_kwargs)
            if isinstance(pred_df, pl.DataFrame):
                if "ci_lower" in pred_df.columns:
                    result_df = result_df.with_columns(
                        [
                            pl.Series("ci_lower", pred_df["ci_lower"].to_numpy()),
                            pl.Series("ci_upper", pred_df["ci_upper"].to_numpy()),
                        ]
                    )
                elif "lwr" in pred_df.columns:
                    result_df = result_df.with_columns(
                        [
                            pl.Series("lwr", pred_df["lwr"].to_numpy()),
                            pl.Series("upr", pred_df["upr"].to_numpy()),
                        ]
                    )
        except (TypeError, ValueError):
            pass

    # For mixed models with BLUPs, also add population-level predictions
    if show_blups and is_mixed and grouping_factors:
        # Add a column to identify BLUP vs fixed effects
        group_col = grouping_factors[0]
        result_df = result_df.with_columns(
            pl.col(group_col).cast(pl.Utf8).alias("_line_type")
        )

        # Cast grouping factor columns to String for consistent schema
        for gf in grouping_factors:
            result_df = result_df.with_columns(pl.col(gf).cast(pl.Utf8))

        # Get population-level predictions (no random effects)
        pop_grid = pred_grid.drop(grouping_factors)
        pop_grid = pop_grid.unique()

        # Use kwargs to pass varying only to mixed models (type checker can't narrow here)
        pop_kwargs: dict = {"type": pred_type, "varying": "exclude"}
        pop_preds = model.predict(pop_grid, **pop_kwargs)
        pop_preds_array = np.asarray(pop_preds).ravel()  # Ensure 1D array
        pop_df = pop_grid.with_columns(
            [
                pl.Series("fit", pop_preds_array),
                pl.lit("Fixed Effects").alias("_line_type"),
            ]
        )

        # Add placeholder for group column (String type to match result_df)
        for gf in grouping_factors:
            pop_df = pop_df.with_columns(pl.lit("Fixed Effects").alias(gf))

        result_df = pl.concat([result_df, pop_df], how="diagonal")

    return result_df


def _plot_continuous(
    plot_df: pl.DataFrame,
    term: str,
    hue: str | None,
    col: str | None,
    row: str | None,
    height: float,
    aspect: float,
    palette: str,
    style: dict,
    show_blups: bool,
) -> sns.FacetGrid:
    """Create FacetGrid for continuous predictor."""
    import seaborn as sns

    # Determine what to use for hue
    effective_hue = hue
    if show_blups and "_line_type" in plot_df.columns:
        effective_hue = "_line_type"

    # Build relplot kwargs
    relplot_kwargs = {
        "data": plot_df,
        "x": term,
        "y": "fit",
        "kind": "line",
        "col": col,
        "row": row,
        "height": height,
        "aspect": aspect,
        "linewidth": style["line_width"],
    }

    if effective_hue is not None:
        relplot_kwargs["hue"] = effective_hue
        relplot_kwargs["palette"] = palette

    g = sns.relplot(**relplot_kwargs)

    # Add confidence bands if present
    if "ci_lower" in plot_df.columns or "lwr" in plot_df.columns:
        g.map_dataframe(_add_ci_band, term=term, hue=effective_hue, style=style)

    # Style the fixed effects line differently if showing BLUPs
    if show_blups and "_line_type" in plot_df.columns:
        _style_fixed_effects_line(g, plot_df)

    return g


def _plot_categorical(
    plot_df: pl.DataFrame,
    term: str,
    hue: str | None,
    col: str | None,
    row: str | None,
    height: float,
    aspect: float,
    palette: str,
    style: dict,
) -> sns.FacetGrid:
    """Create FacetGrid for categorical predictor."""
    import seaborn as sns

    catplot_kwargs = {
        "data": plot_df,
        "x": term,
        "y": "fit",
        "kind": "point",
        "col": col,
        "row": row,
        "height": height,
        "aspect": aspect,
        "capsize": 0.1,
        "err_kws": {"linewidth": style["line_width"]},
        "markersize": 8,
    }

    if hue is not None:
        catplot_kwargs["hue"] = hue
        catplot_kwargs["palette"] = palette
        catplot_kwargs["dodge"] = True

    # Use errorbar for CI if available
    if "ci_lower" in plot_df.columns or "lwr" in plot_df.columns:
        catplot_kwargs["errorbar"] = None  # We'll add custom error bars

    g = sns.catplot(**catplot_kwargs)

    return g


def _add_ci_band(
    data,  # Polars or pandas DataFrame from FacetGrid
    *,
    term: str,
    hue: str | None,
    style: dict,
    **kwargs,
) -> None:
    """Add confidence/prediction interval band."""
    import matplotlib.pyplot as plt

    ax = plt.gca()

    lower_col = "ci_lower" if "ci_lower" in data.columns else "lwr"
    upper_col = "ci_upper" if "ci_upper" in data.columns else "upr"

    if lower_col not in data.columns:
        return

    if hue is None:
        x = np.asarray(data[term])
        lower = np.asarray(data[lower_col])
        upper = np.asarray(data[upper_col])
        sort_idx = np.argsort(x)
        ax.fill_between(
            x[sort_idx],
            lower[sort_idx],
            upper[sort_idx],
            alpha=style["ci_alpha"],
            color="C0",
        )
    else:
        # Get unique groups - works for both polars and pandas
        hue_col = np.asarray(data[hue])
        groups = list(dict.fromkeys(hue_col))  # unique preserving order
        colors = plt.cm.tab10(np.linspace(0, 1, len(groups)))

        x_all = np.asarray(data[term])
        lower_all = np.asarray(data[lower_col])
        upper_all = np.asarray(data[upper_col])

        for i, group in enumerate(groups):
            mask = hue_col == group
            x = x_all[mask]
            sort_idx = np.argsort(x)

            ax.fill_between(
                x[sort_idx],
                lower_all[mask][sort_idx],
                upper_all[mask][sort_idx],
                alpha=style["ci_alpha"],
                color=colors[i],
            )


def _style_fixed_effects_line(g, plot_df: pl.DataFrame) -> None:
    """Make the fixed effects line thicker/distinct."""
    # This is called after plotting to emphasize the fixed effects line
    # The implementation depends on how seaborn structures the lines
    pass  # For now, the hue coloring distinguishes them


def _add_data_layer(
    data,  # Polars or pandas DataFrame from FacetGrid
    *,
    model: BaseModel,
    term: str,
    hue: str | None,
    style: dict,
    **kwargs,
) -> None:
    """Add actual data points as a layer."""
    import matplotlib.pyplot as plt

    ax = plt.gca()
    original_data = model.data  # Already Polars
    response_col = model._formula.split("~")[0].strip()

    x = np.asarray(original_data[term])
    y = np.asarray(original_data[response_col])

    if hue is None or hue not in original_data.columns:
        ax.scatter(x, y, alpha=0.3, s=style["point_size"] * 0.5, color="gray", zorder=0)
    else:
        hue_col = np.asarray(original_data[hue])
        groups = original_data[hue].unique().to_list()
        colors = plt.cm.tab10(np.linspace(0, 1, len(groups)))

        for i, group in enumerate(groups):
            mask = hue_col == group
            ax.scatter(
                x[mask],
                y[mask],
                alpha=0.3,
                s=style["point_size"] * 0.5,
                color=colors[i],
                zorder=0,
            )


def _add_rug_layer(
    data,  # Polars or pandas DataFrame from FacetGrid
    *,
    model: BaseModel,
    term: str,
    **kwargs,
) -> None:
    """Add rug plot showing observed data distribution."""
    import matplotlib.pyplot as plt

    ax = plt.gca()
    original_data = model.data  # Already Polars
    x = np.asarray(original_data[term])

    ax.plot(
        x,
        np.zeros_like(x),
        "|",
        color="gray",
        alpha=0.5,
        markersize=10,
        transform=ax.get_xaxis_transform(),
        zorder=0,
    )
