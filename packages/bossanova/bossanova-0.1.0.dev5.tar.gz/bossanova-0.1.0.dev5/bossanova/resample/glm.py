"""GLM resampling with IRLS refitting.

This module provides bootstrap procedures for generalized linear models
with support for both JAX (accelerated) and NumPy (Pyodide-compatible) backends.
Unlike lm bootstrap which uses the hat-matrix trick, GLM bootstrap requires
full model refitting via IRLS for each sample.

Performance: JAX backend uses parallel processing. NumPy backend uses
Python loops with optional joblib parallelization.
"""

from typing import Any, Literal

import numpy as np
from joblib import Parallel, delayed
from tqdm.auto import tqdm

from bossanova._backend import get_backend
from bossanova.ops.family import Family
from bossanova.ops.glm_fit import fit_glm_irls
from bossanova.ops.rng import RNG
from bossanova.resample.core import (
    bootstrap_ci_basic,
    bootstrap_ci_bca,
    bootstrap_ci_percentile,
    generate_kfold_indices,
    generate_loo_indices,
)
from bossanova.resample.results import BootstrapResult, CVResult, PermutationResult

# Type alias for arrays (works with both JAX and NumPy)
Array = Any

__all__ = [
    "Array",
    "simulate_response",
    "glm_bootstrap",
    "glm_permute",
    "glm_cv",
]


# =============================================================================
# Response Simulation (for parametric bootstrap)
# =============================================================================


def _simulate_gaussian(
    rng: RNG,
    mu: Array,
    dispersion: float,
) -> Array:
    """Simulate Gaussian response from fitted values.

    Args:
        rng: RNG object for random sampling.
        mu: Fitted values (n,).
        dispersion: Dispersion parameter (φ). For Gaussian family, φ = σ² where σ is the
            residual standard error. Related to sigma by: σ = √dispersion.

    Returns:
        Simulated response (n,).
    """
    mu_np = np.asarray(mu)
    sigma = np.sqrt(dispersion)
    noise = rng.normal(shape=mu_np.shape)
    return mu_np + sigma * np.asarray(noise)


def _simulate_binomial(
    rng: RNG,
    mu: Array,
    weights: Array | None = None,
) -> Array:
    """Simulate binomial response from fitted probabilities.

    For standard Bernoulli trials (weights=1), samples 0/1.
    For binomial with n trials, samples proportion.

    Args:
        rng: RNG object for random sampling.
        mu: Fitted probabilities (n,), must be in (0, 1).
        weights: Number of trials per observation. If None, uses 1 (Bernoulli).

    Returns:
        Simulated response (n,) as proportions in [0, 1].
    """
    mu_np = np.asarray(mu)
    n = mu_np.shape[0]

    # Sample counts from binomial using uniform comparison (Bernoulli case)
    u = rng.uniform(shape=(n,))
    counts = (np.asarray(u) < mu_np).astype(np.float64)

    return counts


def _simulate_poisson(
    rng: RNG,
    mu: Array,
) -> Array:
    """Simulate Poisson response from fitted rates.

    Args:
        rng: RNG object for random sampling.
        mu: Fitted rates (n,), must be positive.

    Returns:
        Simulated response (n,) as counts.
    """
    mu_np = np.asarray(mu)
    return np.asarray(rng.poisson(mu_np)).astype(np.float64)


def simulate_response(
    rng: RNG,
    mu: Array,
    family: Family,
    dispersion: float = 1.0,
    weights: Array | None = None,
) -> Array:
    """Simulate response from GLM fitted values.

    Dispatches to family-specific simulation functions.

    Args:
        rng: RNG object for random sampling.
        mu: Fitted values on response scale (n,).
        family: GLM family object.
        dispersion: Dispersion parameter (φ). For Gaussian family, dispersion = σ² where σ
            is the residual standard error (related to lm's sigma by: σ = √dispersion).
            For other families, dispersion is typically fixed at 1.0.
        weights: Prior weights (only used for binomial trials).

    Returns:
        Simulated response (n,).

    Raises:
        ValueError: If family is not supported.
    """
    if family.name == "gaussian":
        return _simulate_gaussian(rng, mu, dispersion)
    elif family.name == "binomial":
        return _simulate_binomial(rng, mu, weights)
    elif family.name == "poisson":
        return _simulate_poisson(rng, mu)
    else:
        raise ValueError(f"Unsupported family: {family.name}")


# =============================================================================
# GLM Bootstrap
# =============================================================================


def _glm_bootstrap_single_iteration(
    rng: RNG,
    X_np: np.ndarray,
    y_np: np.ndarray,
    family: Family,
    fitted_np: np.ndarray,
    dispersion: float,
    weights_np: np.ndarray | None,
    boot_type: str,
    max_iter: int,
    tol: float,
    n: int,
    p: int,
) -> np.ndarray:
    """Execute a single GLM bootstrap iteration.

    This is a standalone function (not a closure) to enable joblib parallelization.

    Args:
        rng: RNG object for this iteration.
        X_np: Design matrix as numpy array (n, p).
        y_np: Response vector as numpy array (n,).
        family: GLM family object.
        fitted_np: Fitted values as numpy array (n,).
        dispersion: Dispersion parameter.
        weights_np: Prior weights as numpy array or None.
        boot_type: "case" or "parametric".
        max_iter: Maximum IRLS iterations.
        tol: Convergence tolerance.
        n: Number of observations.
        p: Number of coefficients.

    Returns:
        Bootstrap coefficient estimates (p,), or NaN array if failed.
    """
    try:
        if boot_type == "case":
            # Case bootstrap: resample (X, y) pairs
            boot_idx = np.asarray(rng.choice(n, shape=(n,), replace=True))
            X_boot = X_np[boot_idx]
            y_boot = y_np[boot_idx]
            weights_boot = weights_np[boot_idx] if weights_np is not None else None

            result = fit_glm_irls(y_boot, X_boot, family, weights_boot, max_iter, tol)

        else:  # parametric
            # Parametric bootstrap: simulate from fitted model
            y_boot = simulate_response(
                rng,
                fitted_np,
                family,
                dispersion,
                weights_np,
            )

            result = fit_glm_irls(y_boot, X_np, family, weights_np, max_iter, tol)

        if result["converged"]:
            return result["coef"]
        else:
            # Non-convergence: return NaN
            return np.full(p, np.nan)

    except Exception:
        # Numerical failure: return NaN
        return np.full(p, np.nan)


def glm_bootstrap(
    X: Array,
    y: Array,
    X_names: list[str],
    family: Family,
    fitted: Array,
    dispersion: float,
    weights: Array | None = None,
    n_boot: int = 999,
    seed: int | None = None,
    boot_type: Literal["case", "parametric"] = "case",
    ci_type: Literal["percentile", "basic", "bca"] = "percentile",
    level: float = 0.95,
    max_iter: int = 25,
    tol: float = 1e-8,
    verbose: bool = False,
    n_jobs: int = 1,
) -> BootstrapResult:
    """Bootstrap inference for GLM coefficients.

    Each bootstrap iteration requires a full GLM fit via IRLS, making this
    more computationally intensive than lm bootstrap.

    Bootstrap types:
    - case: Resample (X, y) pairs with replacement. Robust to model
        misspecification and heteroscedasticity.
    - parametric: Simulate y* from fitted μ̂ using the family distribution,
        then refit. Assumes the fitted model is correct.

    Note:
        Residual bootstrap is not available for GLM because GLMs have
        heteroscedastic errors by design (variance is a function of the mean).
        The residual bootstrap assumes homoscedastic errors, making it
        inappropriate for GLM. Use case bootstrap for robustness or parametric
        bootstrap when the model is correctly specified.

    Args:
        X: Design matrix, shape (n, p).
        y: Response vector, shape (n,).
        X_names: Coefficient names.
        family: GLM family object (gaussian, binomial, or poisson).
        fitted: Fitted values from original model, shape (n,).
        dispersion: Dispersion parameter (φ) from original fit. For Gaussian family,
            dispersion = σ² where σ is the residual standard error (related to lm's sigma
            by: σ = √dispersion). For other families, typically fixed at 1.0.
        weights: Prior observation weights (n,) or None.
        n_boot: Number of bootstrap samples.
        seed: Random seed for reproducibility.
        boot_type: Type of bootstrap: "case" or "parametric".
        ci_type: Confidence interval type: "percentile", "basic", or "bca".
        level: Confidence level (e.g., 0.95 for 95% CI).
        max_iter: Maximum IRLS iterations for each refit.
        tol: Convergence tolerance for IRLS.
        verbose: If True, show tqdm progress bar.
        n_jobs: Number of parallel jobs. Default 1 (sequential). Use -1 for all cores.

    Returns:
        BootstrapResult with observed stats, bootstrap samples, and CIs.

    Raises:
        ValueError: If boot_type is not "case" or "parametric".
        ValueError: If ci_type is not "percentile", "basic", or "bca".

    Examples:
        >>> from bossanova.ops.family import binomial
        >>> family = binomial()
        >>> result = glm_bootstrap(
        ...     X, y, ["Intercept", "x"], family,
        ...     fitted=fitted_vals, dispersion=1.0,
        ...     n_boot=999, boot_type="case", n_jobs=4
        ... )
        >>> print(result.ci)
    """
    # Input validation
    if boot_type not in ("case", "parametric"):
        raise ValueError(f"boot_type must be 'case' or 'parametric', got {boot_type}")
    if ci_type not in ("percentile", "basic", "bca"):
        raise ValueError(
            f"ci_type must be 'percentile', 'basic', or 'bca', got {ci_type}"
        )

    # Convert to numpy arrays
    X_np = np.asarray(X)
    y_np = np.asarray(y)
    fitted_np = np.asarray(fitted)
    n, p = X_np.shape

    if weights is not None:
        weights_np = np.asarray(weights)
    else:
        weights_np = None

    rng = RNG.from_seed(seed)

    # Get observed coefficients from original fit
    result_obs = fit_glm_irls(y_np, X_np, family, weights_np, max_iter, tol)
    coef_obs = result_obs["coef"]

    # Generate all RNG keys upfront
    keys = rng.split(n_boot)

    # Shared iteration arguments
    iter_args = {
        "X_np": X_np,
        "y_np": y_np,
        "family": family,
        "fitted_np": fitted_np,
        "dispersion": dispersion,
        "weights_np": weights_np,
        "boot_type": boot_type,
        "max_iter": max_iter,
        "tol": tol,
        "n": n,
        "p": p,
    }

    # Bootstrap iterations with optional parallelization
    if n_jobs == 1:
        # Sequential execution with tqdm progress bar
        boot_samples_list = []
        for i in tqdm(range(n_boot), desc="Bootstrap", disable=not verbose):
            result = _glm_bootstrap_single_iteration(rng=keys[i], **iter_args)
            boot_samples_list.append(result)
    else:
        # Parallel execution with joblib
        if verbose:
            print(f"Running {n_boot} bootstrap iterations with {n_jobs} workers...")
        boot_samples_list = Parallel(n_jobs=n_jobs, return_as="generator")(
            delayed(_glm_bootstrap_single_iteration)(rng=keys[i], **iter_args)
            for i in range(n_boot)
        )
        # Wrap generator with tqdm for progress
        boot_samples_list = list(
            tqdm(boot_samples_list, total=n_boot, desc="Bootstrap", disable=not verbose)
        )

    # Count failures
    n_failed = sum(1 for coef in boot_samples_list if np.any(np.isnan(coef)))

    # Stack bootstrap samples
    boot_samples = np.stack(boot_samples_list, axis=0)

    # Warn if many failures
    if n_failed > n_boot * 0.1:
        import warnings

        warnings.warn(
            f"Bootstrap: {n_failed}/{n_boot} iterations failed to converge. "
            f"Consider increasing max_iter or checking data quality.",
            RuntimeWarning,
        )

    # Compute confidence intervals (excluding NaN samples)
    valid_mask = ~np.any(np.isnan(boot_samples), axis=1)
    boot_samples_valid = boot_samples[valid_mask]

    if ci_type == "percentile":
        ci_lower, ci_upper = bootstrap_ci_percentile(boot_samples_valid, level=level)
    elif ci_type == "basic":
        ci_lower, ci_upper = bootstrap_ci_basic(
            coef_obs, boot_samples_valid, level=level
        )
    else:  # bca
        # BCa requires jackknife - use simple leave-one-out for GLM
        # This is expensive but necessary for proper BCa
        jackknife_stats = _compute_glm_jackknife(
            X_np, y_np, family, weights_np, max_iter, tol
        )
        ci_lower, ci_upper = bootstrap_ci_bca(
            boot_stats=boot_samples_valid,
            observed=coef_obs,
            jackknife_stats=jackknife_stats,
            level=level,
        )

    return BootstrapResult(
        observed=coef_obs,
        boot_samples=boot_samples,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        param_names=X_names,
        n_boot=n_boot,
        ci_type=ci_type,
        level=level,
    )


def _compute_glm_jackknife(
    X: np.ndarray,
    y: np.ndarray,
    family: Family,
    weights: np.ndarray | None,
    max_iter: int,
    tol: float,
) -> Array:
    """Compute leave-one-out jackknife coefficients for GLM.

    This is O(n × IRLS_cost) which is expensive, but necessary for proper
    BCa confidence intervals.

    Args:
        X: Design matrix (n, p).
        y: Response vector (n,).
        family: GLM family object.
        weights: Prior weights (n,) or None.
        max_iter: IRLS max iterations.
        tol: IRLS tolerance.

    Returns:
        Jackknife coefficients (n, p).
    """
    n, p = X.shape
    jack_coefs = []

    for i in range(n):
        # Leave out observation i
        mask = np.ones(n, dtype=bool)
        mask[i] = False

        X_loo = X[mask]
        y_loo = y[mask]
        weights_loo = weights[mask] if weights is not None else None

        try:
            result = fit_glm_irls(y_loo, X_loo, family, weights_loo, max_iter, tol)
            jack_coefs.append(result["coef"])
        except Exception:
            # If LOO fit fails, use NaN (will be handled in BCa)
            jack_coefs.append(np.full(p, np.nan))

    return np.stack(jack_coefs, axis=0)


# =============================================================================
# GLM Permutation Test
# =============================================================================


def glm_permute(
    X: Array,
    y: Array,
    X_names: list[str],
    family: Family,
    weights: Array | None = None,
    n_perm: int = 999,
    seed: int | None = None,
    alternative: Literal["two-sided", "greater", "less"] = "two-sided",
    test_stat: Literal["coef", "wald", "deviance"] = "coef",
    max_iter: int = 25,
    tol: float = 1e-8,
) -> PermutationResult:
    """Permutation test for GLM coefficients.

    Permutes the response vector y under the null hypothesis of no association
    between predictors and response. Each permutation requires a full GLM
    refit via IRLS.

    Note: For non-Gaussian families, permuting y directly may not preserve
    the marginal distribution. This is a known limitation; consider using
    parametric bootstrap for more principled inference.

    Args:
        X: Design matrix, shape (n, p).
        y: Response vector, shape (n,).
        X_names: Coefficient names.
        family: GLM family object (gaussian, binomial, or poisson).
        weights: Prior observation weights (n,) or None.
        n_perm: Number of permutations.
        seed: Random seed for reproducibility.
        alternative: Alternative hypothesis type:
            - "two-sided": |T| >= |T_obs|
            - "greater": T >= T_obs
            - "less": T <= T_obs
        test_stat: Test statistic to use:
            - "coef": Raw coefficient estimates.
            - "wald": Wald z-statistic (coef / SE).
            - "deviance": Model deviance (not per-coefficient).
        max_iter: Maximum IRLS iterations for each refit.
        tol: Convergence tolerance for IRLS.

    Returns:
        PermutationResult with observed stats, null distribution, and p-values.

    Raises:
        ValueError: If alternative is not valid.
        ValueError: If test_stat is not valid.

    Examples:
        >>> from bossanova.ops.family import binomial
        >>> family = binomial()
        >>> result = glm_permute(
        ...     X, y, ["Intercept", "x"], family,
        ...     n_perm=999, test_stat="coef"
        ... )
        >>> print(result.pvalues)
    """
    from bossanova.resample.core import compute_pvalues

    # Input validation
    if alternative not in ("two-sided", "greater", "less"):
        raise ValueError(
            f"alternative must be 'two-sided', 'greater', or 'less', got {alternative}"
        )
    if test_stat not in ("coef", "wald", "deviance"):
        raise ValueError(
            f"test_stat must be 'coef', 'wald', or 'deviance', got {test_stat}"
        )

    # Convert to numpy arrays
    X_np = np.asarray(X)
    y_np = np.asarray(y)
    n, p = X_np.shape

    if weights is not None:
        weights_np = np.asarray(weights)
    else:
        weights_np = None

    rng = RNG.from_seed(seed)

    # Compute observed test statistics
    result_obs = fit_glm_irls(y_np, X_np, family, weights_np, max_iter, tol)
    coef_obs = result_obs["coef"]

    if test_stat == "coef":
        observed = np.asarray(coef_obs)
    elif test_stat == "wald":
        se_obs = np.sqrt(np.diag(result_obs["vcov"]))
        observed = np.asarray(coef_obs / se_obs)
    else:  # deviance
        observed = np.array([result_obs["deviance"]])

    # Generate permutation keys
    keys = rng.split(n_perm)

    # Permutation loop
    null_stats_list = []
    n_failed = 0

    for i in range(n_perm):
        subkey = keys[i]

        try:
            # Permute y
            perm_idx = np.asarray(subkey.permutation(n))
            y_perm = y_np[perm_idx]

            # Refit model
            result_perm = fit_glm_irls(y_perm, X_np, family, weights_np, max_iter, tol)

            if result_perm["converged"]:
                if test_stat == "coef":
                    null_stats_list.append(result_perm["coef"])
                elif test_stat == "wald":
                    se_perm = np.sqrt(np.diag(result_perm["vcov"]))
                    null_stats_list.append(result_perm["coef"] / se_perm)
                else:  # deviance
                    null_stats_list.append([result_perm["deviance"]])
            else:
                n_failed += 1
                if test_stat == "deviance":
                    null_stats_list.append([np.nan])
                else:
                    null_stats_list.append(np.full(p, np.nan))

        except Exception:
            n_failed += 1
            if test_stat == "deviance":
                null_stats_list.append([np.nan])
            else:
                null_stats_list.append(np.full(p, np.nan))

    # Stack null statistics
    null_distribution = np.stack(null_stats_list, axis=0)

    # Warn if many failures
    if n_failed > n_perm * 0.1:
        import warnings

        warnings.warn(
            f"Permutation: {n_failed}/{n_perm} iterations failed to converge. "
            f"Consider increasing max_iter or checking data quality.",
            RuntimeWarning,
        )

    # Compute p-values (excluding NaN samples)
    valid_mask = ~np.any(np.isnan(null_distribution), axis=1)
    null_valid = null_distribution[valid_mask]

    pvalues = compute_pvalues(observed, null_valid, alternative=alternative)

    # Adjust param_names for deviance (single value)
    if test_stat == "deviance":
        param_names = ["deviance"]
    else:
        param_names = X_names

    return PermutationResult(
        observed=observed,
        null_distribution=null_distribution,
        pvalues=pvalues,
        param_names=param_names,
        n_perm=n_perm,
        test_stat=test_stat,
        alternative=alternative,
    )


# =============================================================================
# GLM Cross-Validation
# =============================================================================


def glm_cv(
    X: Array,
    y: Array,
    X_names: list[str],
    family: Family,
    cv: int | Literal["loo"] = 5,
    seed: int | None = None,
    weights: Array | None = None,
    return_predictions: bool = False,
) -> CVResult:
    """Cross-validation for generalized linear models.

    Performs k-fold or leave-one-out cross-validation using IRLS refitting
    for each fold.

    Args:
        X: Design matrix, shape (n, p).
        y: Response vector, shape (n,).
        X_names: Coefficient names.
        family: GLM family object (gaussian, binomial, or poisson).
        cv: Cross-validation strategy:
            - int: K-fold with this many splits.
            - "loo": Leave-one-out cross-validation.
        seed: Random seed for k-fold shuffling.
        weights: Observation weights, shape (n,). For binomial models with
            varying trial counts, these are the number of trials per observation.
        return_predictions: If True, return out-of-fold predictions.

    Returns:
        CVResult with per-fold metrics (MSE, RMSE, MAE, deviance).

    Notes:
        - For GLMs, R2 is replaced by pseudo-R2 based on deviance.
        - Predictions are on the response scale (after applying linkinv).
        - For binomial models, predictions are probabilities.
        - For Poisson models, predictions are expected counts.

    Examples:
        >>> from bossanova.ops.family import binomial
        >>> family = binomial()
        >>> result = glm_cv(X, y, ["Intercept", "x"], family, cv=5)
        >>> print(result.mean_scores)
    """
    backend = get_backend()
    X_np = np.asarray(X)
    y_np = np.asarray(y)
    weights_np = np.asarray(weights) if weights is not None else None
    n, _ = X_np.shape

    rng = RNG.from_seed(seed)

    # Generate splits
    if cv == "loo":
        splits = generate_loo_indices(n)
        cv_type = "loo"
    elif isinstance(cv, int):
        splits = generate_kfold_indices(rng, n, cv, shuffle=True)
        cv_type = f"{cv}-fold"
    else:
        raise ValueError(f"cv must be int or 'loo', got {cv}")

    n_folds = len(splits)

    # Storage
    fold_scores: dict[str, list[float]] = {
        "mse": [],
        "rmse": [],
        "mae": [],
        "deviance": [],
        "pseudo_r2": [],
    }
    predictions_list = [] if return_predictions else None
    actuals_list = [] if return_predictions else None

    # Perform cross-validation
    for train_idx, test_idx in splits:
        # Convert indices to numpy for indexing
        train_idx_np = np.asarray(train_idx)
        test_idx_np = np.asarray(test_idx)

        X_train = X_np[train_idx_np]
        y_train = y_np[train_idx_np]
        X_test = X_np[test_idx_np]
        y_test = y_np[test_idx_np]

        # Subset weights if provided
        weights_train = weights_np[train_idx_np] if weights_np is not None else None

        # Fit on training data using IRLS
        result = fit_glm_irls(y_train, X_train, family, weights=weights_train)
        coef_fold = result["coef"]

        # Predict on test data
        eta = X_test @ coef_fold

        # Apply link inverse (works with both backends)
        if backend == "jax":
            import jax.numpy as jnp

            mu = family.link_inverse(jnp.asarray(eta))
            y_pred = np.asarray(mu)
        else:
            # For NumPy backend, family.link_inverse should work with numpy arrays
            # but may return JAX array, so convert to numpy
            mu = family.link_inverse(eta)
            y_pred = np.asarray(mu)

        # Compute metrics on response scale
        residuals = y_test - y_pred
        mse = float(np.mean(residuals**2))
        rmse = float(np.sqrt(mse))
        mae = float(np.mean(np.abs(residuals)))

        # Compute deviance for test set
        if backend == "jax":
            import jax.numpy as jnp

            dev_contributions = family.deviance(jnp.asarray(y_test), jnp.asarray(mu))
            deviance = float(np.sum(np.asarray(dev_contributions)))
        else:
            dev_contributions = family.deviance(y_test, mu)
            deviance = float(np.sum(np.asarray(dev_contributions)))

        # Compute pseudo-R2 (McFadden's)
        # Compare deviance to null model (mean prediction)
        y_test_mean = np.mean(y_test)
        if family.name == "binomial":
            null_mu = np.clip(y_test_mean, 1e-10, 1 - 1e-10) * np.ones_like(y_test)
        elif family.name == "poisson":
            null_mu = np.maximum(y_test_mean, 1e-10) * np.ones_like(y_test)
        else:
            null_mu = y_test_mean * np.ones_like(y_test)

        if backend == "jax":
            import jax.numpy as jnp

            null_dev_contributions = family.deviance(
                jnp.asarray(y_test), jnp.asarray(null_mu)
            )
            null_deviance = float(np.sum(np.asarray(null_dev_contributions)))
        else:
            null_dev_contributions = family.deviance(y_test, null_mu)
            null_deviance = float(np.sum(np.asarray(null_dev_contributions)))

        # Pseudo-R2: 1 - (deviance / null_deviance)
        if null_deviance > 0:
            pseudo_r2 = 1 - (deviance / null_deviance)
        else:
            pseudo_r2 = 0.0

        fold_scores["mse"].append(mse)
        fold_scores["rmse"].append(rmse)
        fold_scores["mae"].append(mae)
        fold_scores["deviance"].append(deviance)
        fold_scores["pseudo_r2"].append(pseudo_r2)

        if return_predictions:
            assert predictions_list is not None
            assert actuals_list is not None
            predictions_list.append(y_pred)
            actuals_list.append(y_test)

    # Compute summary statistics
    mean_scores = {metric: np.mean(scores) for metric, scores in fold_scores.items()}
    std_scores = {metric: np.std(scores) for metric, scores in fold_scores.items()}

    # Concatenate predictions if requested
    predictions = None
    actuals = None
    if return_predictions and predictions_list:
        predictions = np.concatenate(predictions_list)
        actuals = np.concatenate(actuals_list)

    return CVResult(
        scores=fold_scores,
        mean_scores=mean_scores,
        std_scores=std_scores,
        n_folds=n_folds,
        cv_type=cv_type,
        predictions=predictions,
        actuals=actuals,
    )
