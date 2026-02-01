"""Interfaces for dependency injection.

These protocols define the contracts for injectable components,
enabling easy testing and customization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Logger(Protocol):
    """Logger interface for SDK operations.

    Implement this protocol to provide custom logging behavior.
    The SDK will call these methods during operation.

    Example:
        >>> class MyLogger:
        ...     def debug(self, msg: str, meta: dict | None = None) -> None:
        ...         print(f"[DEBUG] {msg}")
        ...
        ...     def info(self, msg: str, meta: dict | None = None) -> None:
        ...         print(f"[INFO] {msg}")
        ...
        ...     def warn(self, msg: str, meta: dict | None = None) -> None:
        ...         print(f"[WARN] {msg}")
        ...
        ...     def error(self, msg: str, meta: dict | None = None) -> None:
        ...         print(f"[ERROR] {msg}")
    """

    def debug(self, message: str, meta: dict[str, Any] | None = None) -> None:
        """Log a debug message.

        Args:
            message: The message to log
            meta: Optional metadata dict
        """
        ...

    def info(self, message: str, meta: dict[str, Any] | None = None) -> None:
        """Log an info message.

        Args:
            message: The message to log
            meta: Optional metadata dict
        """
        ...

    def warn(self, message: str, meta: dict[str, Any] | None = None) -> None:
        """Log a warning message.

        Args:
            message: The message to log
            meta: Optional metadata dict
        """
        ...

    def error(self, message: str, meta: dict[str, Any] | None = None) -> None:
        """Log an error message.

        Args:
            message: The message to log
            meta: Optional metadata dict
        """
        ...


class DefaultLogger:
    """Default logger that does nothing.

    Override by providing a custom Logger to the client.
    """

    def debug(self, message: str, meta: dict[str, Any] | None = None) -> None:
        """Log a debug message (no-op)."""
        pass

    def info(self, message: str, meta: dict[str, Any] | None = None) -> None:
        """Log an info message (no-op)."""
        pass

    def warn(self, message: str, meta: dict[str, Any] | None = None) -> None:
        """Log a warning message (no-op)."""
        pass

    def error(self, message: str, meta: dict[str, Any] | None = None) -> None:
        """Log an error message (no-op)."""
        pass


@dataclass
class CacheControlDirectives:
    """Parsed Cache-Control header directives."""

    no_store: bool = False
    no_cache: bool = False
    private: bool = False
    max_age: int | None = None
    stale_while_revalidate: int | None = None


@dataclass
class CacheEntry:
    """An entry stored in the cache.

    Attributes:
        value: The cached response data
        expires_at: Unix timestamp (ms) when entry expires
        cache_control: Parsed Cache-Control directives
    """

    value: Any
    expires_at: float
    cache_control: CacheControlDirectives


@runtime_checkable
class Cache(Protocol):
    """Cache interface for storing API responses.

    Implement this protocol to provide custom caching behavior
    (e.g., Redis, file-based, etc.).

    Example:
        >>> class RedisCache:
        ...     async def get(self, key: str) -> CacheEntry | None:
        ...         # Fetch from Redis
        ...         ...
        ...
        ...     async def set(self, key: str, entry: CacheEntry) -> None:
        ...         # Store in Redis with TTL
        ...         ...
        ...
        ...     async def delete(self, key: str) -> None:
        ...         # Delete from Redis
        ...         ...
    """

    async def get(self, key: str) -> CacheEntry | None:
        """Get a cached entry by key.

        Args:
            key: The cache key

        Returns:
            The cached entry, or None if not found/expired
        """
        ...

    async def set(self, key: str, entry: CacheEntry) -> None:
        """Store an entry in the cache.

        Args:
            key: The cache key
            entry: The cache entry to store
        """
        ...

    async def delete(self, key: str) -> None:
        """Delete an entry from the cache.

        Args:
            key: The cache key to delete
        """
        ...


@runtime_checkable
class HttpClient(Protocol):
    """HTTP client interface for making requests.

    Implement this protocol to provide custom HTTP behavior
    (e.g., for testing or custom transports).
    """

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Make an HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Request headers
            json: JSON body to send
            timeout: Request timeout in seconds

        Returns:
            httpx-compatible Response object
        """
        ...
