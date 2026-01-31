"""GLM family functions for link, variance, and deviance computations.

This module provides pure JAX functions for GLM families, designed for JIT compilation
and automatic differentiation. All link, variance, and deviance functions are
stateless and composable.

The Family NamedTuple serves as a simple container for family-specific functions,
enabling efficient IRLS implementation without class overhead.

Note: For Pyodide/WASM compatibility, this module falls back to NumPy/SciPy when
JAX is not available.
"""

from typing import NamedTuple, Callable

# Conditional JAX import for Pyodide compatibility
try:
    import jax
    import jax.numpy as jnp
    import jax.scipy as jsp

    _HAS_JAX = True
except ImportError:
    import numpy as jnp  # type: ignore[no-redef]
    import scipy as jsp  # type: ignore[no-redef]

    _HAS_JAX = False

    # No-op decorator when JAX is not available
    class _FakeJax:
        @staticmethod
        def jit(fn):
            return fn

    jax = _FakeJax()  # type: ignore[assignment]

__all__ = [
    # Link functions
    "identity_link",
    "identity_link_inverse",
    "identity_link_deriv",
    "log_link",
    "log_link_inverse",
    "log_link_deriv",
    "logit_link",
    "logit_link_inverse",
    "logit_link_deriv",
    "probit_link",
    "probit_link_inverse",
    "probit_link_deriv",
    # Gaussian family
    "gaussian_variance",
    "gaussian_deviance",
    "gaussian_loglik",
    "gaussian_initialize",
    "gaussian_dispersion",
    # Binomial family
    "binomial_variance",
    "binomial_deviance",
    "binomial_loglik",
    "binomial_initialize",
    "binomial_dispersion",
    # Poisson family
    "poisson_variance",
    "poisson_deviance",
    "poisson_loglik",
    "poisson_initialize",
    "poisson_dispersion",
    # Student-t family
    "tdist_variance",
    "tdist_deviance",
    "tdist_loglik",
    "tdist_initialize",
    "tdist_dispersion",
    "tdist_robust_weights",
    # Family configuration
    "Family",
    # Factory functions
    "gaussian",
    "binomial",
    "poisson",
    "tdist",
]


# ============================================================================
# Link Functions (pure JAX, JIT-decorated)
# ============================================================================


@jax.jit
def identity_link(mu: jnp.ndarray) -> jnp.ndarray:
    """Identity link function: η = μ.

    Args:
        mu: Mean values (n,)

    Returns:
        Linear predictor values η (n,)
    """
    return mu


@jax.jit
def identity_link_inverse(eta: jnp.ndarray) -> jnp.ndarray:
    """Identity inverse link: μ = η.

    Args:
        eta: Linear predictor values (n,)

    Returns:
        Mean values μ (n,)
    """
    return eta


@jax.jit
def identity_link_deriv(mu: jnp.ndarray) -> jnp.ndarray:
    """Identity link derivative: dη/dμ = 1.

    Args:
        mu: Mean values (n,)

    Returns:
        Derivative values (n,)
    """
    return jnp.ones_like(mu)


@jax.jit
def log_link(mu: jnp.ndarray) -> jnp.ndarray:
    """Log link function: η = log(μ).

    Args:
        mu: Mean values (n,), must be positive

    Returns:
        Linear predictor values η (n,)
    """
    return jnp.log(mu)


@jax.jit
def log_link_inverse(eta: jnp.ndarray) -> jnp.ndarray:
    """Log inverse link: μ = exp(η).

    Args:
        eta: Linear predictor values (n,)

    Returns:
        Mean values μ (n,)
    """
    return jnp.exp(eta)


@jax.jit
def log_link_deriv(mu: jnp.ndarray) -> jnp.ndarray:
    """Log link derivative: dη/dμ = 1/μ.

    Args:
        mu: Mean values (n,), must be positive

    Returns:
        Derivative values (n,)
    """
    return 1.0 / mu


@jax.jit
def logit_link(mu: jnp.ndarray) -> jnp.ndarray:
    """Logit link function: η = log(μ/(1-μ)).

    Values are clipped to [1e-10, 1-1e-10] to avoid log(0).

    Args:
        mu: Mean values (n,), must be in (0, 1)

    Returns:
        Linear predictor values η (n,)
    """
    mu_clipped = jnp.clip(mu, 1e-10, 1 - 1e-10)
    return jnp.log(mu_clipped / (1 - mu_clipped))


@jax.jit
def logit_link_inverse(eta: jnp.ndarray) -> jnp.ndarray:
    """Logit inverse link: μ = 1/(1 + exp(-η)).

    Uses numerically stable computation to avoid overflow.

    Args:
        eta: Linear predictor values (n,)

    Returns:
        Mean values μ (n,) in (0, 1)
    """
    return jnp.where(
        eta >= 0,
        1.0 / (1.0 + jnp.exp(-eta)),
        jnp.exp(eta) / (1.0 + jnp.exp(eta)),
    )


@jax.jit
def logit_link_deriv(mu: jnp.ndarray) -> jnp.ndarray:
    """Logit link derivative: dη/dμ = 1/(μ(1-μ)).

    Values are clipped to [1e-10, 1-1e-10] to avoid division by zero.

    Args:
        mu: Mean values (n,), must be in (0, 1)

    Returns:
        Derivative values (n,)
    """
    mu_clipped = jnp.clip(mu, 1e-10, 1 - 1e-10)
    return 1.0 / (mu_clipped * (1 - mu_clipped))


@jax.jit
def probit_link(mu: jnp.ndarray) -> jnp.ndarray:
    """Probit link function: η = Φ⁻¹(μ).

    Uses the inverse error function for numerical stability.
    Values are clipped to [1e-10, 1-1e-10] to avoid infinite results.

    Args:
        mu: Mean values (n,), must be in (0, 1)

    Returns:
        Linear predictor values η (n,)
    """
    mu_clipped = jnp.clip(mu, 1e-10, 1 - 1e-10)
    # Φ⁻¹(p) = √2 * erf⁻¹(2p - 1)
    return jnp.sqrt(2.0) * jsp.special.erfinv(2.0 * mu_clipped - 1.0)


@jax.jit
def probit_link_inverse(eta: jnp.ndarray) -> jnp.ndarray:
    """Probit inverse link: μ = Φ(η).

    Args:
        eta: Linear predictor values (n,)

    Returns:
        Mean values μ (n,) in (0, 1)
    """
    return jsp.stats.norm.cdf(eta)


@jax.jit
def probit_link_deriv(mu: jnp.ndarray) -> jnp.ndarray:
    """Probit link derivative: dη/dμ = 1/φ(Φ⁻¹(μ)).

    Where φ is the standard normal PDF.
    Values are clipped to [1e-10, 1-1e-10] to avoid infinite results.

    Args:
        mu: Mean values (n,), must be in (0, 1)

    Returns:
        Derivative values (n,)
    """
    mu_clipped = jnp.clip(mu, 1e-10, 1 - 1e-10)
    eta = jnp.sqrt(2.0) * jsp.special.erfinv(2.0 * mu_clipped - 1.0)
    # φ(η) = exp(-η²/2) / √(2π)
    pdf_val = jnp.exp(-(eta**2) / 2.0) / jnp.sqrt(2.0 * jnp.pi)
    return 1.0 / (pdf_val + 1e-10)


# ============================================================================
# Gaussian Family Functions
# ============================================================================


@jax.jit
def gaussian_variance(mu: jnp.ndarray) -> jnp.ndarray:
    """Gaussian variance function: V(μ) = 1.

    Args:
        mu: Mean values (n,)

    Returns:
        Variance values (n,), all ones
    """
    return jnp.ones_like(mu)


@jax.jit
def gaussian_deviance(y: jnp.ndarray, mu: jnp.ndarray) -> jnp.ndarray:
    """Gaussian unit deviance: d(y, μ) = (y - μ)².

    Args:
        y: Response values (n,)
        mu: Fitted mean values (n,)

    Returns:
        Unit deviance values (n,)
    """
    return (y - mu) ** 2


@jax.jit
def gaussian_loglik(y: jnp.ndarray, mu: jnp.ndarray) -> jnp.ndarray:
    """Gaussian conditional log-likelihood (per observation).

    Computes log p(y|μ) = -0.5 * (y - μ)² ignoring constant terms.
    The full Gaussian log-likelihood includes -0.5*log(2πσ²), but this
    constant term cancels in optimization and is added separately when
    computing final log-likelihood values.

    Args:
        y: Response values (n,)
        mu: Fitted mean values (n,)

    Returns:
        Per-observation log-likelihood values (n,), NOT summed
    """
    return -0.5 * (y - mu) ** 2


def gaussian_initialize(
    y: jnp.ndarray, weights: jnp.ndarray | None = None
) -> jnp.ndarray:
    """Initialize μ for Gaussian family.

    Uses y directly as the starting value (matches R's gaussian family).

    Args:
        y: Response values (n,)
        weights: Optional prior weights (n,). Unused for Gaussian, included
            for API consistency with other families.

    Returns:
        Initial mean values (n,)
    """
    # R uses mustart <- y for Gaussian
    return y + 0.01 * jnp.std(y)


def gaussian_dispersion(y: jnp.ndarray, mu: jnp.ndarray, df_resid: int) -> float:
    """Estimate dispersion parameter for Gaussian family.

    Uses Pearson χ² / df_resid.

    Args:
        y: Response values (n,)
        mu: Fitted mean values (n,)
        df_resid: Residual degrees of freedom

    Returns:
        Dispersion estimate φ̂
    """
    var = gaussian_variance(mu)
    pearson_resid = (y - mu) / jnp.sqrt(var + 1e-10)
    pearson_chi2 = jnp.sum(pearson_resid**2)
    return float(pearson_chi2 / df_resid) if df_resid > 0 else 1.0


# ============================================================================
# Binomial Family Functions
# ============================================================================


@jax.jit
def binomial_variance(mu: jnp.ndarray) -> jnp.ndarray:
    """Binomial variance function: V(μ) = μ(1-μ).

    Args:
        mu: Mean values (n,), must be in (0, 1)

    Returns:
        Variance values (n,)
    """
    mu_clipped = jnp.clip(mu, 1e-10, 1 - 1e-10)
    return mu_clipped * (1 - mu_clipped)


@jax.jit
def binomial_deviance(y: jnp.ndarray, mu: jnp.ndarray) -> jnp.ndarray:
    """Binomial unit deviance: d(y, μ) = 2[y log(y/μ) + (1-y) log((1-y)/(1-μ))].

    Uses log-space arithmetic for numerical stability.

    Args:
        y: Response values (n,), must be in [0, 1]
        mu: Fitted mean values (n,), must be in (0, 1)

    Returns:
        Unit deviance values (n,)
    """
    y_clipped = jnp.clip(y, 1e-10, 1 - 1e-10)
    mu_clipped = jnp.clip(mu, 1e-10, 1 - 1e-10)

    # Use log-space: log(a/b) = log(a) - log(b)
    dev = jnp.where(
        y > 0,
        2 * y * (jnp.log(y_clipped) - jnp.log(mu_clipped)),
        0.0,
    )
    dev += jnp.where(
        y < 1,
        2 * (1 - y) * (jnp.log(1 - y_clipped) - jnp.log(1 - mu_clipped)),
        0.0,
    )
    return dev


@jax.jit
def binomial_loglik(y: jnp.ndarray, mu: jnp.ndarray) -> jnp.ndarray:
    """Binomial conditional log-likelihood (per observation).

    Computes log p(y|μ) = y*log(μ) + (1-y)*log(1-μ) for Bernoulli trials.
    Uses the same numerical stability patterns as binomial_deviance.

    For binomial trials with n > 1, the binomial coefficient log(n choose k)
    would be added, but for Bernoulli (n=1) this term is zero.

    Args:
        y: Response values (n,), must be in [0, 1]
        mu: Fitted mean values (n,), must be in (0, 1)

    Returns:
        Per-observation log-likelihood values (n,), NOT summed
    """
    mu_clipped = jnp.clip(mu, 1e-10, 1 - 1e-10)

    # log p(y|μ) = y*log(μ) + (1-y)*log(1-μ)
    # Use conditional evaluation to avoid log(0) issues
    ll = jnp.where(
        y > 0,
        y * jnp.log(mu_clipped),
        0.0,
    )
    ll += jnp.where(
        y < 1,
        (1 - y) * jnp.log(1 - mu_clipped),
        0.0,
    )
    return ll


def binomial_initialize(
    y: jnp.ndarray, weights: jnp.ndarray | None = None
) -> jnp.ndarray:
    """Initialize μ for binomial family.

    Uses the weighted formula from R's stats::binomial family:
        mustart <- (weights * y + 0.5) / (weights + 1)

    This avoids boundary values (0 or 1) while accounting for prior weights.
    When weights=1 (unweighted), this gives (y + 0.5) / 2.

    Args:
        y: Response values (n,), must be in [0, 1]
        weights: Optional prior weights (n,). Defaults to 1.0 for all observations.

    Returns:
        Initial mean values (n,)
    """
    if weights is None:
        weights = jnp.ones_like(y)
    # Match R's formula exactly: (n*y + 0.5) / (n + 1) where n = weights
    return (weights * y + 0.5) / (weights + 1)


def binomial_dispersion(y: jnp.ndarray, mu: jnp.ndarray, df_resid: int) -> float:
    """Dispersion parameter for binomial family.

    Fixed at 1.0 for binomial models.

    Args:
        y: Response values (n,)
        mu: Fitted mean values (n,)
        df_resid: Residual degrees of freedom (unused)

    Returns:
        Dispersion value (always 1.0)
    """
    return 1.0


# ============================================================================
# Poisson Family Functions
# ============================================================================


@jax.jit
def poisson_variance(mu: jnp.ndarray) -> jnp.ndarray:
    """Poisson variance function: V(μ) = μ.

    Args:
        mu: Mean values (n,), must be positive

    Returns:
        Variance values (n,)
    """
    return mu


@jax.jit
def poisson_deviance(y: jnp.ndarray, mu: jnp.ndarray) -> jnp.ndarray:
    """Poisson unit deviance: d(y, μ) = 2[y log(y/μ) - (y - μ)].

    Uses log-space arithmetic for numerical stability.

    Args:
        y: Response values (n,), must be non-negative
        mu: Fitted mean values (n,), must be positive

    Returns:
        Unit deviance values (n,)
    """
    mu_clipped = jnp.clip(mu, 1e-10, jnp.inf)

    # Use log-space: log(a/b) = log(a) - log(b)
    dev = jnp.where(
        y > 0,
        2 * (y * (jnp.log(y) - jnp.log(mu_clipped)) - (y - mu_clipped)),
        2 * mu_clipped,  # When y = 0: 2μ
    )
    return dev


@jax.jit
def poisson_loglik(y: jnp.ndarray, mu: jnp.ndarray) -> jnp.ndarray:
    """Poisson conditional log-likelihood (per observation).

    Computes log p(y|μ) = y*log(μ) - μ - log(y!).
    The log(y!) term uses log-gamma: log(Γ(y+1)) = log(y!).

    Uses numerical stability patterns similar to poisson_deviance.

    Args:
        y: Response values (n,), must be non-negative
        mu: Fitted mean values (n,), must be positive

    Returns:
        Per-observation log-likelihood values (n,), NOT summed
    """
    mu_clipped = jnp.clip(mu, 1e-10, jnp.inf)

    # log p(y|μ) = y*log(μ) - μ - log(Γ(y+1))
    ll = jnp.where(
        y > 0,
        y * jnp.log(mu_clipped) - mu_clipped - jsp.special.gammaln(y + 1),
        -mu_clipped,  # When y = 0: -μ (since log(0!) = 0)
    )
    return ll


def poisson_initialize(
    y: jnp.ndarray, weights: jnp.ndarray | None = None
) -> jnp.ndarray:
    """Initialize μ for Poisson family.

    Adds small value to avoid zero counts (matches R's poisson family).

    Args:
        y: Response values (n,), must be non-negative
        weights: Optional prior weights (n,). Unused for Poisson, included
            for API consistency with other families.

    Returns:
        Initial mean values (n,)
    """
    # R uses mustart <- y + 0.1 for Poisson
    return y + 0.1


def poisson_dispersion(y: jnp.ndarray, mu: jnp.ndarray, df_resid: int) -> float:
    """Dispersion parameter for Poisson family.

    Fixed at 1.0 for Poisson models (can estimate for quasi-Poisson).

    Args:
        y: Response values (n,)
        mu: Fitted mean values (n,)
        df_resid: Residual degrees of freedom (unused)

    Returns:
        Dispersion value (always 1.0)
    """
    return 1.0


# ============================================================================
# Student-t Family Functions (for robust regression)
# ============================================================================


@jax.jit
def tdist_variance(mu: jnp.ndarray) -> jnp.ndarray:
    """Student-t variance function: V(μ) = 1.

    Like Gaussian, the variance function is constant. The heavy-tailed
    behavior comes from the robust weights, not the variance function.

    Args:
        mu: Mean values (n,)

    Returns:
        Variance values (n,), all ones
    """
    return jnp.ones_like(mu)


def _make_tdist_deviance(df: int):
    """Create t-distribution deviance function with fixed df.

    The deviance for t-distribution is based on -2 * log-likelihood.
    For location-scale t-distribution: -2 * log(p(y|μ,σ,df))

    Args:
        df: Degrees of freedom for the t-distribution.

    Returns:
        JIT-compiled deviance function.
    """

    @jax.jit
    def tdist_deviance(y: jnp.ndarray, mu: jnp.ndarray) -> jnp.ndarray:
        """Student-t unit deviance.

        Uses the t-distribution density to compute deviance.
        Deviance = (df + 1) * log(1 + (y - μ)² / df)

        This is proportional to -2 * log(density) ignoring constants.

        Args:
            y: Response values (n,)
            mu: Fitted mean values (n,)

        Returns:
            Unit deviance values (n,)
        """
        residuals_sq = (y - mu) ** 2
        # Deviance contribution: (df + 1) * log(1 + r²/df)
        return (df + 1) * jnp.log(1 + residuals_sq / df)

    return tdist_deviance


def _make_tdist_loglik(df: int):
    """Create t-distribution log-likelihood function with fixed df.

    Args:
        df: Degrees of freedom for the t-distribution.

    Returns:
        JIT-compiled log-likelihood function.
    """

    @jax.jit
    def tdist_loglik(y: jnp.ndarray, mu: jnp.ndarray) -> jnp.ndarray:
        """Student-t conditional log-likelihood (per observation).

        Computes log p(y|μ, df) for standardized t-distribution (σ=1).
        log p = log(Γ((df+1)/2)) - log(Γ(df/2)) - 0.5*log(df*π)
                - ((df+1)/2) * log(1 + (y-μ)²/df)

        Args:
            y: Response values (n,)
            mu: Fitted mean values (n,)

        Returns:
            Per-observation log-likelihood values (n,), NOT summed
        """
        residuals_sq = (y - mu) ** 2
        # Log-likelihood of t-distribution (up to constant terms)
        # The constant terms involving Gamma functions cancel in optimization
        return -0.5 * (df + 1) * jnp.log(1 + residuals_sq / df)

    return tdist_loglik


def tdist_initialize(y: jnp.ndarray, weights: jnp.ndarray | None = None) -> jnp.ndarray:
    """Initialize μ for Student-t family.

    Uses y directly as the starting value (like Gaussian).

    Args:
        y: Response values (n,)
        weights: Optional prior weights (n,). Unused for t-distribution.

    Returns:
        Initial mean values (n,)
    """
    return y + 0.01 * jnp.std(y)


def tdist_dispersion(y: jnp.ndarray, mu: jnp.ndarray, df_resid: int) -> float:
    """Estimate dispersion (scale) parameter for Student-t family.

    Uses MAD (median absolute deviation) for robust scale estimation:
        σ = MAD / 0.6745

    where 0.6745 is the MAD of the standard normal distribution.

    Args:
        y: Response values (n,)
        mu: Fitted mean values (n,)
        df_resid: Residual degrees of freedom (unused for MAD)

    Returns:
        Dispersion estimate σ̂
    """
    residuals = y - mu
    mad = jnp.median(jnp.abs(residuals - jnp.median(residuals)))
    # Scale MAD to be consistent with standard deviation for normal
    scale = mad / 0.6745
    # Avoid zero scale
    return float(jnp.maximum(scale, 1e-10))


def _make_tdist_robust_weights(df: int):
    """Create t-distribution robust weights function with fixed df.

    Args:
        df: Degrees of freedom for the t-distribution.

    Returns:
        JIT-compiled robust weights function.
    """

    @jax.jit
    def tdist_robust_weights(
        y: jnp.ndarray, mu: jnp.ndarray, scale: float
    ) -> jnp.ndarray:
        """Compute robust weights for t-distribution IRLS.

        These weights downweight observations with large residuals:
            w_i = (df + 1) / (df + (r_i / σ)²)

        As df → ∞, weights → 1 (Gaussian behavior).
        For small df, outliers get strongly downweighted.

        Args:
            y: Response values (n,)
            mu: Fitted mean values (n,)
            scale: Scale parameter σ

        Returns:
            Robust weights (n,), values in (0, 1]
        """
        residuals_sq = ((y - mu) / (scale + 1e-10)) ** 2
        return (df + 1) / (df + residuals_sq)

    return tdist_robust_weights


# Placeholder functions for direct import (will be replaced by factory)
def tdist_deviance(y: jnp.ndarray, mu: jnp.ndarray) -> jnp.ndarray:
    """Placeholder - use tdist(df=...) factory to get proper function."""
    raise RuntimeError("Use tdist(df=...) factory to create t-distribution family")


def tdist_loglik(y: jnp.ndarray, mu: jnp.ndarray) -> jnp.ndarray:
    """Placeholder - use tdist(df=...) factory to get proper function."""
    raise RuntimeError("Use tdist(df=...) factory to create t-distribution family")


def tdist_robust_weights(y: jnp.ndarray, mu: jnp.ndarray, scale: float) -> jnp.ndarray:
    """Placeholder - use tdist(df=...) factory to get proper function."""
    raise RuntimeError("Use tdist(df=...) factory to create t-distribution family")


# ============================================================================
# Family Configuration
# ============================================================================


class Family(NamedTuple):
    """Family configuration for GLM fitting.

    All functions are pure JAX operations, enabling JIT compilation and
    automatic differentiation. This is a simple data container with no methods.

    Attributes:
        name: Family name (e.g., "gaussian", "binomial", "poisson", "tdist")
        link_name: Link function name (e.g., "identity", "logit", "log")
        link: Link function η = g(μ)
        link_inverse: Inverse link μ = g⁻¹(η)
        link_deriv: Link derivative dη/dμ
        variance: Variance function V(μ)
        deviance: Unit deviance function d(y, μ)
        loglik: Conditional log-likelihood function log p(y|μ)
        initialize: Initialization function for starting μ values.
            Signature: (y, weights=None) -> mu_init. The weights parameter
            is optional and only used by binomial family.
        dispersion: Dispersion parameter estimation function
        df: Degrees of freedom for t-distribution family (None for others)
        robust_weights: Optional function for residual-based weights (t-dist).
            Signature: (y, mu, scale) -> weights. Returns multiplicative
            weights that downweight outliers. None for standard families.
    """

    name: str
    link_name: str
    link: Callable[[jnp.ndarray], jnp.ndarray]
    link_inverse: Callable[[jnp.ndarray], jnp.ndarray]
    link_deriv: Callable[[jnp.ndarray], jnp.ndarray]
    variance: Callable[[jnp.ndarray], jnp.ndarray]
    deviance: Callable[[jnp.ndarray, jnp.ndarray], jnp.ndarray]
    loglik: Callable[[jnp.ndarray, jnp.ndarray], jnp.ndarray]
    initialize: Callable[..., jnp.ndarray]  # (y, weights=None) -> mu_init
    dispersion: Callable[[jnp.ndarray, jnp.ndarray, int], float]
    df: int | None = None
    robust_weights: Callable[[jnp.ndarray, jnp.ndarray, float], jnp.ndarray] | None = (
        None
    )


# ============================================================================
# Family Factory Functions (public API)
# ============================================================================


def gaussian(link: str | None = None) -> Family:
    """Create Gaussian family with identity link.

    The Gaussian family is appropriate for continuous response data with
    constant variance. This is equivalent to ordinary least squares (OLS)
    when using the identity link.

    Args:
        link: Link function name. Only "identity" supported (canonical).
            Defaults to "identity" if None.

    Returns:
        Gaussian family configuration

    Raises:
        ValueError: If link is not None or "identity"

    Examples:
        >>> fam = gaussian()
        >>> fam.name
        'gaussian'
        >>> fam.link_name
        'identity'
    """
    if link is None or link == "identity":
        return Family(
            name="gaussian",
            link_name="identity",
            link=identity_link,
            link_inverse=identity_link_inverse,
            link_deriv=identity_link_deriv,
            variance=gaussian_variance,
            deviance=gaussian_deviance,
            loglik=gaussian_loglik,
            initialize=gaussian_initialize,
            dispersion=gaussian_dispersion,
        )
    else:
        raise ValueError(
            f"Invalid link '{link}' for gaussian family. Supported links: 'identity'"
        )


def binomial(link: str | None = None) -> Family:
    """Create binomial family for binary or proportion data.

    The binomial family is appropriate for binary outcomes (0/1) or
    proportions (successes/trials). Commonly used for logistic and
    probit regression.

    Args:
        link: Link function name. Options are "logit" (default) or "probit".
            Defaults to "logit" if None.

    Returns:
        Binomial family configuration

    Raises:
        ValueError: If link is not None, "logit", or "probit"

    Examples:
        >>> # Logistic regression (default)
        >>> fam = binomial()
        >>> fam.link_name
        'logit'

        >>> # Probit regression
        >>> fam = binomial("probit")
        >>> fam.link_name
        'probit'
    """
    if link is None or link == "logit":
        return Family(
            name="binomial",
            link_name="logit",
            link=logit_link,
            link_inverse=logit_link_inverse,
            link_deriv=logit_link_deriv,
            variance=binomial_variance,
            deviance=binomial_deviance,
            loglik=binomial_loglik,
            initialize=binomial_initialize,
            dispersion=binomial_dispersion,
        )
    elif link == "probit":
        return Family(
            name="binomial",
            link_name="probit",
            link=probit_link,
            link_inverse=probit_link_inverse,
            link_deriv=probit_link_deriv,
            variance=binomial_variance,
            deviance=binomial_deviance,
            loglik=binomial_loglik,
            initialize=binomial_initialize,
            dispersion=binomial_dispersion,
        )
    else:
        raise ValueError(
            f"Invalid link '{link}' for binomial family. "
            f"Supported links: 'logit', 'probit'"
        )


def poisson(link: str | None = None) -> Family:
    """Create Poisson family for count data.

    The Poisson family is appropriate for count data where the variance
    equals the mean. Commonly used for modeling event counts, frequencies,
    or rates.

    Args:
        link: Link function name. Only "log" supported (canonical).
            Defaults to "log" if None.

    Returns:
        Poisson family configuration

    Raises:
        ValueError: If link is not None or "log"

    Examples:
        >>> fam = poisson()
        >>> fam.name
        'poisson'
        >>> fam.link_name
        'log'
    """
    if link is None or link == "log":
        return Family(
            name="poisson",
            link_name="log",
            link=log_link,
            link_inverse=log_link_inverse,
            link_deriv=log_link_deriv,
            variance=poisson_variance,
            deviance=poisson_deviance,
            loglik=poisson_loglik,
            initialize=poisson_initialize,
            dispersion=poisson_dispersion,
        )
    else:
        raise ValueError(
            f"Invalid link '{link}' for poisson family. Supported links: 'log'"
        )


def tdist(df: int, link: str | None = None) -> Family:
    """Create Student-t family for robust regression.

    The Student-t family provides robust regression by using a t-distribution
    for the errors instead of Gaussian. This downweights outliers through
    iteratively reweighted least squares (IRLS).

    The t-distribution has heavier tails than the Gaussian:
    - df=1: Cauchy distribution (very heavy tails)
    - df=4-5: Moderately heavy tails (common for robust regression)
    - df→∞: Converges to Gaussian

    For automatic df based on residual degrees of freedom (n - p), use
    `family="tdist"` in glm() and df will be set at fit() time.

    Args:
        df: Degrees of freedom. Must be > 0. Typically set to n - p
            (residual degrees of freedom) for proper inference.
        link: Link function name. Only "identity" supported.
            Defaults to "identity" if None.

    Returns:
        Student-t family configuration with robust weights.

    Raises:
        ValueError: If df <= 0 or link is not "identity".

    Examples:
        >>> # Robust regression with df=10
        >>> fam = tdist(df=10)
        >>> fam.name
        'tdist'

        >>> # In practice, use with glm (df set automatically)
        >>> model = glm("y ~ x", data=df, family="tdist").fit()
    """
    if df <= 0:
        raise ValueError(f"df must be positive, got {df}")

    if link is not None and link != "identity":
        raise ValueError(
            f"Invalid link '{link}' for tdist family. Supported links: 'identity'"
        )

    # Create df-specific functions using closures
    deviance_fn = _make_tdist_deviance(df)
    loglik_fn = _make_tdist_loglik(df)
    robust_weights_fn = _make_tdist_robust_weights(df)

    return Family(
        name="tdist",
        link_name="identity",
        link=identity_link,
        link_inverse=identity_link_inverse,
        link_deriv=identity_link_deriv,
        variance=tdist_variance,
        deviance=deviance_fn,
        loglik=loglik_fn,
        initialize=tdist_initialize,
        dispersion=tdist_dispersion,
        df=df,
        robust_weights=robust_weights_fn,
    )
