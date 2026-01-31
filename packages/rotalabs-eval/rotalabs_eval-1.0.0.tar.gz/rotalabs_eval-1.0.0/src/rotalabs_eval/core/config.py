"""Configuration dataclasses for evaluation tasks."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from rotalabs_eval.core.exceptions import EvalConfigError

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    DATABRICKS = "databricks"
    VLLM = "vllm"
    CUSTOM = "custom"


@dataclass
class ModelConfig:
    """Configuration for a model to evaluate.

    Args:
        provider: LLM provider.
        model_name: Model identifier (e.g., "gpt-4o", "llama3").
        temperature: Sampling temperature.
        max_tokens: Maximum output tokens.
        api_key: API key (falls back to env var).
        api_base: Custom API endpoint.
        extra_params: Additional model-specific parameters.
    """

    provider: ModelProvider
    model_name: str
    temperature: float = 0.0
    max_tokens: int = 1024
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    extra_params: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.temperature < 0 or self.temperature > 2:
            raise EvalConfigError(f"Temperature must be between 0 and 2, got {self.temperature}")
        if self.max_tokens <= 0:
            raise EvalConfigError(f"max_tokens must be positive, got {self.max_tokens}")

    def get_api_key(self) -> Optional[str]:
        """Get API key from config or environment."""
        if self.api_key:
            return self.api_key
        env_map = {
            ModelProvider.OPENAI: "OPENAI_API_KEY",
            ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            ModelProvider.GOOGLE: "GOOGLE_API_KEY",
        }
        env_var = env_map.get(self.provider)
        if env_var:
            return os.environ.get(env_var)
        return None


@dataclass
class MetricConfig:
    """Configuration for a single metric.

    Args:
        name: Metric name (must match registry).
        kwargs: Additional arguments passed to metric constructor.
        requires_reference: Whether this metric needs a reference answer.
        weight: Metric weight for composite scores.
    """

    name: str
    kwargs: Dict[str, Any] = field(default_factory=dict)
    requires_reference: bool = True
    weight: float = 1.0


@dataclass
class StatisticsConfig:
    """Configuration for statistical analysis.

    Args:
        confidence_level: CI confidence level (e.g., 0.95).
        bootstrap_iterations: Number of bootstrap samples.
        ci_method: CI method ("bootstrap" or "analytical").
        compute_effect_sizes: Whether to compute effect sizes.
    """

    confidence_level: float = 0.95
    bootstrap_iterations: int = 1000
    ci_method: str = "bootstrap"
    compute_effect_sizes: bool = True

    def __post_init__(self) -> None:
        if not 0 < self.confidence_level < 1:
            raise EvalConfigError(
                f"confidence_level must be between 0 and 1, got {self.confidence_level}"
            )


@dataclass
class InferenceConfig:
    """Configuration for inference execution.

    Args:
        batch_size: Batch size for inference.
        max_retries: Maximum retries per request.
        retry_delay: Base delay between retries (seconds).
        requests_per_minute: Rate limit (RPM).
        tokens_per_minute: Rate limit (TPM).
        timeout: Request timeout in seconds.
        concurrency: Max concurrent requests (for async executor).
    """

    batch_size: int = 32
    max_retries: int = 3
    retry_delay: float = 1.0
    requests_per_minute: int = 500
    tokens_per_minute: int = 100000
    timeout: int = 60
    concurrency: int = 10

    def get_effective_cache_config(self) -> Any:
        """Get the effective cache config, defaulting to disabled."""
        from rotalabs_eval.cache.config import CacheConfig, CachePolicy

        return CacheConfig(policy=CachePolicy.DISABLED)


@dataclass
class SamplingConfig:
    """Configuration for dataset sampling.

    Args:
        strategy: Sampling strategy ("random" or "stratified").
        sample_size: Number of examples to sample.
        seed: Random seed for reproducibility.
        stratify_column: Column for stratified sampling.
    """

    strategy: str = "random"
    sample_size: Optional[int] = None
    seed: int = 42
    stratify_column: Optional[str] = None


@dataclass
class OutputConfig:
    """Configuration for output and saving results.

    Args:
        save_results: Whether to save results.
        results_path: Path to save results.
        save_predictions: Whether to save per-example predictions.
        output_format: Output format ("parquet", "csv", "json").
    """

    save_results: bool = False
    results_path: Optional[str] = None
    save_predictions: bool = False
    output_format: str = "parquet"
