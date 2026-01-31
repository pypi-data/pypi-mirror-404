"""Result types for evaluation outputs."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class MetricValue:
    """A metric value with statistical metadata.

    Args:
        value: Point estimate (mean).
        confidence_interval: (lower, upper) CI bounds.
        confidence_level: CI level (e.g., 0.95).
        standard_error: Standard error of the estimate.
        sample_size: Number of examples used.
    """

    value: float
    confidence_interval: Optional[Tuple[float, float]] = None
    confidence_level: float = 0.95
    standard_error: Optional[float] = None
    sample_size: int = 0

    @property
    def ci_lower(self) -> Optional[float]:
        if self.confidence_interval:
            return self.confidence_interval[0]
        return None

    @property
    def ci_upper(self) -> Optional[float]:
        if self.confidence_interval:
            return self.confidence_interval[1]
        return None

    @property
    def ci_width(self) -> Optional[float]:
        if self.confidence_interval:
            return self.confidence_interval[1] - self.confidence_interval[0]
        return None

    def __str__(self) -> str:
        if self.confidence_interval:
            return (
                f"{self.value:.4f} "
                f"[{self.confidence_interval[0]:.4f}, {self.confidence_interval[1]:.4f}]"
            )
        return f"{self.value:.4f}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "confidence_level": self.confidence_level,
            "standard_error": self.standard_error,
            "sample_size": self.sample_size,
        }


@dataclass
class CostBreakdown:
    """Cost tracking for an evaluation run."""

    total_cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    num_requests: int = 0
    cached_requests: int = 0
    cache_savings_usd: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def cost_per_request(self) -> float:
        if self.num_requests == 0:
            return 0.0
        return self.total_cost_usd / self.num_requests

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_cost_usd": round(self.total_cost_usd, 6),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "num_requests": self.num_requests,
            "cached_requests": self.cached_requests,
            "cache_savings_usd": round(self.cache_savings_usd, 6),
            "cost_per_request": round(self.cost_per_request, 6),
        }


@dataclass
class LatencyStats:
    """Latency statistics for an evaluation run."""

    mean_ms: float = 0.0
    median_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0
    total_duration_s: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "mean_ms": round(self.mean_ms, 2),
            "median_ms": round(self.median_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "p99_ms": round(self.p99_ms, 2),
            "min_ms": round(self.min_ms, 2),
            "max_ms": round(self.max_ms, 2),
            "total_duration_s": round(self.total_duration_s, 2),
        }


@dataclass
class EvalResult:
    """Complete result from an evaluation run.

    Contains all metrics, cost tracking, latency stats, and metadata.
    """

    task_id: str
    run_id: Optional[str]
    timestamp: datetime
    metrics: Dict[str, MetricValue]
    stratified_metrics: Dict[str, Dict[str, MetricValue]] = field(default_factory=dict)
    cost: Optional[CostBreakdown] = None
    latency: Optional[LatencyStats] = None
    predictions_table: Optional[str] = None
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    num_examples: int = 0
    num_failures: int = 0

    @property
    def success_rate(self) -> float:
        if self.num_examples == 0:
            return 0.0
        return (self.num_examples - self.num_failures) / self.num_examples

    def get_metric(self, name: str) -> Optional[MetricValue]:
        return self.metrics.get(name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "stratified_metrics": {
                k: {sk: sv.to_dict() for sk, sv in v.items()}
                for k, v in self.stratified_metrics.items()
            },
            "cost": self.cost.to_dict() if self.cost else None,
            "latency": self.latency.to_dict() if self.latency else None,
            "num_examples": self.num_examples,
            "num_failures": self.num_failures,
            "success_rate": self.success_rate,
            "config": self.config_snapshot,
        }

    def __str__(self) -> str:
        lines = [f"EvalResult(task={self.task_id}, n={self.num_examples})"]
        for name, value in self.metrics.items():
            lines.append(f"  {name}: {value}")
        return "\n".join(lines)


@dataclass
class ComparisonResult:
    """Result of comparing two models."""

    model_a: str
    model_b: str
    metrics_a: Dict[str, MetricValue]
    metrics_b: Dict[str, MetricValue]
    significance_tests: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    effect_sizes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    winner: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_a": self.model_a,
            "model_b": self.model_b,
            "metrics_a": {k: v.to_dict() for k, v in self.metrics_a.items()},
            "metrics_b": {k: v.to_dict() for k, v in self.metrics_b.items()},
            "significance_tests": self.significance_tests,
            "effect_sizes": self.effect_sizes,
            "winner": self.winner,
        }
