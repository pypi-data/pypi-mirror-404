"""Confidence interval calculations."""
from __future__ import annotations

import logging
from typing import Any, Callable, Optional, Tuple

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


def bootstrap_ci(
    scores: np.ndarray,
    statistic_fn: Optional[Callable] = None,
    confidence_level: float = 0.95,
    n_iterations: int = 1000,
    seed: Optional[int] = None,
) -> Tuple[float, Tuple[float, float], float]:
    """Compute bootstrap confidence interval using percentile method.

    Args:
        scores: Array of metric scores.
        statistic_fn: Function to compute statistic (default: np.mean).
        confidence_level: Confidence level (e.g., 0.95).
        n_iterations: Number of bootstrap iterations.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (point_estimate, (ci_lower, ci_upper), standard_error).
    """
    scores = np.asarray(scores, dtype=float)
    if statistic_fn is None:
        statistic_fn = np.mean

    rng = np.random.RandomState(seed)
    point_estimate = float(statistic_fn(scores))

    if len(scores) <= 1:
        return point_estimate, (point_estimate, point_estimate), 0.0

    bootstrap_stats = np.array([
        statistic_fn(rng.choice(scores, size=len(scores), replace=True))
        for _ in range(n_iterations)
    ])

    alpha = 1 - confidence_level
    ci_lower = float(np.percentile(bootstrap_stats, 100 * alpha / 2))
    ci_upper = float(np.percentile(bootstrap_stats, 100 * (1 - alpha / 2)))
    se = float(np.std(bootstrap_stats, ddof=1))

    return point_estimate, (ci_lower, ci_upper), se


def bootstrap_ci_bca(
    scores: np.ndarray,
    statistic_fn: Optional[Callable] = None,
    confidence_level: float = 0.95,
    n_iterations: int = 1000,
    seed: Optional[int] = None,
) -> Tuple[float, Tuple[float, float], float]:
    """Compute bias-corrected and accelerated (BCa) bootstrap CI.

    More accurate than percentile method, especially for skewed distributions.

    Args:
        scores: Array of metric scores.
        statistic_fn: Function to compute statistic (default: np.mean).
        confidence_level: Confidence level.
        n_iterations: Number of bootstrap iterations.
        seed: Random seed.

    Returns:
        Tuple of (point_estimate, (ci_lower, ci_upper), standard_error).
    """
    scores = np.asarray(scores, dtype=float)
    if statistic_fn is None:
        statistic_fn = np.mean

    rng = np.random.RandomState(seed)
    n = len(scores)
    point_estimate = float(statistic_fn(scores))

    if n <= 1:
        return point_estimate, (point_estimate, point_estimate), 0.0

    # Bootstrap distribution
    bootstrap_stats = np.array([
        statistic_fn(rng.choice(scores, size=n, replace=True))
        for _ in range(n_iterations)
    ])

    # Bias correction factor
    z0 = stats.norm.ppf(np.mean(bootstrap_stats < point_estimate))

    # Acceleration factor (jackknife)
    jackknife_stats = np.array([
        statistic_fn(np.delete(scores, i))
        for i in range(n)
    ])
    jack_mean = np.mean(jackknife_stats)
    jack_diff = jack_mean - jackknife_stats
    numerator = np.sum(jack_diff ** 3)
    denominator = 6.0 * (np.sum(jack_diff ** 2) ** 1.5)
    a = numerator / denominator if denominator != 0 else 0.0

    # Adjusted percentiles
    alpha = 1 - confidence_level
    z_alpha_lower = stats.norm.ppf(alpha / 2)
    z_alpha_upper = stats.norm.ppf(1 - alpha / 2)

    def _adjusted_percentile(z_alpha: float) -> float:
        numerator_val = z0 + z_alpha
        adjusted = z0 + numerator_val / (1 - a * numerator_val)
        return float(stats.norm.cdf(adjusted) * 100)

    try:
        pct_lower = _adjusted_percentile(z_alpha_lower)
        pct_upper = _adjusted_percentile(z_alpha_upper)
        pct_lower = max(0, min(100, pct_lower))
        pct_upper = max(0, min(100, pct_upper))
    except (ZeroDivisionError, ValueError):
        pct_lower = 100 * alpha / 2
        pct_upper = 100 * (1 - alpha / 2)

    ci_lower = float(np.percentile(bootstrap_stats, pct_lower))
    ci_upper = float(np.percentile(bootstrap_stats, pct_upper))
    se = float(np.std(bootstrap_stats, ddof=1))

    return point_estimate, (ci_lower, ci_upper), se


def analytical_ci_mean(
    scores: np.ndarray,
    confidence_level: float = 0.95,
) -> Tuple[float, Tuple[float, float], float]:
    """Compute analytical CI for mean using t-distribution.

    Args:
        scores: Array of metric scores.
        confidence_level: Confidence level.

    Returns:
        Tuple of (mean, (ci_lower, ci_upper), standard_error).
    """
    scores = np.asarray(scores, dtype=float)
    n = len(scores)

    if n <= 1:
        mean = float(scores[0]) if n == 1 else 0.0
        return mean, (mean, mean), 0.0

    mean = float(np.mean(scores))
    se = float(np.std(scores, ddof=1) / np.sqrt(n))

    alpha = 1 - confidence_level
    t_crit = stats.t.ppf(1 - alpha / 2, df=n - 1)

    ci_lower = mean - t_crit * se
    ci_upper = mean + t_crit * se

    return mean, (ci_lower, ci_upper), se


def analytical_ci_proportion(
    successes: int,
    total: int,
    confidence_level: float = 0.95,
    method: str = "wilson",
) -> Tuple[float, Tuple[float, float], float]:
    """Compute CI for a proportion (binary metric).

    Args:
        successes: Number of successes.
        total: Total number of trials.
        confidence_level: Confidence level.
        method: CI method ("wilson", "normal", "clopper_pearson").

    Returns:
        Tuple of (proportion, (ci_lower, ci_upper), standard_error).
    """
    if total == 0:
        return 0.0, (0.0, 0.0), 0.0

    p = successes / total
    alpha = 1 - confidence_level
    z = stats.norm.ppf(1 - alpha / 2)

    if method == "wilson":
        denominator = 1 + z**2 / total
        center = (p + z**2 / (2 * total)) / denominator
        margin = z * np.sqrt(p * (1 - p) / total + z**2 / (4 * total**2)) / denominator
        ci_lower = max(0, center - margin)
        ci_upper = min(1, center + margin)
    elif method == "normal":
        se = np.sqrt(p * (1 - p) / total)
        ci_lower = max(0, p - z * se)
        ci_upper = min(1, p + z * se)
    elif method == "clopper_pearson":
        ci_lower = stats.beta.ppf(alpha / 2, successes, total - successes + 1) if successes > 0 else 0.0
        ci_upper = stats.beta.ppf(1 - alpha / 2, successes + 1, total - successes) if successes < total else 1.0
    else:
        raise ValueError(f"Unknown method: {method}")

    se = float(np.sqrt(p * (1 - p) / total))
    return float(p), (float(ci_lower), float(ci_upper)), se


def compare_cis(
    ci_a: Tuple[float, float],
    ci_b: Tuple[float, float],
) -> bool:
    """Check if two confidence intervals overlap.

    Args:
        ci_a: (lower, upper) for model A.
        ci_b: (lower, upper) for model B.

    Returns:
        True if CIs overlap, False otherwise.
    """
    return ci_a[0] <= ci_b[1] and ci_b[0] <= ci_a[1]
