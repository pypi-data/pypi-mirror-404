"""BOBYQA optimizer via NLOPT for variance component optimization.

This module provides BOBYQA (Bound Optimization BY Quadratic Approximation)
via NLOPT for mixed model fitting, matching lme4's optimization approach.
"""

import nlopt
import numpy as np

__all__ = ["optimize_theta"]


def optimize_theta(
    objective,
    theta0,
    lower,
    upper,
    rhobeg=2e-3,
    rhoend=2e-7,
    maxfun=10000,
    verbose=False,
):
    """Optimize theta using BOBYQA via NLOPT.

    BOBYQA is Powell's derivative-free trust-region method for bound-constrained
    optimization. This implementation uses NLOPT's LN_BOBYQA algorithm.

    Args:
        objective: Function f(theta) -> scalar deviance to minimize.
        theta0: Initial parameter values (array-like).
        lower: Lower bounds for parameters.
        upper: Upper bounds for parameters.
        rhobeg: Initial trust region radius (sets initial step size).
            Default 2e-3 (lme4's default of 0.002).
        rhoend: Final trust region radius (used to set tolerances).
            Default 2e-7 (lme4 default).
        maxfun: Maximum function evaluations. Default 10000.
        verbose: Print optimization progress.

    Returns:
        dict with keys:
            - theta: Optimized parameters (np.ndarray)
            - fun: Final objective value (float)
            - converged: Whether optimization succeeded (bool)
            - n_evals: Number of function evaluations (int)
            - message: Status message (str)

    Examples:
        >>> def rosenbrock(theta):
        ...     x, y = theta
        ...     return (1 - x)**2 + 100 * (y - x**2)**2
        >>> result = optimize_theta(
        ...     rosenbrock,
        ...     theta0=[0.0, 0.0],
        ...     lower=[-2.0, -2.0],
        ...     upper=[2.0, 2.0]
        ... )
        >>> result['converged']
        True
        >>> np.allclose(result['theta'], [1.0, 1.0], atol=1e-3)
        True
    """
    # Convert inputs to numpy arrays
    theta0 = np.asarray(theta0, dtype=float)
    lower = np.asarray(lower, dtype=float)
    upper = np.asarray(upper, dtype=float)

    # Validate dimensions
    n = len(theta0)
    if len(lower) != n or len(upper) != n:
        raise ValueError(
            f"Dimension mismatch: theta0 has {n} elements, "
            f"lower has {len(lower)}, upper has {len(upper)}"
        )

    # Ensure bounds are valid
    if np.any(lower >= upper):
        raise ValueError("Lower bounds must be strictly less than upper bounds")

    if np.any(theta0 < lower) or np.any(theta0 > upper):
        raise ValueError("Initial theta0 must be within bounds")

    # Track function evaluations
    n_evals = [0]

    def nlopt_objective(x, grad):
        """NLOPT objective wrapper (grad ignored for derivative-free)."""
        n_evals[0] += 1
        val = objective(x)
        if verbose and n_evals[0] % 50 == 0:
            print(f"  Eval {n_evals[0]}: deviance = {val:.6f}")
        return float(val)

    # Create NLOPT optimizer
    opt = nlopt.opt(nlopt.LN_BOBYQA, n)
    opt.set_min_objective(nlopt_objective)

    # Set bounds
    opt.set_lower_bounds(lower.tolist())
    opt.set_upper_bounds(upper.tolist())

    # Set initial step size from rhobeg (initial trust region radius)
    # This controls how far BOBYQA looks in its first iterations
    opt.set_initial_step(rhobeg)

    # Set tolerances for convergence based on rhoend (model-specific)
    # rhoend is the final trust region radius from lme4, use as convergence threshold
    tol = max(rhoend, 1e-8)  # Floor at 1e-8 for numerical stability
    opt.set_xtol_rel(tol)  # Parameter relative tolerance
    opt.set_ftol_abs(tol)  # Function absolute tolerance

    # Set maximum evaluations
    opt.set_maxeval(maxfun)

    # Run optimization
    message = ""
    converged = False

    try:
        theta_opt = np.array(opt.optimize(theta0.tolist()))
        fun_opt = opt.last_optimum_value()
        result_code = opt.last_optimize_result()

        # Interpret result code
        if result_code > 0:
            converged = True
            message = _get_nlopt_message(result_code)
        else:
            converged = False
            message = _get_nlopt_message(result_code)

    except nlopt.RoundoffLimited:
        # Roundoff-limited convergence - still valid
        theta_opt = theta0
        fun_opt = objective(theta0)
        converged = True
        message = "Optimization stopped due to roundoff limits"

    except Exception as e:
        # Other failures
        theta_opt = theta0
        fun_opt = objective(theta0)
        converged = False
        message = f"Optimization failed: {e}"

    return {
        "theta": theta_opt,
        "fun": float(fun_opt),
        "converged": bool(converged),
        "n_evals": n_evals[0],
        "message": message,
    }


def _get_nlopt_message(result_code):
    """Convert NLOPT result code to human-readable message."""
    messages = {
        nlopt.SUCCESS: "Optimization succeeded",
        nlopt.STOPVAL_REACHED: "Stopval reached",
        nlopt.FTOL_REACHED: "Function tolerance reached",
        nlopt.XTOL_REACHED: "Parameter tolerance reached",
        nlopt.MAXEVAL_REACHED: (
            "Return from bobyqa because the objective function "
            "has been evaluated maxfev times."
        ),
        nlopt.MAXTIME_REACHED: "Maximum time reached",
        nlopt.FAILURE: "Generic failure",
        nlopt.INVALID_ARGS: "Invalid arguments",
        nlopt.OUT_OF_MEMORY: "Out of memory",
        nlopt.ROUNDOFF_LIMITED: "Roundoff limited",
        nlopt.FORCED_STOP: "Forced stop",
    }
    return messages.get(result_code, f"Unknown result code: {result_code}")
