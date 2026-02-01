# Refyne Python SDK Examples

This directory contains example code demonstrating how to use the Refyne Python SDK.

## Prerequisites

- Python 3.9+
- A valid Refyne API key

## Installation

Install the SDK and example dependencies:

```bash
pip install refyne rich
```

Or using uv:

```bash
uv pip install refyne rich
```

## Environment Setup

Set the required environment variables:

```bash
export REFYNE_API_KEY="your_api_key_here"
export REFYNE_BASE_URL="https://api.refyne.uk"  # Optional, defaults to production
```

## Examples

### Full Demo (`full_demo.py`)

A comprehensive demo that tests all major SDK functionality:
- Usage/subscription information retrieval
- Job listing
- Website analysis (structure detection)
- Single page extraction
- Crawl job creation and monitoring
- Job result retrieval

**Run with:**

```bash
python examples/full_demo.py
```

Or using uv:

```bash
uv run python examples/full_demo.py
```

## Notes

- The demo uses the `rich` library for colorful terminal output
- All API calls are async - run with `asyncio.run(main())`
- Error handling demonstrates the `RefyneError` class for API errors
- The client should be closed after use with `await client.close()`
