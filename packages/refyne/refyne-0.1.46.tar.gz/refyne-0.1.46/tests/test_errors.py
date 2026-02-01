"""Tests for the errors module."""


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


class TestRefyneError:
    """Tests for RefyneError."""

    def test_stores_message_and_status(self) -> None:
        """Test that message and status are stored."""
        error = RefyneError("test message", 404)
        assert error.message == "test message"
        assert error.status == 404
        assert str(error) == "test message"

    def test_stores_detail(self) -> None:
        """Test that detail is stored."""
        error = RefyneError("test", 400, "additional detail")
        assert error.detail == "additional detail"
        assert "additional detail" in str(error)

    def test_is_exception(self) -> None:
        """Test that it's an Exception."""
        error = RefyneError("test", 500)
        assert isinstance(error, Exception)


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_stores_retry_after(self) -> None:
        """Test that retry_after is stored."""
        error = RateLimitError("rate limited", 60)
        assert error.retry_after == 60
        assert error.status == 429

    def test_is_refyne_error(self) -> None:
        """Test that it inherits from RefyneError."""
        error = RateLimitError("rate limited", 60)
        assert isinstance(error, RefyneError)


class TestValidationError:
    """Tests for ValidationError."""

    def test_stores_errors(self) -> None:
        """Test that field errors are stored."""
        errors = {"url": ["required"], "schema": ["invalid"]}
        error = ValidationError("validation failed", errors)
        assert error.errors == errors
        assert error.status == 400


class TestUnsupportedAPIVersionError:
    """Tests for UnsupportedAPIVersionError."""

    def test_stores_versions(self) -> None:
        """Test that version info is stored."""
        error = UnsupportedAPIVersionError("0.1.0", "0.2.0", "0.3.0")
        assert error.api_version == "0.1.0"
        assert error.min_version == "0.2.0"
        assert error.max_known_version == "0.3.0"

    def test_formats_message(self) -> None:
        """Test that message contains version info."""
        error = UnsupportedAPIVersionError("0.1.0", "0.2.0", "0.3.0")
        assert "0.1.0" in error.message
        assert "0.2.0" in error.message


class TestTLSError:
    """Tests for TLSError."""

    def test_stores_url_and_error(self) -> None:
        """Test that URL and TLS error are stored."""
        error = TLSError("https://example.com", "certificate expired")
        assert error.url == "https://example.com"
        assert error.tls_error == "certificate expired"


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = AuthenticationError()
        assert error.message == "Authentication failed"
        assert error.status == 401


class TestForbiddenError:
    """Tests for ForbiddenError."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = ForbiddenError()
        assert error.message == "Access forbidden"
        assert error.status == 403


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = NotFoundError()
        assert error.message == "Resource not found"
        assert error.status == 404
