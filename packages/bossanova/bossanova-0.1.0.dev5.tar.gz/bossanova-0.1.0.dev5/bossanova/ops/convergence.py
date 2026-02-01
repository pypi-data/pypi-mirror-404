"""Convergence diagnostics for mixed-effects models.

Provides user-friendly convergence warnings that pair lme4-style technical
messages with plain-English explanations and actionable tips.
"""

from dataclasses import dataclass

import numpy as np

__all__ = [
    "ConvergenceMessage",
    "diagnose_convergence",
    "format_convergence_warnings",
]


def _normalize_re_structure(
    re_structure: str | list[str] | dict[str, str],
    group_names: list[str],
) -> dict[str, str]:
    """Normalize random effects structure to a dict mapping group -> structure.

    Args:
        re_structure: Random effects structure specification.
            - str: Same structure for all groups
            - list[str]: Structure per group (same order as group_names)
            - dict[str, str]: Mapping from group name to structure
        group_names: Names of grouping factors.

    Returns:
        Dict mapping each group name to its structure type.
    """
    if isinstance(re_structure, str):
        return {gn: re_structure for gn in group_names}
    elif isinstance(re_structure, list):
        return dict(zip(group_names, re_structure))
    else:
        return re_structure


def _normalize_random_names(
    random_names: list[str] | dict[str, list[str]],
    group_names: list[str],
    re_structure: str | list[str] | dict[str, str],
) -> dict[str, list[str]]:
    """Normalize random effect names to a dict mapping group -> names list.

    Args:
        random_names: Random effect names specification.
            - list[str]: Same names for all groups, or one per group if structured
            - dict[str, list[str]]: Mapping from group name to effect names
        group_names: Names of grouping factors.
        re_structure: Random effects structure (used to determine list interpretation).

    Returns:
        Dict mapping each group name to its list of random effect names.
    """
    if isinstance(random_names, list):
        if isinstance(re_structure, list) and len(random_names) == len(group_names):
            return {gn: [random_names[i]] for i, gn in enumerate(group_names)}
        else:
            return {gn: random_names for gn in group_names}
    else:
        return random_names


@dataclass
class ConvergenceMessage:
    """A convergence diagnostic message with technical and user-friendly parts.

    Attributes:
        category: Type of issue ("singular", "correlation", "boundary", "convergence")
        technical: lme4-style technical message
        explanation: User-friendly explanation of the issue
        tip: Actionable suggestion to fix the issue (optional)
    """

    category: str
    technical: str
    explanation: str
    tip: str | None = None


def _map_theta_to_terms(
    theta: np.ndarray,
    theta_lower: list[float],
    group_names: list[str],
    random_names: list[str] | dict[str, list[str]],
    re_structure: str | list[str] | dict[str, str],
) -> list[dict]:
    """Map theta indices to group/term names and structure info.

    Returns a list of dicts, one per theta element:
        {"group": str, "term": str, "is_diagonal": bool, "theta_idx": int, "lower": float}

    Diagonal elements correspond to variance components (SD when sqrt'd).
    Off-diagonal elements correspond to covariance/correlation terms.
    """
    structure_dict = _normalize_re_structure(re_structure, group_names)
    names_dict = _normalize_random_names(random_names, group_names, re_structure)

    mapping = []
    theta_idx = 0

    for group_name in group_names:
        structure = structure_dict[group_name]
        re_names = names_dict[group_name]
        n_re = len(re_names)

        if structure == "intercept":
            # Single diagonal element
            mapping.append(
                {
                    "group": group_name,
                    "term": re_names[0],
                    "is_diagonal": True,
                    "theta_idx": theta_idx,
                    "lower": theta_lower[theta_idx],
                }
            )
            theta_idx += 1

        elif structure == "diagonal":
            # n_re diagonal elements
            for i, term in enumerate(re_names):
                mapping.append(
                    {
                        "group": group_name,
                        "term": term,
                        "is_diagonal": True,
                        "theta_idx": theta_idx,
                        "lower": theta_lower[theta_idx],
                    }
                )
                theta_idx += 1

        elif structure == "slope":
            # Lower triangle of Cholesky (column-major)
            # Diagonal elements are variance SDs, off-diagonals are covariance terms
            for j in range(n_re):
                for i in range(j, n_re):
                    is_diag = i == j
                    if is_diag:
                        term = re_names[i]
                    else:
                        term = f"{re_names[j]}:{re_names[i]}"
                    mapping.append(
                        {
                            "group": group_name,
                            "term": term,
                            "is_diagonal": is_diag,
                            "theta_idx": theta_idx,
                            "lower": theta_lower[theta_idx],
                        }
                    )
                    theta_idx += 1
        else:
            raise ValueError(f"Unknown RE structure: {structure}")

    return mapping


def _detect_singular_components(
    theta: np.ndarray,
    theta_mapping: list[dict],
    singular_tol: float,
) -> list[tuple[str, str, float]]:
    """Detect variance components that are near zero.

    Returns list of (group, term, sd_value) for singular components.
    Only checks diagonal elements (variance terms) with lower bound 0.
    """
    singular = []
    for m in theta_mapping:
        if m["is_diagonal"] and m["lower"] == 0:
            val = theta[m["theta_idx"]]
            if val < singular_tol:
                singular.append((m["group"], m["term"], float(val)))
    return singular


def _compute_correlations(
    theta: np.ndarray,
    group_names: list[str],
    random_names: list[str] | dict[str, list[str]],
    re_structure: str | list[str] | dict[str, str],
    sigma: float,
) -> dict[str, dict[str, float]]:
    """Compute correlations between random effects per group.

    Returns dict: {group: {term1:term2: corr_value, ...}, ...}
    """
    structure_dict = _normalize_re_structure(re_structure, group_names)
    names_dict = _normalize_random_names(random_names, group_names, re_structure)

    correlations = {}
    theta_idx = 0

    for group_name in group_names:
        structure = structure_dict[group_name]
        re_names = names_dict[group_name]
        n_re = len(re_names)

        if structure == "intercept":
            theta_idx += 1
            continue
        elif structure == "diagonal":
            theta_idx += n_re
            continue
        elif structure == "slope":
            # Extract Cholesky factor
            n_theta = n_re * (n_re + 1) // 2
            L = np.zeros((n_re, n_re))
            k = theta_idx
            for j in range(n_re):
                for i in range(j, n_re):
                    L[i, j] = theta[k]
                    k += 1
            theta_idx += n_theta

            # Compute variance-covariance and correlations
            Sigma = sigma**2 * (L @ L.T)
            group_corrs = {}
            for i in range(n_re):
                for j in range(i + 1, n_re):
                    denom = np.sqrt(Sigma[i, i] * Sigma[j, j])
                    if denom > 1e-10:
                        corr = Sigma[i, j] / denom
                    else:
                        corr = 0.0
                    group_corrs[f"{re_names[i]}:{re_names[j]}"] = float(corr)
            if group_corrs:
                correlations[group_name] = group_corrs

    return correlations


def _detect_degenerate_correlations(
    correlations: dict[str, dict[str, float]],
    corr_tol: float,
) -> list[tuple[str, str, float]]:
    """Detect correlations that are near |1| (degenerate).

    Returns list of (group, term_pair, corr_value) for degenerate correlations.
    """
    degenerate = []
    for group, corrs in correlations.items():
        for term_pair, corr in corrs.items():
            if abs(corr) > corr_tol:
                degenerate.append((group, term_pair, corr))
    return degenerate


def diagnose_convergence(
    theta: np.ndarray,
    theta_lower: list[float],
    group_names: list[str],
    random_names: list[str] | dict[str, list[str]],
    re_structure: str | list[str] | dict[str, str],
    sigma: float,
    converged: bool,
    boundary_adjusted: bool,
    restarted: bool,
    optimizer_message: str = "",
    singular_tol: float = 1e-4,
    corr_tol: float = 0.99,
) -> list[ConvergenceMessage]:
    """Analyze model convergence state and generate diagnostic messages.

    Args:
        theta: Optimized theta parameters (Cholesky factors, relative scale).
        theta_lower: Lower bounds for each theta element.
        group_names: Names of grouping factors.
        random_names: Names of random effects per group.
        re_structure: RE structure per group ("intercept", "diagonal", "slope").
        sigma: Residual standard deviation (1.0 for GLMMs).
        converged: Whether optimizer reported convergence.
        boundary_adjusted: Whether boundary checking adjusted parameters.
        restarted: Whether restart_edge triggered a restart.
        optimizer_message: Message from optimizer (for non-convergence).
        singular_tol: Tolerance for near-zero variance detection.
        corr_tol: Tolerance for degenerate correlation detection (|corr| > tol).

    Returns:
        List of ConvergenceMessage objects describing any issues found.
    """
    messages = []

    # Map theta indices to group/term names
    theta_mapping = _map_theta_to_terms(
        theta, theta_lower, group_names, random_names, re_structure
    )

    # Check for non-convergence first (most severe)
    if not converged:
        messages.append(
            ConvergenceMessage(
                category="convergence",
                technical=f"Model failed to converge: {optimizer_message}",
                explanation="The optimizer could not find a stable solution.",
                tip="Try simplifying the random effects structure or rescaling predictors.",
            )
        )

    # Check for singular variance components
    singular = _detect_singular_components(theta, theta_mapping, singular_tol)
    for group, term, sd_val in singular:
        # Build a helpful formula suggestion
        if term == "Intercept":
            tip = f"Consider removing the random intercept: (0 + ... | {group})"
        else:
            tip = f"Consider removing '{term}' from random effects for '{group}'."

        messages.append(
            ConvergenceMessage(
                category="singular",
                technical="boundary (singular fit): some random effect variances estimated at zero",
                explanation=f"Random effect '{term}' for '{group}' has near-zero variance (SD={sd_val:.4f}).",
                tip=tip,
            )
        )

    # Check for degenerate correlations
    correlations = _compute_correlations(
        theta, group_names, random_names, re_structure, sigma
    )
    degenerate = _detect_degenerate_correlations(correlations, corr_tol)
    for group, term_pair, corr in degenerate:
        terms = term_pair.split(":")
        messages.append(
            ConvergenceMessage(
                category="correlation",
                technical="boundary (singular fit): random effect correlations close to |1|",
                explanation=(
                    f"Correlation between '{terms[0]}' and '{terms[1]}' is {corr:.2f} for '{group}'."
                ),
                tip=(
                    f"These terms may be redundant. Try separating them: "
                    f"(1 | {group}) + (0 + {terms[1]} | {group})"
                ),
            )
        )

    # Note boundary adjustments (informational, not a problem)
    if boundary_adjusted and not singular and not degenerate:
        messages.append(
            ConvergenceMessage(
                category="boundary",
                technical="boundary: parameters adjusted to boundary",
                explanation="Some variance parameters were snapped to their boundary values.",
                tip=None,  # Not necessarily a problem
            )
        )

    # Note restart (informational)
    if restarted:
        messages.append(
            ConvergenceMessage(
                category="restart",
                technical="optimizer restarted from boundary",
                explanation="Optimization was restarted after hitting a boundary constraint.",
                tip="This is usually fine; check that estimates look reasonable.",
            )
        )

    return messages


def format_convergence_warnings(messages: list[ConvergenceMessage]) -> str:
    """Format convergence messages for display as warning text.

    Uses paired format: technical message (deemphasized) followed by
    explanation (prominent), without explicit labels.

    Args:
        messages: List of ConvergenceMessage objects.

    Returns:
        Formatted warning string.
    """
    if not messages:
        return ""

    lines = []
    for msg in messages:
        # Technical message (lowercase, lme4-style)
        lines.append(msg.technical)
        # Explanation (indented, prominent)
        lines.append(f"  → {msg.explanation}")
        if msg.tip:
            lines.append(f"    {msg.tip}")
        lines.append("")  # Blank line between messages

    # Remove trailing blank line
    if lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)
