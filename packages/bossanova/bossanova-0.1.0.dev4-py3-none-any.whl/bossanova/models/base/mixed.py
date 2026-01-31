"""Base class for mixed-effects models (lmer, glmer)."""

from __future__ import annotations

__all__ = ["BaseMixedModel"]

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Literal

import numpy as np

# Conditional JAX import for Pyodide compatibility
try:
    import jax.numpy as jnp
except ImportError:
    import numpy as jnp  # type: ignore[no-redef]
import polars as pl
import scipy.sparse as sp

from bossanova.models.base.model import BaseModel
from bossanova.ops.lambda_builder import build_lambda_sparse
from bossanova.results.builders import (
    build_ranef_dataframe,
    build_varying_corr_df,
    build_varying_var_df,
)

if TYPE_CHECKING:
    from typing_extensions import Self
    from pandas import DataFrame as PandasDataFrame
    from bossanova.results.wrappers import ResultFit


class BaseMixedModel(BaseModel, ABC):
    """Base class for mixed-effects models.

    Provides shared functionality for lmer and glmer:
    - Random effects formula parsing (including || expansion)
    - Z matrix construction
    - Random effects (BLUPs) computation
    - Shared properties (theta, ranef, ngroups, etc.)
    - Shared methods (simulate, confint)
    - Theta parameter lower bounds computation

    Subclasses must implement:
    - fit(): Model-specific optimization
    - _compute_result_params(): Build coefficient table
    - _compute_result_model(): Build fit statistics
    - _compute_inference(): Statistical inference
    - _simulate_response(): Response simulation
    - varying_var: Variance components property
    """

    def __init__(
        self,
        formula: str,
        data: pl.DataFrame | PandasDataFrame,
        reorder_terms: bool = True,
        missing: Literal["drop", "fail"] = "drop",
    ):
        """Initialize mixed-effects model.

        Args:
            formula: R-style model formula with random effects.
            data: Input data.
            reorder_terms: If True (default), reorder random effect terms by
                q = ℓ × p (levels × RE per group) to minimize Cholesky fill-in.
                This is a performance optimization with no statistical impact.
                Set to False for exact reproducibility with other software or
                to preserve formula order for debugging.
            missing: How to handle missing values ("drop" or "fail").

        Raises:
            ValueError: If formula contains no random effects terms.
        """
        # Store reorder_terms parameter
        self._reorder_terms = reorder_terms

        # Store original formula for user-facing .formula property
        # Note: DesignMatrixBuilder will expand || syntax internally
        self._original_formula = formula

        # Initialize permutation tracking (will be set during parsing if reordering occurs)
        self._term_permutation = None
        self._term_inverse_permutation = None

        # Call BaseModel init (creates DesignMatrixBuilder, parses fixed effects)
        super().__init__(formula, data, missing=missing)

        # Restore original formula (with ||) for user-facing property
        self._formula = formula

        # Initialize weights (will be set in fit() if provided)
        self._weights = None

        # Parse random effects from formula
        self._parse_random_effects()

        # Set fitted flag
        self.is_fitted = False

        # Type stubs for attributes set during fit()
        # These help quartodoc generate proper documentation
        self._coef: np.ndarray | None = None
        self._vcov: np.ndarray | None = None
        self._theta: np.ndarray | None = None
        self._u: np.ndarray | None = None
        self._ranef_df: pl.DataFrame | None = None
        self._optimizer_diagnostics: dict | None = None
        self._loglik: float | None = None
        self._deviance: float | None = None
        self._aic: float | None = None
        self._bic: float | None = None
        self._result_params: pl.DataFrame | None = None
        self._result_model: pl.DataFrame | None = None
        self._fitted_values: np.ndarray | None = None
        self._residuals: np.ndarray | None = None

    def _parse_random_effects(self) -> None:
        """Parse random effects from formula and build sparse Z matrix.

        This method uses DesignMatrixBuilder.build_re() which:
        1. Expands || syntax internally
        2. Parses RE terms from formula
        3. Builds sparse Z matrix with correct layout
        4. Extracts group information

        Raises:
            ValueError: If no random effects terms found in formula.
        """
        # Use the builder (already created by BaseModel._parse_formula())
        re_info = self._builder.build_re()

        # Check for random effects
        if re_info is None:
            raise ValueError(
                f"Formula '{self._formula}' contains no random effects terms. "
                "Use lm() for linear models without random effects."
            )

        # Extract all fields from RandomEffectsInfo
        self._Z = re_info.Z
        self._group_ids_list = re_info.group_ids_list
        self._n_groups_list = re_info.n_groups_list
        self._group_names = re_info.group_names
        self._random_names = re_info.random_names
        self._re_structure = re_info.re_structure
        self._X_re = re_info.X_re

        # Validate grouping variables have sufficient levels
        for i, (group_name, n_groups) in enumerate(
            zip(self._group_names, self._n_groups_list)
        ):
            # Check for single-level grouping variable
            if n_groups == 1:
                raise ValueError(
                    f"Grouping factor '{group_name}' has only 1 level. "
                    f"Random effects variance cannot be estimated with a single group. "
                    f"Use lm() instead, or check that the grouping variable is correct."
                )

            # Check for too many random effect levels (over-parameterized)
            # When n_groups >= n_obs, the model is overspecified
            if n_groups >= self._n:
                raise ValueError(
                    f"Grouping factor '{group_name}' has {n_groups} levels for "
                    f"{self._n} observations (ratio={n_groups / self._n:.2f}). "
                    f"This is overparameterized - random effects cannot be estimated "
                    f"when each observation is its own group. "
                    f"Use lm() with the grouping variable as a fixed effect instead."
                )

        # Handle term permutation for result ordering
        if re_info.term_permutation is not None:
            self._term_permutation = list(re_info.term_permutation)
            # Compute inverse permutation: inverse[order[i]] = i
            n_terms = len(self._term_permutation)
            if self._term_permutation != list(range(n_terms)):
                inverse = [0] * n_terms
                for i, idx in enumerate(self._term_permutation):
                    inverse[idx] = i
                self._term_inverse_permutation = inverse
            else:
                self._term_inverse_permutation = self._term_permutation

        # Store metadata for downstream use (lambda_builder, results)
        self._metadata = {
            "re_type": re_info.re_structure,
            "re_structures_list": re_info.re_structures_list,
            "random_names": self._random_names,
            "group_names": self._group_names,
            "n_groups": self._n_groups_list,
            "re_terms": self._random_names,
        }

    def _build_ranef(self) -> None:
        """Build random effects DataFrame from u vector.

        Converts spherical random effects u to BLUPs b = Lambda @ u
        and organizes by grouping factor.
        """
        # Compute BLUPs: b = Lambda @ u
        Lambda = build_lambda_sparse(
            self._theta,
            self._n_groups_list,
            self._re_structure,
            self._metadata,  # type: ignore[arg-type]
        )
        b = Lambda @ self._u

        # Convert b vector to ranef_dict structure
        ranef_dict = {}
        group_levels = {}

        # For crossed/nested: each factor has its own RE structure
        # For simple: all factors share the same RE structure
        if self._re_structure in ("crossed", "nested"):
            # Get per-factor RE counts from metadata
            re_structures_list = self._metadata.get("re_structures_list", None)
            if re_structures_list is None:
                # Default: intercept-only for each factor
                n_re_per_factor = [1] * len(self._n_groups_list)
            else:
                n_re_per_factor = []
                for rs in re_structures_list:
                    if rs == "intercept":
                        n_re_per_factor.append(1)
                    else:
                        # Slope structures have multiple REs
                        # This needs proper counting from metadata
                        n_re_per_factor.append(1)  # Conservative default
        else:
            # Simple/diagonal/slope: uniform RE count across factors
            if self._re_structure == "intercept":
                n_re_per_group = 1
            elif self._re_structure in ("diagonal", "slope"):
                n_re_per_group = len(self._random_names)
            else:
                n_re_per_group = 1
            n_re_per_factor = [n_re_per_group] * len(self._n_groups_list)

        # Extract group labels from original data (use Polars directly, no pandas)
        b_idx = 0
        all_random_names = []  # Collect per-factor random names
        for i, group_name in enumerate(self._group_names):
            n_groups = self._n_groups_list[i]
            n_re = n_re_per_factor[i]

            # Get unique levels for this group
            if group_name in self._data.columns:
                unique_levels = sorted(self._data[group_name].unique().to_list())
            else:
                # Fallback to numeric labels (e.g., for nested combo names)
                unique_levels = [str(j) for j in range(n_groups)]

            # Extract b values for this group
            group_b = b[b_idx : b_idx + n_groups * n_re]

            # Handle layout differences:
            # - "diagonal" uses blocked layout: [all_re1, all_re2, ...]
            # - Other structures use interleaved layout: [g1_re1, g1_re2, g2_re1, ...]
            if self._re_structure == "diagonal":
                # Blocked layout: reshape(n_re, n_groups).T to get (n_groups, n_re)
                group_b_matrix = group_b.reshape(n_re, n_groups).T
            else:
                # Interleaved layout: standard reshape
                group_b_matrix = group_b.reshape(n_groups, n_re)

            ranef_dict[group_name] = group_b_matrix
            group_levels[group_name] = [str(level) for level in unique_levels]

            # Track RE names per factor
            if n_re == 1:
                all_random_names.append(["Intercept"])
            else:
                all_random_names.append(self._random_names[:n_re])

            b_idx += n_groups * n_re

        # Reorder to formula order for user-facing output
        if self._term_inverse_permutation is not None:
            inv = self._term_inverse_permutation
            formula_order_names = [self._group_names[inv[i]] for i in range(len(inv))]
            ranef_dict = {name: ranef_dict[name] for name in formula_order_names}
            group_levels = {name: group_levels[name] for name in formula_order_names}

        # For crossed/nested with intercept-only, use "Intercept" as the single name
        if self._re_structure in ("crossed", "nested") and all(
            n == 1 for n in n_re_per_factor
        ):
            random_names_for_df = ["Intercept"]
        else:
            random_names_for_df = self._random_names

        # Build DataFrame
        self._ranef_df = build_ranef_dataframe(
            ranef_dict=ranef_dict,
            group_levels=group_levels,
            random_names=random_names_for_df,
        )

    # =========================================================================
    # Abstract methods (subclasses must implement)
    # =========================================================================

    @abstractmethod
    def fit(self, **kwargs) -> Self:
        """Fit the model. Subclasses implement model-specific optimization."""

    @abstractmethod
    def _compute_result_params(self, conf_level: float = 0.95) -> pl.DataFrame:
        """Build coefficient table. Schema varies by model type."""

    @abstractmethod
    def _compute_result_model(self) -> pl.DataFrame:
        """Build fit statistics table. Schema varies by model type."""

    def _get_theta_lower_bounds(self, n_theta: int) -> list[float]:
        """Get lower bounds for theta parameters.

        Diagonal elements of Cholesky factor must be non-negative.
        Off-diagonal elements are unbounded.

        Args:
            n_theta: Number of theta parameters.

        Returns:
            List of lower bounds for each theta parameter.
        """
        # For simple structures, determine bounds based on structure
        if self._re_structure == "intercept":
            # All theta are diagonal (variance parameters)
            return [0.0] * n_theta

        elif self._re_structure == "diagonal":
            # All theta are diagonal
            return [0.0] * n_theta

        elif self._re_structure == "slope":
            # Cholesky factor: diagonal elements >= 0, off-diagonal unbounded
            # For 2x2 Cholesky: theta = [L00, L10, L11]
            # L00 and L11 are diagonal (>= 0), L10 is off-diagonal (unbounded)
            dim = int((-1 + np.sqrt(1 + 8 * n_theta)) / 2)
            bounds = []
            idx = 0
            for col in range(dim):
                for row in range(col, dim):
                    if row == col:
                        # Diagonal element
                        bounds.append(0.0)
                    else:
                        # Off-diagonal element
                        bounds.append(-np.inf)
                    idx += 1
            return bounds

        else:
            # For nested/crossed/mixed, compute bounds based on per-factor structure
            re_structures_list = self._metadata.get("re_structures_list", None)

            if re_structures_list is None:
                # Fallback: assume all intercepts (all bounds = 0)
                return [0.0] * n_theta

            bounds = []
            for factor_structure in re_structures_list:
                if factor_structure == "intercept":
                    # Single variance parameter: bound = 0
                    bounds.append(0.0)
                elif factor_structure == "slope":
                    # 2x2 Cholesky: [L00, L10, L11]
                    # L00, L11 diagonal (>= 0), L10 off-diagonal (unbounded)
                    bounds.extend([0.0, -np.inf, 0.0])
                elif factor_structure == "diagonal":
                    # All diagonal elements: bound = 0
                    # Default to 2 terms (matching initialization)
                    bounds.extend([0.0, 0.0])
                else:
                    # Unknown structure, use conservative bound
                    bounds.append(0.0)

            return bounds

    @abstractmethod
    def _compute_inference(self, conf_level: float) -> None:
        """Compute statistical inference (p-values, confidence intervals).

        Args:
            conf_level: Confidence level for intervals.
        """

    @abstractmethod
    def _simulate_response(self, mu: np.ndarray) -> np.ndarray:
        """Simulate response given expected values.

        Args:
            mu: Expected values (fitted values or predictions).

        Returns:
            Simulated response values.
        """

    def _get_re_structure(self) -> str | list[str]:
        """Get random effects structure for variance component calculations.

        For crossed/nested models, returns the per-factor structure list.
        Otherwise returns the overall structure string.
        """
        if self._re_structure in ("crossed", "nested"):
            return self._metadata.get("re_structures_list", self._re_structure)
        return self._re_structure

    @property
    def varying_var(self) -> pl.DataFrame:
        """Variance components by grouping factor (in formula order).

        Returns:
            DataFrame with columns [group, effect, variance, sd].
            For lmer, includes a Residual row. For glmer, no Residual row
            (dispersion fixed at 1 for most families).

        Examples:
            For lmer with (Days|Subject):
            ```
            shape: (3, 4)
            ┌──────────┬───────────┬──────────┬───────────┐
            │ group    ┆ effect    ┆ variance ┆ sd        │
            ├──────────┼───────────┼──────────┼───────────┤
            │ Subject  ┆ Intercept ┆ 612.10   ┆ 24.74     │
            │ Subject  ┆ Days      ┆ 35.07    ┆ 5.92      │
            │ Residual ┆ Residual  ┆ 654.94   ┆ 25.59     │
            └──────────┴───────────┴──────────┴───────────┘
            ```
        """
        self._check_fitted()
        re_struct = self._get_re_structure()

        # lmer has _sigma (residual SD), glmer does not
        sigma = getattr(self, "_sigma", None)

        df = build_varying_var_df(
            theta=self._theta,  # type: ignore[arg-type]
            group_names=self._group_names,
            random_names=self._random_names,
            re_structure=re_struct,
            sigma=sigma,
        )

        # Reorder to formula order for user-facing output
        if self._term_inverse_permutation is not None:
            inv = self._term_inverse_permutation
            formula_names = [self._group_names[inv[i]] for i in range(len(inv))]
            # Include Residual in sort order if present (lmer only)
            order = formula_names + ["Residual"] if sigma is not None else formula_names
            df = (
                df.with_columns(pl.col("group").cast(pl.Enum(order)).alias("_sort"))
                .sort("_sort")
                .drop("_sort")
            )

        return df

    @property
    def varying_corr(self) -> pl.DataFrame:
        """Varying effect correlations by grouping factor (in formula order).

        Returns:
            DataFrame with columns [group, effect1, effect2, corr].
            Empty DataFrame if no correlations (intercept-only models).

        Examples:
            For (Days|Subject):
            ```
            shape: (1, 4)
            ┌─────────┬───────────┬─────────┬───────┐
            │ group   ┆ effect1   ┆ effect2 ┆ corr  │
            ├─────────┼───────────┼─────────┼───────┤
            │ Subject ┆ Intercept ┆ Days    ┆ 0.066 │
            └─────────┴───────────┴─────────┴───────┘
            ```
        """
        self._check_fitted()
        re_struct = self._get_re_structure()

        # lmer has _sigma, glmer does not
        sigma = getattr(self, "_sigma", None)

        df = build_varying_corr_df(
            theta=self._theta,  # type: ignore[arg-type]
            group_names=self._group_names,
            random_names=self._random_names,
            re_structure=re_struct,
            sigma=sigma,
        )

        # Reorder to formula order for user-facing output
        if self._term_inverse_permutation is not None and len(df) > 0:
            inv = self._term_inverse_permutation
            formula_names = [self._group_names[inv[i]] for i in range(len(inv))]
            df = (
                df.with_columns(
                    pl.col("group").cast(pl.Enum(formula_names)).alias("_sort")
                )
                .sort("_sort")
                .drop("_sort")
            )

        return df

    # =========================================================================
    # Shared properties
    # =========================================================================

    @property
    def coef_(self) -> np.ndarray:
        """Fixed effect coefficient estimates as numpy array (sklearn-compatible).

        Returns:
            1D array of shape (p,) containing fixed effect coefficient estimates,
            where p is the number of fixed effect terms (including intercept if present).
            Order matches `params["term"]`. For varying effects, use `varying`.
        """
        self._check_fitted()
        return self._coef  # type: ignore[return-value]

    @property
    def params(self) -> pl.DataFrame:
        """Population-level coefficients as DataFrame.

        Returns:
            DataFrame with columns ["term", "estimate"] containing coefficient
            names and their estimated values.
        """
        self._check_fitted()
        return pl.DataFrame(
            {"term": self._X_names, "estimate": self._get_coef().tolist()}
        )  # type: ignore[union-attr]

    @property
    def varying(self) -> pl.DataFrame:
        """Varying effects (group deviations) by group.

        These are the group-level deviations from the population-level parameters.
        To get the effective coefficients per group, use `params_group`.

        Returns:
            DataFrame with columns [group, level, ...effect names...].

        Examples:
            For (Days|Subject):
            ```
            shape: (18, 4)
            ┌─────────┬───────┬────────────┬──────────┐
            │ group   │ level │ Intercept  │ Days     │
            ├─────────┼───────┼────────────┼──────────┤
            │ Subject │ 308   │ 2.258      │ 9.199    │
            │ Subject │ 309   │ -40.398    │ -8.621   │
            └─────────┴───────┴────────────┴──────────┘
            ```
        """
        self._check_fitted()
        return self._ranef_df  # type: ignore[return-value]

    @property
    def params_group(self) -> pl.DataFrame:
        """Group-specific coefficients (population params + varying effects).

        Computes population-level parameters combined with varying effects for
        each group level, giving the effective coefficients for each group.

        Returns:
            DataFrame with columns [group, level, ...effect names...] where
            each effect column contains params + varying for that group.

        Examples:
            For model with Intercept and Days slope, varying by Subject:
            ```
            shape: (18, 4)
            ┌─────────┬───────┬────────────┬──────────┐
            │ group   │ level │ Intercept  │ Days     │
            ├─────────┼───────┼────────────┼──────────┤
            │ Subject │ 308   │ 253.663    │ 19.666   │
            │ Subject │ 309   │ 211.007    │ 1.847    │
            └─────────┴───────┴────────────┴──────────┘
            ```
        """
        self._check_fitted()
        # Get population-level params as dict for lookup
        params_dict = dict(zip(self._X_names, self._get_coef().tolist()))  # type: ignore[union-attr]
        # Clone varying effects DataFrame
        result = self._ranef_df.clone()  # type: ignore[union-attr]
        # Effect columns are all except group and level
        effect_cols = [c for c in result.columns if c not in ("group", "level")]
        # Add population params to each effect column
        for col in effect_cols:
            if col in params_dict:
                result = result.with_columns(
                    (pl.col(col) + params_dict[col]).alias(col)
                )
        return result

    @property
    def theta_(self) -> np.ndarray:
        """Optimized theta parameters (relative scale).

        Returns:
            Cholesky factor elements on relative scale (theta = tau/sigma).
        """
        self._check_fitted()
        return self._theta  # type: ignore[return-value]

    @property
    def ngroups(self) -> dict[str, int]:
        """Number of groups per grouping factor (in formula order).

        Returns:
            Dictionary mapping grouping factor names to group counts.

        Examples:
            ```python
            {'Subject': 18}
            ```
        """
        self._check_fitted()

        # Apply inverse permutation for formula-order presentation
        if self._term_inverse_permutation is not None:
            inv = self._term_inverse_permutation
            names = [self._group_names[inv[i]] for i in range(len(inv))]
            counts = [self._n_groups_list[inv[i]] for i in range(len(inv))]
        else:
            names = self._group_names
            counts = self._n_groups_list

        return dict(zip(names, counts))

    @property
    def optimizer_diagnostics(self) -> "pl.DataFrame":
        """Optimizer convergence diagnostics (wide format DataFrame).

        Returns:
            DataFrame with one row per theta parameter containing:
            - optimizer: Optimization algorithm name
            - converged: Whether optimization converged
            - n_iter: Number of iterations
            - final_objective: Final deviance/objective value
            - theta_index: Index of this theta parameter
            - theta_final: Final theta value
            - boundary_adjusted: Whether adjusted to bounds
            - restarted: Whether optimization was restarted
            - singular: Whether fit is singular
        """
        self._check_fitted()
        return self._optimizer_diagnostics  # type: ignore[return-value]

    @property
    def loglik(self) -> float:
        """Log-likelihood (REML or ML depending on method)."""
        self._check_fitted()
        return float(self._loglik)  # type: ignore[arg-type]

    @property
    def deviance(self) -> float:
        """Deviance (-2 * log-likelihood)."""
        self._check_fitted()
        return float(self._deviance)  # type: ignore[arg-type]

    @property
    def aic(self) -> float:
        """Akaike Information Criterion."""
        self._check_fitted()
        return float(self._aic)  # type: ignore[arg-type]

    @property
    def bic(self) -> float:
        """Bayesian Information Criterion."""
        self._check_fitted()
        return float(self._bic)  # type: ignore[arg-type]

    @property
    def result_params(self) -> "ResultFit":
        """Coefficient table with estimates, standard errors, and p-values.

        Returns a :class:`~bossanova.results.ResultFit` wrapper with methods:

        - :meth:`~bossanova.results.ResultFit.to_effect_size`: Standardized effect sizes (lmer)
        - :meth:`~bossanova.results.ResultFit.to_odds_ratio`: Odds ratio scale (glmer binomial)
        - :meth:`~bossanova.results.ResultFit.recompute_ci`: CIs at different level
        - :meth:`~bossanova.results.ResultFit.filter_params`: Filter to specific terms
        - :meth:`~bossanova.results.ResultFit.filter_significant`: Filter by p-value
        - :meth:`~bossanova.results.ResultFit.exclude_intercept`: Remove intercept row

        All standard polars DataFrame operations (filter, select, etc.) also work.

        See Also:
            :class:`~bossanova.results.ResultFit`: Full API documentation.
        """
        from bossanova.results.wrappers import ResultFit

        self._check_fitted()
        return ResultFit(self._result_params, self)  # type: ignore[arg-type]

    @property
    def result_model(self) -> pl.DataFrame:
        """Fit statistics table (deviance, AIC, BIC, etc.)."""
        self._check_fitted()
        return self._result_model  # type: ignore[return-value]

    @property
    def fitted(self) -> np.ndarray:
        """Fitted values (y_hat) as numpy array.

        For mixed models, these are conditional fitted values including
        varying effects (equivalent to predict(varying="include")).
        """
        self._check_fitted()
        return self._fitted_values  # type: ignore[return-value]

    @property
    def residuals(self) -> np.ndarray:
        """Response residuals (y - y_hat) as numpy array."""
        self._check_fitted()
        return self._residuals  # type: ignore[return-value]

    @property
    def vcov(self) -> np.ndarray:
        """Variance-covariance matrix of fixed effect estimates.

        Returns:
            2D array of shape (p, p) where p is the number of fixed effects.
            Diagonal elements are variances; off-diagonal are covariances.
            Use `np.sqrt(np.diag(model.vcov))` to get standard errors.
            For random effect variances, use `varying_var`.
        """
        self._check_fitted()
        return self._vcov  # type: ignore[return-value]

    # =========================================================================
    # Shared methods
    # =========================================================================

    def is_singular(self, tol: float | None = None) -> bool:
        """Test if fit is singular (variance component at or near zero).

        Matches lme4's isSingular() (utilities.R:924-928).

        A mixed model fit is singular when one or more variance components
        are estimated at or very close to zero. This often indicates:
        - Insufficient data to estimate random effects
        - Random effects structure is too complex for the data
        - Near-zero between-group variance

        Args:
            tol: Tolerance for singularity detection. Values of theta
                (for variance components with lower bound 0) below this
                threshold are considered singular. If None, uses the
                global tolerance from get_singular_tolerance() (default 1e-4).

        Returns:
            True if any variance component theta with lower_bound=0 is below tol.

        Examples:
            ```python
            model = lmer("y ~ x + (1|group)", data=df)
            model.fit()

            if model.is_singular():
                print("Warning: singular fit detected")

            # Use stricter tolerance
            if model.is_singular(tol=1e-6):
                print("Variance component very close to zero")
            ```

        References:
            - lme4/R/utilities.R lines 924-928
            - Bates et al. (2015) on singular fits in mixed models
        """
        self._check_fitted()

        # Get tolerance from config if not specified
        if tol is None:
            from bossanova._config import get_singular_tolerance

            tol = get_singular_tolerance()

        # Get lower bounds for theta
        n_theta = len(self._theta)  # type: ignore[arg-type]
        lower_bounds = self._get_theta_lower_bounds(n_theta)

        # Check if any theta with lower_bound==0 is below tolerance
        for theta_val, lb in zip(self._theta, lower_bounds):  # type: ignore[arg-type]
            if lb == 0 and theta_val < tol:
                return True

        return False

    @property
    def convergence_messages(self) -> list:
        """Access convergence diagnostic messages from model fitting.

        Returns a list of ConvergenceMessage objects describing any convergence
        issues detected during fitting. Each message contains:
        - category: Type of issue ("singular", "correlation", "boundary", "convergence")
        - technical: lme4-style technical message
        - explanation: User-friendly explanation
        - tip: Actionable suggestion (optional)

        Returns:
            List of ConvergenceMessage objects. Empty list if no issues detected.

        Examples:
            ```python
            model = lmer("y ~ x + (1|group)", data=df)
            model.fit()

            for msg in model.convergence_messages:
                print(f"{msg.category}: {msg.explanation}")
                if msg.tip:
                    print(f"  Tip: {msg.tip}")
            ```
        """
        self._check_fitted()
        return getattr(self, "_convergence_messages", [])

    def simulate(
        self,
        nsim: int = 1,
        seed: int | None = None,
        varying: Literal["fitted", "sample"] = "fitted",
    ) -> np.ndarray:
        """Simulate responses from fitted model.

        Args:
            nsim: Number of simulations.
            seed: Random seed for reproducibility.
            varying: How to handle varying effects:
                - "fitted": Use estimated varying effects (BLUPs).
                - "sample": Draw new varying effects from estimated distribution.

        Returns:
            Array of shape (n, nsim) with simulated responses.

        Examples:
            ```python
            # Parametric bootstrap (sample new varying effects)
            sims = model.simulate(nsim=1000, varying="sample", seed=42)
            ```
        """
        self._check_fitted()

        if seed is not None:
            np.random.seed(seed)

        Lambda = build_lambda_sparse(
            self._theta,
            self._n_groups_list,
            self._re_structure,
            self._metadata,  # type: ignore[arg-type]
        )

        sims = np.zeros((self._n, nsim))

        for i in range(nsim):
            if varying == "fitted":
                # Use fitted varying effects
                mu = self._fitted_values
            elif varying == "sample":
                # Draw new varying effects from estimated distribution
                u_new = np.random.randn(Lambda.shape[0])
                b_new = Lambda @ u_new
                mu = self._X @ self._coef + self._Z.toarray() @ b_new  # type: ignore[operator]
            else:
                raise ValueError(f"Unknown varying: {varying}")

            # Add noise via subclass-specific method
            sims[:, i] = self._simulate_response(mu)  # type: ignore[arg-type]

        return sims

    def _deriv12(
        self,
        fun: Callable[[jnp.ndarray], float],
        x: jnp.ndarray,
        delta: float = 1e-4,
        fx: float | None = None,
    ) -> dict[str, jnp.ndarray]:
        """Compute gradient and Hessian via central finite differences.

        Matches lme4/R/deriv.R exactly for statistical parity.

        Implementation follows lme4's deriv12() algorithm:
        - Gradient uses central differences: g[j] = (f(x+h) - f(x-h)) / (2h)
        - Diagonal Hessian: H[j,j] = (f(x+h) - 2f(x) + f(x-h)) / h²
        - Off-diagonal Hessian uses 4-point symmetric formula:
          H[i,j] = (f(x+h_i+h_j) - f(x+h_i-h_j) - f(x-h_i+h_j) + f(x-h_i-h_j)) / (4h²)

        Args:
            fun: Scalar function f: array -> float
            x: Point at which to evaluate derivatives
            delta: Step size (lme4 default: 1e-4)
            fx: f(x) if already computed (avoids redundant evaluation)

        Returns:
            dict with keys:
            - 'gradient': shape (n,)
            - 'Hessian': shape (n, n), symmetric

        Examples:
            ```python
            # Compute Hessian of deviance for glmer
            def dev_fun(params):
                return self._compute_deviance(params)

            derivs = self._deriv12(dev_fun, x=combined_params)
            hessian = derivs['Hessian']
            ```
        """
        x = jnp.asarray(x)
        nx = len(x)

        # Evaluate function at base point if not provided
        if fx is None:
            fx = float(fun(x))

        # Initialize output arrays
        H: jnp.ndarray = jnp.zeros((nx, nx))
        g: jnp.ndarray = jnp.zeros(nx)

        # Compute perturbation points
        xadd = x + delta  # x + h
        xsub = x - delta  # x - h

        # Helper to substitute values at positions
        def spos(base, mod, pos):
            """Substitute mod value at position pos in base array."""
            return base.at[pos].set(mod[pos])

        # Diagonal elements and gradient
        for j in range(nx):
            # Perturbed points: x with j-th element ±delta
            x_j_add = spos(x, xadd, j)
            x_j_sub = spos(x, xsub, j)

            fadd = float(fun(x_j_add))
            fsub = float(fun(x_j_sub))

            # Diagonal Hessian: second derivative
            H = H.at[j, j].set((fadd - 2 * fx + fsub) / (delta**2))  # type: ignore[union-attr]

            # Gradient: central difference
            g = g.at[j].set((fadd - fsub) / (2 * delta))  # type: ignore[union-attr]

        # Off-diagonal elements (upper triangle, then mirror)
        for j in range(nx):
            for i in range(j):  # i < j
                # 4-point symmetric formula
                # Need: f(x + h_i + h_j), f(x + h_i - h_j), f(x - h_i + h_j), f(x - h_i - h_j)
                x_aa = spos(spos(x, xadd, i), xadd, j)  # x + h_i + h_j
                x_as = spos(spos(x, xadd, i), xsub, j)  # x + h_i - h_j
                x_sa = spos(spos(x, xsub, i), xadd, j)  # x - h_i + h_j
                x_ss = spos(spos(x, xsub, i), xsub, j)  # x - h_i - h_j

                f_aa = float(fun(x_aa))
                f_as = float(fun(x_as))
                f_sa = float(fun(x_sa))
                f_ss = float(fun(x_ss))

                # Mixed partial: ∂²f/∂x_i∂x_j
                hij = (f_aa - f_as - f_sa + f_ss) / (4 * delta**2)

                # Set both upper and lower triangle (symmetric)
                H = H.at[i, j].set(hij)  # type: ignore[union-attr]
                H = H.at[j, i].set(hij)  # type: ignore[union-attr]

        return {"gradient": g, "Hessian": H}

    def _compute_vcov_from_hessian(
        self,
        hess: jnp.ndarray,
        n_theta: int,
    ) -> jnp.ndarray:
        """Extract fixed-effects vcov from full Hessian.

        Matches lme4's calc.vcov.hess() in lmer.R.

        The full Hessian from finite differences of the deviance includes
        both variance parameters (theta) and fixed effects (beta). This
        extracts the fixed-effects block and inverts it to get vcov.

        Args:
            hess: Full Hessian matrix (n_theta + n_beta) × (n_theta + n_beta)
            n_theta: Number of variance component parameters

        Returns:
            vcov: Variance-covariance matrix for fixed effects (n_beta × n_beta)

        Raises:
            ValueError: If Hessian submatrix is singular

        Examples:
            ```python
            # After computing Hessian of deviance
            vcov = self._compute_vcov_from_hessian(hess, n_theta=len(theta))
            ```
        """
        # Extract fixed-effects block (drop first n_theta rows/cols)
        hess_beta = hess[n_theta:, n_theta:]

        # Force symmetry (numerical precision)
        hess_beta = (hess_beta + hess_beta.T) / 2

        # Invert to get vcov
        # For deviance Hessian h: vcov = 2 * inv(h) = solve(h/2)
        # This matches lme4's calc.vcov.hess() formula
        try:
            vcov = 2 * jnp.linalg.inv(hess_beta)
        except np.linalg.LinAlgError as e:
            raise ValueError(
                "Hessian submatrix for fixed effects is singular. "
                "Model may be overparameterized or data may be degenerate."
            ) from e

        # Ensure positive definite (force symmetry again after inversion)
        vcov = (vcov + vcov.T) / 2

        return vcov

    def _predict_newdata(
        self,
        newdata: pl.DataFrame,
        varying: Literal["include", "exclude"],
        allow_new_levels: bool,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute predictions on new data (shared by lmer/glmer).

        This is the core prediction logic for mixed models with new data.
        It handles:
        - Fixed effects: X_new @ coef
        - Varying effects: Z_new @ b (if varying="include")
        - New grouping levels (zero-fill if allowed, error otherwise)

        Args:
            newdata: New data as Polars DataFrame.
            varying: How to handle varying effects:
                - "include": Use estimated BLUPs for known levels, 0 for new levels
                - "exclude": Population-level predictions (fixed effects only)
            allow_new_levels: If True, new grouping levels get varying effect=0.
                If False, raises ValueError on new levels.

        Returns:
            Tuple of (X_new, linear_predictor):
                - X_new: Fixed effects design matrix for new data
                - linear_predictor: X_new @ coef + Z_new @ b (or just X_new @ coef)

        Raises:
            ValueError: If new grouping levels found and allow_new_levels=False.

        Examples:
            ```python
            # In lmer.predict():
            X_new, eta = self._predict_newdata(newdata, varying, allow_new_levels)
            return pl.DataFrame({".fitted": eta})

            # In glmer.predict():
            X_new, eta = self._predict_newdata(newdata, varying, allow_new_levels)
            if type == "response":
                fitted = self._family.link_inverse(eta)
            ```
        """
        # Get fixed effects design matrix using builder's evaluate_new_data
        # This preserves transformations (center, scale, etc.) from training
        X_new = self._builder.evaluate_new_data(newdata)

        # Fixed effects prediction
        eta = X_new @ self._coef

        # If excluding varying effects, we're done
        if varying == "exclude":
            return X_new, eta

        # Include random effects - need to build Z_new and extract b values
        # First, compute BLUPs from fitted model
        Lambda = build_lambda_sparse(
            self._theta, self._n_groups_list, self._re_structure, self._metadata
        )
        b = Lambda @ self._u  # Full b vector from training

        # Build mapping from group levels to b indices
        # and construct Z_new matrix
        n_new = len(newdata)

        # Track b values to use for each new observation
        # We'll build Z_new directly with the appropriate structure
        Z_new_contribution = np.zeros(n_new)

        # Determine number of RE per group based on structure
        if self._re_structure == "intercept":
            n_re_per_group = 1
        elif self._re_structure in ("diagonal", "slope"):
            n_re_per_group = len(self._random_names)
        else:
            n_re_per_group = (
                len(self._random_names) if isinstance(self._random_names, list) else 1
            )

        b_offset = 0
        for i, group_name in enumerate(self._group_names):
            n_groups = self._n_groups_list[i]

            # Get original levels (sorted, matching training order) - use Polars directly
            if group_name in self._data.columns:
                original_levels = sorted(self._data[group_name].unique().to_list())
            else:
                original_levels = list(range(n_groups))

            # Create level-to-index mapping
            level_to_idx = {level: idx for idx, level in enumerate(original_levels)}

            # Get new data's group values
            if group_name not in newdata.columns:
                raise ValueError(
                    f"Grouping factor '{group_name}' not found in newdata. "
                    f"Required columns: {self._group_names}"
                )

            new_group_values = newdata[group_name].to_numpy()

            # Check for new levels
            new_levels = set(new_group_values) - set(original_levels)
            if new_levels and not allow_new_levels:
                # Format level list, truncating if too many
                sorted_levels = sorted(new_levels, key=str)
                if len(sorted_levels) <= 5:
                    levels_str = ", ".join(str(lv) for lv in sorted_levels)
                else:
                    levels_str = ", ".join(str(lv) for lv in sorted_levels[:5])
                    levels_str += f" ... and {len(sorted_levels) - 5} more"
                raise ValueError(
                    f'New group levels found in "{group_name}".\n\n'
                    f"Unknown levels: {levels_str}\n"
                    "These levels were not present in the training data.\n\n"
                    "Options:\n"
                    "  - Use allow_new_levels=True to predict at population level\n"
                    "    (random effects assumed to be zero for new groups)\n"
                    "  - Use varying='exclude' for fixed-effects-only predictions\n"
                    "  - Filter your prediction data to known groups only"
                )

            # Extract b values for this grouping factor
            group_b = b[b_offset : b_offset + n_groups * n_re_per_group]
            group_b_matrix = group_b.reshape(n_groups, n_re_per_group)

            # Get random effects covariates for new data
            if self._re_structure == "intercept":
                # Simple intercept: X_re is just 1s
                X_re_new = np.ones((n_new, 1))
            elif self._re_structure == "slope":
                # Correlated slopes: need to evaluate RE covariates on new data
                # X_re contains [1, covariate1, covariate2, ...]
                X_re_new = self._get_re_covariates_for_newdata(newdata)
            elif self._re_structure == "diagonal":
                # Uncorrelated slopes: similar to slope but blocked
                X_re_new = self._get_re_covariates_for_newdata(newdata)
            else:
                X_re_new = np.ones((n_new, n_re_per_group))

            # Compute RE contribution for each new observation
            for obs_idx in range(n_new):
                group_val = new_group_values[obs_idx]

                if group_val in level_to_idx:
                    # Known level - use fitted BLUPs
                    group_idx = level_to_idx[group_val]
                    b_for_obs = group_b_matrix[group_idx, :]  # (n_re_per_group,)
                    x_re_for_obs = X_re_new[obs_idx, :]  # (n_re_per_group,)
                    Z_new_contribution[obs_idx] += np.dot(x_re_for_obs, b_for_obs)
                # else: new level with allow_new_levels=True -> contributes 0

            b_offset += n_groups * n_re_per_group

        # Add RE contribution to linear predictor
        eta = eta + Z_new_contribution

        return X_new, eta

    def _get_re_covariates_for_newdata(self, newdata: pl.DataFrame) -> np.ndarray:
        """Extract random effects covariates for new data.

        For models with random slopes, extracts the covariate values
        that correspond to the random effects terms.

        Args:
            newdata: New data as Polars DataFrame.

        Returns:
            Array of shape (n_new, n_re_per_group) with covariate values.
            First column is 1s (intercept), remaining columns are covariates.
        """
        n_new = len(newdata)
        n_re = len(self._random_names)

        X_re_new = np.zeros((n_new, n_re))

        for r, re_name in enumerate(self._random_names):
            if re_name in ("Intercept", "(Intercept)", "1"):
                # Intercept term
                X_re_new[:, r] = 1.0
            elif re_name in newdata.columns:
                # Covariate term - get directly from data
                X_re_new[:, r] = newdata[re_name].to_numpy()
            else:
                # Try to find in fixed effects design matrix columns
                # This handles cases like poly(x, 2) or I(x^2)
                try:
                    # Get column index in X (if it exists)
                    if re_name in self._X_names:
                        col_idx = self._X_names.index(re_name)
                        # Evaluate new data with builder
                        X_new = self._builder.evaluate_new_data(newdata)
                        X_re_new[:, r] = X_new[:, col_idx]
                    else:
                        # Last resort: assume intercept
                        X_re_new[:, r] = 1.0
                except Exception:
                    X_re_new[:, r] = 1.0

        return X_re_new

    def _check_boundary(
        self,
        theta: np.ndarray,
        lower_bounds: list[float],
        devfun: Callable[[np.ndarray], float],
        boundary_tol: float = 1e-5,
    ) -> tuple[np.ndarray, bool]:
        """Snap near-boundary parameters to exact boundary if it improves fit.

        Matches lme4's check.boundary() logic in modular.R (lines 856-874).

        This is statistically principled, not just numerical convenience:
        - A parameter AT the boundary (θ=0) has clear meaning: variance is zero
        - A parameter NEAR the boundary (θ≈0) is ambiguous for inference
        - The 50:50 mixture distribution for LRT only applies at exact boundary
        - Setting θ=0 when appropriate ensures correct interpretation

        For each θ parameter within boundary_tol of its lower bound:
        1. Test if setting it exactly to the boundary improves deviance
        2. If yes, use the boundary value (this is the true MLE)
        3. If no, keep the optimizer's value

        Args:
            theta: Optimized theta parameters from optimizer.
            lower_bounds: Lower bounds for each theta (0 for diagonals, -inf for off-diag).
            devfun: Deviance function that takes theta and returns deviance.
            boundary_tol: Distance from boundary within which to test.
                Default 1e-5 matches lme4.

        Returns:
            Tuple of (adjusted_theta, any_adjusted):
                - adjusted_theta: Theta with near-boundary values snapped to boundary
                - any_adjusted: True if any values were changed

        Examples:
            ```python
            # After optimization
            theta_opt, adjusted = self._check_boundary(
                theta=theta_opt,
                lower_bounds=lower_bounds,
                devfun=deviance_fn,
            )
            if adjusted:
                # Recompute results at new theta
                ...
            ```

        References:
            - lme4/R/modular.R check.boundary() (lines 856-874)
            - Self & Liang (1987) on boundary inference
            - Stram & Lee (1994) on variance component testing
        """
        theta = np.array(theta, dtype=float)
        current_dev = devfun(theta)
        any_adjusted = False

        for i, (t, lb) in enumerate(zip(theta, lower_bounds)):
            # Only check finite lower bounds (skip -inf for off-diagonal elements)
            if not np.isfinite(lb):
                continue

            # Check if parameter is close to but not at boundary
            bdiff = t - lb
            if 0 < bdiff < boundary_tol:
                # Test if exact boundary improves deviance
                theta_test = theta.copy()
                theta_test[i] = lb
                test_dev = devfun(theta_test)

                if test_dev < current_dev:
                    # Boundary value is better - accept it
                    theta[i] = lb
                    current_dev = test_dev
                    any_adjusted = True

        return theta, any_adjusted

    def _restart_edge(
        self,
        theta: np.ndarray,
        lower_bounds: list[float],
        devfun: Callable[[np.ndarray], float],
        optimizer_fn: Callable,
        optimizer_kwargs: dict,
        boundary_tol: float = 1e-5,
        verbose: bool = False,
    ) -> tuple[np.ndarray, float, bool]:
        """Restart optimization if gradient at boundary suggests improvement.

        Matches lme4's restart_edge logic (modular.R:610-644).

        When theta parameters land exactly on their lower bounds (typically 0
        for variance components), this checks whether the deviance gradient
        is negative. A negative gradient means the optimizer got stuck at the
        boundary when it should have continued - restarting often finds a
        better solution.

        Args:
            theta: Optimized theta parameters from initial optimization.
            lower_bounds: Lower bounds for each theta parameter.
            devfun: Deviance function that takes theta and returns deviance.
            optimizer_fn: Optimizer function to use for restart.
            optimizer_kwargs: Keyword arguments for the optimizer.
            boundary_tol: Step size for one-sided gradient computation.
                Default 1e-5 matches lme4's btol.
            verbose: If True, print message when restarting.

        Returns:
            Tuple of (theta, deviance, restarted):
                - theta: Final theta parameters (possibly from restart)
                - deviance: Final deviance value
                - restarted: True if optimization was restarted

        Examples:
            ```python
            theta_opt, dev, restarted = self._restart_edge(
                theta=theta_opt,
                lower_bounds=lower_bounds,
                devfun=deviance_fn,
                optimizer_fn=minimize,
                optimizer_kwargs={"method": "L-BFGS-B", ...},
            )
            if restarted and verbose:
                print("Restarted optimization from boundary")
            ```

        References:
            - lme4/R/modular.R lines 610-644
        """
        theta = np.array(theta, dtype=float)

        # Find parameters exactly at boundary
        boundary_indices = []
        for i, (t, lb) in enumerate(zip(theta, lower_bounds)):
            if np.isfinite(lb) and t == lb:
                boundary_indices.append(i)

        # No parameters at boundary - nothing to do
        if not boundary_indices:
            return theta, float(devfun(theta)), False

        # Compute base deviance
        d0 = float(devfun(theta))

        # Compute one-sided gradient for each boundary parameter
        gradients = []
        for i in boundary_indices:
            theta_test = theta.copy()
            theta_test[i] = lower_bounds[i] + boundary_tol
            d_test = float(devfun(theta_test))
            grad = (d_test - d0) / boundary_tol
            gradients.append(grad)

        # Reset deviance state by re-evaluating at original theta
        devfun(theta)

        # Check for NA gradients (would indicate numerical issues)
        if any(np.isnan(g) for g in gradients):
            import warnings

            warnings.warn(
                "Some gradient components are NA near boundaries, "
                "skipping boundary restart check",
                stacklevel=2,
            )
            return theta, d0, False

        # If any gradient is negative, restart optimization
        if any(g < 0 for g in gradients):
            if verbose:
                print("Some theta parameters on the boundary, restarting")

            # Restart optimization from current theta
            # optimizer_fn is optimize_theta(objective, theta0, lower, upper, **kwargs)
            # Extract positional args from kwargs, pass rest as keyword args
            kwargs = optimizer_kwargs.copy()
            lower = kwargs.pop("lower", lower_bounds)
            upper = kwargs.pop("upper", [np.inf] * len(lower_bounds))

            result = optimizer_fn(devfun, theta, lower, upper, **kwargs)

            return np.array(result["theta"]), float(result["fun"]), True

        # No restart needed
        return theta, d0, False

    def _compute_vcov_schur(
        self,
        X: jnp.ndarray,
        Z: sp.csc_matrix,
        Lambda: sp.csc_matrix,
        W: jnp.ndarray | None = None,
        sigma2: float = 1.0,
    ) -> jnp.ndarray:
        """Compute vcov via Schur complement of augmented system.

        This is the standard approach for linear mixed models (lmer).
        For GLMMs, observation weights W are the final IRLS weights.

        The augmented system is:
            [X'WX        X'WZΛ      ] [β]   [X'Wy]
            [Λ'Z'WX   Λ'Z'WZΛ + I   ] [u] = [Λ'Z'Wy]

        The Schur complement gives:
            Vcov(β) = σ² * (X'WX - X'WZΛ(Λ'Z'WZΛ + I)⁻¹Λ'Z'WX)⁻¹

        Args:
            X: Fixed effects design matrix (n × p)
            Z: Random effects design matrix (sparse, n × q)
            Lambda: Relative covariance factor (sparse, q × q)
            W: Observation weights (n,). If None, uses identity (W=1).
            sigma2: Residual variance. For GLMMs with known dispersion, use 1.0.

        Returns:
            vcov: Variance-covariance matrix for fixed effects (p × p)

        Examples:
            ```python
            # For lmer (identity weights)
            vcov = self._compute_vcov_schur(
                X=self._X, Z=self._Z, Lambda=Lambda, W=None, sigma2=sigma2
            )

            # For glmer (IRLS weights)
            vcov = self._compute_vcov_schur(
                X=self._X, Z=self._Z, Lambda=Lambda, W=weights, sigma2=1.0
            )
            ```
        """
        from bossanova.ops.sparse_solver import sparse_cholesky

        # Compute ZΛ
        ZL = Z @ Lambda

        if W is None:
            # Identity weights: standard formulation
            # S22 = Λ'Z'ZΛ + I
            S22 = (ZL.T @ ZL).tocsc() + sp.eye(Lambda.shape[0], format="csc")
            XtX = X.T @ X
            XtZL = X.T @ ZL.toarray()
        else:
            # Weighted formulation for GLMMs
            # S22 = Λ'Z'WZΛ + I
            # Convert JAX array to numpy for scipy.sparse compatibility
            W_diag = sp.diags(np.asarray(W), format="csc")
            S22 = (ZL.T @ W_diag @ ZL).tocsc() + sp.eye(Lambda.shape[0], format="csc")
            # X'WX
            WX = W[:, None] * X  # Broadcasting: (n,) × (n,p) -> (n,p)
            XtX = X.T @ WX
            # X'WZΛ
            XtZL = X.T @ (W_diag @ ZL).toarray()

        # Sparse Cholesky factorization of S22
        factor_S22 = sparse_cholesky(S22)

        # Solve S22 * Y = (X'ZΛ)' to get Y = S22^{-1} * (X'ZΛ)'
        S22_inv_XtZL_T = factor_S22(XtZL.T)

        # Schur complement: X'WX - X'WZΛ * S22^{-1} * Λ'Z'WX
        schur = XtX - XtZL @ S22_inv_XtZL_T

        # Vcov = σ² * Schur^{-1}
        vcov = sigma2 * jnp.linalg.inv(schur)

        return vcov
