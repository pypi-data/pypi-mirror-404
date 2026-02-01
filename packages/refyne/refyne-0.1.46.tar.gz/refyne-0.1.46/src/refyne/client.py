"""Main Refyne client implementation."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from typing import Any, TypeVar
from urllib.parse import urlencode

import httpx

from refyne.cache import (
    MemoryCache,
    create_cache_entry,
    generate_cache_key,
    hash_string,
)
from refyne.errors import RefyneError, create_error_from_response
from refyne.interfaces import Cache, DefaultLogger, Logger
from refyne.types import (
    AnalyzeResponseBody as AnalyzeResponse,
    CreateKeyOutputBody as ApiKeyCreated,
    CrawlJobResponseBody as CrawlJobCreated,
    ExtractOutputBody as ExtractResponse,
    GetUsageOutputBody as UsageResponse,
    GetUserFallbackChainOutputBody as LlmChain,
    JobResponse as Job,
    ListJobsOutputBody as JobList,
    ListKeysOutputBody as ApiKeyList,
    ListSavedSitesOutputBody as SiteList,
    ListSchemasOutputBody as SchemaList,
    ListUserServiceKeysOutputBody as LlmKeyList,
    SavedSiteOutput as Site,
    SchemaOutput as Schema,
    ListModelsOutputBody as ModelList,
    UserServiceKeyResponse as LlmKey,
)
from refyne.version import build_user_agent, check_api_version_compatibility


@dataclass
class JobResultEntry:
    """A single result entry from a crawl job."""

    id: str
    url: str
    data: dict[str, Any]


@dataclass
class JobResults:
    """Response from the job results endpoint."""

    job_id: str
    status: str
    page_count: int
    results: list[JobResultEntry] | None = None
    merged: dict[str, Any] | None = None

T = TypeVar("T")


@dataclass
class RefyneConfig:
    """Configuration options for the Refyne client.

    Attributes:
        api_key: Your Refyne API key
        base_url: Base URL for the API (default: https://api.refyne.uk)
        timeout: Request timeout in seconds (default: 30)
        max_retries: Maximum retry attempts for failed requests (default: 3)
        logger: Custom logger implementation
        cache: Custom cache implementation
        cache_enabled: Whether caching is enabled (default: True)
        user_agent_suffix: Custom User-Agent suffix (e.g., "MyApp/1.0")
        verify_ssl: Whether to verify SSL certificates (default: True)
    """

    api_key: str
    base_url: str = "https://api.refyne.uk"
    timeout: float = 30.0
    max_retries: int = 3
    logger: Logger = field(default_factory=DefaultLogger)
    cache: Cache | None = None
    cache_enabled: bool = True
    user_agent_suffix: str | None = None
    verify_ssl: bool = True


class Refyne:
    """The main Refyne SDK client.

    Provides methods for extracting data from web pages, managing crawl jobs,
    and configuring LLM providers.

    Example:
        >>> from refyne import Refyne
        >>>
        >>> client = Refyne(api_key="your_api_key")
        >>>
        >>> # Extract data from a page
        >>> result = await client.extract(
        ...     url="https://example.com/product",
        ...     schema={"name": "string", "price": "number"},
        ... )
        >>> print(result.data)
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.refyne.uk",
        timeout: float = 30.0,
        max_retries: int = 3,
        logger: Logger | None = None,
        cache: Cache | None = None,
        cache_enabled: bool = True,
        user_agent_suffix: str | None = None,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize the Refyne client.

        Args:
            api_key: Your Refyne API key
            base_url: Base URL for the API (default: https://api.refyne.uk)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retry attempts for failed requests (default: 3)
            logger: Custom logger implementation
            cache: Custom cache implementation
            cache_enabled: Whether caching is enabled (default: True)
            user_agent_suffix: Custom User-Agent suffix (e.g., "MyApp/1.0")
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._logger = logger or DefaultLogger()
        self._cache: Cache = cache or MemoryCache(logger=self._logger)
        self._cache_enabled = cache_enabled
        self._user_agent = build_user_agent(user_agent_suffix)
        self._verify_ssl = verify_ssl

        # Hash the API key for cache key generation
        self._auth_hash = hash_string(api_key)

        # Track if we've checked API version
        self._api_version_checked = False

        # httpx client - created lazily
        self._http_client: httpx.AsyncClient | None = None

        # Warn about insecure connections
        if not self._base_url.startswith("https://"):
            self._logger.warn(
                "API base URL is not using HTTPS. This is insecure.",
                {"base_url": self._base_url},
            )

        if not verify_ssl:
            self._logger.warn(
                "SSL certificate verification is disabled. "
                "This is dangerous and should only be used for development.",
                {"base_url": self._base_url},
            )

        # Initialize sub-clients
        self.jobs = JobsClient(self)
        self.schemas = SchemasClient(self)
        self.sites = SitesClient(self)
        self.keys = KeysClient(self)
        self.llm = LlmClient(self)
        self.webhooks = WebhooksClient(self)

    @classmethod
    def from_config(cls, config: RefyneConfig) -> Refyne:
        """Create a client from a config object.

        Args:
            config: Configuration object

        Returns:
            Configured Refyne client
        """
        return cls(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
            logger=config.logger,
            cache=config.cache,
            cache_enabled=config.cache_enabled,
            user_agent_suffix=config.user_agent_suffix,
            verify_ssl=config.verify_ssl,
        )

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=self._timeout,
                verify=self._verify_ssl,
            )
        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self) -> Refyne:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def extract(
        self,
        url: str,
        schema: dict[str, Any],
        *,
        fetch_mode: str | None = None,
        llm_config: dict[str, Any] | None = None,
    ) -> ExtractResponse:
        """Extract structured data from a single web page.

        Args:
            url: URL to extract data from
            schema: Schema defining the data structure to extract
            fetch_mode: Fetch mode (auto, static, or dynamic)
            llm_config: Custom LLM configuration

        Returns:
            Extracted data matching the schema

        Example:
            >>> result = await client.extract(
            ...     url="https://example.com/product/123",
            ...     schema={
            ...         "name": "string",
            ...         "price": "number",
            ...         "description": "string",
            ...     },
            ... )
            >>> print(result.data["name"])
            'Product Name'
        """
        body: dict[str, Any] = {"url": url, "schema": schema}
        if fetch_mode:
            body["fetchMode"] = fetch_mode
        if llm_config:
            body["llmConfig"] = llm_config

        data = await self._request("POST", "/api/v1/extract", body=body)
        return self._parse_extract_response(data)

    async def crawl(
        self,
        url: str,
        schema: dict[str, Any],
        *,
        options: dict[str, Any] | None = None,
        webhook_url: str | None = None,
        llm_config: dict[str, Any] | None = None,
    ) -> CrawlJobCreated:
        """Start an asynchronous crawl job.

        Args:
            url: Seed URL to start crawling from
            schema: Schema defining the data structure to extract
            options: Crawl options (max_pages, delay, etc.)
            webhook_url: URL to notify on completion
            llm_config: Custom LLM configuration

        Returns:
            Job creation response with job ID

        Example:
            >>> job = await client.crawl(
            ...     url="https://example.com/products",
            ...     schema={"name": "string", "price": "number"},
            ...     options={"max_pages": 20, "delay": "1s"},
            ... )
            >>> print(f"Job started: {job.job_id}")
        """
        body: dict[str, Any] = {"url": url, "schema": schema}
        if options:
            body["options"] = options
        if webhook_url:
            body["webhookUrl"] = webhook_url
        if llm_config:
            body["llmConfig"] = llm_config

        data = await self._request("POST", "/api/v1/crawl", body=body)
        return CrawlJobCreated.model_validate(data)

    async def analyze(
        self,
        url: str,
        *,
        depth: int | None = None,
    ) -> AnalyzeResponse:
        """Analyze a website to detect structure and suggest schemas.

        Args:
            url: URL to analyze
            depth: Analysis depth (default: 1)

        Returns:
            Analysis results with suggested schema and patterns

        Example:
            >>> analysis = await client.analyze(
            ...     url="https://example.com/products",
            ...     depth=1,
            ... )
            >>> print(analysis.suggested_schema)
        """
        body: dict[str, Any] = {"url": url}
        if depth is not None:
            body["depth"] = depth

        from refyne.types import AnalyzeResponseBody

        data = await self._request("POST", "/api/v1/analyze", body=body)
        return AnalyzeResponseBody.model_validate(data)

    async def get_usage(self) -> UsageResponse:
        """Get usage statistics for the current billing period.

        Returns:
            Usage statistics including credits used and remaining
        """
        data = await self._request("GET", "/api/v1/usage")
        return UsageResponse.model_validate(data)

    async def health(self) -> dict[str, Any]:
        """Check API health status.

        Returns:
            Health check response with status and version
        """
        return await self._request("GET", "/api/v1/health")

    async def list_cleaners(self) -> dict[str, Any]:
        """List available content cleaners.

        Returns:
            List of cleaners with their options
        """
        return await self._request("GET", "/api/v1/cleaners")

    async def get_pricing_tiers(self) -> dict[str, Any]:
        """Get available pricing tiers and their limits.

        Returns:
            List of pricing tiers with limits
        """
        return await self._request("GET", "/api/v1/pricing/tiers")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        skip_cache: bool = False,
    ) -> dict[str, Any]:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method
            path: API path
            body: Request body
            skip_cache: Whether to skip cache lookup

        Returns:
            Response data as dict
        """
        url = f"{self._base_url}{path}"
        cache_key = generate_cache_key(method, url, self._auth_hash)

        # Check cache for GET requests
        if method == "GET" and self._cache_enabled and not skip_cache:
            cached = await self._cache.get(cache_key)
            if cached:
                return dict(cached.value)

        response = await self._execute_with_retry(method, url, body)

        # Check API version on first request
        if not self._api_version_checked:
            api_version = response.headers.get("X-API-Version")
            if api_version:
                check_api_version_compatibility(api_version, self._logger)
            else:
                self._logger.warn("API did not return X-API-Version header")
            self._api_version_checked = True

        # Parse response
        if not response.is_success:
            raise await create_error_from_response(response)

        data: dict[str, Any] = response.json()

        # Cache GET responses
        if method == "GET" and self._cache_enabled:
            cache_control = response.headers.get("Cache-Control")
            entry = create_cache_entry(data, cache_control)
            if entry:
                await self._cache.set(cache_key, entry)

        return data

    async def _execute_with_retry(
        self,
        method: str,
        url: str,
        body: dict[str, Any] | None = None,
        attempt: int = 1,
    ) -> httpx.Response:
        """Execute a request with retry logic.

        Args:
            method: HTTP method
            url: Request URL
            body: Request body
            attempt: Current attempt number

        Returns:
            httpx Response
        """
        client = await self._get_http_client()

        try:
            response = await client.request(
                method,
                url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": self._user_agent,
                    "Accept": "application/json",
                },
                json=body,
            )

            # Handle rate limiting with retry
            if response.status_code == 429 and attempt <= self._max_retries:
                retry_after = int(response.headers.get("Retry-After", "1"))
                self._logger.warn(
                    f"Rate limited. Retrying in {retry_after}s",
                    {"attempt": attempt, "max_retries": self._max_retries},
                )
                await asyncio.sleep(retry_after)
                return await self._execute_with_retry(method, url, body, attempt + 1)

            # Handle server errors with retry
            if response.status_code >= 500 and attempt <= self._max_retries:
                backoff = self._calculate_backoff(attempt)
                self._logger.warn(
                    f"Server error. Retrying in {backoff:.2f}s",
                    {
                        "status": response.status_code,
                        "attempt": attempt,
                        "max_retries": self._max_retries,
                    },
                )
                await asyncio.sleep(backoff)
                return await self._execute_with_retry(method, url, body, attempt + 1)

            return response

        except httpx.TimeoutException:
            raise RefyneError(f"Request timed out after {self._timeout}s", 0)

        except httpx.RequestError as e:
            # Retry on network errors
            if attempt <= self._max_retries:
                backoff = self._calculate_backoff(attempt)
                self._logger.warn(
                    f"Network error. Retrying in {backoff:.2f}s",
                    {
                        "error": str(e),
                        "attempt": attempt,
                        "max_retries": self._max_retries,
                    },
                )
                await asyncio.sleep(backoff)
                return await self._execute_with_retry(method, url, body, attempt + 1)

            raise RefyneError(f"Network error: {e}", 0)

    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter.

        Args:
            attempt: Current attempt number (1-based)

        Returns:
            Backoff duration in seconds with jitter applied
        """
        # Exponential backoff: 2^(attempt-1) seconds
        base_backoff = min(2 ** (attempt - 1), 30)
        # Add jitter: random value between 0% and 25% of the backoff
        jitter = random.random() * 0.25 * base_backoff
        return base_backoff + jitter

    def _parse_extract_response(self, data: dict[str, Any]) -> ExtractResponse:
        """Parse extraction response data."""
        from refyne.types import ExtractOutputBody

        return ExtractOutputBody.model_validate(data)


class JobsClient:
    """Client for job-related operations."""

    def __init__(self, client: Refyne) -> None:
        """Initialize the jobs client.

        Args:
            client: Parent Refyne client
        """
        self._client = client

    async def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> JobList:
        """List all jobs.

        Args:
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip

        Returns:
            List of jobs
        """
        params: dict[str, int] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        query = urlencode(params) if params else ""
        path = f"/api/v1/jobs{'?' + query if query else ''}"

        from refyne.types import ListJobsOutputBody

        data = await self._client._request("GET", path)
        return ListJobsOutputBody.model_validate(data)

    async def get(self, job_id: str) -> Job:
        """Get a job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job details
        """
        from refyne.types import JobResponse

        data = await self._client._request(
            "GET", f"/api/v1/jobs/{job_id}", skip_cache=True
        )
        return JobResponse.model_validate(data)

    async def get_results(
        self,
        job_id: str,
        *,
        merge: bool = False,
    ) -> JobResults:
        """Get job results.

        Args:
            job_id: Job ID
            merge: Whether to merge results into single object

        Returns:
            Job results
        """
        path = f"/api/v1/jobs/{job_id}/results"
        if merge:
            path += "?merge=true"

        data = await self._client._request("GET", path, skip_cache=True)
        # Parse results entries if present
        results = None
        if data.get("results"):
            results = [
                JobResultEntry(id=r["id"], url=r["url"], data=r["data"])
                for r in data["results"]
            ]
        return JobResults(
            job_id=data["job_id"],
            status=data["status"],
            page_count=data["page_count"],
            results=results,
            merged=data.get("merged"),
        )

    async def get_results_merged(self, job_id: str) -> dict[str, Any]:
        """Get merged results as a single object.

        Args:
            job_id: Job ID

        Returns:
            Merged results dict
        """
        results = await self.get_results(job_id, merge=True)
        return results.merged or {}

    async def download(self, job_id: str) -> dict[str, Any]:
        """Get a presigned download URL for job results.

        Args:
            job_id: Job ID

        Returns:
            Download URL response
        """
        return await self._client._request("GET", f"/api/v1/jobs/{job_id}/download")

    async def get_crawl_map(self, job_id: str) -> dict[str, Any]:
        """Get the crawl map for a job.

        Args:
            job_id: Job ID

        Returns:
            Crawl map with page URLs and status
        """
        return await self._client._request("GET", f"/api/v1/jobs/{job_id}/crawl-map")

    async def get_debug_capture(self, job_id: str) -> dict[str, Any]:
        """Get debug capture data for a job.

        Args:
            job_id: Job ID

        Returns:
            Debug capture data
        """
        return await self._client._request("GET", f"/api/v1/jobs/{job_id}/debug-capture")

    async def get_webhook_deliveries(self, job_id: str) -> dict[str, Any]:
        """Get webhook deliveries for a job.

        Args:
            job_id: Job ID

        Returns:
            Webhook deliveries
        """
        return await self._client._request("GET", f"/api/v1/jobs/{job_id}/webhooks")

class SchemasClient:
    """Client for schema catalog operations."""

    def __init__(self, client: Refyne) -> None:
        """Initialize the schemas client."""
        self._client = client

    async def list(self) -> SchemaList:
        """List all schemas (user + platform)."""
        from refyne.types import ListSchemasOutputBody

        data = await self._client._request("GET", "/api/v1/schemas")
        return ListSchemasOutputBody.model_validate(data)

    async def get(self, schema_id: str) -> Schema:
        """Get a schema by ID."""
        from refyne.types import SchemaOutput

        data = await self._client._request("GET", f"/api/v1/schemas/{schema_id}")
        return SchemaOutput.model_validate(data)

    async def create(
        self,
        name: str,
        schema_yaml: str,
        *,
        description: str | None = None,
        category: str | None = None,
    ) -> Schema:
        """Create a new schema."""
        from refyne.types import SchemaOutput

        body: dict[str, Any] = {"name": name, "schema_yaml": schema_yaml}
        if description:
            body["description"] = description
        if category:
            body["category"] = category

        data = await self._client._request("POST", "/api/v1/schemas", body=body)
        return SchemaOutput.model_validate(data)

    async def update(
        self,
        schema_id: str,
        *,
        name: str | None = None,
        schema_yaml: str | None = None,
        description: str | None = None,
        category: str | None = None,
    ) -> Schema:
        """Update a schema."""
        from refyne.types import SchemaOutput

        body: dict[str, Any] = {}
        if name:
            body["name"] = name
        if schema_yaml:
            body["schema_yaml"] = schema_yaml
        if description:
            body["description"] = description
        if category:
            body["category"] = category

        data = await self._client._request(
            "PUT", f"/api/v1/schemas/{schema_id}", body=body
        )
        return SchemaOutput.model_validate(data)

    async def delete(self, schema_id: str) -> None:
        """Delete a schema."""
        await self._client._request("DELETE", f"/api/v1/schemas/{schema_id}")


class SitesClient:
    """Client for saved sites operations."""

    def __init__(self, client: Refyne) -> None:
        """Initialize the sites client."""
        self._client = client

    async def list(self) -> SiteList:
        """List all saved sites."""
        from refyne.types import ListSavedSitesOutputBody

        data = await self._client._request("GET", "/api/v1/sites")
        return ListSavedSitesOutputBody.model_validate(data)

    async def get(self, site_id: str) -> Site:
        """Get a site by ID."""
        from refyne.types import SavedSiteOutput

        data = await self._client._request("GET", f"/api/v1/sites/{site_id}")
        return SavedSiteOutput.model_validate(data)

    async def create(
        self,
        name: str,
        url: str,
        *,
        schema_id: str | None = None,
        crawl_options: dict[str, Any] | None = None,
    ) -> Site:
        """Create a new saved site."""
        from refyne.types import SavedSiteOutput

        body: dict[str, Any] = {"name": name, "url": url}
        if schema_id:
            body["default_schema_id"] = schema_id
        if crawl_options:
            body["crawl_options"] = crawl_options

        data = await self._client._request("POST", "/api/v1/sites", body=body)
        return SavedSiteOutput.model_validate(data)

    async def update(
        self,
        site_id: str,
        *,
        name: str | None = None,
        url: str | None = None,
        schema_id: str | None = None,
        crawl_options: dict[str, Any] | None = None,
    ) -> Site:
        """Update a saved site."""
        from refyne.types import SavedSiteOutput

        body: dict[str, Any] = {}
        if name:
            body["name"] = name
        if url:
            body["url"] = url
        if schema_id:
            body["default_schema_id"] = schema_id
        if crawl_options:
            body["crawl_options"] = crawl_options

        data = await self._client._request("PUT", f"/api/v1/sites/{site_id}", body=body)
        return SavedSiteOutput.model_validate(data)

    async def delete(self, site_id: str) -> None:
        """Delete a saved site."""
        await self._client._request("DELETE", f"/api/v1/sites/{site_id}")


class KeysClient:
    """Client for API key management."""

    def __init__(self, client: Refyne) -> None:
        """Initialize the keys client."""
        self._client = client

    async def list(self) -> ApiKeyList:
        """List all API keys."""
        from refyne.types import ListKeysOutputBody

        data = await self._client._request("GET", "/api/v1/keys")
        return ListKeysOutputBody.model_validate(data)

    async def create(self, name: str) -> ApiKeyCreated:
        """Create a new API key."""
        from refyne.types import CreateKeyOutputBody

        data = await self._client._request("POST", "/api/v1/keys", body={"name": name})
        return CreateKeyOutputBody.model_validate(data)

    async def revoke(self, key_id: str) -> None:
        """Revoke an API key."""
        await self._client._request("DELETE", f"/api/v1/keys/{key_id}")


class LlmClient:
    """Client for LLM configuration."""

    def __init__(self, client: Refyne) -> None:
        """Initialize the LLM client."""
        self._client = client

    async def list_providers(self) -> Any:
        """List available LLM providers."""
        from refyne.types import ListProvidersOutputBody

        data = await self._client._request("GET", "/api/v1/llm/providers")
        return ListProvidersOutputBody.model_validate(data)

    async def list_keys(self) -> LlmKeyList:
        """List configured provider keys (BYOK)."""
        from refyne.types import ListUserServiceKeysOutputBody

        data = await self._client._request("GET", "/api/v1/llm/keys")
        return ListUserServiceKeysOutputBody.model_validate(data)

    async def upsert_key(
        self,
        provider: str,
        api_key: str,
        default_model: str,
        *,
        base_url: str | None = None,
        is_enabled: bool | None = None,
    ) -> LlmKey:
        """Add or update a provider key."""
        from refyne.types import UserServiceKeyResponse

        body: dict[str, Any] = {
            "provider": provider,
            "api_key": api_key,
            "default_model": default_model,
        }
        if base_url:
            body["base_url"] = base_url
        if is_enabled is not None:
            body["is_enabled"] = is_enabled

        data = await self._client._request("PUT", "/api/v1/llm/keys", body=body)
        return UserServiceKeyResponse.model_validate(data)

    async def delete_key(self, key_id: str) -> None:
        """Delete a provider key."""
        await self._client._request("DELETE", f"/api/v1/llm/keys/{key_id}")

    async def get_chain(self) -> LlmChain:
        """Get the fallback chain configuration."""
        from refyne.types import GetUserFallbackChainOutputBody

        data = await self._client._request("GET", "/api/v1/llm/chain")
        return GetUserFallbackChainOutputBody.model_validate(data)

    async def set_chain(
        self,
        chain: list[dict[str, Any]],
    ) -> None:
        """Set the fallback chain configuration."""
        await self._client._request("PUT", "/api/v1/llm/chain", body={"chain": chain})

    async def list_models(self, provider: str) -> ModelList:
        """List available models for a provider."""
        from refyne.types import UserListModelsOutputBody

        data = await self._client._request("GET", f"/api/v1/llm/models/{provider}")
        return UserListModelsOutputBody.model_validate(data)


class WebhooksClient:
    """Client for webhook management."""

    def __init__(self, client: Refyne) -> None:
        """Initialize the webhooks client."""
        self._client = client

    async def list(self) -> dict[str, Any]:
        """List all webhooks."""
        return await self._client._request("GET", "/api/v1/webhooks")

    async def get(self, webhook_id: str) -> dict[str, Any]:
        """Get a webhook by ID."""
        return await self._client._request("GET", f"/api/v1/webhooks/{webhook_id}")

    async def create(
        self,
        name: str,
        url: str,
        *,
        events: list[str] | None = None,
        is_active: bool = True,
        secret: str | None = None,
    ) -> dict[str, Any]:
        """Create a new webhook.

        Args:
            name: Webhook name
            url: Webhook URL
            events: Event types to subscribe to
            is_active: Whether the webhook is active
            secret: Secret for HMAC-SHA256 signature
        """
        body: dict[str, Any] = {"name": name, "url": url, "is_active": is_active}
        if events:
            body["events"] = events
        if secret:
            body["secret"] = secret
        return await self._client._request("POST", "/api/v1/webhooks", body=body)

    async def update(
        self,
        webhook_id: str,
        *,
        name: str | None = None,
        url: str | None = None,
        events: list[str] | None = None,
        is_active: bool | None = None,
        secret: str | None = None,
    ) -> dict[str, Any]:
        """Update a webhook.

        Args:
            webhook_id: Webhook ID
            name: Webhook name
            url: Webhook URL
            events: Event types to subscribe to
            is_active: Whether the webhook is active
            secret: Secret for HMAC-SHA256 signature
        """
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if url is not None:
            body["url"] = url
        if events is not None:
            body["events"] = events
        if is_active is not None:
            body["is_active"] = is_active
        if secret is not None:
            body["secret"] = secret
        return await self._client._request(
            "PUT", f"/api/v1/webhooks/{webhook_id}", body=body
        )

    async def delete(self, webhook_id: str) -> None:
        """Delete a webhook."""
        await self._client._request("DELETE", f"/api/v1/webhooks/{webhook_id}")

    async def list_deliveries(
        self,
        webhook_id: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """List webhook deliveries.

        Args:
            webhook_id: Webhook ID
            limit: Maximum number of deliveries to return
            offset: Number of deliveries to skip
        """
        params: dict[str, int] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        query = urlencode(params) if params else ""
        path = f"/api/v1/webhooks/{webhook_id}/deliveries{'?' + query if query else ''}"
        return await self._client._request("GET", path)
