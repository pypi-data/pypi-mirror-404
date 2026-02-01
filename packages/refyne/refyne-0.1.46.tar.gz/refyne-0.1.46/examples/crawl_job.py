"""Crawl job example.

This example demonstrates how to start a crawl job, poll for completion,
and retrieve results.

Usage:
    export REFYNE_API_KEY=your_api_key_here
    python examples/crawl_job.py
"""

import asyncio
import os

from refyne import JobStatus, Refyne


async def main() -> None:
    """Run the crawl job example."""
    api_key = os.environ.get("REFYNE_API_KEY")
    if not api_key:
        print("Error: REFYNE_API_KEY environment variable not set")
        return

    async with Refyne(api_key=api_key, timeout=60.0) as client:
        print("Starting crawl job...\n")

        try:
            # Start a crawl job
            job = await client.crawl(
                url="https://example.com/products",
                schema={
                    "products": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "price": {"type": "number"},
                                "url": {"type": "string"},
                            },
                        },
                    },
                },
                options={
                    "followSelector": "a.pagination-next",
                    "maxPages": 5,
                    "delay": "1s",
                    "concurrency": 2,
                },
            )

            print(f"Job created: {job.job_id}")
            print(f"Status URL: {job.status_url}")
            print()

            # Poll for completion
            status = await client.jobs.get(job.job_id)
            print(f"Initial status: {status.status.value}")

            while status.status in (JobStatus.PENDING, JobStatus.RUNNING):
                await asyncio.sleep(2)
                status = await client.jobs.get(job.job_id)
                print(f"Status: {status.status.value} ({status.page_count} pages processed)")

            print()

            if status.status == JobStatus.FAILED:
                print(f"Job failed: {status.error_message}")
                return

            # Get results
            results = await client.jobs.get_results(job.job_id)
            print(f"Completed! Processed {results.page_count} pages")
            print()

            # Display results
            if results.results:
                for i, result in enumerate(results.results, 1):
                    print(f"Page {i} result: {result}")
                    print()

            # Or get merged results
            merged = await client.jobs.get_results_merged(job.job_id)
            print("All products:")
            if "products" in merged:
                for product in merged["products"]:
                    print(f"  - {product.get('name')}: ${product.get('price')}")

        except Exception as e:
            print(f"Crawl failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
