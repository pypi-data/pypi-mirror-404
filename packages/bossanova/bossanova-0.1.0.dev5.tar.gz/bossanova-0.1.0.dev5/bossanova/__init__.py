"""bossanova - Clean Python implementation of R's formula-based statistical models.

A modern Python library providing formula-based model fitting for:

- lm: Linear models (OLS regression)
- glm: Generalized linear models (logistic, Poisson, etc.)
- lmer: Linear mixed-effects models
- glmer: Generalized linear mixed-effects models

Examples:
    >>> from bossanova import lm
    >>> model = lm("mpg ~ wt + hp", data=mtcars)
    >>> model.fit()
    >>> model.summary()

Backend Selection:
    By default, bossanova uses JAX for optimal performance. You can switch
    to NumPy before fitting any models:

    >>> import bossanova
    >>> bossanova.set_backend("numpy")
    >>> model = bossanova.lm("y ~ x", data=df).fit()
"""

# Backend API (must be imported first, before any JAX usage)
from bossanova._backend import backend, get_backend, set_backend

# Configure JAX x64 eagerly if JAX is available
# This MUST happen before any JAX arrays are created anywhere in the codebase.
# We cannot defer this to lazy loading because submodules (e.g., lmer_core.py)
# import JAX at module level and would create float32 arrays otherwise.
try:
    import jax

    jax.config.update("jax_enable_x64", True)
except ImportError:
    pass  # JAX not available, will use numpy backend

# Configuration
from bossanova._config import (  # noqa: E402
    get_singular_tolerance,
    set_singular_tolerance,
)

# Data loading
from bossanova.data import (  # noqa: E402
    load_dataset,
    show_datasets,
)

# Models
from bossanova.models import glm, glmer, lm, lmer  # noqa: E402

# Statistics
from bossanova.stats import compare, lrt  # noqa: E402

# Visualization
from bossanova import viz  # noqa: E402

__all__ = [
    # Backend
    "get_backend",
    "set_backend",
    "backend",
    # Models
    "lm",
    "glm",
    "lmer",
    "glmer",
    # Model comparison
    "compare",
    "lrt",
    # Data loading
    "load_dataset",
    "show_datasets",
    # Configuration
    "get_singular_tolerance",
    "set_singular_tolerance",
    # Visualization
    "viz",
]

from importlib.metadata import version as _get_version

__version__ = _get_version("bossanova")
