"""Tests for utility functions."""
from __future__ import annotations

import pytest

from rotalabs_eval.utils.helpers import safe_json_parse
from rotalabs_eval.utils.cost import estimate_cost, estimate_eval_cost
from rotalabs_eval.utils.tiktoken_cache import count_tokens, estimate_tokens


class TestSafeJsonParse:
    def test_valid_json(self):
        result = safe_json_parse('{"score": 5, "reasoning": "good"}')
        assert result == {"score": 5, "reasoning": "good"}

    def test_markdown_block(self):
        result = safe_json_parse('```json\n{"score": 3}\n```')
        assert result == {"score": 3}

    def test_embedded_json(self):
        result = safe_json_parse('The score is {"score": 4} based on analysis.')
        assert result == {"score": 4}

    def test_invalid(self):
        result = safe_json_parse("no json here")
        assert result is None

    def test_empty(self):
        assert safe_json_parse("") is None


class TestCostEstimation:
    def test_known_model(self):
        cost = estimate_cost("gpt-4o", 1000, 500)
        assert cost > 0

    def test_unknown_model(self):
        cost = estimate_cost("unknown-model-xyz", 1000, 500)
        assert cost == 0.0

    def test_eval_cost(self):
        result = estimate_eval_cost("gpt-4o", 100)
        assert result["estimated_cost_usd"] > 0
        assert result["total_input_tokens"] == 50000


class TestTokenization:
    def test_count_tokens(self):
        n = count_tokens("Hello, world!")
        assert n > 0

    def test_estimate_tokens(self):
        n = estimate_tokens("Hello, world!")
        assert n > 0
