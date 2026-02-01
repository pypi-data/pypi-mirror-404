"""Official Python SDK for the Refyne API.

Refyne is an LLM-powered web extraction API that transforms unstructured
websites into clean, typed data.

Example:
    >>> from refyne import Refyne
    >>>
    >>> client = Refyne(api_key="your_api_key")
    >>>
    >>> result = await client.extract(
    ...     url="https://example.com/product",
    ...     schema={"name": "string", "price": "number"},
    ... )
    >>> print(result.data)
"""

from refyne.cache import MemoryCache, create_cache_entry, parse_cache_control
from refyne.client import JobResultEntry, JobResults, Refyne, RefyneConfig
from refyne.errors import (
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    RefyneError,
    TLSError,
    UnsupportedAPIVersionError,
    ValidationError,
)
from refyne.interfaces import Cache, CacheEntry, HttpClient, Logger
from refyne.types import (
    # Request types
    AnalyzeInputBody as AnalyzeRequest,
    CrawlOptionsInput as CrawlOptions,
    CreateKeyInputBody as CreateApiKeyRequest,
    CreateSchemaInputBody as CreateSchemaRequest,
    CreateSavedSiteInputBody as CreateSiteRequest,
    ExtractInputBody as ExtractRequest,
    SetUserFallbackChainInputBody as SetLlmChainRequest,
    UserServiceKeyInput as UpsertLlmKeyRequest,
    # Response types
    AnalyzeResponseBody as AnalyzeResponse,
    APIKeyResponse as ApiKey,
    CreateKeyOutputBody as ApiKeyCreated,
    CrawlJobResponseBody as CrawlJobCreated,
    ExtractOutputBody as ExtractResponse,
    GetUsageOutputBody as UsageResponse,
    GetUserFallbackChainOutputBody as LlmChain,
    JobResponse as Job,
    ListJobsOutputBody as JobList,
    ListKeysOutputBody as ApiKeyList,
    ListModelsOutputBody as ModelList,
    ListSavedSitesOutputBody as SiteList,
    ListSchemasOutputBody as SchemaList,
    ListUserServiceKeysOutputBody as LlmKeyList,
    SavedSiteOutput as Site,
    SchemaOutput as Schema,
    UserFallbackChainEntryResponse as LlmChainEntry,
    UserServiceKeyResponse as LlmKey,
    # Other types
    LLMConfigInput as LlmConfig,
    TokenUsage,
)
from refyne.version import (
    MAX_KNOWN_API_VERSION,
    MIN_API_VERSION,
    SDK_VERSION,
)

__version__ = SDK_VERSION

__all__ = [
    # Client
    "Refyne",
    "RefyneConfig",
    # Errors
    "RefyneError",
    "RateLimitError",
    "ValidationError",
    "AuthenticationError",
    "ForbiddenError",
    "NotFoundError",
    "UnsupportedAPIVersionError",
    "TLSError",
    # Types
    "ExtractRequest",
    "ExtractResponse",
    "CrawlJobCreated",
    "CrawlOptions",
    "Job",
    "JobList",
    "JobResults",
    "JobResultEntry",
    "AnalyzeRequest",
    "AnalyzeResponse",
    "Schema",
    "SchemaList",
    "CreateSchemaRequest",
    "Site",
    "SiteList",
    "CreateSiteRequest",
    "ApiKey",
    "ApiKeyList",
    "ApiKeyCreated",
    "CreateApiKeyRequest",
    "UsageResponse",
    "LlmKey",
    "LlmKeyList",
    "UpsertLlmKeyRequest",
    "LlmChain",
    "LlmChainEntry",
    "SetLlmChainRequest",
    "ModelList",
    "TokenUsage",
    "LlmConfig",
    # Interfaces
    "Logger",
    "HttpClient",
    "Cache",
    "CacheEntry",
    # Cache
    "MemoryCache",
    "parse_cache_control",
    "create_cache_entry",
    # Version
    "SDK_VERSION",
    "MIN_API_VERSION",
    "MAX_KNOWN_API_VERSION",
]
