"""Tests for statistics module."""
from __future__ import annotations

import numpy as np
import pytest

from rotalabs_eval.statistics.confidence import (
    analytical_ci_mean,
    analytical_ci_proportion,
    bootstrap_ci,
    bootstrap_ci_bca,
    compare_cis,
)
from rotalabs_eval.statistics.effect_size import cohens_d, hedges_g, odds_ratio, relative_improvement
from rotalabs_eval.statistics.significance import (
    bootstrap_significance,
    choose_test,
    mcnemar_test,
    paired_ttest,
    wilcoxon_signed_rank,
)
from rotalabs_eval.statistics.power import compute_power, sample_size_for_mean_diff


class TestBootstrapCI:
    def test_basic(self):
        scores = np.array([0.8, 0.85, 0.9, 0.75, 0.82])
        mean, ci, se = bootstrap_ci(scores, seed=42)
        assert 0.7 < mean < 0.95
        assert ci[0] < mean < ci[1]
        assert se > 0

    def test_single_value(self):
        scores = np.array([0.5])
        mean, ci, se = bootstrap_ci(scores)
        assert mean == 0.5
        assert se == 0.0


class TestBootstrapCIBCA:
    def test_basic(self):
        scores = np.array([0.8, 0.85, 0.9, 0.75, 0.82, 0.88])
        mean, ci, se = bootstrap_ci_bca(scores, seed=42)
        assert ci[0] < mean < ci[1]


class TestAnalyticalCI:
    def test_mean(self):
        scores = np.array([0.8, 0.85, 0.9, 0.75, 0.82])
        mean, ci, se = analytical_ci_mean(scores)
        assert ci[0] < mean < ci[1]

    def test_proportion_wilson(self):
        p, ci, se = analytical_ci_proportion(80, 100, method="wilson")
        assert 0.7 < ci[0] < 0.8
        assert 0.8 < ci[1] < 0.9

    def test_proportion_normal(self):
        p, ci, se = analytical_ci_proportion(50, 100, method="normal")
        assert p == 0.5


class TestCompareCIs:
    def test_overlap(self):
        assert compare_cis((0.7, 0.9), (0.8, 1.0)) is True

    def test_no_overlap(self):
        assert compare_cis((0.7, 0.8), (0.9, 1.0)) is False


class TestCohensD:
    def test_no_difference(self):
        a = np.array([0.8, 0.82, 0.81, 0.79])
        result = cohens_d(a, a)
        assert result.value == 0.0

    def test_large_difference(self):
        a = np.array([0.9, 0.95, 0.88, 0.92])
        b = np.array([0.5, 0.55, 0.48, 0.52])
        result = cohens_d(a, b)
        assert abs(result.value) > 0.8
        assert result.interpretation == "large"


class TestHedgesG:
    def test_basic(self):
        a = np.array([0.8, 0.85, 0.9])
        b = np.array([0.7, 0.75, 0.8])
        result = hedges_g(a, b)
        assert result.name == "hedges_g"


class TestOddsRatio:
    def test_equal(self):
        a = np.array([True, False, True, False])
        b = np.array([True, False, True, False])
        result = odds_ratio(a, b)
        assert result.value == 1.0

    def test_a_better(self):
        a = np.array([True, True, True, False])
        b = np.array([False, False, True, False])
        result = odds_ratio(a, b)
        assert result.value > 1.0


class TestRelativeImprovement:
    def test_improvement(self):
        result = relative_improvement(0.9, 0.8)
        assert result.value == pytest.approx(12.5)

    def test_no_change(self):
        result = relative_improvement(0.8, 0.8)
        assert result.value == 0.0


class TestPairedTTest:
    def test_no_difference(self):
        a = np.array([0.8, 0.82, 0.81, 0.79, 0.80])
        result = paired_ttest(a, a)
        assert not result.significant
        assert result.p_value == 1.0

    def test_significant(self):
        a = np.array([0.9, 0.92, 0.88, 0.91, 0.89, 0.93, 0.90, 0.92])
        b = np.array([0.5, 0.52, 0.48, 0.51, 0.49, 0.53, 0.50, 0.52])
        result = paired_ttest(a, b)
        assert result.significant


class TestMcNemar:
    def test_equal(self):
        a = np.array([True, False, True, False])
        b = np.array([True, False, True, False])
        result = mcnemar_test(a, b)
        assert not result.significant


class TestWilcoxon:
    def test_no_difference(self):
        a = np.array([0.8, 0.82, 0.81, 0.79, 0.80])
        result = wilcoxon_signed_rank(a, a)
        assert not result.significant


class TestChooseTest:
    def test_binary(self):
        a = np.array([1, 0, 1, 0, 1])
        b = np.array([1, 0, 1, 0, 1])
        result = choose_test(a.astype(float), b.astype(float))
        assert result.test_name == "mcnemar"


class TestPowerAnalysis:
    def test_sample_size(self):
        result = sample_size_for_mean_diff(0.5)
        assert result.required_sample_size > 0

    def test_compute_power(self):
        power = compute_power(100, 0.5)
        assert 0.0 < power <= 1.0
