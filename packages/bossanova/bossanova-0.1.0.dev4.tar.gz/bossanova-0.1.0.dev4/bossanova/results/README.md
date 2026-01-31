# Results Module

> **Internal module** — This is an implementation detail of bossanova.
> Users should not import from this module directly. Access results via
> model properties like `.result_fit`, `.result_diagnostics`, or `.summary()`.

## Purpose

This module provides dataclass schemas and builder functions that define
the structure of result DataFrames returned by bossanova models. It ensures
consistent column names and types across all model types.

## Components

- **schemas.py**: Dataclass definitions for result structures
- **builders.py**: Functions that construct Polars DataFrames from schemas
- **wrappers.py**: `ResultFit` wrapper providing DataFrame + convenience methods

## How It Connects

```
model.fit()
       │
       ▼
  Internal computation
       │
       ▼
  results/          ← THIS MODULE: Structure outputs
       │
       ├── LMResultFit schema
       └── build_result_fit()
       │
       ▼
  model.result_fit  → Polars DataFrame
```

## Schema Hierarchy

```
BaseResultFit
    ├── LMResultFit
    ├── GLMResultFit
    ├── LMerResultFit
    └── RidgeResultFit

BaseResultFitDiagnostics
    ├── LMResultFitDiagnostics
    ├── GLMResultFitDiagnostics
    └── ...
```

## Why Schemas?

Using dataclasses provides:

- **Type safety**: Catch missing/wrong columns at construction time
- **Documentation**: Schema defines what each result contains
- **Consistency**: All models produce identically-structured outputs
- **Validation**: Ensure required fields are present

## Key Exports

| Class/Function | Purpose |
|----------------|---------|
| `LMResultFit` | Schema for lm coefficient table |
| `GLMResultFit` | Schema for glm coefficient table |
| `LMerResultFit` | Schema for lmer fixed effects |
| `build_result_fit` | Construct DataFrame from schema |
| `ResultFit` | Wrapper with `.filter()`, `.ci()` methods |
