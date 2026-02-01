"""
FirmeAPI Exception Classes
"""

from typing import Optional


class FirmeApiError(Exception):
    """Base exception class for all FirmeAPI errors"""

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        status_code: int = 500,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


class AuthenticationError(FirmeApiError):
    """Thrown when authentication fails (invalid or missing API key)"""

    def __init__(self, message: str, code: str = "AUTH_ERROR") -> None:
        super().__init__(message, code, 401)


class NotFoundError(FirmeApiError):
    """Thrown when a resource is not found"""

    def __init__(self, message: str, code: str = "NOT_FOUND") -> None:
        super().__init__(message, code, 404)


class RateLimitError(FirmeApiError):
    """Thrown when rate limit is exceeded"""

    def __init__(
        self,
        message: str,
        code: str = "RATE_LIMIT_EXCEEDED",
        retry_after: int = 1,
        current_usage: int = 0,
        limit: int = 0,
    ) -> None:
        super().__init__(message, code, 429)
        self.retry_after = retry_after
        self.current_usage = current_usage
        self.limit = limit


class InsufficientCreditsError(FirmeApiError):
    """Thrown when credits are exhausted"""

    def __init__(
        self,
        message: str,
        code: str = "CREDITS_EXHAUSTED",
        available_credits: int = 0,
        required_credits: int = 1,
    ) -> None:
        super().__init__(message, code, 403)
        self.available_credits = available_credits
        self.required_credits = required_credits


class ValidationError(FirmeApiError):
    """Thrown when request validation fails"""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR") -> None:
        super().__init__(message, code, 400)


class ApiError(FirmeApiError):
    """Thrown when the API returns an unexpected error"""

    pass


class NetworkError(FirmeApiError):
    """Thrown when a network error occurs"""

    def __init__(self, message: str = "Network request failed") -> None:
        super().__init__(message, "NETWORK_ERROR", 0)


class TimeoutError(FirmeApiError):
    """Thrown when request times out"""

    def __init__(self, message: str = "Request timed out") -> None:
        super().__init__(message, "TIMEOUT", 0)
