#!/usr/bin/env python3
"""Full SDK Demo - Tests all major functionality

Install dependencies: pip install rich httpx
Run with: python examples/full_demo.py
"""

import asyncio
import json
import sys

# Check for rich library
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
except ImportError:
    print("Please install rich: pip install rich")
    sys.exit(1)

# Add src to path for development
sys.path.insert(0, 'src')

# Configuration - Override with environment variables for local development
import os

from refyne import Refyne, RefyneError
from refyne.version import MAX_KNOWN_API_VERSION, MIN_API_VERSION, SDK_VERSION

API_KEY = os.environ.get("REFYNE_API_KEY")
if not API_KEY:
    print("Error: REFYNE_API_KEY environment variable is required")
    sys.exit(1)
BASE_URL = os.environ.get("REFYNE_BASE_URL", "https://api.refyne.uk")
TEST_URL = "https://www.bbc.co.uk/news"

console = Console()


def header(text: str) -> None:
    """Print a section header."""
    console.print()
    console.print(Panel(text, style="bold blue"))


def subheader(text: str) -> None:
    """Print a subsection header."""
    console.print(f"[bold cyan]> {text}[/bold cyan]")


def info(label: str, value: str) -> None:
    """Print an info line."""
    console.print(f"  [dim]{label}:[/dim] {value}")


def success(text: str) -> None:
    """Print a success message."""
    console.print(f"[green]OK[/green] {text}")


def warn(text: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]WARN[/yellow] {text}")


def error(text: str) -> None:
    """Print an error message."""
    console.print(f"[red]ERR[/red] {text}")


def print_json(obj) -> None:
    """Print formatted JSON."""
    if hasattr(obj, '__dict__'):
        obj = obj.__dict__
    syntax = Syntax(
        json.dumps(obj, indent=2, default=str),
        "json",
        theme="monokai",
        line_numbers=False,
    )
    console.print(syntax)


async def main() -> None:
    # Banner
    console.print()
    console.print(
        Panel(
            "[bold magenta]Refyne Python SDK - Full Demo[/bold magenta]",
            border_style="magenta",
        )
    )

    # ========== Configuration ==========
    header("Configuration")

    subheader("SDK Information")
    info("SDK Version", SDK_VERSION)
    info("Min API Version", MIN_API_VERSION)
    info("Max Known API Version", MAX_KNOWN_API_VERSION)
    info("Runtime", f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    subheader("Client Settings")
    info("Base URL", BASE_URL)
    info("API Key", f"{API_KEY[:10]}...{API_KEY[-4:]}")
    info("Timeout", "30s")
    info("Max Retries", "3")
    info("Cache", "Enabled (in-memory)")

    # Create client
    client = Refyne(api_key=API_KEY, base_url=BASE_URL)

    try:
        # ========== Usage Info ==========
        header("Usage Information")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Fetching usage details...", total=None)
            usage = await client.get_usage()
            progress.remove_task(task)

        success("Usage details retrieved")
        info("Total Jobs", str(usage.total_jobs))
        info("Total Charged", f"${usage.total_charged_usd:.2f} USD")
        info("BYOK Jobs", str(usage.byok_jobs))

        # ========== List Jobs ==========
        header("Recent Jobs")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Fetching job list...", total=None)
            job_list = await client.jobs.list(limit=5, offset=0)
            progress.remove_task(task)

        success(f"Found {len(job_list.jobs)} jobs")

        if job_list.jobs:
            subheader("Latest Jobs")
            for job in job_list.jobs[:3]:
                console.print()
                info("ID", job.id)
                info("Type", job.type)
                info("Status", str(job.status))
                info("URL", job.url)
                info("Pages", str(job.page_count))
                if job.completed_at:
                    info("Completed", job.completed_at)

        # ========== Try Analyze ==========
        header("Website Analysis")

        subheader("Target")
        info("URL", TEST_URL)

        suggested_schema = None
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Analyzing website structure...", total=None)
            try:
                analysis = await client.analyze(url=TEST_URL)
                progress.remove_task(task)
                success("Website analysis complete")
                # suggested_schema is a YAML string - display it and use fallback dict
                info("Suggested Schema (YAML)", "")
                console.print(f"[dim]{analysis.suggested_schema}[/dim]")
                # Use a simple dict schema for extraction demo
                suggested_schema = {"headline": "string", "summary": "string"}
                info("Using simplified schema for demo", "")
                print_json(suggested_schema)
            except RefyneError as e:
                progress.remove_task(task)
                warn(f"Analysis unavailable: {e}")
                suggested_schema = {"headline": "string", "summary": "string"}
                info("Using fallback schema", "")
                print_json(suggested_schema)

        # ========== Single Page Extract ==========
        header("Single Page Extraction")

        subheader("Request")
        info("URL", TEST_URL)
        info("Schema", "Using schema from above")

        schema = suggested_schema or {"title": "string", "description": "string"}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Extracting data from page...", total=None)
            try:
                result = await client.extract(url=TEST_URL, schema=schema)
                progress.remove_task(task)
                success("Extraction complete")

                subheader("Result")
                info("Fetched At", result.fetched_at)
                if result.usage:
                    info("Tokens", f"{result.usage.input_tokens} in / {result.usage.output_tokens} out")
                    info("Cost", f"${result.usage.cost_usd:.6f}")
                if result.metadata:
                    info("Model", f"{result.metadata.provider}/{result.metadata.model}")

                subheader("Extracted Data")
                print_json(result.data)
            except RefyneError as e:
                progress.remove_task(task)
                warn(f"Extraction failed: {e}")

        # ========== Crawl Job ==========
        header("Crawl Job")

        subheader("Request")
        info("URL", TEST_URL)
        info("Max URLs", "5")
        info("Schema", "Using schema from above")

        job_id = None
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Starting crawl job...", total=None)
            try:
                crawl_result = await client.crawl(
                    url=TEST_URL,
                    schema=schema,
                    options={"max_urls": 5, "max_depth": 1},
                )
                progress.remove_task(task)
                success("Crawl job started")
                job_id = crawl_result.job_id
                info("Job ID", job_id)
                info("Status", str(crawl_result.status))
            except RefyneError as e:
                progress.remove_task(task)
                warn(f"Failed to start crawl: {e}")

        # ========== Monitor Job Progress ==========
        if job_id:
            header("Monitoring Job Progress")

            subheader("Polling job status...")

            last_status = ""
            page_count = 0
            poll_interval = 2.0

            while True:
                job = await client.jobs.get(job_id)

                if str(job.status) != last_status:
                    console.print(f"  [cyan]->[/cyan] Status: [bold]{job.status}[/bold]")
                    last_status = str(job.status)

                if job.page_count > page_count:
                    new_pages = job.page_count - page_count
                    for i in range(new_pages):
                        console.print(f"  [green]OK[/green] Page {page_count + i + 1} extracted")
                    page_count = job.page_count

                if str(job.status) in ("completed", "failed"):
                    if str(job.status) == "completed":
                        success(f"Crawl completed - {job.page_count} pages processed")
                    else:
                        error(f"Crawl failed: {job.error_message or 'Unknown error'}")
                    break

                await asyncio.sleep(poll_interval)

            # ========== Fetch Job Results ==========
            header("Job Results")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task("Fetching job details and results...", total=None)
                job = await client.jobs.get(job_id)
                progress.remove_task(task)

            success("Job details retrieved")

            subheader("Job Details")
            info("ID", job.id)
            info("Type", job.type)
            info("Status", str(job.status))
            info("URL", job.url)
            info("Pages Processed", str(job.page_count))
            info("Tokens", f"{job.token_usage_input} in / {job.token_usage_output} out")
            info("Cost", f"${job.cost_usd:.4f} USD")
            if job.started_at:
                info("Started", job.started_at)
            if job.completed_at:
                info("Completed", job.completed_at)

            # Get results
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task("Fetching extraction results...", total=None)
                results = await client.jobs.get_results(job_id)
                progress.remove_task(task)

            success("Results retrieved")

            subheader("Extracted Data")
            if results.results:
                info("Total Results", str(len(results.results)))
                console.print()
                # Convert dataclasses to dicts for display
                results_data = [
                    {"id": r.id, "url": r.url, "data": r.data}
                    for r in results.results
                ]
                print_json(results_data)
            else:
                warn("No results available")

    except RefyneError as e:
        error(f"API Error: {e}")
        raise
    finally:
        await client.close()

    # ========== Done ==========
    console.print()
    console.print(Panel("[bold green]Demo Complete[/bold green]", border_style="green"))
    console.print()


if __name__ == "__main__":
    asyncio.run(main())
