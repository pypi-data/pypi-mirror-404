"""Graph layout algorithms for DAG and lattice visualization.

Pure Python implementations with no external graph library dependencies.
These algorithms compute (x, y) positions for nodes in causal DAGs and
model lattices (Hasse diagrams).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass  # Future type hints if needed

__all__ = [
    "LayoutConfig",
    "dag_layout",
    "LatticeNode",
    "LatticeEdge",
    "Lattice",
    "generate_lattice",
    "lattice_layout",
]


@dataclass
class LayoutConfig:
    """Configuration for graph layout algorithms."""

    node_width: float = 1.0
    node_height: float = 0.5
    h_spacing: float = 1.5  # Horizontal spacing between nodes
    v_spacing: float = 1.2  # Vertical spacing between rows
    padding: float = 0.5  # Padding around the graph


# =============================================================================
# DAG Layout
# =============================================================================


def dag_layout(
    edges: list[tuple[str, str]],
    bidirected: list[tuple[str, str]] | None = None,
    exposure: str | None = None,
    outcome: str | None = None,
    config: LayoutConfig | None = None,
) -> dict[str, tuple[float, float]]:
    """Compute causal-aware layout for a DAG.

    Positions nodes according to their causal roles:
    - Exposure on the left, outcome on the right (main row)
    - Confounders (common causes) positioned above
    - Mediators positioned between exposure/outcome, slightly above
    - Colliders and other nodes positioned below

    Args:
        edges: Directed edges as (source, target) tuples.
        bidirected: Bidirected edges (unmeasured confounding).
        exposure: Exposure/treatment variable name.
        outcome: Outcome variable name.
        config: Layout configuration.

    Returns:
        Dictionary mapping node names to (x, y) positions.
    """
    if config is None:
        config = LayoutConfig()

    bidirected = bidirected or []

    # Extract all nodes
    nodes = _extract_nodes(edges, bidirected)
    if not nodes:
        return {}

    # Build adjacency structures
    children, parents = _build_adjacency(nodes, edges)

    # Classify nodes by causal role
    confounders = []
    mediators = []
    other = []

    for n in nodes:
        if n == exposure or n == outcome:
            continue

        if exposure and outcome:
            if _is_confounder(n, exposure, outcome, parents):
                confounders.append(n)
            elif _is_mediator(n, exposure, outcome, children, parents):
                mediators.append(n)
            else:
                other.append(n)
        else:
            other.append(n)

    # Determine row positions
    positions: dict[str, tuple[float, float]] = {}

    # Calculate y positions based on what's present
    y_positions = _compute_dag_rows(
        has_confounders=len(confounders) > 0,
        has_mediators=len(mediators) > 0,
        has_other=len(other) > 0,
        config=config,
    )

    # Position exposure and outcome on main row
    if exposure:
        positions[exposure] = (config.padding, y_positions["main"])
    if outcome:
        # Leave space for mediators
        n_between = max(1, len(mediators))
        outcome_x = config.padding + (n_between + 1) * config.h_spacing
        positions[outcome] = (outcome_x, y_positions["main"])

    # Position mediators between exposure and outcome
    if mediators and exposure in positions and outcome in positions:
        exp_x = positions[exposure][0]
        out_x = positions[outcome][0]

        # Sort mediators by distance from exposure
        med_depth = {}
        for n in mediators:
            d = _path_distance(exposure, n, children)
            med_depth[n] = d if d is not None else 1
        mediators_sorted = sorted(mediators, key=lambda n: med_depth.get(n, 0))

        # Space evenly between exposure and outcome
        for i, n in enumerate(mediators_sorted):
            t = (i + 1) / (len(mediators) + 1)
            x = exp_x + t * (out_x - exp_x)
            positions[n] = (x, y_positions["mediator"])

    # Position confounders above, centered
    if confounders and exposure in positions and outcome in positions:
        exp_x = positions[exposure][0]
        out_x = positions[outcome][0]
        center_x = (exp_x + out_x) / 2

        total_width = (len(confounders) - 1) * config.h_spacing
        start_x = center_x - total_width / 2

        for i, n in enumerate(confounders):
            x = start_x + i * config.h_spacing
            positions[n] = (x, y_positions["confounder"])

    # Position other nodes below, centered
    if other:
        if positions:
            min_x = min(x for x, y in positions.values())
            max_x = max(x for x, y in positions.values())
            center_x = (min_x + max_x) / 2
        else:
            center_x = config.padding

        total_width = (len(other) - 1) * config.h_spacing
        start_x = center_x - total_width / 2

        for i, n in enumerate(other):
            x = start_x + i * config.h_spacing
            positions[n] = (x, y_positions["other"])

    return positions


def _compute_dag_rows(
    has_confounders: bool,
    has_mediators: bool,
    has_other: bool,
    config: LayoutConfig,
) -> dict[str, float]:
    """Compute y positions for each row in DAG layout."""
    # Build from top to bottom (confounders at top, y increases downward)
    y = config.padding
    rows = {}

    if has_confounders:
        rows["confounder"] = y
        y += config.v_spacing

    if has_mediators:
        rows["mediator"] = y
        y += config.v_spacing

    rows["main"] = y
    y += config.v_spacing

    if has_other:
        rows["other"] = y

    return rows


def _is_confounder(
    node: str, exposure: str, outcome: str, parents: dict[str, set[str]]
) -> bool:
    """Check if node is a common cause of exposure and outcome."""
    exp_ancestors = _get_ancestors(exposure, parents)
    out_ancestors = _get_ancestors(outcome, parents)
    return node in exp_ancestors and node in out_ancestors


def _is_mediator(
    node: str,
    exposure: str,
    outcome: str,
    children: dict[str, set[str]],
    parents: dict[str, set[str]],
) -> bool:
    """Check if node is on a directed path from exposure to outcome."""
    exp_descendants = _get_descendants(exposure, children)
    out_ancestors = _get_ancestors(outcome, parents)
    return node in exp_descendants and node in out_ancestors


# =============================================================================
# Lattice (Hasse Diagram) Layout
# =============================================================================


@dataclass
class LatticeNode:
    """A node in the model lattice."""

    id: str
    terms: frozenset[str]
    formula: str
    rank: int  # Number of terms (for vertical positioning)
    annotations: list[str] = field(default_factory=list)


@dataclass
class LatticeEdge:
    """An edge in the model lattice (covering relation)."""

    parent_id: str  # More complex model
    child_id: str  # Simpler model
    added_term: str  # Term that distinguishes parent from child


@dataclass
class Lattice:
    """Complete model lattice structure."""

    nodes: list[LatticeNode]
    edges: list[LatticeEdge]
    truncated: bool = False


def generate_lattice(
    terms: list[str],
    outcome: str,
    include_intercept: bool = True,
    max_nodes: int = 200,
) -> Lattice:
    """Generate the model lattice from a maximal term set.

    Creates all marginality-respecting subsets of terms and the
    covering relations between them.

    Args:
        terms: Maximal term set (e.g., ["intercept", "x1", "x2", "x1:x2"]).
        outcome: Response variable name (for formula generation).
        include_intercept: Whether intercept-only model is included.
        max_nodes: Maximum number of nodes before truncation.

    Returns:
        Lattice with nodes and edges.
    """
    # Separate intercept from other terms
    has_intercept = "intercept" in terms
    other_terms = [t for t in terms if t != "intercept"]

    # Build marginality dependencies
    # For each term, which terms must be present for it to be valid?
    marginality = _compute_marginality(other_terms)

    # Generate all valid subsets
    valid_subsets = _generate_valid_subsets(other_terms, marginality, max_nodes)

    # Check for truncation
    truncated = len(valid_subsets) >= max_nodes

    # Create lattice nodes
    nodes = []
    subset_to_id = {}

    for i, subset in enumerate(
        sorted(valid_subsets, key=lambda s: (len(s), sorted(s)))
    ):
        node_id = f"n{i}"
        subset_to_id[subset] = node_id

        # Build formula
        if has_intercept or include_intercept:
            if subset:
                formula_terms = ["1"] + sorted(subset)
            else:
                formula_terms = ["1"]
        else:
            formula_terms = sorted(subset) if subset else ["0"]

        formula = f"{outcome} ~ {' + '.join(formula_terms)}"

        # Include intercept in terms for display
        term_set = frozenset(subset)
        if has_intercept or include_intercept:
            term_set = frozenset(["intercept"]) | term_set

        nodes.append(
            LatticeNode(
                id=node_id,
                terms=term_set,
                formula=formula,
                rank=len(subset) + (1 if has_intercept else 0),
            )
        )

    # Create edges (covering relations)
    edges = []
    for child_subset in valid_subsets:
        # Find all parents that differ by exactly one term
        for term in other_terms:
            if term in child_subset:
                continue  # Term already in child

            # Can we add this term while respecting marginality?
            parent_subset = child_subset | {term}

            # Check marginality: parent must also include any terms required by `term`
            required = marginality.get(term, set())
            if not required.issubset(parent_subset):
                # Need to add required terms too - not a covering relation
                continue

            if parent_subset in valid_subsets:
                edges.append(
                    LatticeEdge(
                        parent_id=subset_to_id[parent_subset],
                        child_id=subset_to_id[child_subset],
                        added_term=term,
                    )
                )

    return Lattice(nodes=nodes, edges=edges, truncated=truncated)


def _compute_marginality(terms: list[str]) -> dict[str, set[str]]:
    """Compute marginality requirements for each term.

    An interaction term requires all its component main effects.
    E.g., x1:x2 requires {x1, x2}
          x1:x2:x3 requires {x1, x2, x3, x1:x2, x1:x3, x2:x3}
    """
    marginality: dict[str, set[str]] = {}

    for term in terms:
        if ":" not in term:
            marginality[term] = set()
            continue

        # Interaction term
        components = term.split(":")
        required = set()

        # Add all main effects
        for c in components:
            if c in terms:
                required.add(c)

        # Add all lower-order interactions
        if len(components) > 2:
            from itertools import combinations

            for r in range(2, len(components)):
                for combo in combinations(components, r):
                    lower_interaction = ":".join(sorted(combo))
                    if lower_interaction in terms:
                        required.add(lower_interaction)

        marginality[term] = required

    return marginality


def _generate_valid_subsets(
    terms: list[str],
    marginality: dict[str, set[str]],
    max_nodes: int,
) -> set[frozenset[str]]:
    """Generate all marginality-respecting subsets."""
    valid = {frozenset()}  # Empty set is always valid

    # BFS to generate subsets
    queue = [frozenset()]
    seen = {frozenset()}

    while queue and len(valid) < max_nodes:
        current = queue.pop(0)

        for term in terms:
            if term in current:
                continue

            # Check if adding this term is valid
            required = marginality.get(term, set())
            if not required.issubset(current):
                continue

            new_subset = current | {term}
            if new_subset not in seen:
                seen.add(new_subset)
                valid.add(new_subset)
                queue.append(new_subset)

                if len(valid) >= max_nodes:
                    break

    return valid


def lattice_layout(
    lattice: Lattice,
    config: LayoutConfig | None = None,
) -> dict[str, tuple[float, float]]:
    """Compute layout positions for a model lattice (Hasse diagram).

    Positions nodes by rank (term count), with the intercept-only
    model at the bottom and the maximal model at the top.

    Args:
        lattice: The model lattice structure.
        config: Layout configuration.

    Returns:
        Dictionary mapping node IDs to (x, y) positions.
    """
    if config is None:
        config = LayoutConfig()

    if not lattice.nodes:
        return {}

    # Group nodes by rank
    by_rank: dict[int, list[LatticeNode]] = {}
    for node in lattice.nodes:
        by_rank.setdefault(node.rank, []).append(node)

    # Sort ranks (ascending = bottom to top)
    ranks = sorted(by_rank.keys())

    positions = {}

    for row_idx, rank in enumerate(ranks):
        row_nodes = by_rank[rank]
        n_nodes = len(row_nodes)

        # Compute y position (bottom = 0, increases upward)
        y = config.padding + row_idx * config.v_spacing

        # Center nodes horizontally
        total_width = (n_nodes - 1) * config.h_spacing
        start_x = config.padding - total_width / 2 + (len(ranks) * config.h_spacing / 2)

        # Sort nodes within rank for consistent ordering
        row_nodes_sorted = sorted(row_nodes, key=lambda n: sorted(n.terms))

        for i, node in enumerate(row_nodes_sorted):
            x = start_x + i * config.h_spacing
            positions[node.id] = (x, y)

    return positions


# =============================================================================
# Helper Functions
# =============================================================================


def _extract_nodes(
    edges: list[tuple[str, str]],
    bidirected: list[tuple[str, str]],
) -> list[str]:
    """Extract unique nodes from edge lists."""
    nodes = []
    seen = set()

    for src, dst in edges:
        if src not in seen:
            nodes.append(src)
            seen.add(src)
        if dst not in seen:
            nodes.append(dst)
            seen.add(dst)

    for a, b in bidirected:
        if a not in seen:
            nodes.append(a)
            seen.add(a)
        if b not in seen:
            nodes.append(b)
            seen.add(b)

    return nodes


def _build_adjacency(
    nodes: list[str],
    edges: list[tuple[str, str]],
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Build children and parents adjacency dicts."""
    children = {n: set() for n in nodes}
    parents = {n: set() for n in nodes}

    for src, dst in edges:
        if src in children and dst in children:
            children[src].add(dst)
            parents[dst].add(src)

    return children, parents


def _get_ancestors(node: str, parents: dict[str, set[str]]) -> set[str]:
    """Get all ancestors of a node via BFS."""
    ancestors = set()
    to_visit = list(parents.get(node, []))

    while to_visit:
        n = to_visit.pop()
        if n not in ancestors:
            ancestors.add(n)
            to_visit.extend(parents.get(n, []))

    return ancestors


def _get_descendants(node: str, children: dict[str, set[str]]) -> set[str]:
    """Get all descendants of a node via BFS."""
    descendants = set()
    to_visit = list(children.get(node, []))

    while to_visit:
        n = to_visit.pop()
        if n not in descendants:
            descendants.add(n)
            to_visit.extend(children.get(n, []))

    return descendants


def _path_distance(start: str, end: str, children: dict[str, set[str]]) -> int | None:
    """BFS distance from start to end."""
    if start == end:
        return 0

    visited = {start}
    queue = [(start, 0)]

    while queue:
        node, dist = queue.pop(0)
        for child in children.get(node, []):
            if child == end:
                return dist + 1
            if child not in visited:
                visited.add(child)
                queue.append((child, dist + 1))

    return None
