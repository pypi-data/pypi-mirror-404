"""Adaptive rate limiting for API calls."""
from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """Thread-safe token bucket rate limiter.

    Supports both RPM (requests per minute) and TPM (tokens per minute) limits.
    """

    def __init__(
        self,
        requests_per_minute: int = 500,
        tokens_per_minute: int = 100000,
    ) -> None:
        self.rpm = requests_per_minute
        self.tpm = tokens_per_minute

        self._request_tokens = float(requests_per_minute)
        self._token_tokens = float(tokens_per_minute)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, estimated_tokens: int = 1) -> float:
        """Acquire permission to make a request.

        Args:
            estimated_tokens: Estimated token count for the request.

        Returns:
            Wait time in seconds (0 if no wait needed).
        """
        with self._lock:
            self._refill()

            wait_time = 0.0

            # Check request limit
            if self._request_tokens < 1:
                wait_time = max(wait_time, 60.0 / self.rpm)

            # Check token limit
            if self._token_tokens < estimated_tokens:
                wait_time = max(
                    wait_time, (estimated_tokens - self._token_tokens) * 60.0 / self.tpm
                )

            if wait_time > 0:
                return wait_time

            self._request_tokens -= 1
            self._token_tokens -= estimated_tokens
            return 0.0

    def report_actual_tokens(self, actual_tokens: int, estimated_tokens: int) -> None:
        """Report actual token usage to correct the bucket.

        Args:
            actual_tokens: Actual tokens used.
            estimated_tokens: Previously estimated tokens.
        """
        with self._lock:
            diff = estimated_tokens - actual_tokens
            self._token_tokens += diff

    def _refill(self) -> None:
        """Refill token buckets based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._last_refill = now

        self._request_tokens = min(
            float(self.rpm), self._request_tokens + elapsed * self.rpm / 60.0
        )
        self._token_tokens = min(
            float(self.tpm), self._token_tokens + elapsed * self.tpm / 60.0
        )


class AsyncRateLimiter:
    """Async-compatible rate limiter using semaphores."""

    def __init__(
        self,
        requests_per_minute: int = 500,
        max_concurrent: int = 10,
    ) -> None:
        self.rpm = requests_per_minute
        self.max_concurrent = max_concurrent
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._min_interval = 60.0 / requests_per_minute
        self._last_request = 0.0

    def _get_semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
        return self._semaphore

    async def acquire(self) -> None:
        """Acquire rate limit permission (async)."""
        semaphore = self._get_semaphore()
        await semaphore.acquire()

        now = time.monotonic()
        elapsed = now - self._last_request
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        self._last_request = time.monotonic()

    def release(self) -> None:
        """Release the semaphore."""
        if self._semaphore is not None:
            self._semaphore.release()
