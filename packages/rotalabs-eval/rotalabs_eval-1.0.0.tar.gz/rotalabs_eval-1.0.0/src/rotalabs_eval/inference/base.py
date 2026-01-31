"""Abstract base class for inference engines."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class InferenceRequest:
    """A single inference request.

    Args:
        prompt: Input prompt text.
        max_tokens: Maximum output tokens.
        temperature: Sampling temperature.
        stop_sequences: Optional stop sequences.
        request_id: Optional request identifier.
        metadata: Additional request metadata.
    """

    prompt: str
    max_tokens: int = 1024
    temperature: float = 0.0
    stop_sequences: Optional[List[str]] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceResponse:
    """Response from an inference request.

    Args:
        text: Generated text.
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.
        latency_ms: Request latency in milliseconds.
        cost_usd: Estimated cost in USD.
        finish_reason: Reason generation stopped.
        error: Error message if failed.
        request_id: Matching request identifier.
    """

    text: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    finish_reason: Optional[str] = None
    error: Optional[str] = None
    request_id: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and self.text is not None

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class InferenceEngine(ABC):
    """Abstract base class for LLM inference engines.

    Subclasses must implement generate() and optionally generate_batch().
    """

    name: str = "base"

    @abstractmethod
    def generate(self, request: InferenceRequest) -> InferenceResponse:
        """Generate a response for a single request.

        Args:
            request: Inference request.

        Returns:
            Inference response.
        """
        ...

    def generate_batch(
        self, requests: Sequence[InferenceRequest]
    ) -> List[InferenceResponse]:
        """Generate responses for a batch of requests.

        Default implementation processes sequentially.

        Args:
            requests: Sequence of inference requests.

        Returns:
            List of inference responses.
        """
        return [self.generate(req) for req in requests]

    def validate_config(self) -> None:
        """Validate engine configuration. Override in subclasses."""
        pass

    def close(self) -> None:
        """Cleanup resources. Override in subclasses."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
