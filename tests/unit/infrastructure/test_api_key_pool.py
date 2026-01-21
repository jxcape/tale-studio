"""
Tests for API Key Pool, rotation strategies, and retry logic.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from infrastructure.api_key_pool import (
    APIKeyPool,
    APIKeyInfo,
    KeyUsageTracker,
    FailureTracker,
    RotationStrategy,
)


class TestAPIKeyInfo:
    """Tests for APIKeyInfo parsing."""

    def test_parse_with_alias(self):
        """Should parse key:alias format."""
        info = APIKeyInfo.parse("abc123:prod-main")
        assert info.key == "abc123"
        assert info.alias == "prod-main"
        assert info.project_id is None

    def test_parse_without_alias(self):
        """Should generate default alias."""
        info = APIKeyInfo.parse("abc123", default_index=2)
        assert info.key == "abc123"
        assert info.alias == "key-2"
        assert info.project_id is None

    def test_parse_strips_whitespace(self):
        """Should strip whitespace from key and alias."""
        info = APIKeyInfo.parse("  abc123  :  prod-main  ")
        assert info.key == "abc123"
        assert info.alias == "prod-main"

    def test_parse_with_project_id(self):
        """Should parse key:alias:project_id format."""
        info = APIKeyInfo.parse("abc123:prod:my-gcp-project")
        assert info.key == "abc123"
        assert info.alias == "prod"
        assert info.project_id == "my-gcp-project"

    def test_parse_with_default_project_id(self):
        """Should use default project_id when not specified."""
        info = APIKeyInfo.parse("abc123:prod", default_project_id="default-project")
        assert info.key == "abc123"
        assert info.alias == "prod"
        assert info.project_id == "default-project"

    def test_parse_explicit_project_overrides_default(self):
        """Explicit project_id should override default."""
        info = APIKeyInfo.parse("abc123:prod:explicit-project", default_project_id="default-project")
        assert info.project_id == "explicit-project"

    def test_parse_key_only_with_default_project(self):
        """Key-only format should use default project."""
        info = APIKeyInfo.parse("abc123", default_index=0, default_project_id="default-project")
        assert info.key == "abc123"
        assert info.alias == "key-0"
        assert info.project_id == "default-project"


class TestKeyUsageTracker:
    """Tests for key usage tracking."""

    def test_increment_usage(self):
        """Should track usage count."""
        tracker = KeyUsageTracker(daily_limit=10)
        tracker.increment("key1")
        tracker.increment("key1")
        tracker.increment("key2")

        assert tracker.get_usage("key1") == 2
        assert tracker.get_usage("key2") == 1

    def test_is_available_under_limit(self):
        """Key should be available under daily limit."""
        tracker = KeyUsageTracker(daily_limit=10)
        for _ in range(5):
            tracker.increment("key1")

        assert tracker.is_available("key1") is True

    def test_is_available_at_limit(self):
        """Key should not be available at daily limit."""
        tracker = KeyUsageTracker(daily_limit=10)
        for _ in range(10):
            tracker.increment("key1")

        assert tracker.is_available("key1") is False

    def test_reset_daily(self):
        """Should reset counts on new day."""
        tracker = KeyUsageTracker(daily_limit=10)
        tracker.increment("key1")
        tracker.increment("key1")

        # Simulate new day
        tracker._last_reset = datetime.now() - timedelta(days=1)
        tracker._check_daily_reset()

        assert tracker.get_usage("key1") == 0

    def test_get_available_keys(self):
        """Should return only available keys."""
        tracker = KeyUsageTracker(daily_limit=2)
        keys = ["key1", "key2", "key3"]

        tracker.increment("key1")
        tracker.increment("key1")  # key1 at limit

        available = tracker.get_available_keys(keys)
        assert "key1" not in available
        assert "key2" in available
        assert "key3" in available


class TestFailureTracker:
    """Tests for failure tracking."""

    def test_mark_failed(self):
        """Should track failure count."""
        tracker = FailureTracker(max_failures=3)
        tracker.mark_failed("key1")
        tracker.mark_failed("key1")

        assert tracker.get_failure_count("key1") == 2
        assert tracker.is_healthy("key1") is True

    def test_is_healthy_at_max_failures(self):
        """Key should be unhealthy at max failures."""
        tracker = FailureTracker(max_failures=3)
        tracker.mark_failed("key1")
        tracker.mark_failed("key1")
        tracker.mark_failed("key1")

        assert tracker.is_healthy("key1") is False

    def test_mark_success_resets_count(self):
        """Success should reset failure count."""
        tracker = FailureTracker(max_failures=3)
        tracker.mark_failed("key1")
        tracker.mark_failed("key1")
        tracker.mark_success("key1")

        assert tracker.get_failure_count("key1") == 0
        assert tracker.is_healthy("key1") is True

    def test_reset_all(self):
        """Should reset all failure counts."""
        tracker = FailureTracker(max_failures=3)
        tracker.mark_failed("key1")
        tracker.mark_failed("key2")
        tracker.reset_all()

        assert tracker.get_failure_count("key1") == 0
        assert tracker.get_failure_count("key2") == 0


class TestAPIKeyPool:
    """Tests for API Key Pool."""

    def test_accepts_key_alias_format(self):
        """Should accept key:alias format."""
        keys = ["key1:prod", "key2:test", "key3:backup"]
        pool = APIKeyPool(keys=keys, strategy=RotationStrategy.ROUND_ROBIN)

        assert pool.get_alias("key1") == "prod"
        assert pool.get_alias("key2") == "test"
        assert pool.get_alias("key3") == "backup"

    def test_accepts_api_key_info_objects(self):
        """Should accept APIKeyInfo objects directly."""
        keys = [
            APIKeyInfo(key="key1", alias="prod"),
            APIKeyInfo(key="key2", alias="test"),
        ]
        pool = APIKeyPool(keys=keys, strategy=RotationStrategy.ROUND_ROBIN)

        assert pool.get_alias("key1") == "prod"
        assert pool.get_alias("key2") == "test"

    def test_round_robin_rotation(self):
        """Should rotate keys in round-robin order."""
        keys = ["key1:a", "key2:b", "key3:c"]
        pool = APIKeyPool(
            keys=keys,
            strategy=RotationStrategy.ROUND_ROBIN,
            daily_limit=10,
        )

        # Should cycle through keys
        assert pool.get_key() == "key1"
        assert pool.get_key() == "key2"
        assert pool.get_key() == "key3"
        assert pool.get_key() == "key1"  # Back to start

    def test_least_used_rotation(self):
        """Should prefer least used keys."""
        keys = ["key1:a", "key2:b", "key3:c"]
        pool = APIKeyPool(
            keys=keys,
            strategy=RotationStrategy.LEAST_USED,
            daily_limit=10,
        )

        # Use key1 twice
        pool.get_key()  # key1 (all start at 0, picks first)
        pool.mark_used("key1")
        pool.mark_used("key1")

        # Should now prefer key2 or key3
        next_key = pool.get_key()
        assert next_key in ["key2", "key3"]

    def test_skips_exhausted_keys(self):
        """Should skip keys at daily limit."""
        keys = ["key1:a", "key2:b"]
        pool = APIKeyPool(
            keys=keys,
            strategy=RotationStrategy.ROUND_ROBIN,
            daily_limit=2,
        )

        # Exhaust key1
        pool.mark_used("key1")
        pool.mark_used("key1")

        # Should only return key2 now
        assert pool.get_key() == "key2"
        assert pool.get_key() == "key2"

    def test_skips_failed_keys(self):
        """Should skip keys with too many failures."""
        keys = ["key1:a", "key2:b"]
        pool = APIKeyPool(
            keys=keys,
            strategy=RotationStrategy.ROUND_ROBIN,
            daily_limit=10,
            max_failures_per_key=2,
        )

        # Mark key1 as failed twice
        pool.mark_failed("key1", Exception("error"))
        pool.mark_failed("key1", Exception("error"))

        # Should only return key2 now
        assert pool.get_key() == "key2"
        assert pool.get_key() == "key2"

    def test_raises_when_all_exhausted(self):
        """Should raise when all keys exhausted."""
        keys = ["key1:a", "key2:b"]
        pool = APIKeyPool(
            keys=keys,
            strategy=RotationStrategy.ROUND_ROBIN,
            daily_limit=1,
        )

        pool.mark_used("key1")
        pool.mark_used("key2")

        with pytest.raises(RuntimeError) as exc_info:
            pool.get_key()

        assert "Exhausted" in str(exc_info.value)

    def test_raises_when_all_failed(self):
        """Should raise when all keys failed."""
        keys = ["key1:a", "key2:b"]
        pool = APIKeyPool(
            keys=keys,
            strategy=RotationStrategy.ROUND_ROBIN,
            daily_limit=10,
            max_failures_per_key=1,
        )

        pool.mark_failed("key1", Exception("error"))
        pool.mark_failed("key2", Exception("error"))

        with pytest.raises(RuntimeError) as exc_info:
            pool.get_key()

        assert "Failed" in str(exc_info.value)

    def test_get_status_includes_alias(self):
        """Should return status with aliases as keys."""
        keys = ["key1:prod", "key2:test"]
        pool = APIKeyPool(
            keys=keys,
            strategy=RotationStrategy.ROUND_ROBIN,
            daily_limit=10,
        )

        pool.mark_used("key1")
        pool.mark_used("key1")
        pool.mark_failed("key2", Exception("error"))

        status = pool.get_status()

        # Status should use aliases as keys
        assert "prod" in status
        assert "test" in status

        assert status["prod"]["used"] == 2
        assert status["prod"]["remaining"] == 8
        assert status["prod"]["failure_count"] == 0
        assert status["prod"]["healthy"] is True

        assert status["test"]["used"] == 0
        assert status["test"]["failure_count"] == 1
        assert status["test"]["healthy"] is True

    def test_concurrent_limit(self):
        """Should respect concurrent usage limit."""
        keys = ["key1:a", "key2:b"]
        pool = APIKeyPool(
            keys=keys,
            strategy=RotationStrategy.ROUND_ROBIN,
            daily_limit=10,
            max_concurrent_per_key=2,
        )

        # Acquire 2 concurrent uses of key1
        pool.acquire("key1")
        pool.acquire("key1")

        # key1 should be unavailable for new concurrent use
        assert pool.can_acquire("key1") is False
        assert pool.can_acquire("key2") is True

        # Release one
        pool.release("key1")
        assert pool.can_acquire("key1") is True

    def test_context_manager(self):
        """Should support context manager for automatic release."""
        keys = ["key1:prod"]
        pool = APIKeyPool(
            keys=keys,
            strategy=RotationStrategy.ROUND_ROBIN,
            daily_limit=10,
            max_concurrent_per_key=1,
        )

        with pool.use_key() as key:
            assert key == "key1"
            assert pool.can_acquire("key1") is False

        # After context, should be released
        assert pool.can_acquire("key1") is True

    def test_reset_failures(self):
        """Should reset all failure counts."""
        keys = ["key1:a", "key2:b"]
        pool = APIKeyPool(
            keys=keys,
            strategy=RotationStrategy.ROUND_ROBIN,
            daily_limit=10,
            max_failures_per_key=2,
        )

        pool.mark_failed("key1", Exception("error"))
        pool.mark_failed("key1", Exception("error"))
        pool.mark_failed("key2", Exception("error"))

        pool.reset_failures()

        status = pool.get_status()
        assert status["a"]["failure_count"] == 0
        assert status["a"]["healthy"] is True
        assert status["b"]["failure_count"] == 0


class TestAPIKeyPoolRetry:
    """Tests for execute_with_retry functionality."""

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self):
        """Should execute successfully on first try."""
        keys = ["key1:prod", "key2:test"]
        pool = APIKeyPool(keys=keys, strategy=RotationStrategy.ROUND_ROBIN)

        async def mock_operation(key: str):
            return f"result-{key}"

        result = await pool.execute_with_retry(mock_operation)

        assert result == "result-key1"

    @pytest.mark.asyncio
    async def test_execute_with_retry_failover(self):
        """Should failover to next key on error."""
        keys = ["key1:prod", "key2:test"]
        pool = APIKeyPool(
            keys=keys,
            strategy=RotationStrategy.ROUND_ROBIN,
            max_failures_per_key=1,
        )

        call_count = 0

        async def mock_operation(key: str):
            nonlocal call_count
            call_count += 1
            if key == "key1":
                raise Exception("key1 failed")
            return f"result-{key}"

        result = await pool.execute_with_retry(mock_operation, max_retries=3)

        assert result == "result-key2"
        assert call_count == 2  # First failed, second succeeded

    @pytest.mark.asyncio
    async def test_execute_with_retry_calls_on_success(self):
        """Should call on_success callback."""
        keys = ["key1:prod"]
        pool = APIKeyPool(keys=keys, strategy=RotationStrategy.ROUND_ROBIN)

        async def mock_operation(key: str):
            return "result"

        await pool.execute_with_retry(
            mock_operation,
            on_success=pool.mark_used,
        )

        status = pool.get_status()
        assert status["prod"]["used"] == 1

    @pytest.mark.asyncio
    async def test_execute_with_retry_exhausts_all(self):
        """Should raise after all retries exhausted."""
        keys = ["key1:prod", "key2:test"]
        pool = APIKeyPool(
            keys=keys,
            strategy=RotationStrategy.ROUND_ROBIN,
            max_failures_per_key=2,
        )

        async def mock_operation(key: str):
            raise Exception(f"{key} failed")

        with pytest.raises(RuntimeError) as exc_info:
            await pool.execute_with_retry(mock_operation, max_retries=3)

        assert "All retry attempts failed" in str(exc_info.value)


class TestRotationStrategy:
    """Tests for rotation strategy enum."""

    def test_from_string(self):
        """Should parse strategy from string."""
        assert RotationStrategy.from_string("round_robin") == RotationStrategy.ROUND_ROBIN
        assert RotationStrategy.from_string("least_used") == RotationStrategy.LEAST_USED
        assert RotationStrategy.from_string("random") == RotationStrategy.RANDOM

    def test_from_string_case_insensitive(self):
        """Should be case insensitive."""
        assert RotationStrategy.from_string("ROUND_ROBIN") == RotationStrategy.ROUND_ROBIN
        assert RotationStrategy.from_string("Least_Used") == RotationStrategy.LEAST_USED
