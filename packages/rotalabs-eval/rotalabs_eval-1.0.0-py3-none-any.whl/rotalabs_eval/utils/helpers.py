"""Common utility functions."""
from __future__ import annotations

import json
import logging
import os
import re
from functools import lru_cache
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def safe_json_parse(text: str) -> Optional[Dict[str, Any]]:
    """Safely parse JSON from LLM output.

    Handles common issues like markdown code blocks and trailing text.

    Args:
        text: Text potentially containing JSON.

    Returns:
        Parsed dict or None.
    """
    if not text:
        return None

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding JSON object in text
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Try nested JSON objects
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


@lru_cache(maxsize=8)
def get_api_key(provider: str) -> Optional[str]:
    """Get API key from environment, with caching.

    Args:
        provider: Provider name (openai, anthropic, google, etc).

    Returns:
        API key or None.
    """
    env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "wandb": "WANDB_API_KEY",
    }
    env_var = env_map.get(provider.lower())
    if env_var:
        return os.environ.get(env_var)
    return None


def handle_batch_errors(func):
    """Decorator for batch processing with error handling.

    Catches per-item errors without failing the whole batch.
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Batch error in {func.__name__}: {e}")
            return None
    return wrapper
