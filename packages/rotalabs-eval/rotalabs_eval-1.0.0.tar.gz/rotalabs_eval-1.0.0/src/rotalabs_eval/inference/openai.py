"""OpenAI inference engine."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Sequence

from rotalabs_eval.core.exceptions import EvalInferenceError
from rotalabs_eval.inference.base import InferenceEngine, InferenceRequest, InferenceResponse

logger = logging.getLogger(__name__)

# Pricing per 1M tokens (input, output)
OPENAI_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "o1": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
    "o3-mini": {"input": 1.10, "output": 4.40},
}


class OpenAIEngine(InferenceEngine):
    """OpenAI inference engine.

    Supports GPT-4, GPT-4o, GPT-3.5, and o-series models.
    """

    name = "openai"

    def __init__(
        self,
        model_name: str = "gpt-4o",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 60,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.model_name = model_name
        self.api_key = api_key
        self.api_base = api_base
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.extra_params = extra_params or {}
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import openai
            except ImportError:
                raise ImportError(
                    "openai package required. Install with: pip install rotalabs-eval[openai]"
                )

            kwargs: Dict[str, Any] = {"timeout": self.timeout}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.api_base:
                kwargs["base_url"] = self.api_base

            self._client = openai.OpenAI(**kwargs)
        return self._client

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        """Generate a response using OpenAI API."""
        client = self._get_client()

        messages = [{"role": "user", "content": request.prompt}]
        kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        if request.stop_sequences:
            kwargs["stop"] = request.stop_sequences

        kwargs.update(self.extra_params)

        last_error = None
        for attempt in range(self.max_retries):
            try:
                start = time.time()
                response = client.chat.completions.create(**kwargs)
                latency_ms = (time.time() - start) * 1000

                choice = response.choices[0]
                usage = response.usage

                cost = self._calculate_cost(
                    usage.prompt_tokens, usage.completion_tokens
                )

                return InferenceResponse(
                    text=choice.message.content,
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    latency_ms=latency_ms,
                    cost_usd=cost,
                    finish_reason=choice.finish_reason,
                    request_id=request.request_id,
                )
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"OpenAI request failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)

        return InferenceResponse(
            error=str(last_error),
            request_id=request.request_id,
        )

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD."""
        pricing = OPENAI_PRICING.get(self.model_name)
        if not pricing:
            return 0.0
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
