# Refyne SDK for Python

Official Python SDK for the [Refyne API](https://refyne.uk/docs) - LLM-powered web extraction that transforms unstructured websites into clean, typed data.

**API Endpoint**: `https://api.refyne.uk` | **Documentation**: [refyne.uk/docs](https://refyne.uk/docs)

[![PyPI version](https://badge.fury.io/py/refyne.svg)](https://pypi.org/project/refyne/)
[![CI](https://github.com/jmylchreest/refyne-sdk-python/actions/workflows/test.yml/badge.svg)](https://github.com/jmylchreest/refyne-sdk-python/actions/workflows/test.yml)

## Features

- **Async-First**: Built on httpx for async/await support
- **Type-Safe**: Full type hints and dataclasses
- **Smart Caching**: Respects `Cache-Control` headers automatically
- **Auto-Retry**: Handles rate limits and transient errors with exponential backoff
- **SOLID Design**: Dependency injection for loggers, HTTP clients, and caches
- **API Version Compatibility**: Warns about breaking changes
- **Python 3.9+**: Supports Python 3.9 through 3.13

## Installation

```bash
pip install refyne
```

## Quick Start

```python
import asyncio
from refyne import Refyne

async def main():
    # Create client
    client = Refyne(api_key="your_api_key")

    # Extract structured data from a web page
    result = await client.extract(
        url="https://example.com/product/123",
        schema={
            "name": {"type": "string", "description": "Product name"},
            "price": {"type": "number", "description": "Price in USD"},
            "in_stock": {"type": "boolean"},
        },
    )

    print(result.data)
    # {"name": "Example Product", "price": 29.99, "in_stock": True}

    # Don't forget to close the client
    await client.close()

asyncio.run(main())
```

### Using Context Manager

```python
async with Refyne(api_key="your_api_key") as client:
    result = await client.extract(url=url, schema=schema)
```

## Crawl Jobs

Extract data from multiple pages:

```python
from refyne import Refyne, JobStatus

async with Refyne(api_key="your_api_key") as client:
    # Start a crawl job
    job = await client.crawl(
        url="https://example.com/products",
        schema={"name": "string", "price": "number"},
        options={
            "followSelector": "a.product-link",
            "maxPages": 20,
            "delay": "1s",
        },
    )

    print(f"Job started: {job.job_id}")

    # Poll for completion
    status = await client.jobs.get(job.job_id)
    while status.status in (JobStatus.PENDING, JobStatus.RUNNING):
        await asyncio.sleep(2)
        status = await client.jobs.get(job.job_id)
        print(f"Progress: {status.page_count} pages")

    # Get results
    results = await client.jobs.get_results(job.job_id)
    print(f"Extracted {results.page_count} pages")
```

## Configuration

```python
from refyne import Refyne

client = Refyne(
    api_key="your_api_key",
    base_url="https://api.refyne.uk",  # Override API URL
    timeout=60.0,                       # Request timeout (seconds)
    max_retries=3,                      # Retry attempts
    logger=my_logger,                   # Custom logger
    cache=my_cache,                     # Custom cache
    cache_enabled=True,                 # Enable/disable caching
    user_agent_suffix="MyApp/1.0",     # Custom User-Agent
    verify_ssl=True,                    # SSL verification
)
```

## Custom Logger

Inject your own logger:

```python
from refyne import Logger

class MyLogger:
    def debug(self, msg: str, meta: dict | None = None) -> None:
        print(f"[DEBUG] {msg}")

    def info(self, msg: str, meta: dict | None = None) -> None:
        print(f"[INFO] {msg}")

    def warn(self, msg: str, meta: dict | None = None) -> None:
        print(f"[WARN] {msg}")

    def error(self, msg: str, meta: dict | None = None) -> None:
        print(f"[ERROR] {msg}")

client = Refyne(api_key="...", logger=MyLogger())
```

## Custom Cache

The SDK respects `Cache-Control` headers. Provide a custom cache:

```python
from refyne import Cache, CacheEntry

class RedisCache:
    async def get(self, key: str) -> CacheEntry | None:
        # Fetch from Redis
        ...

    async def set(self, key: str, entry: CacheEntry) -> None:
        # Store in Redis with TTL from entry.expires_at
        ...

    async def delete(self, key: str) -> None:
        # Delete from Redis
        ...

client = Refyne(api_key="...", cache=RedisCache())
```

## BYOK (Bring Your Own Key)

Use your own LLM provider API keys:

```python
# Configure your OpenAI key
await client.llm.upsert_key(
    provider="openai",
    api_key="sk-...",
    default_model="gpt-4o",
)

# Set fallback chain
await client.llm.set_chain([
    {"provider": "openai", "model": "gpt-4o"},
    {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"},
    {"provider": "credits", "model": "default"},
])

# Extract using your keys
result = await client.extract(
    url="https://example.com/product",
    schema={"title": "string"},
    llm_config={
        "provider": "openai",
        "model": "gpt-4o-mini",
    },
)

print(f"Used BYOK: {result.usage.is_byok}")
```

## Error Handling

```python
from refyne import (
    RefyneError,
    RateLimitError,
    ValidationError,
    AuthenticationError,
)

try:
    await client.extract(url=url, schema=schema)
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except ValidationError as e:
    print(f"Validation errors: {e.errors}")
except AuthenticationError:
    print("Invalid API key")
except RefyneError as e:
    print(f"API error: {e.message} ({e.status})")
```

## API Reference

### Main Client

| Method | Description |
|--------|-------------|
| `client.extract(url, schema)` | Extract data from a single page |
| `client.crawl(url, schema, options)` | Start an async crawl job |
| `client.analyze(url, depth)` | Analyze a site and suggest schema |
| `client.get_usage()` | Get usage statistics |

### Sub-Clients

| Client | Methods |
|--------|---------|
| `client.jobs` | `list()`, `get(id)`, `get_results(id)` |
| `client.schemas` | `list()`, `get(id)`, `create()`, `update()`, `delete()` |
| `client.sites` | `list()`, `get(id)`, `create()`, `update()`, `delete()` |
| `client.keys` | `list()`, `create()`, `revoke(id)` |
| `client.llm` | `list_providers()`, `list_keys()`, `upsert_key()`, `get_chain()`, `set_chain()` |

## Documentation

- [API Reference](https://docs.refyne.uk/docs/api-reference)
- [Python SDK Guide](https://docs.refyne.uk/docs/sdks/python)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src tests

# Run type checker
mypy src
```

## Testing with Demo Site

A demo site is available at [demo.refyne.uk](https://demo.refyne.uk) for testing SDK functionality. The site contains realistic data across multiple content types:

| Endpoint | Content Type | Example Use Case |
|----------|--------------|------------------|
| `https://demo.refyne.uk/products` | Product catalog | Extract prices, descriptions, ratings |
| `https://demo.refyne.uk/jobs` | Job listings | Extract salaries, requirements, companies |
| `https://demo.refyne.uk/blog` | Blog posts | Extract articles, authors, tags |
| `https://demo.refyne.uk/news` | News articles | Extract headlines, sources, timestamps |

Example:

```python
result = await client.extract(
    url="https://demo.refyne.uk/products/1",
    schema={
        "name": "string",
        "price": "number",
        "description": "string",
        "brand": "string",
        "rating": "number",
    },
)
```

## License

MIT License - see [LICENSE](LICENSE) for details.
