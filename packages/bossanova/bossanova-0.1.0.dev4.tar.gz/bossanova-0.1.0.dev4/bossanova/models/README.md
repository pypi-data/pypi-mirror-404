# Models Module

> **User-facing** — This is the primary entry point for bossanova.
> Import model classes directly: `from bossanova import lm, glm, lmer, glmer`

## Purpose

This module provides the main model classes that users interact with.
Each class follows an R-like API with formula-based model specification.

## Model Classes

| Class | Description | R Equivalent |
|-------|-------------|--------------|
| `lm` | Linear models (OLS) | `lm()` |
| `glm` | Generalized linear models | `glm()` |
| `lmer` | Linear mixed-effects models | `lme4::lmer()` |
| `glmer` | Generalized linear mixed-effects models | `lme4::glmer()` |
| `ridge` | Ridge regression (L2 penalty) | `glmnet(..., alpha=0)` |

## Basic Usage

```python
from bossanova import lm, glm, lmer
from bossanova.data import load_dataset

# Linear model
mtcars = load_dataset("mtcars")
model = lm("mpg ~ wt + hp", data=mtcars).fit()
model.summary()

# GLM (logistic regression)
model = glm("am ~ wt + hp", data=mtcars, family="binomial").fit()

# Mixed model
sleep = load_dataset("sleep")
model = lmer("Reaction ~ Days + (Days | Subject)", data=sleep).fit()
```

## Common Methods

All fitted models share these methods:

| Method | Purpose |
|--------|---------|
| `.fit()` | Fit the model |
| `.summary()` | Print coefficient table |
| `.predict()` | Generate predictions |
| `.emmeans()` | Estimated marginal means |
| `.jointtest()` | ANOVA table |
| `.bootstrap()` | Bootstrap inference |
| `.plot_params()` | Forest plot of coefficients |
| `.plot_resid()` | Residual diagnostics |

## Architecture

Model classes are thin wrappers that orchestrate internal modules:

```
lm("y ~ x", data)
       │
       ▼
  _parser/       → Parse formula to AST
       │
       ▼
  formula/       → Build design matrices
       │
       ▼
  ops/           → Solve least squares
       │
       ▼
  results/       → Structure output
       │
       ▼
  Fitted model with .result_fit, .summary(), etc.
```

## See Also

- **Grammar API**: For a more declarative, pipeable interface, see `bossanova.grammar`
- **Visualization**: `bossanova.viz` for plotting utilities
- **Model comparison**: `bossanova.compare()` and `bossanova.lrt()`
