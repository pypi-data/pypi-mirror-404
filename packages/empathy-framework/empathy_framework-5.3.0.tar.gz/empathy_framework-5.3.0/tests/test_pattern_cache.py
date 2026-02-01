"""Test Pattern Cache Module

Tests the PatternMatchCache class and cached_pattern_query decorator.

Copyright 2025 Smart AI Memory, LLC
Licensed under Fair Source 0.9
"""

from unittest.mock import MagicMock

import pytest

from empathy_os.cache_monitor import CacheMonitor
from empathy_os.pattern_cache import PatternMatchCache, cached_pattern_query


class TestPatternMatchCache:
    """Test PatternMatchCache class"""

    @pytest.fixture(autouse=True)
    def reset_monitor(self):
        """Reset singleton CacheMonitor before each test"""
        CacheMonitor.reset_instance()
        yield
        CacheMonitor.reset_instance()

    def test_init_registers_with_monitor(self):
        """Test cache registration with CacheMonitor"""
        PatternMatchCache(max_size=500)

        monitor = CacheMonitor.get_instance()
        stats = monitor.get_stats("pattern_match")

        assert stats is not None
        assert stats.name == "pattern_match"
        assert stats.max_size == 500

    def test_init_handles_duplicate_registration(self):
        """Test that duplicate registration doesn't raise error"""
        PatternMatchCache(max_size=500)
        PatternMatchCache(max_size=1000)  # Should not raise

        # Should have been registered once with first max_size
        monitor = CacheMonitor.get_instance()
        stats = monitor.get_stats("pattern_match")
        assert stats.max_size == 500  # First registration wins

    def test_make_key_creates_deterministic_key(self):
        """Test cache key generation is deterministic"""
        cache = PatternMatchCache()

        context1 = {"domain": "testing", "language": "python", "priority": 1}
        context2 = {"language": "python", "domain": "testing", "priority": 1}

        key1 = cache._make_key(context1)
        key2 = cache._make_key(context2)

        # Keys should be identical despite different key order
        assert key1 == key2
        assert isinstance(key1, str)

    def test_make_key_different_for_different_contexts(self):
        """Test different contexts produce different keys"""
        cache = PatternMatchCache()

        context1 = {"domain": "testing", "language": "python"}
        context2 = {"domain": "testing", "language": "javascript"}

        key1 = cache._make_key(context1)
        key2 = cache._make_key(context2)

        assert key1 != key2

    def test_get_cache_miss(self):
        """Test cache miss returns None"""
        cache = PatternMatchCache()
        context = {"query": "test"}

        result = cache.get(context)

        assert result is None

        # Verify miss was recorded
        monitor = CacheMonitor.get_instance()
        stats = monitor.get_stats("pattern_match")
        assert stats.misses == 1
        assert stats.hits == 0

    def test_get_cache_hit(self):
        """Test cache hit returns stored value"""
        cache = PatternMatchCache()
        context = {"query": "test"}
        expected_result = ["match1", "match2"]

        # Store value
        cache.set(context, expected_result)

        # Retrieve value
        result = cache.get(context)

        assert result == expected_result

        # Verify hit was recorded
        monitor = CacheMonitor.get_instance()
        stats = monitor.get_stats("pattern_match")
        assert stats.hits == 1

    def test_get_updates_lru_order(self):
        """Test that get() updates LRU access order"""
        cache = PatternMatchCache(max_size=3)

        # Add 3 items
        cache.set({"id": 1}, "value1")
        cache.set({"id": 2}, "value2")
        cache.set({"id": 3}, "value3")

        # Access item 1 (moves to end)
        cache.get({"id": 1})

        # Add 4th item (should evict item 2, not item 1)
        cache.set({"id": 4}, "value4")

        # Item 1 should still be cached (was accessed recently)
        assert cache.get({"id": 1}) == "value1"

        # Item 2 should be evicted (oldest unaccessed)
        assert cache.get({"id": 2}) is None

    def test_set_stores_value(self):
        """Test set() stores value in cache"""
        cache = PatternMatchCache()
        context = {"test": "context"}
        value = {"result": "data"}

        cache.set(context, value)

        # Verify stored
        assert cache.get(context) == value

    def test_set_updates_existing_value(self):
        """Test set() updates existing cache entry"""
        cache = PatternMatchCache()
        context = {"id": 1}

        cache.set(context, "old_value")
        cache.set(context, "new_value")

        assert cache.get(context) == "new_value"
        assert len(cache._cache) == 1  # Only one entry

    def test_set_evicts_oldest_when_full(self):
        """Test LRU eviction when cache is full"""
        cache = PatternMatchCache(max_size=3)

        # Fill cache
        cache.set({"id": 1}, "value1")
        cache.set({"id": 2}, "value2")
        cache.set({"id": 3}, "value3")

        # Add 4th item
        cache.set({"id": 4}, "value4")

        # First item should be evicted
        assert cache.get({"id": 1}) is None
        assert cache.get({"id": 4}) == "value4"

        # Verify eviction was recorded
        monitor = CacheMonitor.get_instance()
        stats = monitor.get_stats("pattern_match")
        assert stats.evictions == 1

    def test_set_updates_monitor_size(self):
        """Test that set() updates cache size in monitor"""
        cache = PatternMatchCache(max_size=100)
        monitor = CacheMonitor.get_instance()

        cache.set({"id": 1}, "value1")
        stats = monitor.get_stats("pattern_match")
        assert stats.size == 1

        cache.set({"id": 2}, "value2")
        stats = monitor.get_stats("pattern_match")
        assert stats.size == 2

    def test_clear_removes_all_entries(self):
        """Test clear() removes all cached entries"""
        cache = PatternMatchCache()

        # Add some entries
        cache.set({"id": 1}, "value1")
        cache.set({"id": 2}, "value2")
        cache.set({"id": 3}, "value3")

        # Clear cache
        cache.clear()

        # Verify empty
        assert len(cache._cache) == 0
        assert len(cache._access_order) == 0
        assert cache.get({"id": 1}) is None

    def test_clear_updates_monitor_size(self):
        """Test that clear() updates monitor size to 0"""
        cache = PatternMatchCache()
        cache.set({"id": 1}, "value1")
        cache.set({"id": 2}, "value2")

        cache.clear()

        monitor = CacheMonitor.get_instance()
        stats = monitor.get_stats("pattern_match")
        assert stats.size == 0

    def test_get_or_compute_cache_hit(self):
        """Test get_or_compute returns cached value on hit"""
        cache = PatternMatchCache()
        context = {"query": "test"}
        cached_value = "cached_result"

        # Pre-populate cache
        cache.set(context, cached_value)

        # Compute function should NOT be called
        compute_fn = MagicMock(return_value="computed_result")

        result = cache.get_or_compute(context, compute_fn)

        assert result == cached_value
        compute_fn.assert_not_called()

    def test_get_or_compute_cache_miss(self):
        """Test get_or_compute computes and caches on miss"""
        cache = PatternMatchCache()
        context = {"query": "test"}
        computed_value = "computed_result"

        compute_fn = MagicMock(return_value=computed_value)

        result = cache.get_or_compute(context, compute_fn)

        assert result == computed_value
        compute_fn.assert_called_once()

        # Verify value was cached
        assert cache.get(context) == computed_value

    def test_get_or_compute_with_none_result(self):
        """Test get_or_compute handles None results (treated as cache miss)"""
        cache = PatternMatchCache()
        context = {"query": "test"}

        # First call returns None
        compute_fn = MagicMock(return_value=None)
        result = cache.get_or_compute(context, compute_fn)

        assert result is None

        # Second call should compute again (None is not cached effectively)
        cache.get_or_compute(context, compute_fn)
        assert compute_fn.call_count == 2

    def test_large_cache_performance(self):
        """Test cache handles large number of entries"""
        cache = PatternMatchCache(max_size=10000)

        # Add many entries
        for i in range(10000):
            cache.set({"id": i}, f"value{i}")

        # Verify size limit
        assert len(cache._cache) == 10000

        # Add one more (should evict oldest)
        cache.set({"id": 10000}, "value10000")
        assert len(cache._cache) == 10000
        assert cache.get({"id": 0}) is None  # First item evicted

    def test_cache_with_complex_contexts(self):
        """Test cache handles complex nested contexts"""
        cache = PatternMatchCache()

        context = {
            "domain": "testing",
            "metadata": {"timestamp": 123456, "user": "test_user"},
            "filters": ["filter1", "filter2"],
            "nested": {"level2": {"level3": "value"}},
        }

        cache.set(context, "result")
        assert cache.get(context) == "result"

    def test_cache_key_uniqueness_with_similar_contexts(self):
        """Test cache keys are unique for similar but different contexts"""
        cache = PatternMatchCache()

        context1 = {"a": 1, "b": 2}
        context2 = {"a": 1, "b": 3}
        context3 = {"a": 2, "b": 2}

        cache.set(context1, "result1")
        cache.set(context2, "result2")
        cache.set(context3, "result3")

        assert cache.get(context1) == "result1"
        assert cache.get(context2) == "result2"
        assert cache.get(context3) == "result3"


class TestCachedPatternQueryDecorator:
    """Test cached_pattern_query decorator"""

    @pytest.fixture(autouse=True)
    def reset_monitor(self):
        """Reset singleton CacheMonitor before each test"""
        CacheMonitor.reset_instance()
        yield
        CacheMonitor.reset_instance()

    def test_decorator_caches_method_results(self):
        """Test decorator caches method results"""
        cache = PatternMatchCache()

        class TestClass:
            def __init__(self):
                self.call_count = 0

            @cached_pattern_query(cache)
            def query_patterns(self, context: dict, **kwargs):
                self.call_count += 1
                return f"result_{self.call_count}"

        obj = TestClass()
        context = {"query": "test"}

        # First call
        result1 = obj.query_patterns(context)
        assert result1 == "result_1"
        assert obj.call_count == 1

        # Second call (should use cache)
        result2 = obj.query_patterns(context)
        assert result2 == "result_1"  # Same result
        assert obj.call_count == 1  # Not called again

    def test_decorator_includes_kwargs_in_cache_key(self):
        """Test decorator includes kwargs in cache key"""
        cache = PatternMatchCache()

        class TestClass:
            @cached_pattern_query(cache)
            def query_patterns(self, context: dict, min_confidence: float = 0.5):
                return f"confidence_{min_confidence}"

        obj = TestClass()
        context = {"query": "test"}

        # Different kwargs should produce different results
        result1 = obj.query_patterns(context, min_confidence=0.5)
        result2 = obj.query_patterns(context, min_confidence=0.8)

        assert result1 == "confidence_0.5"
        assert result2 == "confidence_0.8"

        # Same kwargs should use cache
        result3 = obj.query_patterns(context, min_confidence=0.5)
        assert result3 == "confidence_0.5"

    def test_decorator_preserves_function_metadata(self):
        """Test decorator preserves function name and docstring"""
        cache = PatternMatchCache()

        class TestClass:
            @cached_pattern_query(cache)
            def query_patterns(self, context: dict, **kwargs):
                """Query patterns with caching"""
                return "result"

        obj = TestClass()

        assert obj.query_patterns.__name__ == "query_patterns"
        assert obj.query_patterns.__doc__ == "Query patterns with caching"

    def test_decorator_with_multiple_instances(self):
        """Test decorator works correctly with multiple class instances"""
        cache = PatternMatchCache()

        class TestClass:
            def __init__(self, prefix: str):
                self.prefix = prefix

            @cached_pattern_query(cache)
            def query_patterns(self, context: dict, **kwargs):
                return f"{self.prefix}_{context['query']}"

        obj1 = TestClass("obj1")
        obj2 = TestClass("obj2")

        context = {"query": "test"}

        # Both objects share the same cache
        result1 = obj1.query_patterns(context)
        result2 = obj2.query_patterns(context)

        # Second call uses cached result from first call
        assert result1 == "obj1_test"
        assert result2 == "obj1_test"  # Uses cached result from obj1

    def test_decorator_with_empty_kwargs(self):
        """Test decorator handles methods with no kwargs"""
        cache = PatternMatchCache()

        class TestClass:
            @cached_pattern_query(cache)
            def query_patterns(self, context: dict):
                return context["result"]

        obj = TestClass()
        context = {"result": "test_value"}

        result = obj.query_patterns(context)
        assert result == "test_value"

        # Verify caching works
        context["result"] = "new_value"
        result2 = obj.query_patterns({"result": "test_value"})
        assert result2 == "test_value"  # Cached

    def test_decorator_with_complex_kwargs(self):
        """Test decorator handles complex kwargs"""
        cache = PatternMatchCache()

        class TestClass:
            @cached_pattern_query(cache)
            def query_patterns(self, context: dict, filters: list = None, options: dict = None):
                return {
                    "context": context,
                    "filters": filters,
                    "options": options,
                }

        obj = TestClass()
        context = {"query": "test"}

        result1 = obj.query_patterns(context, filters=["a", "b"], options={"limit": 10})

        # Same call should hit cache
        result2 = obj.query_patterns(context, filters=["a", "b"], options={"limit": 10})

        assert result1 == result2


class TestPatternCacheIntegration:
    """Integration tests for PatternMatchCache with CacheMonitor"""

    @pytest.fixture(autouse=True)
    def reset_monitor(self):
        """Reset singleton CacheMonitor before each test"""
        CacheMonitor.reset_instance()
        yield
        CacheMonitor.reset_instance()

    def test_cache_statistics_tracking(self):
        """Test that cache operations are tracked in monitor"""
        cache = PatternMatchCache(max_size=10)
        monitor = CacheMonitor.get_instance()

        # Perform operations
        cache.set({"id": 1}, "value1")
        cache.set({"id": 2}, "value2")
        cache.get({"id": 1})  # Hit
        cache.get({"id": 3})  # Miss

        stats = monitor.get_stats("pattern_match")

        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.size == 2
        assert stats.evictions == 0

    def test_cache_eviction_tracking(self):
        """Test that evictions are tracked in monitor"""
        cache = PatternMatchCache(max_size=2)
        monitor = CacheMonitor.get_instance()

        cache.set({"id": 1}, "value1")
        cache.set({"id": 2}, "value2")
        cache.set({"id": 3}, "value3")  # Triggers eviction

        stats = monitor.get_stats("pattern_match")
        assert stats.evictions == 1
        assert stats.size == 2

    def test_cache_hit_rate_calculation(self):
        """Test hit rate calculation through monitor"""
        cache = PatternMatchCache()
        monitor = CacheMonitor.get_instance()

        # Add entries
        for i in range(10):
            cache.set({"id": i}, f"value{i}")

        # 7 hits, 3 misses
        for i in range(7):
            cache.get({"id": i})  # Hits

        for i in range(10, 13):
            cache.get({"id": i})  # Misses

        stats = monitor.get_stats("pattern_match")
        assert abs(stats.hit_rate - 0.7) < 0.0001  # 7/10
        assert abs(stats.miss_rate - 0.3) < 0.0001  # 3/10

    def test_multiple_cache_instances_share_monitor(self):
        """Test that multiple cache instances register with same monitor"""
        PatternMatchCache(max_size=100)
        PatternMatchCache(max_size=200)

        monitor = CacheMonitor.get_instance()

        # Only one registration (first one wins)
        stats = monitor.get_stats("pattern_match")
        assert stats is not None
        assert stats.max_size == 100  # First registration

    def test_cache_monitor_report_includes_pattern_cache(self):
        """Test that monitor report includes pattern cache stats"""
        cache = PatternMatchCache()
        monitor = CacheMonitor.get_instance()

        cache.set({"id": 1}, "value1")
        cache.get({"id": 1})

        report = monitor.get_report()

        assert "pattern_match" in report
        assert "Hit Rate" in report
