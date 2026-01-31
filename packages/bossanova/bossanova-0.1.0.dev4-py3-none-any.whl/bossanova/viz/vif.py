"""VIF (Variance Inflation Factor) visualization for bossanova models.

This module provides plot_vif() for visualizing multicollinearity in the
design matrix via correlation heatmap and VIF statistics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from bossanova.viz._core import BOSSANOVA_STYLE, setup_ax

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from bossanova.models.base import BaseModel

__all__ = ["plot_vif"]


# =============================================================================
# VIF Computation
# =============================================================================


def _compute_vif(X: np.ndarray, X_names: list[str]) -> dict[str, float]:
    """Compute Variance Inflation Factor for each predictor.

    VIF measures multicollinearity. For predictor j:
    VIF_j = 1 / (1 - R²_j)

    where R²_j is from regressing X_j on all other predictors.

    Args:
        X: Design matrix (n_obs, n_predictors).
        X_names: Column names for the design matrix.

    Returns:
        Dictionary mapping predictor names to VIF values.
        Intercept is excluded (VIF undefined).
    """
    vif_values: dict[str, float] = {}

    # Find non-intercept columns
    non_intercept_idx = [i for i, name in enumerate(X_names) if name != "Intercept"]

    if len(non_intercept_idx) < 2:
        # Need at least 2 predictors for VIF
        for i in non_intercept_idx:
            vif_values[X_names[i]] = 1.0
        return vif_values

    # Extract non-intercept columns
    X_pred = X[:, non_intercept_idx]
    pred_names = [X_names[i] for i in non_intercept_idx]

    for j, name in enumerate(pred_names):
        # Regress X_j on all other predictors
        y = X_pred[:, j]
        X_others = np.delete(X_pred, j, axis=1)

        # Add intercept for the regression
        X_others_with_intercept = np.column_stack([np.ones(len(y)), X_others])

        # Solve least squares
        try:
            beta, residuals, rank, s = np.linalg.lstsq(
                X_others_with_intercept, y, rcond=None
            )
            y_pred = X_others_with_intercept @ beta

            # Compute R²
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)

            if ss_tot == 0:
                # Constant predictor
                r_squared = 0.0
            else:
                r_squared = 1 - ss_res / ss_tot

            # VIF = 1 / (1 - R²)
            if r_squared >= 1.0:
                vif = np.inf
            else:
                vif = 1.0 / (1.0 - r_squared)

        except np.linalg.LinAlgError:
            vif = np.inf

        vif_values[name] = vif

    return vif_values


def _compute_correlation_matrix(
    X: np.ndarray, X_names: list[str]
) -> tuple[np.ndarray, list[str]]:
    """Compute correlation matrix for design matrix predictors.

    Args:
        X: Design matrix (n_obs, n_predictors).
        X_names: Column names for the design matrix.

    Returns:
        Tuple of (correlation_matrix, predictor_names).
        Intercept is excluded.
    """
    # Find non-intercept columns
    non_intercept_idx = [i for i, name in enumerate(X_names) if name != "Intercept"]
    X_pred = X[:, non_intercept_idx]
    pred_names = [X_names[i] for i in non_intercept_idx]

    # Compute correlation matrix
    corr_matrix = np.corrcoef(X_pred, rowvar=False)

    # Handle single predictor case
    if corr_matrix.ndim == 0:
        corr_matrix = np.array([[1.0]])

    return corr_matrix, pred_names


# =============================================================================
# Main Plot Function
# =============================================================================


def plot_vif(
    model: BaseModel,
    *,
    cmap: str | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
) -> Figure | Axes:
    """Plot VIF diagnostics as correlation heatmap.

    Visualizes multicollinearity in the design matrix:
    - Correlation heatmap between predictors
    - VIF (Variance Inflation Factor) for each predictor
    - CI increase factor (√VIF) showing confidence interval inflation

    VIF interpretation:
    - VIF = 1: No multicollinearity
    - VIF = 1-5: Moderate (generally acceptable)
    - VIF > 5: High multicollinearity (concerning)
    - VIF > 10: Severe multicollinearity (problematic)

    Works on unfitted models since the design matrix is built at initialization.

    For pairwise scatter plots including the response variable, use
    `plot_relationships()` instead.

    Args:
        model: A bossanova model (lm, glm, lmer, glmer). Can be fitted or unfitted.
        cmap: Matplotlib colormap name. Default "coolwarm".
        figsize: Figure size as (width, height). Auto-computed if None.
        ax: Existing matplotlib Axes to plot on.

    Returns:
        Figure if creating new figure, Axes if ax was provided.

    Examples:
        >>> from bossanova import lm, load_dataset
        >>> cars = load_dataset("mtcars")
        >>> model = lm("mpg ~ wt + hp + disp", data=cars)
        >>> model.plot_vif()  # Correlation heatmap with VIF stats
    """
    # Get design matrix
    X = model._X
    X_names = model._X_names

    # Find non-intercept columns
    non_intercept_idx = [i for i, name in enumerate(X_names) if name != "Intercept"]
    pred_names = [X_names[i] for i in non_intercept_idx]

    n_predictors = len(pred_names)

    if n_predictors == 0:
        raise ValueError("Model has no predictors (only intercept)")

    # Compute VIF
    vif_values = _compute_vif(X, X_names)
    style = BOSSANOVA_STYLE

    # Build VIF info text (one variable per line)
    vif_lines = []
    for name in pred_names:
        vif = vif_values.get(name, 1.0)
        ci_increase = np.sqrt(vif)
        if np.isinf(vif):
            vif_lines.append(f"{name}: VIF=∞")
        else:
            vif_lines.append(f"{name}: VIF={vif:.1f}, CI inc: {ci_increase:.1f}x")
    vif_text = "\n".join(vif_lines)

    return _plot_vif_heatmap(
        X,
        X_names,
        pred_names,
        vif_values,
        vif_text,
        n_predictors,
        style,
        cmap,
        figsize,
        ax,
    )


def _plot_vif_heatmap(
    X: np.ndarray,
    X_names: list[str],
    pred_names: list[str],
    vif_values: dict[str, float],
    vif_text: str,
    n_predictors: int,
    style: dict,
    cmap: str | None,
    figsize: tuple[float, float] | None,
    ax: Axes | None,
) -> Figure | Axes:
    """Render VIF as correlation heatmap."""
    # Compute correlation matrix
    corr_matrix, _ = _compute_correlation_matrix(X, X_names)

    # Compute figure size
    if figsize is None:
        size = max(5, min(12, 2 + n_predictors * 0.8))
        figsize = (size, size)

    # Set up axes
    user_provided_ax = ax is not None
    fig, ax = setup_ax(ax, figsize=figsize)

    # Colormap: correlations are always -1 to 1, so diverging
    cmap = cmap if cmap is not None else "coolwarm"

    # Plot heatmap
    im = ax.imshow(
        corr_matrix,
        aspect="equal",
        cmap=cmap,
        vmin=-1,
        vmax=1,
        interpolation="nearest",
    )

    # Add colorbar
    cbar = fig.colorbar(im, ax=ax, shrink=0.6, pad=0.02, aspect=30)
    cbar.ax.tick_params(labelsize=style["font_size"] - 1)
    cbar.set_label("Pearson r", rotation=270, labelpad=15, fontsize=style["font_size"])

    # Add correlation values as text annotations
    for i in range(n_predictors):
        for j in range(n_predictors):
            value = corr_matrix[i, j]
            # Use white text on dark backgrounds, black on light
            text_color = "white" if abs(value) > 0.6 else "black"
            ax.text(
                j,
                i,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=style["font_size"] - 2,
                color=text_color,
            )

    # Add faint grid lines
    for i in range(n_predictors + 1):
        ax.axhline(y=i - 0.5, color="white", linewidth=0.5, alpha=0.6)
        ax.axvline(x=i - 0.5, color="white", linewidth=0.5, alpha=0.6)

    # Set tick labels
    ax.set_xticks(np.arange(n_predictors))
    ax.set_yticks(np.arange(n_predictors))
    ax.set_xticklabels(
        pred_names, fontsize=style["font_size"] - 1, rotation=45, ha="right"
    )
    ax.set_yticklabels(pred_names, fontsize=style["font_size"] - 1)

    # Add VIF info above the heatmap (left-aligned)
    ax.text(
        0.0,
        1.02,
        vif_text,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=style["font_size"] - 1,
        color="#666666",
    )

    # Add title (with extra padding for VIF text)
    title_pad = 10 + n_predictors * 12
    ax.set_title("Predictor Correlations", fontsize=style["title_size"], pad=title_pad)

    fig.tight_layout()

    return ax if user_provided_ax else fig
