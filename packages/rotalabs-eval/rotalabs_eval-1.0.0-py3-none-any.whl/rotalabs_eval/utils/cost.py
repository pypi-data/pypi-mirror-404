"""Cost tracking and estimation utilities."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Pricing per 1M tokens: (input_price, output_price)
MODEL_PRICING: Dict[str, Tuple[float, float]] = {
    # OpenAI
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-4": (30.00, 60.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "o1": (15.00, 60.00),
    "o1-mini": (3.00, 12.00),
    "o3-mini": (1.10, 4.40),
    # Anthropic
    "claude-3-opus": (15.00, 75.00),
    "claude-3.5-sonnet": (3.00, 15.00),
    "claude-3-haiku": (0.25, 1.25),
    # Google
    "gemini-1.5-pro": (1.25, 5.00),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-2.0-flash": (0.10, 0.40),
}


def estimate_cost(
    model_name: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """Estimate cost in USD for a request.

    Args:
        model_name: Model identifier.
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.

    Returns:
        Estimated cost in USD.
    """
    pricing = MODEL_PRICING.get(model_name)
    if not pricing:
        # Try partial match
        for key, price in MODEL_PRICING.items():
            if key in model_name or model_name in key:
                pricing = price
                break

    if not pricing:
        return 0.0

    input_cost = (input_tokens / 1_000_000) * pricing[0]
    output_cost = (output_tokens / 1_000_000) * pricing[1]
    return input_cost + output_cost


def estimate_eval_cost(
    model_name: str,
    num_examples: int,
    avg_input_tokens: int = 500,
    avg_output_tokens: int = 200,
) -> Dict[str, float]:
    """Estimate total cost for an evaluation run.

    Args:
        model_name: Model identifier.
        num_examples: Number of examples.
        avg_input_tokens: Average input tokens per example.
        avg_output_tokens: Average output tokens per example.

    Returns:
        Dict with cost breakdown.
    """
    total_input = num_examples * avg_input_tokens
    total_output = num_examples * avg_output_tokens
    total = estimate_cost(model_name, total_input, total_output)

    return {
        "estimated_cost_usd": round(total, 4),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "cost_per_example": round(total / num_examples, 6) if num_examples > 0 else 0.0,
        "model": model_name,
    }
