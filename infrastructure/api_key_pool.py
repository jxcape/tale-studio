"""
API Key Pool with rotation strategies and retry logic.

Handles multiple API keys for services with rate limits (e.g., Veo 10/day).
"""
import random
import threading
import logging
from contextlib import contextmanager, asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Callable, TypeVar, Awaitable

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RotationStrategy(Enum):
    """Key rotation strategies."""

    ROUND_ROBIN = "round_robin"
    LEAST_USED = "least_used"
    RANDOM = "random"

    @classmethod
    def from_string(cls, value: str) -> "RotationStrategy":
        """Parse strategy from string."""
        return cls(value.lower())


@dataclass
class APIKeyInfo:
    """
    API Key with alias and project ID for debugging.

    Attributes:
        key: The actual API key value.
        alias: Human-readable name for logging/debugging.
        project_id: Google Cloud project ID (optional, for Vertex AI).
    """
    key: str
    alias: str
    project_id: Optional[str] = None

    @classmethod
    def parse(cls, key_string: str, default_index: int = 0, default_project_id: Optional[str] = None) -> "APIKeyInfo":
        """
        Parse key string in format 'key:alias:project_id', 'key:alias', or just 'key'.

        Examples:
            'abc123:prod:my-project' -> APIKeyInfo(key='abc123', alias='prod', project_id='my-project')
            'abc123:prod-main' -> APIKeyInfo(key='abc123', alias='prod-main', project_id=None)
            'abc123' -> APIKeyInfo(key='abc123', alias='key-0', project_id=None)
        """
        parts = key_string.split(":")

        if len(parts) >= 3:
            # key:alias:project_id format
            key = parts[0].strip()
            alias = parts[1].strip()
            project_id = ":".join(parts[2:]).strip()  # Handle project IDs with colons
            return cls(key=key, alias=alias, project_id=project_id or default_project_id)
        elif len(parts) == 2:
            # key:alias format
            key = parts[0].strip()
            alias = parts[1].strip()
            return cls(key=key, alias=alias, project_id=default_project_id)
        else:
            # Just key
            return cls(key=key_string.strip(), alias=f"key-{default_index}", project_id=default_project_id)

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        if isinstance(other, APIKeyInfo):
            return self.key == other.key
        return False


@dataclass
class KeyUsageTracker:
    """
    Tracks API key usage with daily limits.

    Automatically resets counts at midnight.
    """

    daily_limit: int
    _usage: dict = field(default_factory=dict)
    _last_reset: datetime = field(default_factory=datetime.now)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def increment(self, key: str) -> None:
        """Increment usage count for key."""
        with self._lock:
            self._check_daily_reset()
            self._usage[key] = self._usage.get(key, 0) + 1

    def get_usage(self, key: str) -> int:
        """Get current usage count for key."""
        with self._lock:
            self._check_daily_reset()
            return self._usage.get(key, 0)

    def is_available(self, key: str) -> bool:
        """Check if key is under daily limit."""
        return self.get_usage(key) < self.daily_limit

    def get_available_keys(self, keys: list[str]) -> list[str]:
        """Get list of keys under daily limit."""
        return [k for k in keys if self.is_available(k)]

    def get_remaining(self, key: str) -> int:
        """Get remaining uses for key."""
        return max(0, self.daily_limit - self.get_usage(key))

    def _check_daily_reset(self) -> None:
        """Reset counts if new day."""
        now = datetime.now()
        if now.date() > self._last_reset.date():
            self._usage.clear()
            self._last_reset = now


@dataclass
class ConcurrencyTracker:
    """Tracks concurrent usage of keys."""

    max_per_key: int
    _active: dict = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def acquire(self, key: str) -> bool:
        """Try to acquire a slot for key. Returns True if successful."""
        with self._lock:
            current = self._active.get(key, 0)
            if current >= self.max_per_key:
                return False
            self._active[key] = current + 1
            return True

    def release(self, key: str) -> None:
        """Release a slot for key."""
        with self._lock:
            current = self._active.get(key, 0)
            if current > 0:
                self._active[key] = current - 1

    def can_acquire(self, key: str) -> bool:
        """Check if slot available for key."""
        with self._lock:
            return self._active.get(key, 0) < self.max_per_key

    def get_active(self, key: str) -> int:
        """Get current active count for key."""
        with self._lock:
            return self._active.get(key, 0)


@dataclass
class FailureTracker:
    """Tracks temporary failures for keys."""

    max_failures: int = 3
    _failures: dict = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def mark_failed(self, key: str) -> None:
        """Mark a key as having failed."""
        with self._lock:
            self._failures[key] = self._failures.get(key, 0) + 1

    def mark_success(self, key: str) -> None:
        """Reset failure count on success."""
        with self._lock:
            self._failures[key] = 0

    def is_healthy(self, key: str) -> bool:
        """Check if key is below failure threshold."""
        with self._lock:
            return self._failures.get(key, 0) < self.max_failures

    def get_failure_count(self, key: str) -> int:
        """Get current failure count for key."""
        with self._lock:
            return self._failures.get(key, 0)

    def reset_all(self) -> None:
        """Reset all failure counts."""
        with self._lock:
            self._failures.clear()


class APIKeyPool:
    """
    Pool of API keys with rotation, rate limiting, and retry logic.

    Features:
    - Multiple rotation strategies (round-robin, least-used, random)
    - Daily usage tracking with automatic reset
    - Concurrent usage limits
    - Context manager for automatic release
    - Retry with automatic failover on errors
    - Alias support for debugging
    """

    def __init__(
        self,
        keys: list[str | APIKeyInfo],
        strategy: RotationStrategy = RotationStrategy.ROUND_ROBIN,
        daily_limit: int = 10,
        max_concurrent_per_key: int = 2,
        max_failures_per_key: int = 3,
    ):
        if not keys:
            raise ValueError("At least one API key is required")

        # Parse keys with aliases
        self._key_infos: list[APIKeyInfo] = []
        for i, k in enumerate(keys):
            if isinstance(k, APIKeyInfo):
                self._key_infos.append(k)
            else:
                self._key_infos.append(APIKeyInfo.parse(k, i))

        # Map for quick lookup: key_value -> APIKeyInfo
        self._key_map: dict[str, APIKeyInfo] = {
            info.key: info for info in self._key_infos
        }

        self._keys = [info.key for info in self._key_infos]
        self._strategy = strategy
        self._daily_limit = daily_limit
        self._usage_tracker = KeyUsageTracker(daily_limit=daily_limit)
        self._concurrency_tracker = ConcurrencyTracker(max_per_key=max_concurrent_per_key)
        self._failure_tracker = FailureTracker(max_failures=max_failures_per_key)
        self._round_robin_index = 0
        self._lock = threading.Lock()

    def get_alias(self, key: str) -> str:
        """Get alias for a key."""
        info = self._key_map.get(key)
        return info.alias if info else "unknown"

    def get_key(self) -> str:
        """
        Get next available key using configured strategy.

        Raises:
            RuntimeError: If all keys are exhausted or unhealthy.
        """
        available = [
            k for k in self._usage_tracker.get_available_keys(self._keys)
            if self._failure_tracker.is_healthy(k)
        ]

        if not available:
            # Check if it's exhaustion or failures
            exhausted = [k for k in self._keys if not self._usage_tracker.is_available(k)]
            failed = [k for k in self._keys if not self._failure_tracker.is_healthy(k)]

            raise RuntimeError(
                f"No API keys available. "
                f"Exhausted: {len(exhausted)}, Failed: {len(failed)}, "
                f"Total keys: {len(self._keys)}, Daily limit: {self._daily_limit}"
            )

        if self._strategy == RotationStrategy.ROUND_ROBIN:
            return self._get_round_robin(available)
        elif self._strategy == RotationStrategy.LEAST_USED:
            return self._get_least_used(available)
        else:  # RANDOM
            return random.choice(available)

    def mark_used(self, key: str) -> None:
        """Mark key as used (increment daily count)."""
        self._usage_tracker.increment(key)
        alias = self.get_alias(key)
        remaining = self._usage_tracker.get_remaining(key)
        logger.debug(f"[{alias}] Used. Remaining today: {remaining}/{self._daily_limit}")

    def mark_failed(self, key: str, error: Optional[Exception] = None) -> None:
        """Mark key as having failed."""
        self._failure_tracker.mark_failed(key)
        alias = self.get_alias(key)
        count = self._failure_tracker.get_failure_count(key)
        max_f = self._failure_tracker.max_failures
        logger.warning(
            f"[{alias}] Failed ({count}/{max_f}). Error: {error}"
        )

    def mark_success(self, key: str) -> None:
        """Mark key as successful (reset failure count)."""
        self._failure_tracker.mark_success(key)

    def acquire(self, key: str) -> bool:
        """Acquire concurrent slot for key."""
        return self._concurrency_tracker.acquire(key)

    def release(self, key: str) -> None:
        """Release concurrent slot for key."""
        self._concurrency_tracker.release(key)

    def can_acquire(self, key: str) -> bool:
        """Check if can acquire concurrent slot."""
        return self._concurrency_tracker.can_acquire(key)

    @contextmanager
    def use_key(self):
        """
        Context manager for using a key with automatic release.

        Usage:
            with pool.use_key() as key:
                # Use key for API call
                pass
            # Key automatically released
        """
        key = self.get_key()

        # Try to acquire, if concurrent limit reached, find another key
        attempts = 0
        while not self.acquire(key) and attempts < len(self._keys):
            attempts += 1
            available = [
                k for k in self._usage_tracker.get_available_keys(self._keys)
                if self.can_acquire(k) and self._failure_tracker.is_healthy(k)
            ]
            if not available:
                raise RuntimeError("No keys available for concurrent use")
            key = available[0]

        alias = self.get_alias(key)
        logger.debug(f"[{alias}] Acquired for use")

        try:
            yield key
        finally:
            self.release(key)
            logger.debug(f"[{alias}] Released")

    async def execute_with_retry(
        self,
        operation: Callable[[str], Awaitable[T]],
        max_retries: int = 3,
        on_success: Optional[Callable[[str], None]] = None,
    ) -> T:
        """
        Execute an async operation with automatic retry and failover.

        Args:
            operation: Async function that takes API key and returns result.
            max_retries: Maximum number of retry attempts.
            on_success: Optional callback on successful execution (e.g., mark_used).

        Returns:
            Result from successful operation.

        Raises:
            RuntimeError: If all retries exhausted.

        Usage:
            result = await pool.execute_with_retry(
                lambda key: veo.generate(key, request),
                on_success=pool.mark_used,
            )
        """
        last_error: Optional[Exception] = None
        tried_keys: set[str] = set()

        for attempt in range(max_retries):
            try:
                key = self.get_key()

                # Avoid retrying with same failed key if possible
                if key in tried_keys:
                    available = [
                        k for k in self._usage_tracker.get_available_keys(self._keys)
                        if k not in tried_keys and self._failure_tracker.is_healthy(k)
                    ]
                    if available:
                        key = available[0]

                tried_keys.add(key)
                alias = self.get_alias(key)

                logger.info(f"[{alias}] Attempt {attempt + 1}/{max_retries}")

                # Execute operation
                result = await operation(key)

                # Success
                self.mark_success(key)
                if on_success:
                    on_success(key)

                logger.info(f"[{alias}] Success")
                return result

            except Exception as e:
                last_error = e
                self.mark_failed(key, e)

                # Check if any keys still available
                available = [
                    k for k in self._usage_tracker.get_available_keys(self._keys)
                    if self._failure_tracker.is_healthy(k)
                ]

                if not available:
                    break

                logger.info(f"Retrying with different key... ({len(available)} keys remaining)")

        raise RuntimeError(
            f"All retry attempts failed after {max_retries} tries. "
            f"Last error: {last_error}"
        )

    def get_status(self) -> dict[str, dict]:
        """Get status of all keys with aliases."""
        return {
            info.alias: {
                "key_preview": f"{info.key[:8]}...",
                "used": self._usage_tracker.get_usage(info.key),
                "remaining": self._usage_tracker.get_remaining(info.key),
                "available": self._usage_tracker.is_available(info.key),
                "active_concurrent": self._concurrency_tracker.get_active(info.key),
                "failure_count": self._failure_tracker.get_failure_count(info.key),
                "healthy": self._failure_tracker.is_healthy(info.key),
            }
            for info in self._key_infos
        }

    def get_total_remaining(self) -> int:
        """Get total remaining uses across all healthy keys."""
        return sum(
            self._usage_tracker.get_remaining(key)
            for key in self._keys
            if self._failure_tracker.is_healthy(key)
        )

    def reset_failures(self) -> None:
        """Reset all failure counts (e.g., after fixing an issue)."""
        self._failure_tracker.reset_all()
        logger.info("All failure counts reset")

    def _get_round_robin(self, available: list[str]) -> str:
        """Get next key in round-robin order."""
        with self._lock:
            # Find next available key starting from current index
            for _ in range(len(self._keys)):
                key = self._keys[self._round_robin_index % len(self._keys)]
                self._round_robin_index += 1
                if key in available:
                    return key
            # Fallback (shouldn't reach here if available is non-empty)
            return available[0]

    def _get_least_used(self, available: list[str]) -> str:
        """Get key with least usage."""
        return min(
            available,
            key=lambda k: self._usage_tracker.get_usage(k),
        )
