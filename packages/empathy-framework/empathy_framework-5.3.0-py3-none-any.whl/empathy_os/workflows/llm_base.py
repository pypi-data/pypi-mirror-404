"""Base class for LLM-enhanced workflow generation.

Provides reusable patterns for hybrid LLM + template generation with:
- Smart caching for expensive operations
- Fallback to templates when LLM fails
- Quality validation
- Dashboard integration
- Cost tracking

Copyright 2026 Smart-AI-Memory
Licensed under Apache 2.0
"""

import hashlib
import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class LLMWorkflowGenerator(ABC):
    """Base class for LLM-enhanced workflow generation.

    Provides hybrid approach: intelligent LLM generation with fallback templates.

    Usage:
        class TestGeneratorLLM(LLMWorkflowGenerator):
            def _generate_with_template(self, context: dict) -> str:
                return create_template(context)

            def _validate(self, result: str) -> bool:
                return validate_python_syntax(result)

        generator = TestGeneratorLLM(model_tier="capable")
        output = generator.generate(context, prompt)
    """

    def __init__(
        self,
        model_tier: str = "capable",
        enable_cache: bool = True,
        cache_ttl_hours: int = 24,
    ):
        """Initialize LLM workflow generator.

        Args:
            model_tier: Model tier to use (cheap, capable, premium)
            enable_cache: Whether to cache LLM responses
            cache_ttl_hours: Cache time-to-live in hours
        """
        self.model_tier = model_tier
        self.enable_cache = enable_cache
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self._cache: dict[str, tuple[str, datetime]] = {}
        self._stats = {
            "llm_requests": 0,
            "llm_failures": 0,
            "template_fallbacks": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
        }

    def generate(self, context: dict[str, Any], prompt: str) -> str:
        """Generate output with LLM, fallback to template.

        Args:
            context: Context dict for generation
            prompt: LLM prompt

        Returns:
            Generated output (from LLM or template)
        """
        # Check cache first
        if self.enable_cache:
            cache_key = self._make_cache_key(context, prompt)
            cached = self._get_from_cache(cache_key)
            if cached:
                self._stats["cache_hits"] += 1
                logger.debug(f"Cache hit for {cache_key[:16]}...")
                return cached
            self._stats["cache_misses"] += 1

        # Try LLM generation
        try:
            self._stats["llm_requests"] += 1
            result = self._generate_with_llm(prompt)

            # Validate result
            if self._validate(result):
                # Cache successful result
                if self.enable_cache:
                    self._put_in_cache(cache_key, result)

                # Track tokens and cost
                self._update_usage_stats(result)

                logger.info("LLM generation successful")
                return result
            else:
                logger.warning("LLM result failed validation")

        except Exception as e:
            self._stats["llm_failures"] += 1
            logger.warning(f"LLM generation failed: {e}")

        # Fallback to template
        self._stats["template_fallbacks"] += 1
        logger.info("Falling back to template generation")
        return self._generate_with_template(context)

    def _generate_with_llm(self, prompt: str) -> str:
        """Generate using LLM API.

        Args:
            prompt: LLM prompt

        Returns:
            Generated content

        Raises:
            Exception: If LLM generation fails
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package not installed")

        # Get API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        # Get model ID for tier
        model_id = self._get_model_id(self.model_tier)

        # Call Anthropic API
        logger.debug(f"Calling LLM with {self.model_tier} tier (model: {model_id})")
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model_id,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )

        if not response.content:
            raise ValueError("Empty LLM response")

        result = response.content[0].text.strip()

        # Clean up markdown fences if present
        if result.startswith("```python"):
            result = result[len("```python") :].strip()
        elif result.startswith("```"):
            result = result[3:].strip()
        if result.endswith("```"):
            result = result[:-3].strip()

        return result

    def _get_model_id(self, tier: str) -> str:
        """Get model ID for tier.

        Args:
            tier: Model tier (cheap, capable, premium)

        Returns:
            Model ID string
        """
        from empathy_os.models.registry import get_model

        model_info = get_model("anthropic", tier)
        if not model_info:
            raise ValueError(f"No model found for tier: {tier}")

        return model_info.model_id

    def _make_cache_key(self, context: dict[str, Any], prompt: str) -> str:
        """Create cache key from context and prompt.

        Args:
            context: Context dict
            prompt: Prompt string

        Returns:
            Cache key (hex hash)
        """
        # Combine context and prompt for cache key
        cache_data = {
            "context": context,
            "prompt": prompt,
            "model_tier": self.model_tier,
        }
        cache_json = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_json.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> str | None:
        """Get item from cache if not expired.

        Args:
            cache_key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if cache_key not in self._cache:
            return None

        value, timestamp = self._cache[cache_key]

        # Check if expired
        if datetime.now() - timestamp > self.cache_ttl:
            del self._cache[cache_key]
            return None

        return value

    def _put_in_cache(self, cache_key: str, value: str):
        """Put item in cache with current timestamp.

        Args:
            cache_key: Cache key
            value: Value to cache
        """
        self._cache[cache_key] = (value, datetime.now())

    def _update_usage_stats(self, result: str):
        """Update token and cost statistics.

        Args:
            result: Generated result
        """
        # Rough token estimate (4 chars per token)
        estimated_tokens = len(result) // 4
        self._stats["total_tokens"] += estimated_tokens

        # Cost estimation (based on capable tier: $3/M input, $15/M output)
        if self.model_tier == "cheap":
            cost_per_token = 1.0 / 1_000_000  # $1/M tokens
        elif self.model_tier == "capable":
            cost_per_token = 15.0 / 1_000_000  # $15/M output tokens
        elif self.model_tier == "premium":
            cost_per_token = 75.0 / 1_000_000  # $75/M output tokens
        else:
            cost_per_token = 15.0 / 1_000_000

        self._stats["total_cost_usd"] += estimated_tokens * cost_per_token

    def get_stats(self) -> dict[str, Any]:
        """Get generation statistics.

        Returns:
            Dict with usage stats
        """
        stats = self._stats.copy()

        # Calculate rates
        total_requests = stats["llm_requests"]
        if total_requests > 0:
            stats["llm_success_rate"] = (
                total_requests - stats["llm_failures"]
            ) / total_requests
            stats["template_fallback_rate"] = stats["template_fallbacks"] / total_requests
        else:
            stats["llm_success_rate"] = 0.0
            stats["template_fallback_rate"] = 0.0

        # Cache performance
        total_cache_ops = stats["cache_hits"] + stats["cache_misses"]
        if total_cache_ops > 0:
            stats["cache_hit_rate"] = stats["cache_hits"] / total_cache_ops
        else:
            stats["cache_hit_rate"] = 0.0

        return stats

    def clear_cache(self):
        """Clear the cache."""
        self._cache.clear()
        logger.info("Cache cleared")

    @abstractmethod
    def _generate_with_template(self, context: dict[str, Any]) -> str:
        """Generate using template fallback.

        Args:
            context: Context dict with generation data

        Returns:
            Generated output from template

        Note:
            Subclasses must implement this method.
        """
        raise NotImplementedError("Subclass must implement _generate_with_template")

    @abstractmethod
    def _validate(self, result: str) -> bool:
        """Validate generated output.

        Args:
            result: Generated output to validate

        Returns:
            True if valid, False otherwise

        Note:
            Subclasses must implement this method.
        """
        raise NotImplementedError("Subclass must implement _validate")


class TestGeneratorLLM(LLMWorkflowGenerator):
    """Example LLM-enhanced test generator.

    Shows how to use the base class for test generation.
    """

    def _generate_with_template(self, context: dict[str, Any]) -> str:
        """Fallback template generation.

        Args:
            context: Must contain 'module_name', 'module_path'

        Returns:
            Template test file
        """
        module_name = context.get("module_name", "unknown")
        module_path = context.get("module_path", "unknown")

        return f'''"""Behavioral tests for {module_name}.

Generated by template fallback.

Copyright 2026 Smart-AI-Memory
Licensed under Apache 2.0
"""

import pytest

def test_{module_name}_placeholder():
    """Placeholder test - implement actual tests."""
    # TODO: Implement comprehensive tests
    pass
'''

    def _validate(self, result: str) -> bool:
        """Validate test file has basic structure.

        Args:
            result: Generated test file content

        Returns:
            True if valid test file structure
        """
        # Check for basic test file structure
        required = ["import pytest", "def test_", '"""']
        return all(req in result for req in required) and len(result) > 100
