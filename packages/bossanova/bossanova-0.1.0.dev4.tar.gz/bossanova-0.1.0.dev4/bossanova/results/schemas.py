"""Result dataclass schemas for bossanova models.

These schemas define the structure of result DataFrames returned by models.
Each schema is a dataclass that:

1. Documents the expected columns and types
2. Validates data during construction
3. Provides a consistent interface for builders

Inheritance mirrors model hierarchy:
    BaseResultFit -> LMResultFit -> (future: GLMResultFit, etc.)

Examples:
    >>> schema = LMResultFit(
    ...     term=["Intercept", "x"],
    ...     estimate=[1.0, 2.0],
    ...     se=[0.1, 0.2],
    ...     statistic=[10.0, 10.0],
    ...     df=[28.0, 28.0],
    ...     p_value=[0.001, 0.001],
    ...     ci_lower=[0.8, 1.6],
    ...     ci_upper=[1.2, 2.4],
    ... )
"""

from dataclasses import dataclass, field
from typing import Sequence

__all__ = [
    "BaseResultFit",
    "BaseResultFitDiagnostics",
    "LMResultFit",
    "LMResultFitDiagnostics",
    "BootResultFit",
    "PermResultFit",
    "GLMResultFit",
    "GLMResultFitDiagnostics",
    "GLMOptimizerDiagnostics",
    "LMerOptimizerDiagnostics",
    "GLMerOptimizerDiagnostics",
    "LMerResultFit",
    "LMerResultFitDiagnostics",
    "GLMerResultFit",
    "GLMerResultFitDiagnostics",
    "RidgeResultFit",
    "RidgeResultFitDiagnostics",
    # MEE schemas
    "MeeResult",
    "MeeAsympResult",
    "MeeBootResult",
    "MeeContrastResult",
]

# =============================================================================
# Base Result Schemas (shared across all models)
# =============================================================================


@dataclass
class BaseResultFit:
    """Base schema for coefficient table (result_params).

    All models share these core columns. Model-specific schemas
    inherit and may add additional columns.

    Attributes:
        term: Coefficient names (e.g., "Intercept", "x1", "x1:x2").
        estimate: Point estimates (β̂).
        se: Standard errors.
        statistic: Test statistic (t for lm/lmer, z for glm/glmer).
        p_value: Two-tailed p-values.
        ci_lower: Lower confidence interval bound.
        ci_upper: Upper confidence interval bound.
    """

    term: Sequence[str]
    estimate: Sequence[float]
    se: Sequence[float]
    statistic: Sequence[float]
    p_value: Sequence[float]
    ci_lower: Sequence[float]
    ci_upper: Sequence[float]

    def __post_init__(self):
        """Validate that all sequences have the same length."""
        lengths = {
            "term": len(self.term),
            "estimate": len(self.estimate),
            "se": len(self.se),
            "statistic": len(self.statistic),
            "p_value": len(self.p_value),
            "ci_lower": len(self.ci_lower),
            "ci_upper": len(self.ci_upper),
        }
        unique_lengths = set(lengths.values())
        if len(unique_lengths) > 1:
            raise ValueError(f"All sequences must have same length. Got: {lengths}")


@dataclass
class BaseResultFitDiagnostics:
    """Base schema for fit diagnostics (result_model).

    These are model-level statistics stored as a two-column DataFrame:
    [metric, value]. All models share these core statistics.

    Attributes:
        nobs: Number of observations.
        df_model: Model degrees of freedom.
        df_resid: Residual degrees of freedom (float for Satterthwaite).
        aic: Akaike Information Criterion.
        bic: Bayesian Information Criterion.
        loglik: Log-likelihood.
    """

    nobs: int
    df_model: int
    df_resid: float
    aic: float
    bic: float
    loglik: float

    def __post_init__(self):
        """Validate basic constraints."""
        if self.nobs <= 0:
            raise ValueError(f"nobs must be positive, got {self.nobs}")
        if self.df_model < 0:
            raise ValueError(f"df_model must be non-negative, got {self.df_model}")
        # Allow df_resid=0 for saturated models (n=p)
        if self.df_resid < 0:
            raise ValueError(f"df_resid must be non-negative, got {self.df_resid}")


# =============================================================================
# LM Result Schemas
# =============================================================================


@dataclass
class LMResultFit(BaseResultFit):
    """Schema for lm coefficient table.

    Adds df column for t-distribution degrees of freedom.

    Attributes:
        df: Degrees of freedom for t-distribution (typically n - p).
    """

    df: Sequence[float] = field(default_factory=list)

    def __post_init__(self):
        """Validate that all sequences have the same length, including df."""
        super().__post_init__()
        if len(self.df) > 0 and len(self.df) != len(self.term):
            raise ValueError(
                f"df length ({len(self.df)}) must match term length ({len(self.term)})"
            )


@dataclass
class LMResultFitDiagnostics(BaseResultFitDiagnostics):
    """Schema for lm fit diagnostics.

    Adds R², F-statistic, and sigma specific to linear models.

    Attributes:
        rsquared: R² (coefficient of determination).
        rsquared_adj: Adjusted R².
        fstatistic: F-statistic for overall model significance.
        fstatistic_pvalue: P-value for F-statistic.
        sigma: Residual standard error (√(SS_res / df_resid)).
    """

    rsquared: float = 0.0
    rsquared_adj: float = 0.0
    fstatistic: float = 0.0
    fstatistic_pvalue: float = 1.0
    sigma: float = 0.0

    def __post_init__(self):
        """Validate lm-specific constraints."""
        super().__post_init__()
        if not (0.0 <= self.rsquared <= 1.0):
            raise ValueError(f"rsquared must be in [0, 1], got {self.rsquared}")
        if self.sigma < 0:
            raise ValueError(f"sigma must be non-negative, got {self.sigma}")


# =============================================================================
# Bootstrap/Permutation Result Schemas
# =============================================================================


@dataclass
class BootResultFit:
    """Schema for bootstrap coefficient table.

    Used when `inference="boot"` in fit(). Contains bootstrap standard errors
    and BCa confidence intervals instead of asymptotic t-based inference.

    Attributes:
        term: Coefficient names.
        estimate: Point estimates (β̂) from original data.
        se: Bootstrap standard errors (std of boot samples).
        ci_lower: Lower CI bound (BCa by default).
        ci_upper: Upper CI bound (BCa by default).
        n: Number of observations used in fitting.
        ci_type: Type of CI ("bca", "percentile", or "basic").
        n_boot: Number of bootstrap samples used.
    """

    term: Sequence[str]
    estimate: Sequence[float]
    se: Sequence[float]
    ci_lower: Sequence[float]
    ci_upper: Sequence[float]
    n: int
    ci_type: str = "bca"
    n_boot: int = 999

    def __post_init__(self):
        """Validate that all sequences have the same length."""
        lengths = {
            "term": len(self.term),
            "estimate": len(self.estimate),
            "se": len(self.se),
            "ci_lower": len(self.ci_lower),
            "ci_upper": len(self.ci_upper),
        }
        unique_lengths = set(lengths.values())
        if len(unique_lengths) > 1:
            raise ValueError(f"All sequences must have same length. Got: {lengths}")


@dataclass
class PermResultFit:
    """Schema for permutation test coefficient table.

    Used when `inference="perm"` in fit(). Contains permutation p-values
    instead of asymptotic t-based p-values.

    Attributes:
        term: Coefficient names.
        estimate: Point estimates (β̂) from original data.
        se: Standard errors (asymptotic, for reference).
        statistic: Test statistic used (t-statistic by default).
        n: Number of observations used in fitting.
        p_value: Permutation p-values.
        ci_lower: Lower CI bound (asymptotic, for reference).
        ci_upper: Upper CI bound (asymptotic, for reference).
        n_perm: Number of permutations used.
        test_stat: Type of test statistic ("t", "coef", or "abs_coef").
    """

    term: Sequence[str]
    estimate: Sequence[float]
    se: Sequence[float]
    statistic: Sequence[float]
    n: int
    p_value: Sequence[float]
    ci_lower: Sequence[float]
    ci_upper: Sequence[float]
    n_perm: int = 999
    test_stat: str = "t"

    def __post_init__(self):
        """Validate that all sequences have the same length."""
        lengths = {
            "term": len(self.term),
            "estimate": len(self.estimate),
            "se": len(self.se),
            "statistic": len(self.statistic),
            "p_value": len(self.p_value),
            "ci_lower": len(self.ci_lower),
            "ci_upper": len(self.ci_upper),
        }
        unique_lengths = set(lengths.values())
        if len(unique_lengths) > 1:
            raise ValueError(f"All sequences must have same length. Got: {lengths}")


# =============================================================================
# GLM Result Schemas
# =============================================================================


@dataclass
class GLMResultFit(BaseResultFit):
    """Schema for glm coefficient table.

    Adds df column for consistency, but values are inf for z-statistics.

    Attributes:
        df: Degrees of freedom for z-distribution (always inf).
    """

    df: Sequence[float] = field(default_factory=list)

    def __post_init__(self):
        """Validate that all sequences have the same length, including df."""
        super().__post_init__()
        if len(self.df) > 0 and len(self.df) != len(self.term):
            raise ValueError(
                f"df length ({len(self.df)}) must match term length ({len(self.term)})"
            )


@dataclass
class GLMResultFitDiagnostics(BaseResultFitDiagnostics):
    """Schema for glm fit diagnostics.

    Adds deviance-based statistics specific to GLMs.

    Attributes:
        null_deviance: Null model deviance (intercept-only).
        deviance: Residual deviance.
        dispersion: Dispersion parameter (φ̂).
        pseudo_rsquared: McFadden's pseudo R² (1 - deviance/null_deviance).
    """

    null_deviance: float = 0.0
    deviance: float = 0.0
    dispersion: float = 1.0
    pseudo_rsquared: float = 0.0

    def __post_init__(self):
        """Validate glm-specific constraints."""
        super().__post_init__()
        # Allow small negative values due to floating point errors
        if self.deviance < -1e-10:
            raise ValueError(f"deviance must be non-negative, got {self.deviance}")
        if self.null_deviance < -1e-10:
            raise ValueError(
                f"null_deviance must be non-negative, got {self.null_deviance}"
            )
        if self.dispersion <= 0:
            raise ValueError(f"dispersion must be positive, got {self.dispersion}")


# =============================================================================
# Optimizer Diagnostics - Wide Format Schemas
# =============================================================================


@dataclass
class GLMOptimizerDiagnostics:
    """Schema for GLM optimizer diagnostics (wide format, single row).

    Attributes:
        optimizer: Name of optimization algorithm ("irls").
        converged: Whether optimization converged.
        n_iter: Number of iterations performed.
        tol: Convergence tolerance used.
        final_objective: Final deviance value.
        n_func_evals: Number of objective function evaluations (None for IRLS).
        has_separation: Separation detected (binomial only, else None).
    """

    optimizer: str
    converged: bool
    n_iter: int
    tol: float
    final_objective: float
    n_func_evals: int | None = None
    has_separation: bool | None = None

    def __post_init__(self):
        """Validate basic constraints."""
        if self.n_iter < 0:
            raise ValueError(f"n_iter must be non-negative, got {self.n_iter}")
        if self.tol <= 0:
            raise ValueError(f"tol must be positive, got {self.tol}")


@dataclass
class LMerOptimizerDiagnostics:
    """Schema for lmer optimizer diagnostics (wide format, multi-row for theta).

    Returns a DataFrame with one row per theta parameter, with scalar
    convergence info repeated across rows.

    Attributes:
        optimizer: Name of optimization algorithm ("bobyqa", "nelder_mead").
        converged: Whether optimization converged.
        n_iter: Number of iterations/function evaluations.
        final_objective: Final REML/ML deviance.
        message: Optimizer message.
        theta_index: Index for each theta parameter (0, 1, 2, ...).
        theta_initial: Initial theta values.
        theta_final: Final optimized theta values.
        boundary_adjusted: Whether theta was adjusted to stay within bounds.
        restarted: Whether optimization was restarted from boundary.
        singular: Whether fit is singular (variance component at zero).
    """

    optimizer: str
    converged: bool
    n_iter: int
    final_objective: float
    message: str
    theta_index: Sequence[int]
    theta_initial: Sequence[float]
    theta_final: Sequence[float]
    boundary_adjusted: bool
    restarted: bool
    singular: bool

    def __post_init__(self):
        """Validate basic constraints."""
        if self.n_iter < 0:
            raise ValueError(f"n_iter must be non-negative, got {self.n_iter}")
        if len(self.theta_index) != len(self.theta_initial):
            raise ValueError(
                f"theta_index length ({len(self.theta_index)}) must match "
                f"theta_initial length ({len(self.theta_initial)})"
            )
        if len(self.theta_index) != len(self.theta_final):
            raise ValueError(
                f"theta_index length ({len(self.theta_index)}) must match "
                f"theta_final length ({len(self.theta_final)})"
            )


@dataclass
class GLMerOptimizerDiagnostics:
    """Schema for glmer optimizer diagnostics (wide format, multi-row for theta).

    Returns a DataFrame with one row per theta parameter, with scalar
    convergence info repeated across rows.

    Attributes:
        optimizer: Name of optimization algorithm ("bobyqa", "nelder_mead").
        converged: Whether optimization converged.
        n_iter: Number of outer iterations.
        n_func_evals: Number of objective function evaluations.
        final_objective: Final Laplace objective.
        pirls_converged: Whether PIRLS converged on final iteration.
        pirls_n_iter: Number of PIRLS iterations on final iteration.
        theta_index: Index for each theta parameter (0, 1, 2, ...).
        theta_final: Final optimized theta values.
        boundary_adjusted: Whether theta was adjusted to stay within bounds.
        restarted: Whether optimization was restarted from boundary.
        singular: Whether fit is singular (variance component at zero).
    """

    optimizer: str
    converged: bool
    n_iter: int
    n_func_evals: int
    final_objective: float
    pirls_converged: bool
    pirls_n_iter: int
    theta_index: Sequence[int]
    theta_final: Sequence[float]
    boundary_adjusted: bool
    restarted: bool
    singular: bool

    def __post_init__(self):
        """Validate basic constraints."""
        if self.n_iter < 0:
            raise ValueError(f"n_iter must be non-negative, got {self.n_iter}")
        if self.n_func_evals < 0:
            raise ValueError(
                f"n_func_evals must be non-negative, got {self.n_func_evals}"
            )
        if len(self.theta_index) != len(self.theta_final):
            raise ValueError(
                f"theta_index length ({len(self.theta_index)}) must match "
                f"theta_final length ({len(self.theta_final)})"
            )


# =============================================================================
# LMER Result Schemas
# =============================================================================


@dataclass
class LMerResultFit(BaseResultFit):
    """Schema for lmer coefficient table.

    Matches lme4's summary() fixed effects table with Satterthwaite
    degrees of freedom.

    Attributes:
        df: Denominator degrees of freedom (Satterthwaite approximation).
    """

    df: Sequence[float] = field(default_factory=list)

    def __post_init__(self):
        """Validate that all sequences have the same length, including df."""
        super().__post_init__()
        if len(self.df) > 0 and len(self.df) != len(self.term):
            raise ValueError(
                f"df length ({len(self.df)}) must match term length ({len(self.term)})"
            )


@dataclass
class LMerResultFitDiagnostics(BaseResultFitDiagnostics):
    """Schema for lmer fit diagnostics.

    Contains model fit metrics and convergence info specific to mixed models.

    Attributes:
        method: Estimation method ("REML" or "ML").
        sigma: Residual standard deviation.
        deviance: -2 * log-likelihood (at optimum).
        rsquared_marginal: Nakagawa-Schielzeth R² for fixed effects only.
        rsquared_conditional: Nakagawa-Schielzeth R² for fixed + random effects.
        icc: Intraclass correlation coefficient (proportion of variance from groups).
    """

    method: str = "REML"
    sigma: float = 0.0
    deviance: float = 0.0
    rsquared_marginal: float = 0.0
    rsquared_conditional: float = 0.0
    icc: float = 0.0

    def __post_init__(self):
        """Validate lmer-specific constraints."""
        super().__post_init__()
        if self.method not in ("REML", "ML"):
            raise ValueError(f"method must be 'REML' or 'ML', got {self.method}")
        if self.sigma < 0:
            raise ValueError(f"sigma must be non-negative, got {self.sigma}")
        # Note: negative deviance can occur in edge cases:
        # 1. sigma ≈ 0 (perfect fit): log(sigma²) becomes extremely negative
        # 2. ICC ≈ 1 (extreme): random effect dominates, REML deviance can be negative
        # Only reject if neither boundary condition applies.
        is_boundary_sigma = self.sigma < 1e-6
        is_extreme_icc = self.icc > 0.99
        if self.deviance < 0 and not is_boundary_sigma and not is_extreme_icc:
            raise ValueError(f"deviance must be non-negative, got {self.deviance}")
        # R² and ICC should be in [0, 1] range
        for name, val in [
            ("rsquared_marginal", self.rsquared_marginal),
            ("rsquared_conditional", self.rsquared_conditional),
            ("icc", self.icc),
        ]:
            if not 0 <= val <= 1:
                raise ValueError(f"{name} must be in [0, 1], got {val}")


# =============================================================================
# GLMER Result Schemas
# =============================================================================


@dataclass
class GLMerResultFit(BaseResultFit):
    """Schema for glmer coefficient table.

    Uses Wald z-tests for inference (df = infinity).

    Attributes:
        df: Degrees of freedom for z-distribution (always inf for Wald).
    """

    df: Sequence[float] = field(default_factory=list)

    def __post_init__(self):
        """Validate that all sequences have the same length, including df."""
        super().__post_init__()
        if len(self.df) > 0 and len(self.df) != len(self.term):
            raise ValueError(
                f"df length ({len(self.df)}) must match term length ({len(self.term)})"
            )


@dataclass
class GLMerResultFitDiagnostics(BaseResultFitDiagnostics):
    """Schema for glmer fit diagnostics.

    Contains model fit metrics specific to GLMMs fit via Laplace approximation.

    Attributes:
        family: Distribution family (e.g., "binomial", "poisson").
        link: Link function (e.g., "logit", "log").
        deviance: Conditional deviance (sum of unit deviances, lme4 style).
            Note: For GLMMs, deviance != -2*loglik. This is a GOF measure.
        objective: Laplace objective (optimization criterion, MixedModels.jl style).
            This is: Σ devresid + logdet + ||u||².
    """

    family: str = "binomial"
    link: str = "logit"
    deviance: float = 0.0
    objective: float = 0.0

    def __post_init__(self):
        """Validate glmer-specific constraints."""
        super().__post_init__()
        if self.family not in ("binomial", "poisson"):
            raise ValueError(
                f"family must be 'binomial' or 'poisson', got {self.family}"
            )
        # Allow small negative values due to floating point errors
        if self.deviance < -1e-10:
            raise ValueError(f"deviance must be non-negative, got {self.deviance}")


# =============================================================================
# Ridge Result Schemas
# =============================================================================


@dataclass
class RidgeResultFit:
    """Ridge coefficient table schema.

    Note: se, ci_lower, ci_upper are only populated for:
        - auto mode with inference="asymp" (BLUP-based)
        - any mode with inference="boot" (bootstrap-based)
    For fixed/cv modes with inference="asymp", these are None.

    Attributes:
        term: Coefficient names (e.g., "Intercept", "x1").
        estimate: Point estimates (β̂).
        se: Standard errors (None for fixed/cv asymp mode).
        ci_lower: Lower confidence interval bound (None for fixed/cv asymp mode).
        ci_upper: Upper confidence interval bound (None for fixed/cv asymp mode).
    """

    term: Sequence[str]
    estimate: Sequence[float]
    se: Sequence[float] | None
    ci_lower: Sequence[float] | None
    ci_upper: Sequence[float] | None

    def __post_init__(self):
        """Validate that all sequences have the same length."""
        lengths = {
            "term": len(self.term),
            "estimate": len(self.estimate),
        }

        # Check optional fields if not None
        if self.se is not None:
            lengths["se"] = len(self.se)
        if self.ci_lower is not None:
            lengths["ci_lower"] = len(self.ci_lower)
        if self.ci_upper is not None:
            lengths["ci_upper"] = len(self.ci_upper)

        unique_lengths = set(lengths.values())
        if len(unique_lengths) > 1:
            raise ValueError(f"All sequences must have same length. Got: {lengths}")


@dataclass
class RidgeResultFitDiagnostics:
    """Ridge fit statistics schema.

    Attributes:
        nobs: Number of observations.
        df_model: Number of predictors (excluding intercept).
        df_effective: Effective degrees of freedom (trace(H)).
        rsquared: R² (coefficient of determination).
        rsquared_adj: Adjusted R² (using df_effective).
        mode: Fitting mode ("auto", "fixed", or "cv").
        alpha: Regularization strength (fixed/cv modes, None for auto).
        c_hat: Optimal c value (auto mode, None for fixed/cv).
        cv_score: Best CV MSE (cv mode only, None otherwise).
        prior_scale: Prior scale used (auto mode, None for fixed/cv).
        sigma: Residual standard error.
        gcv: Generalized cross-validation score.
        aic: Akaike Information Criterion (using df_effective).
        bic: Bayesian Information Criterion (using df_effective).
    """

    nobs: int
    df_model: int
    df_effective: float
    rsquared: float
    rsquared_adj: float
    mode: str
    alpha: float | None
    c_hat: float | None
    cv_score: float | None
    prior_scale: float | None
    sigma: float
    gcv: float
    aic: float
    bic: float

    def __post_init__(self):
        """Validate ridge-specific constraints."""
        if self.nobs <= 0:
            raise ValueError(f"nobs must be positive, got {self.nobs}")
        if self.df_model < 0:
            raise ValueError(f"df_model must be non-negative, got {self.df_model}")
        if self.df_effective <= 0:
            raise ValueError(f"df_effective must be positive, got {self.df_effective}")
        # Note: Ridge R² can be negative due to shrinkage bias
        # (sum of squared residuals can exceed total sum of squares)
        if self.rsquared > 1.0:
            raise ValueError(f"rsquared must be <= 1, got {self.rsquared}")
        if self.mode not in ("auto", "fixed", "cv"):
            raise ValueError(f"mode must be 'auto', 'fixed', or 'cv', got {self.mode}")
        if self.sigma < 0:
            raise ValueError(f"sigma must be non-negative, got {self.sigma}")


# =============================================================================
# MEE (Marginal Estimated Effects) Result Schemas
# =============================================================================


@dataclass
class MeeResult:
    """Schema for minimal MEE output (before inference).

    Contains only point estimates. Call .infer() to add uncertainty
    quantification (SE, CIs, p-values).

    Attributes:
        term: Focal variable name(s) (e.g., "treatment", "age").
        level: Factor level or "slope" for continuous variables.
        estimate: Point estimates (marginal means or marginal effects).
    """

    term: Sequence[str]
    level: Sequence[str]
    estimate: Sequence[float]

    def __post_init__(self):
        """Validate that all sequences have the same length."""
        lengths = {
            "term": len(self.term),
            "level": len(self.level),
            "estimate": len(self.estimate),
        }
        unique_lengths = set(lengths.values())
        if len(unique_lengths) > 1:
            raise ValueError(f"All sequences must have same length. Got: {lengths}")


@dataclass
class MeeAsympResult:
    """Schema for MEE with asymptotic inference.

    Contains point estimates plus SE, df, and CIs computed via delta method.
    For contrasts, also includes statistic and p_value.

    Attributes:
        term: Focal variable name(s).
        level: Factor level or "slope" for continuous variables.
        estimate: Point estimates (marginal means or marginal effects).
        se: Standard errors (via delta method).
        df: Degrees of freedom (Satterthwaite for mixed models).
        ci_lower: Lower confidence interval bound.
        ci_upper: Upper confidence interval bound.
        statistic: Test statistic (only for contrasts, otherwise None).
        p_value: P-value (only for contrasts, otherwise None).
    """

    term: Sequence[str]
    level: Sequence[str]
    estimate: Sequence[float]
    se: Sequence[float]
    df: Sequence[float]
    ci_lower: Sequence[float]
    ci_upper: Sequence[float]
    statistic: Sequence[float] | None = None
    p_value: Sequence[float] | None = None

    def __post_init__(self):
        """Validate that all sequences have the same length."""
        required_lengths = {
            "term": len(self.term),
            "level": len(self.level),
            "estimate": len(self.estimate),
            "se": len(self.se),
            "df": len(self.df),
            "ci_lower": len(self.ci_lower),
            "ci_upper": len(self.ci_upper),
        }
        unique_lengths = set(required_lengths.values())
        if len(unique_lengths) > 1:
            raise ValueError(
                f"All required sequences must have same length. Got: {required_lengths}"
            )

        # Optional fields (for contrasts)
        n = len(self.term)
        if self.statistic is not None and len(self.statistic) != n:
            raise ValueError(
                f"statistic length ({len(self.statistic)}) must match term length ({n})"
            )
        if self.p_value is not None and len(self.p_value) != n:
            raise ValueError(
                f"p_value length ({len(self.p_value)}) must match term length ({n})"
            )


@dataclass
class MeeBootResult:
    """Schema for MEE with bootstrap inference.

    Contains point estimates plus SE and CIs computed via bootstrap.
    Bootstrap MEE = boot_coefs @ X_ref.T (linear transformation).

    Attributes:
        term: Focal variable name(s).
        level: Factor level or "slope" for continuous variables.
        estimate: Point estimates (marginal means or marginal effects).
        se: Bootstrap standard errors (std of boot_mees).
        ci_lower: Lower CI bound (percentile, basic, or BCa).
        ci_upper: Upper CI bound (percentile, basic, or BCa).
        n_resamples: Number of bootstrap samples used.
        ci_type: Type of CI ("bca", "percentile", or "basic").
    """

    term: Sequence[str]
    level: Sequence[str]
    estimate: Sequence[float]
    se: Sequence[float]
    ci_lower: Sequence[float]
    ci_upper: Sequence[float]
    n_resamples: int
    ci_type: str = "bca"

    def __post_init__(self):
        """Validate that all sequences have the same length."""
        lengths = {
            "term": len(self.term),
            "level": len(self.level),
            "estimate": len(self.estimate),
            "se": len(self.se),
            "ci_lower": len(self.ci_lower),
            "ci_upper": len(self.ci_upper),
        }
        unique_lengths = set(lengths.values())
        if len(unique_lengths) > 1:
            raise ValueError(f"All sequences must have same length. Got: {lengths}")

        if self.n_resamples <= 0:
            raise ValueError(f"n_resamples must be positive, got {self.n_resamples}")
        if self.ci_type not in ("bca", "percentile", "basic"):
            raise ValueError(
                f"ci_type must be 'bca', 'percentile', or 'basic', got {self.ci_type}"
            )


@dataclass
class MeeContrastResult:
    """Schema for MEE contrast results (pairwise comparisons, etc.).

    Contains contrast estimates with full inference including p-values.

    Attributes:
        term: Focal variable name(s).
        contrast: Contrast description (e.g., "A - B", "B - A").
        estimate: Contrast estimates.
        se: Standard errors.
        df: Degrees of freedom.
        statistic: Test statistic (t or z).
        p_value: Two-tailed p-value.
        ci_lower: Lower confidence interval bound.
        ci_upper: Upper confidence interval bound.
    """

    term: Sequence[str]
    contrast: Sequence[str]
    estimate: Sequence[float]
    se: Sequence[float]
    df: Sequence[float]
    statistic: Sequence[float]
    p_value: Sequence[float]
    ci_lower: Sequence[float]
    ci_upper: Sequence[float]

    def __post_init__(self):
        """Validate that all sequences have the same length."""
        lengths = {
            "term": len(self.term),
            "contrast": len(self.contrast),
            "estimate": len(self.estimate),
            "se": len(self.se),
            "df": len(self.df),
            "statistic": len(self.statistic),
            "p_value": len(self.p_value),
            "ci_lower": len(self.ci_lower),
            "ci_upper": len(self.ci_upper),
        }
        unique_lengths = set(lengths.values())
        if len(unique_lengths) > 1:
            raise ValueError(f"All sequences must have same length. Got: {lengths}")
