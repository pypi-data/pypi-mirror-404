"""Custom exceptions for the CUFinder SDK."""

from typing import Any, Dict, Optional


class CufinderError(Exception):
    """Base exception for all CUFinder SDK errors."""

    def __init__(
        self,
        message: str,
        code: str = "CUFINDER_ERROR",
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.code}] {self.message} (Status: {self.status_code})"
        return f"[{self.code}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "code": self.code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }


class NetworkError(CufinderError):
    """Raised when network-related errors occur."""

    def __init__(self, message: str = "Network error", status_code: Optional[int] = None):
        super().__init__(message, "NETWORK_ERROR", status_code)


class AuthenticationError(CufinderError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR", 401)


class RateLimitError(CufinderError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, "RATE_LIMIT_ERROR", 429, details)
        self.retry_after = retry_after


class CreditLimitError(CufinderError):
    """Raised when credit limit is exceeded."""

    def __init__(self, message: str = "Not enough credit"):
        super().__init__(message, "CREDIT_LIMIT_ERROR", 400)


class NotFoundError(CufinderError):
    """Raised when a resource is not found."""

    def __init__(self, message: str = "Not found result"):
        super().__init__(message, "NOT_FOUND_ERROR", 404)


class PayloadError(CufinderError):
    """Raised when there's an error in the payload."""

    def __init__(
        self,
        message: str = "Error in the payload",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "PAYLOAD_ERROR", 422, details)


class ServerError(CufinderError):
    """Raised when server errors occur."""

    def __init__(self, message: str = "Server error", status_code: int = 500):
        super().__init__(message, "SERVER_ERROR", status_code)


class ValidationError(CufinderError):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "VALIDATION_ERROR", 400, details)
