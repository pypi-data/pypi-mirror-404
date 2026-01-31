"""Cache configuration."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CachePolicy(Enum):
    """Cache lookup and storage policies."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    READ_ONLY = "read_only"
    WRITE_ONLY = "write_only"
    REPLAY = "replay"


@dataclass
class CacheConfig:
    """Configuration for response caching.

    Args:
        policy: Cache behavior policy.
        cache_dir: Directory for disk cache.
        ttl_hours: Time-to-live in hours (None = no expiry).
        cache_version: Version string for invalidation.
        max_memory_entries: Max entries for in-memory cache.
    """

    policy: CachePolicy = CachePolicy.DISABLED
    cache_dir: Optional[str] = None
    ttl_hours: Optional[int] = None
    cache_version: str = "1.0"
    max_memory_entries: int = 10000

    def __post_init__(self) -> None:
        if self.ttl_hours is not None and self.ttl_hours <= 0:
            raise ValueError("ttl_hours must be positive")
