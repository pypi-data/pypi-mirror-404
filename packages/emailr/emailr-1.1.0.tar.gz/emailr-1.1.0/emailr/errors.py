"""
Exception classes for the Emailr SDK.

All exceptions inherit from EmailrError, which provides common attributes
for error handling including status code, error code, and request ID.
"""

from typing import Any, Dict, Optional


class EmailrError(Exception):
    """
    Base exception class for all Emailr SDK errors.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code (0 for network errors)
        code: Error code string for programmatic handling
        request_id: Request ID for debugging (when available)
    """

    def __init__(
        self,
        message: str,
        status_code: int,
        code: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.request_id = request_id

    def __str__(self) -> str:
        parts = [self.message]
        if self.code:
            parts.append(f"[{self.code}]")
        if self.request_id:
            parts.append(f"(request_id: {self.request_id})")
        return " ".join(parts)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code}, "
            f"code={self.code!r}, "
            f"request_id={self.request_id!r})"
        )


class NetworkError(EmailrError):
    """
    Exception raised when a network request fails.

    This includes connection errors, timeouts, and other transport-level failures.
    """

    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        super().__init__(message, status_code=0, code="NETWORK_ERROR")
        self.__cause__ = cause


class AuthenticationError(EmailrError):
    """
    Exception raised when authentication fails.

    This typically indicates an invalid or expired API key.
    """

    def __init__(
        self,
        message: str = "Invalid API key",
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            status_code=401,
            code="AUTHENTICATION_ERROR",
            request_id=request_id,
        )


class RateLimitError(EmailrError):
    """
    Exception raised when the rate limit is exceeded.

    Attributes:
        retry_after: Number of seconds to wait before retrying (when available)
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            status_code=429,
            code="RATE_LIMIT_ERROR",
            request_id=request_id,
        )
        self.retry_after = retry_after


class NotFoundError(EmailrError):
    """
    Exception raised when a requested resource is not found.
    """

    def __init__(
        self,
        message: str = "Resource not found",
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            status_code=404,
            code="NOT_FOUND",
            request_id=request_id,
        )


class ValidationError(EmailrError):
    """
    Exception raised when request validation fails.

    Attributes:
        details: Additional details about validation errors (when available)
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            status_code=400,
            code="VALIDATION_ERROR",
            request_id=request_id,
        )
        self.details = details
