"""Error types for the Refyne SDK.

All SDK errors inherit from RefyneError which provides consistent
error handling across the API.
"""

from __future__ import annotations

from typing import Any


class RefyneError(Exception):
    """Base error class for all Refyne SDK errors.

    Attributes:
        message: Human-readable error message
        status: HTTP status code from the API response
        detail: Additional error details from the API
        response: The original httpx response (if available)

    Example:
        >>> try:
        ...     await refyne.extract(url=url, schema=schema)
        ... except RefyneError as e:
        ...     print(f"API Error: {e.message} (status: {e.status})")
    """

    def __init__(
        self,
        message: str,
        status: int = 0,
        detail: str | None = None,
        response: Any = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Human-readable error message
            status: HTTP status code (0 for non-HTTP errors)
            detail: Additional error detail string
            response: Original httpx response object
        """
        super().__init__(message)
        self.message = message
        self.status = status
        self.detail = detail
        self.response = response

    def __str__(self) -> str:
        """Return string representation."""
        if self.detail:
            return f"{self.message}: {self.detail}"
        return self.message


class RateLimitError(RefyneError):
    """Error thrown when the API rate limit is exceeded.

    The `retry_after` property indicates how many seconds to wait
    before retrying. The SDK's auto-retry handles this automatically.

    Attributes:
        retry_after: Number of seconds to wait before retrying

    Example:
        >>> try:
        ...     await refyne.extract(url=url, schema=schema)
        ... except RateLimitError as e:
        ...     print(f"Rate limited. Retry after {e.retry_after} seconds")
    """

    def __init__(
        self,
        message: str,
        retry_after: int,
        detail: str | None = None,
        response: Any = None,
    ) -> None:
        """Initialize the rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            detail: Additional detail
            response: Original response
        """
        super().__init__(message, status=429, detail=detail, response=response)
        self.retry_after = retry_after


class ValidationError(RefyneError):
    """Error thrown when request validation fails.

    This typically indicates an issue with the request payload,
    such as an invalid URL or malformed schema.

    Attributes:
        errors: Dict of field names to lists of error messages
    """

    def __init__(
        self,
        message: str,
        errors: dict[str, list[str]] | None = None,
        response: Any = None,
    ) -> None:
        """Initialize the validation error.

        Args:
            message: Error message
            errors: Dict of field validation errors
            response: Original response
        """
        super().__init__(message, status=400, response=response)
        self.errors = errors or {}


class AuthenticationError(RefyneError):
    """Error thrown when authentication fails.

    This typically indicates an invalid or expired API key.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        response: Any = None,
    ) -> None:
        """Initialize the authentication error.

        Args:
            message: Error message
            response: Original response
        """
        super().__init__(message, status=401, response=response)


class ForbiddenError(RefyneError):
    """Error thrown when the user lacks permission for an operation.

    This may indicate the user's tier doesn't have access to a feature,
    or they've exceeded their quota.
    """

    def __init__(
        self,
        message: str = "Access forbidden",
        response: Any = None,
    ) -> None:
        """Initialize the forbidden error.

        Args:
            message: Error message
            response: Original response
        """
        super().__init__(message, status=403, response=response)


class NotFoundError(RefyneError):
    """Error thrown when a requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        response: Any = None,
    ) -> None:
        """Initialize the not found error.

        Args:
            message: Error message
            response: Original response
        """
        super().__init__(message, status=404, response=response)


class UnsupportedAPIVersionError(RefyneError):
    """Error thrown when the API version is incompatible with the SDK.

    This occurs when the API version is lower than the SDK's minimum
    supported version.

    Attributes:
        api_version: The API version that was detected
        min_version: The minimum version this SDK supports
        max_known_version: The maximum version this SDK was built for

    Example:
        >>> try:
        ...     await refyne.extract(url=url, schema=schema)
        ... except UnsupportedAPIVersionError as e:
        ...     print(f"API version {e.api_version} is not supported.")
        ...     print(f"This SDK requires API version >= {e.min_version}")
    """

    def __init__(
        self,
        api_version: str,
        min_version: str,
        max_known_version: str,
    ) -> None:
        """Initialize the version error.

        Args:
            api_version: Detected API version
            min_version: Minimum supported version
            max_known_version: Maximum known version
        """
        message = (
            f"API version {api_version} is not supported. "
            f"This SDK requires API version >= {min_version}. "
            "Please upgrade the API or use an older SDK version."
        )
        super().__init__(message, status=0)
        self.api_version = api_version
        self.min_version = min_version
        self.max_known_version = max_known_version


class TLSError(RefyneError):
    """Error thrown when TLS certificate validation fails.

    This error is thrown when connecting to an API endpoint with
    an invalid, self-signed, or expired certificate.

    Attributes:
        url: The URL that failed TLS validation
        tls_error: The underlying TLS error message
    """

    def __init__(self, url: str, tls_error: str) -> None:
        """Initialize the TLS error.

        Args:
            url: URL that failed validation
            tls_error: Underlying TLS error message
        """
        message = f"TLS certificate validation failed for {url}: {tls_error}"
        super().__init__(message, status=0)
        self.url = url
        self.tls_error = tls_error


async def create_error_from_response(response: Any) -> RefyneError:
    """Create the appropriate error type from an API response.

    Args:
        response: httpx Response object

    Returns:
        Appropriate RefyneError subclass
    """
    error_body: dict[str, Any] = {}

    try:
        error_body = response.json()
    except Exception:
        pass

    message = (
        error_body.get("error")
        or error_body.get("message")
        or response.reason_phrase
        or "Unknown error"
    )
    detail = error_body.get("detail")

    status = response.status_code

    if status == 400:
        return ValidationError(
            message=message,
            errors=error_body.get("errors"),
            response=response,
        )
    elif status == 401:
        return AuthenticationError(message=message, response=response)
    elif status == 403:
        return ForbiddenError(message=message, response=response)
    elif status == 404:
        return NotFoundError(message=message, response=response)
    elif status == 429:
        retry_after = int(response.headers.get("Retry-After", "60"))
        return RateLimitError(
            message=message,
            retry_after=retry_after,
            detail=detail,
            response=response,
        )
    else:
        return RefyneError(
            message=message,
            status=status,
            detail=detail,
            response=response,
        )
