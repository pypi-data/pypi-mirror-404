"""In-memory LRU cache for LLM responses."""
from __future__ import annotations

import hashlib
import json
import logging
from collections import OrderedDict
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MemoryCache:
    """Thread-safe in-memory LRU cache for LLM responses.

    Useful for non-distributed environments where disk cache is overkill.
    """

    def __init__(self, max_entries: int = 10000) -> None:
        self.max_entries = max_entries
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def _make_key(self, prompt: str, model: str, temperature: float) -> str:
        data = json.dumps(
            {"prompt": prompt.strip(), "model": model, "temp": round(temperature, 4)},
            sort_keys=True,
        )
        return hashlib.sha256(data.encode()).hexdigest()

    def get(self, prompt: str, model: str, temperature: float = 0.0) -> Optional[Dict[str, Any]]:
        """Look up cached response."""
        key = self._make_key(prompt, model, temperature)
        if key in self._cache:
            self._hits += 1
            self._cache.move_to_end(key)
            return self._cache[key]
        self._misses += 1
        return None

    def put(
        self,
        prompt: str,
        model: str,
        temperature: float,
        response: Dict[str, Any],
    ) -> None:
        """Store response in cache."""
        key = self._make_key(prompt, model, temperature)
        self._cache[key] = response
        self._cache.move_to_end(key)
        while len(self._cache) > self.max_entries:
            self._cache.popitem(last=False)

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return (self._hits / total * 100) if total > 0 else 0.0

    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0
