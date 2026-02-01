# Formula Module

> **Internal module** — This is an implementation detail of bossanova.
> Users should not import from this module directly. Use the model classes
> (`lm`, `glm`, `lmer`, `glmer`) which handle formula processing automatically.

## Purpose

This module provides the formula transformation and design matrix construction
infrastructure that powers bossanova's R-style formula interface.

## Components

- **transforms.py**: Formula transformers (`Center`, `Scale`, `Standardize`, `Zscore`)
  that modify variables before fitting
- **contrasts.py**: Contrast coding functions (`treatment_contrast`, `sum_contrast`,
  `poly_contrast`) for categorical variables
- **random_effects.py**: Random effects syntax expansion (e.g., `||` to uncorrelated)
- **design.py**: `DesignMatrixBuilder` that constructs X and Z matrices from formulas

## How It Connects

```
User formula string
       │
       ▼
  _parser/          ← Tokenize & parse to AST
       │
       ▼
  formula/          ← THIS MODULE: Build design matrices
       │
       ▼
  models/           ← Fit model using matrices
```

When you call `lm("y ~ x1 + x2", data=df)`, the model class uses this module
internally to:

1. Parse the formula into an AST (via `_parser/`)
2. Detect categorical variables and apply contrast coding
3. Build the design matrix X (and Z for mixed models)
4. Handle transformations like `center(x)` or `C(group, Sum)`

## Key Exports

| Function | Purpose |
|----------|---------|
| `transform_formula` | Apply variable transforms to formula |
| `DesignMatrixBuilder` | Build X/Z matrices from formula + data |
| `treatment_contrast` | Dummy coding for categoricals |
| `sum_contrast` | Sum-to-zero (effects) coding |
| `build_random_effects` | Construct Z matrix for mixed models |
