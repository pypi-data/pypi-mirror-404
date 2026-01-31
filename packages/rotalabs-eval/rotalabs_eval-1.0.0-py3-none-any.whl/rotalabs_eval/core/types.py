"""Type definitions for rotalabs-eval."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, TypeVar, Union

# Type aliases
MetricScores = List[float]
PromptTemplate = str
JsonDict = Dict[str, Any]

T = TypeVar("T")


@dataclass
class ModelResponse:
    """Standardized model response across all providers."""

    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    finish_reason: Optional[str] = None
    error: Optional[str] = None
    model_name: Optional[str] = None
    provider: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def success(self) -> bool:
        return self.error is None and self.text is not None
