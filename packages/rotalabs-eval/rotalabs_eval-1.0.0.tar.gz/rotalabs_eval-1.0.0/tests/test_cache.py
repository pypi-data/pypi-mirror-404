"""Tests for cache module."""
from __future__ import annotations

import tempfile

import pytest

from rotalabs_eval.cache.config import CacheConfig, CachePolicy
from rotalabs_eval.cache.disk import DiskCache
from rotalabs_eval.cache.memory import MemoryCache


class TestMemoryCache:
    def test_put_get(self):
        cache = MemoryCache(max_entries=10)
        cache.put("prompt", "model", 0.0, {"text": "response"})
        result = cache.get("prompt", "model", 0.0)
        assert result == {"text": "response"}

    def test_miss(self):
        cache = MemoryCache()
        assert cache.get("nonexistent", "model", 0.0) is None

    def test_lru_eviction(self):
        cache = MemoryCache(max_entries=2)
        cache.put("a", "m", 0.0, {"text": "1"})
        cache.put("b", "m", 0.0, {"text": "2"})
        cache.put("c", "m", 0.0, {"text": "3"})
        assert cache.get("a", "m", 0.0) is None
        assert cache.get("c", "m", 0.0) is not None

    def test_hit_rate(self):
        cache = MemoryCache()
        cache.put("a", "m", 0.0, {"text": "1"})
        cache.get("a", "m", 0.0)  # hit
        cache.get("b", "m", 0.0)  # miss
        assert cache.hit_rate == 50.0

    def test_clear(self):
        cache = MemoryCache()
        cache.put("a", "m", 0.0, {"text": "1"})
        cache.clear()
        assert cache.size == 0


class TestDiskCache:
    def test_put_get(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CacheConfig(policy=CachePolicy.ENABLED, cache_dir=tmpdir)
            cache = DiskCache(config)
            cache.store("prompt", "gpt-4", "openai", 0.0, 1024, "response text", 100, 50, 0.01, 500.0)
            result = cache.lookup("prompt", "gpt-4", "openai", 0.0, 1024)
            assert result is not None
            assert result["response_text"] == "response text"
            cache.close()

    def test_disabled(self):
        config = CacheConfig(policy=CachePolicy.DISABLED)
        cache = DiskCache(config)
        result = cache.lookup("prompt", "gpt-4", "openai", 0.0, 1024)
        assert result is None
