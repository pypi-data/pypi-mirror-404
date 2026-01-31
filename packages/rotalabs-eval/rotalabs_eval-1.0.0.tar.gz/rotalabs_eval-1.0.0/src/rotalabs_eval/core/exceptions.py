"""Custom exception hierarchy for rotalabs-eval."""
from __future__ import annotations


class RotalabsEvalError(Exception):
    """Base exception for all rotalabs-eval errors."""

    pass


class EvalConfigError(RotalabsEvalError):
    """Raised for configuration validation errors."""

    pass


class EvalInferenceError(RotalabsEvalError):
    """Raised for inference/API call errors."""

    pass


class EvalRateLimitError(EvalInferenceError):
    """Raised when rate limits are exceeded."""

    pass


class EvalMetricError(RotalabsEvalError):
    """Raised for metric computation errors."""

    pass


class EvalCacheError(RotalabsEvalError):
    """Raised for cache-related errors."""

    pass


class EvalDatasetError(RotalabsEvalError):
    """Raised for dataset loading/validation errors."""

    pass


class EvalOrchestratorError(RotalabsEvalError):
    """Raised for orchestration errors."""

    pass
