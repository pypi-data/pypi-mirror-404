"""Residual diagnostic plots for bossanova models.

This module provides plot_resid() for visualizing residual diagnostics
in a faceted grid similar to R's plot(lm_model).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np
import polars as pl

from bossanova.viz._core import (
    BOSSANOVA_STYLE,
    extract_residuals,
    finalize_facetgrid,
)

if TYPE_CHECKING:
    import seaborn as sns

    from bossanova.models.base import BaseModel

__all__ = ["plot_resid"]

# Diagnostic panel names in display order
DIAGNOSTIC_NAMES = [
    "Residuals vs Fitted",
    "Normal Q-Q",
    "Scale-Location",
    "Residuals vs Leverage",
]


def plot_resid(
    model: BaseModel,
    *,
    which: list[int] | Literal["all"] = "all",
    residual_type: Literal["response", "pearson", "deviance"] | None = None,
    lowess: bool = True,
    label_outliers: int | float = 3,
    # FacetGrid params
    height: float = 3.5,
    aspect: float = 1.0,
    col_wrap: int = 2,
    palette: str | None = None,
) -> sns.FacetGrid:
    """Plot residual diagnostics as a faceted grid.

    Creates a diagnostic plot grid similar to R's plot(lm_model):

    1. **Residuals vs Fitted**: Check linearity and heteroscedasticity.
       Points should be randomly scattered around 0.
    2. **Q-Q Plot**: Check normality of residuals.
       Points should follow the diagonal line.
    3. **Scale-Location**: Check homoscedasticity (constant variance).
       Points should be randomly scattered with constant spread.
    4. **Residuals vs Leverage**: Identify influential observations.
       Points outside Cook's D contours may be influential.

    Args:
        model: A fitted bossanova model (lm, glm, lmer, glmer).
        which: Which panels to show.
            - "all": All 4 panels (default).
            - List of integers [1,2,3,4]: Specific panels.
        residual_type: Type of residuals to use.
            - None: Auto-select based on model type.
            - "response": Raw residuals (y - fitted).
            - "pearson": Pearson residuals.
            - "deviance": Deviance residuals (GLM/GLMER).
        lowess: Add lowess smoothing line to applicable panels.
        label_outliers: Label points with standardized residuals exceeding
            this threshold. Set to 0 to disable.
        height: Height of each facet in inches.
        aspect: Aspect ratio of each facet.
        col_wrap: Number of columns before wrapping.
        palette: Color palette name (default: BOSSANOVA_STYLE palette).

    Returns:
        Seaborn FacetGrid containing the diagnostic panels.

    Raises:
        RuntimeError: If model is not fitted.

    Examples:
        >>> from bossanova import lm, viz
        >>> model = lm("mpg ~ wt + hp", data=mtcars).fit()
        >>> viz.plot_resid(model)

        >>> # Show only Q-Q plot
        >>> viz.plot_resid(model, which=[2])

        >>> # GLM with deviance residuals
        >>> model = glm("am ~ wt + hp", data=mtcars, family="binomial").fit()
        >>> viz.plot_resid(model, residual_type="deviance")

    Note:
        This function returns a FacetGrid. To access the underlying Figure,
        use `g.figure`. Migration from previous API:
        `fig = model.plot_resid()` → `g = model.plot_resid(); fig = g.figure`
    """
    import seaborn as sns
    from scipy import stats

    if not model.is_fitted:
        raise RuntimeError("Model must be fitted before plotting residuals")

    style = BOSSANOVA_STYLE
    if palette is None:
        palette = style["palette"]

    # Extract residual data
    resid_data = extract_residuals(model, residual_type=residual_type)

    fitted = resid_data["fitted"]
    residuals = resid_data["residuals"]
    std_resid = resid_data["std_resid"]
    leverage = resid_data["leverage"]
    cooksd = resid_data["cooksd"]

    n = len(fitted)

    # Determine which panels to plot
    if which == "all":
        panels = [1, 2, 3, 4]
    else:
        panels = which

    # Build long-format DataFrame for each selected diagnostic
    panels_data = []

    # Panel 1: Residuals vs Fitted
    if 1 in panels:
        panel1_df = pl.DataFrame(
            {
                "diagnostic": ["Residuals vs Fitted"] * n,
                "x": fitted,
                "y": residuals,
                "std_resid": std_resid,
                "leverage": leverage,
                "cooksd": cooksd if cooksd is not None else np.zeros(n),
                "idx": list(range(n)),
            }
        )
        panels_data.append(panel1_df)

    # Panel 2: Q-Q
    if 2 in panels:
        sorted_idx = np.argsort(std_resid)
        sorted_resid = std_resid[sorted_idx]
        theoretical = stats.norm.ppf(np.arange(1, n + 1) / (n + 1))

        panel2_df = pl.DataFrame(
            {
                "diagnostic": ["Normal Q-Q"] * n,
                "x": theoretical,
                "y": sorted_resid,
                "std_resid": sorted_resid,
                "leverage": leverage[sorted_idx],
                "cooksd": (cooksd if cooksd is not None else np.zeros(n))[sorted_idx],
                "idx": sorted_idx.tolist(),
            }
        )
        panels_data.append(panel2_df)

    # Panel 3: Scale-Location
    if 3 in panels:
        sqrt_abs_resid = np.sqrt(np.abs(std_resid))
        panel3_df = pl.DataFrame(
            {
                "diagnostic": ["Scale-Location"] * n,
                "x": fitted,
                "y": sqrt_abs_resid,
                "std_resid": std_resid,
                "leverage": leverage,
                "cooksd": cooksd if cooksd is not None else np.zeros(n),
                "idx": list(range(n)),
            }
        )
        panels_data.append(panel3_df)

    # Panel 4: Residuals vs Leverage
    if 4 in panels:
        panel4_df = pl.DataFrame(
            {
                "diagnostic": ["Residuals vs Leverage"] * n,
                "x": leverage,
                "y": std_resid,
                "std_resid": std_resid,
                "leverage": leverage,
                "cooksd": cooksd if cooksd is not None else np.zeros(n),
                "idx": list(range(n)),
            }
        )
        panels_data.append(panel4_df)

    # Concatenate all panels
    plot_df = pl.concat(panels_data, how="diagonal")

    # Get selected diagnostic names in order
    selected_names = [DIAGNOSTIC_NAMES[i - 1] for i in panels]

    # Create FacetGrid
    g = sns.FacetGrid(
        plot_df,
        col="diagnostic",
        col_wrap=col_wrap if len(panels) > 1 else None,
        height=height,
        aspect=aspect,
        sharex=False,
        sharey=False,
    )

    # Map the diagnostic panel drawing
    g.map_dataframe(
        _draw_diagnostic_panel,
        lowess=lowess,
        label_outliers=label_outliers,
        style=style,
        n_obs=n,
    )

    # Set axis labels per facet (they differ per diagnostic)
    _set_facet_labels(g, selected_names, style)

    finalize_facetgrid(g, title="Residual Diagnostics")

    return g


def _draw_diagnostic_panel(
    data,  # Polars or pandas DataFrame from FacetGrid
    *,
    lowess: bool,
    label_outliers: float,
    style: dict,
    n_obs: int,
    **kwargs,
) -> None:
    """Draw the appropriate diagnostic panel based on data."""
    import matplotlib.pyplot as plt

    ax = plt.gca()

    # Get diagnostic name from data
    diag_col = np.asarray(data["diagnostic"])
    if len(diag_col) == 0:
        return
    diagnostic = str(diag_col[0])

    x = np.asarray(data["x"])
    y = np.asarray(data["y"])
    std_resid = np.asarray(data["std_resid"])
    idx = np.asarray(data["idx"]).astype(int)

    if diagnostic == "Residuals vs Fitted":
        _draw_resid_vs_fitted(ax, x, y, std_resid, idx, lowess, label_outliers, style)
    elif diagnostic == "Normal Q-Q":
        _draw_qq(ax, x, y, std_resid, idx, label_outliers, style)
    elif diagnostic == "Scale-Location":
        _draw_scale_location(ax, x, y, std_resid, idx, lowess, label_outliers, style)
    elif diagnostic == "Residuals vs Leverage":
        leverage = np.asarray(data["leverage"])
        cooksd = np.asarray(data["cooksd"])
        _draw_resid_vs_leverage(
            ax, x, y, std_resid, leverage, cooksd, idx, label_outliers, style, n_obs
        )


def _draw_resid_vs_fitted(
    ax,
    fitted: np.ndarray,
    residuals: np.ndarray,
    std_resid: np.ndarray,
    idx: np.ndarray,
    lowess: bool,
    label_outliers: float,
    style: dict,
) -> None:
    """Panel 1: Residuals vs Fitted values."""
    ax.scatter(
        fitted,
        residuals,
        alpha=0.6,
        s=style["point_size"] * 0.5,
        edgecolors="none",
    )

    # Reference line at 0
    ax.axhline(0, color=style["ref_line_color"], linestyle=style["ref_line_style"])

    # LOWESS smoothing
    if lowess:
        _add_lowess(ax, fitted, residuals, style)

    # Label outliers
    if label_outliers > 0:
        _label_outliers(ax, fitted, residuals, std_resid, idx, label_outliers)


def _draw_qq(
    ax,
    theoretical: np.ndarray,
    sorted_resid: np.ndarray,
    std_resid: np.ndarray,
    idx: np.ndarray,
    label_outliers: float,
    style: dict,
) -> None:
    """Panel 2: Q-Q plot of standardized residuals."""
    ax.scatter(
        theoretical,
        sorted_resid,
        alpha=0.6,
        s=style["point_size"] * 0.5,
        edgecolors="none",
    )

    # Reference line (45-degree through quartiles)
    q1_t, q3_t = np.percentile(theoretical, [25, 75])
    q1_s, q3_s = np.percentile(sorted_resid, [25, 75])
    slope = (q3_s - q1_s) / (q3_t - q1_t) if q3_t != q1_t else 1
    intercept = q1_s - slope * q1_t

    xlim = ax.get_xlim()
    x_line = np.array(xlim)
    y_line = intercept + slope * x_line
    ax.plot(
        x_line,
        y_line,
        color=style["ref_line_color"],
        linestyle=style["ref_line_style"],
    )

    # Label outliers
    if label_outliers > 0:
        outlier_mask = np.abs(sorted_resid) > label_outliers
        for t, s, i in zip(
            theoretical[outlier_mask], sorted_resid[outlier_mask], idx[outlier_mask]
        ):
            ax.annotate(
                str(i),
                (t, s),
                fontsize=style["font_size"] - 2,
                alpha=0.7,
            )


def _draw_scale_location(
    ax,
    fitted: np.ndarray,
    sqrt_abs_resid: np.ndarray,
    std_resid: np.ndarray,
    idx: np.ndarray,
    lowess: bool,
    label_outliers: float,
    style: dict,
) -> None:
    """Panel 3: Scale-Location plot (sqrt of |standardized residuals|)."""
    ax.scatter(
        fitted,
        sqrt_abs_resid,
        alpha=0.6,
        s=style["point_size"] * 0.5,
        edgecolors="none",
    )

    # LOWESS smoothing
    if lowess:
        _add_lowess(ax, fitted, sqrt_abs_resid, style)

    # Label outliers
    if label_outliers > 0:
        _label_outliers(ax, fitted, sqrt_abs_resid, std_resid, idx, label_outliers)


def _draw_resid_vs_leverage(
    ax,
    leverage: np.ndarray,
    std_resid: np.ndarray,
    std_resid_full: np.ndarray,
    leverage_full: np.ndarray,
    cooksd: np.ndarray,
    idx: np.ndarray,
    label_outliers: float,
    style: dict,
    n_obs: int,
) -> None:
    """Panel 4: Standardized residuals vs Leverage."""
    # Color by Cook's distance if available
    has_cooksd = cooksd is not None and np.any(cooksd != 0)

    if has_cooksd:
        ax.scatter(
            leverage,
            std_resid,
            c=cooksd,
            cmap="Reds",
            alpha=0.6,
            s=style["point_size"] * 0.5,
            edgecolors="none",
        )
    else:
        ax.scatter(
            leverage,
            std_resid,
            alpha=0.6,
            s=style["point_size"] * 0.5,
            edgecolors="none",
        )

    # Reference lines
    ax.axhline(0, color=style["ref_line_color"], linestyle=style["ref_line_style"])

    # Cook's distance contours (0.5 and 1.0)
    if leverage.any():
        h_range = np.linspace(0.001, max(leverage) * 1.1, 100)
        for d_val in [0.5, 1.0]:
            try:
                r_upper = np.sqrt(d_val * n_obs / h_range)
                r_lower = -r_upper
                ax.plot(
                    h_range,
                    r_upper,
                    color="red",
                    linestyle=":",
                    alpha=0.5,
                    label=f"Cook's D = {d_val}" if d_val == 0.5 else None,
                )
                ax.plot(h_range, r_lower, color="red", linestyle=":", alpha=0.5)
            except (ValueError, RuntimeWarning):
                pass

    # Label outliers (high leverage or high residuals)
    if label_outliers > 0:
        outlier_mask = np.abs(std_resid) > label_outliers
        leverage_threshold = 2 * np.mean(leverage)
        high_leverage = leverage > leverage_threshold
        combined_mask = outlier_mask | high_leverage

        for lev, res, i in zip(
            leverage[combined_mask], std_resid[combined_mask], idx[combined_mask]
        ):
            ax.annotate(
                str(i),
                (lev, res),
                fontsize=style["font_size"] - 2,
                alpha=0.7,
            )


def _set_facet_labels(g, diagnostic_names: list[str], style: dict) -> None:
    """Set axis labels for each facet based on diagnostic type."""
    label_map = {
        "Residuals vs Fitted": ("Fitted values", "Residuals"),
        "Normal Q-Q": ("Theoretical Quantiles", "Standardized Residuals"),
        "Scale-Location": ("Fitted values", "√|Standardized Residuals|"),
        "Residuals vs Leverage": ("Leverage", "Standardized Residuals"),
    }

    for ax, diag in zip(g.axes.flat, diagnostic_names):
        if diag in label_map:
            xlabel, ylabel = label_map[diag]
            ax.set_xlabel(xlabel, fontsize=style["label_size"])
            ax.set_ylabel(ylabel, fontsize=style["label_size"])


def _add_lowess(
    ax,
    x: np.ndarray,
    y: np.ndarray,
    style: dict,
) -> None:
    """Add LOWESS smoothing line to axes."""
    try:
        from statsmodels.nonparametric.smoothers_lowess import lowess as sm_lowess

        # Sort by x for proper line
        sorted_idx = np.argsort(x)
        x_sorted = x[sorted_idx]
        y_sorted = y[sorted_idx]

        # Compute LOWESS
        smoothed = sm_lowess(y_sorted, x_sorted, frac=0.6)

        ax.plot(
            smoothed[:, 0],
            smoothed[:, 1],
            color="red",
            linewidth=style["line_width"],
            alpha=0.8,
        )
    except ImportError:
        # statsmodels not available, skip lowess
        pass


def _label_outliers(
    ax,
    x: np.ndarray,
    y: np.ndarray,
    std_resid: np.ndarray,
    idx: np.ndarray,
    threshold: float,
) -> None:
    """Label outlier points by index."""
    outlier_mask = np.abs(std_resid) > threshold

    for xi, yi, i in zip(x[outlier_mask], y[outlier_mask], idx[outlier_mask]):
        ax.annotate(
            str(i),
            (xi, yi),
            fontsize=8,
            alpha=0.7,
        )
