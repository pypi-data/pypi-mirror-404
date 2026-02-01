"""Resampling distribution visualization for bossanova models.

This module provides plot_resamples() for visualizing bootstrap coefficient
distributions or permutation null distributions.
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

__all__ = ["plot_resamples"]


def plot_resamples(
    model: BaseModel,
    *,
    which: Literal["params", "mee"] = "params",
    include_intercept: bool = False,
    terms: list[str] | None = None,
    height: float = 3.0,
    aspect: float = 1.2,
    col_wrap: int = 4,
    palette: str | None = None,
    show_ci: bool = True,
    show_pvalue: bool = True,
    fill: bool = True,
) -> sns.FacetGrid:
    """Plot distribution of resampled statistics.

    Visualizes bootstrap coefficient distributions or permutation null
    distributions. Requires save_resamples=True (default for n<=5000)
    during infer().

    Args:
        model: A fitted bossanova model with resampling results.
        which: What to plot:
            - "params": Model coefficients (from boot_samples_ or perm_samples_)
            - "mee": Marginal effects (from boot_mee_samples_)
        include_intercept: Include intercept in coefficient plots.
        terms: Subset of terms to plot. If None, plot all.
        height: Height of each facet in inches.
        aspect: Aspect ratio of each facet (width = height * aspect).
        col_wrap: Number of columns before wrapping.
        palette: Color palette name (default: BOSSANOVA_STYLE palette).
        show_ci: For bootstrap, shade confidence interval region.
        show_pvalue: For permutation, annotate p-value.
        fill: Fill under density curve.

    Returns:
        Seaborn FacetGrid with one facet per parameter.

    Raises:
        RuntimeError: If no resampling results available.
        ValueError: If requested context has no samples.

    Examples:
        >>> from bossanova import lm, viz, load_dataset
        >>> mtcars = load_dataset("mtcars")
        >>> model = lm("mpg ~ wt + hp", data=mtcars).fit()

        >>> # Bootstrap distributions (auto-saved for n<=5000)
        >>> model.infer(how="boot", n=999)
        >>> viz.plot_resamples(model)

        >>> # Permutation null distributions
        >>> model.infer(how="perm", n=999)
        >>> viz.plot_resamples(model)

        >>> # MEE bootstrap
        >>> model.mee("wt").infer(how="boot", n=999)
        >>> viz.plot_resamples(model, which="mee")

    See Also:
        plot_params: Forest plot of parameter estimates.
    """
    import seaborn as sns

    # Extract samples and metadata based on context
    samples, observed, names, ci_info, pvalue_info, resample_type = (
        _extract_resample_data(model, which, include_intercept)
    )

    # Filter to specific terms if requested
    if terms is not None:
        mask = [n in terms for n in names]
        indices = [i for i, m in enumerate(mask) if m]
        samples = samples[:, indices]
        observed = {names[i]: observed[names[i]] for i in indices}
        if ci_info:
            ci_info = {names[i]: ci_info[names[i]] for i in indices}
        if pvalue_info:
            pvalue_info = {names[i]: pvalue_info[names[i]] for i in indices}
        names = [names[i] for i in indices]

    if len(names) == 0:
        raise ValueError("No terms to plot after filtering.")

    # Reshape to long format for FacetGrid
    long_data = []
    for i, name in enumerate(names):
        for val in samples[:, i]:
            long_data.append({"term": name, "value": float(val)})
    plot_df = pl.DataFrame(long_data)

    # Determine col_wrap based on number of terms
    n_terms = len(names)
    effective_col_wrap = min(col_wrap, n_terms)

    style = BOSSANOVA_STYLE
    if palette is None:
        palette = style["palette"]

    # Build FacetGrid kwargs
    facet_kwargs = build_facetgrid_kwargs(
        data=plot_df,
        height=height,
        aspect=aspect,
        col="term",
        col_wrap=effective_col_wrap,
        palette=palette,
        sharex=False,  # Each param has different scale
        sharey=False,
    )

    # Create FacetGrid
    g = sns.FacetGrid(**facet_kwargs)

    # Map the density drawing function
    g.map_dataframe(
        _draw_resample_density,
        observed=observed,
        ci_info=ci_info,
        pvalue_info=pvalue_info,
        resample_type=resample_type,
        style=style,
        fill=fill,
        show_ci=show_ci,
        show_pvalue=show_pvalue,
    )

    # Title based on resample type
    if resample_type == "bootstrap":
        title = "Bootstrap Distribution"
    else:
        title = "Permutation Null Distribution"

    finalize_facetgrid(g, title=title, xlabel="Value", ylabel="Density")

    return g


def _extract_resample_data(
    model: BaseModel,
    which: Literal["params", "mee"],
    include_intercept: bool,
) -> tuple[np.ndarray, dict, list, dict | None, dict | None, str]:
    """Extract resampling data from model.

    Returns:
        Tuple of (samples, observed, names, ci_info, pvalue_info, resample_type)
        - samples: Array of shape [n_resamples, n_params]
        - observed: Dict mapping term name to observed value
        - names: List of term names
        - ci_info: Dict mapping term name to (ci_lower, ci_upper) or None
        - pvalue_info: Dict mapping term name to p-value or None
        - resample_type: "bootstrap" or "permutation"
    """
    ci_info = None
    pvalue_info = None

    if which == "mee":
        # MEE bootstrap samples
        boot_mee = getattr(model, "boot_mee_samples_", None)
        if boot_mee is None:
            raise RuntimeError(
                "No MEE bootstrap samples. Call .mee().infer(how='boot') "
                "with save_resamples=True (default for n<=5000)."
            )
        samples = np.asarray(boot_mee)
        # Get observed values and names from result_mee
        result_mee = model.result_mee
        if result_mee is None:
            raise RuntimeError("No MEE results found.")

        # Build names from term + level columns
        if "level" in result_mee.columns:
            names = [
                f"{t}[{lv}]" if lv else t
                for t, lv in zip(
                    result_mee["term"].to_list(),
                    result_mee["level"].to_list(),
                )
            ]
        else:
            names = result_mee["term"].to_list()

        observed = dict(zip(names, result_mee["estimate"].to_list()))

        # Get CIs if available
        if "ci_lower" in result_mee.columns and "ci_upper" in result_mee.columns:
            ci_info = {
                name: (lo, hi)
                for name, lo, hi in zip(
                    names,
                    result_mee["ci_lower"].to_list(),
                    result_mee["ci_upper"].to_list(),
                )
            }

        return samples, observed, names, ci_info, None, "bootstrap"

    # Parameter-level resampling
    boot_result = getattr(model, "boot_samples_", None)
    perm_result = getattr(model, "perm_samples_", None)

    if boot_result is not None:
        samples = np.asarray(boot_result.boot_samples)
        observed_arr = np.asarray(boot_result.observed)
        names = list(boot_result.param_names)
        ci_lower = np.asarray(boot_result.ci_lower)
        ci_upper = np.asarray(boot_result.ci_upper)

        # Filter intercept if needed
        if not include_intercept:
            mask = [not _is_intercept(n) for n in names]
            indices = [i for i, m in enumerate(mask) if m]
            samples = samples[:, indices]
            observed_arr = observed_arr[indices]
            ci_lower = ci_lower[indices]
            ci_upper = ci_upper[indices]
            names = [names[i] for i in indices]

        observed = dict(zip(names, observed_arr.tolist()))
        ci_info = {
            name: (lo, hi)
            for name, lo, hi in zip(names, ci_lower.tolist(), ci_upper.tolist())
        }

        return samples, observed, names, ci_info, None, "bootstrap"

    elif perm_result is not None:
        samples = np.asarray(perm_result.null_distribution)
        observed_arr = np.asarray(perm_result.observed)
        names = list(perm_result.param_names)
        pvalues = np.asarray(perm_result.pvalues)

        # Filter intercept if needed
        if not include_intercept:
            mask = [not _is_intercept(n) for n in names]
            indices = [i for i, m in enumerate(mask) if m]
            samples = samples[:, indices]
            observed_arr = observed_arr[indices]
            pvalues = pvalues[indices]
            names = [names[i] for i in indices]

        observed = dict(zip(names, observed_arr.tolist()))
        pvalue_info = dict(zip(names, pvalues.tolist()))

        return samples, observed, names, None, pvalue_info, "permutation"

    else:
        raise RuntimeError(
            "No resampling results found. Call .infer(how='boot') or "
            ".infer(how='perm') with save_resamples=True (default for n<=5000)."
        )


def _is_intercept(name: str) -> bool:
    """Check if a term name represents an intercept."""
    lower = name.lower()
    return lower in ("intercept", "(intercept)", "1")


def _draw_resample_density(
    data,  # Polars or pandas DataFrame from FacetGrid
    *,
    observed: dict[str, float],
    ci_info: dict[str, tuple[float, float]] | None,
    pvalue_info: dict[str, float] | None,
    resample_type: str,
    style: dict,
    fill: bool,
    show_ci: bool,
    show_pvalue: bool,
    **kwargs,
) -> None:
    """Draw density for a single parameter facet."""
    import matplotlib.pyplot as plt
    from scipy import stats

    ax = plt.gca()

    # Get term name from facet (works with both polars and pandas)
    term = list(data["term"])[0]
    values = np.asarray(data["value"])
    obs = observed[term]

    # Compute KDE
    if len(np.unique(values)) < 2:
        # Degenerate case - all same value
        ax.axvline(values[0], color="C0", linewidth=2, label="Samples")
        ax.axvline(obs, color="C3", linestyle="--", linewidth=2, label="Observed")
        ax.set_xlim(values[0] - 1, values[0] + 1)
        return

    kde = stats.gaussian_kde(values)
    x_min, x_max = values.min(), values.max()
    x_pad = (x_max - x_min) * 0.1
    x_range = np.linspace(x_min - x_pad, x_max + x_pad, 200)
    density = kde(x_range)

    # Plot density line
    color = "C0"
    ax.plot(x_range, density, color=color, linewidth=1.5)

    # Fill under curve if requested
    if fill:
        ax.fill_between(x_range, density, alpha=style["ci_alpha"], color=color)

    # Observed value line
    ax.axvline(obs, color="C3", linestyle="--", linewidth=2, label="Observed")

    # For bootstrap: shade CI region
    if resample_type == "bootstrap" and show_ci and ci_info is not None:
        ci_lo, ci_hi = ci_info[term]
        ci_mask = (x_range >= ci_lo) & (x_range <= ci_hi)
        if ci_mask.any():
            ax.fill_between(
                x_range[ci_mask],
                density[ci_mask],
                alpha=0.2,
                color="C2",
                label="95% CI",
            )
        # Draw CI bounds as vertical lines
        ax.axvline(ci_lo, color="C2", linestyle=":", linewidth=1, alpha=0.7)
        ax.axvline(ci_hi, color="C2", linestyle=":", linewidth=1, alpha=0.7)

    # For permutation: annotate p-value
    if resample_type == "permutation" and show_pvalue and pvalue_info is not None:
        p = pvalue_info[term]
        p_str = f"p = {p:.3f}" if p >= 0.001 else "p < 0.001"
        ax.annotate(
            p_str,
            xy=(0.95, 0.95),
            xycoords="axes fraction",
            ha="right",
            va="top",
            fontsize=style["font_size"],
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
        )

    # Clean up axes
    ax.set_ylabel("")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
