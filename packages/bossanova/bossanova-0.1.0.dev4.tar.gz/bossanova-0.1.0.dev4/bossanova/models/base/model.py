"""Base model class for all bossanova models."""

from __future__ import annotations

__all__ = ["BaseModel"]

import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import polars as pl

from bossanova._utils import remove_predictor_from_formula
from bossanova.formula.design import DesignMatrixBuilder

if TYPE_CHECKING:
    from typing_extensions import Self
    from pandas import DataFrame as PandasDataFrame
    from bossanova.resample.results import BootstrapResult, PermutationResult, CVResult
    from bossanova.results.wrappers import ResultMee
    from bossanova.models.latex import MathDisplay


class BaseModel(ABC):
    """Base class for all bossanova statistical models.

    This class provides common infrastructure shared by all model types:

    - Formula parsing and design matrix construction
    - Factor/contrast/transform management
    - Fitted state checking
    - Common method signatures (fit, predict, summary, anova, vif)

    Subclasses (lm, glm, lmer, glmer) implement model-specific fitting
    and prediction logic.

    Attributes:
        formula: Model formula (read-only).
        data: Input data, augmented after fit.
        designmat: Design matrix as DataFrame.
        is_fitted: Whether model has been fitted.
    """

    def __init__(
        self,
        formula: str,
        data: pl.DataFrame | PandasDataFrame,
        missing: Literal["drop", "fail"] = "drop",
    ):
        """Initialize base model.

        Args:
            formula: R-style model formula (e.g., "y ~ x1 + x2").
            data: Input data as pandas or polars DataFrame.
            missing: How to handle missing values in formula variables:
                - "drop" (default): Drop rows with NAs, warn user with count.
                  Output arrays (fitted, residuals) maintain original length
                  with NaN in dropped positions.
                - "fail": Raise ValueError if any NAs in formula variables.
        """
        # Validate and store missing data policy
        if missing not in ("drop", "fail"):
            raise ValueError(f"missing must be 'drop' or 'fail', got {missing!r}")
        self._missing = missing

        # Store original formula (user's input, never modified)
        self._formula = formula

        # Working formula (may be transformed by set_transforms/set_contrasts)
        self._formula_working = formula

        # Convert data to polars if needed
        if not isinstance(data, pl.DataFrame):
            # Assume pandas
            import pandas as pd

            if isinstance(data, pd.DataFrame):
                data = pl.from_pandas(data)
            else:
                raise TypeError(
                    f"Expected a DataFrame but received {type(data).__name__}.\n\n"
                    f"The 'data' argument must be a polars DataFrame.\n"
                    f"If you have a pandas DataFrame, convert it with: pl.DataFrame(pandas_df)"
                )

        self._data = data

        # Configuration state for transforms and contrasts
        self._transforms_spec: dict[str, str] | None = None
        self._contrasts_spec: dict[str, str | tuple[str, str]] | None = None

        # Custom contrast matrices (for numeric contrast specs)
        self._custom_contrasts: dict[str, np.ndarray] | None = None

        # Factor management state
        self._factors: dict[str, list[str]] | None = None
        self._original_dtypes: dict[str, pl.DataType] | None = None

        # Parse formula and extract design matrices
        self._parse_formula()

        # Initialize state flags
        self.is_fitted = False

        # Initialize result caches
        self._result_params: pl.DataFrame | None = None
        self._result_model: pl.DataFrame | None = None

        # Initialize inference type (set by fit() or infer())
        self._inference: str | None = None

        # Common fitted-state attributes (set by subclass fit() methods)
        self._coef: np.ndarray | None = None
        self._vcov: np.ndarray | None = None
        self._fitted_values: np.ndarray | None = None
        self._residuals: np.ndarray | None = None
        self._df_resid: float | None = None  # Residual degrees of freedom (lm, glm)

        # Storage for resample results (populated when save_resamples=True in infer())
        self.boot_samples_: "BootstrapResult | None" = None
        self.perm_samples_: "PermutationResult | None" = None
        self.cv_results_: "CVResult | None" = None

        # Internal flags for inference
        self._save_resamples: bool = False
        self._perm_alternative: str = "two-sided"

        # MEE state (populated by .mee())
        self._result_mee: pl.DataFrame | None = None
        self._mee_X_ref: np.ndarray | None = None  # Design matrix for bootstrap
        self._mee_contrast_matrix: np.ndarray | None = None  # For contrasts
        self._mee_specs: str | None = None  # Original specs string
        self._mee_has_contrasts: bool = (
            False  # Whether current MEE result has contrasts
        )

        # Operation tracking for .infer() dispatch
        self._last_operation: str | None = None  # "fit" or "mee"

    def _get_coef(self) -> np.ndarray:
        """Get coefficient array with type narrowing.

        This helper is used internally to access _coef in contexts where
        the model must be fitted. It asserts _coef is not None, helping
        the type checker narrow the type from `np.ndarray | None` to `np.ndarray`.

        Returns:
            Coefficient array.

        Raises:
            AssertionError: If _coef is None (model not fitted).
        """
        assert self._coef is not None, (
            "Model must be fitted before accessing coefficients"
        )
        return self._coef

    def _parse_formula(self) -> None:
        """Parse formula and extract design matrices.

        Uses the working formula (which may include transforms/contrasts
        applied via set_transforms() or set_contrasts()).
        """
        # Use custom DesignMatrixBuilder (pure Polars, no pandas/formulae)
        self._builder = DesignMatrixBuilder(
            self._formula_working,
            self._data,
            factors=self._factors,
            custom_contrasts=self._custom_contrasts,
        )
        self._dm = self._builder.build()

        # Merge contrast types from design matrix into _contrasts_spec
        # This captures factor(x, Sum) syntax from formula that wasn't set via set_contrasts()
        # Method-set contrasts (already in _contrasts_spec) take precedence
        if self._dm.contrast_types:
            for var_name, contrast_type in self._dm.contrast_types.items():
                if self._contrasts_spec is None:
                    self._contrasts_spec = {}
                # Only set if not already specified via set_contrasts()
                if var_name not in self._contrasts_spec:
                    self._contrasts_spec[var_name] = contrast_type

        # Extract response variable (y)
        if self._dm.y is not None:
            self._y = self._dm.y.astype(np.float64)
            self._y_name = self._dm.y_label
        else:
            raise ValueError(
                "No response variable found in formula.\n\n"
                f"Your formula: {self._formula}\n"
                "A valid formula has the form: response ~ predictors\n"
                "Example: 'y ~ x1 + x2' where 'y' is the response variable"
            )

        # Check for Inf/-Inf in response (must be done before missing data handling)
        n_inf = int(np.sum(np.isinf(self._y)))
        if n_inf > 0:
            raise ValueError(
                f'Response variable "{self._y_name}" contains {n_inf} infinite value(s).\n\n'
                "Infinite values (Inf, -Inf) cannot be used in model fitting.\n"
                "Common causes:\n"
                "  - Division by zero in data preprocessing\n"
                "  - Log transformation of zero or negative values\n\n"
                "Remove or replace infinite values before fitting."
            )

        # Extract design matrix (X)
        if self._dm.X is not None and self._dm.X.shape[1] > 0:
            self._X_names = self._dm.X_labels
            self._X = self._dm.X
        else:
            raise ValueError(
                "No predictor variables found in formula.\n\n"
                f"Your formula: {self._formula}\n"
                "Add at least one predictor after the '~'.\n"
                "Example: 'y ~ x1' or 'y ~ x1 + x2' or 'y ~ 1'"
            )

        # Store total observations (before dropping missing)
        self._n_total = len(self._y)
        self._p = self._X.shape[1]

        # Compute validity mask for missing data handling
        y_valid = ~np.isnan(self._y)
        X_valid = ~np.any(np.isnan(self._X), axis=1)
        self._valid_mask = y_valid & X_valid

        # Count valid and missing observations
        self._n_valid = int(np.sum(self._valid_mask))
        self._n_missing = self._n_total - self._n_valid

        # Compute per-variable missing info for diagnostics
        self._missing_info = self._compute_missing_info()

        # Handle missing data policy
        if self._n_missing > 0:
            if self._missing == "fail":
                var_details = "\n".join(
                    f"  - {var}: {len(rows)} missing"
                    for var, rows in self._missing_info.items()
                )
                raise ValueError(
                    f"Missing values found in {self._n_missing} rows.\n\n"
                    f"Affected variables:\n{var_details}\n\n"
                    "To handle this:\n"
                    "Use missing='drop' to exclude incomplete rows"
                )
            else:  # missing="drop"
                var_summary = ", ".join(
                    f"{var}: {len(rows)}" for var, rows in self._missing_info.items()
                )
                warnings.warn(
                    f"{self._n_missing} rows with missing values will be dropped "
                    f"({var_summary}). Use missing='fail' to raise an error instead.",
                    UserWarning,
                    stacklevel=4,
                )

        # For backwards compatibility, _n refers to valid observations
        self._n = self._n_valid

    def _compute_missing_info(self) -> dict[str, list[int]]:
        """Compute per-variable breakdown of rows with missing values.

        Returns:
            Dict mapping variable names to lists of row indices with NAs.
            Only includes variables that have at least one missing value.
        """
        info: dict[str, list[int]] = {}

        # Check response variable
        y_na_rows = np.where(np.isnan(self._y))[0].tolist()
        if y_na_rows:
            info[self._y_name] = y_na_rows

        # Check each predictor column
        # Track which base variables we've already processed
        processed_vars: set[str] = set()

        for i, name in enumerate(self._X_names):
            if name == "Intercept":
                continue

            # Extract base variable name (strip encoding suffix, function wrappers)
            var_name = self._extract_var_name_for_missing(name)
            if var_name is None or var_name in processed_vars:
                continue

            # Find NA rows for this column
            col_na_rows = np.where(np.isnan(self._X[:, i]))[0].tolist()
            if col_na_rows:
                if var_name in info:
                    # Merge with existing (handles multiple columns from same var)
                    info[var_name] = sorted(set(info[var_name] + col_na_rows))
                else:
                    info[var_name] = col_na_rows
                processed_vars.add(var_name)

        return info

    def _extract_var_name_for_missing(self, term_name: str) -> str | None:
        """Extract base variable name from term name for missing data reporting.

        Similar to _extract_var_name but simplified for missing data purposes.

        Args:
            term_name: Term name like "group[B]", "center(x)", "x:y".

        Returns:
            Base variable name, or None if not extractable.
        """
        if not term_name:
            return None

        # Handle interaction terms - take first component
        if ":" in term_name:
            term_name = term_name.split(":")[0]

        # Handle function-wrapped names: center(x), scale(y), factor(group)
        if "(" in term_name and ")" in term_name:
            start = term_name.rfind("(") + 1
            end = term_name.find(",") if "," in term_name else term_name.find(")")
            inner = term_name[start:end].strip()
            return self._extract_var_name_for_missing(inner)

        # Handle factor level notation: group[B], cyl[6]
        if "[" in term_name:
            return term_name.split("[")[0]

        return term_name

    @property
    def formula(self) -> str:
        """Model formula string (read-only)."""
        return self._formula

    @property
    def data(self) -> pl.DataFrame:
        """Input data, augmented with diagnostic columns after fit."""
        return self._data

    @property
    def designmat(self) -> pl.DataFrame:
        """Design matrix as polars DataFrame with named columns."""
        return pl.DataFrame(self._X, schema=self._X_names)

    @property
    def response(self) -> str:
        """Name of the response (dependent) variable."""
        return self._y_name

    @property
    def nparams(self) -> int:
        """Number of fixed effect parameters (columns in design matrix)."""
        return self._p

    @property
    def nobs(self) -> int:
        """Number of observations used in fitting (excludes rows with missing values)."""
        return self._n_valid

    @property
    def nobs_total(self) -> int:
        """Total number of rows in input data (before dropping missing)."""
        return self._n_total

    @property
    def nobs_missing(self) -> int:
        """Number of rows dropped due to missing values."""
        return self._n_missing

    @property
    def missing_info(self) -> pl.DataFrame:
        """Per-variable breakdown of rows with missing values.

        Returns:
            DataFrame with columns: variable, n_missing, row_indices.
            Empty DataFrame (0 rows) if no missing values.

        Examples:
            >>> model = lm("y ~ x1 + x2", data=df)
            >>> model.missing_info
            shape: (2, 3)
            ┌──────────┬───────────┬─────────────┐
            │ variable ┆ n_missing ┆ row_indices │
            │ ---      ┆ ---       ┆ ---         │
            │ str      ┆ i64       ┆ list[i64]   │
            ╞══════════╪═══════════╪═════════════╡
            │ y        ┆ 2         ┆ [2, 7]      │
            │ x1       ┆ 2         ┆ [4, 12]     │
            └──────────┴───────────┴─────────────┘
        """
        if not self._missing_info:
            return pl.DataFrame(
                {"variable": [], "n_missing": [], "row_indices": []},
                schema={
                    "variable": pl.String,
                    "n_missing": pl.Int64,
                    "row_indices": pl.List(pl.Int64),
                },
            )
        return pl.DataFrame(
            {
                "variable": list(self._missing_info.keys()),
                "n_missing": [len(rows) for rows in self._missing_info.values()],
                "row_indices": list(self._missing_info.values()),
            }
        )

    @property
    def valid_mask(self) -> np.ndarray:
        """Boolean mask indicating rows without missing values.

        Returns:
            1D boolean array of shape (nobs_total,). True for complete cases,
            False for rows with any missing values in formula variables.
        """
        return self._valid_mask

    def _check_fitted(self) -> None:
        """Raise error if model has not been fitted."""
        if not self.is_fitted:
            model_name = type(self).__name__
            # Build a representative formula example
            if model_name in ("lmer", "glmer"):
                formula_example = "'y ~ x + (1|group)'"
            else:
                formula_example = "'y ~ x'"
            raise RuntimeError(
                "Model has not been fitted yet.\n\n"
                "You need to call .fit() before accessing results:\n\n"
                f"    model = {model_name}({formula_example}, data=df)\n"
                f"    model.fit()          # <-- Add this\n"
                f"    model.result_params  # Now this works"
            )

    def __repr__(self) -> str:
        """Return single-line string representation."""
        parts = self._repr_parts()
        return f"{type(self).__name__}({', '.join(f'{k}={v!r}' for k, v in parts)})"

    def _repr_parts(self) -> list[tuple[str, Any]]:
        """Return (key, value) pairs for repr. Override in subclasses."""
        parts: list[tuple[str, Any]] = [
            ("formula", self.formula),
            ("data", (self._n, self._p)),
            ("fitted", self.is_fitted),
        ]
        return parts

    def _augment_data(self) -> None:
        """Augment data with fitted values, residuals, and diagnostics.

        This shared implementation handles the common case for lm/glm:
        - Computes studentized residuals and Cook's distance
        - Adds fitted, resid, std_resid, hat, cooksd columns
        - Adds _orig columns for transformed variables

        Subclasses can override _compute_augment_residuals() to customize
        residual preprocessing (e.g., GLM uses Pearson residuals).

        Ridge overrides _augment_data() entirely since it only adds
        fitted and resid (no diagnostics due to shrinkage complexity).
        """
        from bossanova.ops.diagnostics import (
            compute_cooks_distance,
            compute_studentized_residuals,
        )

        # Get residuals (may be preprocessed by subclass)
        residuals = self._compute_augment_residuals()

        # Get sigma (GLM uses 1.0, lm uses _sigma)
        sigma = self._get_augment_sigma()

        # Compute diagnostics
        std_resid = compute_studentized_residuals(residuals, self._leverage, sigma)
        cooksd = compute_cooks_distance(self._residuals, self._leverage, sigma, self._p)

        # Augment data
        self._data = self._data.with_columns(
            [
                pl.lit(self._fitted_values).alias("fitted"),
                pl.lit(self._residuals).alias("resid"),
                pl.lit(std_resid).alias("std_resid"),
                pl.lit(self._leverage).alias("hat"),
                pl.lit(cooksd).alias("cooksd"),
            ]
        )

        # Add _orig columns for transformed variables
        self._add_orig_columns()

    def _compute_augment_residuals(self) -> np.ndarray:
        """Compute residuals for augmentation diagnostics.

        Override in subclasses for preprocessing (e.g., GLM uses Pearson residuals).

        Returns:
            Residuals array for studentized residual computation.
        """
        return self._residuals

    def _get_augment_sigma(self) -> float:
        """Get sigma for augmentation diagnostics.

        Override in subclasses (e.g., GLM uses 1.0).

        Returns:
            Sigma value for standardization.
        """
        return self._sigma

    def _expand_to_full_length(self, valid_values: np.ndarray) -> np.ndarray:
        """Expand values from valid rows to full length with NaN padding.

        When the model has missing data (missing="drop"), fitted values and
        residuals are computed only on valid rows. This helper expands them
        back to full dataset length, inserting NaN for excluded rows.

        Args:
            valid_values: Array of length n_valid (number of valid rows).

        Returns:
            Array of length n_total with valid_values inserted at valid_mask
            positions and NaN elsewhere.

        Example:
            >>> # Instead of:
            >>> self._fitted_values = np.full(self._n_total, np.nan)
            >>> self._fitted_values[self._valid_mask] = result["fitted"]
            >>> # Use:
            >>> self._fitted_values = self._expand_to_full_length(result["fitted"])
        """
        full = np.full(self._n_total, np.nan)
        full[self._valid_mask] = valid_values
        return full

    def _add_orig_columns(self) -> None:
        """Add {var}_orig columns for transformed variables.

        For each transform in transform_state (center, scale, log, etc.),
        creates a backup column with the original values. This enables
        visualization on the original scale after transformation.

        Called by _augment_data() after fitting.
        """
        if not self._dm.transform_state:
            return

        # Collect columns to add
        new_columns = []
        for state in self._dm.transform_state.values():
            var_name = state["variable"]
            orig_col = f"{var_name}_orig"

            # Skip if already exists (idempotent)
            if orig_col in self._data.columns:
                continue

            # Skip if source column doesn't exist (shouldn't happen, but be safe)
            if var_name not in self._data.columns:
                continue

            # Add original column
            new_columns.append(pl.col(var_name).alias(orig_col))

        if new_columns:
            self._data = self._data.with_columns(new_columns)

    def _parse_conf_int(self, conf_int: float | int | str) -> float:
        """Parse flexible confidence interval input to float.

        Args:
            conf_int: Confidence level as float (0.95), int (95), or string ("95", "95%").

        Returns:
            Confidence level as float in [0, 1].

        Examples:
            >>> model._parse_conf_int(0.95)
            0.95
            >>> model._parse_conf_int(95)
            0.95
            >>> model._parse_conf_int("95%")
            0.95
        """
        from bossanova.ops.inference import parse_conf_int

        return parse_conf_int(conf_int)

    # =========================================================================
    # Abstract methods (subclasses must implement)
    # =========================================================================

    @abstractmethod
    def fit(self, **kwargs) -> Self:
        """Fit the model. Subclasses must implement model-specific fitting algorithm."""

    @abstractmethod
    def _compute_result_params(self, conf_level: float = 0.95) -> pl.DataFrame:
        """Build coefficient table. Schema varies by model type.

        Args:
            conf_level: Confidence level for intervals (default 0.95).
        """

    @abstractmethod
    def _compute_result_model(self) -> pl.DataFrame:
        """Build fit statistics table. Schema varies by model type."""

    @abstractmethod
    def _simulate_response(self, mu: np.ndarray) -> np.ndarray:
        """Simulate response given expected values.

        Subclasses implement family-specific noise generation:
        - lm: Gaussian noise with sigma
        - glm: Family-specific (gaussian, binomial, poisson)
        - lmer/glmer: Handled in BaseMixedModel

        Args:
            mu: Expected values (fitted values or predictions).

        Returns:
            Simulated response values with appropriate noise.
        """

    # =========================================================================
    # Concrete methods (shared implementation)
    # =========================================================================

    def simulate(
        self,
        nsim: int = 1,
        seed: int | None = None,
    ) -> np.ndarray:
        """Simulate responses from fitted model.

        Generates new response values by adding appropriate noise to the
        fitted values. Useful for parametric bootstrap and model checking.

        Args:
            nsim: Number of simulations.
            seed: Random seed for reproducibility.

        Returns:
            Array of shape (n, nsim) with simulated responses.

        Examples:
            ```python
            # Parametric bootstrap
            model = lm("y ~ x", data).fit()
            sims = model.simulate(nsim=1000, seed=42)

            # Check if observed data looks like simulated data
            observed_mean = model.fitted.mean()
            sim_means = sims.mean(axis=0)
            ```
        """
        self._check_fitted()

        if seed is not None:
            np.random.seed(seed)

        sims = np.zeros((self._n, nsim))
        mu = self._fitted_values

        for i in range(nsim):
            sims[:, i] = self._simulate_response(mu)

        return sims

    def predict(
        self,
        data: pl.DataFrame | PandasDataFrame,
        units: str = "data",
        pred_int: float | None = None,
        **kwargs,
    ) -> pl.DataFrame:
        """Predict response values for new data.

        This method is for making predictions on new observations.
        For fitted values on training data, use the `.fitted` property.

        Args:
            data: New data for prediction. Must contain all predictor columns.
            units: Scale for predictions: ``"data"`` (response scale, default)
                or ``"link"`` (link function scale). For lm/lmer both are
                identical. For GLM/GLMER, ``"data"`` applies the inverse link
                (e.g., probabilities for logistic).
            pred_int: Prediction interval level (e.g., 0.95 for 95% intervals).
                None (default) returns point predictions only.
            **kwargs: Subclass-specific options (e.g., varying for mixed models).

        Returns:
            DataFrame with prediction columns (fitted, and optionally lwr, upr).

        See Also:
            fitted: Property returning fitted values on training data.
            mem: Method for marginal effects and means (model interpretation).
        """
        self._check_fitted()
        raise NotImplementedError("predict() implementation in subclass")

    def summary(self, decimals: int = 3) -> None:
        """Print model summary.

        Args:
            decimals: Number of decimal places to display.
        """
        self._check_fitted()
        raise NotImplementedError("summary() implementation in subclass")

    def show_math(self, explanations: bool = True) -> "MathDisplay":
        """Display structural LaTeX equation with term explanations.

        Returns a display object that renders as LaTeX in Jupyter notebooks
        and Quarto documents. Shows the symbolic form of the model equation,
        NOT fitted coefficient values.

        Args:
            explanations: If True (default), include term explanations with
                contrast types, reference levels, and transformation parameters.

        Returns:
            MathDisplay object with rich display support:
            - Renders as LaTeX in Jupyter/Quarto
            - Falls back to HTML+MathJax when needed
            - ``.to_latex()`` for raw LaTeX string

        Examples:
            >>> model = lm("y ~ center(x1) + group", data=df)
            >>> model.show_math()  # Works before or after fit()

            >>> latex_str = model.show_math().to_latex()  # Get raw LaTeX
        """
        from bossanova.models.latex import build_equation

        return build_equation(self, explanations=explanations)

    def jointtest(self, *, verbose: bool = True, errors: str = "auto") -> pl.DataFrame:
        """Compute ANOVA table (Type III tests).

        Args:
            verbose: If True (default), print a message when auto-fitting
                an unfitted model. Set to False to suppress the message.
            errors: Error structure assumption for robust F-tests (lm only):
                - None: Use standard OLS F-test (default)
                - "hetero": Robust F-test with HC3 sandwich covariance
                - "unequal_var": Welch's ANOVA (group-specific variances,
                  auto-detects factors from formula)
                - "HC0", "HC1", "HC2", "HC3": Specific sandwich estimators

        Returns:
            ANOVA table with columns [term, df1, df2, f_ratio, p_value]
            or [term, df1, Chisq, p_value] for glm/glmer.

        Note:
            Uses emmeans-style joint tests (tests EMM contrasts).
            Equivalent to Type III ANOVA for factors with balanced contrasts.
            If the model has not been fitted, it will be automatically
            fitted with default parameters.

        Examples:
            >>> # Standard ANOVA
            >>> model.fit().jointtest()

            >>> # Welch's ANOVA (unequal variances)
            >>> model.fit().jointtest(errors="unequal_var")

            >>> # Robust ANOVA with HC3
            >>> model.fit().jointtest(errors="hetero")
        """
        if not self.is_fitted:
            if verbose:
                print("Model not fitted. Fitting with default parameters...")
            self.fit()
        from bossanova.marginal import joint_tests

        return joint_tests(self, errors=errors)

    def anova(self, *, verbose: bool = True, errors: str = "auto") -> pl.DataFrame:
        """Alias for :meth:`jointtest`."""
        return self.jointtest(verbose=verbose, errors=errors)

    def vif(self) -> pl.DataFrame:
        """Compute variance inflation factors.

        Returns:
            DataFrame with columns [term, vif, ci_increase_factor].

        Note:
            Excludes intercept. ci_increase_factor = sqrt(vif) shows
            CI inflation due to multicollinearity. Warns if VIF > 10.
            Does not require fitting - computed from design matrix only.
        """
        from bossanova.ops.diagnostics import compute_vif

        # Use only valid rows (excludes rows dropped due to missing values)
        X_valid = self._X[self._valid_mask]
        return compute_vif(X_valid, self._X_names)

    # =========================================================================
    # Factor/Contrast/Transform methods
    # =========================================================================

    def set_factors(
        self, factors: dict[str, list[str]] | list[str] | str, *, refit: bool = True
    ) -> None:
        """Set variables as categorical factors with the first level as reference.

        Converts specified columns to polars Enum type and automatically sets
        treatment contrasts with the first level as the reference. This matches
        the intuitive pymer4/R behavior where factor level order determines
        the reference level.

        Args:
            factors: Either a dict mapping column names to ordered level lists,
                a list of column names, or a single column name string (levels
                will be auto-detected as sorted unique values). The first level
                becomes the reference.
            refit: Whether to mark model as unfitted after changing factors.
                Default True. Set to False only when setting factors before
                first fit.

        Examples:
            >>> # Explicit levels - "control" is reference
            >>> model.set_factors({"group": ["control", "treatment1", "treatment2"]})
            >>> model.fit()
            >>> # Coefficients: Intercept, group[treatment1], group[treatment2]

            >>> # Single column (auto-detect levels)
            >>> model.set_factors("group")
            >>> model.fit()

            >>> # Multiple columns as list
            >>> model.set_factors(["group", "condition"])
            >>> model.fit()

            >>> # Override contrast type after setting factors
            >>> model.set_factors({"group": ["A", "B", "C"]})
            >>> model.set_contrasts({"group": "sum"})  # Switch to sum coding
            >>> model.fit()

        Note:
            This method automatically calls set_contrasts() with treatment
            contrasts using the first level as reference. You can override
            this by calling set_contrasts() again after set_factors().
        """
        # Normalize single string to list
        if isinstance(factors, str):
            factors = [factors]

        # Normalize to dict format
        if isinstance(factors, list):
            factors_dict: dict[str, list[str]] = {}
            for col_name in factors:
                if col_name not in self._data.columns:
                    raise ValueError(f"Column '{col_name}' not found in data")
                # Auto-detect levels: sorted unique values cast to string
                unique_vals = (
                    self._data[col_name].unique().cast(pl.String).sort().to_list()
                )
                factors_dict[col_name] = unique_vals
        else:
            factors_dict = factors

        # Validate columns exist
        for col_name in factors_dict:
            if col_name not in self._data.columns:
                raise ValueError(f"Column '{col_name}' not found in data")

        # Store original dtypes before conversion
        if self._original_dtypes is None:
            self._original_dtypes = {}
        for col_name in factors_dict:
            if col_name not in self._original_dtypes:
                self._original_dtypes[col_name] = self._data[col_name].dtype

        # Convert columns to Enum type
        expressions = []
        for col_name, levels in factors_dict.items():
            expr = pl.col(col_name).cast(pl.String).cast(pl.Enum(levels))
            expressions.append(expr)

        self._data = self._data.with_columns(*expressions)

        # Merge with existing factors (update if already exists)
        if self._factors is None:
            self._factors = factors_dict
        else:
            self._factors.update(factors_dict)

        # Auto-set treatment contrasts with first level as reference (pymer4 pattern)
        # Build contrast spec: each factor gets ("treatment", first_level)
        new_contrasts = {
            col: ("treatment", levels[0]) for col, levels in factors_dict.items()
        }

        # Merge with existing contrasts (new factors override)
        if self._contrasts_spec is None:
            self._contrasts_spec = new_contrasts
        else:
            self._contrasts_spec.update(new_contrasts)

        # Rebuild working formula with transforms and contrasts
        from bossanova.formula.transforms import transform_formula

        self._formula_working = transform_formula(
            self._formula,
            transforms=self._transforms_spec,
            contrasts=self._contrasts_spec,
        )

        # Re-parse formula with new factor types and contrasts
        self._parse_formula()

        if refit:
            self.is_fitted = False

    def unset_factors(self, columns: list[str] | str | None = None) -> None:
        """Remove factor settings and restore original column types.

        Reverts Enum columns back to their original data types (Float64, Int64,
        or String) and removes them from the factor registry.

        Args:
            columns: Columns to remove factor settings for. Accepts a single
                column name string, a list of column names, or None for all.

        Examples:
            >>> model.set_factors(["group", "condition"])
            >>> model.unset_factors("group")  # Revert only group
            >>> model.unset_factors()  # Revert all remaining factors

        Note:
            After unsetting factors, you must call fit() again.
        """
        if self._factors is None:
            return

        # Normalize string to list
        if isinstance(columns, str):
            columns = [columns]

        # Determine which columns to unset
        if columns is None:
            cols_to_unset = list(self._factors.keys())
        else:
            cols_to_unset = [c for c in columns if c in self._factors]

        if not cols_to_unset:
            return

        # Restore original dtypes
        expressions = []
        for col_name in cols_to_unset:
            if self._original_dtypes and col_name in self._original_dtypes:
                original_dtype = self._original_dtypes[col_name]
            else:
                # Fallback: infer from first level value (pymer4 pattern)
                levels = self._factors[col_name]
                if levels:
                    first_level = levels[0]
                    if "." in first_level:
                        try:
                            float(first_level)
                            original_dtype = pl.Float64
                        except ValueError:
                            original_dtype = pl.String
                    else:
                        try:
                            int(first_level)
                            original_dtype = pl.Int64
                        except ValueError:
                            original_dtype = pl.String
                else:
                    original_dtype = pl.String

            # Cast through String first: Enum → String → original_type
            # Direct Enum → Int64 gives physical category codes, not values
            if original_dtype == pl.String:
                expressions.append(pl.col(col_name).cast(pl.String))
            else:
                expressions.append(
                    pl.col(col_name).cast(pl.String).cast(original_dtype)
                )

        self._data = self._data.with_columns(*expressions)

        # Remove from factor registry
        for col_name in cols_to_unset:
            del self._factors[col_name]
            if self._original_dtypes and col_name in self._original_dtypes:
                del self._original_dtypes[col_name]

        # Keep as empty dict (not None) to signal explicit user management
        # This prevents show_factors() from falling back to auto-detected factors
        if self._original_dtypes and not self._original_dtypes:
            self._original_dtypes = None

        # Remove contrasts for unset columns and regenerate formula
        if self._contrasts_spec is not None:
            for col_name in cols_to_unset:
                self._contrasts_spec.pop(col_name, None)
            if not self._contrasts_spec:
                self._contrasts_spec = None

        from bossanova.formula.transforms import transform_formula

        self._formula_working = transform_formula(
            self._formula,
            transforms=self._transforms_spec,
            contrasts=self._contrasts_spec,
        )

        # Re-parse formula
        self._parse_formula()
        self.is_fitted = False

    def show_factors(self, *, verbose: bool = False) -> dict[str, list[str]]:
        """Show current factor settings.

        Prints a compact summary of factor terms with level counts and
        ordered levels (reference level marked with ``*``). Returns the
        underlying dictionary for programmatic use.

        Args:
            verbose: If True, show all levels without truncation.
                Default False truncates to first 3 + last 3 levels.

        Returns:
            Dictionary mapping column names to level lists (first level is
            the reference). Empty dict if no factors are present.

        Examples:
            >>> model.show_factors()
            Factors:
              sex      (2 levels): female*, male
              pclass   (3 levels): 1st*, 2nd, 3rd
        """
        # First priority: explicitly set factors (includes empty dict after unset)
        if self._factors is not None:
            result = {k: list(v) for k, v in self._factors.items()}
        elif hasattr(self, "_dm") and self._dm is not None:
            if hasattr(self._dm, "factors") and self._dm.factors:
                result = {k: list(v) for k, v in self._dm.factors.items()}
            else:
                result = {}
        else:
            result = {}

        self._print_factors(result, verbose=verbose)
        return result

    def _print_factors(
        self, factors: dict[str, list[str]], *, verbose: bool = False
    ) -> None:
        """Print factors in compact format."""
        if not factors:
            print("Factors: (none)")
            return

        max_name = max(len(n) for n in factors)
        lines = ["Factors:"]
        for name, levels in factors.items():
            n = len(levels)
            ref = str(levels[0]) + "*"
            rest = [str(lv) for lv in levels[1:]]

            if not verbose and n > 6:
                # First 3 (including ref) + last 3
                shown = [ref] + rest[:2] + ["..."] + rest[-3:]
            else:
                shown = [ref] + rest

            levels_str = ", ".join(shown)
            lines.append(f"  {name:<{max_name}}  ({n} levels): {levels_str}")

        print("\n".join(lines))

    def set_contrasts(
        self,
        contrasts: dict[str, str | tuple[str, str] | np.ndarray | list],
        *,
        normalize: bool = True,
    ) -> None:
        """Set contrast coding for categorical variables.

        Transforms the formula by wrapping categorical variables in factor()
        with the specified contrast type, or uses custom numeric contrasts.

        Args:
            contrasts: Mapping from column name to contrast specification.
                Each value can be:
                - String: "treatment", "sum", or "poly" (uses default reference)
                - Tuple: ("treatment", "reference_level") for explicit reference
                - Array/list: Custom contrast vector(s). Shape (n_contrasts, n_levels)
                  or (n_levels,) for single contrast. Converted to coding matrix
                  via QR decomposition.
            normalize: If True, normalize custom contrast vectors by their L2 norm
                before conversion. Only applies to numeric contrasts.

        Examples:
            >>> # Named contrast type
            >>> model.set_contrasts({"group": "sum"})

            >>> # Treatment with explicit reference level
            >>> model.set_contrasts({"group": ("treatment", "control")})

            >>> # Custom contrast: A vs average(B, C)
            >>> model.set_contrasts({"group": [-1, 0.5, 0.5]})

            >>> # Multiple custom contrasts
            >>> model.set_contrasts({"group": [[-1, 0.5, 0.5], [0, -1, 1]]})

            >>> # With normalization
            >>> model.set_contrasts({"group": [-1, 0.5, 0.5]}, normalize=True)

        Note:
            After calling set_contrasts(), you must call fit() again.
            The model's fitted_ flag is set to False.

            Custom contrasts are converted to a coding matrix using QR
            decomposition, matching R's gmodels::make.contrasts() behavior.
        """
        from bossanova.formula.transforms import transform_formula, VALID_CONTRASTS
        from bossanova.formula.contrasts import array_to_coding_matrix

        # Separate named contrasts from custom (numeric) contrasts
        named_contrasts: dict[str, str | tuple[str, str]] = {}
        custom_contrasts: dict[str, np.ndarray] = {}

        for col, contrast_spec in contrasts.items():
            # Check if it's a numeric contrast (array or list of numbers)
            if isinstance(contrast_spec, np.ndarray):
                # Validate we have factor info to determine n_levels
                if self._factors and col in self._factors:
                    n_levels = len(self._factors[col])
                else:
                    # Try to infer from data
                    if col not in self._data.columns:
                        raise ValueError(f"Variable '{col}' not found in data")
                    n_levels = self._data[col].n_unique()

                custom_contrasts[col] = array_to_coding_matrix(
                    contrast_spec, n_levels=n_levels, normalize=normalize
                )
            elif isinstance(contrast_spec, list) and contrast_spec:
                # Check if it's a list of numbers (single contrast) or list of lists
                first = contrast_spec[0]
                if isinstance(first, (int, float, np.floating, np.integer)):
                    # Single contrast vector
                    if self._factors and col in self._factors:
                        n_levels = len(self._factors[col])
                    else:
                        if col not in self._data.columns:
                            raise ValueError(f"Variable '{col}' not found in data")
                        n_levels = self._data[col].n_unique()

                    custom_contrasts[col] = array_to_coding_matrix(
                        contrast_spec, n_levels=n_levels, normalize=normalize
                    )
                elif isinstance(first, (list, np.ndarray)):
                    # Multiple contrast vectors
                    if self._factors and col in self._factors:
                        n_levels = len(self._factors[col])
                    else:
                        if col not in self._data.columns:
                            raise ValueError(f"Variable '{col}' not found in data")
                        n_levels = self._data[col].n_unique()

                    custom_contrasts[col] = array_to_coding_matrix(
                        contrast_spec, n_levels=n_levels, normalize=normalize
                    )
                else:
                    # Not a numeric list - treat as error
                    raise ValueError(
                        f"Invalid contrast specification for '{col}'. "
                        "Expected string, tuple, or numeric array."
                    )
            elif isinstance(contrast_spec, (str, tuple)):
                # Named contrast type
                contrast_type = (
                    contrast_spec[0]
                    if isinstance(contrast_spec, tuple)
                    else contrast_spec
                )
                if contrast_type not in VALID_CONTRASTS:
                    raise ValueError(
                        f"Unknown contrast '{contrast_type}' for variable '{col}'. "
                        f"Valid contrasts: {sorted(VALID_CONTRASTS)}"
                    )
                named_contrasts[col] = contrast_spec
            else:
                raise ValueError(
                    f"Invalid contrast specification for '{col}'. "
                    "Expected string, tuple, or numeric array."
                )

        # Store specs
        self._contrasts_spec = named_contrasts if named_contrasts else None
        self._custom_contrasts = custom_contrasts if custom_contrasts else None

        # Rebuild working formula with named contrasts only
        # (custom contrasts don't need formula transformation)
        self._formula_working = transform_formula(
            self._formula,
            transforms=self._transforms_spec,
            contrasts=self._contrasts_spec,
        )

        # Re-parse formula with new contrasts
        self._parse_formula()
        self.is_fitted = False

    def show_contrasts(self, *, verbose: bool = False) -> dict[str, dict[str, Any]]:
        """Show current contrast settings.

        Prints a compact summary of contrast type and code vectors per factor.
        Returns the underlying dictionary for programmatic use.

        Args:
            verbose: If True, show the full contrast matrix with labeled
                rows and columns. Default False shows contrast type and
                code vectors aligned to displayed factor levels.

        Returns:
            Dictionary mapping column names to contrast info. Each value
            contains ``"type"`` and optionally ``"reference"`` or
            ``"matrix"``. Empty dict if no contrasts configured.

        Examples:
            >>> model.show_contrasts()
            Contrasts:
              sex      treatment  [0, 1]
              pclass   treatment  [0, 1, 0]  [0, 0, 1]
        """
        if not self._dm.contrast_matrices:
            print("Contrasts: (none)")
            return {}

        # Build info dict
        result: dict[str, dict[str, Any]] = {}
        for var_name in self._dm.contrast_matrices:
            if self._custom_contrasts and var_name in self._custom_contrasts:
                result[var_name] = {
                    "type": "custom",
                    "matrix": self._dm.contrast_matrices[var_name],
                }
            elif self._contrasts_spec and var_name in self._contrasts_spec:
                contrast_spec = self._contrasts_spec[var_name]
                if isinstance(contrast_spec, tuple):
                    result[var_name] = {
                        "type": contrast_spec[0],
                        "reference": contrast_spec[1],
                    }
                else:
                    result[var_name] = {"type": contrast_spec}
            else:
                result[var_name] = {"type": "treatment"}

        self._print_contrasts(result, verbose=verbose)
        return result

    def _print_contrasts(
        self, contrasts: dict[str, dict[str, Any]], *, verbose: bool = False
    ) -> None:
        """Print contrasts in compact format."""
        if not contrasts:
            print("Contrasts: (none)")
            return

        max_name = max(len(n) for n in contrasts)
        lines = ["Contrasts:"]

        for var_name, info in contrasts.items():
            ctype = info["type"]
            mat = self._dm.contrast_matrices.get(var_name)

            # Get factor levels
            levels: list[str] = []
            if self._factors and var_name in self._factors:
                levels = list(self._factors[var_name])
            elif hasattr(self._dm, "factors") and var_name in self._dm.factors:
                levels = list(self._dm.factors[var_name])

            if verbose and mat is not None:
                # Full matrix with labeled rows
                ref_note = ""
                if "reference" in info:
                    ref_note = f"  (ref={info['reference']})"
                lines.append(f"  {var_name:<{max_name}}  {ctype}{ref_note}")

                def _fmt_val(v: float) -> str:
                    return f"{v: .0f}" if v == int(v) else f"{v:.2f}"

                if levels:
                    max_lv = max(len(str(lv)) for lv in levels)
                    for i, level in enumerate(levels):
                        codes = "  ".join(_fmt_val(v) for v in mat[i])
                        lines.append(f"    {str(level):<{max_lv}}  [{codes}]")
                else:
                    for row in mat:
                        codes = "  ".join(_fmt_val(v) for v in row)
                        lines.append(f"    [{codes}]")
            elif mat is not None:
                # Compact: type + code vectors (columns of contrast matrix)
                n_levels = mat.shape[0]
                n_cols = mat.shape[1]

                # For high-cardinality factors, skip code vectors entirely
                if n_cols > 6:
                    lines.append(
                        f"  {var_name:<{max_name}}  {ctype}"
                        f"  ({n_cols} contrasts, {n_levels} levels)"
                    )
                else:
                    code_strs = []
                    for col_idx in range(n_cols):
                        col = mat[:, col_idx]
                        if n_levels > 6:
                            vals = list(col[:3]) + list(col[-3:])
                            parts = [
                                str(int(v)) if v == int(v) else f"{v:.1f}" for v in vals
                            ]
                            code_str = (
                                "["
                                + ", ".join(parts[:3])
                                + ", ..., "
                                + ", ".join(parts[3:])
                                + "]"
                            )
                        else:
                            parts = [
                                str(int(v)) if v == int(v) else f"{v:.1f}" for v in col
                            ]
                            code_str = "[" + ", ".join(parts) + "]"
                        code_strs.append(code_str)
                    codes_display = "  ".join(code_strs)
                    lines.append(f"  {var_name:<{max_name}}  {ctype}  {codes_display}")
            else:
                lines.append(f"  {var_name:<{max_name}}  {ctype}")

        print("\n".join(lines))

    def set_transforms(self, transforms: dict[str, str]) -> None:
        """Set transforms for numeric variables.

        Transforms the formula by wrapping variables in transform functions.
        Formulae handles parameter storage (mean, std) automatically.

        Args:
            transforms: Mapping from column name to transform type.
                Valid types: "center", "scale", "log", "log10", "sqrt".

        Examples:
            >>> model.set_transforms({"tv": "center", "radio": "scale"})
            >>> model.fit()  # Must re-fit after changing transforms

        Note:
            After calling set_transforms(), you must call fit() again.
            Transform parameters (mean, std) are learned from the training data
            and automatically preserved for predictions on new data.
        """
        from bossanova.formula.transforms import transform_formula, VALID_TRANSFORMS

        # Validate transform types and column existence
        for col, transform in transforms.items():
            if transform not in VALID_TRANSFORMS:
                raise ValueError(
                    f"Unknown transform '{transform}' for variable '{col}'. "
                    f"Valid transforms: {sorted(VALID_TRANSFORMS)}"
                )
            if col not in self._data.columns:
                raise ValueError(f"Column '{col}' not found in data")

        # Store spec and rebuild working formula
        self._transforms_spec = transforms
        self._formula_working = transform_formula(
            self._formula,
            transforms=self._transforms_spec,
            contrasts=self._contrasts_spec,
        )

        # Re-parse formula with new transforms
        self._parse_formula()
        self.is_fitted = False

    def unset_transforms(self, cols: list[str] | str | None = None) -> None:
        """Remove transform settings.

        Args:
            cols: Columns to remove transforms for. Accepts a single column
                name string, a list of column names, or None for all.

        Examples:
            >>> model.unset_transforms("tv")  # Remove tv transform only
            >>> model.unset_transforms()  # Remove all transforms
            >>> model.fit()  # Must re-fit
        """
        if self._transforms_spec is None:
            return

        # Normalize string to list
        if isinstance(cols, str):
            cols = [cols]

        if cols is None:
            self._transforms_spec = None
        else:
            for col in cols:
                self._transforms_spec.pop(col, None)
            if not self._transforms_spec:
                self._transforms_spec = None

        # Rebuild working formula
        from bossanova.formula.transforms import transform_formula

        self._formula_working = transform_formula(
            self._formula,
            transforms=self._transforms_spec,
            contrasts=self._contrasts_spec,
        )
        self._parse_formula()
        self.is_fitted = False

    def show_transforms(self, *, verbose: bool = False) -> dict[str, dict[str, Any]]:
        """Show current transform settings.

        Prints a compact summary of transform types applied to variables.
        Returns the underlying dictionary for programmatic use.

        Args:
            verbose: If True, show stored parameters (mean, std, etc.).
                Default False shows only variable name and transform type.

        Returns:
            Dictionary mapping transform keys to info dicts containing
            ``"type"``, ``"variable"``, and optionally ``"params"`` with
            stored parameters. Empty dict if no transforms configured.

        Examples:
            >>> model.show_transforms()
            Transforms:
              age   center
              hp    scale

            >>> model.show_transforms(verbose=True)
            Transforms:
              age   center  (mean=29.70)
              hp    scale   (mean=146.69, std=68.56)
        """
        if not self._dm.transform_state:
            print("Transforms: (none)")
            return {}

        # Build result dict (copy to prevent mutation, clarify log base)
        result: dict[str, dict[str, Any]] = {}
        for k, v in self._dm.transform_state.items():
            info = dict(v)
            if info.get("type") == "log":
                info["type"] = "log (natural)"
            result[k] = info

        self._print_transforms(result, verbose=verbose)
        return result

    def _print_transforms(
        self, transforms: dict[str, dict[str, Any]], *, verbose: bool = False
    ) -> None:
        """Print transforms in compact format."""
        if not transforms:
            print("Transforms: (none)")
            return

        # Use the original variable name for display
        entries = []
        for _key, info in transforms.items():
            var = info.get("variable", _key)
            ttype = info.get("type", "unknown")
            entries.append((var, ttype, info))

        max_name = max(len(e[0]) for e in entries)
        lines = ["Transforms:"]
        for var, ttype, info in entries:
            line = f"  {var:<{max_name}}  {ttype}"
            if verbose:
                params = info.get("params", {})
                if params:
                    parts = [f"{k}={v:.2f}" for k, v in params.items()]
                    line += f"  ({', '.join(parts)})"
            lines.append(line)

        print("\n".join(lines))

    # =========================================================================
    # Marginal Estimation Methods
    # =========================================================================

    def _get_inference_df(self) -> float:
        """Get degrees of freedom for inference.

        Returns the appropriate df for confidence intervals and hypothesis tests:
        - lm: residual df (n - p) for t-distribution
        - glm/glmer: np.inf for z-distribution (asymptotic)
        - lmer: mean Satterthwaite df across coefficients

        Subclasses should override if needed.

        Returns:
            Degrees of freedom (scalar). np.inf indicates z-distribution.
        """
        # Default: use _df_resid if available, else infinity (asymptotic)
        if hasattr(self, "_df_resid"):
            return float(self._df_resid)
        return np.inf

    def _compute_emm_df(self, X_ref: np.ndarray) -> float | np.ndarray:
        """Compute degrees of freedom for EMMs given prediction matrix.

        This hook allows models with contrast-specific df (like lmer with
        Satterthwaite) to compute per-EMM df values. Each row of X_ref
        defines a contrast (linear combination of coefficients).

        Default implementation returns scalar df from _get_inference_df().
        LMer overrides this to return per-contrast Satterthwaite df.

        Args:
            X_ref: Prediction matrix, shape (n_emms, n_coef). Each row defines
                one EMM as a linear combination of coefficients.

        Returns:
            Either a scalar float (same df for all EMMs) or an array of shape
            (n_emms,) with per-EMM df values.
        """
        return self._get_inference_df()

    def _get_family(self):
        """Get the GLM family for link transformations.

        Returns None for linear models (lm, lmer) which don't have a link function.
        Overridden by GLM and GLMER to return their Family object.

        Returns:
            Family object with link_inverse and link_deriv methods, or None.
        """
        return None

    def mee(
        self,
        specs: str,
        *,
        at: dict[str, Any] | None = None,
        agg: bool = True,
        contrasts: str | dict[str, list | np.ndarray] | None = None,
        units: str = "data",
        normalize: bool = True,
    ) -> Self:
        """Compute marginal estimated effects.

        Unified method for model interpretation that automatically computes:
        - Marginal means for categorical variables
        - Marginal effects (slopes) for continuous variables

        This method computes point estimates only. Call ``.infer()`` to add
        uncertainty quantification (standard errors, confidence intervals,
        p-values for contrasts).

        Args:
            specs: Formula specifying what to compute. Supports:
                - Variable names: "treatment", "age"
                - Multiple specs: "treatment + age" (returns both)
                - Stratification: "treatment | gender" (treatment BY gender)
                - Inline values: "treatment | age[30, 50]"
                - Shortcuts: "age[mean]", "age[minmax]", "age[q25, q75]"
            at: Alternative to inline syntax for specifying covariate values.
                Used for programmatic access or complex cases.
            agg: If True (default), average over non-focal variables to get
                population-level effects. With by_vars (``|``), averaging is
                within each by-group. If False, return individual-level
                counterfactual predictions (one per observation per level for
                categorical, or per-cell slopes for continuous).
            contrasts: Type of contrast to compute (for categorical variables):
                - None: Return effects/means (default)
                - "pairwise": All pairwise comparisons
                - "revpairwise": Reversed pairwise
                - "trt.vs.ctrl": Each level vs first level
                - dict: Custom contrasts {"name": [coefficients]}
            units: Scale for output values. Options:

                - ``"data"`` (default): Response/data scale. For lm/lmer this
                  is the identity (no transformation). For GLM/GLMER, applies
                  the inverse link to give interpretable units (probabilities
                  for logistic, counts for Poisson).
                - ``"link"``: Link function scale. For lm/lmer, identical to
                  ``"data"``. For GLM/GLMER, gives log-odds (logit), log-counts
                  (log), etc.
            normalize: If True, normalize custom contrast vectors to unit length
                (L2 norm = 1). This changes the scale of estimates but not
                statistical significance. Only applies to custom dict contrasts.

        Returns:
            Self for method chaining. Access results via ``.result_mee``.

        Examples:
            >>> model = lm("y ~ treatment * age + gender", data=df)
            >>> model.fit()

            >>> # Marginal means for treatment (estimates only)
            >>> model.mee("treatment")
            >>> model.result_mee  # term, level, estimate

            >>> # Add inference (SE, CI)
            >>> model.mee("treatment").infer()
            >>> model.result_mee  # + se, df, ci_lower, ci_upper

            >>> # Both in one call
            >>> model.mee("treatment + age")

            >>> # Treatment means BY gender
            >>> model.mee("treatment | gender")

            >>> # Pairwise contrasts with p-values
            >>> model.mee("treatment", contrasts="pairwise").infer()

            >>> # Bootstrap inference
            >>> model.mee("treatment").infer(how="boot", n=999)
        """
        self._check_fitted()

        # Validate units parameter
        if units not in ("link", "data"):
            raise ValueError(f"units must be 'link' or 'data', got {units!r}")

        from bossanova.marginal.parser import parse_mee_spec, resolve_shortcuts

        # Parse the specification
        parsed = parse_mee_spec(specs)

        # Resolve any shortcuts in at_values
        at_values: dict[str, list[Any]] = {}
        if parsed.at_values:
            at_values = resolve_shortcuts(parsed.at_values, self._data)

        # Merge with explicit at parameter
        if at is not None:
            at_values.update(at)

        # Classify focal variables
        categorical_vars = []
        continuous_vars = []

        for var in parsed.focal_vars:
            if var not in self._data.columns:
                raise ValueError(f"Variable {var!r} not found in data")
            var_type = self._classify_variable(var)
            if var_type == "categorical":
                categorical_vars.append(var)
            else:
                continuous_vars.append(var)

        # Compute results for each variable type
        # Internal methods now store X_ref/inference data and return minimal DataFrames
        results = []
        X_refs = []
        mee_dfs = []

        # Categorical variables → marginal means
        if categorical_vars:
            for var in categorical_vars:
                df_result, X_ref, df_val = self._mee_categorical_minimal(
                    var=var,
                    by_vars=parsed.by_vars,
                    at_values=at_values,
                    agg=agg,
                    contrasts=contrasts,
                    units=units,
                    normalize=normalize,
                )
                results.append(df_result)
                X_refs.append(X_ref)
                mee_dfs.append(df_val)

        # Continuous variables → marginal effects (slopes) OR EMMs at explicit values
        if continuous_vars:
            for var in continuous_vars:
                # Check if this focal var has explicit at_values (from bracket syntax)
                # If so, compute EMMs at those points instead of slopes
                if var in at_values:
                    df_result, X_ref, df_val = self._mee_continuous_at_values_minimal(
                        var=var,
                        values=at_values[var],
                        by_vars=parsed.by_vars,
                        at_values={k: v for k, v in at_values.items() if k != var},
                        units=units,
                    )
                else:
                    # Default: compute slopes (marginal effects)
                    df_result, X_ref, df_val = self._mee_continuous_minimal(
                        var=var,
                        by_vars=parsed.by_vars,
                        at_values=at_values,
                        agg=agg,
                        units=units,
                    )
                results.append(df_result)
                X_refs.append(X_ref)
                mee_dfs.append(df_val)

        # Combine results
        if not results:
            raise ValueError("No valid focal variables in specs")

        if len(results) == 1:
            combined_result = results[0]
        else:
            combined_result = pl.concat(results, how="diagonal")

        # Store MEE state for .infer()
        self._result_mee = combined_result
        self._mee_specs = specs
        self._mee_has_contrasts = contrasts is not None

        # Stack X_refs if multiple focal variables
        if len(X_refs) == 1:
            self._mee_X_ref = X_refs[0]
            self._mee_df = mee_dfs[0]
        else:
            # Vertical stack for multiple focal vars
            self._mee_X_ref = np.vstack(X_refs)
            # Concatenate df arrays
            self._mee_df = np.concatenate(
                [
                    np.atleast_1d(d) if np.isscalar(d) or d.ndim == 0 else d
                    for d in mee_dfs
                ]
            )

        # Track operation for .infer() dispatch
        self._last_operation = "mee"

        return self

    def _classify_variable(self, var: str) -> str:
        """Classify a variable as categorical or continuous.

        Checks both the data column dtype and whether the variable was
        wrapped in factor() in the formula (stored in _dm.contrast_types).

        Args:
            var: Variable name.

        Returns:
            "categorical" or "continuous".
        """
        # Check if variable was wrapped in factor() in formula
        if self._dm.contrast_types and var in self._dm.contrast_types:
            return "categorical"
        # Check data dtype
        dtype = self._data[var].dtype
        if dtype in (pl.Enum, pl.Categorical, pl.String):
            return "categorical"
        return "continuous"

    def _mee_categorical(
        self,
        var: str,
        by_vars: list[str],
        at_values: dict[str, list[Any]],
        agg: bool,
        contrasts: str | dict[str, list | np.ndarray] | None,
        conf_level: float,
        p_adjust: str,
        units: str,
        normalize: bool = True,
    ) -> pl.DataFrame:
        """Compute marginal means for a categorical variable.

        Delegates to existing EMM infrastructure.
        """
        from bossanova.marginal.emm import compute_emm, EMMResult
        from bossanova.marginal.grid import build_reference_grid

        # Individual-level counterfactual predictions when agg=False
        if not agg:
            return self._mee_categorical_individual(
                var, by_vars, at_values, conf_level, p_adjust, units
            )

        # Build reference grid
        # Separate by_vars into categorical (expand grid) and continuous (set to mean)
        factors = [var]
        continuous_by_vars = []
        if by_vars:
            for bv in by_vars:
                if self._classify_variable(bv) == "categorical":
                    factors.append(bv)
                else:
                    continuous_by_vars.append(bv)

        # Get other model variables for proper interaction handling
        other_factors, covariates = self._get_other_model_variables(factors)
        all_factors = factors + other_factors

        # Add continuous by_vars to covariates so they appear in grid at their mean
        covariates = list(covariates) + continuous_by_vars

        # Merge at_values with covariate means
        at_for_grid = at_values.copy() if at_values else {}

        grid = build_reference_grid(
            self._data,
            factors=all_factors,
            covariates=covariates,
            at=at_for_grid if at_for_grid else None,
        )

        # Compute EMMs
        df_placeholder = self._get_inference_df()
        result = compute_emm(
            builder=self._builder,
            grid=grid,
            coef=self._coef,
            vcov=self._vcov,
            df=df_placeholder,
        )

        # Compute proper df
        df = self._compute_emm_df(result.X_ref)
        result = EMMResult(
            grid=result.grid,
            emmeans=result.emmeans,
            se=result.se,
            df=df,
            X_ref=result.X_ref,
            vcov_emm=result.vcov_emm,
        )

        # Handle contrasts if requested
        if contrasts is not None:
            contrast_df = self._compute_contrasts(
                result,
                specs=[var],
                contrast_type=contrasts,
                conf_int=conf_level,
                p_adjust=p_adjust,
                normalize=normalize,
                units=units,
            )
            # Add term column for unified output
            return contrast_df.with_columns(pl.lit(var).alias("term")).select(
                ["term"] + [c for c in contrast_df.columns]
            )

        # Format as mee output
        return self._format_mee_categorical(
            result,
            var,
            by_vars,
            at_values,
            conf_level,
            p_adjust,
            units,
            agg=agg,
            other_factors=other_factors,
        )

    def _mee_categorical_minimal(
        self,
        var: str,
        by_vars: list[str],
        at_values: dict[str, list[Any]],
        agg: bool,
        contrasts: str | dict[str, list | np.ndarray] | None,
        units: str,
        normalize: bool = True,
    ) -> tuple[pl.DataFrame, np.ndarray, np.ndarray | float]:
        """Compute minimal marginal means for a categorical variable.

        Returns minimal DataFrame (term, level, estimate) plus X_ref and df
        for later inference via .infer().

        Returns:
            Tuple of (df_minimal, X_ref, df_values) where:
            - df_minimal: DataFrame with columns term, level, estimate
            - X_ref: Design matrix for bootstrap (boot_mees = boot_coefs @ X_ref.T)
            - df_values: Degrees of freedom (scalar or array for Satterthwaite)
        """
        from bossanova.marginal.emm import compute_emm, EMMResult
        from bossanova.marginal.grid import build_reference_grid

        # Individual-level: not supported in minimal mode (requires full recompute)
        if not agg:
            raise NotImplementedError(
                "Individual-level MEE (agg=False) not yet supported with new API. "
                "Use model.fit().infer() pattern for now."
            )

        # Build reference grid
        factors = [var]
        continuous_by_vars = []
        if by_vars:
            for bv in by_vars:
                if self._classify_variable(bv) == "categorical":
                    factors.append(bv)
                else:
                    continuous_by_vars.append(bv)

        other_factors, covariates = self._get_other_model_variables(factors)
        all_factors = factors + other_factors
        # Add continuous by_vars to covariates (avoiding duplicates)
        covariates_set = set(covariates)
        covariates = list(covariates) + [
            bv for bv in continuous_by_vars if bv not in covariates_set
        ]
        at_for_grid = at_values.copy() if at_values else {}

        grid = build_reference_grid(
            self._data,
            factors=all_factors,
            covariates=covariates,
            at=at_for_grid if at_for_grid else None,
        )

        # Compute EMMs
        df_placeholder = self._get_inference_df()
        result = compute_emm(
            builder=self._builder,
            grid=grid,
            coef=self._coef,
            vcov=self._vcov,
            df=df_placeholder,
        )

        # Compute proper df (Satterthwaite for mixed models)
        df_values = self._compute_emm_df(result.X_ref)
        result = EMMResult(
            grid=result.grid,
            emmeans=result.emmeans,
            se=result.se,
            df=df_values,
            X_ref=result.X_ref,
            vcov_emm=result.vcov_emm,
        )

        # Handle contrasts
        if contrasts is not None:
            return self._mee_contrasts_minimal(result, var, contrasts, normalize, units)

        # Extract estimates (apply data-scale transformation if needed)
        estimates = result.emmeans
        family = self._get_family()
        if units == "data" and family is not None:
            estimates = np.asarray(family.link_inverse(estimates))

        n = len(estimates)
        levels = result.grid[var].to_list()

        # Average over other factors if agg=True
        if agg and other_factors:
            # Group and average - marginalize over other factors
            unique_levels = []
            avg_estimates = []
            avg_X_refs = []
            avg_dfs = []

            # Add row index to track original positions
            grid_with_idx = result.grid.with_row_index("__row_idx__")

            # Get unique combinations of focal var + by_vars
            group_cols = [var] + [bv for bv in by_vars if bv in result.grid.columns]
            for _, group_df in grid_with_idx.group_by(group_cols, maintain_order=True):
                idx = group_df["__row_idx__"].to_numpy()
                # Get the level value for this group (first element has correct level)
                unique_levels.append(group_df[var][0])
                avg_estimates.append(np.mean(estimates[idx]))
                avg_X_refs.append(np.mean(result.X_ref[idx], axis=0))
                # Average df values
                if hasattr(df_values, "__getitem__") and len(df_values) > 1:
                    avg_dfs.append(np.mean(df_values[idx]))
                else:
                    avg_dfs.append(
                        float(df_values)
                        if np.isscalar(df_values)
                        else float(df_values[0])
                    )

            # Build minimal DataFrame
            df_minimal = pl.DataFrame(
                {
                    "term": [var] * len(unique_levels),
                    "level": [str(lv) for lv in unique_levels],
                    "estimate": avg_estimates,
                }
            )

            X_ref_out = np.vstack(avg_X_refs)
            df_out = np.array(avg_dfs)

        else:
            # Build minimal DataFrame
            df_minimal = pl.DataFrame(
                {
                    "term": [var] * n,
                    "level": [str(lv) for lv in levels],
                    "estimate": np.asarray(estimates),
                }
            )

            X_ref_out = result.X_ref
            df_out = (
                df_values
                if isinstance(df_values, np.ndarray)
                else np.full(n, df_values)
            )

        # Add by_var columns if stratified
        if by_vars:
            for by_var in by_vars:
                if by_var in result.grid.columns:
                    if agg and other_factors:
                        # Get unique by_var values matching unique_levels
                        by_vals = [
                            result.grid[by_var][levels.index(lv)]
                            for lv in unique_levels
                        ]
                    else:
                        by_vals = result.grid[by_var].to_list()
                    df_minimal = df_minimal.with_columns(pl.Series(by_var, by_vals))

        return df_minimal, X_ref_out, df_out

    def _mee_contrasts_minimal(
        self,
        result,
        var: str,
        contrast_type: str | dict[str, list | np.ndarray],
        normalize: bool,
        units: str,
    ) -> tuple[pl.DataFrame, np.ndarray, np.ndarray | float]:
        """Compute minimal contrast results.

        Returns minimal DataFrame plus contrast-transformed X_ref for inference.
        """
        from bossanova.marginal.contrasts import build_contrast_matrix

        levels = result.grid[var].to_list()

        # Build contrast matrix
        C = build_contrast_matrix(contrast_type, levels, normalize=normalize)
        n_contrasts = C.shape[0]

        # Validate contrast dimensions
        n_levels = len(levels)
        if C.shape[1] != n_levels:
            raise ValueError(
                f"Contrast vector has {C.shape[1]} coefficients but factor '{var}' "
                f"has {n_levels} levels ({levels}). "
                f"Each contrast must have exactly {n_levels} coefficients."
            )

        # Compute contrast estimates
        contrast_estimates = C @ result.emmeans

        # Transform X_ref for contrasts: contrast_X_ref = C @ X_ref
        contrast_X_ref = C @ result.X_ref

        # Compute df for contrasts (average of contributing df values)
        if isinstance(result.df, np.ndarray):
            # Weighted average based on contrast weights
            contrast_df = np.abs(C) @ result.df / np.sum(np.abs(C), axis=1)
        else:
            contrast_df = np.full(n_contrasts, result.df)

        # Apply data-scale transformation if needed
        family = self._get_family()
        if units == "data" and family is not None:
            contrast_estimates = np.asarray(family.link_inverse(contrast_estimates))

        # Build contrast labels
        contrast_labels = self._build_contrast_labels(contrast_type, levels)

        # Build minimal DataFrame
        df_minimal = pl.DataFrame(
            {
                "term": [var] * n_contrasts,
                "contrast": contrast_labels,
                "estimate": np.asarray(contrast_estimates),
            }
        )

        return df_minimal, contrast_X_ref, contrast_df

    def _build_contrast_labels(
        self,
        contrast_type: str | dict[str, list | np.ndarray],
        levels: list,
    ) -> list[str]:
        """Build human-readable contrast labels matching contrast matrix ordering.

        For pairwise: build_all_pairwise_contrast produces j - i (later - earlier)
        For revpairwise: negated matrix, so i - j (earlier - later)
        For trt.vs.ctrl: level_i - ref (compare each to first)
        """
        if isinstance(contrast_type, dict):
            return list(contrast_type.keys())
        elif contrast_type == "pairwise":
            # Matrix has j - i order (later level - earlier level)
            labels = []
            for i, lv1 in enumerate(levels):
                for lv2 in levels[i + 1 :]:
                    labels.append(f"{lv2} - {lv1}")  # lv2 is later
            return labels
        elif contrast_type == "revpairwise":
            # Matrix is negated, so i - j order (earlier - later)
            labels = []
            for i, lv1 in enumerate(levels):
                for lv2 in levels[i + 1 :]:
                    labels.append(f"{lv1} - {lv2}")  # lv1 is earlier
            return labels
        elif contrast_type in ("trt.vs.ctrl", "treatment"):
            ref = levels[0]
            return [f"{lv} - {ref}" for lv in levels[1:]]
        else:
            raise ValueError(f"Unknown contrast type: {contrast_type}")

    def _mee_categorical_individual(
        self,
        var: str,
        by_vars: list[str],
        at_values: dict[str, list[Any]],
        conf_level: float,
        p_adjust: str,  # noqa: ARG002
        units: str,
    ) -> pl.DataFrame:
        """Compute individual-level counterfactual marginal means.

        For each observation, computes the predicted value at each level
        of the focal variable while holding all other variables at their
        observed values. This matches R's marginaleffects::comparisons()
        behavior.

        Returns one row per observation per focal level.
        """
        from scipy import stats as scipy_stats

        # Get focal variable levels (sorted for consistent ordering)
        col = self._data[var]
        if isinstance(col.dtype, pl.Enum):
            levels = col.dtype.categories.to_list()
        else:
            levels = sorted(col.unique().to_list())

        n_obs = len(self._data)
        df_resid = self._get_inference_df()

        # For each level, create counterfactual data and predict
        all_emmeans = np.zeros((len(levels), n_obs))
        all_se = np.zeros((len(levels), n_obs))

        for i, level in enumerate(levels):
            # Create counterfactual: all rows with focal variable set to this level
            if isinstance(col.dtype, pl.Enum):
                cf_data = self._data.with_columns(
                    pl.lit(str(level)).cast(col.dtype).alias(var)
                )
            else:
                cf_data = self._data.with_columns(pl.lit(level).alias(var))

            # Build design matrix for counterfactual data
            X_cf = self._builder.evaluate_new_data(cf_data)

            # Point predictions: X @ β
            all_emmeans[i] = X_cf @ self._coef

            # SE: sqrt(diag(X @ V @ X.T)) without forming full n×n matrix
            # = sqrt(row_sums((X @ V) * X))
            all_se[i] = np.sqrt(np.sum((X_cf @ self._vcov) * X_cf, axis=1))

        # Determine scale
        family = self._get_family()
        if family is None:
            scale_label = "identity"
        elif units == "data":
            scale_label = "response"
        else:
            scale_label = family.link_name

        # Build output: one row per observation per level
        parts = []
        for i, level in enumerate(levels):
            df_values = (
                np.full(n_obs, df_resid)
                if not isinstance(df_resid, np.ndarray)
                else df_resid
            )
            t_crit = scipy_stats.t.ppf((1 + conf_level) / 2, df_values)

            estimates = all_emmeans[i]
            se = all_se[i]
            ci_lower = estimates - t_crit * se
            ci_upper = estimates + t_crit * se

            # Apply response scale transformation if needed
            if units == "data" and family is not None:
                estimates = np.asarray(family.link_inverse(estimates))
                ci_lower = np.asarray(family.link_inverse(ci_lower))
                ci_upper = np.asarray(family.link_inverse(ci_upper))

            part = pl.DataFrame(
                {
                    "rowid": np.arange(n_obs),
                    "term": [var] * n_obs,
                    "level": [str(level)] * n_obs,
                    "estimate": np.asarray(estimates),
                    "se": np.asarray(se),
                    "df": df_values,
                    "ci_lower": np.asarray(ci_lower),
                    "ci_upper": np.asarray(ci_upper),
                    "scale": [scale_label] * n_obs,
                }
            )
            parts.append(part)

        result = pl.concat(parts)

        # Add by_var values from original data (repeated for each level)
        if by_vars:
            for bv in by_vars:
                if bv in self._data.columns:
                    orig_values = self._data[bv].to_list()
                    result = result.with_columns(
                        pl.Series(bv, orig_values * len(levels))
                    )

        return result

    def _format_mee_categorical(
        self,
        result,
        var: str,
        by_vars: list[str],
        at_values: dict[str, list[Any]],
        conf_level: float,
        p_adjust: str,  # noqa: ARG002 - kept for API compatibility
        units: str,
        *,
        agg: bool = True,
        other_factors: list[str] | None = None,
    ) -> pl.DataFrame:
        """Format EMM result as mee DataFrame.

        Note: Does not include t_value or p_value columns. Testing H0: mean = 0
        is not meaningful for marginal means. Use contrasts to get p-values
        for meaningful comparisons.

        Args:
            agg: If True (default), average EMMs over other factors (marginalize).
                If False, return raw EMMs at each grid point.
            other_factors: List of other factor variables in the model that
                aren't focal or by_vars. Used when agg=False to include in output.
        """
        from scipy import stats as scipy_stats

        other_factors = other_factors or []
        n = len(result.emmeans)
        levels = result.grid[var].to_list()

        # Get df (scalar or array)
        if isinstance(result.df, np.ndarray):
            df_values = result.df
        else:
            df_values = np.full(n, result.df)

        # Confidence intervals
        t_crit = scipy_stats.t.ppf((1 + conf_level) / 2, df_values)
        ci_lower = result.emmeans - t_crit * result.se
        ci_upper = result.emmeans + t_crit * result.se

        # Apply data-scale transformation if needed
        estimates = result.emmeans
        family = self._get_family()
        if units == "data" and family is not None:
            estimates = np.asarray(family.link_inverse(estimates))
            ci_lower = np.asarray(family.link_inverse(ci_lower))
            ci_upper = np.asarray(family.link_inverse(ci_upper))

        # Determine scale label for output
        if family is None:
            scale_label = "identity"  # Linear models
        elif units == "data":
            scale_label = "response"  # Probability for binomial, counts for poisson
        else:
            scale_label = family.link_name  # "logit", "log", etc.

        # Build DataFrame (no t_value/p_value - testing mean=0 is meaningless)
        df_out = pl.DataFrame(
            {
                "term": [var] * n,
                "level": [str(lv) for lv in levels],
                "estimate": np.asarray(estimates),
                "se": np.asarray(result.se),
                "df": df_values,
                "ci_lower": np.asarray(ci_lower),
                "ci_upper": np.asarray(ci_upper),
                "scale": [scale_label] * n,
            }
        )

        # Add by columns if stratified
        if by_vars:
            for by_var in by_vars:
                if by_var in result.grid.columns:
                    df_out = df_out.with_columns(
                        pl.Series(by_var, result.grid[by_var].to_list())
                    )

        # Add other factor columns when agg=False
        if not agg and other_factors:
            for of in other_factors:
                if of in result.grid.columns:
                    df_out = df_out.with_columns(
                        pl.Series(of, result.grid[of].to_list())
                    )

        # Add covariate columns from at_values (from bracket syntax like Income[50])
        # Always include these so users can see conditioning values used
        if at_values:
            for cov, vals in at_values.items():
                if cov in result.grid.columns and cov not in by_vars:
                    df_out = df_out.with_columns(
                        pl.Series(cov, result.grid[cov].to_list())
                    )

        # When agg=True, average EMMs over other factors
        if agg and other_factors:
            # Group by focal variable (and by_vars if present) and average
            # Keep scale column as first value (it's constant within groups)
            group_cols = ["term", "level"] + by_vars
            agg_cols = ["estimate", "se", "df", "ci_lower", "ci_upper"]
            df_out = df_out.group_by(group_cols, maintain_order=True).agg(
                [pl.col(c).mean() for c in agg_cols] + [pl.col("scale").first()]
            )

        # Reorder columns: conditioning vars first, then term/level, then stats, scale last
        base_cols = [
            "term",
            "level",
            "estimate",
            "se",
            "df",
            "ci_lower",
            "ci_upper",
            "scale",
        ]
        conditioning_cols = [c for c in df_out.columns if c not in base_cols]
        ordered_cols = conditioning_cols + [c for c in base_cols if c in df_out.columns]
        df_out = df_out.select(ordered_cols)

        return df_out

    def _mee_continuous_at_values(
        self,
        var: str,
        values: list[Any],
        by_vars: list[str],
        at_values: dict[str, list[Any]],
        conf_level: float,
        p_adjust: str,  # noqa: ARG002 - kept for API compatibility
        units: str,
    ) -> pl.DataFrame:
        """Compute EMMs for a continuous variable at explicit values.

        When a continuous focal variable has explicit values specified
        (e.g., "Days[0, 3, 6, 9]"), we compute predicted values at those
        points rather than slopes/derivatives.

        Args:
            var: The continuous variable name.
            values: List of values to compute EMMs at.
            by_vars: Stratification variables.
            at_values: Additional at-values for other variables.
            conf_level: Confidence level for intervals.
            p_adjust: P-value adjustment method.
            units: "link" or "data" scale.

        Returns:
            DataFrame with EMMs at each specified value.

        Note:
            Does not include t_value or p_value columns. Testing H0: prediction = 0
            is not meaningful. Use contrasts to get p-values for comparisons.
        """
        from scipy import stats as scipy_stats

        from bossanova.marginal.emm import EMMResult, compute_emm
        from bossanova.marginal.grid import build_reference_grid

        # Get other model variables for proper grid construction
        other_factors, covariates = self._get_other_model_variables([var])

        # Build factors list - include by_vars if categorical
        factors_for_grid = list(other_factors)
        if by_vars:
            cat_by_vars = [
                v for v in by_vars if self._classify_variable(v) == "categorical"
            ]
            factors_for_grid.extend(cat_by_vars)

        # Build at_values with the focal var's explicit values
        # The focal var will be treated like a factor with these specific values
        at_for_grid = at_values.copy() if at_values else {}
        at_for_grid[var] = values

        # Build reference grid - the focal var values will be in the grid
        # We need to include the focal var in the grid expansion
        # Since it's continuous, we pass it through 'at' to set specific values
        grid = build_reference_grid(
            self._data,
            factors=factors_for_grid,
            covariates=[c for c in covariates if c != var] + [var],
            at=at_for_grid,
        )

        # If grid doesn't have our focal var at all values, expand it
        # This can happen if build_reference_grid sets to mean instead
        if var in grid.columns:
            unique_vals = grid[var].unique().to_list()
            if len(unique_vals) != len(values):
                # Expand grid to include all focal values
                grid_expanded = []
                base_grid = grid.drop(var).unique()
                for val in values:
                    expanded = base_grid.with_columns(pl.lit(val).alias(var))
                    grid_expanded.append(expanded)
                grid = pl.concat(grid_expanded)
        else:
            # Add focal var column if missing
            grid_expanded = []
            for val in values:
                expanded = grid.with_columns(pl.lit(val).alias(var))
                grid_expanded.append(expanded)
            grid = pl.concat(grid_expanded)

        # Compute EMMs
        df_placeholder = self._get_inference_df()
        result = compute_emm(
            builder=self._builder,
            grid=grid,
            coef=self._coef,
            vcov=self._vcov,
            df=df_placeholder,
        )

        # Compute proper df for each row
        df_proper = self._compute_emm_df(result.X_ref)
        result = EMMResult(
            grid=result.grid,
            emmeans=result.emmeans,
            se=result.se,
            df=df_proper,
            X_ref=result.X_ref,
            vcov_emm=result.vcov_emm,
        )

        # Format output - similar to categorical but with focal var as "term"
        n = len(result.emmeans)

        # Get df values
        if isinstance(result.df, np.ndarray):
            df_values = result.df
        else:
            df_values = np.full(n, result.df)

        # Confidence intervals (no t_value/p_value - testing prediction=0 is meaningless)
        t_crit = scipy_stats.t.ppf((1 + conf_level) / 2, df_values)
        ci_lower = result.emmeans - t_crit * result.se
        ci_upper = result.emmeans + t_crit * result.se

        # Apply data-scale transformation if needed
        estimates = result.emmeans
        family = self._get_family()
        if units == "data" and family is not None:
            estimates = np.asarray(family.link_inverse(estimates))
            ci_lower = np.asarray(family.link_inverse(ci_lower))
            ci_upper = np.asarray(family.link_inverse(ci_upper))

        # Get levels from the grid's focal var column
        levels = result.grid[var].to_list()

        # Determine scale label for output
        if family is None:
            scale_label = "identity"  # Linear models
        elif units == "data":
            scale_label = "response"  # Probability for binomial, counts for poisson
        else:
            scale_label = family.link_name  # "logit", "log", etc.

        # Build DataFrame
        df_out = pl.DataFrame(
            {
                "term": [var] * n,
                "level": [str(lv) for lv in levels],
                "estimate": np.asarray(estimates),
                "se": np.asarray(result.se),
                "df": df_values,
                "ci_lower": np.asarray(ci_lower),
                "ci_upper": np.asarray(ci_upper),
                "scale": [scale_label] * n,
            }
        )

        # Add by columns if stratified
        if by_vars:
            for by_var in by_vars:
                if by_var in result.grid.columns:
                    df_out = df_out.with_columns(
                        pl.Series(by_var, result.grid[by_var].to_list())
                    )

        # Add covariate columns from at_values (from bracket syntax)
        # Always include these so users can see conditioning values used
        if at_values:
            for cov, vals in at_values.items():
                if cov in result.grid.columns and cov not in by_vars:
                    df_out = df_out.with_columns(
                        pl.Series(cov, result.grid[cov].to_list())
                    )

        # Reorder columns: conditioning vars first, then term/level, then stats, scale last
        base_cols = [
            "term",
            "level",
            "estimate",
            "se",
            "df",
            "ci_lower",
            "ci_upper",
            "scale",
        ]
        conditioning_cols = [c for c in df_out.columns if c not in base_cols]
        ordered_cols = conditioning_cols + [c for c in base_cols if c in df_out.columns]
        df_out = df_out.select(ordered_cols)

        return df_out

    def _mee_continuous(
        self,
        var: str,
        by_vars: list[str],
        at_values: dict[str, list[Any]],
        agg: bool,
        conf_level: float,
        p_adjust: str,
        units: str,
    ) -> pl.DataFrame:
        """Compute marginal effects (slopes) for a continuous variable."""
        from scipy import stats as scipy_stats

        from bossanova.marginal.grid import build_reference_grid
        from bossanova.marginal.slopes import compute_slopes, average_slopes
        from bossanova.ops.inference import adjust_pvalues

        # Get all model factors and covariates (needed for proper grid)
        other_factors, covariates = self._get_other_model_variables([var])

        # Build reference grid including all factors
        # This ensures the design matrix can be built correctly
        if by_vars:
            # Include by_vars in factors
            cat_by_vars = [
                v for v in by_vars if self._classify_variable(v) == "categorical"
            ]
            all_factors = list(set(cat_by_vars + other_factors))
        else:
            all_factors = other_factors

        if all_factors:
            grid = build_reference_grid(
                self._data,
                factors=all_factors,
                covariates=[c for c in covariates if c != var],
                at=at_values if at_values else None,
            )
        else:
            # No factors - minimal grid with covariates at their means
            grid = build_reference_grid(
                self._data,
                factors=[],
                covariates=[c for c in covariates if c != var],
                at=at_values if at_values else None,
            )

        # Compute slopes
        slope_result = compute_slopes(
            builder=self._builder,
            grid=grid,
            var=var,
            coef=self._coef,
            vcov=self._vcov,
            df=self._get_inference_df(),
            data=self._data,
        )

        # Aggregate slopes based on agg and by_vars
        cat_by_vars = (
            [v for v in by_vars if self._classify_variable(v) == "categorical"]
            if by_vars
            else []
        )

        if agg and cat_by_vars and len(slope_result.slopes) > 1:
            # Group by by_vars, average over other_factors within each group
            slope_df = slope_result.grid.select(cat_by_vars).with_columns(
                pl.Series("_slope", slope_result.slopes),
                pl.Series("_se", slope_result.se),
                pl.Series(
                    "_df",
                    slope_result.df
                    if isinstance(slope_result.df, np.ndarray)
                    else np.full(len(slope_result.slopes), slope_result.df),
                ),
            )
            grouped = slope_df.group_by(cat_by_vars, maintain_order=True).agg(
                pl.col("_slope").mean(),
                pl.col("_se").mean(),
                pl.col("_df").mean(),
            )
            slopes = grouped["_slope"].to_numpy()
            ses = grouped["_se"].to_numpy()
            dfs = grouped["_df"].to_numpy()
            levels = [
                "_".join(str(row[v]) for v in cat_by_vars)
                for row in grouped.select(cat_by_vars).iter_rows(named=True)
            ]
            # Build a grid with one row per by_var combination for delta method
            grid_for_output = grouped.select(cat_by_vars)
            # Add covariate means for delta method grid evaluation
            for c in [c for c in covariates if c != var]:
                grid_for_output = grid_for_output.with_columns(
                    pl.lit(self._data[c].mean()).alias(c)
                )
            # Add focal var at its mean for delta method
            grid_for_output = grid_for_output.with_columns(
                pl.lit(self._data[var].mean()).alias(var)
            )
        elif agg and len(slope_result.slopes) > 1:
            avg = average_slopes(slope_result)
            slopes = np.array([avg["slope"]])
            ses = np.array([avg["se"]])
            dfs = np.array([avg["df"]])
            levels = ["slope"]
            grid_for_output = None
        else:
            slopes = slope_result.slopes
            ses = slope_result.se
            if isinstance(slope_result.df, np.ndarray):
                dfs = slope_result.df
            else:
                dfs = np.full(len(slopes), slope_result.df)

            # Determine level labels
            if cat_by_vars and all(v in slope_result.grid.columns for v in cat_by_vars):
                levels = [
                    "_".join(str(row[v]) for v in cat_by_vars)
                    for row in slope_result.grid.select(cat_by_vars).iter_rows(
                        named=True
                    )
                ]
            else:
                levels = ["slope"] * len(slopes)
            grid_for_output = slope_result.grid

        n = len(slopes)

        # Apply data-scale transformation for GLM if needed
        # Delta method: dmu/dx = deta/dx / link_deriv(mu)
        family = self._get_family()
        if units == "data" and family is not None:
            # Get predicted values at grid points (on link scale -> mu scale)
            if grid_for_output is not None:
                X_grid = self._builder.evaluate_new_data(grid_for_output)
            else:
                # For aggregated slopes, use mean grid point
                X_grid = self._builder.evaluate_new_data(slope_result.grid)
                # Average the X matrix rows if we aggregated
                if agg and len(slope_result.slopes) > 1:
                    X_grid = X_grid.mean(axis=0, keepdims=True)

            eta = X_grid @ self._coef
            mu = np.asarray(family.link_inverse(eta))

            # Delta method: transform slopes from link to data scale
            # link_deriv gives deta/dmu, so dmu/deta = 1/link_deriv
            link_deriv_vals = np.asarray(family.link_deriv(mu)).flatten()
            # Avoid division by zero
            link_deriv_vals = np.where(
                np.abs(link_deriv_vals) < 1e-10, 1e-10, link_deriv_vals
            )

            # Transform slopes and SEs
            slopes = slopes / link_deriv_vals
            ses = ses / np.abs(link_deriv_vals)

        # Compute t-values and p-values (always on transformed scale)
        t_values = slopes / ses
        p_values = 2 * (1 - scipy_stats.t.cdf(np.abs(t_values), dfs))

        # Confidence intervals (on transformed scale)
        t_crit = scipy_stats.t.ppf((1 + conf_level) / 2, dfs)
        ci_lower = slopes - t_crit * ses
        ci_upper = slopes + t_crit * ses

        # Determine scale label for output
        if family is None:
            scale_label = "identity"  # Linear models (slopes are on original scale)
        elif units == "data":
            scale_label = "response"  # Marginal effects on probability/count scale
        else:
            scale_label = (
                family.link_name
            )  # "logit", "log", etc. (slopes on link scale)

        # Build DataFrame
        df_out = pl.DataFrame(
            {
                "term": [var] * n,
                "level": levels,
                "estimate": slopes,
                "se": ses,
                "df": dfs,
                "t_value": t_values,
                "p_value": p_values,
                "ci_lower": ci_lower,
                "ci_upper": ci_upper,
                "scale": [scale_label] * n,
            }
        )

        # Add by columns if stratified
        if cat_by_vars and grid_for_output is not None:
            for by_var in cat_by_vars:
                if by_var in grid_for_output.columns:
                    df_out = df_out.with_columns(
                        pl.Series(by_var, grid_for_output[by_var].to_list())
                    )

        # Add covariate columns from at_values (from bracket syntax)
        # Always include these so users can see conditioning values used
        if at_values and grid_for_output is not None:
            for cov, vals in at_values.items():
                if cov in grid_for_output.columns and cov not in (by_vars or []):
                    df_out = df_out.with_columns(
                        pl.Series(cov, grid_for_output[cov].to_list())
                    )

        # P-value adjustment
        if p_adjust != "none":
            adjusted = adjust_pvalues(p_values, method=p_adjust)
            df_out = df_out.with_columns(pl.Series("p_adjusted", adjusted))

        # Reorder columns: conditioning vars first, then term/level, then stats, scale last
        base_cols = [
            "term",
            "level",
            "estimate",
            "se",
            "df",
            "t_value",
            "p_value",
            "ci_lower",
            "ci_upper",
            "p_adjusted",
            "scale",
        ]
        conditioning_cols = [c for c in df_out.columns if c not in base_cols]
        ordered_cols = conditioning_cols + [c for c in base_cols if c in df_out.columns]
        df_out = df_out.select(ordered_cols)

        return df_out

    def _mee_continuous_minimal(
        self,
        var: str,
        by_vars: list[str],
        at_values: dict[str, list[Any]],
        agg: bool,
        units: str,
    ) -> tuple[pl.DataFrame, np.ndarray, np.ndarray | float]:
        """Compute minimal marginal effects (slopes) for a continuous variable.

        Returns minimal DataFrame plus L_diff and df for later inference.

        Returns:
            Tuple of (df_minimal, L_diff, df_values) where:
            - df_minimal: DataFrame with columns term, level, estimate
            - L_diff: Finite difference operator (boot_slopes = boot_coefs @ L_diff.T)
            - df_values: Degrees of freedom
        """
        from bossanova.marginal.grid import build_reference_grid
        from bossanova.marginal.slopes import compute_slopes

        # Get all model factors and covariates
        other_factors, covariates = self._get_other_model_variables([var])

        # Build reference grid
        if by_vars:
            cat_by_vars = [
                v for v in by_vars if self._classify_variable(v) == "categorical"
            ]
            all_factors = list(set(cat_by_vars + other_factors))
        else:
            all_factors = other_factors
            cat_by_vars = []

        if all_factors:
            grid = build_reference_grid(
                self._data,
                factors=all_factors,
                covariates=[c for c in covariates if c != var],
                at=at_values if at_values else None,
            )
        else:
            grid = build_reference_grid(
                self._data,
                factors=[],
                covariates=[c for c in covariates if c != var],
                at=at_values if at_values else None,
            )

        # Compute slopes (includes L_diff operator)
        slope_result = compute_slopes(
            builder=self._builder,
            grid=grid,
            var=var,
            coef=self._coef,
            vcov=self._vcov,
            df=self._get_inference_df(),
            data=self._data,
        )

        slopes = slope_result.slopes
        L_diff = slope_result.L_diff
        dfs = slope_result.df

        # Handle aggregation
        if agg and cat_by_vars and len(slopes) > 1:
            # Group and average
            slope_df = slope_result.grid.select(cat_by_vars).with_columns(
                pl.Series("_slope", slopes),
                pl.Series("_idx", list(range(len(slopes)))),
            )
            grouped = slope_df.group_by(cat_by_vars, maintain_order=True).agg(
                pl.col("_slope").mean(),
                pl.col("_idx").first(),  # Use first index for L_diff row
            )

            slopes = grouped["_slope"].to_numpy()
            indices = grouped["_idx"].to_numpy()
            L_diff = L_diff[indices]
            dfs = (
                dfs[indices]
                if isinstance(dfs, np.ndarray)
                else np.full(len(slopes), dfs)
            )

            n = len(slopes)
            levels = [
                f"{var}|{','.join(str(v) for v in row)}"
                for row in grouped.select(cat_by_vars).iter_rows()
            ]
            grid_for_by = grouped.select(cat_by_vars)
        elif agg and len(slopes) > 1 and not cat_by_vars:
            # Average all slopes
            slopes = np.array([np.mean(slopes)])
            L_diff = np.mean(L_diff, axis=0, keepdims=True)
            dfs = (
                np.array([np.mean(dfs)])
                if isinstance(dfs, np.ndarray)
                else np.array([dfs])
            )
            n = 1
            levels = ["slope"]
            grid_for_by = None
        else:
            n = len(slopes)
            levels = ["slope"] * n
            dfs = dfs if isinstance(dfs, np.ndarray) else np.full(n, dfs)
            grid_for_by = slope_result.grid if cat_by_vars else None

        # Apply data-scale transformation if needed
        family = self._get_family()
        if units == "data" and family is not None:
            # Need to compute mu for delta method transformation
            grid_for_transform = slope_result.grid
            X_grid = self._builder.evaluate_new_data(grid_for_transform)
            eta = X_grid @ self._coef
            mu = np.asarray(family.link_inverse(eta))
            link_deriv_vals = np.asarray(family.link_deriv(mu)).flatten()
            link_deriv_vals = np.where(
                np.abs(link_deriv_vals) < 1e-10, 1e-10, link_deriv_vals
            )

            # For aggregated case, use mean transformation
            if agg and len(link_deriv_vals) > 1:
                if cat_by_vars:
                    # Group and average
                    transform_df = slope_result.grid.select(cat_by_vars).with_columns(
                        pl.Series("_deriv", link_deriv_vals),
                    )
                    grouped_deriv = transform_df.group_by(
                        cat_by_vars, maintain_order=True
                    ).agg(
                        pl.col("_deriv").mean(),
                    )
                    link_deriv_vals = grouped_deriv["_deriv"].to_numpy()
                else:
                    link_deriv_vals = np.array([np.mean(link_deriv_vals)])

            slopes = slopes / link_deriv_vals

        # Build minimal DataFrame
        df_minimal = pl.DataFrame(
            {
                "term": [var] * n,
                "level": levels,
                "estimate": np.asarray(slopes),
            }
        )

        # Add by_var columns if stratified
        if grid_for_by is not None and cat_by_vars:
            for by_var in cat_by_vars:
                if by_var in grid_for_by.columns:
                    df_minimal = df_minimal.with_columns(
                        pl.Series(by_var, grid_for_by[by_var].to_list())
                    )

        return df_minimal, L_diff, dfs

    def _mee_continuous_at_values_minimal(
        self,
        var: str,
        values: list[Any],
        by_vars: list[str],
        at_values: dict[str, list[Any]],
        units: str,
    ) -> tuple[pl.DataFrame, np.ndarray, np.ndarray | float]:
        """Compute minimal EMMs at explicit continuous variable values.

        Returns minimal DataFrame plus X_ref and df for later inference.
        """
        from bossanova.marginal.emm import compute_emm, EMMResult
        from bossanova.marginal.grid import build_reference_grid

        # Build grid with explicit values for the continuous focal variable
        # Separate by_vars into categorical and continuous
        cat_by_vars = []
        cont_by_vars = []
        if by_vars:
            for bv in by_vars:
                if self._classify_variable(bv) == "categorical":
                    cat_by_vars.append(bv)
                else:
                    cont_by_vars.append(bv)

        # Get other model variables
        other_factors, covariates = self._get_other_model_variables([var])
        all_factors = cat_by_vars + other_factors

        # Build reference grid
        at_for_grid = at_values.copy() if at_values else {}
        at_for_grid[var] = values  # Set explicit values for focal variable

        # Build grid covariates: exclude cont_by_vars (which get explicit values),
        # but include var since it has explicit values and needs a column
        grid_covariates = [c for c in covariates if c not in cont_by_vars]
        if var not in grid_covariates:
            grid_covariates.append(var)  # Focal var with explicit values

        grid = build_reference_grid(
            self._data,
            factors=all_factors if all_factors else [],
            covariates=grid_covariates,
            at=at_for_grid,
        )

        # Compute EMMs at these grid points
        df_placeholder = self._get_inference_df()
        result = compute_emm(
            builder=self._builder,
            grid=grid,
            coef=self._coef,
            vcov=self._vcov,
            df=df_placeholder,
        )

        # Compute proper df
        df_values = self._compute_emm_df(result.X_ref)
        result = EMMResult(
            grid=result.grid,
            emmeans=result.emmeans,
            se=result.se,
            df=df_values,
            X_ref=result.X_ref,
            vcov_emm=result.vcov_emm,
        )

        # Extract estimates
        estimates = result.emmeans
        family = self._get_family()
        if units == "data" and family is not None:
            estimates = np.asarray(family.link_inverse(estimates))

        n = len(estimates)
        levels = [str(v) for v in result.grid[var].to_list()]

        # Build minimal DataFrame
        df_minimal = pl.DataFrame(
            {
                "term": [var] * n,
                "level": levels,
                "estimate": np.asarray(estimates),
            }
        )

        # Add by_var columns
        if cat_by_vars:
            for by_var in cat_by_vars:
                if by_var in result.grid.columns:
                    df_minimal = df_minimal.with_columns(
                        pl.Series(by_var, result.grid[by_var].to_list())
                    )

        df_out = (
            df_values if isinstance(df_values, np.ndarray) else np.full(n, df_values)
        )

        return df_minimal, result.X_ref, df_out

    def _compute_contrasts(
        self,
        emm_result,
        specs: list[str],
        contrast_type: str | dict[str, list | np.ndarray],
        conf_int: float = 0.95,
        p_adjust: str = "none",
        normalize: bool = True,
        units: str = "link",
    ) -> pl.DataFrame:
        """Compute contrasts from EMM results.

        Args:
            emm_result: EMMResult from compute_emm().
            specs: Variables the EMMs are computed for.
            contrast_type: Type of contrasts. Either a string
                ("pairwise", "revpairwise", "trt.vs.ctrl") or a dict
                of custom contrasts {"name": [coefficients]}.
            conf_int: Confidence level for intervals.
            p_adjust: P-value adjustment method.
            normalize: If True, normalize custom contrast vectors by their L2 norm.
            units: Scale for output. "link" (default) returns log-odds/log
                differences. "data" returns ratios (odds ratios for logit,
                rate ratios for log link).

        Returns:
            DataFrame with contrast results.
        """
        from bossanova.marginal.contrasts import (
            build_all_pairwise_contrast,
            build_pairwise_contrast,
            get_contrast_labels,
        )
        from bossanova.marginal.emm import (
            compute_emm_contrasts,
            format_contrast_table,
        )

        n_emms = len(emm_result.emmeans)

        # Handle custom contrast dict
        if isinstance(contrast_type, dict):
            # Build contrast matrix from user-specified vectors
            labels = list(contrast_type.keys())
            contrast_vectors = list(contrast_type.values())

            # Build contrast matrix - each row is one contrast
            C = np.zeros((len(labels), n_emms))
            for i, vec in enumerate(contrast_vectors):
                arr = np.asarray(vec, dtype=np.float64)
                if arr.shape[0] != n_emms:
                    raise ValueError(
                        f"Contrast '{labels[i]}' has {arr.shape[0]} coefficients "
                        f"but there are {n_emms} EMM levels"
                    )
                if normalize:
                    norm = np.linalg.norm(arr)
                    if norm > 0:
                        arr = arr / norm
                C[i] = arr

            # Compute contrasts
            contrast_result = compute_emm_contrasts(
                emm_result, C, self._coef, self._vcov
            )

            # Format the contrast table (on link scale)
            result_df = format_contrast_table(
                contrast_labels=labels,
                estimates=contrast_result.estimates,
                se=contrast_result.se,
                df=emm_result.df,
                conf_int=conf_int,
                p_adjust=p_adjust,
            )

            # Transform to ratio scale for GLM if requested
            # Note: t-values and p-values stay on link scale (matching emmeans)
            family = self._get_family()
            if units == "data" and family is not None:
                result_df = result_df.with_columns(
                    [
                        np.exp(pl.col("estimate")).alias("estimate"),
                        (np.exp(pl.col("estimate")) * pl.col("se")).alias("se"),
                        np.exp(pl.col("ci_lower")).alias("ci_lower"),
                        np.exp(pl.col("ci_upper")).alias("ci_upper"),
                    ]
                )

            return result_df

        # Handle string contrast types
        if contrast_type == "pairwise":
            # All pairwise comparisons (B-A, C-A, C-B, etc.)
            C = build_all_pairwise_contrast(n_emms)
            label_type = "all_pairwise"
        elif contrast_type == "revpairwise":
            # Reversed pairwise (A-B, A-C, B-C, etc.)
            C = -build_all_pairwise_contrast(n_emms)
            label_type = "all_pairwise"  # Will negate labels below
        elif contrast_type == "trt.vs.ctrl":
            # Treatment vs control (each level vs first level)
            C = build_pairwise_contrast(n_emms)
            label_type = "pairwise"
        else:
            raise ValueError(f"Unknown contrast type: {contrast_type}")

        # Compute contrasts
        contrast_result = compute_emm_contrasts(emm_result, C, self._coef, self._vcov)

        # Get level labels from the grid in the order they appear
        # This order must match the EMM order for correct contrast labeling
        if len(specs) == 1:
            # For single factor, get levels in order from grid rows
            levels = emm_result.grid[specs[0]].to_list()
        else:
            # For multi-factor specs, combine level labels from each row
            levels = [
                "_".join(str(v) for v in row.values())
                for row in emm_result.grid.select(specs).iter_rows(named=True)
            ]

        # Generate contrast labels
        labels = get_contrast_labels(levels, label_type)

        # For revpairwise, reverse the labels (A-B instead of B-A)
        if contrast_type == "revpairwise":
            labels = [" - ".join(reversed(label.split(" - "))) for label in labels]

        # Format the contrast table (on link scale)
        result_df = format_contrast_table(
            contrast_labels=labels,
            estimates=contrast_result.estimates,
            se=contrast_result.se,
            df=emm_result.df,
            conf_int=conf_int,
            p_adjust=p_adjust,
        )

        # Transform to ratio scale for GLM if requested
        # Note: t-values and p-values stay on link scale (matching emmeans)
        family = self._get_family()
        if units == "data" and family is not None:
            # Update labels to indicate ratio (e.g., "B / A" instead of "B - A")
            result_df = result_df.with_columns(
                pl.col("contrast").str.replace(" - ", " / ").alias("contrast")
            )
            result_df = result_df.with_columns(
                [
                    np.exp(pl.col("estimate")).alias("estimate"),
                    (np.exp(pl.col("estimate")) * pl.col("se")).alias("se"),
                    np.exp(pl.col("ci_lower")).alias("ci_lower"),
                    np.exp(pl.col("ci_upper")).alias("ci_upper"),
                ]
            )

        return result_df

    def _get_other_model_variables(
        self, specs: list[str]
    ) -> tuple[list[str], list[str]]:
        """Get other model variables not in specs.

        Extracts all variables from model terms (including interaction terms)
        and classifies them as either factors or numeric covariates.

        This is used by emmeans() to ensure the reference grid includes all
        variables needed by evaluate_new_data() to compute predictions.

        Args:
            specs: Variable names to exclude (the specs being estimated).

        Returns:
            Tuple of (factors, covariates) where:
            - factors: Categorical/Enum variables from model
            - covariates: Numeric variables from model
        """
        exclude_set = set(specs)
        factors_found: set[str] = set()
        covariates_found: set[str] = set()

        # Get variables that are used as factors in the formula (e.g., via factor())
        # This is tracked by the builder, regardless of underlying data type
        formula_factors = set(getattr(self._builder, "_factors", {}).keys())

        for term_name in self._dm.X_labels:
            if term_name.lower() == "intercept":
                continue

            # Split interaction terms on ':' to get components
            # e.g., "center(wt):cyl[6]" -> ["center(wt)", "cyl[6]"]
            components = term_name.split(":")

            for component in components:
                # Extract base variable name from component
                var_name = self._extract_var_name(component)
                if not var_name or var_name in exclude_set:
                    continue
                if var_name not in self._data.columns:
                    continue

                # Classify as factor or numeric covariate
                # Check formula factors first (handles factor() wrapper on numeric cols)
                if var_name in formula_factors:
                    factors_found.add(var_name)
                else:
                    dtype = self._data[var_name].dtype
                    if dtype in (pl.Enum, pl.Categorical, pl.String):
                        factors_found.add(var_name)
                    elif dtype in (
                        pl.Float32,
                        pl.Float64,
                        pl.Int8,
                        pl.Int16,
                        pl.Int32,
                        pl.Int64,
                    ):
                        covariates_found.add(var_name)

        return list(factors_found), list(covariates_found)

    def _get_numeric_covariates(self, exclude_factors: list[str]) -> list[str]:
        """Get numeric covariate names from model terms.

        Returns column names that are numeric and not in the excluded factors.
        Used by emmeans() to identify covariates to hold at representative values.

        Note: This method is kept for backwards compatibility. New code should
        use _get_other_model_variables() which also returns factors.

        Args:
            exclude_factors: Factor names to exclude from result.

        Returns:
            List of numeric covariate column names.
        """
        _, covariates = self._get_other_model_variables(exclude_factors)
        return covariates

    def _extract_var_name(self, term_name: str) -> str | None:
        """Extract base variable name from term name.

        Strips function wrappers like factor(), center(), scale() and
        factor level notation like cyl[6] or group[B].

        Args:
            term_name: Term name like "factor(group)", "center(x)", or "cyl[6]".

        Returns:
            Base variable name, or None if not extractable.
        """
        if not term_name:
            return None

        # Handle function-wrapped names: center(x), scale(y), factor(group)
        if "(" in term_name and ")" in term_name:
            start = term_name.rfind("(") + 1
            end = term_name.find(",") if "," in term_name else term_name.find(")")
            inner = term_name[start:end].strip()
            # Recursively handle nested cases like center(x)[level]
            return self._extract_var_name(inner)

        # Handle factor level notation: cyl[6], group[B], treatment[drug]
        if "[" in term_name:
            return term_name.split("[")[0]

        return term_name

    # =========================================================================
    # Visualization Methods
    # =========================================================================

    def plot_params(self, **kwargs):
        """Plot fixed effect estimates as a forest plot.

        Convenience method that calls `bossanova.viz.plot_params(self, **kwargs)`.

        Args:
            **kwargs (Any): Passed to `viz.plot_params`. Key options:
                include_intercept: Include intercept term (default False);
                effect_sizes: Plot Cohen's d instead of raw estimates;
                sort: Sort by magnitude (default False);
                show_values: Display estimate values (default False);
                show_pvalue: Add significance stars (default False).

        Returns:
            Seaborn FacetGrid containing the plot.

        Raises:
            RuntimeError: If model is not fitted.

        See Also:
            bossanova.viz.plot_params: Full documentation.
            plot_ranef: Random effects caterpillar plot.
        """
        try:
            from bossanova.viz.params import plot_params

            return plot_params(self, **kwargs)
        except ImportError:
            raise NotImplementedError(
                "plot_params not yet implemented. Coming in a future release."
            )

    def plot_ranef(self, **kwargs):
        """Plot random effects as a caterpillar plot.

        Convenience method that calls `bossanova.viz.plot_ranef(self, **kwargs)`.

        Args:
            **kwargs (Any): Passed to `viz.plot_ranef`. Key options:
                group: Which grouping factor to show;
                term: Which RE term to show (e.g., "Intercept");
                col: Column faceting variable;
                show: Which levels to display ("all", int, list, "quartile");
                sort: Sort by magnitude (default False).

        Returns:
            Seaborn FacetGrid containing the plot.

        Raises:
            RuntimeError: If model is not fitted.
            TypeError: If model has no random effects.

        See Also:
            bossanova.viz.plot_ranef: Full documentation.
            plot_params: Fixed effects forest plot.
        """
        try:
            from bossanova.viz.ranef import plot_ranef

            return plot_ranef(self, **kwargs)
        except ImportError:
            raise NotImplementedError(
                "plot_ranef not yet implemented. Coming in a future release."
            )

    def plot_resid(self, **kwargs):
        """Plot residual diagnostics (4-panel grid).

        Convenience method that calls `bossanova.viz.plot_resid(self, **kwargs)`.

        Args:
            **kwargs (Any): Passed to `viz.plot_resid`. Key options:
                which: Panel selection (default "all");
                residual_type: "response", "pearson", or "deviance";
                lowess: Add lowess smooth (default True).

        Returns:
            object: Residual diagnostics figure (matplotlib.figure.Figure).

        Raises:
            NotImplementedError: Plot function not yet implemented.

        See Also:
            bossanova.viz.plot_resid: Full documentation.
        """
        try:
            from bossanova.viz.resid import plot_resid

            return plot_resid(self, **kwargs)
        except ImportError:
            raise NotImplementedError(
                "plot_resid not yet implemented. Coming in a future release."
            )

    def plot_predict(self, term: str, **kwargs):
        """Plot marginal predictions across a predictor's range.

        Convenience method that calls `bossanova.viz.plot_predict(self, term, **kwargs)`.

        Args:
            term (str): Predictor variable to plot.
            **kwargs (Any): Passed to `viz.plot_predict`. Key options:
                hue: Color encoding (categorical grouping);
                col: Column faceting variable;
                row: Row faceting variable;
                at: Fix other predictors at specific values;
                units: "data" (default) or "link";
                interval: "confidence" (default) or "prediction";
                show_blups: For mixed models, show group-specific BLUP lines;
                groups: Which group levels to show when show_blups=True.

        Returns:
            Seaborn FacetGrid containing the plot.

        Raises:
            RuntimeError: If model is not fitted.
            ValueError: If term is not in model data.

        See Also:
            bossanova.viz.plot_predict: Full documentation.
        """
        try:
            from bossanova.viz.predict import plot_predict

            return plot_predict(self, term=term, **kwargs)
        except ImportError:
            raise NotImplementedError(
                "plot_predict not yet implemented. Coming in a future release."
            )

    def plot_mee(self, specs: str, **kwargs):
        """Plot marginal estimated effects.

        Convenience method that calls `bossanova.viz.plot_mee(self, specs, **kwargs)`.

        Args:
            specs (str): Variable(s) to compute EMMs for.
            **kwargs (Any): Passed to `viz.plot_mee`. Key options:
                hue: Color encoding for grouping;
                col: Column faceting variable;
                row: Row faceting variable;
                units: "data" (default) or "link";
                contrasts: Show contrast annotations.

        Returns:
            Seaborn FacetGrid containing the plot.

        Raises:
            RuntimeError: If model is not fitted.

        See Also:
            bossanova.viz.plot_mee: Full documentation.
        """
        try:
            from bossanova.viz.mem import plot_mee

            return plot_mee(self, specs=specs, **kwargs)
        except ImportError:
            raise NotImplementedError(
                "plot_mee not yet implemented. Coming in a future release."
            )

    def plot_fit(self, **kwargs):
        """Plot observed vs predicted values to assess model fit.

        Convenience method that calls `bossanova.viz.plot_fit(self, **kwargs)`.

        Creates a scatter plot comparing observed (actual) values against
        predicted (fitted) values. A perfect model would have all points
        on the 45-degree identity line.

        This answers: "How well does the model capture the data?"

        Args:
            **kwargs (Any): Passed to `viz.plot_fit`. Key options:
                hue: Column name for color encoding.
                col: Column name for faceting into columns.
                row: Column name for faceting into rows.
                show_identity: Show 45-degree identity line (default True).
                show_r2: Annotate with R² value (default True).

        Returns:
            object: Seaborn FacetGrid containing the plot.

        Raises:
            RuntimeError: If model is not fitted.

        See Also:
            bossanova.viz.plot_fit: Full documentation.
            plot_resid: Residual diagnostics (Q-Q, scale-location, leverage).
        """
        try:
            from bossanova.viz.fit import plot_fit

            return plot_fit(self, **kwargs)
        except ImportError:
            raise NotImplementedError(
                "plot_fit not yet implemented. Coming in a future release."
            )

    def plot_design(self, **kwargs):
        """Plot design matrix heatmap.

        Convenience method that calls `bossanova.viz.plot_design(self, **kwargs)`.

        Visualizes the structure of the model's design matrix with:
        - Color-coded cells by value (diverging colormap)
        - Column grouping annotations showing which columns belong to each term
        - Reference level annotations for categorical variables

        Works on unfitted models since the design matrix is built at initialization.

        Args:
            **kwargs (Any): Passed to `viz.plot_design`. Key options:
                max_rows: Maximum rows to display (default 50);
                annotate_terms: Show term grouping brackets (default True);
                show_contrast_info: Show reference level annotations (default True);
                cmap: Matplotlib colormap (default "RdBu_r");
                figsize: Figure size as (width, height);
                ax: Existing matplotlib Axes to plot on.

        Returns:
            object: Design matrix figure (matplotlib.figure.Figure or Axes).

        See Also:
            bossanova.viz.plot_design: Full documentation.
        """
        from bossanova.viz.design import plot_design

        return plot_design(self, **kwargs)

    def plot_vif(self, **kwargs):
        """Plot VIF (Variance Inflation Factor) diagnostics.

        Convenience method that calls `bossanova.viz.plot_vif(self, **kwargs)`.

        Visualizes multicollinearity in the design matrix:
        - Correlation heatmap between predictors
        - VIF for each predictor (1=no collinearity, >5=concerning, >10=severe)
        - CI increase factor (√VIF) showing confidence interval inflation

        Works on unfitted models since the design matrix is built at initialization.

        For pairwise scatter plots including the response, use `plot_relationships()`.

        Args:
            **kwargs (Any): Passed to `viz.plot_vif`. Key options:
                cmap: Matplotlib colormap (default "coolwarm");
                figsize: Figure size as (width, height);
                ax: Existing matplotlib Axes.

        Returns:
            object: VIF figure (matplotlib.figure.Figure or Axes).

        See Also:
            bossanova.viz.plot_vif: Full documentation.
            plot_relationships: Pairwise scatter plots with response variable.
        """
        from bossanova.viz.vif import plot_vif

        return plot_vif(self, **kwargs)

    def plot_relationships(self, **kwargs):
        """Plot pairwise relationships between response and predictors.

        Convenience method that calls `bossanova.viz.plot_relationships(self, **kwargs)`.

        Creates a scatter plot matrix showing:
        - Response variable (y) in the first row/column
        - All predictor variables from the design matrix
        - Diagonal shows distributions (KDE) colored by variable type
        - Off-diagonal shows pairwise scatter plots
        - VIF statistics for multicollinearity assessment (optional)

        Works on unfitted models since the design matrix is built at initialization.

        Args:
            **kwargs (Any): Passed to `viz.plot_relationships`. Key options:
                show_vif: Whether to display VIF statistics (default True);
                figsize: Figure size as (width, height).

        Returns:
            object: Relationships figure (matplotlib.figure.Figure).

        See Also:
            bossanova.viz.plot_relationships: Full documentation.
            plot_vif: Correlation heatmap for multicollinearity.
        """
        from bossanova.viz.relationships import plot_relationships

        return plot_relationships(self, **kwargs)

    # =========================================================================
    # Inference Method
    # =========================================================================

    def infer(
        self,
        how: Literal["asymp", "boot", "perm", "cv"] = "asymp",
        *,
        summary: bool = True,
        save_resamples: bool = False,
        # Common
        n: int = 999,
        conf_int: float = 0.95,
        seed: int | None = None,
        n_jobs: int = 1,
        verbose: bool = False,
        # Bootstrap-specific
        boot_type: str = "residual",
        ci_type: str = "bca",
        # CV-specific
        folds: int | Literal["loo"] = 5,
        # Permutation-specific
        alternative: Literal["two-sided", "greater", "less"] = "two-sided",
        # MEE-specific (moved from .mee())
        p_adjust: str = "none",
        # Error structure assumption
        errors: str = "auto",
    ) -> Self:
        """Perform statistical inference on fitted model or MEE results.

        Call this after fit() to compute standard errors, confidence intervals,
        and p-values using the specified method. Also supports inference on
        marginal effects computed via .mee().

        Dispatches based on last operation:
        - After .fit(): inference on model parameters
        - After .mee(): inference on marginal effects

        Args:
            how: Inference method:
                - "asymp": Asymptotic inference (Wald/t-tests, default)
                - "boot": Bootstrap confidence intervals
                - "perm": Permutation test p-values (not for MEE)
                - "cv": Cross-validation with ablation importance (not for MEE)
            summary: If True (default), print summary after inference.
            save_resamples: If True, store raw resampling results in:
                - self.boot_samples_ (BootstrapResult for how="boot")
                - self.perm_samples_ (PermutationResult for how="perm")
                - self.cv_results_ (CVResult for how="cv")
            n: Number of resamples for bootstrap/permutation (default 999).
            conf_int: Confidence level (default 0.95).
            seed: Random seed for reproducibility.
            n_jobs: Number of parallel jobs (default 1).
            verbose: Print progress during resampling.
            boot_type: Bootstrap method: "residual", "case", or "parametric".
                Model-specific defaults apply if not specified.
            ci_type: Bootstrap CI method: "bca", "percentile", or "basic".
            folds: CV folds as int, or "loo" for leave-one-out.
            alternative: Permutation test direction: "two-sided", "greater", "less".
            p_adjust: P-value adjustment method for MEE contrasts. Options:
                - "none" (default): No adjustment
                - "bonferroni", "holm", "hochberg", "hommel", "fdr_bh", "fdr_by"
            errors: Error structure assumption for standard errors (lm only):
                - "auto": Standard OLS assumption (default, same as "iid")
                - "iid": Standard OLS assumption (homoscedastic, independent)
                - "hetero": Sandwich HC3 estimator (arbitrary heteroscedasticity)
                - "unequal_var": Welch-style (group-specific variances, auto-detects
                  factors from formula)
                - "HC0", "HC1", "HC2", "HC3": Specific sandwich estimators

        Returns:
            Self for method chaining.

        Raises:
            RuntimeError: If model not fitted.
            NotImplementedError: If method not supported for this model type.
            ValueError: If MEE inference requested with unsupported method.

        Examples:
            >>> model = lm("y ~ x", data=df).fit()
            >>> model.infer()  # Asymptotic inference (default)

            >>> model.infer(how="boot", n=999)  # Bootstrap CIs

            >>> # MEE inference
            >>> model.mee("treatment").infer()  # Asymptotic
            >>> model.mee("treatment").infer(how="boot", n=999)  # Bootstrap

            >>> # MEE contrasts with p-value adjustment
            >>> model.mee("treatment", contrasts="pairwise").infer(p_adjust="bonferroni")
        """
        self._check_fitted()

        # MEE context detection: dispatch to MEE inference if last operation was mee()
        if self._last_operation == "mee":
            # Validate MEE-compatible methods
            if how not in ("asymp", "boot"):
                raise ValueError(
                    f"For MEE inference, how must be 'asymp' or 'boot', got {how!r}. "
                    f"Permutation and CV are not supported for marginal effects."
                )

            if how == "asymp":
                self._infer_mee_asymp(
                    conf_int=conf_int, p_adjust=p_adjust, errors=errors
                )
            else:  # how == "boot"
                self._infer_mee_boot(
                    n_boot=n,
                    ci_type=ci_type,
                    conf_level=conf_int,
                    seed=seed,
                    save_resamples=save_resamples,
                )

            # Don't print summary for MEE (use result_mee instead)
            return self

        # Standard parameter inference
        # Validate method
        # Note: "wald" and "satterthwaite" are lmer-specific variants of asymptotic inference
        valid_methods = {"asymp", "boot", "perm", "cv", "wald", "satterthwaite"}
        if how not in valid_methods:
            raise ValueError(
                f"how must be one of: {', '.join(sorted(valid_methods))}; got '{how}'"
            )
        method = how

        # Store save_resamples flag for use by _infer_* methods
        self._save_resamples = save_resamples

        # Store alternative for permutation tests
        self._perm_alternative = alternative

        # Map consolidated parameters
        n_boot = n
        n_perm = n
        k = folds if isinstance(folds, int) else 5
        loo = folds == "loo"

        # Delegate to internal method
        self._infer(
            method=method,
            conf_int=conf_int,
            n_boot=n_boot,
            n_perm=n_perm,
            boot_type=boot_type,
            ci_type=ci_type,
            k=k,
            loo=loo,
            seed=seed,
            n_jobs=n_jobs,
            verbose=verbose,
            errors=errors,
        )

        # Set last_operation to fit (so subsequent .mee() works correctly)
        self._last_operation = "fit"

        # Print summary if requested
        if summary:
            self.summary()

        return self

    def _infer(
        self,
        method: str = "asymp",
        *,
        conf_int: float = 0.95,
        # Boot/perm kwargs
        n_boot: int = 999,
        n_perm: int = 999,
        boot_type: str = "parametric",
        ci_type: str = "percentile",
        # CV kwargs
        k: int = 5,
        loo: bool = False,
        # Common
        seed: int | None = None,
        n_jobs: int = 1,
        verbose: bool = False,
        # Error structure
        errors: str = "auto",
    ) -> Self:
        """Compute inference on fitted model (internal).

        Called by fit() when inference parameter is specified.
        Always updates result_params in place.
        """
        self._check_fitted()

        # Normalize method names: "asymp" and "wald" are equivalent
        if method == "wald":
            method = "asymp"

        # Parse conf_int
        conf_level = self._parse_conf_int(conf_int)

        # Dispatch to appropriate inference method
        if method == "asymp":
            result_df = self._infer_asymp(conf_level, errors=errors)
        elif method == "boot":
            result_df = self._infer_boot(
                conf_level=conf_level,
                n_boot=n_boot,
                boot_type=boot_type,
                ci_type=ci_type,
                seed=seed,
                n_jobs=n_jobs,
                verbose=verbose,
            )
        elif method == "perm":
            result_df = self._infer_perm(
                conf_level=conf_level,
                n_perm=n_perm,
                seed=seed,
                n_jobs=n_jobs,
                verbose=verbose,
            )
        elif method == "cv":
            result_df = self._infer_cv(
                conf_level=conf_level,
                k=k,
                loo=loo,
                seed=seed,
                n_jobs=n_jobs,
                verbose=verbose,
            )
        elif method == "satterthwaite":
            result_df = self._infer_satterthwaite(conf_level)
        else:
            raise NotImplementedError(
                f"Inference method '{method}' not supported for {type(self).__name__}. "
                f"Supported methods depend on model type."
            )

        # Update model state
        # For CV, update diagnostics instead of result_params
        if method == "cv":
            self._result_model = result_df
        else:
            self._result_params = result_df
            self._inference = method
        return self

    def _infer_asymp(
        self,
        conf_level: float,
        errors: str = "auto",
    ) -> pl.DataFrame:
        """Compute asymptotic/Wald inference.

        Subclasses should override if they support asymptotic inference.

        Args:
            conf_level: Confidence level for intervals.
            errors: Error structure assumption ('auto', 'iid', 'hetero',
                'unequal_var', 'HC0', 'HC1', 'HC2', 'HC3').

        Returns:
            DataFrame with inference results.

        Raises:
            NotImplementedError: If not supported.
        """
        raise NotImplementedError(
            f"Asymptotic inference not implemented for {type(self).__name__}."
        )

    def _infer_boot(
        self,
        conf_level: float,
        n_boot: int,
        boot_type: str,
        ci_type: str,
        seed: int | None,
        n_jobs: int,
        verbose: bool,
    ) -> pl.DataFrame:
        """Compute bootstrap inference.

        Subclasses should override if they support bootstrap inference.

        Args:
            conf_level: Confidence level for intervals.
            n_boot: Number of bootstrap samples.
            boot_type: Type of bootstrap.
            ci_type: Type of confidence interval.
            seed: Random seed.
            n_jobs: Number of parallel jobs.
            verbose: Print progress.

        Returns:
            DataFrame with inference results.

        Raises:
            NotImplementedError: If not supported.
        """
        raise NotImplementedError(
            f"Bootstrap inference not implemented for {type(self).__name__}."
        )

    def _infer_perm(
        self,
        conf_level: float,
        n_perm: int,
        seed: int | None,
        n_jobs: int,
        verbose: bool,
    ) -> pl.DataFrame:
        """Compute permutation test inference.

        Subclasses should override if they support permutation tests.

        Args:
            conf_level: Confidence level for reference CIs.
            n_perm: Number of permutations.
            seed: Random seed.
            n_jobs: Number of parallel jobs.
            verbose: Print progress.

        Returns:
            DataFrame with inference results.

        Raises:
            NotImplementedError: If not supported.
        """
        raise NotImplementedError(
            f"Permutation inference not implemented for {type(self).__name__}."
        )

    def _infer_cv(
        self,
        conf_level: float,
        k: int,
        loo: bool,
        seed: int | None,
        n_jobs: int,
        verbose: bool,
    ) -> pl.DataFrame:
        """Compute cross-validation metrics.

        Subclasses should override if they support cross-validation.

        Args:
            conf_level: Confidence level (unused for CV, kept for consistency).
            k: Number of folds.
            loo: Use leave-one-out CV.
            seed: Random seed.
            n_jobs: Number of parallel jobs.
            verbose: Print progress.

        Returns:
            DataFrame with CV metrics.

        Raises:
            NotImplementedError: If not supported.
        """
        raise NotImplementedError(
            f"Cross-validation not implemented for {type(self).__name__}."
        )

    def _infer_satterthwaite(self, conf_level: float) -> pl.DataFrame:
        """Compute Satterthwaite degrees of freedom inference.

        Only applicable to mixed models (lmer).

        Args:
            conf_level: Confidence level for intervals.

        Returns:
            DataFrame with inference results.

        Raises:
            NotImplementedError: If not supported.
        """
        raise NotImplementedError(
            f"Satterthwaite inference not implemented for {type(self).__name__}. "
            f"This method is only available for mixed models (lmer)."
        )

    # =========================================================================
    # MEE Inference Methods
    # =========================================================================

    def _infer_mee_asymp(
        self,
        conf_int: float = 0.95,
        p_adjust: str = "none",
        errors: str = "auto",
    ) -> None:
        """Add asymptotic inference columns to MEE results.

        Uses delta method: SE = sqrt(diag(X_ref @ Var(β) @ X_ref.T))

        Args:
            conf_int: Confidence level (0-1).
            p_adjust: P-value adjustment method for contrasts.
            errors: Error structure assumption for robust inference (lm only):
                - None: Use standard OLS vcov and df (default)
                - "hetero": Use HC3 sandwich vcov
                - "unequal_var": Use Welch-style df
                - "HC0", "HC1", "HC2", "HC3": Specific sandwich variants
        """
        import polars as pl
        from scipy import stats as scipy_stats

        from bossanova.ops.inference import adjust_pvalues

        if self._result_mee is None or self._mee_X_ref is None:
            raise RuntimeError("No MEE results to infer. Call .mee() first.")

        X_ref = self._mee_X_ref
        vcov = self._vcov
        df_values = self._mee_df

        # Handle errors parameter for lm models
        # 'auto' and 'iid' use standard inference (no special handling needed)
        if errors not in ("auto", "iid"):
            # Check if this is an lm model
            from bossanova.models.lm import lm as LMClass

            if not isinstance(self, LMClass):
                raise ValueError(
                    f"errors parameter '{errors}' is only supported for lm models, "
                    f"got {type(self).__name__}. Use errors='auto' or 'iid'."
                )

            if errors in ("hetero", "HC0", "HC1", "HC2", "HC3"):
                # Compute HC vcov
                from bossanova.stats.sandwich import compute_hc_vcov

                hc_type = "HC3" if errors == "hetero" else errors
                sigma_sq = self._sigma**2
                XtX_inv = self._vcov / sigma_sq

                X_valid = self._X[self._valid_mask]
                resid_valid = self._residuals[self._valid_mask]

                vcov = compute_hc_vcov(X_valid, resid_valid, XtX_inv, hc_type=hc_type)

            elif errors == "unequal_var":
                # Use Welch df
                from bossanova.stats.welch import (
                    compute_cell_info,
                    extract_factors_from_formula,
                    welch_satterthwaite_df,
                )

                factors = extract_factors_from_formula(self._formula, self._data)

                if not factors:
                    raise ValueError(
                        "errors='unequal_var' requires at least one factor "
                        "(categorical) variable in the formula.\n"
                        "For arbitrary heteroscedasticity, use errors='hetero' instead."
                    )

                valid_data = self._data.filter(pl.Series(self._valid_mask))
                cell_info = compute_cell_info(
                    self._residuals[self._valid_mask],
                    valid_data,
                    factors,
                )

                # Use Welch df for all MEE entries
                df_values = welch_satterthwaite_df(
                    cell_info.cell_variances,
                    cell_info.cell_counts,
                )

            else:
                raise ValueError(
                    f"Unknown errors type: {errors!r}. "
                    "Use 'auto', 'iid', 'hetero', 'unequal_var', or 'HC0'/'HC1'/'HC2'/'HC3'."
                )

        # Compute SE: sqrt(diag(X_ref @ vcov @ X_ref.T))
        vcov_emm = X_ref @ vcov @ X_ref.T
        se = np.sqrt(np.diag(vcov_emm))

        n = len(se)

        # Ensure df_values is an array
        if np.isscalar(df_values) or (
            isinstance(df_values, np.ndarray) and df_values.ndim == 0
        ):
            df_arr = np.full(n, float(df_values))
        else:
            df_arr = np.asarray(df_values)

        # Compute CIs
        t_crit = np.array([scipy_stats.t.ppf((1 + conf_int) / 2, d) for d in df_arr])
        estimates = self._result_mee["estimate"].to_numpy()
        ci_lower = estimates - t_crit * se
        ci_upper = estimates + t_crit * se

        # Add inference columns to result
        self._result_mee = self._result_mee.with_columns(
            [
                pl.Series("se", se),
                pl.Series("df", df_arr),
                pl.Series("ci_lower", ci_lower),
                pl.Series("ci_upper", ci_upper),
            ]
        )

        # For contrasts and slopes, compute statistic and p-value
        # (Testing H0: contrast=0 or slope=0 is meaningful)
        is_slopes = (
            "level" in self._result_mee.columns
            and (self._result_mee["level"] == "slope").any()
        )

        if self._mee_has_contrasts or is_slopes:
            statistic = estimates / se
            p_values = 2 * (1 - scipy_stats.t.cdf(np.abs(statistic), df_arr))

            cols = [
                pl.Series("statistic", statistic),
                pl.Series("p_value", p_values),
            ]

            if p_adjust != "none":
                p_adjusted = adjust_pvalues(p_values, method=p_adjust)
                cols.append(pl.Series("p_adjusted", p_adjusted))

            self._result_mee = self._result_mee.with_columns(cols)

    def _infer_mee_boot(
        self,
        n_boot: int = 999,
        ci_type: str = "bca",
        conf_level: float = 0.95,
        seed: int | None = None,
        save_resamples: bool = False,
    ) -> None:
        """Add bootstrap inference columns to MEE results.

        Key insight: MEEs = X_ref @ coef, so boot_mees = boot_coefs @ X_ref.T
        No model refitting needed for MEE bootstrap!

        Args:
            n_boot: Number of bootstrap samples.
            ci_type: CI method ("bca", "percentile", "basic").
            conf_level: Confidence level (0-1).
            seed: Random seed.
            save_resamples: Store raw bootstrap MEE samples in self.boot_mee_samples_.
        """
        if self._result_mee is None or self._mee_X_ref is None:
            raise RuntimeError("No MEE results to infer. Call .mee() first.")

        X_ref = self._mee_X_ref

        # Get bootstrap coefficient samples from model
        # This reuses the existing bootstrap infrastructure
        boot_result = self._bootstrap(
            n_boot=n_boot,
            ci_type=ci_type,
            level=conf_level,
            seed=seed,
        )

        boot_coefs = np.asarray(boot_result.boot_samples)  # [n_boot, n_params]

        # Transform to MEE scale: boot_mees = boot_coefs @ X_ref.T
        boot_mees = boot_coefs @ X_ref.T  # [n_boot, n_emms]

        # Observed MEEs
        observed_mees = self._result_mee["estimate"].to_numpy()

        # Bootstrap SE
        boot_se = np.std(boot_mees, axis=0)

        # Compute CIs based on ci_type
        alpha = 1 - conf_level
        if ci_type == "percentile":
            ci_lower = np.percentile(boot_mees, 100 * alpha / 2, axis=0)
            ci_upper = np.percentile(boot_mees, 100 * (1 - alpha / 2), axis=0)
        elif ci_type == "basic":
            # Basic bootstrap: 2*observed - percentiles
            lower_pct = np.percentile(boot_mees, 100 * (1 - alpha / 2), axis=0)
            upper_pct = np.percentile(boot_mees, 100 * alpha / 2, axis=0)
            ci_lower = 2 * observed_mees - lower_pct
            ci_upper = 2 * observed_mees - upper_pct
        elif ci_type == "bca":
            # BCa bootstrap - compute bias-corrected and accelerated CIs
            ci_lower, ci_upper = self._bca_ci(boot_mees, observed_mees, conf_level)
        else:
            raise ValueError(f"Unknown ci_type: {ci_type}")

        # Update result
        self._result_mee = self._result_mee.with_columns(
            [
                pl.Series("se", boot_se),
                pl.Series("ci_lower", ci_lower),
                pl.Series("ci_upper", ci_upper),
                pl.lit(n_boot).alias("n_resamples"),
            ]
        )

        if save_resamples:
            self.boot_mee_samples_ = boot_mees

    def _bca_ci(
        self,
        boot_samples: np.ndarray,
        observed: np.ndarray,
        conf_level: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute BCa confidence intervals for MEE bootstrap.

        Args:
            boot_samples: Bootstrap samples [n_boot, n_params].
            observed: Observed estimates [n_params].
            conf_level: Confidence level.

        Returns:
            Tuple of (ci_lower, ci_upper) arrays.
        """
        from scipy import stats as scipy_stats

        n_boot, n_params = boot_samples.shape
        alpha = 1 - conf_level

        ci_lower = np.zeros(n_params)
        ci_upper = np.zeros(n_params)

        for i in range(n_params):
            samples = boot_samples[:, i]
            obs = observed[i]

            # Bias correction factor z0
            z0 = scipy_stats.norm.ppf(np.mean(samples < obs))

            # Acceleration factor a (simplified - use 0 for speed)
            # Full BCa would compute jackknife influence values
            a = 0.0

            # Adjusted percentiles
            z_alpha = scipy_stats.norm.ppf(alpha / 2)
            z_1_alpha = scipy_stats.norm.ppf(1 - alpha / 2)

            # Bias-corrected percentiles
            alpha1 = scipy_stats.norm.cdf(
                z0 + (z0 + z_alpha) / (1 - a * (z0 + z_alpha))
            )
            alpha2 = scipy_stats.norm.cdf(
                z0 + (z0 + z_1_alpha) / (1 - a * (z0 + z_1_alpha))
            )

            # Handle edge cases
            alpha1 = np.clip(alpha1, 0.001, 0.999)
            alpha2 = np.clip(alpha2, 0.001, 0.999)

            ci_lower[i] = np.percentile(samples, 100 * alpha1)
            ci_upper[i] = np.percentile(samples, 100 * alpha2)

        return ci_lower, ci_upper

    @property
    def result_mee(self) -> "ResultMee | None":
        """Marginal effects table from last .mee() call.

        Returns a :class:`~bossanova.results.ResultMee` wrapper with methods:

        - :meth:`~bossanova.results.ResultMee.filter_terms`: Filter by focal variable
        - :meth:`~bossanova.results.ResultMee.filter_levels`: Filter by level
        - :meth:`~bossanova.results.ResultMee.filter_contrasts`: Filter contrasts
        - :meth:`~bossanova.results.ResultMee.filter_significant`: Filter by p-value
        - :meth:`~bossanova.results.ResultMee.recompute_ci`: CIs at different level
        - :meth:`~bossanova.results.ResultMee.to_response_scale`: Transform GLM to response

        All standard polars DataFrame operations (filter, select, etc.) also work.

        Returns:
            ResultMee wrapper if .mee() has been called, None otherwise.

        Examples:
            >>> model = lm("y ~ treatment", data=df).fit()
            >>> model.mee("treatment")
            >>> model.result_mee  # Minimal: term, level, estimate

            >>> model.mee("treatment").infer()
            >>> model.result_mee  # + se, df, ci_lower, ci_upper

            >>> # Filter and convert
            >>> model.result_mee.filter_terms("treatment")
            >>> model.result_mee.to_dataframe()  # Raw polars DataFrame

        See Also:
            :class:`~bossanova.results.ResultMee`: Full API documentation.
        """
        from bossanova.results.wrappers import ResultMee

        if self._result_mee is None:
            return None

        return ResultMee(self._result_mee, self)

    # =========================================================================
    # CV Ablation Infrastructure (Template Method Pattern)
    # =========================================================================

    @property
    def _cv_metric_name(self) -> str:
        """Name of the metric to use for CV importance computation.

        Subclasses should override if they use a different metric.
        Default is "r2" for regression models.

        Returns:
            Metric name (key in CVResult.mean_scores dict).
        """
        return "r2"

    def _create_ablated_model(self, ablated_formula: str) -> "Self":
        """Create and fit a model with an ablated formula.

        Default implementation creates same model type with new formula.
        Subclasses may override if they need special handling (e.g., GLM family).

        Args:
            ablated_formula: Formula with one predictor removed.

        Returns:
            Fitted model instance.
        """
        return type(self)(ablated_formula, data=self._data).fit()

    def _compute_cv_importance(
        self,
        full_cv_metric: float,
        cv_strategy: int | str,
        seed: int | None,
    ) -> dict[str, float]:
        """Compute CV-based importance for each predictor via ablation.

        For each predictor (excluding Intercept), fits an ablated model
        (predictor removed) and computes CV metric. Importance is the drop
        in the metric when the predictor is removed.

        Args:
            full_cv_metric: Metric value from full model CV.
            cv_strategy: CV strategy (k for k-fold, "loo" for leave-one-out).
            seed: Random seed for reproducibility.

        Returns:
            Dict mapping term names to importance scores.
            Intercept gets importance=0, predictors get (full_metric - ablated_metric).
        """
        importance: dict[str, float] = {}
        metric_name = self._cv_metric_name

        # Get predictor names (excluding Intercept)
        predictors = [name for name in self._X_names if name.lower() != "intercept"]

        for pred in predictors:
            # Create ablated formula
            ablated_formula = remove_predictor_from_formula(self._formula, pred)

            # Skip if formula didn't change (predictor couldn't be removed)
            if ablated_formula == self._formula:
                importance[pred] = 0.0
                continue

            try:
                # Fit ablated model and run CV
                ablated_model = self._create_ablated_model(ablated_formula)
                ablated_cv = ablated_model._cv(cv=cv_strategy, seed=seed)
                ablated_metric = float(ablated_cv.mean_scores[metric_name])

                # Importance = drop in metric when predictor removed
                importance[pred] = full_cv_metric - ablated_metric
            except Exception:
                # If ablated model fails, assign zero importance
                importance[pred] = 0.0

        # Intercept has no ablation importance
        if "Intercept" in self._X_names or "intercept" in self._X_names:
            intercept_name = (
                "Intercept" if "Intercept" in self._X_names else "intercept"
            )
            importance[intercept_name] = 0.0

        return importance

    def _add_cv_importance_to_result_params(self, importance: dict[str, float]) -> None:
        """Add cv_importance column to result_params.

        Args:
            importance: Dict mapping term names to importance scores.
        """
        # Get current term order from result_params
        terms = self._result_params["term"].to_list()

        # Build importance column in same order as terms
        importance_values = [importance.get(term, 0.0) for term in terms]

        # Add column to result_params
        self._result_params = self._result_params.with_columns(
            pl.Series("cv_importance", importance_values)
        )
