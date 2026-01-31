"""Ollama local inference engine."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Sequence

from rotalabs_eval.core.exceptions import EvalInferenceError
from rotalabs_eval.inference.base import InferenceEngine, InferenceRequest, InferenceResponse

logger = logging.getLogger(__name__)


class OllamaEngine(InferenceEngine):
    """Ollama local inference engine.

    Supports running local models via the Ollama API.
    """

    name = "ollama"

    def __init__(
        self,
        model_name: str = "llama3",
        host: str = "http://localhost:11434",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        timeout: int = 120,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.model_name = model_name
        self.host = host
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.extra_params = extra_params or {}
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import ollama
            except ImportError:
                raise ImportError(
                    "ollama package required. Install with: pip install rotalabs-eval[ollama]"
                )
            self._client = ollama.Client(host=self.host, timeout=self.timeout)
        return self._client

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        """Generate a response using Ollama."""
        client = self._get_client()

        options: Dict[str, Any] = {
            "temperature": request.temperature,
            "num_predict": request.max_tokens,
        }
        if request.stop_sequences:
            options["stop"] = request.stop_sequences
        options.update(self.extra_params)

        try:
            start = time.time()
            response = client.generate(
                model=self.model_name,
                prompt=request.prompt,
                options=options,
            )
            latency_ms = (time.time() - start) * 1000

            return InferenceResponse(
                text=response.get("response", ""),
                input_tokens=response.get("prompt_eval_count", 0),
                output_tokens=response.get("eval_count", 0),
                latency_ms=latency_ms,
                cost_usd=0.0,  # Local inference is free
                finish_reason="stop" if response.get("done") else None,
                request_id=request.request_id,
            )
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            return InferenceResponse(
                error=str(e),
                request_id=request.request_id,
            )
