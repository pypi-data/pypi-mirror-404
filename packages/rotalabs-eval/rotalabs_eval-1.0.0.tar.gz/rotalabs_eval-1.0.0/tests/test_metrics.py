"""Tests for evaluation metrics."""
from __future__ import annotations

import pytest

from rotalabs_eval.metrics.base import MetricResult
from rotalabs_eval.metrics.lexical import (
    BLEUMetric,
    ContainsMetric,
    ExactMatchMetric,
    F1Metric,
    LengthRatioMetric,
    ROUGELMetric,
)
from rotalabs_eval.metrics.registry import MetricRegistry, get_metric


class TestExactMatch:
    def test_perfect_match(self):
        m = ExactMatchMetric()
        r = m.compute(["hello world"], ["hello world"])
        assert r.value == 1.0

    def test_no_match(self):
        m = ExactMatchMetric()
        r = m.compute(["hello"], ["world"])
        assert r.value == 0.0

    def test_case_insensitive(self):
        m = ExactMatchMetric()
        r = m.compute(["Hello World"], ["hello world"])
        assert r.value == 1.0

    def test_multiple(self):
        m = ExactMatchMetric()
        r = m.compute(["a", "b", "c"], ["a", "b", "d"])
        assert r.value == pytest.approx(2 / 3)
        assert len(r.per_example_scores) == 3


class TestF1:
    def test_perfect(self):
        m = F1Metric()
        r = m.compute(["the cat sat"], ["the cat sat"])
        assert r.value == 1.0

    def test_partial(self):
        m = F1Metric()
        r = m.compute(["the cat"], ["the cat sat on mat"])
        assert 0.0 < r.value < 1.0

    def test_no_overlap(self):
        m = F1Metric()
        r = m.compute(["hello"], ["world"])
        assert r.value == 0.0

    def test_empty(self):
        m = F1Metric()
        r = m.compute([""], [""])
        assert r.value == 1.0


class TestBLEU:
    def test_perfect(self):
        m = BLEUMetric()
        r = m.compute(["the cat sat on the mat"], ["the cat sat on the mat"])
        assert r.value == pytest.approx(1.0, abs=0.01)

    def test_no_match(self):
        m = BLEUMetric()
        r = m.compute(["hello"], ["world"])
        assert r.value == 0.0


class TestROUGEL:
    def test_perfect(self):
        m = ROUGELMetric()
        r = m.compute(["the cat sat"], ["the cat sat"])
        assert r.value == 1.0

    def test_partial(self):
        m = ROUGELMetric()
        r = m.compute(["the cat sat on mat"], ["the big cat sat"])
        assert 0.0 < r.value < 1.0


class TestContains:
    def test_contains(self):
        m = ContainsMetric()
        r = m.compute(["The answer is 42."], ["42"])
        assert r.value == 1.0

    def test_not_contains(self):
        m = ContainsMetric()
        r = m.compute(["The answer is 42."], ["43"])
        assert r.value == 0.0


class TestLengthRatio:
    def test_equal(self):
        m = LengthRatioMetric()
        r = m.compute(["hello"], ["world"])
        assert r.value == 1.0


class TestRegistry:
    def test_get_metric(self):
        m = get_metric("exact_match")
        assert m.name == "exact_match"

    def test_unknown_metric(self):
        with pytest.raises(KeyError):
            get_metric("nonexistent_metric_xyz")

    def test_list_metrics(self):
        registry = MetricRegistry()
        metrics = registry.list_metrics()
        assert "exact_match" in metrics
        assert "f1" in metrics
