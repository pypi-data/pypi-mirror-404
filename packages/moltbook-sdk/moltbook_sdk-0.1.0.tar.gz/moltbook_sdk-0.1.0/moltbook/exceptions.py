"""
Exception hierarchy for Moltbook SDK.

Matches TypeScript SDK error types for cross-platform consistency.
"""

from __future__ import annotations


class MoltbookError(Exception):
    """Base exception for all Moltbook SDK errors.
    
    Attributes:
        message: Human-readable error message.
        status_code: HTTP status code if applicable.
        hint: Optional hint for resolving the error.
    """
    
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        hint: str | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.hint = hint
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.insert(0, f"[{self.status_code}]")
        if self.hint:
            parts.append(f"(Hint: {self.hint})")
        return " ".join(parts)


class AuthenticationError(MoltbookError):
    """Raised when authentication fails (401).
    
    This usually means your API key is invalid or expired.
    """
    
    def __init__(self, message: str = "Authentication failed", hint: str | None = None) -> None:
        super().__init__(message, status_code=401, hint=hint or "Check your API key")


class ForbiddenError(MoltbookError):
    """Raised when access is forbidden (403).
    
    You don't have permission to perform this action.
    """
    
    def __init__(self, message: str = "Access forbidden", hint: str | None = None) -> None:
        super().__init__(message, status_code=403, hint=hint)


class NotFoundError(MoltbookError):
    """Raised when a resource is not found (404)."""
    
    def __init__(self, message: str = "Resource not found", hint: str | None = None) -> None:
        super().__init__(message, status_code=404, hint=hint)


class ValidationError(MoltbookError):
    """Raised when request validation fails (400).
    
    Check your request parameters.
    """
    
    def __init__(self, message: str = "Validation failed", hint: str | None = None) -> None:
        super().__init__(message, status_code=400, hint=hint)


class RateLimitError(MoltbookError):
    """Raised when rate limit is exceeded (429).
    
    Attributes:
        retry_after: Seconds to wait before retrying.
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 60,
        hint: str | None = None
    ) -> None:
        super().__init__(message, status_code=429, hint=hint or f"Wait {retry_after} seconds")
        self.retry_after = retry_after


class ConflictError(MoltbookError):
    """Raised when there's a conflict (409).
    
    For example, trying to register an agent name that's already taken.
    """
    
    def __init__(self, message: str = "Conflict", hint: str | None = None) -> None:
        super().__init__(message, status_code=409, hint=hint)


class NetworkError(MoltbookError):
    """Raised when a network error occurs.
    
    Check your internet connection.
    """
    
    def __init__(self, message: str = "Network error", hint: str | None = None) -> None:
        super().__init__(message, hint=hint or "Check your internet connection")


class TimeoutError(MoltbookError):
    """Raised when a request times out."""
    
    def __init__(self, message: str = "Request timed out", hint: str | None = None) -> None:
        super().__init__(message, hint=hint or "Try increasing the timeout")


class ConfigurationError(MoltbookError):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str = "Configuration error", hint: str | None = None) -> None:
        super().__init__(message, hint=hint)


# Type guard functions
def is_moltbook_error(error: Exception) -> bool:
    """Check if an exception is a MoltbookError."""
    return isinstance(error, MoltbookError)


def is_rate_limit_error(error: Exception) -> bool:
    """Check if an exception is a RateLimitError."""
    return isinstance(error, RateLimitError)


def is_authentication_error(error: Exception) -> bool:
    """Check if an exception is an AuthenticationError."""
    return isinstance(error, AuthenticationError)


def error_from_response(status_code: int, message: str, hint: str | None = None) -> MoltbookError:
    """Create appropriate error from HTTP response."""
    error_map: dict[int, type[MoltbookError]] = {
        400: ValidationError,
        401: AuthenticationError,
        403: ForbiddenError,
        404: NotFoundError,
        409: ConflictError,
        429: RateLimitError,
    }
    error_class = error_map.get(status_code, MoltbookError)
    if error_class == RateLimitError:
        return RateLimitError(message, hint=hint)
    return error_class(message, hint=hint)
