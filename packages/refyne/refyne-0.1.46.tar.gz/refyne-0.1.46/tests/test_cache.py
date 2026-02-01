"""Tests for the cache module."""

import time

import pytest

from refyne.cache import (
    MemoryCache,
    create_cache_entry,
    generate_cache_key,
    hash_string,
    parse_cache_control,
)
from refyne.interfaces import CacheControlDirectives


class TestParseCacheControl:
    """Tests for parse_cache_control."""

    def test_returns_empty_for_none(self) -> None:
        """Test that None header returns empty directives."""
        result = parse_cache_control(None)
        assert result == CacheControlDirectives()

    def test_returns_empty_for_empty_string(self) -> None:
        """Test that empty string returns empty directives."""
        result = parse_cache_control("")
        assert result == CacheControlDirectives()

    def test_parses_no_store(self) -> None:
        """Test parsing no-store directive."""
        result = parse_cache_control("no-store")
        assert result.no_store is True

    def test_parses_no_cache(self) -> None:
        """Test parsing no-cache directive."""
        result = parse_cache_control("no-cache")
        assert result.no_cache is True

    def test_parses_private(self) -> None:
        """Test parsing private directive."""
        result = parse_cache_control("private")
        assert result.private is True

    def test_parses_max_age(self) -> None:
        """Test parsing max-age directive."""
        result = parse_cache_control("max-age=3600")
        assert result.max_age == 3600

    def test_parses_stale_while_revalidate(self) -> None:
        """Test parsing stale-while-revalidate directive."""
        result = parse_cache_control("stale-while-revalidate=60")
        assert result.stale_while_revalidate == 60

    def test_parses_multiple_directives(self) -> None:
        """Test parsing multiple directives."""
        result = parse_cache_control("private, max-age=3600, stale-while-revalidate=60")
        assert result.private is True
        assert result.max_age == 3600
        assert result.stale_while_revalidate == 60

    def test_ignores_invalid_max_age(self) -> None:
        """Test that invalid max-age is ignored."""
        result = parse_cache_control("max-age=invalid")
        assert result.max_age is None


class TestGenerateCacheKey:
    """Tests for generate_cache_key."""

    def test_generates_key_from_method_and_url(self) -> None:
        """Test basic key generation."""
        key = generate_cache_key("GET", "https://api.example.com/data")
        assert key == "GET:https://api.example.com/data"

    def test_includes_auth_hash(self) -> None:
        """Test key generation with auth hash."""
        key = generate_cache_key("GET", "https://api.example.com/data", "abc123")
        assert key == "GET:https://api.example.com/data:abc123"

    def test_normalizes_method_to_uppercase(self) -> None:
        """Test that method is uppercased."""
        key = generate_cache_key("get", "https://api.example.com/data")
        assert key == "GET:https://api.example.com/data"


class TestHashString:
    """Tests for hash_string."""

    def test_consistent_hash(self) -> None:
        """Test that same input produces same hash."""
        hash1 = hash_string("test-api-key")
        hash2 = hash_string("test-api-key")
        assert hash1 == hash2

    def test_different_hashes_for_different_inputs(self) -> None:
        """Test that different inputs produce different hashes."""
        hash1 = hash_string("key1")
        hash2 = hash_string("key2")
        assert hash1 != hash2


class TestCreateCacheEntry:
    """Tests for create_cache_entry."""

    def test_returns_none_for_no_store(self) -> None:
        """Test that no-store returns None."""
        entry = create_cache_entry({"data": "test"}, "no-store")
        assert entry is None

    def test_returns_none_without_max_age(self) -> None:
        """Test that missing max-age returns None."""
        entry = create_cache_entry({"data": "test"}, "private")
        assert entry is None

    def test_creates_entry_with_max_age(self) -> None:
        """Test creating entry with max-age."""
        now = time.time()
        entry = create_cache_entry({"data": "test"}, "max-age=3600")

        assert entry is not None
        assert entry.value == {"data": "test"}
        assert entry.expires_at >= now + 3600
        assert entry.cache_control.max_age == 3600


class TestMemoryCache:
    """Tests for MemoryCache."""

    @pytest.fixture
    def cache(self) -> MemoryCache:
        """Create a cache instance."""
        return MemoryCache(max_entries=3)

    @pytest.mark.asyncio
    async def test_stores_and_retrieves(self, cache: MemoryCache) -> None:
        """Test basic store and retrieve."""
        entry = create_cache_entry({"data": "test"}, "max-age=3600")
        assert entry is not None

        await cache.set("key1", entry)
        retrieved = await cache.get("key1")

        assert retrieved is not None
        assert retrieved.value == {"data": "test"}

    @pytest.mark.asyncio
    async def test_returns_none_for_missing(self, cache: MemoryCache) -> None:
        """Test that missing keys return None."""
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_expires_entries(self, cache: MemoryCache) -> None:
        """Test that expired entries return None."""
        entry = create_cache_entry({"data": "test"}, "max-age=3600")
        assert entry is not None

        # Set expiry to past
        entry.expires_at = time.time() - 1000

        await cache.set("key1", entry)
        result = await cache.get("key1")

        assert result is None

    @pytest.mark.asyncio
    async def test_evicts_oldest(self, cache: MemoryCache) -> None:
        """Test that oldest entries are evicted at capacity."""
        for i in range(4):
            entry = create_cache_entry(f"value{i}", "max-age=3600")
            assert entry is not None
            await cache.set(f"key{i}", entry)

        # key0 should be evicted
        assert await cache.get("key0") is None
        assert await cache.get("key1") is not None
        assert await cache.get("key2") is not None
        assert await cache.get("key3") is not None

    @pytest.mark.asyncio
    async def test_delete(self, cache: MemoryCache) -> None:
        """Test deleting entries."""
        entry = create_cache_entry("value", "max-age=3600")
        assert entry is not None

        await cache.set("key1", entry)
        await cache.delete("key1")

        assert await cache.get("key1") is None

    def test_clear(self, cache: MemoryCache) -> None:
        """Test clearing all entries."""
        cache.clear()
        assert cache.size == 0
