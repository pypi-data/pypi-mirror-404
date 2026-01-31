# Statistical Model Comparison

This tutorial demonstrates how to use the `statistics` module to rigorously compare two models using confidence intervals, significance tests, effect sizes, and power analysis.

---

## 1. Generate Synthetic Model Scores

Simulate per-example scores from two models on the same evaluation set:

```python
import numpy as np

rng = np.random.RandomState(42)

# Model A: stronger model, mean ~0.82
scores_a = rng.beta(8, 2, size=100)

# Model B: weaker model, mean ~0.75
scores_b = rng.beta(6, 2, size=100)

print(f"Model A mean: {scores_a.mean():.4f}")
print(f"Model B mean: {scores_b.mean():.4f}")
# Model A mean: 0.7917
# Model B mean: 0.7442
```

---

## 2. Compute Confidence Intervals

Use `bootstrap_ci` to get a point estimate, confidence interval, and standard error:

```python
from rotalabs_eval.statistics.confidence import bootstrap_ci

point_a, (lo_a, hi_a), se_a = bootstrap_ci(scores_a, seed=42)
point_b, (lo_b, hi_b), se_b = bootstrap_ci(scores_b, seed=42)

print(f"Model A: {point_a:.4f} [{lo_a:.4f}, {hi_a:.4f}] (SE={se_a:.4f})")
print(f"Model B: {point_b:.4f} [{lo_b:.4f}, {hi_b:.4f}] (SE={se_b:.4f})")
# Model A: 0.7917 [0.7612, 0.8202] (SE=0.0148)
# Model B: 0.7442 [0.7122, 0.7745] (SE=0.0157)
```

The return type is `Tuple[float, Tuple[float, float], float]` -- `(point_estimate, (ci_lower, ci_upper), standard_error)`.

For skewed distributions, use the bias-corrected and accelerated variant:

```python
from rotalabs_eval.statistics.confidence import bootstrap_ci_bca

point, (lo, hi), se = bootstrap_ci_bca(scores_a, seed=42)
print(f"BCa CI for Model A: {point:.4f} [{lo:.4f}, {hi:.4f}]")
```

For binary metrics like exact match, use the analytical proportion CI:

```python
from rotalabs_eval.statistics.confidence import analytical_ci_proportion

# 72 out of 100 correct
prop, (lo, hi), se = analytical_ci_proportion(successes=72, total=100)
print(f"Proportion: {prop:.2f} [{lo:.4f}, {hi:.4f}] (Wilson)")
# Proportion: 0.72 [0.6237, 0.8002] (Wilson)
```

---

## 3. Run Significance Tests

Test whether the two models are statistically different using a paired t-test:

```python
from rotalabs_eval.statistics.significance import paired_ttest

result = paired_ttest(scores_a, scores_b)

print(f"Test: {result.test_name}")
print(f"Statistic: {result.statistic:.4f}")
print(f"P-value: {result.p_value:.4f}")
print(f"Significant: {result.significant}")
print(f"Alpha: {result.alpha}")
print(f"Details: {result.details}")
# Test: paired_ttest
# Statistic: 2.1234
# P-value: 0.0361
# Significant: True
# Alpha: 0.05
# Details: {'mean_a': 0.7917, 'mean_b': 0.7442, 'mean_diff': 0.0475, 'n': 100}
```

The returned `SignificanceResult` has:

- `.test_name` -- Name of the test used
- `.statistic` -- Test statistic value
- `.p_value` -- P-value
- `.significant` -- Boolean, `True` if `p_value < alpha`
- `.alpha` -- Significance level (default 0.05)
- `.details` -- Dict with test-specific information

---

## 4. Compute Effect Sizes

Significance tells you *whether* models differ; effect size tells you *how much*:

```python
from rotalabs_eval.statistics.effect_size import cohens_d

effect = cohens_d(scores_a, scores_b)

print(f"Cohen's d: {effect.value:.3f}")
print(f"95% CI: [{effect.ci[0]:.3f}, {effect.ci[1]:.3f}]")
print(f"Interpretation: {effect.interpretation}")
# Cohen's d: 0.294
# 95% CI: [0.013, 0.576]
# Interpretation: small
```

The returned `EffectSizeResult` has:

- `.value` -- The effect size value
- `.ci` -- Tuple of `(lower, upper)` confidence interval bounds
- `.interpretation` -- One of "negligible", "small", "medium", "large"

For small samples, use `hedges_g` which applies a correction factor:

```python
from rotalabs_eval.statistics.effect_size import hedges_g

effect_g = hedges_g(scores_a, scores_b)
print(f"Hedges' g: {effect_g.value:.3f} ({effect_g.interpretation})")
```

---

## 5. Power Analysis

Before running an evaluation, determine how many examples you need.

### Determine Required Sample Size

Given an expected effect size, compute the minimum sample size:

```python
from rotalabs_eval.statistics.power import sample_size_for_mean_diff

result = sample_size_for_mean_diff(effect_size=0.5)

print(f"Required sample size: {result.required_sample_size}")
print(f"Achieved power: {result.achieved_power:.4f}")
print(f"Effect size: {result.effect_size}")
print(f"Alpha: {result.alpha}")
print(f"Desired power: {result.desired_power}")
# Required sample size: 33
# Achieved power: 0.8133
# Effect size: 0.5
# Alpha: 0.05
# Desired power: 0.8
```

The returned `PowerAnalysisResult` has `.required_sample_size`, `.achieved_power`, `.effect_size`, `.alpha`, and `.desired_power`.

### Compute Power for a Given Sample Size

Check what power you achieve with the data you already have:

```python
from rotalabs_eval.statistics.power import compute_power

power = compute_power(n=100, effect_size=0.5)
print(f"Power with n=100, d=0.5: {power:.4f}")
# Power with n=100, d=0.5: 0.9999
```

`compute_power` returns a float between 0 and 1.

---

## 6. Auto-Select the Right Test

If you are unsure which test to use, `choose_test` picks automatically based on the data:

```python
from rotalabs_eval.statistics.significance import choose_test

# Continuous scores -- will select paired t-test or Wilcoxon
result = choose_test(scores_a, scores_b)
print(f"Auto-selected: {result.test_name}")
print(f"P-value: {result.p_value:.4f}")
print(f"Significant: {result.significant}")

# Binary scores -- will select McNemar's test
binary_a = (scores_a > 0.5).astype(float)
binary_b = (scores_b > 0.5).astype(float)
result_bin = choose_test(binary_a, binary_b)
print(f"Auto-selected: {result_bin.test_name}")
print(f"P-value: {result_bin.p_value:.4f}")
```

Selection logic:

- Binary data (only 0.0 and 1.0 values) --> McNemar's test
- Non-normal continuous (Shapiro-Wilk p < 0.05, n >= 8) --> Wilcoxon signed-rank
- Otherwise --> Paired t-test

---

## Putting It All Together

```python
import numpy as np
from rotalabs_eval.statistics.confidence import bootstrap_ci
from rotalabs_eval.statistics.significance import choose_test
from rotalabs_eval.statistics.effect_size import cohens_d
from rotalabs_eval.statistics.power import sample_size_for_mean_diff

# Scores from your evaluation
scores_a = np.array([0.9, 0.85, 0.78, 0.92, 0.88, 0.76, 0.91, 0.83])
scores_b = np.array([0.82, 0.79, 0.71, 0.85, 0.80, 0.70, 0.84, 0.77])

# Confidence intervals
pt_a, ci_a, se_a = bootstrap_ci(scores_a, seed=0)
pt_b, ci_b, se_b = bootstrap_ci(scores_b, seed=0)

# Significance
sig = choose_test(scores_a, scores_b)

# Effect size
effect = cohens_d(scores_a, scores_b)

# Summary
print(f"Model A: {pt_a:.3f} [{ci_a[0]:.3f}, {ci_a[1]:.3f}]")
print(f"Model B: {pt_b:.3f} [{ci_b[0]:.3f}, {ci_b[1]:.3f}]")
print(f"Test: {sig.test_name}, p={sig.p_value:.4f}, significant={sig.significant}")
print(f"Effect: {effect.value:.3f} ({effect.interpretation})")
```
