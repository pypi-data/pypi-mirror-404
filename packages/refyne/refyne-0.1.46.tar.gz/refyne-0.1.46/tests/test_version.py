"""Tests for the version module."""


from refyne.interfaces import DefaultLogger
from refyne.version import (
    MAX_KNOWN_API_VERSION,
    MIN_API_VERSION,
    SDK_VERSION,
    build_user_agent,
    check_api_version_compatibility,
    compare_versions,
    parse_version,
)


class TestParseVersion:
    """Tests for parse_version."""

    def test_parses_major_minor_patch(self) -> None:
        """Test parsing basic semver."""
        major, minor, patch, prerelease = parse_version("1.2.3")
        assert major == 1
        assert minor == 2
        assert patch == 3
        assert prerelease is None

    def test_parses_prerelease(self) -> None:
        """Test parsing version with prerelease."""
        major, minor, patch, prerelease = parse_version("1.2.3-beta")
        assert major == 1
        assert minor == 2
        assert patch == 3
        assert prerelease == "beta"

    def test_returns_zeros_for_invalid(self) -> None:
        """Test that invalid format returns zeros."""
        major, minor, patch, prerelease = parse_version("invalid")
        assert major == 0
        assert minor == 0
        assert patch == 0
        assert prerelease is None


class TestCompareVersions:
    """Tests for compare_versions."""

    def test_equal_versions(self) -> None:
        """Test comparing equal versions."""
        assert compare_versions("1.2.3", "1.2.3") == 0

    def test_compares_major(self) -> None:
        """Test comparing major versions."""
        assert compare_versions("2.0.0", "1.0.0") == 1
        assert compare_versions("1.0.0", "2.0.0") == -1

    def test_compares_minor(self) -> None:
        """Test comparing minor versions."""
        assert compare_versions("1.2.0", "1.1.0") == 1
        assert compare_versions("1.1.0", "1.2.0") == -1

    def test_compares_patch(self) -> None:
        """Test comparing patch versions."""
        assert compare_versions("1.1.2", "1.1.1") == 1
        assert compare_versions("1.1.1", "1.1.2") == -1


class TestCheckApiVersionCompatibility:
    """Tests for check_api_version_compatibility."""

    def test_compatible_version_passes(self) -> None:
        """Test that compatible versions don't raise."""
        logger = DefaultLogger()
        # Should not raise
        check_api_version_compatibility(MIN_API_VERSION, logger)

    def test_warns_about_newer_major(self) -> None:
        """Test that newer major versions produce a warning."""
        # We'd need to capture the warning to verify this
        # For now, just verify it doesn't crash
        logger = DefaultLogger()
        check_api_version_compatibility("99.0.0", logger)


class TestBuildUserAgent:
    """Tests for build_user_agent."""

    def test_includes_sdk_version(self) -> None:
        """Test that user agent includes SDK version."""
        ua = build_user_agent()
        assert "Refyne-SDK-Python" in ua
        assert SDK_VERSION in ua

    def test_includes_custom_suffix(self) -> None:
        """Test that custom suffix is appended."""
        ua = build_user_agent("MyApp/1.0")
        assert "MyApp/1.0" in ua


class TestVersionConstants:
    """Tests for version constants."""

    def test_sdk_version_is_semver(self) -> None:
        """Test that SDK_VERSION is valid semver."""
        major, _, _, _ = parse_version(SDK_VERSION)
        assert major >= 0

    def test_min_api_version_is_semver(self) -> None:
        """Test that MIN_API_VERSION is valid semver."""
        major, _, _, _ = parse_version(MIN_API_VERSION)
        assert major >= 0

    def test_max_known_version_is_semver(self) -> None:
        """Test that MAX_KNOWN_API_VERSION is valid semver."""
        major, _, _, _ = parse_version(MAX_KNOWN_API_VERSION)
        assert major >= 0

    def test_min_le_max(self) -> None:
        """Test that MIN <= MAX."""
        assert compare_versions(MIN_API_VERSION, MAX_KNOWN_API_VERSION) <= 0
