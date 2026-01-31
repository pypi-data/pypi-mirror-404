"""DAG visualization using matplotlib.

Renders causal DAGs with clean, minimal styling matching the bossanova
aesthetic. Supports exposure/outcome highlighting, bidirected edges,
and causal role-based positioning.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np

from bossanova.viz.layout import LayoutConfig, dag_layout

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

__all__ = ["DAG_STYLE", "plot_dag", "default_dag_edges"]


# =============================================================================
# Style Constants
# =============================================================================

DAG_STYLE = {
    # Node styling
    "node_width": 0.8,
    "node_height": 0.4,
    "node_fontsize": 10,
    "node_fontfamily": "sans-serif",
    # Node colors by role
    "exposure_fill": "#e3f2fd",
    "exposure_edge": "#1976d2",
    "outcome_fill": "#fff3e0",
    "outcome_edge": "#f57c00",
    "default_fill": "#fafafa",
    "default_edge": "#666666",
    # Edge styling
    "edge_color": "#666666",
    "edge_width": 1.5,
    "arrow_size": 0.15,
    # Bidirected edge styling
    "bidir_color": "#999999",
    "bidir_width": 1.2,
    "bidir_style": "--",
    # Text
    "text_color": "#333333",
}


# =============================================================================
# Main Plot Function
# =============================================================================


def plot_dag(
    edges: list[tuple[str, str]],
    bidirected: list[tuple[str, str]] | None = None,
    exposure: str | None = None,
    outcome: str | None = None,
    title: str | None = None,
    ax: Axes | None = None,
    figsize: tuple[float, float] | None = None,
    legend: bool = True,
) -> Figure:
    """Plot a causal DAG using matplotlib.

    Creates a clean visualization with causal-aware node positioning:
    - Exposure on left, outcome on right
    - Confounders above the main causal path
    - Mediators between exposure and outcome
    - Other nodes below

    Args:
        edges: Directed edges as (source, target) tuples.
        bidirected: Bidirected edges (unmeasured confounding).
        exposure: Exposure variable (highlighted blue).
        outcome: Outcome variable (highlighted orange).
        title: Optional plot title.
        ax: Matplotlib axes. If None, creates new figure.
        figsize: Figure size if creating new figure.
        legend: Whether to show color legend (default True).

    Returns:
        Matplotlib Figure object.

    Examples:
        >>> # Simple confounding DAG
        >>> fig = plot_dag(
        ...     edges=[("Z", "X"), ("Z", "Y"), ("X", "Y")],
        ...     exposure="X",
        ...     outcome="Y",
        ... )

        >>> # Mediation
        >>> fig = plot_dag(
        ...     edges=[("X", "M"), ("M", "Y"), ("X", "Y")],
        ...     exposure="X",
        ...     outcome="Y",
        ... )

        >>> # Unmeasured confounding
        >>> fig = plot_dag(
        ...     edges=[("X", "Y")],
        ...     bidirected=[("X", "Y")],
        ...     exposure="X",
        ...     outcome="Y",
        ... )
    """
    import matplotlib.pyplot as plt

    bidirected = bidirected or []

    # Compute layout
    config = LayoutConfig(
        node_width=DAG_STYLE["node_width"],
        node_height=DAG_STYLE["node_height"],
        h_spacing=1.5,
        v_spacing=1.2,
    )
    positions = dag_layout(edges, bidirected, exposure, outcome, config)

    if not positions:
        # Empty DAG
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize or (4, 2))
        else:
            fig = ax.get_figure()
        ax.text(0.5, 0.5, "Empty DAG", ha="center", va="center", fontsize=12)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        return fig

    # Create figure if needed
    if ax is None:
        if figsize is None:
            figsize = _compute_dag_figsize(positions)
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    # Draw edges first (behind nodes)
    for src, dst in edges:
        if src in positions and dst in positions:
            _draw_directed_edge(ax, positions[src], positions[dst], config)

    for a, b in bidirected:
        if a in positions and b in positions:
            _draw_bidirected_edge(ax, positions[a], positions[b], config)

    # Draw nodes
    for name, (x, y) in positions.items():
        role = "default"
        if name == exposure:
            role = "exposure"
        elif name == outcome:
            role = "outcome"
        _draw_node(ax, x, y, name, role, config)

    # Configure axes
    _configure_axes(ax, positions, config, title)

    # Add legend
    if legend and (exposure or outcome or bidirected):
        _draw_dag_legend(ax, exposure, outcome, bool(bidirected))

    return fig


def _compute_dag_figsize(
    positions: dict[str, tuple[float, float]],
) -> tuple[float, float]:
    """Compute appropriate figure size based on node positions."""
    if not positions:
        return (4, 3)

    xs = [x for x, y in positions.values()]
    ys = [y for x, y in positions.values()]

    x_range = max(xs) - min(xs) + 2
    y_range = max(ys) - min(ys) + 1.5

    # Scale to reasonable figure size
    width = max(4, min(10, x_range * 1.5))
    height = max(2.5, min(8, y_range * 1.2))

    return (width, height)


def _draw_node(
    ax: Axes,
    x: float,
    y: float,
    label: str,
    role: Literal["exposure", "outcome", "default"],
    config: LayoutConfig,
) -> None:
    """Draw a single node with rounded rectangle."""
    from matplotlib.patches import FancyBboxPatch

    # Get colors based on role
    if role == "exposure":
        fill = DAG_STYLE["exposure_fill"]
        edge = DAG_STYLE["exposure_edge"]
        lw = 2.0
    elif role == "outcome":
        fill = DAG_STYLE["outcome_fill"]
        edge = DAG_STYLE["outcome_edge"]
        lw = 2.0
    else:
        fill = DAG_STYLE["default_fill"]
        edge = DAG_STYLE["default_edge"]
        lw = 1.5

    # Adjust width based on label length
    min_width = config.node_width
    text_width = len(label) * 0.08 + 0.3
    width = max(min_width, text_width)
    height = config.node_height

    # Create rounded rectangle
    box = FancyBboxPatch(
        (x - width / 2, y - height / 2),
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.15",
        facecolor=fill,
        edgecolor=edge,
        linewidth=lw,
        zorder=2,
    )
    ax.add_patch(box)

    # Add label
    ax.text(
        x,
        y,
        label,
        ha="center",
        va="center",
        fontsize=DAG_STYLE["node_fontsize"],
        fontfamily=DAG_STYLE["node_fontfamily"],
        color=DAG_STYLE["text_color"],
        zorder=3,
    )


def _draw_directed_edge(
    ax: Axes,
    pos1: tuple[float, float],
    pos2: tuple[float, float],
    config: LayoutConfig,
) -> None:
    """Draw a directed edge with arrowhead."""
    from matplotlib.patches import FancyArrowPatch

    x1, y1 = pos1
    x2, y2 = pos2

    # Compute direction
    dx = x2 - x1
    dy = y2 - y1
    dist = np.sqrt(dx**2 + dy**2)

    if dist < 0.01:
        return  # Skip self-loops

    # Normalize direction
    ux, uy = dx / dist, dy / dist

    # Adjust start and end points to node boundaries
    # For simplicity, use ellipse approximation
    half_w = config.node_width / 2 + 0.05
    half_h = config.node_height / 2 + 0.05

    # Start point: move from center toward target
    start_x = x1 + ux * half_w
    start_y = y1 + uy * half_h

    # End point: move from center toward source, plus arrow offset
    arrow_offset = 0.1
    end_x = x2 - ux * (half_w + arrow_offset)
    end_y = y2 - uy * (half_h + arrow_offset)

    # Draw arrow
    arrow = FancyArrowPatch(
        (start_x, start_y),
        (end_x, end_y),
        arrowstyle="-|>",
        mutation_scale=15,
        color=DAG_STYLE["edge_color"],
        linewidth=DAG_STYLE["edge_width"],
        zorder=1,
    )
    ax.add_patch(arrow)


def _draw_bidirected_edge(
    ax: Axes,
    pos1: tuple[float, float],
    pos2: tuple[float, float],
    config: LayoutConfig,
) -> None:
    """Draw a bidirected (curved dashed) edge."""
    from matplotlib.patches import FancyArrowPatch

    x1, y1 = pos1
    x2, y2 = pos2

    # Curved arc above both nodes
    arrow = FancyArrowPatch(
        (x1, y1 - config.node_height / 2 - 0.05),
        (x2, y2 - config.node_height / 2 - 0.05),
        arrowstyle="<|-|>",
        mutation_scale=12,
        connectionstyle="arc3,rad=-0.4",
        color=DAG_STYLE["bidir_color"],
        linewidth=DAG_STYLE["bidir_width"],
        linestyle=DAG_STYLE["bidir_style"],
        zorder=1,
    )
    ax.add_patch(arrow)


def _configure_axes(
    ax: Axes,
    positions: dict[str, tuple[float, float]],
    config: LayoutConfig,
    title: str | None,
) -> None:
    """Configure axes appearance."""
    if not positions:
        ax.axis("off")
        return

    xs = [x for x, y in positions.values()]
    ys = [y for x, y in positions.values()]

    # Set limits with padding
    pad = 0.8
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)

    # Remove axes
    ax.axis("off")

    # Add title if provided
    if title:
        ax.set_title(title, fontsize=12, fontweight="medium")


# =============================================================================
# Legend
# =============================================================================


def _draw_dag_legend(
    ax: Axes,
    exposure: str | None,
    outcome: str | None,
    has_bidirected: bool,
) -> None:
    """Draw a compact legend inside the plot area."""
    # Build legend text
    parts = []
    if outcome:
        parts.append("\u25a0 outcome")  # filled square
    if exposure:
        parts.append("\u25a1 exposure")  # hollow square
    if has_bidirected:
        parts.append("-- unmeasured")

    if not parts:
        return

    # Add text at bottom-center using axes transform (0-1 coordinates)
    legend_text = "  |  ".join(parts)
    ax.text(
        0.5,
        0.02,
        legend_text,
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=7,
        color="#888888",
        fontfamily="sans-serif",
        bbox=dict(
            boxstyle="round,pad=0.3", facecolor="white", edgecolor="#dddddd", alpha=0.9
        ),
    )


# =============================================================================
# Convenience Functions
# =============================================================================


def default_dag_edges(
    predictors: list[str],
    outcome: str,
) -> list[tuple[str, str]]:
    """Generate default DAG edges for regression.

    The default causal interpretation of regression: all predictors
    directly cause the outcome, with no edges among predictors.

    Args:
        predictors: List of predictor names (excluding intercept).
        outcome: Outcome variable name.

    Returns:
        List of (predictor, outcome) edges.
    """
    return [(p, outcome) for p in predictors if p != "intercept"]
