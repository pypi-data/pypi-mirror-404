"""Cache implementation that respects Cache-Control headers."""

from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from typing import Any

from refyne.interfaces import CacheControlDirectives, CacheEntry, Logger


def parse_cache_control(header: str | None) -> CacheControlDirectives:
    """Parse Cache-Control header into directives.

    Args:
        header: The Cache-Control header value

    Returns:
        Parsed directives

    Example:
        >>> parse_cache_control("private, max-age=3600, stale-while-revalidate=60")
        CacheControlDirectives(private=True, max_age=3600, stale_while_revalidate=60)
    """
    if not header:
        return CacheControlDirectives()

    directives = CacheControlDirectives()

    parts = [part.strip().lower() for part in header.split(",")]

    for part in parts:
        if part == "no-store":
            directives.no_store = True
        elif part == "no-cache":
            directives.no_cache = True
        elif part == "private":
            directives.private = True
        elif part.startswith("max-age="):
            try:
                directives.max_age = int(part[8:])
            except ValueError:
                pass
        elif part.startswith("stale-while-revalidate="):
            try:
                directives.stale_while_revalidate = int(part[23:])
            except ValueError:
                pass

    return directives


def generate_cache_key(method: str, url: str, auth_hash: str | None = None) -> str:
    """Generate a cache key from request details.

    Args:
        method: HTTP method
        url: Request URL
        auth_hash: Hash of the auth token (for user-specific caching)

    Returns:
        Cache key string
    """
    parts = [method.upper(), url]
    if auth_hash:
        parts.append(auth_hash)
    return ":".join(parts)


def hash_string(s: str) -> str:
    """Hash a string using SHA-256 (truncated to 16 chars for cache keys).

    Args:
        s: String to hash

    Returns:
        Truncated SHA-256 hash string (16 chars, 64 bits of entropy)
    """
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def create_cache_entry(
    value: Any,
    cache_control_header: str | None,
) -> CacheEntry | None:
    """Create a cache entry from a response.

    Args:
        value: The response body to cache
        cache_control_header: The Cache-Control header value

    Returns:
        Cache entry, or None if response should not be cached
    """
    cache_control = parse_cache_control(cache_control_header)

    # Don't cache if no-store
    if cache_control.no_store:
        return None

    # Calculate expiry
    if cache_control.max_age is not None:
        expires_at = time.time() + cache_control.max_age
    else:
        # No max-age specified, don't cache
        return None

    return CacheEntry(
        value=value,
        expires_at=expires_at,
        cache_control=cache_control,
    )


class MemoryCache:
    """In-memory cache implementation that respects Cache-Control headers.

    This is the default cache used by the SDK. It stores entries in memory
    and automatically evicts the oldest entries when the limit is reached.

    Example:
        >>> cache = MemoryCache(max_entries=50)
        >>> client = Refyne(api_key=key, cache=cache)
    """

    def __init__(
        self,
        max_entries: int = 100,
        logger: Logger | None = None,
    ) -> None:
        """Initialize the memory cache.

        Args:
            max_entries: Maximum number of entries to store
            logger: Optional logger for cache operations
        """
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_entries = max_entries
        self._logger = logger

    async def get(self, key: str) -> CacheEntry | None:
        """Get a cached entry by key.

        Args:
            key: The cache key

        Returns:
            The cached entry, or None if not found/expired
        """
        entry = self._store.get(key)

        if entry is None:
            return None

        now = time.time()

        # Check if entry has expired
        if entry.expires_at < now:
            # Check for stale-while-revalidate
            if entry.cache_control.stale_while_revalidate:
                stale_deadline = entry.expires_at + entry.cache_control.stale_while_revalidate
                if now < stale_deadline:
                    if self._logger:
                        self._logger.debug("Serving stale cache entry", {"key": key})
                    return entry

            # Entry is fully expired
            del self._store[key]
            if self._logger:
                self._logger.debug("Cache entry expired", {"key": key})
            return None

        if self._logger:
            self._logger.debug("Cache hit", {"key": key})
        return entry

    async def set(self, key: str, entry: CacheEntry) -> None:
        """Store an entry in the cache.

        Args:
            key: The cache key
            entry: The cache entry to store
        """
        # Don't cache if no-store
        if entry.cache_control.no_store:
            if self._logger:
                self._logger.debug("Not caching due to no-store", {"key": key})
            return

        # Evict oldest entries if at capacity
        while len(self._store) >= self._max_entries:
            oldest_key, _ = self._store.popitem(last=False)
            if self._logger:
                self._logger.debug("Evicted oldest cache entry", {"key": oldest_key})

        self._store[key] = entry
        if self._logger:
            self._logger.debug("Cache set", {"key": key, "expires_at": entry.expires_at})

    async def delete(self, key: str) -> None:
        """Delete an entry from the cache.

        Args:
            key: The cache key to delete
        """
        if key in self._store:
            del self._store[key]
            if self._logger:
                self._logger.debug("Cache delete", {"key": key})

    def clear(self) -> None:
        """Clear all cache entries."""
        self._store.clear()
        if self._logger:
            self._logger.debug("Cache cleared")

    @property
    def size(self) -> int:
        """Get the current number of cached entries."""
        return len(self._store)
