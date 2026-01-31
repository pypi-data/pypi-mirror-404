"""Tests for core module."""
from __future__ import annotations

import pytest

from rotalabs_eval.core.config import (
    InferenceConfig,
    MetricConfig,
    ModelConfig,
    ModelProvider,
    StatisticsConfig,
)
from rotalabs_eval.core.exceptions import EvalConfigError, RotalabsEvalError
from rotalabs_eval.core.result import CostBreakdown, EvalResult, LatencyStats, MetricValue
from rotalabs_eval.core.task import EvalTask
from rotalabs_eval.core.types import ModelResponse


class TestModelConfig:
    def test_valid_config(self):
        config = ModelConfig(provider=ModelProvider.OPENAI, model_name="gpt-4o")
        assert config.model_name == "gpt-4o"
        assert config.temperature == 0.0

    def test_invalid_temperature(self):
        with pytest.raises(EvalConfigError):
            ModelConfig(provider=ModelProvider.OPENAI, model_name="gpt-4o", temperature=3.0)

    def test_invalid_max_tokens(self):
        with pytest.raises(EvalConfigError):
            ModelConfig(provider=ModelProvider.OPENAI, model_name="gpt-4o", max_tokens=-1)

    def test_get_api_key_from_config(self):
        config = ModelConfig(provider=ModelProvider.OPENAI, model_name="gpt-4o", api_key="test-key")
        assert config.get_api_key() == "test-key"


class TestStatisticsConfig:
    def test_valid_config(self):
        config = StatisticsConfig(confidence_level=0.99)
        assert config.confidence_level == 0.99

    def test_invalid_confidence(self):
        with pytest.raises(EvalConfigError):
            StatisticsConfig(confidence_level=1.5)


class TestMetricValue:
    def test_with_ci(self):
        mv = MetricValue(value=0.85, confidence_interval=(0.80, 0.90))
        assert mv.ci_lower == 0.80
        assert mv.ci_upper == 0.90
        assert mv.ci_width == pytest.approx(0.10)

    def test_without_ci(self):
        mv = MetricValue(value=0.85)
        assert mv.ci_lower is None
        assert mv.ci_upper is None

    def test_to_dict(self):
        mv = MetricValue(value=0.85, confidence_interval=(0.80, 0.90), sample_size=100)
        d = mv.to_dict()
        assert d["value"] == 0.85
        assert d["sample_size"] == 100


class TestEvalTask:
    def test_template_columns(self):
        task = EvalTask(prompt_template="Answer: {{ question }} Context: {{ context }}")
        cols = task.get_template_columns()
        assert "question" in cols
        assert "context" in cols

    def test_no_template(self):
        task = EvalTask(input_column="text")
        cols = task.get_template_columns()
        assert cols == ["text"]


class TestCostBreakdown:
    def test_totals(self):
        cost = CostBreakdown(total_cost_usd=1.0, input_tokens=500, output_tokens=200, num_requests=10)
        assert cost.total_tokens == 700
        assert cost.cost_per_request == 0.1


class TestModelResponse:
    def test_success(self):
        resp = ModelResponse(text="hello", input_tokens=10, output_tokens=5)
        assert resp.success
        assert resp.total_tokens == 15

    def test_failure(self):
        resp = ModelResponse(text="", error="timeout")
        assert not resp.success


class TestExceptions:
    def test_hierarchy(self):
        assert issubclass(EvalConfigError, RotalabsEvalError)
        assert issubclass(RotalabsEvalError, Exception)
