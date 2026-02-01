"""Display utilities for model summaries.

Shared formatting functions used by model summary() methods to ensure
consistent output across lm, glm, ridge, lmer, and glmer.
"""

from __future__ import annotations

__all__ = ["print_signif_codes", "print_coefficient_table", "print_random_effects"]

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl

    from bossanova.models.base.mixed import BaseMixedModel


def print_signif_codes() -> None:
    """Print significance codes legend.

    Standard R-style significance codes used in coefficient tables.
    """
    print("---")
    print("Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1")
    print()


def print_coefficient_table(
    coef_table: pl.DataFrame,
    decimals: int = 3,
    stat_label: str = "t value",
    p_label: str = "Pr(>|t|)",
    show_df: bool = False,
    inference: str | None = None,
) -> None:
    """Print formatted coefficient table with significance stars.

    Args:
        coef_table: DataFrame with columns: term, estimate, se.
            For asymptotic inference: also statistic, p_value (and optionally df).
            For bootstrap/perm: also ci_lower, ci_upper.
        decimals: Number of decimal places for estimates and standard errors.
        stat_label: Label for test statistic column ("t value" or "z value").
        p_label: Label for p-value column ("Pr(>|t|)" or "Pr(>|z|)").
        show_df: Whether to display degrees of freedom column (for lmer).
        inference: Inference method used (e.g., "asymp", "boot", "perm").
            If provided, prints a header indicating the method.

    Examples:
        >>> print_coefficient_table(model._result_params)
                     Estimate Std. Error   t value    Pr(>|t|)
        (Intercept)    37.285      1.878    19.858   < 2e-16 ***
        wt             -3.878      0.633    -6.129   1.1e-06 ***
    """
    columns = coef_table.columns
    has_pvalue = "p_value" in columns
    has_statistic = "statistic" in columns
    has_ci = "ci_lower" in columns and "ci_upper" in columns
    has_n_resamples = "n_resamples" in columns

    # Print inference method header if specified
    if inference and inference not in ("asymp", "wald", "satterthwaite"):
        # Include n_resamples in header for boot/perm
        if has_n_resamples:
            n_resamples = coef_table["n_resamples"][0]
            print(f"[Inference: {inference}, n_resamples: {n_resamples}]")
        else:
            print(f"[Inference: {inference}]")

    # Calculate term column width dynamically based on longest term name
    term_width = max(len(row["term"]) for row in coef_table.iter_rows(named=True))

    # Determine table format based on available columns
    if has_pvalue and has_statistic:
        # Asymptotic inference: show statistic and p-value
        from bossanova.ops.inference import format_pvalue_with_stars

        if show_df:
            print(
                f"{'':>{term_width}s} {'Estimate':>10s} {'Std. Error':>11s} "
                f"{'df':>6s} {stat_label:>9s} {p_label:>11s}"
            )
        else:
            print(
                f"{'':>{term_width}s} {'Estimate':>10s} {'Std. Error':>11s} "
                f"{stat_label:>9s} {p_label:>11s}"
            )

        for row in coef_table.iter_rows(named=True):
            p_str = format_pvalue_with_stars(row["p_value"])
            if show_df:
                print(
                    f"{row['term']:{term_width}s} {row['estimate']:10.{decimals}f} "
                    f"{row['se']:11.{decimals}f} {row['df']:6.1f} "
                    f"{row['statistic']:9.3f}  {p_str}"
                )
            else:
                print(
                    f"{row['term']:{term_width}s} {row['estimate']:10.{decimals}f} "
                    f"{row['se']:11.{decimals}f} {row['statistic']:9.3f}  {p_str}"
                )
    elif has_ci:
        # Bootstrap/perm inference: show confidence intervals
        print(
            f"{'':>{term_width}s} {'Estimate':>10s} {'Std. Error':>11s} "
            f"{'CI Lower':>10s} {'CI Upper':>10s}"
        )

        for row in coef_table.iter_rows(named=True):
            print(
                f"{row['term']:{term_width}s} {row['estimate']:10.{decimals}f} "
                f"{row['se']:11.{decimals}f} {row['ci_lower']:10.{decimals}f} "
                f"{row['ci_upper']:10.{decimals}f}"
            )
    else:
        # Minimal: just estimate and SE
        print(f"{'':>{term_width}s} {'Estimate':>10s} {'Std. Error':>11s}")

        for row in coef_table.iter_rows(named=True):
            print(
                f"{row['term']:{term_width}s} {row['estimate']:10.{decimals}f} "
                f"{row['se']:11.{decimals}f}"
            )


def print_random_effects(
    model: BaseMixedModel,
    var_decimals: int = 2,
) -> None:
    """Print random effects variance components table.

    Formats the random effects section of a mixed model summary, including:
    - Variance and standard deviation for each random effect
    - Correlations between random effects within the same group
    - Number of observations and group counts

    Args:
        model: A fitted mixed model (lmer or glmer) with varying_var, varying_corr,
            ngroups, and _n attributes.
        var_decimals: Number of decimal places for variance/SD (2 for lmer, 4 for glmer).

    Examples:
        >>> print_random_effects(model, var_decimals=2)
        Random effects:
         Subject  (Intercept)   612.10    24.74
                  Days           35.07     5.92    0.07
         Residual              654.94    25.59
        Number of obs: 180, groups:  Subject, 18
    """
    import polars as pl

    print("Random effects:")
    varying_var = model.varying_var
    varying_corr = model.varying_corr

    # Print variance components
    current_group = None
    for row in varying_var.iter_rows(named=True):
        group = row["group"]
        effect = row["effect"]
        var = row["variance"]
        sd = row["sd"]

        if group == "Residual":
            # Residual variance (lmer only)
            print(
                f" Residual             {var:>8.{var_decimals}f}   {sd:>6.{var_decimals}f}"
            )
        elif group != current_group:
            # First effect in group
            current_group = group
            print(
                f" {group:8s} {effect:12s} {var:>8.{var_decimals}f}   {sd:>6.{var_decimals}f}"
            )
        else:
            # Subsequent effects - check for correlation
            corr_row = varying_corr.filter(
                (pl.col("group") == group) & (pl.col("effect2") == effect)
            )
            if len(corr_row) > 0:
                corr = corr_row["corr"][0]
                print(
                    f" {'':8s} {effect:12s} {var:>8.{var_decimals}f}   "
                    f"{sd:>6.{var_decimals}f}   {corr:>5.2f}"
                )
            else:
                print(
                    f" {'':8s} {effect:12s} {var:>8.{var_decimals}f}   {sd:>6.{var_decimals}f}"
                )

    # Number of observations and groups
    ngroups_str = ", ".join(
        [f"{name}, {count}" for name, count in model.ngroups.items()]
    )
    print(f"Number of obs: {model._n}, groups:  {ngroups_str}")
    print()
