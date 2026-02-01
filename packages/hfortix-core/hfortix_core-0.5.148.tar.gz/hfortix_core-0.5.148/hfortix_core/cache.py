"""
TTL-based caching for readonly reference data.

Provides in-memory caching with Time-To-Live (TTL) for read-only
endpoints that rarely change (e.g., geography, timezone).
"""

from __future__ import annotations

import time
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class CacheEntry(Generic[T]):
    """A cache entry with expiration time."""

    def __init__(self, value: T, ttl_seconds: float):
        """
        Initialize cache entry.

        Args:
            value: The cached value
            ttl_seconds: Time to live in seconds
        """
        self.value = value
        self.expiry = time.time() + ttl_seconds

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() > self.expiry


class TTLCache(Generic[T]):
    """
    Simple TTL-based cache for readonly reference data.

    Thread-safe in-memory cache with time-based expiration.
    Designed for caching readonly reference tables that rarely change.

    Example:
        >>> cache = TTLCache[dict](default_ttl=3600)  # 1 hour
        >>> cache.set("geography/countries", country_data)
        >>> data = cache.get("geography/countries")
    """

    def __init__(self, default_ttl: float = 3600):
        """
        Initialize TTL cache.

        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self.default_ttl = default_ttl
        self._cache: dict[str, CacheEntry[T]] = {}

    def get(self, key: str) -> T | None:
        """
        Get cached value if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/not found
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if entry.is_expired():
            del self._cache[key]
            return None

        return entry.value

    def set(self, key: str, value: T, ttl: float | None = None) -> None:
        """
        Store value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        ttl_seconds = ttl if ttl is not None else self.default_ttl
        self._cache[key] = CacheEntry(value, ttl_seconds)

    def invalidate(self, key: str) -> None:
        """
        Remove entry from cache.

        Args:
            key: Cache key to remove
        """
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def cleanup(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items() if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)

    def __len__(self) -> int:
        """Return number of cached entries (including expired)."""
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None


# Global cache instance for readonly reference data
# TTL: 24 hours (reference data rarely changes)
readonly_cache: TTLCache[dict[str, Any]] = TTLCache(default_ttl=86400)
