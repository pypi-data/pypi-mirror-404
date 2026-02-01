"""Basic extraction example.

This example demonstrates how to extract structured data from a web page.

Usage:
    export REFYNE_API_KEY=your_api_key_here
    python examples/basic_extraction.py
"""

import asyncio
import os

from refyne import Refyne


async def main() -> None:
    """Run the basic extraction example."""
    api_key = os.environ.get("REFYNE_API_KEY")
    if not api_key:
        print("Error: REFYNE_API_KEY environment variable not set")
        return

    # Create a client - use async context manager for automatic cleanup
    async with Refyne(api_key=api_key, timeout=60.0) as client:
        print("Extracting product data...\n")

        try:
            # Extract structured data from a page
            result = await client.extract(
                url="https://example.com/product/123",
                schema={
                    "name": {"type": "string", "description": "Product name"},
                    "price": {"type": "number", "description": "Price in USD"},
                    "description": {"type": "string", "description": "Product description"},
                    "in_stock": {"type": "boolean", "description": "Whether in stock"},
                },
            )

            print("Extracted data:")
            for key, value in result.data.items():
                print(f"  {key}: {value}")

            print(f"\nURL: {result.url}")
            print(f"Fetched at: {result.fetched_at}")

            if result.usage:
                print("\nUsage:")
                print(f"  Input tokens: {result.usage.input_tokens}")
                print(f"  Output tokens: {result.usage.output_tokens}")
                print(f"  Cost: ${result.usage.cost_usd:.4f}")

            if result.metadata:
                print("\nPerformance:")
                print(f"  Fetch time: {result.metadata.fetch_duration_ms}ms")
                print(f"  Extract time: {result.metadata.extract_duration_ms}ms")
                print(f"  Model: {result.metadata.provider}/{result.metadata.model}")

        except Exception as e:
            print(f"Extraction failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
