"""Batch inference coordinator."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence

import pandas as pd
from tqdm import tqdm

from rotalabs_eval.core.config import InferenceConfig, ModelConfig
from rotalabs_eval.inference.base import InferenceEngine, InferenceRequest, InferenceResponse
from rotalabs_eval.inference.rate_limiter import TokenBucketRateLimiter

logger = logging.getLogger(__name__)


def create_engine(model_config: ModelConfig) -> InferenceEngine:
    """Create an inference engine from model config.

    Args:
        model_config: Model configuration.

    Returns:
        Configured inference engine.
    """
    from rotalabs_eval.core.config import ModelProvider

    if model_config.provider == ModelProvider.OPENAI:
        from rotalabs_eval.inference.openai import OpenAIEngine

        return OpenAIEngine(
            model_name=model_config.model_name,
            api_key=model_config.get_api_key(),
            api_base=model_config.api_base,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
            extra_params=model_config.extra_params,
        )
    elif model_config.provider == ModelProvider.OLLAMA:
        from rotalabs_eval.inference.ollama import OllamaEngine

        return OllamaEngine(
            model_name=model_config.model_name,
            host=model_config.api_base or "http://localhost:11434",
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
            extra_params=model_config.extra_params,
        )
    else:
        raise ValueError(f"Unsupported provider: {model_config.provider}")


def run_batch_inference(
    prompts: List[str],
    model_config: ModelConfig,
    inference_config: Optional[InferenceConfig] = None,
    show_progress: bool = True,
) -> List[InferenceResponse]:
    """Run batch inference on a list of prompts.

    Args:
        prompts: List of prompt strings.
        model_config: Model configuration.
        inference_config: Inference configuration.
        show_progress: Whether to show progress bar.

    Returns:
        List of inference responses.
    """
    if inference_config is None:
        inference_config = InferenceConfig()

    engine = create_engine(model_config)
    rate_limiter = TokenBucketRateLimiter(
        requests_per_minute=inference_config.requests_per_minute,
        tokens_per_minute=inference_config.tokens_per_minute,
    )

    responses: List[InferenceResponse] = []
    iterator = tqdm(prompts, desc="Inference", disable=not show_progress)

    for i, prompt in enumerate(iterator):
        # Rate limit
        wait_time = rate_limiter.acquire(estimated_tokens=len(prompt) // 4)
        if wait_time > 0:
            import time
            time.sleep(wait_time)

        request = InferenceRequest(
            prompt=prompt,
            max_tokens=model_config.max_tokens,
            temperature=model_config.temperature,
            request_id=str(i),
        )
        response = engine.generate(request)
        responses.append(response)

        # Report actual tokens
        if response.success:
            rate_limiter.report_actual_tokens(
                response.total_tokens, len(prompt) // 4
            )

    engine.close()
    return responses
