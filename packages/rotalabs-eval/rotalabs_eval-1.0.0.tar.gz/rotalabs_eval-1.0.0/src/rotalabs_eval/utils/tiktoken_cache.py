"""Cached tokenization utilities."""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)


@lru_cache(maxsize=4)
def _get_encoding(model_name: str):
    """Get tiktoken encoding for a model, with caching."""
    try:
        import tiktoken
    except ImportError:
        raise ImportError("tiktoken required. Install with: pip install tiktoken")

    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens in text for a given model.

    Args:
        text: Input text.
        model: Model name for tokenizer selection.

    Returns:
        Token count.
    """
    encoding = _get_encoding(model)
    return len(encoding.encode(text))


def estimate_tokens(text: str) -> int:
    """Quick token estimation without tiktoken (4 chars per token).

    Args:
        text: Input text.

    Returns:
        Estimated token count.
    """
    return max(1, len(text) // 4)


def truncate_to_tokens(
    text: str,
    max_tokens: int,
    model: str = "gpt-4o",
) -> str:
    """Truncate text to a maximum number of tokens.

    Args:
        text: Input text.
        max_tokens: Maximum token count.
        model: Model name for tokenizer.

    Returns:
        Truncated text.
    """
    encoding = _get_encoding(model)
    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return encoding.decode(tokens[:max_tokens])
