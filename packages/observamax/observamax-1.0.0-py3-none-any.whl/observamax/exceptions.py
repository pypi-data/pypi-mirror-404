"""
ObservaMax SDK Exceptions
"""


class ObservaMaxError(Exception):
    """Base exception for ObservaMax SDK"""

    pass


class ApiError(ObservaMaxError):
    """API request error"""

    def __init__(self, message: str, status_code: int, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code

    def __str__(self) -> str:
        return f"ApiError({self.status_code}): {self.message}"


class AuthenticationError(ApiError):
    """Authentication failed (401)"""

    pass


class PermissionError(ApiError):
    """Permission denied (403)"""

    pass


class NotFoundError(ApiError):
    """Resource not found (404)"""

    pass


class RateLimitError(ApiError):
    """Rate limit exceeded (429)"""

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
    ):
        super().__init__(message, 429, "RATE_LIMITED")
        self.retry_after = retry_after


class ValidationError(ApiError):
    """Validation error (400)"""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, 400, "VALIDATION_ERROR")
        self.details = details or {}
