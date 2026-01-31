"""SQLite-based disk cache for LLM responses."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import time
from typing import Any, Dict, Optional

from rotalabs_eval.cache.config import CacheConfig, CachePolicy
from rotalabs_eval.core.exceptions import EvalCacheError

logger = logging.getLogger(__name__)


def _generate_cache_key(
    prompt: str,
    model_name: str,
    provider: str,
    temperature: float,
    max_tokens: int,
    extra_params: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate content-addressable cache key."""
    normalized = prompt.strip().replace("\r\n", "\n")
    key_data: Dict[str, Any] = {
        "prompt": normalized,
        "model": model_name,
        "provider": provider,
        "temperature": round(temperature, 4),
        "max_tokens": max_tokens,
    }
    if extra_params:
        filtered = {
            k: v for k, v in sorted(extra_params.items())
            if k not in ("stream", "user", "request_id")
        }
        if filtered:
            key_data["extra"] = filtered

    canonical = json.dumps(key_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class DiskCache:
    """SQLite-backed response cache.

    Provides persistent caching of LLM responses with TTL support.
    """

    def __init__(self, config: CacheConfig) -> None:
        self.config = config
        self._db: Optional[sqlite3.Connection] = None
        self._hits = 0
        self._misses = 0

        if config.policy != CachePolicy.DISABLED and config.cache_dir:
            os.makedirs(config.cache_dir, exist_ok=True)
            self._init_db()

    def _init_db(self) -> None:
        db_path = os.path.join(self.config.cache_dir, "cache.db")
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                cache_key TEXT PRIMARY KEY,
                response_text TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cost_usd REAL,
                latency_ms REAL,
                model_name TEXT,
                provider TEXT,
                cache_version TEXT,
                created_at REAL,
                access_count INTEGER DEFAULT 1
            )
        """)
        self._db.commit()

    def lookup(
        self,
        prompt: str,
        model_name: str,
        provider: str,
        temperature: float,
        max_tokens: int,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Look up a cached response."""
        if self.config.policy in (CachePolicy.DISABLED, CachePolicy.WRITE_ONLY):
            return None
        if self._db is None:
            return None

        key = _generate_cache_key(prompt, model_name, provider, temperature, max_tokens, extra_params)

        cursor = self._db.execute(
            "SELECT response_text, input_tokens, output_tokens, cost_usd, latency_ms, created_at "
            "FROM cache WHERE cache_key = ? AND cache_version = ?",
            (key, self.config.cache_version),
        )
        row = cursor.fetchone()

        if row is None:
            self._misses += 1
            return None

        # Check TTL
        if self.config.ttl_hours:
            created_at = row[5]
            if time.time() - created_at > self.config.ttl_hours * 3600:
                self._misses += 1
                return None

        self._hits += 1

        # Update access count
        self._db.execute(
            "UPDATE cache SET access_count = access_count + 1 WHERE cache_key = ?",
            (key,),
        )
        self._db.commit()

        return {
            "response_text": row[0],
            "input_tokens": row[1],
            "output_tokens": row[2],
            "cost_usd": row[3],
            "latency_ms": row[4],
        }

    def store(
        self,
        prompt: str,
        model_name: str,
        provider: str,
        temperature: float,
        max_tokens: int,
        response_text: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        latency_ms: float = 0.0,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store a response in the cache."""
        if self.config.policy in (CachePolicy.DISABLED, CachePolicy.READ_ONLY):
            return
        if self._db is None:
            return

        key = _generate_cache_key(prompt, model_name, provider, temperature, max_tokens, extra_params)

        self._db.execute(
            """INSERT OR REPLACE INTO cache
            (cache_key, response_text, input_tokens, output_tokens, cost_usd, latency_ms,
             model_name, provider, cache_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (key, response_text, input_tokens, output_tokens, cost_usd, latency_ms,
             model_name, provider, self.config.cache_version, time.time()),
        )
        self._db.commit()

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return (self._hits / total * 100) if total > 0 else 0.0

    def close(self) -> None:
        if self._db:
            self._db.close()
            self._db = None
