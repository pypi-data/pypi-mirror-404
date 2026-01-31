"""
Tests for Emailr SDK error classes.
"""

import pytest
from emailr.errors import (
    EmailrError,
    NetworkError,
    ValidationError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)


class TestEmailrError:
    """Tests for the base EmailrError class."""

    def test_create_with_message(self):
        """Should create an error with message."""
        error = EmailrError("Something went wrong")
        
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.status_code is None

    def test_create_with_status_code(self):
        """Should create an error with status code."""
        error = EmailrError("Server error", status_code=500)
        
        assert error.message == "Server error"
        assert error.status_code == 500

    def test_create_with_code_and_details(self):
        """Should create an error with code and details."""
        error = EmailrError(
            "Bad request",
            status_code=400,
            code="INVALID_INPUT",
            details={"field": "email"}
        )
        
        assert error.code == "INVALID_INPUT"
        assert error.details == {"field": "email"}

    def test_is_exception(self):
        """Should be catchable as Exception."""
        error = EmailrError("Test error")
        
        assert isinstance(error, Exception)
        
        with pytest.raises(Exception):
            raise error


class TestNetworkError:
    """Tests for NetworkError class."""

    def test_create_network_error(self):
        """Should create a network error."""
        error = NetworkError("Connection failed")
        
        assert error.message == "Connection failed"
        assert isinstance(error, EmailrError)

    def test_with_original_error(self):
        """Should include original error."""
        original = ConnectionError("ECONNREFUSED")
        error = NetworkError("Connection failed", original_error=original)
        
        assert error.original_error is original


class TestValidationError:
    """Tests for ValidationError class."""

    def test_create_validation_error(self):
        """Should create a validation error with details."""
        details = {
            "email": ["Invalid email format"],
            "subject": ["Subject is required"],
        }
        error = ValidationError("Validation failed", details=details)
        
        assert error.message == "Validation failed"
        assert error.status_code == 400
        assert error.details == details

    def test_is_emailr_error(self):
        """Should be an EmailrError."""
        error = ValidationError("Invalid input")
        
        assert isinstance(error, EmailrError)


class TestAuthenticationError:
    """Tests for AuthenticationError class."""

    def test_create_auth_error(self):
        """Should create an authentication error."""
        error = AuthenticationError("Invalid API key")
        
        assert error.message == "Invalid API key"
        assert error.status_code == 401

    def test_default_message(self):
        """Should use default message."""
        error = AuthenticationError()
        
        assert error.message == "Authentication failed"


class TestNotFoundError:
    """Tests for NotFoundError class."""

    def test_create_not_found_error(self):
        """Should create a not found error."""
        error = NotFoundError("Email not found")
        
        assert error.message == "Email not found"
        assert error.status_code == 404

    def test_default_message(self):
        """Should use default message."""
        error = NotFoundError()
        
        assert error.message == "Resource not found"


class TestRateLimitError:
    """Tests for RateLimitError class."""

    def test_create_rate_limit_error(self):
        """Should create a rate limit error."""
        error = RateLimitError("Too many requests", retry_after=60)
        
        assert error.message == "Too many requests"
        assert error.status_code == 429
        assert error.retry_after == 60

    def test_default_message(self):
        """Should use default message."""
        error = RateLimitError()
        
        assert error.message == "Rate limit exceeded"
        assert error.retry_after is None

    def test_retry_after_optional(self):
        """Should allow retry_after to be optional."""
        error = RateLimitError("Rate limited")
        
        assert error.retry_after is None


class TestErrorHierarchy:
    """Tests for error class hierarchy."""

    def test_all_errors_inherit_from_emailr_error(self):
        """All error types should inherit from EmailrError."""
        errors = [
            NetworkError("test"),
            ValidationError("test"),
            AuthenticationError("test"),
            NotFoundError("test"),
            RateLimitError("test"),
        ]
        
        for error in errors:
            assert isinstance(error, EmailrError)

    def test_catch_specific_error(self):
        """Should be able to catch specific error types."""
        with pytest.raises(ValidationError):
            raise ValidationError("Invalid input")

    def test_catch_base_error(self):
        """Should be able to catch all errors with base class."""
        with pytest.raises(EmailrError):
            raise NotFoundError("Not found")
