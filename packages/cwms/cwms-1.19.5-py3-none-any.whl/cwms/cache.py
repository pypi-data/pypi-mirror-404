"""Generic TTL (Time-To-Live) cache with LRU eviction."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class CacheEntry[T]:
    """Cache entry with value and timestamp."""

    value: T
    timestamp: float

    def is_valid(self, ttl_seconds: float) -> bool:
        """Check if entry is still valid based on TTL.

        Args:
            ttl_seconds: Time-to-live in seconds

        Returns:
            True if entry is still valid, False if expired
        """
        return (time.time() - self.timestamp) < ttl_seconds


class TTLCache[T]:
    """Generic time-to-live cache with LRU eviction.

    Stores values with automatic expiration based on TTL. When the cache
    exceeds max_size, oldest entries (by timestamp) are evicted first.

    Type Parameters:
        T: Type of values stored in the cache

    Example:
        >>> cache = TTLCache[str](ttl_seconds=300.0, max_size=100)
        >>> cache.set("key", "value")
        >>> value = cache.get("key")  # Returns "value" if not expired
        >>> cache.invalidate("key")   # Remove specific key
        >>> cache.invalidate_all()    # Clear entire cache
    """

    def __init__(self, ttl_seconds: float = 300.0, max_size: int = 100) -> None:
        """Initialize TTL cache.

        Args:
            ttl_seconds: Time-to-live for cache entries in seconds (default: 300.0)
            max_size: Maximum number of entries before eviction (default: 100)
        """
        self._ttl_seconds = ttl_seconds
        self._max_size = max_size
        self._cache: dict[str, CacheEntry[T]] = {}

    def get(self, key: str) -> T | None:
        """Get cached value if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value if valid, None if expired or not found
        """
        entry = self._cache.get(key)
        if entry is None:
            return None

        if not entry.is_valid(self._ttl_seconds):
            # Entry expired, remove it
            del self._cache[key]
            return None

        return entry.value

    def set(self, key: str, value: T) -> None:
        """Set cache value with current timestamp.

        If the cache exceeds max_size, oldest entries are evicted first.

        Args:
            key: Cache key
            value: Value to cache
        """
        # Add new entry
        self._cache[key] = CacheEntry(value=value, timestamp=time.time())

        # Evict oldest entries if over limit
        while len(self._cache) > self._max_size:
            self._evict_oldest()

    def invalidate(self, key: str) -> None:
        """Remove specific key from cache.

        Args:
            key: Cache key to remove
        """
        self._cache.pop(key, None)

    def invalidate_all(self) -> None:
        """Clear entire cache."""
        self._cache.clear()

    def invalidate_by_prefix(self, prefix: str) -> None:
        """Remove all keys starting with prefix.

        Args:
            prefix: Key prefix to match
        """
        keys_to_remove = [key for key in self._cache if key.startswith(prefix)]
        for key in keys_to_remove:
            del self._cache[key]

    def _evict_oldest(self) -> None:
        """Evict the oldest entry by timestamp (LRU eviction)."""
        if not self._cache:
            return

        # Find oldest entry
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)
        del self._cache[oldest_key]
