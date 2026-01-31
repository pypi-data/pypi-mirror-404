"""Result dataclasses for resampling procedures.

This module provides container classes for results from permutation tests,
bootstrap procedures, and cross-validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import numpy as np
import polars as pl

if TYPE_CHECKING:
    from jax import Array

__all__ = [
    "PermutationResult",
    "BootstrapResult",
    "CVResult",
]


@dataclass
class PermutationResult:
    """Results from a permutation test.

    Attributes:
        observed: Observed test statistics, shape [n_params].
        null_distribution: Null distribution from permutations, shape [n_perm, n_params].
        pvalues: P-values for each parameter, shape [n_params].
        param_names: Names of parameters being tested.
        n_perm: Number of permutations performed.
        test_stat: Name of the test statistic used.
        alternative: Type of alternative hypothesis.
    """

    observed: Array
    null_distribution: Array
    pvalues: Array
    param_names: list[str]
    n_perm: int
    test_stat: str
    alternative: Literal["two-sided", "greater", "less"]

    def summary(self) -> str:
        """Generate a formatted summary of permutation test results.

        Returns:
            Formatted summary table as string.
        """
        obs_np = np.asarray(self.observed)
        pval_np = np.asarray(self.pvalues)

        # Handle scalar case
        if obs_np.ndim == 0:
            obs_np = np.array([obs_np])
            pval_np = np.array([pval_np])

        n_params = len(obs_np)

        lines = []
        lines.append("=" * 70)
        lines.append(f"Permutation Test Results ({self.test_stat})")
        lines.append("=" * 70)
        lines.append(f"Number of permutations: {self.n_perm}")
        lines.append(f"Alternative hypothesis: {self.alternative}")
        lines.append("")
        lines.append(f"{'Parameter':<20} {'Observed':>15} {'P-value':>15}")
        lines.append("-" * 70)

        for i in range(n_params):
            param_name = (
                self.param_names[i] if i < len(self.param_names) else f"param_{i}"
            )
            obs_val = obs_np[i]
            pval = pval_np[i]

            sig_marker = ""
            if pval < 0.001:
                sig_marker = " ***"
            elif pval < 0.01:
                sig_marker = " **"
            elif pval < 0.05:
                sig_marker = " *"

            lines.append(f"{param_name:<20} {obs_val:>15.6f} {pval:>15.6f}{sig_marker}")

        lines.append("-" * 70)
        lines.append("Significance codes: 0 '***' 0.001 '**' 0.01 '*' 0.05")
        lines.append("=" * 70)

        return "\n".join(lines)

    def to_dataframe(self) -> pl.DataFrame:
        """Convert results to a polars DataFrame.

        Returns:
            DataFrame with columns [term, observed, p_value].
        """
        obs_np = np.asarray(self.observed)
        pval_np = np.asarray(self.pvalues)

        if obs_np.ndim == 0:
            obs_np = np.array([obs_np])
            pval_np = np.array([pval_np])

        return pl.DataFrame(
            {
                "term": self.param_names,
                "observed": obs_np,
                "p_value": pval_np,
            }
        )


@dataclass
class BootstrapResult:
    """Results from a bootstrap procedure.

    Attributes:
        observed: Observed statistics, shape [n_params].
        boot_samples: Bootstrap samples, shape [n_boot, n_params].
        ci_lower: Lower confidence bounds, shape [n_params].
        ci_upper: Upper confidence bounds, shape [n_params].
        param_names: Names of parameters.
        n_boot: Number of bootstrap samples.
        ci_type: Type of confidence interval ("percentile", "basic", or "bca").
        level: Confidence level (e.g., 0.95).
        term_types: Optional list indicating "fixef" or "ranef" for each parameter.
            Only populated for mixed model bootstrap with which="all".
    """

    observed: Array
    boot_samples: Array
    ci_lower: Array
    ci_upper: Array
    param_names: list[str]
    n_boot: int
    ci_type: Literal["percentile", "basic", "bca"]
    level: float
    term_types: list[str] | None = None

    @property
    def ci(self) -> tuple[Array, Array]:
        """Return confidence intervals as a tuple (lower, upper)."""
        return self.ci_lower, self.ci_upper

    @property
    def se(self) -> Array:
        """Bootstrap standard errors (std of boot_samples)."""
        return np.std(np.asarray(self.boot_samples), axis=0)

    def summary(self) -> str:
        """Generate a formatted summary of bootstrap results.

        Returns:
            Formatted summary table as string.
        """
        obs_np = np.asarray(self.observed)
        lower_np = np.asarray(self.ci_lower)
        upper_np = np.asarray(self.ci_upper)
        se_np = np.asarray(self.se)

        if obs_np.ndim == 0:
            obs_np = np.array([obs_np])
            lower_np = np.array([lower_np])
            upper_np = np.array([upper_np])
            se_np = np.array([se_np])

        n_params = len(obs_np)
        ci_percent = int(self.level * 100)

        lines = []
        lines.append("=" * 80)
        lines.append(f"Bootstrap Results ({self.ci_type} CI)")
        lines.append("=" * 80)
        lines.append(f"Number of bootstrap samples: {self.n_boot}")
        lines.append(f"Confidence level: {self.level:.1%}")
        lines.append("")
        lines.append(
            f"{'Parameter':<20} {'Observed':>12} {'Boot SE':>12} "
            f"{ci_percent}% CI Lower  {ci_percent}% CI Upper"
        )
        lines.append("-" * 80)

        for i in range(n_params):
            param_name = (
                self.param_names[i] if i < len(self.param_names) else f"param_{i}"
            )
            lines.append(
                f"{param_name:<20} {obs_np[i]:>12.6f} {se_np[i]:>12.6f} "
                f"{lower_np[i]:>12.6f}   {upper_np[i]:>12.6f}"
            )

        lines.append("-" * 80)
        lines.append(
            f"Note: Standard errors computed from {self.n_boot} bootstrap samples"
        )
        lines.append("=" * 80)

        return "\n".join(lines)

    def to_dataframe(self) -> pl.DataFrame:
        """Convert results to a polars DataFrame.

        Returns:
            DataFrame with columns [term, term_type, observed, se, ci_lower, ci_upper].
            The term_type column is included when available (mixed model bootstrap).
        """
        obs_np = np.asarray(self.observed)
        se_np = np.asarray(self.se)
        lower_np = np.asarray(self.ci_lower)
        upper_np = np.asarray(self.ci_upper)

        if obs_np.ndim == 0:
            obs_np = np.array([obs_np])
            se_np = np.array([se_np])
            lower_np = np.array([lower_np])
            upper_np = np.array([upper_np])

        data = {
            "term": self.param_names,
            "observed": obs_np,
            "se": se_np,
            "ci_lower": lower_np,
            "ci_upper": upper_np,
        }

        # Include term_type column when available (mixed model bootstrap)
        if self.term_types is not None:
            data["term_type"] = self.term_types

        return pl.DataFrame(data)


@dataclass
class CVResult:
    """Results from cross-validation.

    Attributes:
        scores: Dictionary mapping metric names to arrays of per-fold scores.
        mean_scores: Mean score for each metric across folds.
        std_scores: Standard deviation of scores for each metric across folds.
        n_folds: Number of cross-validation folds.
        cv_type: Type of cross-validation ("kfold" or "loo").
        predictions: Out-of-fold predictions if return_predictions=True.
        actuals: Actual values corresponding to predictions.
    """

    scores: dict[str, list[float]]
    mean_scores: dict[str, float]
    std_scores: dict[str, float]
    n_folds: int
    cv_type: str
    predictions: np.ndarray | None = None
    actuals: np.ndarray | None = None

    def summary(self) -> str:
        """Generate a formatted summary of cross-validation results.

        Returns:
            Formatted summary table as string.
        """
        lines = []
        lines.append("=" * 70)
        lines.append(f"Cross-Validation Results ({self.cv_type})")
        lines.append("=" * 70)
        lines.append(f"Number of folds: {self.n_folds}")
        lines.append("")
        lines.append(f"{'Metric':<20} {'Mean':>15} {'Std':>15}")
        lines.append("-" * 70)

        for metric in self.mean_scores:
            mean_val = self.mean_scores[metric]
            std_val = self.std_scores[metric]
            lines.append(f"{metric:<20} {mean_val:>15.6f} {std_val:>15.6f}")

        lines.append("-" * 70)

        if self.predictions is not None:
            lines.append(
                f"Note: Out-of-fold predictions available ({len(self.predictions)} obs)"
            )

        lines.append("=" * 70)

        return "\n".join(lines)

    def to_dataframe(self) -> pl.DataFrame:
        """Convert per-fold scores to a polars DataFrame.

        Returns:
            DataFrame with columns [fold, mse, rmse, mae, r2].
        """
        n_folds = len(next(iter(self.scores.values())))

        data = {"fold": list(range(1, n_folds + 1))}
        for metric, values in self.scores.items():
            data[metric] = values

        return pl.DataFrame(data)
