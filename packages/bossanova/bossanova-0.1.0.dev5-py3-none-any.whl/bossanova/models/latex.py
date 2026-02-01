"""LaTeX equation generation for model display.

This module provides utilities for generating structural LaTeX equations
from fitted bossanova models, with detailed term explanations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bossanova.models.base.model import BaseModel

__all__ = ["MathDisplay", "TermInfo", "build_equation"]


# =============================================================================
# Display Wrapper
# =============================================================================


class MathDisplay:
    """Display wrapper for model equation with IPython rich display support.

    Renders as LaTeX in Jupyter notebooks and Quarto documents.
    Falls back to HTML+MathJax or plain text in other environments.

    Attributes:
        equation: The LaTeX equation string.
        explanations: List of term explanation strings.

    Examples:
        >>> display = model.show_math()
        >>> display.to_latex()  # Get raw LaTeX string
    """

    def __init__(
        self, equation: str, explanations: list[str] | None = None, model_info: str = ""
    ):
        """Initialize display wrapper.

        Args:
            equation: LaTeX equation string (without $$ delimiters).
            explanations: Optional list of term explanation strings.
            model_info: Optional model type info for distribution display.
        """
        self._equation = equation
        self._explanations = explanations or []
        self._model_info = model_info

    def _repr_latex_(self) -> str:
        """LaTeX representation for Jupyter rendering."""
        # Return display math format
        return f"$${self._equation}$$"

    def _repr_html_(self) -> str:
        """HTML representation with MathJax fallback."""
        # Build HTML with embedded MathJax
        html_parts = [
            '<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>',
            '<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>',
            f'<div style="font-size: 1.2em; margin: 1em 0;">$${self._equation}$$</div>',
        ]

        if self._explanations:
            html_parts.append('<div style="margin-top: 1em;">')
            html_parts.append("<strong>Terms:</strong>")
            html_parts.append('<ul style="list-style: none; padding-left: 0;">')
            for exp in self._explanations:
                html_parts.append(f"<li>{exp}</li>")
            html_parts.append("</ul>")
            html_parts.append("</div>")

        return "\n".join(html_parts)

    def __repr__(self) -> str:
        """Plain text representation."""
        parts = [self._equation]
        if self._explanations:
            parts.append("")
            parts.append("Terms:")
            for exp in self._explanations:
                parts.append(f"  {exp}")
        return "\n".join(parts)

    def __str__(self) -> str:
        """String representation."""
        return self.__repr__()

    def to_latex(self) -> str:
        """Get raw LaTeX equation string.

        Returns:
            LaTeX equation without $$ delimiters.
        """
        return self._equation


# =============================================================================
# Term Information
# =============================================================================


@dataclass
class TermInfo:
    """Parsed information about a model term.

    Attributes:
        name: Original term name from _X_names (e.g., "center(x1)").
        term_type: Term category ("intercept", "continuous", "factor",
            "interaction", "transform", "poly").
        base_var: Underlying variable name (e.g., "x1" for "center(x1)").
        symbol: LaTeX symbol (e.g., r"\\beta_1").
        latex: Full LaTeX term (e.g., r"\\beta_1 x_{1i}").
        explanation: Human-readable explanation.
    """

    name: str
    term_type: str
    base_var: str
    symbol: str
    latex: str
    explanation: str


# =============================================================================
# Term Parsing
# =============================================================================

# Regex patterns for parsing term names
_FACTOR_PATTERN = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\[([^\]]+)\]$")
_TRANSFORM_PATTERN = re.compile(r"^(center|scale|standardize|zscore|log)\((.+)\)$")
_POLY_PATTERN = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)(\.L|\.Q|\.C|\.\^[0-9]+)$")
_INTERACTION_PATTERN = re.compile(r":")


def _escape_latex(text: str) -> str:
    """Escape text for LaTeX.

    Args:
        text: Raw text.

    Returns:
        LaTeX-safe text with special characters escaped.
    """
    # Replace underscores with escaped underscores for LaTeX
    return text.replace("_", r"\_")


def _variable_latex(name: str, subscript: str = "i") -> str:
    """Format variable name for LaTeX.

    Args:
        name: Variable name.
        subscript: Subscript to add (default "i").

    Returns:
        LaTeX formatted variable.
    """
    escaped = _escape_latex(name)
    return rf"\text{{{escaped}}}_{{{subscript}}}"


def categorize_term(term_name: str, term_idx: int, model: "BaseModel") -> TermInfo:
    """Parse a term name and return its categorization.

    Args:
        term_name: Name from model._X_names.
        term_idx: Index of this term (for beta subscript).
        model: Fitted model for accessing factor/contrast info.

    Returns:
        TermInfo with parsed metadata.
    """
    dm = model._dm
    beta_sub = str(term_idx)
    symbol = rf"\beta_{{{beta_sub}}}"

    # Check for Intercept
    if term_name == "Intercept":
        return TermInfo(
            name=term_name,
            term_type="intercept",
            base_var="Intercept",
            symbol=r"\beta_0",
            latex=r"\beta_0",
            explanation=r"$\beta_0$: Intercept (expected response when all predictors = 0)",
        )

    # Check for interaction (contains :)
    if _INTERACTION_PATTERN.search(term_name):
        parts = term_name.split(":")
        latex_parts = []
        for p in parts:
            # Each part could be a factor level or variable
            factor_match = _FACTOR_PATTERN.match(p)
            if factor_match:
                latex_parts.append(rf"\mathbb{{1}}_{{[{_escape_latex(p)}]}}")
            else:
                latex_parts.append(_variable_latex(p))
        interaction_latex = r" \cdot ".join(latex_parts)
        return TermInfo(
            name=term_name,
            term_type="interaction",
            base_var=term_name,
            symbol=symbol,
            latex=rf"{symbol} ({interaction_latex})",
            explanation=rf"${symbol}$: {term_name} - interaction effect",
        )

    # Check for polynomial contrast (e.g., cyl.L, cyl.Q)
    poly_match = _POLY_PATTERN.match(term_name)
    if poly_match:
        var_name, poly_suffix = poly_match.groups()
        poly_type = {"L": "linear", "Q": "quadratic", "C": "cubic"}.get(
            poly_suffix.lstrip("."), f"degree {poly_suffix.lstrip('.^')}"
        )
        return TermInfo(
            name=term_name,
            term_type="poly",
            base_var=var_name,
            symbol=symbol,
            latex=rf"{symbol} \, {_escape_latex(term_name)}_i",
            explanation=rf"${symbol}$: {var_name} - {poly_type} polynomial contrast",
        )

    # Check for factor level (e.g., group[B])
    factor_match = _FACTOR_PATTERN.match(term_name)
    if factor_match:
        var_name, level = factor_match.groups()
        # Get contrast info
        contrast_type = dm.contrast_types.get(var_name, "treatment")
        levels = dm.factors.get(var_name, [])

        if contrast_type == "treatment":
            ref_level = levels[0] if levels else "?"
            exp = rf"${symbol}$: {var_name}[{level}] - treatment contrast ({level} vs {ref_level} [reference])"
            if levels:
                exp += f"\n     Levels: {ref_level} [ref], " + ", ".join(
                    l for l in levels if l != ref_level
                )
        elif contrast_type == "sum":
            omitted = levels[-1] if levels else "?"
            exp = rf"${symbol}$: {var_name}[{level}] - sum contrast (deviation from grand mean)"
            if levels:
                exp += f"\n     Omitted level: {omitted}"
        else:
            exp = rf"${symbol}$: {var_name}[{level}] - {contrast_type} contrast"

        return TermInfo(
            name=term_name,
            term_type="factor",
            base_var=var_name,
            symbol=symbol,
            latex=rf"{symbol} \, \mathbb{{1}}_{{[{_escape_latex(term_name)}]}}",
            explanation=exp,
        )

    # Check for transform (e.g., center(x), scale(x))
    transform_match = _TRANSFORM_PATTERN.match(term_name)
    if transform_match:
        transform_name, var_name = transform_match.groups()
        # Look up transform state
        # Structure: {'type': 'center', 'variable': 'x1', 'params': {'mean': 4.5}}
        transform_key = term_name
        state = dm.transform_state.get(transform_key, {})
        params = state.get("params", {})

        if transform_name == "center":
            mean_val = params.get("mean", "?")
            if isinstance(mean_val, (int, float)):
                mean_str = f"{mean_val:.3g}"
            else:
                mean_str = str(mean_val)
            superscript = "c"
            exp = rf"${symbol}$: {var_name} (centered, mean = {mean_str})"
        elif transform_name == "scale":
            std_val = params.get("std", "?")
            if isinstance(std_val, (int, float)):
                std_str = f"{std_val:.3g}"
            else:
                std_str = str(std_val)
            superscript = "s"
            exp = rf"${symbol}$: {var_name} (scaled, std = {std_str})"
        elif transform_name in ("standardize", "zscore"):
            mean_val = params.get("mean", "?")
            std_val = params.get("std", "?")
            if isinstance(mean_val, (int, float)):
                mean_str = f"{mean_val:.3g}"
            else:
                mean_str = str(mean_val)
            if isinstance(std_val, (int, float)):
                std_str = f"{std_val:.3g}"
            else:
                std_str = str(std_val)
            superscript = "z"
            exp = rf"${symbol}$: {var_name} (standardized, mean = {mean_str}, std = {std_str})"
        elif transform_name == "log":
            superscript = ""
            exp = rf"${symbol}$: log({var_name})"
        else:
            superscript = ""
            exp = rf"${symbol}$: {term_name}"

        if superscript:
            var_latex = rf"{_variable_latex(var_name)}^{{{superscript}}}"
        else:
            var_latex = rf"\log({_variable_latex(var_name)})"

        return TermInfo(
            name=term_name,
            term_type="transform",
            base_var=var_name,
            symbol=symbol,
            latex=rf"{symbol} \, {var_latex}",
            explanation=exp,
        )

    # Default: continuous variable
    return TermInfo(
        name=term_name,
        term_type="continuous",
        base_var=term_name,
        symbol=symbol,
        latex=rf"{symbol} \, {_variable_latex(term_name)}",
        explanation=rf"${symbol}$: {term_name} - effect per unit increase",
    )


# =============================================================================
# Equation Building
# =============================================================================


def _build_lm_equation(terms: list[TermInfo]) -> str:
    """Build equation for linear model.

    Args:
        terms: List of categorized terms.

    Returns:
        LaTeX equation string.
    """
    # Build fixed effects part
    parts = []
    for term in terms:
        parts.append(term.latex)

    fixed_effects = " + ".join(parts)

    # Add error term
    return rf"y_i = {fixed_effects} + \varepsilon_i, \quad \varepsilon_i \sim N(0, \sigma^2)"


def _build_glm_equation(terms: list[TermInfo], model: "BaseModel") -> str:
    """Build equation for generalized linear model.

    Args:
        terms: List of categorized terms.
        model: Fitted GLM model.

    Returns:
        LaTeX equation string.
    """
    # Get link and family info
    # glm stores family as _family object with .link_name property
    family = getattr(model, "_family", None)
    if family is not None:
        link_name = getattr(family, "link_name", "identity")
        family_name = getattr(family, "name", "gaussian")
    else:
        link_name = "identity"
        family_name = getattr(model, "_family_name", "gaussian")

    # Link function notation
    link_latex = {
        "identity": r"\mu_i",
        "logit": r"\log\left(\frac{\mu_i}{1-\mu_i}\right)",
        "log": r"\log(\mu_i)",
        "probit": r"\Phi^{-1}(\mu_i)",
        "cloglog": r"\log(-\log(1-\mu_i))",
        "inverse": r"\frac{1}{\mu_i}",
        "sqrt": r"\sqrt{\mu_i}",
    }.get(link_name, r"g(\mu_i)")

    # Family notation
    family_latex = {
        "gaussian": r"y_i \sim N(\mu_i, \sigma^2)",
        "binomial": r"y_i \sim \text{Binomial}(n_i, \mu_i)",
        "poisson": r"y_i \sim \text{Poisson}(\mu_i)",
        "gamma": r"y_i \sim \text{Gamma}(\mu_i, \phi)",
        "inverse_gaussian": r"y_i \sim \text{InverseGaussian}(\mu_i, \phi)",
        "t": r"y_i \sim t_\nu(\mu_i, \sigma^2)",
    }.get(family_name, rf"y_i \sim \text{{{family_name}}}(\mu_i)")

    # Build fixed effects part
    parts = []
    for term in terms:
        parts.append(term.latex)

    fixed_effects = " + ".join(parts)

    return (
        rf"{link_latex} = {fixed_effects}"
        rf" \quad \text{{where }} {family_latex}"
    )


def _build_mixed_equation(terms: list[TermInfo], model: "BaseModel") -> str:
    """Build equation for linear mixed model.

    Args:
        terms: List of categorized terms.
        model: Fitted mixed model.

    Returns:
        LaTeX equation string.
    """
    # Build fixed effects part
    parts = []
    for term in terms:
        parts.append(term.latex)

    fixed_effects = " + ".join(parts)

    # Build random effects part
    group_names = getattr(model, "_group_names", [])
    random_names = getattr(model, "_random_names", ["Intercept"])

    re_parts = []
    re_dist_parts = []

    # Handle different RE structures:
    # - Single group: all random_names belong to that group
    # - Crossed groups: each group has one random effect term (intercept only)
    n_groups = len(group_names)

    if n_groups == 1:
        # Single grouping factor - all random effects belong to it
        group_name = group_names[0]
        re_terms = random_names  # All terms belong to this group
        j_sub = "j"

        for r_idx, re_term in enumerate(re_terms):
            if re_term == "Intercept":
                re_parts.append(rf"u_{{0{j_sub}}}")
            else:
                re_parts.append(
                    rf"u_{{{r_idx}{j_sub}}} \, {_variable_latex(re_term, 'i' + j_sub)}"
                )

        # Distribution
        if len(re_terms) == 1:
            re_dist_parts.append(
                rf"u_{{0{j_sub}}} \sim N(0, \sigma_{{u,{_escape_latex(group_name)}}}^2)"
            )
        else:
            re_dist_parts.append(
                rf"\mathbf{{u}}_{{{j_sub}}} \sim N(\mathbf{{0}}, \Sigma_{{{_escape_latex(group_name)}}})"
            )
    else:
        # Multiple grouping factors (crossed/nested)
        # Each group has one entry in random_names
        for g_idx, (group_name, re_term) in enumerate(zip(group_names, random_names)):
            j_sub = chr(ord("j") + g_idx)  # j, k, l, ...

            if re_term == "Intercept":
                re_parts.append(rf"u_{{0{j_sub}}}")
            else:
                re_parts.append(
                    rf"u_{{1{j_sub}}} \, {_variable_latex(re_term, 'i' + j_sub)}"
                )

            # Distribution for this grouping factor (single term)
            re_dist_parts.append(
                rf"u_{{0{j_sub}}} \sim N(0, \sigma_{{u,{_escape_latex(group_name)}}}^2)"
            )

    random_effects = " + ".join(re_parts)
    re_distribution = ", \\quad ".join(re_dist_parts)

    # Check if GLM (has family)
    family = getattr(model, "_family", None)
    if family is not None and getattr(family, "name", "gaussian") != "gaussian":
        # GLMM
        link_name = getattr(family, "link_name", "identity")
        family_name = getattr(family, "name", "gaussian")

        link_latex = {
            "identity": r"\mu_{ij}",
            "logit": r"\log\left(\frac{\mu_{ij}}{1-\mu_{ij}}\right)",
            "log": r"\log(\mu_{ij})",
            "probit": r"\Phi^{-1}(\mu_{ij})",
        }.get(link_name, r"g(\mu_{ij})")

        family_latex = {
            "binomial": r"y_{ij} \sim \text{Binomial}(n_{ij}, \mu_{ij})",
            "poisson": r"y_{ij} \sim \text{Poisson}(\mu_{ij})",
        }.get(family_name, rf"y_{{ij}} \sim \text{{{family_name}}}(\mu_{{ij}})")

        return (
            rf"{link_latex} = {fixed_effects} + {random_effects}"
            rf" \\ \text{{where }} {re_distribution}, \quad {family_latex}"
        )
    else:
        # LMM
        return (
            rf"y_{{ij}} = {fixed_effects} + {random_effects} + \varepsilon_{{ij}}"
            rf" \\ \text{{where }} {re_distribution}, \quad \varepsilon_{{ij}} \sim N(0, \sigma^2)"
        )


def build_equation(model: "BaseModel", explanations: bool = True) -> MathDisplay:
    """Build complete model equation as MathDisplay object.

    Args:
        model: Fitted bossanova model (lm, glm, lmer, glmer).
        explanations: If True, include term explanations.

    Returns:
        MathDisplay object for notebook rendering.
    """
    # Categorize all terms
    terms = []
    for idx, term_name in enumerate(model._X_names):
        term_info = categorize_term(term_name, idx, model)
        terms.append(term_info)

    # Determine model type and build appropriate equation
    is_mixed = hasattr(model, "_group_names") and model._group_names
    family = getattr(model, "_family", None)
    is_glm = family is not None and getattr(family, "name", "gaussian") != "gaussian"

    if is_mixed:
        equation = _build_mixed_equation(terms, model)
    elif is_glm:
        equation = _build_glm_equation(terms, model)
    else:
        equation = _build_lm_equation(terms)

    # Collect explanations
    exp_list = [t.explanation for t in terms] if explanations else []

    return MathDisplay(equation=equation, explanations=exp_list)
