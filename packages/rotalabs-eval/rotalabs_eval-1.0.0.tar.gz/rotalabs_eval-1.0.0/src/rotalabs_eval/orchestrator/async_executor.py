"""Async inference executor with configurable concurrency."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from rotalabs_eval.core.config import InferenceConfig, ModelConfig
from rotalabs_eval.inference.base import InferenceRequest, InferenceResponse
from rotalabs_eval.inference.rate_limiter import AsyncRateLimiter

logger = logging.getLogger(__name__)


class AsyncExecutor:
    """Async inference executor with concurrency control.

    Runs multiple inference requests concurrently using asyncio,
    with rate limiting and error handling.
    """

    def __init__(
        self,
        model_config: ModelConfig,
        inference_config: Optional[InferenceConfig] = None,
    ) -> None:
        self.model_config = model_config
        self.config = inference_config or InferenceConfig()
        self.rate_limiter = AsyncRateLimiter(
            requests_per_minute=self.config.requests_per_minute,
            max_concurrent=self.config.concurrency,
        )

    async def _generate_one(
        self,
        prompt: str,
        request_id: str,
    ) -> InferenceResponse:
        """Generate a single response with rate limiting."""
        await self.rate_limiter.acquire()
        try:
            from rotalabs_eval.inference.batch import create_engine

            engine = create_engine(self.model_config)
            request = InferenceRequest(
                prompt=prompt,
                max_tokens=self.model_config.max_tokens,
                temperature=self.model_config.temperature,
                request_id=request_id,
            )
            return engine.generate(request)
        except Exception as e:
            logger.error(f"Async inference failed for {request_id}: {e}")
            return InferenceResponse(error=str(e), request_id=request_id)
        finally:
            self.rate_limiter.release()

    async def run_async(
        self,
        prompts: List[str],
    ) -> List[InferenceResponse]:
        """Run inference on all prompts concurrently.

        Args:
            prompts: List of prompt strings.

        Returns:
            List of inference responses.
        """
        tasks = [
            self._generate_one(prompt, str(i))
            for i, prompt in enumerate(prompts)
        ]
        return await asyncio.gather(*tasks)

    def run(self, prompts: List[str]) -> List[InferenceResponse]:
        """Synchronous wrapper for run_async."""
        return asyncio.run(self.run_async(prompts))
