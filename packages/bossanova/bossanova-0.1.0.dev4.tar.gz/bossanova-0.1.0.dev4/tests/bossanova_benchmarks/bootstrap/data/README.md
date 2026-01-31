# ChickWeight Dataset

The ChickWeight dataset contains weight measurements of chicks on different diets over time.

## Source

Originally from R's `datasets` package. This is the same dataset used in lme4 documentation.

## Structure

| Column | Type | Description |
|--------|------|-------------|
| weight | numeric | Body weight (grams) |
| Time | numeric | Days since birth (0, 2, 4, ..., 21) |
| Chick | factor | Chick identifier (1-50) |
| Diet | factor | Diet type (1-4) |

## Size

- **578 observations**
- **50 chicks**
- **~12 measurements per chick** (every 2 days from birth to day 21)

## Model Formula

```
weight ~ Time + (Time | Chick)
```

This models weight as a function of time with random intercepts and slopes for each chick,
allowing each chick to have its own growth trajectory.
