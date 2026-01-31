"""Significance testing for model comparisons."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

import numpy as np
from scipy import stats as scipy_stats

logger = logging.getLogger(__name__)


@dataclass
class SignificanceResult:
    """Result of a significance test.

    Args:
        test_name: Name of the statistical test.
        statistic: Test statistic value.
        p_value: P-value.
        significant: Whether the difference is significant.
        alpha: Significance level used.
        details: Additional test details.
    """

    test_name: str
    statistic: float
    p_value: float
    significant: bool
    alpha: float = 0.05
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        sig = "significant" if self.significant else "not significant"
        return f"{self.test_name}: stat={self.statistic:.4f}, p={self.p_value:.4f} ({sig})"


def paired_ttest(
    values_a: np.ndarray,
    values_b: np.ndarray,
    alpha: float = 0.05,
) -> SignificanceResult:
    """Paired t-test for continuous metrics.

    Tests whether two sets of paired observations have different means.

    Args:
        values_a: Scores from model A.
        values_b: Scores from model B.
        alpha: Significance level.

    Returns:
        SignificanceResult.
    """
    values_a = np.asarray(values_a, dtype=float)
    values_b = np.asarray(values_b, dtype=float)

    stat, p_value = scipy_stats.ttest_rel(values_a, values_b)

    # Handle identical arrays (scipy returns nan)
    if np.isnan(p_value):
        p_value = 1.0
        stat = 0.0

    return SignificanceResult(
        test_name="paired_ttest",
        statistic=float(stat),
        p_value=float(p_value),
        significant=float(p_value) < alpha,
        alpha=alpha,
        details={
            "mean_a": float(np.mean(values_a)),
            "mean_b": float(np.mean(values_b)),
            "mean_diff": float(np.mean(values_a - values_b)),
            "n": len(values_a),
        },
    )


def mcnemar_test(
    correct_a: np.ndarray,
    correct_b: np.ndarray,
    alpha: float = 0.05,
) -> SignificanceResult:
    """McNemar's test for paired binary outcomes.

    Tests whether two models have different error rates on the same data.

    Args:
        correct_a: Boolean array - True where model A correct.
        correct_b: Boolean array - True where model B correct.
        alpha: Significance level.

    Returns:
        SignificanceResult.
    """
    correct_a = np.asarray(correct_a, dtype=bool)
    correct_b = np.asarray(correct_b, dtype=bool)

    # Discordant pairs
    b01 = np.sum(correct_a & ~correct_b)  # A right, B wrong
    b10 = np.sum(~correct_a & correct_b)  # A wrong, B right

    n_discordant = b01 + b10

    if n_discordant == 0:
        return SignificanceResult(
            test_name="mcnemar",
            statistic=0.0,
            p_value=1.0,
            significant=False,
            alpha=alpha,
            details={"b01": int(b01), "b10": int(b10)},
        )

    # Use exact binomial test for small samples
    if n_discordant < 25:
        p_value = float(scipy_stats.binomtest(int(b01), int(n_discordant), 0.5).pvalue)
        stat = float(b01)
        test_variant = "exact"
    else:
        # Chi-squared with continuity correction
        stat = float((abs(b01 - b10) - 1) ** 2 / (b01 + b10))
        p_value = float(1 - scipy_stats.chi2.cdf(stat, df=1))
        test_variant = "chi2"

    return SignificanceResult(
        test_name="mcnemar",
        statistic=stat,
        p_value=p_value,
        significant=p_value < alpha,
        alpha=alpha,
        details={
            "b01": int(b01),
            "b10": int(b10),
            "test_variant": test_variant,
        },
    )


def wilcoxon_signed_rank(
    values_a: np.ndarray,
    values_b: np.ndarray,
    alpha: float = 0.05,
) -> SignificanceResult:
    """Wilcoxon signed-rank test for paired non-parametric data.

    Args:
        values_a: Scores from model A.
        values_b: Scores from model B.
        alpha: Significance level.

    Returns:
        SignificanceResult.
    """
    values_a = np.asarray(values_a, dtype=float)
    values_b = np.asarray(values_b, dtype=float)

    diff = values_a - values_b
    # Remove zeros
    non_zero = diff[diff != 0]

    if len(non_zero) == 0:
        return SignificanceResult(
            test_name="wilcoxon",
            statistic=0.0,
            p_value=1.0,
            significant=False,
            alpha=alpha,
        )

    stat, p_value = scipy_stats.wilcoxon(non_zero)

    return SignificanceResult(
        test_name="wilcoxon",
        statistic=float(stat),
        p_value=float(p_value),
        significant=float(p_value) < alpha,
        alpha=alpha,
        details={
            "n_nonzero": len(non_zero),
            "median_diff": float(np.median(diff)),
        },
    )


def bootstrap_significance(
    values_a: np.ndarray,
    values_b: np.ndarray,
    n_iterations: int = 10000,
    alpha: float = 0.05,
    seed: Optional[int] = None,
) -> SignificanceResult:
    """Bootstrap permutation test for significance.

    Args:
        values_a: Scores from model A.
        values_b: Scores from model B.
        n_iterations: Number of permutations.
        alpha: Significance level.
        seed: Random seed.

    Returns:
        SignificanceResult.
    """
    values_a = np.asarray(values_a, dtype=float)
    values_b = np.asarray(values_b, dtype=float)

    rng = np.random.RandomState(seed)
    observed_diff = float(np.mean(values_a) - np.mean(values_b))

    # Pool and permute
    pooled = np.concatenate([values_a, values_b])
    n_a = len(values_a)
    count = 0

    for _ in range(n_iterations):
        rng.shuffle(pooled)
        perm_diff = np.mean(pooled[:n_a]) - np.mean(pooled[n_a:])
        if abs(perm_diff) >= abs(observed_diff):
            count += 1

    p_value = count / n_iterations

    return SignificanceResult(
        test_name="bootstrap_permutation",
        statistic=observed_diff,
        p_value=float(p_value),
        significant=p_value < alpha,
        alpha=alpha,
        details={
            "observed_diff": observed_diff,
            "n_iterations": n_iterations,
        },
    )


def choose_test(
    values_a: np.ndarray,
    values_b: np.ndarray,
    alpha: float = 0.05,
) -> SignificanceResult:
    """Automatically choose and run the appropriate test.

    - Binary data → McNemar's test
    - Normal continuous → Paired t-test
    - Non-normal continuous → Wilcoxon signed-rank

    Args:
        values_a: Scores from model A.
        values_b: Scores from model B.
        alpha: Significance level.

    Returns:
        SignificanceResult from the chosen test.
    """
    values_a = np.asarray(values_a, dtype=float)
    values_b = np.asarray(values_b, dtype=float)

    unique_values = set(np.unique(values_a)) | set(np.unique(values_b))

    # Binary check
    if unique_values.issubset({0.0, 1.0}):
        return mcnemar_test(values_a.astype(bool), values_b.astype(bool), alpha)

    # Normality check (differences)
    diff = values_a - values_b
    if len(diff) >= 8:
        _, normality_p = scipy_stats.shapiro(diff)
        if normality_p < 0.05:
            return wilcoxon_signed_rank(values_a, values_b, alpha)

    return paired_ttest(values_a, values_b, alpha)
