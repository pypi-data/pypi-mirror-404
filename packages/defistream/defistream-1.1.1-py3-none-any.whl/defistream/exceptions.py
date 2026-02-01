"""DeFiStream API exceptions."""

from typing import Any


class DeFiStreamError(Exception):
    """Base exception for DeFiStream API errors."""

    def __init__(self, message: str, status_code: int | None = None, response: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response


class AuthenticationError(DeFiStreamError):
    """Raised when API key is invalid or missing."""

    pass


class QuotaExceededError(DeFiStreamError):
    """Raised when account quota is exceeded."""

    def __init__(
        self,
        message: str,
        remaining: int = 0,
        status_code: int | None = None,
        response: Any = None,
    ):
        super().__init__(message, status_code, response)
        self.remaining = remaining


class RateLimitError(DeFiStreamError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: float | None = None,
        status_code: int | None = None,
        response: Any = None,
    ):
        super().__init__(message, status_code, response)
        self.retry_after = retry_after


class ValidationError(DeFiStreamError):
    """Raised when request parameters are invalid."""

    pass


class NotFoundError(DeFiStreamError):
    """Raised when a resource is not found."""

    pass


class ServerError(DeFiStreamError):
    """Raised when the server returns a 5xx error."""

    pass
