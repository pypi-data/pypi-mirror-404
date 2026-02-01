"""SDK version information and API compatibility checking."""

from __future__ import annotations

import platform
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from refyne.interfaces import Logger

# Current SDK version
SDK_VERSION = "0.0.0"

# Minimum API version this SDK supports
MIN_API_VERSION = "0.0.0"

# Maximum API version this SDK was built against
MAX_KNOWN_API_VERSION = "0.0.0"


def parse_version(version: str) -> tuple[int, int, int, str | None]:
    """Parse a semver version string into components.

    Args:
        version: Version string (e.g., "1.2.3" or "1.2.3-beta")

    Returns:
        Tuple of (major, minor, patch, prerelease)
    """
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$", version)
    if not match:
        return (0, 0, 0, None)

    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
        match.group(4),
    )


def compare_versions(a: str, b: str) -> int:
    """Compare two semver versions.

    Returns:
        -1 if a < b, 0 if a == b, 1 if a > b
    """
    va = parse_version(a)
    vb = parse_version(b)

    # Compare major, minor, patch explicitly to satisfy mypy
    # (tuple indexing with a variable returns a union type)
    if va[0] != vb[0]:
        return -1 if va[0] < vb[0] else 1
    if va[1] != vb[1]:
        return -1 if va[1] < vb[1] else 1
    if va[2] != vb[2]:
        return -1 if va[2] < vb[2] else 1

    return 0


def check_api_version_compatibility(api_version: str, logger: Logger) -> None:
    """Check if an API version is compatible with this SDK.

    Args:
        api_version: The API version from the X-API-Version header
        logger: Logger for warnings

    Raises:
        UnsupportedAPIVersionError: If the API version is too old
    """
    from refyne.errors import UnsupportedAPIVersionError

    # If API version is lower than minimum supported, raise error
    if compare_versions(api_version, MIN_API_VERSION) < 0:
        raise UnsupportedAPIVersionError(
            api_version=api_version,
            min_version=MIN_API_VERSION,
            max_known_version=MAX_KNOWN_API_VERSION,
        )

    # If API major version is higher than known, warn about potential breaking changes
    api_major = parse_version(api_version)[0]
    max_major = parse_version(MAX_KNOWN_API_VERSION)[0]

    if api_major > max_major:
        logger.warn(
            f"API version {api_version} is newer than this SDK was built for "
            f"({MAX_KNOWN_API_VERSION}). There may be breaking changes. "
            "Consider upgrading the SDK.",
            {
                "api_version": api_version,
                "sdk_version": SDK_VERSION,
                "max_known_version": MAX_KNOWN_API_VERSION,
            },
        )


def detect_runtime() -> tuple[str, str]:
    """Detect the current runtime environment.

    Returns:
        Tuple of (runtime name, version string)
    """
    return ("Python", platform.python_version())


def build_user_agent(custom_suffix: str | None = None) -> str:
    """Build the User-Agent string for SDK requests.

    Args:
        custom_suffix: Optional suffix to append (e.g., "MyApp/1.0")

    Returns:
        User-Agent string

    Example:
        >>> build_user_agent()
        'Refyne-SDK-Python/0.1.0 (Python/3.11.0)'

        >>> build_user_agent("MyApp/1.0")
        'Refyne-SDK-Python/0.1.0 (Python/3.11.0) MyApp/1.0'
    """
    runtime_name, runtime_version = detect_runtime()
    user_agent = f"Refyne-SDK-Python/{SDK_VERSION} ({runtime_name}/{runtime_version})"

    if custom_suffix:
        user_agent += f" {custom_suffix}"

    return user_agent
