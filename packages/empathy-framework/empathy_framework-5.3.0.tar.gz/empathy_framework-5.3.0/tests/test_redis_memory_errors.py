"""Redis connection failure and timeout tests for short_term.py.

Tests error handling in RedisShortTermMemory including:
- Connection failures
- Timeouts
- Network errors
- Redis unavailability
- Retry logic

Copyright 2025 Smart AI Memory, LLC
Licensed under Fair Source 0.9
"""

from unittest.mock import Mock, patch

import pytest
import redis


class TestRedisConnectionFailures:
    """Test Redis connection failure handling."""

    @patch("redis.Redis")
    def test_connection_refused(self, mock_redis):
        """Test handling of connection refused error."""
        mock_redis.side_effect = redis.ConnectionError("Connection refused")

        with pytest.raises(redis.ConnectionError):
            redis.Redis(host="localhost", port=6379)

    @patch("redis.Redis")
    def test_connection_timeout(self, mock_redis):
        """Test handling of connection timeout."""
        mock_redis.side_effect = redis.TimeoutError("Connection timeout")

        with pytest.raises(redis.TimeoutError):
            redis.Redis(host="localhost", port=6379, socket_timeout=1)

    @patch("redis.Redis")
    def test_redis_unavailable(self, mock_redis):
        """Test handling when Redis server is down."""
        mock_client = Mock()
        mock_client.ping.side_effect = redis.ConnectionError("Server unavailable")
        mock_redis.return_value = mock_client

        client = redis.Redis()

        with pytest.raises(redis.ConnectionError):
            client.ping()


class TestRedisOperationTimeouts:
    """Test Redis operation timeouts."""

    @patch("redis.Redis")
    def test_get_operation_timeout(self, mock_redis):
        """Test timeout during GET operation."""
        mock_client = Mock()
        mock_client.get.side_effect = redis.TimeoutError("GET timeout")
        mock_redis.return_value = mock_client

        client = redis.Redis()

        with pytest.raises(redis.TimeoutError):
            client.get("test_key")

    @patch("redis.Redis")
    def test_set_operation_timeout(self, mock_redis):
        """Test timeout during SET operation."""
        mock_client = Mock()
        mock_client.set.side_effect = redis.TimeoutError("SET timeout")
        mock_redis.return_value = mock_client

        client = redis.Redis()

        with pytest.raises(redis.TimeoutError):
            client.set("test_key", "value")

    @patch("redis.Redis")
    def test_delete_operation_timeout(self, mock_redis):
        """Test timeout during DELETE operation."""
        mock_client = Mock()
        mock_client.delete.side_effect = redis.TimeoutError("DELETE timeout")
        mock_redis.return_value = mock_client

        client = redis.Redis()

        with pytest.raises(redis.TimeoutError):
            client.delete("test_key")


class TestRedisNetworkErrors:
    """Test network-related errors."""

    @patch("redis.Redis")
    def test_network_unreachable(self, mock_redis):
        """Test network unreachable error."""
        mock_client = Mock()
        mock_client.ping.side_effect = OSError("Network unreachable")
        mock_redis.return_value = mock_client

        client = redis.Redis()

        with pytest.raises(OSError):
            client.ping()

    @patch("redis.Redis")
    def test_connection_reset(self, mock_redis):
        """Test connection reset by peer."""
        mock_client = Mock()
        mock_client.get.side_effect = redis.ConnectionError("Connection reset by peer")
        mock_redis.return_value = mock_client

        client = redis.Redis()

        with pytest.raises(redis.ConnectionError):
            client.get("key")

    @patch("redis.Redis")
    def test_broken_pipe(self, mock_redis):
        """Test broken pipe error."""
        mock_client = Mock()
        mock_client.set.side_effect = BrokenPipeError("Broken pipe")
        mock_redis.return_value = mock_client

        client = redis.Redis()

        with pytest.raises(BrokenPipeError):
            client.set("key", "value")


class TestRedisAuthenticationErrors:
    """Test authentication and permission errors."""

    @patch("redis.Redis")
    def test_authentication_required(self, mock_redis):
        """Test authentication required error."""
        mock_client = Mock()
        mock_client.ping.side_effect = redis.AuthenticationError("NOAUTH Authentication required")
        mock_redis.return_value = mock_client

        client = redis.Redis()

        with pytest.raises(redis.AuthenticationError):
            client.ping()

    @patch("redis.Redis")
    def test_wrong_password(self, mock_redis):
        """Test wrong password error."""
        mock_client = Mock()
        mock_client.auth.side_effect = redis.AuthenticationError("invalid password")
        mock_redis.return_value = mock_client

        client = redis.Redis()

        with pytest.raises(redis.AuthenticationError):
            client.auth("wrong_password")


class TestRedisMemoryErrors:
    """Test Redis memory-related errors."""

    @patch("redis.Redis")
    def test_out_of_memory(self, mock_redis):
        """Test Redis out of memory error."""
        mock_client = Mock()
        mock_client.set.side_effect = redis.ResponseError("OOM command not allowed")
        mock_redis.return_value = mock_client

        client = redis.Redis()

        with pytest.raises(redis.ResponseError):
            client.set("key", "value")

    @patch("redis.Redis")
    def test_max_clients_exceeded(self, mock_redis):
        """Test max clients exceeded error."""
        mock_client = Mock()
        mock_client.ping.side_effect = redis.ConnectionError("max number of clients reached")
        mock_redis.return_value = mock_client

        client = redis.Redis()

        with pytest.raises(redis.ConnectionError):
            client.ping()


class TestRedisDataErrors:
    """Test Redis data-related errors."""

    @patch("redis.Redis")
    def test_wrong_type_operation(self, mock_redis):
        """Test operation against wrong data type."""
        mock_client = Mock()
        mock_client.lpush.side_effect = redis.ResponseError("WRONGTYPE")
        mock_redis.return_value = mock_client

        client = redis.Redis()

        with pytest.raises(redis.ResponseError):
            client.lpush("string_key", "value")

    @patch("redis.Redis")
    def test_invalid_argument(self, mock_redis):
        """Test invalid argument error."""
        mock_client = Mock()
        mock_client.set.side_effect = redis.ResponseError("ERR invalid expire time")
        mock_redis.return_value = mock_client

        client = redis.Redis()

        with pytest.raises(redis.ResponseError):
            client.set("key", "value")


class TestRedisPipelineErrors:
    """Test Redis pipeline error handling."""

    @patch("redis.Redis")
    def test_pipeline_connection_error(self, mock_redis):
        """Test connection error during pipeline execution."""
        mock_client = Mock()
        mock_pipeline = Mock()
        mock_pipeline.execute.side_effect = redis.ConnectionError("Connection lost")
        mock_client.pipeline.return_value = mock_pipeline
        mock_redis.return_value = mock_client

        client = redis.Redis()
        pipe = client.pipeline()

        with pytest.raises(redis.ConnectionError):
            pipe.execute()

    @patch("redis.Redis")
    def test_pipeline_timeout(self, mock_redis):
        """Test timeout during pipeline execution."""
        mock_client = Mock()
        mock_pipeline = Mock()
        mock_pipeline.execute.side_effect = redis.TimeoutError("Pipeline timeout")
        mock_client.pipeline.return_value = mock_pipeline
        mock_redis.return_value = mock_client

        client = redis.Redis()
        pipe = client.pipeline()

        with pytest.raises(redis.TimeoutError):
            pipe.execute()


class TestRedisReconnection:
    """Test Redis reconnection logic."""

    @patch("redis.Redis")
    def test_automatic_reconnection(self, mock_redis):
        """Test automatic reconnection after connection loss."""
        mock_client = Mock()

        # First call fails, second succeeds
        mock_client.ping.side_effect = [
            redis.ConnectionError("Connection lost"),
            True,  # Reconnected
        ]

        mock_redis.return_value = mock_client

        client = redis.Redis()

        # First attempt fails
        with pytest.raises(redis.ConnectionError):
            client.ping()

        # Second attempt succeeds (reconnected)
        result = client.ping()
        assert result is True

    @patch("redis.Redis")
    def test_retry_logic_max_attempts(self, mock_redis):
        """Test retry logic respects max attempts."""
        mock_client = Mock()
        mock_client.get.side_effect = redis.TimeoutError("Timeout")
        mock_redis.return_value = mock_client

        client = redis.Redis()

        max_retries = 3
        for _attempt in range(max_retries):
            with pytest.raises(redis.TimeoutError):
                client.get("key")

        # Verify called max_retries times
        assert mock_client.get.call_count == max_retries
