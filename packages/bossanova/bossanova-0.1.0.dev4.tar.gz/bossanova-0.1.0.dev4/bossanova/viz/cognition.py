"""Model cognition visualization - combined DAG and lattice display.

This module provides the core visualization for understanding models
before estimation: what causal assumptions are implied, and what
alternative models exist in the model space.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from bossanova.viz.dag import DAG_STYLE, default_dag_edges, plot_dag
from bossanova.viz.lattice import plot_lattice

if TYPE_CHECKING:
    from matplotlib.figure import Figure

__all__ = ["plot_cognition", "add_dag_legend"]


def plot_cognition(
    terms: list[str],
    outcome: str,
    dag_edges: list[tuple[str, str]] | None = None,
    dag_bidirected: list[tuple[str, str]] | None = None,
    exposure: str | None = None,
    kind: Literal["both", "dag", "lattice"] = "both",
    dag_source: Literal["default", "user"] = "default",
    figsize: tuple[float, float] | None = None,
    legend: bool = True,
) -> Figure:
    """Plot model cognition: DAG and/or model lattice.

    This is the main visualization function for understanding a model
    specification before estimation. It shows:
    1. The causal DAG (assumed or explicit)
    2. The model lattice (Hasse diagram of nested models)

    Args:
        terms: Model terms including "intercept" if present.
        outcome: Response variable name.
        dag_edges: Directed edges for DAG. If None, uses default
            regression interpretation (all predictors -> outcome).
        dag_bidirected: Bidirected edges (unmeasured confounding).
        exposure: Exposure variable for highlighting.
        kind: What to display:
            - "both": Side-by-side DAG and lattice (default)
            - "dag": DAG only
            - "lattice": Lattice only
        dag_source: Whether DAG is "default" or "user"-specified.
        figsize: Figure size. Auto-computed if None.
        legend: Whether to show color legends (default True).

    Returns:
        Matplotlib Figure object.

    Examples:
        >>> # Default regression assumptions
        >>> fig = plot_cognition(
        ...     terms=["intercept", "x1", "x2"],
        ...     outcome="y",
        ... )

        >>> # With user-specified causal structure
        >>> fig = plot_cognition(
        ...     terms=["intercept", "x1", "x2"],
        ...     outcome="y",
        ...     dag_edges=[("x1", "x2"), ("x2", "y"), ("x1", "y")],
        ...     exposure="x1",
        ...     dag_source="user",
        ... )
    """
    # Get predictors (exclude intercept for DAG)
    predictors = [t for t in terms if t != "intercept" and ":" not in t]

    # Generate default DAG if not provided
    if dag_edges is None:
        dag_edges = default_dag_edges(predictors, outcome)

    # Determine layout based on kind
    if kind == "dag":
        return _plot_dag_only(
            dag_edges, dag_bidirected, exposure, outcome, dag_source, figsize, legend
        )
    elif kind == "lattice":
        return _plot_lattice_only(terms, outcome, figsize, legend)
    else:  # "both"
        return _plot_side_by_side(
            terms,
            outcome,
            dag_edges,
            dag_bidirected,
            exposure,
            dag_source,
            figsize,
            legend,
        )


def _plot_dag_only(
    edges: list[tuple[str, str]],
    bidirected: list[tuple[str, str]] | None,
    exposure: str | None,
    outcome: str,
    source: str,
    figsize: tuple[float, float] | None,
    legend: bool,
) -> Figure:
    """Plot DAG only."""
    title = "Causal Assumptions"
    if source == "default":
        title += " (default)"

    return plot_dag(
        edges=edges,
        bidirected=bidirected,
        exposure=exposure,
        outcome=outcome,
        title=title,
        figsize=figsize,
        legend=legend,
    )


def _plot_lattice_only(
    terms: list[str],
    outcome: str,
    figsize: tuple[float, float] | None,
    legend: bool,
) -> Figure:
    """Plot lattice only."""
    return plot_lattice(
        terms=terms,
        outcome=outcome,
        title="Model Space",
        figsize=figsize,
        legend=legend,
    )


def _plot_side_by_side(
    terms: list[str],
    outcome: str,
    dag_edges: list[tuple[str, str]],
    dag_bidirected: list[tuple[str, str]] | None,
    exposure: str | None,
    dag_source: str,
    figsize: tuple[float, float] | None,
    legend: bool,
) -> Figure:
    """Plot DAG and lattice side-by-side."""
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    # Compute figsize if not provided
    if figsize is None:
        # Estimate based on complexity
        n_terms = len([t for t in terms if t != "intercept"])
        width = max(10, min(16, 5 + n_terms * 1.5))
        height = max(4, min(8, 3 + n_terms * 0.5))
        figsize = (width, height)

    fig = plt.figure(figsize=figsize)

    # Use GridSpec for flexible layout
    # DAG gets less width (it's usually simpler)
    gs = GridSpec(1, 2, figure=fig, width_ratios=[1, 1.3], wspace=0.3)

    # DAG subplot
    ax_dag = fig.add_subplot(gs[0])
    dag_title = "Causal Assumptions"
    if dag_source == "default":
        dag_title += " (default)"

    plot_dag(
        edges=dag_edges,
        bidirected=dag_bidirected,
        exposure=exposure,
        outcome=outcome,
        title=dag_title,
        ax=ax_dag,
        legend=legend,
    )

    # Lattice subplot
    ax_lattice = fig.add_subplot(gs[1])
    plot_lattice(
        terms=terms,
        outcome=outcome,
        title="Model Space",
        ax=ax_lattice,
        legend=legend,
    )

    return fig


# =============================================================================
# Legend / Annotation Helpers
# =============================================================================


def add_dag_legend(ax, include_default_note: bool = True) -> None:
    """Add a legend explaining DAG elements.

    Args:
        ax: Matplotlib axes.
        include_default_note: Whether to add note about default interpretation.
    """
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D

    elements = [
        Patch(
            facecolor=DAG_STYLE["exposure_fill"],
            edgecolor=DAG_STYLE["exposure_edge"],
            label="Exposure",
        ),
        Patch(
            facecolor=DAG_STYLE["outcome_fill"],
            edgecolor=DAG_STYLE["outcome_edge"],
            label="Outcome",
        ),
        Line2D([0], [0], color=DAG_STYLE["edge_color"], linewidth=1.5, label="Causes"),
        Line2D(
            [0],
            [0],
            color=DAG_STYLE["bidir_color"],
            linewidth=1.2,
            linestyle="--",
            label="Unmeasured confounding",
        ),
    ]

    ax.legend(
        handles=elements,
        loc="upper right",
        fontsize=8,
        framealpha=0.9,
    )

    if include_default_note:
        ax.text(
            0.02,
            0.02,
            "Default: all predictors → outcome, no confounding",
            transform=ax.transAxes,
            fontsize=7,
            fontstyle="italic",
            color="#666666",
            va="bottom",
        )
