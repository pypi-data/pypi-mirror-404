"""GLM IRLS fitting algorithm.

This module implements the Iteratively Reweighted Least Squares (IRLS) algorithm
for GLM fitting. The algorithm supports both JAX and NumPy backends:

- JAX backend: Uses lax.while_loop for JIT-compiled, efficient iteration
- NumPy backend: Uses regular Python loops for Pyodide compatibility

All functions are designed to work with Family objects from bossanova.ops.family.
"""

import numpy as np

from bossanova._backend import get_backend
from bossanova.ops.family import Family

__all__ = [
    "fit_glm_irls",
]


def fit_glm_irls(
    y: np.ndarray,
    X: np.ndarray,
    family: Family,
    weights: np.ndarray | None = None,
    max_iter: int = 25,
    tol: float = 1e-8,
) -> dict:
    """Fit GLM using IRLS algorithm.

    Implements Iteratively Reweighted Least Squares for generalized linear
    models. The algorithm iterates until convergence (relative deviance change
    < tol) or max_iter is reached.

    The core fitting loop is JIT-compiled for efficiency. All family-specific
    operations (link, variance, deviance) are pure JAX functions from the
    Family object.

    Args:
        y: Response values (n,)
        X: Design matrix (n, p)
        family: Family object with link, variance, and deviance functions
        weights: Prior observation weights (n,) or None for equal weights
        max_iter: Maximum IRLS iterations (default: 25)
        tol: Convergence tolerance for relative deviance change (default: 1e-8)

    Returns:
        Dictionary with keys:
            - coef: Coefficient estimates (p,)
            - vcov: Variance-covariance matrix (p, p)
            - dispersion: Dispersion parameter estimate
            - fitted: Fitted values μ on response scale (n,)
            - linear_predictor: Linear predictor η on link scale (n,)
            - residuals: Response residuals y - μ (n,)
            - deviance: Residual deviance
            - null_deviance: Null model deviance
            - df_residual: Residual degrees of freedom
            - aic: Akaike Information Criterion
            - bic: Bayesian Information Criterion
            - loglik: Log-likelihood
            - converged: True if converged, False otherwise
            - n_iter: Number of iterations performed
            - has_separation: Separation detection (binomial only, None otherwise)
            - irls_weights: Final IRLS weights (n,)

    Notes:
        - Uses while_loop for early stopping on convergence
        - Clips IRLS weights to [1e-10, 1e10] for numerical stability
        - Clips μ values based on family type (binomial: [1e-10, 1-1e-10],
          poisson: [1e-10, inf])
        - Adds small regularization (1e-10) to diagonal of XtWX
        - Separation detection checks if fitted probabilities are extremely
          close to 0 or 1 (< 1e-6 or > 1-1e-6) for binomial models
    """
    # Dispatch to backend-specific implementation
    # Use NumPy for families with robust weights (e.g., t-distribution)
    # since JAX JIT doesn't easily support the residual-dependent weights
    backend = get_backend()
    if backend == "jax" and family.robust_weights is None:
        return _fit_glm_irls_jax(y, X, family, weights, max_iter, tol)
    else:
        return _fit_glm_irls_numpy(y, X, family, weights, max_iter, tol)


# =============================================================================
# JAX Backend Implementation
# =============================================================================


def _fit_glm_irls_jax(
    y: np.ndarray,
    X: np.ndarray,
    family: Family,
    weights: np.ndarray | None = None,
    max_iter: int = 25,
    tol: float = 1e-8,
) -> dict:
    """JAX-optimized IRLS implementation using lax.while_loop."""
    import jax.numpy as jnp

    n, p = X.shape

    # Convert to JAX arrays
    X_jax = jnp.array(X)
    y_jax = jnp.array(y)

    # Handle weights
    if weights is None:
        prior_weights = jnp.ones(n)
    else:
        prior_weights = jnp.array(weights)

    # Initialize μ and η (pass weights for binomial family)
    mu_init = family.initialize(y_jax, prior_weights)
    eta_init = family.link(mu_init)

    # JIT-compiled core fitting loop
    result = _fit_glm_irls_jit(
        X_jax, y_jax, mu_init, eta_init, prior_weights, family, max_iter, tol, p
    )

    mu = result["mu"]
    eta = result["eta"]
    coef = result["coef"]
    deviance = result["deviance"]
    converged = bool(result["converged"])
    n_iter = int(result["n_iter"])
    XtWX = result["XtWX"]
    irls_weights = result["irls_weights"]

    # Compute final outputs
    residuals = y_jax - mu
    df_residual = n - p

    # Dispersion parameter
    dispersion = family.dispersion(y_jax, mu, df_residual)

    # Variance-covariance matrix
    XtWX_inv = jnp.linalg.inv(XtWX + 1e-10 * jnp.eye(p))
    vcov = dispersion * XtWX_inv

    # Null deviance (intercept-only model)
    null_deviance = _compute_null_deviance_jax(y_jax, family)

    # Log-likelihood, AIC, BIC
    loglik = _compute_loglik_jax(y_jax, mu, deviance, dispersion, family, n)
    aic = _compute_aic(loglik, p, family)
    bic = _compute_bic_jax(loglik, p, n)

    # Separation detection (binomial only)
    has_separation = None
    if family.name == "binomial":
        has_separation = bool(jnp.any((mu < 1e-6) | (mu > 1 - 1e-6)))

    return {
        "coef": np.array(coef),
        "vcov": np.array(vcov),
        "dispersion": float(dispersion),
        "fitted": np.array(mu),
        "linear_predictor": np.array(eta),
        "residuals": np.array(residuals),
        "deviance": float(deviance),
        "null_deviance": float(null_deviance),
        "df_residual": df_residual,
        "aic": float(aic),
        "bic": float(bic),
        "loglik": float(loglik),
        "converged": converged,
        "n_iter": n_iter,
        "has_separation": has_separation,
        "irls_weights": np.array(irls_weights),
        "XtWX_inv": np.array(XtWX_inv),
    }


# Cache for JIT-compiled function
_jit_cache: dict = {}


def _get_jit_fn():
    """Lazily create and return the JIT-compiled IRLS function."""
    if "jit_fn" not in _jit_cache:
        import jax
        import jax.lax as lax
        import jax.numpy as jnp

        def _irls_core(
            X, y, mu_init, eta_init, prior_weights, family, max_iter, tol, p
        ):
            """IRLS core loop using lax.while_loop."""

            def cond_fn(state):
                """Return True to continue looping."""
                _, _, deviance_current, iteration, _, _, _, deviance_prev = state
                continue_iterating = iteration < max_iter

                def check_convergence():
                    dev_change = jnp.abs(deviance_current - deviance_prev)
                    rel_change = dev_change / (jnp.abs(deviance_prev) + 1e-10)
                    return rel_change >= tol

                should_continue = lax.cond(
                    jnp.isinf(deviance_prev),
                    lambda: True,
                    check_convergence,
                )
                return continue_iterating & should_continue

            def body_fn(state):
                """Single IRLS iteration."""
                mu, eta, deviance_current, iteration, _, _, _, _ = state

                deta_dmu = family.link_deriv(mu)
                var_mu = family.variance(mu)
                working_response = eta + (y - mu) * deta_dmu

                irls_weights = prior_weights / (var_mu * deta_dmu**2 + 1e-10)
                irls_weights = jnp.clip(irls_weights, 1e-10, 1e10)

                XtWX = jnp.einsum("ni,n,nj->ij", X, irls_weights, X)
                XtWz = jnp.einsum("ni,n,n->i", X, irls_weights, working_response)

                XtWX_reg = XtWX + 1e-10 * jnp.eye(p)
                L = jnp.linalg.cholesky(XtWX_reg)
                coef = jnp.linalg.solve(L.T, jnp.linalg.solve(L, XtWz))

                eta_new = X @ coef
                mu_new = family.link_inverse(eta_new)

                if family.name == "binomial":
                    mu_new = jnp.clip(mu_new, 1e-10, 1 - 1e-10)
                elif family.name == "poisson":
                    mu_new = jnp.clip(mu_new, 1e-10, jnp.inf)

                dev_contributions = family.deviance(y, mu_new)
                deviance_new = jnp.sum(dev_contributions)

                return (
                    mu_new,
                    eta_new,
                    deviance_new,
                    iteration + 1,
                    coef,
                    XtWX,
                    irls_weights,
                    deviance_current,
                )

            init_state = (
                mu_init,
                eta_init,
                jnp.inf,
                0,
                jnp.zeros(p),
                jnp.eye(p),
                jnp.ones(len(y)),
                jnp.inf,
            )

            final_state = lax.while_loop(cond_fn, body_fn, init_state)

            (
                mu_final,
                eta_final,
                deviance_final,
                n_iter,
                coef_final,
                XtWX_final,
                weights_final,
                _,
            ) = final_state

            converged = n_iter < max_iter

            return {
                "mu": mu_final,
                "eta": eta_final,
                "coef": coef_final,
                "deviance": deviance_final,
                "converged": converged,
                "n_iter": n_iter,
                "XtWX": XtWX_final,
                "irls_weights": weights_final,
            }

        _jit_cache["jit_fn"] = jax.jit(
            _irls_core, static_argnames=("family", "max_iter", "p")
        )
    return _jit_cache["jit_fn"]


def _fit_glm_irls_jit(X, y, mu_init, eta_init, prior_weights, family, max_iter, tol, p):
    """Wrapper that calls the lazily-created JIT function."""
    jit_fn = _get_jit_fn()
    return jit_fn(X, y, mu_init, eta_init, prior_weights, family, max_iter, tol, p)


def _compute_null_deviance_jax(y, family):
    """Compute null deviance for intercept-only model (JAX version)."""
    import jax.numpy as jnp

    if family.name == "gaussian":
        null_mu = jnp.mean(y) * jnp.ones_like(y)
    elif family.name == "binomial":
        y_mean = jnp.mean(y)
        null_mu = jnp.clip(y_mean, 1e-10, 1 - 1e-10) * jnp.ones_like(y)
    elif family.name == "poisson":
        null_mu = jnp.mean(y) * jnp.ones_like(y)
    else:
        null_mu = jnp.mean(y) * jnp.ones_like(y)

    null_dev_contributions = family.deviance(y, null_mu)
    return jnp.sum(null_dev_contributions)


def _compute_loglik_jax(y, mu, deviance, dispersion, family, n):
    """Compute log-likelihood (JAX version)."""
    import jax.numpy as jnp
    import jax.scipy as jsp

    if family.name == "gaussian":
        mle_dispersion = deviance / n
        loglik = -0.5 * n * (jnp.log(2 * jnp.pi) + jnp.log(mle_dispersion) + 1)
    elif family.name == "binomial":
        mu_clipped = jnp.clip(mu, 1e-10, 1 - 1e-10)
        loglik = jnp.sum(y * jnp.log(mu_clipped) + (1 - y) * jnp.log(1 - mu_clipped))
    elif family.name == "poisson":
        mu_clipped = jnp.clip(mu, 1e-10, jnp.inf)
        loglik = jnp.sum(
            y * jnp.log(mu_clipped) - mu_clipped - jsp.special.gammaln(y + 1)
        )
    else:
        loglik = -deviance / (2 * dispersion)

    return loglik


def _compute_aic(loglik, p, family):
    """Compute AIC (backend-agnostic)."""
    if family.name == "gaussian":
        # +1 for scale parameter
        return -2 * loglik + 2 * (p + 1)
    elif family.name == "tdist":
        # +1 for scale parameter (df is fixed, not estimated)
        return -2 * loglik + 2 * (p + 1)
    else:
        return -2 * loglik + 2 * p


def _compute_bic_jax(loglik, p, n):
    """Compute BIC (JAX version)."""
    import jax.numpy as jnp

    return -2 * loglik + jnp.log(n) * p


# =============================================================================
# NumPy Backend Implementation
# =============================================================================


def _fit_glm_irls_numpy(
    y: np.ndarray,
    X: np.ndarray,
    family: Family,
    weights: np.ndarray | None = None,
    max_iter: int = 25,
    tol: float = 1e-8,
) -> dict:
    """NumPy IRLS implementation using regular Python loops."""
    n, p = X.shape

    # Handle weights
    if weights is None:
        prior_weights = np.ones(n)
    else:
        prior_weights = np.asarray(weights)

    # Initialize μ and η
    mu = family.initialize(y, prior_weights)
    eta = family.link(mu)

    # Check if family has robust weights (e.g., t-distribution)
    has_robust_weights = family.robust_weights is not None

    # Initial scale estimate for robust families (MAD-based)
    if has_robust_weights:
        residuals = y - mu
        scale = np.median(np.abs(residuals - np.median(residuals))) / 0.6745
        scale = max(scale, 1e-10)
    else:
        scale = 1.0

    # Initial deviance
    deviance_prev = np.inf
    converged = False

    # IRLS iteration
    for iteration in range(max_iter):
        # Link derivative and variance function
        deta_dmu = family.link_deriv(mu)
        var_mu = family.variance(mu)

        # Working response
        working_response = eta + (y - mu) * deta_dmu

        # IRLS weights (clip for stability)
        irls_weights = prior_weights / (var_mu * deta_dmu**2 + 1e-10)

        # Apply robust weights if available (t-distribution)
        if has_robust_weights and family.robust_weights is not None:
            robust_w = family.robust_weights(y, mu, scale)
            irls_weights = irls_weights * robust_w

        irls_weights = np.clip(irls_weights, 1e-10, 1e10)

        # Weighted least squares
        XtWX = np.einsum("ni,n,nj->ij", X, irls_weights, X)
        XtWz = np.einsum("ni,n,n->i", X, irls_weights, working_response)

        # Solve via Cholesky with small regularization
        XtWX_reg = XtWX + 1e-10 * np.eye(p)
        L = np.linalg.cholesky(XtWX_reg)
        coef = np.linalg.solve(L.T, np.linalg.solve(L, XtWz))

        # Update predictions
        eta = X @ coef
        mu = family.link_inverse(eta)

        # Clip μ based on family type
        if family.name == "binomial":
            mu = np.clip(mu, 1e-10, 1 - 1e-10)
        elif family.name == "poisson":
            mu = np.clip(mu, 1e-10, np.inf)

        # Update scale estimate for robust families
        if has_robust_weights:
            residuals = y - mu
            scale = np.median(np.abs(residuals - np.median(residuals))) / 0.6745
            scale = max(scale, 1e-10)

        # Compute deviance
        dev_contributions = family.deviance(y, mu)
        deviance = np.sum(dev_contributions)

        # Check convergence
        if iteration > 0:
            dev_change = np.abs(deviance - deviance_prev)
            rel_change = dev_change / (np.abs(deviance_prev) + 1e-10)
            if rel_change < tol:
                converged = True
                break

        deviance_prev = deviance

    n_iter = iteration + 1

    # Compute final outputs
    residuals = y - mu
    df_residual = n - p

    # Dispersion parameter
    dispersion = family.dispersion(y, mu, df_residual)

    # Variance-covariance matrix
    XtWX_inv = np.linalg.inv(XtWX + 1e-10 * np.eye(p))
    vcov = dispersion * XtWX_inv

    # Null deviance
    null_deviance = _compute_null_deviance_numpy(y, family)

    # Log-likelihood, AIC, BIC
    loglik = _compute_loglik_numpy(y, mu, deviance, dispersion, family, n)
    aic = _compute_aic(loglik, p, family)
    bic = _compute_bic_numpy(loglik, p, n)

    # Separation detection (binomial only)
    has_separation = None
    if family.name == "binomial":
        has_separation = bool(np.any((mu < 1e-6) | (mu > 1 - 1e-6)))

    return {
        "coef": coef,
        "vcov": vcov,
        "dispersion": float(dispersion),
        "fitted": mu,
        "linear_predictor": eta,
        "residuals": residuals,
        "deviance": float(deviance),
        "null_deviance": float(null_deviance),
        "df_residual": df_residual,
        "aic": float(aic),
        "bic": float(bic),
        "loglik": float(loglik),
        "converged": converged,
        "n_iter": n_iter,
        "has_separation": has_separation,
        "irls_weights": irls_weights,
        "XtWX_inv": XtWX_inv,
    }


def _compute_null_deviance_numpy(y, family):
    """Compute null deviance for intercept-only model (NumPy version)."""
    if family.name == "gaussian":
        null_mu = np.mean(y) * np.ones_like(y)
    elif family.name == "binomial":
        y_mean = np.mean(y)
        null_mu = np.clip(y_mean, 1e-10, 1 - 1e-10) * np.ones_like(y)
    elif family.name == "poisson":
        null_mu = np.mean(y) * np.ones_like(y)
    elif family.name == "tdist":
        # For t-distribution, use median for robustness
        null_mu = np.median(y) * np.ones_like(y)
    else:
        null_mu = np.mean(y) * np.ones_like(y)

    null_dev_contributions = family.deviance(y, null_mu)
    return np.sum(null_dev_contributions)


def _compute_loglik_numpy(y, mu, deviance, dispersion, family, n):
    """Compute log-likelihood (NumPy version)."""
    from scipy import special as sp_special

    if family.name == "gaussian":
        mle_dispersion = deviance / n
        loglik = -0.5 * n * (np.log(2 * np.pi) + np.log(mle_dispersion) + 1)
    elif family.name == "binomial":
        mu_clipped = np.clip(mu, 1e-10, 1 - 1e-10)
        loglik = np.sum(y * np.log(mu_clipped) + (1 - y) * np.log(1 - mu_clipped))
    elif family.name == "poisson":
        mu_clipped = np.clip(mu, 1e-10, np.inf)
        loglik = np.sum(y * np.log(mu_clipped) - mu_clipped - sp_special.gammaln(y + 1))
    elif family.name == "tdist":
        # t-distribution log-likelihood
        df = family.df
        residuals_sq = (y - mu) ** 2 / (dispersion + 1e-10)
        # log p(y|mu, sigma, df) = log(Gamma((df+1)/2)) - log(Gamma(df/2))
        #                        - 0.5*log(df*pi*sigma^2)
        #                        - ((df+1)/2)*log(1 + r^2/(df*sigma^2))
        loglik = np.sum(
            sp_special.gammaln((df + 1) / 2)
            - sp_special.gammaln(df / 2)
            - 0.5 * np.log(df * np.pi * dispersion)
            - 0.5 * (df + 1) * np.log(1 + residuals_sq / df)
        )
    else:
        loglik = -deviance / (2 * dispersion)

    return loglik


def _compute_bic_numpy(loglik, p, n):
    """Compute BIC (NumPy version)."""
    return -2 * loglik + np.log(n) * p
