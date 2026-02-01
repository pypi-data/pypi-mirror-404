"""Monte Carlo simulation harness for parameter recovery studies.

Provides infrastructure for running simulation studies and collecting
results for bias, coverage, and power analysis.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import polars as pl

from bossanova.simulation import metrics

__all__ = ["MonteCarloResult", "monte_carlo"]


@dataclass
class MonteCarloResult:
    """Results from a Monte Carlo simulation study.

    Stores estimates, standard errors, confidence intervals, and p-values
    from repeated simulations, along with ground truth parameters.

    Attributes:
        estimates: Array of shape (n_sims, n_params) with coefficient estimates.
        std_errors: Array of shape (n_sims, n_params) with standard errors.
        ci_lower: Array of shape (n_sims, n_params) with CI lower bounds.
        ci_upper: Array of shape (n_sims, n_params) with CI upper bounds.
        p_values: Array of shape (n_sims, n_params) with p-values.
        true_params: Dictionary with true parameter values (e.g., {"beta": [1.0, 2.0]}).
        param_names: List of parameter names matching array columns.
        n_sims: Number of simulations run.
        n_failed: Number of simulations that failed to converge.

    Examples:
        >>> result = monte_carlo(
        ...     dgp_fn=generate_lm_data,
        ...     dgp_params={"n": 100, "beta": [1.0, 2.0], "sigma": 1.0},
        ...     fit_fn=lambda d: lm("y ~ x1", data=d).fit(),
        ...     n_sims=500,
        ... )
        >>> result.bias("x1")  # Should be close to 0
        >>> result.coverage("x1")  # Should be close to 0.95
    """

    estimates: np.ndarray
    std_errors: np.ndarray
    ci_lower: np.ndarray
    ci_upper: np.ndarray
    p_values: np.ndarray
    true_params: dict[str, Any]
    param_names: list[str]
    n_sims: int = 0
    n_failed: int = 0
    _param_index: dict[str, int] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        """Build parameter name to index mapping."""
        self._param_index = {name: i for i, name in enumerate(self.param_names)}

    def _get_idx(self, param: str | int) -> int:
        """Get array index for a parameter."""
        if isinstance(param, int):
            return param
        if param not in self._param_index:
            raise KeyError(
                f"Unknown parameter '{param}'. "
                f"Available: {list(self._param_index.keys())}"
            )
        return self._param_index[param]

    def _get_true_value(self, param: str | int) -> float:
        """Get true value for a parameter."""
        idx = self._get_idx(param)
        beta = self.true_params.get("beta", [])
        if idx < len(beta):
            return float(beta[idx])
        raise ValueError(f"No true value found for parameter index {idx}")

    def bias(self, param: str | int) -> float:
        """Compute bias for a parameter: E[β̂] - β_true.

        Args:
            param: Parameter name or index.

        Returns:
            Bias value.
        """
        idx = self._get_idx(param)
        true_value = self._get_true_value(param)
        return metrics.bias(self.estimates[:, idx], true_value)

    def rmse(self, param: str | int) -> float:
        """Compute RMSE for a parameter.

        Args:
            param: Parameter name or index.

        Returns:
            Root mean squared error.
        """
        idx = self._get_idx(param)
        true_value = self._get_true_value(param)
        return metrics.rmse(self.estimates[:, idx], true_value)

    def mean_se(self, param: str | int) -> float:
        """Compute mean estimated standard error for a parameter.

        Args:
            param: Parameter name or index.

        Returns:
            Mean SE across simulations.
        """
        idx = self._get_idx(param)
        return metrics.mean_se(self.std_errors[:, idx])

    def empirical_se(self, param: str | int) -> float:
        """Compute empirical SE (SD of estimates) for a parameter.

        Args:
            param: Parameter name or index.

        Returns:
            Empirical SE.
        """
        idx = self._get_idx(param)
        return metrics.empirical_se(self.estimates[:, idx])

    def coverage(self, param: str | int, level: float = 0.95) -> float:
        """Compute coverage probability for a parameter.

        Args:
            param: Parameter name or index.
            level: Confidence level (default 0.95). Currently only used
                for documentation; actual CIs come from the model.

        Returns:
            Coverage probability (0 to 1).
        """
        idx = self._get_idx(param)
        true_value = self._get_true_value(param)
        return metrics.coverage(
            self.ci_lower[:, idx],
            self.ci_upper[:, idx],
            true_value,
        )

    def type1_rate(self, param: str | int, alpha: float = 0.05) -> float:
        """Compute Type I error rate for a parameter.

        This is the rejection rate when the true effect is zero.
        Use this for parameters where true_value = 0.

        Args:
            param: Parameter name or index.
            alpha: Significance level (default 0.05).

        Returns:
            Type I error rate (should be ≈ alpha if correctly calibrated).
        """
        idx = self._get_idx(param)
        return metrics.rejection_rate(self.p_values[:, idx], alpha)

    def power(self, param: str | int, alpha: float = 0.05) -> float:
        """Compute power for a parameter.

        This is the rejection rate when the true effect is non-zero.
        Use this for parameters where true_value ≠ 0.

        Args:
            param: Parameter name or index.
            alpha: Significance level (default 0.05).

        Returns:
            Power (probability of correctly rejecting H0).
        """
        # Power is computed the same way as type1_rate, just interpreted
        # differently based on whether the true effect is zero or not
        return self.type1_rate(param, alpha)

    def summary(self) -> pl.DataFrame:
        """Return summary DataFrame with all metrics for all parameters.

        Returns:
            DataFrame with columns: param, true_value, mean_est, bias,
            rmse, mean_se, empirical_se, coverage, rejection_rate.
        """
        rows = []
        for name in self.param_names:
            idx = self._get_idx(name)
            true_val = self._get_true_value(name)
            rows.append(
                {
                    "param": name,
                    "true_value": true_val,
                    "mean_est": float(np.mean(self.estimates[:, idx])),
                    "bias": self.bias(name),
                    "rmse": self.rmse(name),
                    "mean_se": self.mean_se(name),
                    "empirical_se": self.empirical_se(name),
                    "coverage": self.coverage(name),
                    "rejection_rate": self.type1_rate(name),
                }
            )
        return pl.DataFrame(rows)


def monte_carlo(
    dgp_fn: Callable[..., tuple[pl.DataFrame, dict]],
    dgp_params: dict[str, Any],
    fit_fn: Callable[[pl.DataFrame], Any],
    n_sims: int = 1000,
    seed: int = 42,
    conf_level: float = 0.95,
) -> MonteCarloResult:
    """Run a Monte Carlo simulation study.

    Generates data from a DGP, fits models, and collects results
    for parameter recovery analysis.

    Args:
        dgp_fn: Data generating function that returns (data, true_params).
            Must accept a `seed` parameter.
        dgp_params: Parameters to pass to dgp_fn (excluding seed).
        fit_fn: Function that takes a DataFrame and returns a fitted model.
            The model must have: coef, bse, pvalues, and confint() method.
        n_sims: Number of simulations to run (default 1000).
        seed: Base random seed (default 42). Each simulation uses seed + i.
        conf_level: Confidence level for CIs (default 0.95).

    Returns:
        MonteCarloResult with collected estimates and metrics.

    Examples:
        >>> from bossanova import lm
        >>> from bossanova.simulation import generate_lm_data
        >>> result = monte_carlo(
        ...     dgp_fn=generate_lm_data,
        ...     dgp_params={"n": 100, "beta": [1.0, 2.0], "sigma": 1.0},
        ...     fit_fn=lambda d: lm("y ~ x1", data=d).fit(),
        ...     n_sims=500,
        ... )
        >>> abs(result.bias("x1")) < 0.1
        True
    """
    # Storage for results
    all_estimates = []
    all_std_errors = []
    all_ci_lower = []
    all_ci_upper = []
    all_p_values = []
    param_names: list[str] | None = None
    true_params: dict[str, Any] | None = None
    n_failed = 0

    for i in range(n_sims):
        sim_seed = seed + i

        # Generate data
        data, params = dgp_fn(**dgp_params, seed=sim_seed)
        if true_params is None:
            true_params = params

        # Fit model
        try:
            model = fit_fn(data)
        except Exception:
            n_failed += 1
            continue

        # Extract results
        # Get parameter names from model on first successful fit
        if param_names is None:
            # Try to get names from params DataFrame
            if hasattr(model, "params") and isinstance(model.params, pl.DataFrame):
                param_names = model.params["term"].to_list()
            else:
                # Fall back to generic names
                n_params = len(model.coef_)
                param_names = [f"param_{i}" for i in range(n_params)]

        # Collect estimates
        all_estimates.append(np.asarray(model.coef_))

        # Extract standard errors (different models have different APIs)
        if hasattr(model, "bse"):
            all_std_errors.append(np.asarray(model.bse))
        elif hasattr(model, "result_params") and isinstance(
            model.result_params, pl.DataFrame
        ):
            # GLM stores SE in result_params DataFrame
            all_std_errors.append(model.result_params["se"].to_numpy())
        else:
            # Fall back to zeros if no SE available
            all_std_errors.append(np.zeros_like(model.coef_))

        # Extract p-values (different models have different APIs)
        if hasattr(model, "pvalues"):
            all_p_values.append(np.asarray(model.pvalues))
        elif hasattr(model, "result_params") and isinstance(
            model.result_params, pl.DataFrame
        ):
            # GLM stores p-values in result_params DataFrame
            all_p_values.append(model.result_params["p_value"].to_numpy())
        else:
            # Fall back to ones if no p-values available
            all_p_values.append(np.ones_like(model.coef_))

        # Get confidence intervals from result_params
        ci = model.result_params.recompute_ci(conf_level)
        all_ci_lower.append(ci["ci_lower"].to_numpy())
        all_ci_upper.append(ci["ci_upper"].to_numpy())

    # Stack results
    estimates = np.vstack(all_estimates)
    std_errors = np.vstack(all_std_errors)
    ci_lower = np.vstack(all_ci_lower)
    ci_upper = np.vstack(all_ci_upper)
    p_values = np.vstack(all_p_values)

    return MonteCarloResult(
        estimates=estimates,
        std_errors=std_errors,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        p_values=p_values,
        true_params=true_params or {},
        param_names=param_names or [],
        n_sims=n_sims - n_failed,
        n_failed=n_failed,
    )
