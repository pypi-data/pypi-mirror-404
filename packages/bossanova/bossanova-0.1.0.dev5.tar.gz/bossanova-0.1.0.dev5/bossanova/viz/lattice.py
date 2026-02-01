"""Model lattice (Hasse diagram) visualization using matplotlib.

Renders the space of nested models derived from a formula, showing
marginality-respecting model comparisons. The lattice helps users
understand what modeling choices are available.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bossanova.viz.layout import (
    Lattice,
    LatticeNode,
    LayoutConfig,
    generate_lattice,
    lattice_layout,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

__all__ = ["LATTICE_STYLE", "plot_lattice"]


# =============================================================================
# Style Constants
# =============================================================================

LATTICE_STYLE = {
    # Node styling
    "node_fontsize": 8,
    "node_fontfamily": "monospace",
    # Node colors
    "maximal_fill": "#e8f5e9",  # Light green - maximal model
    "maximal_edge": "#388e3c",
    "minimal_fill": "#fce4ec",  # Light pink - intercept only
    "minimal_edge": "#c2185b",
    "default_fill": "#fafafa",
    "default_edge": "#666666",
    "warning_fill": "#fff8e1",  # Light yellow - has warnings
    "warning_edge": "#f57c00",
    # Edge styling
    "edge_color": "#cccccc",
    "edge_width": 1.0,
    # Text
    "text_color": "#333333",
    "annotation_color": "#e65100",
}


# =============================================================================
# Main Plot Function
# =============================================================================


def plot_lattice(
    terms: list[str],
    outcome: str,
    include_intercept: bool = True,
    annotations: dict[str, list[str]] | None = None,
    highlight_current: frozenset[str] | None = None,
    title: str | None = None,
    ax: Axes | None = None,
    figsize: tuple[float, float] | None = None,
    max_nodes: int = 200,
    legend: bool = True,
) -> Figure:
    """Plot the model lattice (Hasse diagram) for a formula.

    Shows all marginality-respecting submodels and their nesting
    relationships. Useful for understanding the space of models
    implied by a formula.

    Args:
        terms: Maximal term set (e.g., ["intercept", "x1", "x2", "x1:x2"]).
        outcome: Response variable name.
        include_intercept: Whether to include intercept-only model.
        annotations: Dict mapping node IDs to warning/annotation strings.
        highlight_current: Terms in the current model (highlighted).
        title: Optional plot title.
        ax: Matplotlib axes. If None, creates new figure.
        figsize: Figure size if creating new figure.
        max_nodes: Maximum nodes before truncation.
        legend: Whether to show color legend (default True).

    Returns:
        Matplotlib Figure object.

    Examples:
        >>> # Simple additive model
        >>> fig = plot_lattice(
        ...     terms=["intercept", "x1", "x2"],
        ...     outcome="y",
        ... )

        >>> # Model with interaction
        >>> fig = plot_lattice(
        ...     terms=["intercept", "x1", "x2", "x1:x2"],
        ...     outcome="y",
        ... )
    """
    import matplotlib.pyplot as plt

    # Generate lattice structure
    lattice = generate_lattice(terms, outcome, include_intercept, max_nodes)

    if not lattice.nodes:
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize or (4, 2))
        else:
            fig = ax.get_figure()
        ax.text(0.5, 0.5, "Empty lattice", ha="center", va="center", fontsize=12)
        ax.axis("off")
        return fig

    # Compute layout
    config = LayoutConfig(
        node_width=0.8,
        node_height=0.3,
        h_spacing=2.0,
        v_spacing=1.0,
    )
    positions = lattice_layout(lattice, config)

    # Create figure if needed
    if ax is None:
        if figsize is None:
            figsize = _compute_lattice_figsize(lattice, positions)
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    # Apply annotations to nodes
    if annotations:
        for node in lattice.nodes:
            if node.id in annotations:
                node.annotations = annotations[node.id]

    # Draw edges first
    for edge in lattice.edges:
        if edge.parent_id in positions and edge.child_id in positions:
            _draw_lattice_edge(ax, positions[edge.parent_id], positions[edge.child_id])

    # Draw nodes
    max_rank = max(n.rank for n in lattice.nodes)
    min_rank = min(n.rank for n in lattice.nodes)

    for node in lattice.nodes:
        if node.id in positions:
            role = _determine_node_role(node, min_rank, max_rank, highlight_current)
            _draw_lattice_node(ax, positions[node.id], node, role, config)

    # Configure axes
    _configure_lattice_axes(ax, positions, config, title, lattice.truncated)

    # Add legend
    if legend:
        _draw_lattice_legend(ax)

    return fig


# =============================================================================
# Legend
# =============================================================================


def _draw_lattice_legend(ax: Axes) -> None:
    """Draw a compact legend inside the plot area."""
    # Build legend text
    parts = [
        "\u25a0 full model",  # filled square
        "\u25a1 null model",  # hollow square
    ]

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
# Drawing Helpers
# =============================================================================


def _compute_lattice_figsize(
    lattice: Lattice,
    positions: dict[str, tuple[float, float]],
) -> tuple[float, float]:
    """Compute appropriate figure size."""
    if not positions:
        return (5, 4)

    xs = [x for x, y in positions.values()]
    ys = [y for x, y in positions.values()]

    x_range = max(xs) - min(xs) + 3
    y_range = max(ys) - min(ys) + 2

    width = max(5, min(14, x_range * 1.2))
    height = max(3, min(10, y_range * 1.2))

    return (width, height)


def _determine_node_role(
    node: LatticeNode,
    min_rank: int,
    max_rank: int,
    highlight_current: frozenset[str] | None,
) -> str:
    """Determine the visual role of a lattice node."""
    if node.annotations:
        return "warning"
    if highlight_current is not None and node.terms == highlight_current:
        return "current"
    if node.rank == max_rank:
        return "maximal"
    if node.rank == min_rank:
        return "minimal"
    return "default"


def _draw_lattice_node(
    ax: Axes,
    pos: tuple[float, float],
    node: LatticeNode,
    role: str,
    config: LayoutConfig,
) -> None:
    """Draw a single lattice node."""
    from matplotlib.patches import FancyBboxPatch

    x, y = pos

    # Get colors based on role
    colors = {
        "maximal": (LATTICE_STYLE["maximal_fill"], LATTICE_STYLE["maximal_edge"], 2.0),
        "minimal": (LATTICE_STYLE["minimal_fill"], LATTICE_STYLE["minimal_edge"], 2.0),
        "warning": (LATTICE_STYLE["warning_fill"], LATTICE_STYLE["warning_edge"], 1.5),
        "current": ("#e3f2fd", "#1976d2", 2.5),
        "default": (LATTICE_STYLE["default_fill"], LATTICE_STYLE["default_edge"], 1.0),
    }
    fill, edge, lw = colors.get(role, colors["default"])

    # Format label - use compact term list
    label = _format_node_label(node)

    # Adjust width based on label length
    text_width = len(label) * 0.055 + 0.3
    width = max(config.node_width, text_width)
    height = config.node_height

    # Draw rounded rectangle
    box = FancyBboxPatch(
        (x - width / 2, y - height / 2),
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.1",
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
        fontsize=LATTICE_STYLE["node_fontsize"],
        fontfamily=LATTICE_STYLE["node_fontfamily"],
        color=LATTICE_STYLE["text_color"],
        zorder=3,
    )

    # Add annotation indicator if present
    if node.annotations:
        ax.text(
            x + width / 2 - 0.1,
            y + height / 2 - 0.05,
            "!",
            ha="center",
            va="center",
            fontsize=8,
            fontweight="bold",
            color=LATTICE_STYLE["annotation_color"],
            zorder=4,
        )


def _format_node_label(node: LatticeNode) -> str:
    """Format node label for display.

    Uses compact notation: 1 + x1 + x2 rather than full formula.
    """
    terms = sorted(node.terms)

    # Replace 'intercept' with '1' for compactness
    display_terms = []
    for t in terms:
        if t == "intercept":
            display_terms.append("1")
        else:
            display_terms.append(t)

    if not display_terms:
        return "0"

    return " + ".join(display_terms)


def _draw_lattice_edge(
    ax: Axes,
    pos1: tuple[float, float],
    pos2: tuple[float, float],
) -> None:
    """Draw an edge in the lattice (simple line, no arrow)."""
    x1, y1 = pos1
    x2, y2 = pos2

    ax.plot(
        [x1, x2],
        [y1, y2],
        color=LATTICE_STYLE["edge_color"],
        linewidth=LATTICE_STYLE["edge_width"],
        zorder=1,
    )


def _configure_lattice_axes(
    ax: Axes,
    positions: dict[str, tuple[float, float]],
    config: LayoutConfig,
    title: str | None,
    truncated: bool,
) -> None:
    """Configure axes appearance."""
    if not positions:
        ax.axis("off")
        return

    xs = [x for x, y in positions.values()]
    ys = [y for x, y in positions.values()]

    pad = 1.0
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)

    ax.axis("off")

    # Title
    if title:
        ax.set_title(title, fontsize=11, fontweight="medium")

    # Truncation warning
    if truncated:
        ax.text(
            0.5,
            0.02,
            "(Lattice truncated - too many models)",
            transform=ax.transAxes,
            ha="center",
            va="bottom",
            fontsize=8,
            fontstyle="italic",
            color="#666666",
        )
