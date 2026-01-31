# InstEval Dataset

## Source
Exported from `lme4::InstEval` in R (lme4 version 1.1-35).

## Description
University lecture/instructor evaluation data from a large Swiss university.
Each observation is a single evaluation of an instructor by a student.

## Dataset Size
- 73,421 observations
- 7 columns

## Columns
| Column | Type | Description |
|--------|------|-------------|
| s | Factor (2,972 levels) | Student ID |
| d | Factor (1,128 levels) | Instructor ID |
| studage | Ordered factor (4 levels) | Student's age cohort: 2 < 4 < 6 < 8 |
| lectage | Ordered factor (6 levels) | Lecture's age: 1 < 2 < 3 < 4 < 5 < 6 |
| service | Factor (2 levels) | Service course: 0 = No, 1 = Yes |
| dept | Factor (14 levels) | Department code |
| y | Integer | Evaluation score (1-5 scale) |

## Classic Models
```r
# Simple crossed random effects
lmer(y ~ 1 + (1|s) + (1|d), data = InstEval)

# Extended model with fixed effects
lmer(y ~ service + lectage + studage + (1|s) + (1|d) + (1|dept), data = InstEval)
```

## Provenance
- Exported: 2026-01-03
- R version: 4.5.2
- lme4 version: 1.1-35
- Command: `write.csv(InstEval, 'insteval.csv', row.names=FALSE)`

## Reference
Rabe-Hesketh, S., & Skrondal, A. (2008). Multilevel and Longitudinal Modeling
Using Stata (2nd ed.). Stata Press.
