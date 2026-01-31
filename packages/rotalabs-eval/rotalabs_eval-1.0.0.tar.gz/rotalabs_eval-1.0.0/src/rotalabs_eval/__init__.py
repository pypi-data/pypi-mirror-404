"""rotalabs-eval: Comprehensive LLM evaluation framework with statistical rigor."""
from __future__ import annotations

from rotalabs_eval._version import __version__
from rotalabs_eval.core.config import (
    InferenceConfig,
    MetricConfig,
    ModelConfig,
    ModelProvider,
    SamplingConfig,
    StatisticsConfig,
)
from rotalabs_eval.core.exceptions import (
    EvalCacheError,
    EvalConfigError,
    EvalInferenceError,
    EvalMetricError,
    RotalabsEvalError,
)
from rotalabs_eval.core.result import EvalResult, MetricValue
from rotalabs_eval.core.task import EvalTask

__all__ = [
    "__version__",
    # Core config
    "EvalTask",
    "EvalResult",
    "MetricValue",
    "ModelConfig",
    "ModelProvider",
    "MetricConfig",
    "InferenceConfig",
    "StatisticsConfig",
    "SamplingConfig",
    # Exceptions
    "RotalabsEvalError",
    "EvalConfigError",
    "EvalInferenceError",
    "EvalMetricError",
    "EvalCacheError",
]
